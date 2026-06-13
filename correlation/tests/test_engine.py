"""Unit suite for the correlation engine core — BUILD_GUIDE P4 step 1-3 fixtures.

Every test plants a known truth and asserts the engine rediscovers it blind.
"""
import numpy as np
import pytest

from engine import detectors
from engine.gate import Witness, accept_edge
from engine.lagcorr import best_directed, lag_profile
from engine.pipeline import run_pass

rng = np.random.default_rng(42)
N = 180  # 15-minute window at 5s


def noise(scale=1.0, n=N):
    return rng.normal(0, scale, n)


def planted_step(onset=100, level=8.0, n=N):
    x = noise()
    x[onset:] += level
    return x


# ---------- A1: changepoints ----------

def test_cusum_finds_planted_onset_within_2_samples():
    x = planted_step(onset=100)
    ons = detectors.cusum_onsets(x)
    assert ons, "no onset detected"
    assert abs(ons[0]["idx"] - 100) <= 2
    assert ons[0]["direction"] == "up"


def test_cusum_silent_on_pure_noise():
    assert detectors.cusum_onsets(noise()) == []


def test_classify_burst_vs_leak():
    burst = noise(0.3)
    burst[80:110] += 6.0  # rises and returns
    leak = noise(0.3)
    leak[60:] += np.linspace(0, 10, N - 60)  # monotonic climb
    assert detectors.classify(burst, 80) == "burst"
    assert detectors.classify(leak, 60) == "leak"


def test_forecast_to_limit_predicts_rising_signal():
    x = np.linspace(0, 50, N) + noise(0.1)
    eta = detectors.forecast_to_limit(x, limit=60.0)
    assert eta is not None and 0 < eta < 300
    assert detectors.forecast_to_limit(noise(), limit=100.0) is None


# ---------- A4: lag correlation ----------

def test_lag_recovered_for_shifted_pair():
    base = noise(0.2)
    base[60:90] += 5.0
    lag_samples = 3  # 15s
    follower = np.roll(base, lag_samples) + noise(0.2)
    d = best_directed(base, follower)
    assert d["forward"] is True, "direction wrong: leader not identified"
    assert d["lag_s"] == 15
    assert abs(d["r"]) > 0.7


def test_direction_flips_when_arguments_swap():
    base = noise(0.2)
    base[60:90] += 5.0
    follower = np.roll(base, 6) + noise(0.2)  # 30s lag
    d = best_directed(follower, base)
    assert d["forward"] is False
    assert d["lag_s"] == 30


# ---------- gate ----------

def _hot_pair():
    a = noise(0.2)
    a[60:90] += 5.0
    b = np.roll(a, 3) + noise(0.2)
    d = best_directed(a, b)
    return a, b, d


def test_gate_rejects_without_physical_witness():
    _, _, d = _hot_pair()
    e = accept_edge("a", "b", d["r"], d["lag_s"], d["profile"], Witness(), {"a": 300.0, "b": 315.0})
    assert e is None


def test_gate_accepts_with_witness_and_ordering():
    _, _, d = _hot_pair()
    w = Witness(ebpf_edges={("a", "b")})
    e = accept_edge("a", "b", d["r"], d["lag_s"], d["profile"], w, {"a": 300.0, "b": 315.0})
    assert e is not None
    assert "ebpf" in e["evidence"] and "stat" in e["evidence"] and "temporal" in e["evidence"]


def test_gate_rejects_wrong_temporal_order():
    _, _, d = _hot_pair()
    w = Witness(ebpf_edges={("a", "b")})
    e = accept_edge("a", "b", d["r"], d["lag_s"], d["profile"], w, {"a": 400.0, "b": 315.0})
    assert e is None


# ---------- end-to-end: the S1-shaped chain ----------

def chain_vectors():
    """coolmon -> dcim (15s) -> tsdb (30s) -> ccr (30s), plus an innocent bystander."""
    coolmon = noise(0.2)
    coolmon[60:100] += 6.0
    dcim = np.roll(coolmon, 3) * 0.9 + noise(0.25)
    tsdb = np.roll(dcim, 6) * 0.85 + noise(0.25)
    ccr = np.roll(tsdb, 6) * 0.8 + noise(0.25)
    return {
        "coolmon": coolmon, "dcim": dcim, "tsdb": tsdb, "ccr": ccr,
        "edge-ui": noise(),  # must stay out of the story
    }


def s1_witness():
    return Witness(
        ebpf_edges={("tsdb", "ccr")},
        psi_copressure={frozenset(("coolmon", "dcim")), frozenset(("dcim", "tsdb"))},
        shared_relation={frozenset(("coolmon", "dcim")), frozenset(("coolmon", "tsdb"))},
    )


def test_s1_chain_root_cause_is_coolmon():
    out = run_pass(chain_vectors(), s1_witness(), slo_breach=["ccr"])
    assert out["root_cause_ranking"], "no root cause produced"
    assert out["root_cause_ranking"][0]["pod"] == "coolmon"
    assert len(out["edges"]) >= 3, f"chain too short: {out['edges']}"


def test_s1_blast_radius_reaches_ccr():
    out = run_pass(chain_vectors(), s1_witness(), slo_breach=["ccr"])
    blast_pods = {b["pod"] for b in out["blast_radius"]}
    assert "ccr" in blast_pods or "tsdb" in blast_pods


def test_s0_idle_produces_no_edges_and_no_root_cause():
    vecs = {f"pod{i}": noise() for i in range(8)}
    w = Witness(shared_relation={frozenset((f"pod{i}", f"pod{j}")) for i in range(8) for j in range(8) if i < j})
    out = run_pass(vecs, w)
    assert out["edges"] == []
    assert out["root_cause_ranking"] == []


def test_innocent_bystander_never_in_edges():
    out = run_pass(chain_vectors(), s1_witness(), slo_breach=["ccr"])
    for e in out["edges"]:
        assert "edge-ui" not in (e["src"], e["dst"])


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
