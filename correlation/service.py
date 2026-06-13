#!/usr/bin/env python3
"""L3 correlation service (P4).

Polls the L2 aggregator's /window (per-pod signal vectors) and /events (anomaly
seeds), builds the engine inputs, runs one deterministic pass, and serves the
latest CausalGraph at /graph. No language model anywhere in this process; the
single LLM lives at L4.

v0 witness construction (until Caretta/OBI land): shared-storage relations come
from the known storage-domain workloads (one physical disk via local-path), and
PSI co-pressure comes from pods whose signal is elevated in the same window.
"""
import json
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np

from engine.gate import Witness
from engine.pipeline import run_pass

WINDOW_URL = os.environ.get("WINDOW_URL", "http://aggregator.aiops.svc:9000/window")
EVENTS_URL = os.environ.get("EVENTS_URL", "http://aggregator.aiops.svc:9000/events")
SIGNAL     = os.environ.get("ENGINE_SIGNAL", "psi_io")          # representative signal for v0
INTERVAL   = int(os.environ.get("ENGINE_INTERVAL", "10"))        # seconds between passes
PORT       = int(os.environ.get("ENGINE_PORT", "9100"))
COPR_MIN   = float(os.environ.get("COPRESSURE_MIN", "0.10"))     # signal level that counts as "stalled"
STORAGE    = [s.strip() for s in os.environ.get(
    "STORAGE_WORKLOADS", "cooling-monitor,dcim-bridge,log-archiver,timescaledb").split(",")]

_lock = threading.Lock()
_graph = {"meta": {"status": "starting"}}


def _fetch(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.load(r)


def workload(pod):
    """cooling-monitor-59584cbf7d-6szhd -> cooling-monitor (drop replicaset + pod hash)."""
    parts = pod.split("-")
    return "-".join(parts[:-2]) if len(parts) > 2 else pod


def build_inputs(window, events):
    """window: {ns/pod/signal: [{ts,pod,namespace,signal,value}, ...]}  ->  (vectors, witness, breach)."""
    vectors = {}
    for key, samples in window.items():
        parts = key.split("/")
        if len(parts) < 3 or parts[-1] != SIGNAL or not samples:
            continue
        vals = [s["value"] for s in samples]
        if len(vals) >= 12:
            vectors[parts[1]] = np.asarray(vals, dtype=float)

    pods = list(vectors)
    shared, copr = set(), set()
    hot = [p for p in pods if float(np.max(vectors[p][-6:])) > COPR_MIN]
    for i in range(len(pods)):
        for j in range(i + 1, len(pods)):
            a, b = pods[i], pods[j]
            if workload(a) in STORAGE and workload(b) in STORAGE:
                shared.add(frozenset((a, b)))            # same physical disk (local-path)
    for i in range(len(hot)):
        for j in range(i + 1, len(hot)):
            copr.add(frozenset((hot[i], hot[j])))        # single node => same PSI domain

    witness = Witness(ebpf_edges=set(), psi_copressure=copr, shared_relation=shared)
    breach = sorted({e["pod"] for e in events if isinstance(e, dict) and e.get("kind") == "anomaly_candidate"})
    return vectors, witness, breach


def loop():
    global _graph
    while True:
        try:
            window = _fetch(WINDOW_URL)
            events = _fetch(EVENTS_URL)
            vectors, witness, breach = build_inputs(window, events)
            if vectors:
                out = run_pass(vectors, witness, slo_breach=breach or None)
                out["meta"]["signal"] = SIGNAL
                out["meta"]["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                with _lock:
                    _graph = out
        except Exception as e:  # never die; report the error on /graph
            with _lock:
                _graph = {"meta": {"status": "error", "error": str(e)}}
        time.sleep(INTERVAL)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, b"ok\n")
        if self.path.rstrip("/") in ("", "/graph"):
            with _lock:
                return self._send(200, json.dumps(_graph).encode(), "application/json")
        self._send(404, b"not found\n")

    def _send(self, code, body, ctype="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def main():
    threading.Thread(target=loop, daemon=True).start()
    print(f"correlation engine up on :{PORT}; window={WINDOW_URL} signal={SIGNAL}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
