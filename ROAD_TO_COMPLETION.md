# ROAD TO COMPLETION — SiliconKnights / ABB Accelerator

> **Status 2026-06-22 (submission day — see BUILD_LOG LOG-093):** ABB submission cut to a clean repo
> (`ABB_Accelerator_Submission`, orphan history, internal docs gitignored). **Live: S0 silent · S1
> disk-causality cascade · S5 OOM forecast · eBPF topology · recommendations (Q4) · scenario console
> (S1/S2/S5 fire + reset) · gemma4 narrator (`e4b-it-qat`).** S2 fires and log-archiver is the dominant
> writer (~40×), but clean root-attribution is **mark-two**: it never self-stalls (async O_DIRECT) and its
> CronJob psi baseline never matures, while LOG-088 quieted timescaledb out of being a victim — physics +
> baseline gap, same family as S3 (LOG-093). Out of scope: S3 (CPU physics), S4 (network/Chaos Mesh),
> DB-restart probe (Q2). **Live env tunes** (cooling-monitor `FIO_RUNTIME/FSYNC/JOBS`, engine
> `FORECAST_MIN_FRAC=0.5`) must be **baked into `values.yaml`/`engine.yaml`** or `skctl up` wipes them.

The forward plan: **what is missing, and what each stage must deliver to close it.** Grounded in a
file-by-file audit of the code against MASTER_PLAN.md (the *what/why*) and BUILD_GUIDE.md (the
*phase path*). This file **supersedes REMAINING.md** (archived to `archive/`).

> Read order: MASTER_PLAN (spec) → EXPLANATIONS (code map) → **this** (what's left) →
> BUILD_GUIDE (verify commands + troubleshooting) → BUILD_LOG (decision history).

The skeleton is complete — L0→L4 are wired and S1 runs end-to-end. This document is the **muscle**:
the breadth the deck promised that the single proven path does not yet cover.

---

## 0. Where we are — the honest baseline

**Built and solid:** the full L0→L4 spine; the S1 PVC-I/O cascade end-to-end, threshold-free,
correct root; the stateful memory + case-library + deviation-baseline engine (this is *beyond* the
original MASTER_PLAN — see DESIGN doc); source attribution via `io_write`; the gemma4 narrator with
a deterministic fallback; the money-shot dashboard (3D causal graph + verdict + a PSI panel).

**The shape of the gap:** the running engine is **single-signal (`psi_io`) and couples only the
shared-disk quartet.** That nails S1 (and likely S2). Everything else the deck advertises —
CPU/memory/network causality, three of the five named agents, the recommendation engine, the full
dashboard, and 3 of the 4 "judge-bait" questions — needs new muscle.

### Completion matrix

| Capability | Promised in | Status | Closes in |
|---|---|---|---|
| L0 factory (15 pods, real faults) | §2.2 | ● built | — |
| Telemetry core (Prom/PSI/kube-state/node-exp) | §1.2 | ● built | — |
| eBPF — Caretta topology map | §1.2 | ✅ built (LOG-080) | — |
| eBPF — OBI/Beyla latency, Inspektor Gadget | §1.2 | ◐ OBI **dropped** (CCR=MQTT, LOG-078); IG on-demand | S4 / future |
| Logs (Loki / Alloy / Drain3) | §1.2 | ○ Alloy CrashLoops | Stage 3 (blocks A2) |
| L2 aggregator + frozen event schema | §1.3 | ● built | — |
| L3 detect→correlate→gate→rank | §1.4 | ● built | — |
| L3 stateful memory + case library | DESIGN | ● built (beyond plan) | — |
| L3 **multi-signal** (psi_io/cpu/mem) | §1.4 | ✅ built (LOG-069) | — |
| L3 same-node PSI coupling (S3 engine) | §1.4.4 | ✅ built (LOG-073, D-015) | — |
| L3 recency reset (fast verdict clear) | — | ✅ built (LOG-071) | — |
| Source attribution (`io_write`) | — | ● built (beyond plan) | — |
| A2 Log Detective (Drain3 + Poisson) | §1.4.1 | ○ not built (needs Loki) | Stage 3 |
| A3 Topology (engine edge-health / ebpf witness) | §1.4.1 | ◐ map built; engine-witness future | Stage 4 (S4) |
| A5 Verdict/Orchestrator + bounded K8s tools | §1.4.1 | ○ not built | Stage 3 |
| OOM forecast (A1 `forecast_to_limit` wired) | §1.4.2 | ✅ built (LOG-085) | — |
| Narrator (gemma4 + template fallback) | §1.5 | ● built (idle=steady, LOG-075) | tune *parked* |
| Recommendation engine (right-size/KAI/fairness) | §1.5.6, §0-Q4 | ✅ built (LOG-082/083) | — |
| Dashboard (launcher/verdict/unified causal+topo graph/PSI/recs) | §1.6 | ◐ ~5 of 6 | Stage 6 |
| Dashboard — timeline replay, pod drawer, PSI heatmap, insight feed | §1.6 | ○ not built | Stage 6 |
| Scenarios S0, S1 | §2.5 | ● built+verified | — |
| Scenario S2 (large-file I/O) | §2.5 | ◐ self-contained bulk + distinct-root wired (LOG-086); box-verify pending | Stage 4 |
| Scenario S3 (CPU, no-net) | §2.5 | ◐ engine done, **physics-blocked** | Stage 4 |
| Scenario S5 (mem leak → OOM) | §2.5 | ◐ forecast wired (LOG-085); box-verify + runbook pending | Stage 4 |
| Scenario S4 (network + retry) | §2.5 | ○ needs Chaos Mesh + net signal | Stage 4 |
| Chaos Mesh conductor | §2.5 | ○ `TODO` in skctl | Stage 4 |
| Rehearsal ledger / accuracy table | §5.4, D-004 | ○ empty header | Stage 4 |
| PVC-I/O↔restart DB probe (PS-Q2) | §2.3 | ○ no DB probe | **NEXT (#3)** |
| Hardening / air-gap / golden run | §5 P8 | ○ not started | Stage 7 |

### The four judge questions (§0) — coverage today and where each lands

| PS question | Today | Delivered by |
|---|---|---|
| Q1 — which pod causes CPU spikes? | ◐ engine multi-signal ready; **S3 physics-blocked** | Stage 4 (S3 node saturation) |
| Q2 — PVC I/O ↔ pod restarts? | ✗ (no DB probe) | **#3** (DB probe + restarts) |
| Q3 — services influencing each other? | ◐ disk ✅ live (S1); CPU engine-ready | S1 live; CPU via S3 physics |
| Q4 — which workloads need optimization? | ✅ live (LOG-082/083) | right-sizing (reclaim/resize) + fairness index |

**Demonstrable live today: Q3-disk (S1) + Q4 (recommendations).** Engine-ready but physics-gated:
Q1 / Q3-CPU (need S3 node saturation, Stage 4). Pending: Q2 (the DB probe, topic #3). So "answers all
four live" needs S3 physics + the DB probe.

---

## Constraints that carry through every stage (non-negotiable)

1. **`run_pass` stays a pure function** — the 13 fixtures in `correlation/tests/test_engine.py`
   must stay green *by construction*. New state/IO lives in `service.py` / `state.py`.
2. **Threshold-free causal path** — edges rest on correlation + physical-witness topology +
   temporal order, never `value > limit`. Resource thresholds remain an L2 alert hint only.
3. **One LLM, at the edge** — the narrator narrates; it never invents causality (D-002).
4. **Tune via env / Helm values, log every change** — code baked into images needs
   `docker build` + `k3s ctr images import` + rollout restart.
5. **Every change gets a BUILD_LOG entry**; rulings get a D-number; reverts link what they undo.
6. **Running is the operator's** — Claude has editorial access; the cluster lives on the home box.
7. **Fast, clear, self-resetting outcomes** — every scenario must light up within ~50s, name a
   single clear root, and **self-reset within ~2–3 min** of the storm ending (the recency gate,
   LOG-071). This holds for S2–S5, not just S1: no lingering hot edges, no ambiguous/empty verdicts.
   Verify the reset timing as part of each scenario's done-when, with the same `RESET_WINDOW`/`DEV_K`
   discipline.

---

## Stage 0 — Engine residual: source-rooted case promotion  *(REMAINING §1 "item 1")*

**Status: DONE (LOG-068) — Tier-0 verified (31/31), box-apply pending (rebuild engine image).**

**Goal.** Stop the occasional wrong-direction case from being learned. **Smallest, pre-agreed, do
first** — it must precede Stage 4 (which mints many more cases).

- **Missing now.** Between storm pulses the live source edge decays to its floor and a stale
  `dcim→timescaledb` psi-only cascade edge can transiently outrank → `_promote_case` promotes a
  wrong-direction case. `DEV_K=4` only masks it.
- **Work items.** In `state.py._promote_case`: promote **only when the ranked root has an outgoing
  source/`write`-evidenced edge** (a real aggressor), not a psi-only cascade. (Alt: prefer source
  over `stat`-only memory edges in ranking — keep as fallback.)
- **Done when.** New `test_state.py` case: a psi-only victim-cascade pass promotes **no** case; a
  source-rooted pass still does. `run_pass` fixtures untouched (13/13). On the box: a multi-pulse S1
  soak grows `cases` only with `cooling-monitor`-rooted entries.
- **Touches.** `correlation/engine/state.py`, `correlation/tests/test_state.py`.
- **Depends on.** Nothing.

---

## Stage 1 — Multi-signal engine (psi_io + psi_cpu + psi_mem)  *(the core enabler)*

**Status: DONE (LOG-069) — local-verified (36/36 + integration smoke), box-apply pending. Decision
settled: one merged graph with a per-edge `signal` tag.** Plumbing + per-signal findings shipped;
cross-resource *edges* arrive with Stage 2's coupling witness (by design — see Done-when).

**Goal.** Generalize the engine from one signal to a resource-class fan-out, so CPU and memory
contention become first-class. **This is the foundational muscle** — S3, S5, and Q1 all sit on it.

- **Missing now.** `service.py` feeds only `psi_io` (+ `io_write`); `psi_cpu`/`psi_mem` are scraped
  but never analyzed. `pipeline.py`'s docstring promises "multi-signal fan-out in the caller" — the
  caller doesn't do it.
- **Work items.**
  - `service.py`: iterate a `SIGNALS` set (`psi_io,psi_cpu,psi_mem`); run one `run_pass` per signal;
    merge outputs into one graph with a per-edge `signal` tag. `state.py` is already keyed by signal
    (one `MemoryConfig.signal`) → instantiate per-signal memory, or extend the key.
  - Source signals per class: `io_write` (disk, built), `container_cpu_usage_seconds_total` (CPU
    aggressor), memory growth/`working_set` (leak source). Add the CPU/mem source queries to
    `queries.yaml` (ConfigMap, no rebuild).
  - Per-signal baselines + deviation gate already supported by `state.baselines` (keyed by
    `(workload, signal)`) — just exercise it per signal.
  - Merge/dedup edges across signals (a pair may couple on cpu *and* io); root-cause ranking runs on
    the merged graph.
- **Done when.** Engine analyzes all signals in `ENGINE_SIGNALS`; `psi_cpu`/`psi_mem` produce
  **findings** and the merged `/graph` tags every edge with its `signal` (`meta.signals` plural);
  S1 still roots cooling-monitor on `psi_io`; the per-signal witness ensures **no false
  cross-resource edges**. (Cross-resource *edges* themselves land in Stage 2, once CPU/mem get a
  coupling witness — disk(pvc) coupling correctly admits only `psi_io` edges.) `run_pass` + its 13
  fixtures untouched; new `test_merge.py` covers the union/tag/rank.
- **Touches.** `correlation/service.py`, `correlation/engine/pipeline.py` (caller-side only),
  `correlation/engine/state.py`, `aggregator/queries.yaml`, `api/main.py` (`signals` plural).
- **Depends on.** Stage 0 (clean promotion before multi-family cases appear).
- **Open decision (D-needed).** Output shape: one merged graph w/ per-edge `signal` tag
  *(recommended)* vs per-signal graphs the UI toggles.

---

## Stage 2 — Witness layer: real topology + the S3 coupling decision

**Status: IN PROGRESS.** Slice 1 DONE (LOG-073, D-015) — same-node PSI coupling for the source-edge
path (S3 drawable via PSI, no eBPF) + the `cpu` per-pod query fix. A false-edge storm found on the
box was fixed (LOG-074): a source edge now requires a real (active) victim, and cpu/mem edges are
purely live (no backbone). Local-verified (40/40 + S1+S3 smoke). **Slice 2 — Caretta topology map
DONE (LOG-077→080):** Caretta Running on kernel 7.0 (@ 1Gi after an OOM), emitting `caretta_links_observed`
(real MQTT/SQL/HTTP L4 flows); `/api/topology` + a dashboard "Discovered topology · eBPF" panel render
the "zero-config, eBPF found every edge" map. **Remaining:** OBI/Beyla `latency_p95` → CCR hop is
**dropped** (LOG-078: CCR actuates over MQTT — not eBPF-instrumentable); beyla RED for the S4 HTTP path
(alert→notify) is a later sub-item; Inspektor Gadget block-io stays on-demand; the engine A3-witness use
of `ebpf_edges` is future (a network signal only — network ≠ disk/cpu coupling).
**Box-physics blocker → Stage 4:** on the 16-thread box a 2-core burst only self-throttles, so
S3 has no real co-resident victim → engine honestly shows nothing. Demonstrating S3 needs the CPU
analogue of D-014 (saturate the node: more burst pods / tighter cpu limits / cpuset).

**Goal.** Replace the static `STORAGE` heuristic with discovered topology, and give the gate a
witness for **CPU contention that has no network edge** (the S3 thesis).

- **Missing now.** `ebpf_edges` is always empty; A3 "topology" is a hard-coded workload list in
  `service.py`. `gate.couples()` accepts only `pvc`/`ebpf`, so **a psi-only / same-node pair can
  never form an edge** — S3 is architecturally blocked. `latency_p95` (CCR 4th hop) needs OBI.
- **Work items.**
  - Land **Caretta** (eBPF service map → `ebpf_edges` + A3 edge-health) — fixes the helm-repo URL
    (LOG-039), confirm CO-RE load on kernel 7.0 (Otterize fallback if it fails).
  - Land **OBI/Beyla** → `latency_p95` for `critical-control-relay` (the S1 4th hop, PS-relevant).
  - **Inspektor Gadget** (per-pod block-IO) → real disk attribution, hardening `io_write`.
  - **S3 coupling:** admit **same-node PSI co-pressure as a coupling witness**, gated by the
    source-attribution guard generalized to CPU (a dominant *cpu-usage* source that deviated and
    leads the co-resident's `psi_cpu` stall). This restores MASTER_PLAN §1.4.4-2b without the
    false-positive blow-up that demoted it (LOG-061).
- **Done when.** `verify_taps --strict` green (Caretta/OBI/Loki); A3 topology ≈ plane-1+2;
  `/graph` draws a CCR latency hop on S1; an S3 dry-run draws a **psi_cpu edge with a "no network
  path" annotation** and zero false edges at idle.
- **Touches.** `deploy/values/{caretta,beyla,alloy}.yaml`, `deploy/skctl`, `correlation/service.py`
  (witness construction), `correlation/engine/gate.py` (psi-coupling guard), `aggregator/queries.yaml`.
- **Depends on.** Stage 1 (psi_cpu must exist before an S3 edge can form).
- **Open decision (D-needed).** S3 witness: re-admit same-node PSI co-pressure *(recommended,
  guarded)* vs add an explicit same-node `shared_relation` vs accept S3 is eBPF-only (note: eBPF
  shows *traffic*, not CPU contention — PSI is the only true witness for S3).
- **Risk.** kernel-7.0 CO-RE eBPF load is still unproven (LOG-020 watch-item). Fallbacks: Otterize
  for flows; PSI-only path needs no eBPF and already works for S1.

---

## Stage 3 — The missing agents: A2, A5, and wiring A1's forecaster

**Goal.** Build the two named agents that don't exist, and turn on the OOM forecast.

- **Missing now.** A2 Log Detective (Drain3) — absent. A5 Verdict/Orchestrator (evidence-weighted
  verdict + bounded read-only K8s tool calls) — absent. `forecast_to_limit()` — dead code (S5's
  "OOM before it happens" beat).
- **Work items.**
  - **Forecaster (A1): DONE (LOG-085).** `engine/forecast.py` (`incipient_findings`, called from
    `service.py`) projects each pod's `working_set` → its memory limit and emits an `incipient` finding
    with ETA; surfaced on `/api/graph` + a model-free `/api/narrative` forecast line. Box-verify of the
    live S5 leak rides Stage 4 (S5 runbook). *(working_set→limit, not psi_mem: a stall has no cap.)*
  - **A2 Log Detective:** once Alloy/Loki are up (Stage 2), Drain3 template mining + Poisson surprise
    + novelty over the Loki window → a `log_error_rate` signal that *corroborates* edges (it already
    exists in the schema enum). Keep it evidence, never a sole edge-maker.
  - **A5 Verdict:** an evidence-weighted scorer over A1–A4 + (stretch) ≤3 bounded read-only K8s tool
    calls (`get_pod_events`, `get_recent_restarts`, IG `top_blockio`) via a read-only ServiceAccount;
    sets final confidence + gates the narrator (the §1.4.6 confidence ≥ 0.5 gate).
- **Done when.** S5 emits an OOM ETA *before* the kill, then confirms; A2 flags an OOM/crash log
  template inside an incident window; A5 confidence appears on `/graph` and gates `/api/narrative`.
- **Touches.** `correlation/engine/{detectors→pipeline}.py`, new `correlation/engine/logdet.py`,
  new `correlation/engine/verdict.py`, `correlation/service.py`, `api/main.py`.
- **Depends on.** Stage 1 (psi_mem for forecast), Stage 2 (Loki for A2).
- **Open decision (D-needed).** A5 scope: evidence-weighted verdict only *(recommended first)* vs
  full HolmesGPT-style bounded tool calls (stretch).

---

## Stage 4 — Scenario library complete + Chaos Mesh + rehearsal ledger  *(P7)*

**Goal.** Make S2–S5 *detected* (not just triggerable), install the conductor, and produce the
accuracy evidence the report needs.

- **Missing now.** Chaos Mesh is a `TODO` in skctl (S4 can't run). S2 unverified; S3/S4/S5 engine
  blind until Stages 1–3. `ledger.csv` is an empty header. No DB probe → S1's restart hop and PS-Q2
  don't exist. S1 runbook params are stale (`fsync=8/runtime=45` vs live `2/60`).
- **Work items.**
  - Install **Chaos Mesh** (containerd socket flag); wire S4 `NetworkChaos` (toxiproxy fallback).
  - Verify **S2** distinct-root from S1; complete **S3** (psi_cpu, no-net edge), **S5** (mem forecast).
  - **S3 physics (LOG-076):** the engine is proven (draws the edge the instant a co-resident
    stalls), but cross-pod CPU contention does not happen on the box. Two faults to fix: (i) a
    `500m`-capped aggressor only **self-throttles** — it physically cannot starve co-residents; the
    hog must actually *consume* cores (high/no cpu limit). (ii) the CPU domain must be small enough
    to saturate. Make the box **edge-like**: a cpuset / reduced allocatable for a contention cell,
    **protecting observability+engine cores** (else the watcher starves with the watched — Risk #4),
    OR a transient full-node saturation burner (no infra, but loads everything ~90s). Self-throttle
    ≠ noisy-neighbor; only real co-resident `psi_cpu` is the differentiator.
  - Mechanize **PVC-I/O ↔ restart** (PS-Q2): a tight `tcpSocket`/`exec` probe on `timescaledb`
    (timeout < fsync stall) so the storm induces a restart; feed `restarts` into the engine as a
    victim signal/evidence.
  - Author S2–S5 **runbooks** (timeline, witnesses, expected NLP, reset); refresh the S1 runbook.
  - Run the **rehearsal ledger** ≥ 35 runs → the precision/recall table vs ground truth (D-004).
- **Done when.** every scenario: fire → detect (~50s) → **single clear root** → narrate →
  **self-reset within ~2–3 min** (constraint 7), no manual kubectl; ledger ≥ 35 rows; S1 chain
  reaches CCR; S0 stays silent across all of it.
- **Touches.** `deploy/skctl` (chaos install), `scenarios/S{2,3,4,5}/{runbook,reset}.md/.sh`,
  `scenarios/ledger.csv`, `deploy/charts/factory/{values.yaml,templates/workloads.yaml}` (DB probe).
- **Depends on.** Stages 1–3.

---

## Stage 5 — Recommendation engine  *(PS-Q4, §1.5.6)*

**Status: DONE (LOG-082), local-verified (helper sanity + dashboard build), box-apply pending.** `GET
/api/recommendations` = right-sizing (p95 vs requests/limits → reclaim/resize in KAI verbs) + per-ns
fairness (Gini over PSI stall); dashboard "Recommendations · right-sizing" panel (30s poll). Reuses
`PROM_URL`. Deferred (optional): feed the card text into `/api/narrative` + `cases.remediation`;
`consolidate`/`throttle` verbs tied to a causal root.

**Goal.** Answer "which workloads need optimization?" — the one judge question with no machinery.

- **Missing now.** No right-sizing, no KAI scheduler-verb cards, no fairness index; `cases.remediation`
  is never populated; the narrator prompt asks for no remediation.
- **Work items.**
  - Deterministic **right-sizing** pass: p95 usage vs requests/limits → "reclaim 0.9 CPU from
    analytics-batch", in KAI verbs (reclaim / consolidate / throttle / resize).
  - **Fairness index** per namespace (Gini over PSI stall time) — a header widget number.
  - Feed the card text into `/api/narrative` (remediation sentence) and into `cases.remediation`
    (so "throttling X resolved it" accrues with recurrence).
- **Done when.** `/api/recommendations` returns per-workload right-sizing in scheduler verbs; the
  verdict card shows a remediation line; fairness index renders.
- **Touches.** new `api/` endpoint (or a small L3 pass), `aggregator/queries.yaml` (requests/limits
  via kube-state), `correlation/engine/state.py` (remediation accrual), `dashboard/`.
- **Depends on.** Stage 1 (multi-resource usage). Largely parallelizable.

---

## Stage 6 — Dashboard completion  *(P6 full — §1.6 six panels)*

**Goal.** Grow from money-shot to the full operator console.

- **Missing now.** ~3 of 6 panels. Absent: incident **timeline + replay slider**; **pod detail
  drawer** (8 sparklines incl. PSI + restarts + evidence links); full **PSI heatmap** (pods ×
  {cpu,mem,io}, not one psi_io panel); **AI insight feed** with evidence links + remediation; full
  **scenario console** (S2–S5 buttons, not S1-only).
- **Work items.** Build the four missing panels against existing API seams (`/api/signal/{pod}`,
  `/api/events`, `/api/graph` findings, new `/api/recommendations`); wire S2–S5 trigger buttons
  (extend `/api/scenarios/{id}/trigger` beyond S1); fairness-index header widget.
- **Done when.** all six §1.6 panels live; evidence links open the drawer at the cited window;
  S2–S5 fire from buttons; 30-min soak, no WS/memory leak.
- **Touches.** `dashboard/app/*`, `api/main.py` (scenario triggers, recommendations).
- **Depends on.** Stages 1, 4, 5 for the data each panel shows.

---

## Stage 7 — Hardening, air-gap, demo  *(P8)*

**Goal.** Make it demo-proof.

- **Missing now.** No soak/prune; unbounded `graph_snapshots`/`case_observations` growth; no image
  digest pinning; no air-gap tarball rehearsal on a wiped box; no golden-run video.
- **Work items.** prune/cap the memory tables; confirm baseline+memory survive pod restarts; disable
  build-time Grafana extras; pin digests; build + test the `k3s ctr images import` tarball on a wiped
  snapshot (WiFi-off S1); dress rehearsal ×5; record the golden run.
- **Done when.** MASTER_PLAN §5.4 checklist fully ticked; air-gap S1 clean; golden video recorded.
- **Touches.** `deploy/*`, `correlation/engine/state.py` (retention), `appendix/*`.
- **Depends on.** Everything.

---

## Docs workstream  *(continuous — runs alongside, per operator request)*

- **Root `README.md`** — currently absent in this tree (QUICKSTART references one). Author it.
- **Per-component READMEs ("component dive")** — one per `workloads/*`, plus `aggregator/`,
  `correlation/`, `api/`, `dashboard/`: what it is, its contract, its knobs, how to rebuild. Rewrite
  the stale `agents/README.md` (it describes a LangGraph layout that was never built).
- **Refresh actives** — EXPLANATIONS §4 (L4 is built, not "planned"); BUILD_GUIDE status lines
  (P5/P6 done, P7/P8 framing → point at this doc); S1 runbook params.
- **Technical report** — assemble from MASTER_PLAN + BUILD_LOG + ledger + golden stills (P8).

---

## Critical path & sequencing

```
Stage 0 (residual)  →  Stage 1 (multi-signal)  →  Stage 2 (witnesses/eBPF)  →  Stage 3 (A2/A5/forecast)
                                                          │
                                                          └→  Stage 4 (scenarios + chaos + ledger)
Stage 5 (recommendation) ── parallelizable after Stage 1 ──┐
                                                           ├→  Stage 6 (dashboard)  →  Stage 7 (hardening/demo)
Docs workstream ── continuous throughout ──────────────────┘
```

**Recommended order:** 0 → 1 → 2 → 3 → 4, with 5 in parallel once 1 lands, then 6 → 7. Docs trail
each stage (write the component README when you finish touching that component). Branches per
REMAINING strategy: **mark-zero** = baseline `1d4315a`; **mark-one** = current corrected engine;
cut **mark-two** for the time-store after the build is complete.

## Open design decisions (need your call before the stage starts)

1. **Stage 1** — multi-signal output: one merged graph w/ per-edge `signal` tag *(recommended)* vs
   per-signal graphs.
2. **Stage 2** — S3 witness: re-admit guarded same-node PSI co-pressure as coupling *(recommended)*
   vs explicit same-node `shared_relation` vs eBPF-only (won't see CPU contention).
3. **Stage 3** — A5 scope: evidence-weighted verdict only *(recommended first)* vs full bounded
   K8s tool calls.
4. **Stage 5** — recommendation source: deterministic right-sizing from live Prometheus
   *(recommended, §1.5.6)* vs from case-library remediation history.

## Parked (non-blocking, revisit anytime)

- **LLM verdict (gemma4) prose fine-tuning.** The deterministic verdict + the always-on template
  fallback work; the *narrated sentence* wording/grounding can be sharpened (tone, resource
  phrasing, citing evidence/ETA cleanly). Operator call: "later, anytime." Not on the critical
  path — the demo never depends on the model (P5/LOG-066). Idle no-contention now resolved (LOG-075:
  narrator returns "steady" with no root, skips the LLM). **Operator goal: tune gemma4 so an
  *incident* verdict reliably renders via the model (minimize fallback to the template).** Note the
  idle "steady" line is template-**by-design** (we skip the model when there's no root — that's not a
  fallback failure); the real tuning target is incident-prose reliability/quality + prompt grounding.
- **CPU usage-coupling backbone (the CPU "Case 0").** CPU has no *stall* backbone (psi_cpu is 0
  until saturation), but CPU **usage** is constant and coupled in a real edge system (the pipeline:
  plc→ingest→db→…). Learn a usage-correlation backbone (observed, not the earlier hypothetical
  ghost-map) so the CPU view has a meaningful idle state and source attribution sharpens. Additive;
  contention determination stays stall-based (`same_node` witness). Decomposition to remember:
  **usage finds the source, stall finds the victim — need both** (LOG-076).

---

*ROAD v1 — 2026-06-20. Supersedes REMAINING.md. Update via BUILD_LOG entries; revise stages as they
close.*
