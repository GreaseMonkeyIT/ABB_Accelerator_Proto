"""Evidence acceptance gate — MASTER_PLAN section 1.4.4. The false-positive killer.

An edge enters the causal graph only if ALL THREE clauses hold:
  1. statistical: |r| >= R_PEAK at peak AND elevated at an adjacent lag window
  2. physical witness: ebpf | psi (same node) | pvc/same-node relation
  3. temporal: src onset precedes dst onset, consistent with the lag
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .lagcorr import adjacent_support

R_PEAK = 0.6
R_ADJ = 0.4
TEMPORAL_TOL_S = 10.0  # one-2 samples of slack on onset ordering


@dataclass
class Witness:
    """Physical relationships known to the topology agent (A3)."""

    ebpf_edges: set[tuple[str, str]] = field(default_factory=set)  # directed (src, dst)
    psi_copressure: set[frozenset] = field(default_factory=set)    # {frozenset({a,b})} same node+resource
    shared_relation: set[frozenset] = field(default_factory=set)   # shared PVC / same node

    def kinds(self, src: str, dst: str) -> list[str]:
        out = []
        if (src, dst) in self.ebpf_edges or (dst, src) in self.ebpf_edges:
            out.append("ebpf")
        if frozenset((src, dst)) in self.psi_copressure:
            out.append("psi")
        if frozenset((src, dst)) in self.shared_relation:
            out.append("pvc")
        return out


def accept_edge(
    src: str,
    dst: str,
    r: float,
    lag_s: int,
    profile: dict[int, float],
    witness: Witness,
    onset_s: dict[str, float],
) -> dict | None:
    """Apply the three-clause gate. Returns edge dict with evidence list, or None."""
    # clause 1 - statistical
    if abs(r) < R_PEAK or not adjacent_support(profile, lag_s, R_ADJ):
        return None
    # clause 2 - physical witness
    kinds = witness.kinds(src, dst)
    if not kinds:
        return None
    # clause 3 - temporal precedence (only checkable when both onsets exist)
    t_src, t_dst = onset_s.get(src), onset_s.get(dst)
    if t_src is not None and t_dst is not None:
        if t_src > t_dst + TEMPORAL_TOL_S:
            return None
        if lag_s > 0 and (t_dst - t_src) > 4 * lag_s + TEMPORAL_TOL_S:
            return None  # onsets too far apart to be this edge
    evidence = ["stat"] + kinds + (["temporal"] if t_src is not None and t_dst is not None else [])
    return {"src": src, "dst": dst, "r": round(float(r), 3), "lag_s": int(lag_s), "evidence": evidence}
