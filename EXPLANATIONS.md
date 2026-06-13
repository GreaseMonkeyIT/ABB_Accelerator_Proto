# EXPLANATIONS — session journal, human register

When Soumyadip asks "explain what we did/are doing," the answer gets logged here, timestamped,
tied to the question asked. Register (set 2026-06-12): **keep the technical terms — pods, PVC,
CUSUM, Pearson, eBPF, PSI — but explain in narrative**, the way the pod-mesh walkthrough did
("the post office every message passes through"). Not spec-dumps, not babytalk. The technical
references live in MASTER_PLAN.md / BUILD_GUIDE.md / BUILD_LOG.md; this file is the human track.
Newest entries at the bottom.

---

## 2026-06-12 · 11:14 UTC · Q: "explain what we just did" (after the first build + test round; rewritten 11:25 to the corrected register)

**What the engine is.** Four Python modules in `correlation/` that together answer "who caused this." `detectors.py` watches each pod's signal as a 5-second time series: an EWMA tracks what normal looks like, a CUSUM accumulates drift away from normal and fires only when the drift is *sustained* — giving an onset timestamp accurate to one sample. A classifier then names the shape: burst (rises, returns), leak (keeps climbing), saturation (pinned at a limit), flap (oscillation — restart loops). `lagcorr.py` takes two pods' vectors and computes Pearson r at shifted alignments — 0/5/15/30/60/120s. If cooling-monitor's I/O at time T matches dcim-bridge's write latency at T+15s with r≈0.99, that's a lagged relationship, and the shift direction says who leads. `gate.py` is the discipline: correlation alone never creates an edge — it needs strength at the peak lag *and* a neighboring lag (kills flukes), plus a physical witness (an eBPF-seen connection, PSI showing both pods stalled on the same resource on the same node, or a shared PVC), plus correct temporal order. `ranking.py` scores each pod by how much downstream damage it explains, walking accepted edges forward with decaying weight — top score is the root cause; the same walk yields the blast radius with ETAs.

**How we tested it with no cluster.** The engine is pure math on arrays, so it needs honest inputs, not hardware. Every test plants a truth: a step at sample 100 (detector must land within 2 samples), a signal copied and shifted 15s (correlator must recover that exact lag *and* direction), a synthetic S1 — cooling-monitor's burst echoed into dcim → tsdb → ccr at 15/30/30s with an innocent edge-ui placed as bait — and eight pods of pure noise where the only correct output is silence.

**The two bugs the tests caught.** CUSUM measured its noise floor from just 12 samples; on compound-noise signals that under-measures, so ordinary jitter looked like 4-sigma events and the detector hallucinated onsets — the gate then *correctly* rejected the downstream edges because the timestamps were lies. Detector fixed (longer quiet prefix), gate vindicated. And ranking originally used personalized PageRank seeded at the suffering pod — flaw: the seed keeps the restart probability mass, so ccr the *victim* outranked cooling-monitor its *cause*. Replaced with explanatory reach: walk forward from each candidate, sum the symptoms it explains, penalize anyone who's themselves explained from upstream.

**The laptop checks (Tier-1).** pytest 13/13 on WSL2 (Python 3.12 vs the build's 3.10 — both ends covered). `helm template` → exactly 28 manifests (13 Deployments, 2 CronJobs, 11 Services, 2 PVCs) — the chart's switch logic, storage-domain podAffinity, and tmpfs volume all render into legal Kubernetes objects. `go build` × 6 first-try — dependencies resolve, code structurally sound.

**Net position.** L3 verified at unit level, L0 compiles, chart renders, L2 event schema frozen. What remains untestable without a real kernel — PSI, eBPF, genuine disk contention — is exactly what the desktop provides. Queue unchanged: P0 install → P1 images → P2 taps.

## 2026-06-12 · ~11:40 UTC · Q: "so the pods don't exist yet; tested against simulated data?"

Yes. The pods exist as source code + Dockerfiles — verified grammar, never run; no images built, no cluster. The engine was tested against synthetic numpy arrays *shaped like* what the pods are designed to produce (a hand-built cooling-monitor flood, time-delayed copies playing dcim/tsdb/ccr, noise for the innocents). Proven: given honest inputs, the math reaches the right verdict. Not proven: that real telemetry resembles the clean fixtures — real scrapes have jitter and gaps, and the collection pipeline hasn't carried a single live sample. Closure path, in order: replay harness (realistically messy synthetic data through the real L2→L3 contract, still cluster-free), then live fire on the desktop (P4 step 7: real S1 caught ≥8/10 before the engine is "done").

## 2026-06-12 · ~11:50 UTC · Q: "we write code here, sync, changes reflect there, test and improve?"

Yes — write here → Syncthing to the desktop in seconds → run against the cluster → results sync back (ledger/test files) or get pasted in chat → fix → repeat. Git keeps history; Syncthing moves the working copy. The one subtlety: sync ≠ deploy for everything. The Python engine runs from source, so sync *is* deploy (seconds). Pods run baked container images — a synced edit touches nothing live until `docker build` + image import + rollout restart (minutes; Makefile wraps it at P1). Go services sit in between: run the binary directly during dev, containerize when stable. Discipline: commits from one side at a time; the desktop treats the folder as runtime, we treat it as the writing desk.

## 2026-06-13 · ~00:15 IST · Q: "no restarts is good or bad?" (during P1 soak)

Good — zero restarts is the soak's pass criterion; a healthy factory at rest is boring. The twist: restarts aren't villains, *uninvited* ones are. S5 manufactures OOM-kill restarts (vision-qc leak vs its 512Mi limit) and S1 can restart timescaledb via probe timeouts under disk contention — the engineered "PVC I/O ↔ restarts" link from the problem statement. Restart counters are one of the engine's eight input signals precisely because a restart is a loud symptom. Rule: zero restarts at rest, restarts only on command, every restart explainable.

## 2026-06-13 · ~14:00 · Q: "from the ground up — which layers are enacted, what's each component, how do they work?"

**What's running vs built.** Two layers are *live on the cluster* — L0 (the factory) and L1 (telemetry, core). L2 (the Go aggregator) and L3's math kernel are *written and unit-tested* but not yet deployed. L4 (local-LLM narrator + dashboard) isn't built. So the **generation→collection** half is real; the **interpretation** half exists as verified code waiting to be plugged in.

**L0 — the factory (15 pods we watch).** A miniature smart-factory across three namespaces. plc-gateway fakes 200 sensors and publishes to **mqtt-broker** (Mosquitto) at 10 Hz; **telemetry-ingest** drains the broker and batch-INSERTs into **timescaledb** (a 14-day compressed rolling store). **critical-control-relay** is the latency-sensitive actuator with a 100 ms SLO — the pod every cascade eventually hurts; **safety-interlock** trips to safe-mode if CCR's heartbeat misses. The storage trio share one physical disk: **cooling-monitor** journals thermal logs and, on trigger, unleashes the fio storm; **dcim-bridge** writes to the *same* PVC (first victim); **log-archiver** tars on demand. **analytics-batch** does CPU-heavy rollups on demand; **vision-qc** "detects defects" and, on trigger, leaks memory to OOM. The edge tier (alert-dispatcher, notify-gateway, edge-ui, firmware-cache) raises alerts and serves the kiosk. Honesty rule: every fault is a *real kernel mechanism* — fsync storms, CFS throttling, the OOM-killer — never a faked number.

**L1 — telemetry (how we watch, zero app instrumentation).** Prometheus scrapes the kubelet's built-in **cAdvisor** every 5 s for per-container CPU, memory, throttling, and — the differentiator — **PSI**: the kernel's own "this pod is *stalled waiting* for CPU/mem/IO" counter. **kube-state-metrics** adds restarts/OOM-reasons/PVC claims; **node-exporter** adds disk-busy + network retransmits. A `channel=truth` tag fences the apps' own metrics out of the engine's view, keeping "zero instrumentation" honest. (The eBPF add-ons — Caretta's who-talks-to-whom map, OBI's request latency, Alloy's log shipping — are installed but not yet emitting; the open kernel-7.0 item.)

**L2 — aggregator (built, not yet deployed).** A small Go service: runs ~12 PromQL queries every 5 s, normalizes the answers into one frozen JSON "event" shape, raises an `anomaly_candidate` when a signal crosses a threshold, and keeps a 15-minute per-pod history at `/window` for the brain to read.

**L3 — engine (math kernel built + unit-tested, not deployed).** The deterministic detective: spot each pod's onset (EWMA+CUSUM), correlate pods at time-lags, **gate** an edge only with physical evidence (PSI co-stall / eBPF link / shared PVC) *and* correct time order, rank the root cause by how much downstream damage it explains, forecast who's next. No LLM in this core.

**How it works today, proven.** Trigger S1 → cooling-monitor floods the shared disk → the kernel marks **timescaledb** (a *different* pod) IO-stalled → Prometheus scrapes that PSI → we watched timescaledb cross 0.22. The whole chain — fault in L0, seen blind by L1 — works end to end with nothing instrumented inside the apps. L2 would turn that spike into an event; L3 would pin it on cooling-monitor. Those two are coded and tested, next to be wired live.
