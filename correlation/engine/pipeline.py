"""End-to-end A1->A4 pass: signal vectors in, CausalGraph JSON out.

MASTER_PLAN sections 1.4.2-1.4.5. Deterministic; no LLM anywhere near this file.
"""
from __future__ import annotations

import itertools

import numpy as np

from . import detectors
from .gate import Witness, accept_edge
from .lagcorr import best_directed
from .ranking import blast_radius, build_graph, rank_root_causes

DT_S = detectors.DT_S


def run_pass(
    vectors: dict[str, np.ndarray],
    witness: Witness,
    slo_breach: list[str] | None = None,
    caps: dict[str, float] | None = None,
) -> dict:
    """One correlation pass.

    vectors: {pod: 1-D signal vector} (one representative signal per pod for v0;
             multi-signal fan-out happens in the caller)
    witness: physical relations from A3/kube-state
    slo_breach: symptom pods to seed root-cause ranking (defaults to pods with onsets)
    caps: optional {pod: limit} for saturation classification
    """
    caps = caps or {}
    findings: dict[str, dict] = {}
    onset_s: dict[str, float] = {}
    for pod, vec in vectors.items():
        ons = detectors.cusum_onsets(vec)
        ons = [o for o in ons if abs(o["zpeak"]) >= 3.0]  # ignore weak/spurious onsets (robustness on noisy non-negative signals)
        if not ons:
            continue
        first = ons[0]
        onset_s[pod] = first["idx"] * DT_S
        findings[pod] = {
            "pod": pod,
            "class": detectors.classify(vec, first["idx"], caps.get(pod)),
            "onset_s": onset_s[pod],
            "severity": min(abs(first["zpeak"]) / 10.0, 1.0),
            "n_onsets": len(ons),
        }

    # pair pruning: only pairs where at least one pod has an active finding
    active = set(findings)
    edges: list[dict] = []
    for a, b in itertools.combinations(sorted(vectors), 2):
        if a not in active and b not in active:
            continue
        d = best_directed(vectors[a], vectors[b])
        src, dst = (a, b) if d["forward"] else (b, a)
        edge = accept_edge(src, dst, d["r"], d["lag_s"], d["profile"], witness, onset_s)
        if edge:
            edges.append(edge)

    g = build_graph(edges)
    seeds = slo_breach or sorted(active)
    ranking = rank_root_causes(g, seeds, onset_s)
    blast = blast_radius(g, ranking[0]["pod"]) if ranking else []
    return {
        "findings": sorted(findings.values(), key=lambda f: f["onset_s"]),
        "edges": edges,
        "root_cause_ranking": ranking,
        "blast_radius": blast,
        "meta": {"pods": len(vectors), "active": len(active), "accepted_edges": len(edges)},
    }
