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
    window: int | None = None,
) -> dict:
    """One correlation pass.

    vectors: {pod: 1-D signal vector} (one representative signal per pod for v0;
             multi-signal fan-out happens in the caller)
    witness: physical relations from A3/kube-state
    slo_breach: symptom pods to seed root-cause ranking (defaults to pods with onsets)
    caps: optional {pod: limit} for saturation classification
    """
    caps = caps or {}
    # Detect over the FULL ring -- search the whole stored series for a disturbance
    # wherever/whenever it sits, rather than assuming it's in the most recent slice
    # (the data persists; we locate the event by detection, not by the clock). cusum
    # also needs a clean pre-event baseline, which only the full ring provides.
    findings: dict[str, dict] = {}
    onset_s: dict[str, float] = {}
    peak: tuple[float, int] | None = None  # (|zpeak|, idx) of the strongest onset = the event centre
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
        z = max(abs(o["zpeak"]) for o in ons)
        if peak is None or z > peak[0]:
            peak = (z, first["idx"])

    # Correlate on a slice CENTRED on the detected event, not a fixed recent window:
    # the storm dominates the slice (so r isn't diluted) and an event minutes old is
    # still analysed because we found it by detection. Re-detection inside the slice
    # would fail (event lands before cusum's warmup) -- so we keep the full-ring onsets
    # and only narrow the correlation. window=None (fixtures) correlates the full ring.
    cvec = vectors
    if window and peak is not None:
        n = len(next(iter(vectors.values())))
        lo = max(0, min(peak[1] - window // 3, n - window))
        cvec = {p: v[lo:lo + window] for p, v in vectors.items()}

    active = set(findings)
    disturbed = bool(active)  # is anything anomalous at all?  (idle -> no edges)
    edges: list[dict] = []
    for a, b in itertools.combinations(sorted(vectors), 2):
        # Evaluate a pair if it touches an anomalous pod, or -- once the system is
        # disturbed -- if the topology says the two are physically coupled. That pulls
        # a chronically-loaded victim (no clean onset of its own) into the graph by
        # CORRELATION over a shared disk, never by an absolute resource threshold.
        if a not in active and b not in active and not (disturbed and witness.kinds(a, b)):
            continue
        d = best_directed(cvec[a], cvec[b])
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
