# BUILD LOG — SiliconKnights / ABB Accelerator Round 2

Append-only journal. Newest entries at the bottom. Never edit old entries — if an entry was wrong, add a new entry that corrects it and link back.

**Entry format:**

```
## LOG-NNN · YYYY-MM-DD · TYPE
What: one or two sentences — the step taken / decision made / thing reverted.
Why:  the reason, in plain words. For reverts: what we believed before, what changed our mind.
Impact: files/components touched; what someone else must now do differently.
Links: doc sections, commits, scenario IDs, previous LOG entries.
```

**TYPE is one of:** `STEP` (work done) · `DECISION` (a ruling, gets a D-number) · `REVERT` (undoing a prior step/decision, must link it) · `BLOCKER` (stuck, with symptom) · `FIX` (blocker resolved, with root cause) · `NOTE` (observation worth remembering).

**Decision register (running index):**

| ID | Decision | Status | Entry |
|---|---|---|---|
| D-001 | Metrics store: **Prometheus primary**, VictoriaMetrics as documented contingency | Active (reverts MASTER_PLAN v1.0 ruling) | LOG-002 |
| D-002 | L3 agents are **inference engines first**; exactly one LLM, at the language edge | Active | LOG-003 |
| D-003 | Demo substrate: Ubuntu VM (Hyper-V/VirtualBox) on the Windows laptop, **not WSL2** | Active (D-009 amendment withdrawn, LOG-013) | LOG-004 |
| D-004 | Ground-truth channel: L0 app `/metrics` exist but are **never fed to the correlation engine** — used only to score detection accuracy | Active | LOG-004 |
| D-005 | Pods divide across machines by affinity group, never arbitrary equal count | Partially superseded by D-006 (affinity-group rule survives; prescriptive laptop mapping removed) | LOG-006 |
| D-006 | **Machine-agnostic packaging**: one umbrella + component switches; solo mode (all-on, one box) or deferred/fleet mode (turn groups on per laptop, same LAN); GPU opportunistic, never required | Active | LOG-007 |
| D-007 | Primary build host = Linux desktop (i7-10700/16 GB, headless Ubuntu Server); 8 GB VMs dev-only; `language` switch accepts external OLLAMA_HOST | Active | LOG-009 |
| D-008 | Remote topology: Tailscale mesh; Syncthing for working-copy sync (git = truth); home PC never joins an AIC-side fleet cluster | Active | LOG-011 |
| D-009 | Profiles (`full`/`lite`), witness tiers, Loki-less lite log path | **Withdrawn** (LOG-013) — single full design only; WSL2 back to dev-only per D-003 | LOG-012, LOG-013 |
| D-010 | Root-cause ranking = **explanatory reach**, not personalized PageRank (symptom-seeded PageRank mis-ranks the symptom above its own cause) | Active | LOG-014 |
| D-011 | Remote power-on via **cloud smart plug** + AC-BACK=Always-On (WoL armed but board firmware ignores the S5 magic packet) | Active | LOG-021 |
| D-012 | `skctl --components` is **exclusive**; solo mode always runs `skctl up` (all groups on); every PVC carries `helm.sh/resource-policy: keep` so a workload toggle can never delete data | Active | LOG-025 |
| D-013 | **14-day raw telemetry window**: tsdb-pvc 8Gi→64Gi + TimescaleDB compression (1h chunks) + 14-day retention policy in init.sql | Active | LOG-029 |

---

## LOG-001 · 2026-06-12 · STEP
What: MASTER_PLAN.md v1.0 written — architecture L0–L4, 15-pod factory roster, scenario library S0–S5, competitive matrix, KAI/HAMi/Koordinator research synthesis, 14-day plan.
Why: single source of truth for the Round 2 build; deck promises mapped to demo proofs.
Impact: all components now have a normative reference.
Links: MASTER_PLAN.md (all sections).

## LOG-002 · 2026-06-12 · DECISION + REVERT (D-001)
What: Metrics store ruling reversed: **Prometheus (kube-prometheus-stack, tuned) is primary**; VictoriaMetrics demoted to contingency swap. MASTER_PLAN v1.0 had ruled VM primary.
Why: v1.0 chose VM for RAM savings (3–4× at scale). On re-examination for *our* scale (~15 L0 pods + infra, ≤ 50k active series, 12h retention), Prometheus fits in ~600–800 MB — the savings (~400 MB) don't buy enough to justify: (a) deviation from the deck judges already accepted, (b) MetricsQL/PromQL edge-case differences and different staleness semantics, (c) a second alerting path (vmalert) instead of the battle-tested kube-prometheus-stack bundle. VM remains scrape-config-compatible, so the swap stays a half-day contingency if RAM gets tight on the demo box.
Impact: MASTER_PLAN §1.0 diagram, §1.2 table + ruling, §1.7 RAM budget, §4.6 synthesis row, §5.2 Day-1 milestone all updated. Helm: use `kube-prometheus-stack` with values from BUILD_GUIDE P2.
Links: MASTER_PLAN §1.2; BUILD_GUIDE §P2; supersedes the VM ruling in LOG-001's v1.0.

## LOG-003 · 2026-06-12 · DECISION (D-002)
What: Multi-agent layer redefined as **inference-first**: Resource, Log Detective, Network/Topology, and Orchestrator agents are deterministic/statistical inference engines (changepoint detection, log template mining, graph algorithms, evidence-weighted scoring) with **no LLM in their loop**. Exactly one LLM (Ollama, 4B-class) sits at the language edge: narrate the verdict, draft remediation text. Template fallback if the model misbehaves.
Why: (a) "AI agent" ≠ "LLM call" — an agent that parameterizes and categorizes threats itself is better served by engines that are fast, deterministic, and explainable; (b) reliability: statistical engines don't hallucinate and rehearse identically every run; (c) RAM/latency: model can stay cold until an incident warms it; (d) the deck's claims (LSTM anomaly detection, correlation engine, root-cause ranking) were always non-LLM math — this makes the architecture honest about it.
Impact: MASTER_PLAN §1.4 fully rewritten (now the single "Correlation & Dependency Engine" section), §1.5 reduced to "the language layer"; RAM budget eases; demo determinism up.
Links: MASTER_PLAN §1.4, §1.5; BUILD_GUIDE §P4–P5.

## LOG-004 · 2026-06-12 · STEP + DECISIONS (D-003, D-004)
What: Added pod **mesh design** (data / storage / observation planes with metric tap points) and **deployment footprint requirements** (solo-laptop and multi-node) to MASTER_PLAN §2.7–2.8. Two embedded rulings: D-003 demo substrate = Ubuntu VM, not WSL2 (eBPF/BTF, cgroup-v2 PSI, and K3s-systemd friction risks); D-004 L0 app metrics are ground-truth only — correlation engine consumes exclusively kernel/K8s/eBPF signals, so the zero-instrumentation claim stays honest and we can publish precision/recall in the report.
Why: requested design clarity before build start; multi-node must not break the single-node demo (affinity rules + per-node evidence scoping specified).
Impact: §2.7, §2.8 added; correlation engine gains rule "PSI co-pressure evidence valid only within one node"; BUILD_GUIDE P0 lists the exact laptop prep.
Links: MASTER_PLAN §2.7–2.8, §1.4.4; BUILD_GUIDE §P0.

## LOG-005 · 2026-06-12 · STEP
What: BUILD_GUIDE.md v1.0 created — component-by-component build path P0→P8, each with done-when checkpoints, verify commands, troubleshooting, and rollback notes. BUILD_LOG.md (this file) established with decision register.
Why: requested navigation aids: "guide us when lost, log every step and revert."
Impact: working agreement — every build session starts by reading the last 3 LOG entries, ends by appending one.
Links: BUILD_GUIDE.md.

## LOG-006 · 2026-06-12 · STEP + DECISION (D-005)
What: Pod resource spec v1 frozen (per-pod requests/limits table, MASTER_PLAN §2.2): L0 totals 1.85 cores requested / 5.45 cores limit, ≈2.7 Gi memory requested. And Footprint C added (§2.8): 4-laptop fleet topology — K3s server+framework on the i7-14700HX/32 GB machine; agents host three affinity-grouped sets (core spine / storage-contention domain / compute-interference domain). Ruling D-005: pods divide across laptops **by affinity group, not arbitrary equal count** — S1 and S3 are same-node-by-physics (shared disk, shared CFS/PSI domain); the grouping happens to yield a near-equal 4/4/4/3 split anyway.
Why: team asked for per-pod specs and the 4-laptop scenario. Arbitrary splits silently destroy the contention scenarios; declared affinity makes the same Helm chart valid for 1 node and 4.
Impact: Helm values gain per-group nodeSelector/affinity blocks; S3's victim changes from CCR to telemetry-ingest/alert-dispatcher when fleet mode is on (CCR lives on another node — cross-node CPU interference doesn't exist, which we narrate as a feature). GPU (RTX 3050) noted as dual-boot-only stretch for Ollama; CPU-only remains the plan.
Links: MASTER_PLAN §2.2 (spec table), §2.8 Footprint C; D-002 (cold-LLM makes CPU-only viable).

## LOG-007 · 2026-06-12 · DECISION + REVERT (D-006, amends D-005)
What: Footprint C rewritten machine-agnostically. LOG-006's prescriptive laptop mapping (laptop A=framework, B=core, …) is withdrawn — the package must not know machine names. New shape: one Helm umbrella + bootstrap (`skctl`), nine **component switches** (workloads-core/storage/compute/edge, telemetry, engine, language, dashboard, chaos). Solo mode = all switches on one box; deferred/fleet mode = same installer on every LAN laptop, first up becomes K3s seed, each box just flips its switches on. Affinity binds groups to *each other* (D-005's surviving rule), singleton PVCs pin to whichever node enabled their switch, scenarios self-resolve to wherever their workload group lives. GPU correction: the i7-14700HX machine has an **RTX 4060 8 GB** — 8B Q4 fits wholly in VRAM; Ollama chart auto-detects NVIDIA runtime (bare-metal/dual-boot only), CPU path remains the guarantee.
Why: team direction — "design machine-agnostic, don't split workloads for us; final package runs entirely on one machine, or components are simply turned on per laptop."
Impact: Helm values restructure (per-group `enabled` flags + group affinity); D-005's laptop table deleted from MASTER_PLAN; demo-day role assignment becomes a logistics choice.
Links: MASTER_PLAN §2.8 Footprint C; supersedes the mapping half of LOG-006 (D-005).

## LOG-008 · 2026-06-12 · NOTE
What: WSL2 role clarified — banned as a *cluster node* (D-003 stands: PSI usually absent from the stock WSL2 kernel, eBPF/BTF variance, NAT networking blocks fleet-mode LAN join), but **fine as a dev shell** for writing code, building images, and running Claude Code. Dev workflow set: repo on git (shared by all 4); design/docs via Cowork on Windows host; hands-on cluster work via **Claude Code inside the Ubuntu VM** (Linux-native CLI). Quick disqualifier anyone can run in WSL2: `cat /proc/pressure/cpu` — if missing, that machine's WSL2 can't host the demo, no debate needed.
Why: team asked whether WSL2 is truly out, and how to keep Claude in the loop on Linux.
Impact: BUILD_GUIDE P0 unchanged; add `git init` + remote as a Day-1 step.
Links: D-003 (LOG-004); BUILD_GUIDE §P0.

## LOG-009 · 2026-06-12 · DECISION (D-007)
What: Primary build host = the **Linux desktop** (i7-10700, 8c/16t, 16 GB) running **headless Ubuntu Server** (no desktop environment, no VNC — SSH + kubectl-over-LAN + the dashboard is a browser tab; a GUI would burn ~1–1.5 GB for nothing). It becomes the K3s seed and the solo-mode reference box; bare metal means full PSI/eBPF with no VM tax and ~15 GB truly usable — the §1.7 budget fits with real headroom. Laptops = dev machines (WSL2/VM fine for coding). **8 GB VMs are dev-only**: full stack minus LLM ≈ 7.2–7.5 GB incl. OS = ~92% of 8 GB — kernel OOM risk and page-cache starvation that would distort the very I/O scenarios we demo. Packaging addition: the `language` switch gains an `external OLLAMA_HOST` option — Ollama may run *outside* the cluster (e.g., on a Windows gaming laptop's RTX 3050/4060, model fully in VRAM) and the NLP layer just points at it over LAN. Air-gapped demo still uses in-cluster CPU Ollama; external-GPU is a LAN-mode accelerator only.
Why: team hardware reality — WSL2 won't see 16 GB; the alternate desktop exists and is the strongest, most stable host.
Impact: BUILD_GUIDE P0 applies to the desktop verbatim (skip the VM step); MASTER_PLAN Footprint C gains the external-OLLAMA_HOST note; demo-day topology: desktop = seed + framework, laptops join as workload nodes if fleet mode is on.
Links: D-006 (switches), §1.7 budget, §2.8.

## LOG-010 · 2026-06-12 · NOTE
What: Amends D-007's "no GUI" stance slightly: desktop gets an **on-demand** graphical fallback — Xfce (`xubuntu-core`, no recommends) + xrdp, with boot target pinned to `multi-user.target` and xrdp/lightdm disabled by default. Costs 0 RAM until a session is opened (~400–500 MB while active); reach it from any Windows laptop via built-in RDP (mstsc), no VNC client install. Minimal alternative if even that feels heavy: Openbox session (~150 MB active).
Why: occasional need to "really see a screen" (browser-on-box debugging, dashboard check without LAN).
Impact: two install commands in P0 notes; never to be running during demo/rehearsal RAM measurements.
Links: D-007 (LOG-009).

## LOG-011 · 2026-06-12 · DECISION (D-008)
What: Remote topology for the AIC-Bengaluru ↔ home-PC split. (1) **Tailscale** mesh on home PC + laptop — SSH, kubectl (K3s installed with `--tls-san <tailscale-ip>,<magicdns-name>`), xrdp, and dashboard all ride the tailnet; no router port-forwarding. (2) **Files: sync, not mount** — Syncthing between the Cowork folder on the laptop (Windows side, where Cowork writes) and the home PC working copy; `.stignore` excludes images/artifacts/venvs; git remains source of truth with the discipline "commit/push from one machine at a time." SSHFS rejected for the edit path: synchronous internet I/O makes every save a round-trip and breaks file watchers. (3) **Hard rule: the home PC never joins a fleet cluster from AIC** — a cross-internet node has jitter and clock skew that would pollute lag correlation and PSI scoping; it serves as solo-mode reference + remote build box only. Fleet demos use only machines physically on the same LAN.
Why: builder is at AIC; cluster box is at home; Cowork-edits must reflect on the runtime box without friction (replacing the local-symlink workflow with its network equivalent).
Impact: P0 gains Tailscale + `--tls-san` install notes; Claude Code runs on the home PC over tailnet SSH; laptop solo-mode VM remains the offline backup if home power/ISP dies.
Links: D-007 (LOG-009), LOG-008 (git workflow).

## LOG-012 · 2026-06-12 · DECISION (D-009)
What: **Profiles** — the umbrella chart ships two value overlays so the same package runs optimally at two sizes: `--profile full` (16 GB boxes, everything as designed) and `--profile lite` (8 GB headroom: WSL2 with default half-RAM, small VMs). Lite makes five substitutions: (1) metrics = **VictoriaMetrics single + vmagent** (~0.3 GB — this is where D-001's contingency becomes a default); (2) **Loki dropped**; L2 aggregator tails logs via the kube API into a 5-min ring buffer and Drain3 (A2) consumes that — same Log Detective, no log database; (3) **LLM never in-cgroup**: external `OLLAMA_HOST` (e.g., Ollama on the Windows host — *outside* WSL2's memory budget) or template-only narration; (4) L0 trims that don't touch pathologies: timescaledb 640Mi→1Gi lim, firmware-cache tmpfs 512→128Mi; (5) Grafana/extras off. Lite budget: WSL/OS 0.4 + K3s 1.0 + L0 2.1 + VM 0.3 + eBPF duo 0.45 + L2 0.15 + L3 0.4 + dash 0.15 ≈ **4.95 GB**, ~3 GB headroom on 8.
Companion ruling — **witness tiers** in the evidence gate (§1.4.4): tier-1 witnesses (weight 1.0) = eBPF path, PSI co-pressure, shared-PVC; tier-2 (weight 0.6) = co-onset CFS-throttling / disk io_time saturation, used automatically where PSI is absent (stock WSL2 kernel lacks CONFIG_PSI). Engine probes `/proc/pressure` at startup and labels the deployment "reduced-evidence mode" in the UI — graceful degradation instead of a hard requirement. Optional restoration: repo ships `infra/wsl2-kernel/` (config fragment CONFIG_PSI=y + BTF on; one-time build of microsoft/WSL2-Linux-Kernel, point `.wslconfig kernel=` at it) → WSL2 gets tier-1 PSI too. WSL2 runtime rules: `/etc/wsl.conf` `[boot] systemd=true`; `.wslconfig` `memory=8GB processors=6 swap=0` (swap **must** be 0 during measurements — swapping distorts the I/O physics we demo); `kernelCommandLine=cgroup_no_v1=all`; fleet-join from WSL2 only with Win11 mirrored networking, otherwise WSL2 = solo-only.
Why: team direction — the package should run *optimally* on WSL2's realistic 8 GB, not merely be excused from it. Profiles keep one codebase honest at both sizes; witness tiers turn the PSI dependency from a cliff into a slope.
Impact: MASTER_PLAN §1.4.4 (tiers), §1.7 (lite budget), §2.8 Footprint D; BUILD_GUIDE P0 step-1 options + new P0-alt section + lost-finder row; Helm gains `values-full.yaml`/`values-lite.yaml`; `skctl up --mode solo --profile lite`. Demo claims unchanged — stage demo remains full-profile on bare metal (D-003/D-007 stand).
Links: D-001, D-003 (amended), D-006 (switches compose with profiles), D-007 (OLLAMA_HOST reuse).

## LOG-013 · 2026-06-12 · REVERT (withdraws D-009)
What: D-009 withdrawn in full, same day it was made. Removed from the docs: the `full`/`lite` profile system, witness tiers in the evidence gate (§1.4.4 back to the original three-witness clause at full weight), the Loki-less log path, Footprint D, the lite RAM budget, BUILD_GUIDE P0-alt and its lost-finder rows. The build has **one design**: the full architecture as specified pre-LOG-012. WSL2 returns to its D-003/LOG-008 status — dev shell only, never a cluster host. Non-lite catch-up fixes from the same editing round are kept (they implement earlier decisions, not D-009): git-init step (LOG-008), desktop host option + xrdp extras (D-007/LOG-010), Tailscale/`--tls-san` notes (D-008).
Why: team call — one canonical setup beats two maintained sizes; the complexity (two value overlays, two test matrices, a confidence-weighting scheme that exists only to excuse weaker hosts) wasn't buying demo value. 8 GB boxes simply aren't targets.
Impact: anyone reading LOG-012 must read this entry with it; `values-lite.yaml`, witness tiers, and `infra/wsl2-kernel/` must not be built. Register rows D-001/D-003/D-009 updated.
Links: LOG-012 (superseded), D-003 (LOG-004), LOG-008.

## LOG-014 · 2026-06-12 · STEP + DECISION (D-010)
What: **Build started — repo scaffolded and the P4 engine core is green (13/13 unit tests)**, built ahead of schedule in the Cowork sandbox. Shipped: `correlation/` (detectors, lagcorr, gate, ranking, pipeline + test suite with planted-truth fixtures incl. the full S1 chain and the S0 idle drill), all 15 `workloads/` sources + Dockerfiles (Python/Node syntax-checked; Go compiles at P1 — no Go toolchain in sandbox), `deploy/charts/factory` (generic workload template, D-006 group switches, affinity-group labels, PVCs), `deploy/skctl` + Prometheus/Loki values (5s L0 + cadvisor scrape jobs), `scenarios/S0–S5` (triggers, resets, runbooks, ledger.csv), `aggregator/` skeleton + **Event schema v1 frozen** (`aggregator/schema/event.schema.json`).
Two engineering findings, both caught by the test suite:
(1) CUSUM sigma estimated on 12 samples fabricates onsets on compound-noise signals → sigma prefix now first-third clamped 24–60 samples.
(2) **D-010: root-cause ranking = explanatory reach, replacing personalized PageRank.** Seeding PageRank at symptom pods hands the symptom the restart mass — ccr outranked its own cause. New scorer: each candidate scores by how much of the symptom set it explains (forward reachability with decay), ×0.5 penalty if the candidate itself has an upstream explainer, isolated no-in-edge symptoms explain themselves (covers self-caused leaks like vision-qc), tie-break earliest onset. S1 fixture now ranks coolmon #1 (0.42) with blast radius dcim→tsdb→ccr at ETAs 15/60/90s. MASTER_PLAN §1.4.1/§1.4.5 + BUILD_GUIDE P4 updated.
Ops lesson for the log: the Windows↔sandbox file sync tore a mid-rewrite `detectors.py` (truncated at ~4 KB) — symptom was tests importing phantom old code. Remedy that worked: write code files from the bash side when the sandbox must execute them immediately, and clear `__pycache__` after any cross-boundary rewrite.
Why: team said "start build now, whichever phase is possible" — P4's math and all cluster-independent artifacts were buildable without P0.
Impact: desktop P0 remains the next physical step; then P1 = `go mod tidy` + image builds against these sources; P3 completes the aggregator against the frozen schema. Engine thresholds (R_PEAK 0.6, R_ADJ 0.4, CUSUM k=0.5 h=5, DECAY 0.7, CUT 0.15, UPSTREAM_PENALTY 0.5) are the reference values — tune only via config + LOG entry.
Links: BUILD_GUIDE P1/P3/P4 done-when boxes; MASTER_PLAN §1.4; D-006 (switches in chart values).

## LOG-015 · 2026-06-12 · STEP
What: P0_DESKTOP_SETUP.md written — Windows 11 → **dual-boot** Ubuntu Server 24.04 on the home desktop (team choice; amends D-007's implied full-wipe, headless-default stance survives via GRUB rules). Remote-safety engineering baked in: GRUB default=saved + `grub-reboot` for one-time Windows boots from SSH, Fast Startup off, BitLocker suspend procedure, `set-local-rtc 1` to end the dual-boot clock fight (chrony owns system time — lag math depends on it), BIOS restore-on-power-loss, sleep targets masked, DHCP reservation + Tailscale before anything else. Ends at the BUILD_GUIDE P0 step-2 kernel-check gate.
Why: desktop is the cluster reference box and will live headless at home while the builder is at AIC; dual-boot's one real hazard (wrong-OS boot when remote) is closed by the GRUB rules.
Impact: P0 is now fully self-serve; ≈90 min hands-on. Next physical milestone unchanged: five kernel checks green → K3s with PSI gate + `--tls-san`.
Links: P0_DESKTOP_SETUP.md; BUILD_GUIDE P0; D-007 (LOG-009), D-008 (LOG-011), LOG-010 (xrdp).

## LOG-016 · 2026-06-12 · STEP
What: **Tier-0 verification reproduced by the team**: 13/13 engine tests pass on Soumyadip's laptop (WSL2, Python 3.12 venv `abb-env`, repo on /mnt/c). Sandbox build ran 3.10 — engine now proven on both ends of the supported range. Added `correlation/pytest.ini` (`-p no:cacheprovider`) to silence the harmless NTFS cache-permission warning on /mnt/c runs.
Why: first independent reproduction of the P4 core outside the build environment — the "no cluster needed" test-tier design working as intended.
Impact: P4 unit level is double-confirmed; next verification milestone is Tier-1 (`helm template`, `go build` in WSL2) then P0 on the desktop.
Links: LOG-014; BUILD_GUIDE P4 status line.

## LOG-017 · 2026-06-12 · STEP
What: **Tier-1 verification closed, all green, zero fixes needed.** On Soumyadip's WSL2 dev shell: (1) `go mod tidy && go build` clean on all six Go modules first-try — plc-gateway, critical-control-relay, safety-interlock, dcim-bridge, notify-gateway, aggregator; (2) `helm template` (Helm 4.2.0) renders the factory chart to exactly **28 manifests** = 13 Deployments + 2 CronJobs + 11 Services + 2 PVCs — the predicted count. Combined with LOG-016's 13/13 engine tests, everything buildable without a cluster is now verified.
Why: Tier-1 gate before P0 — catches compile and chart errors while they're free to fix.
Impact: the only remaining blocker for P1 (images + deploy) is the physical desktop install (P0_DESKTOP_SETUP.md). Note: one early go-build attempt failed harmlessly by running in `correlation/` (Python, no go.mod) — Go modules live in `workloads/*` and `aggregator/`.
Links: LOG-015 (P0 doc), LOG-016, BUILD_GUIDE P1 done-when.

## LOG-018 · 2026-06-12 · STEP
What: P0_DESKTOP_SETUP.md Part 4b added — consolidated Linux-side sequence for the desktop: BIOS trio (ErP off / AC BACK always-on / Fast Boot off), WoL armed via netplan `wakeonlan: true` (+ Windows driver side for dual-boot), K3s `--tls-san` with the Tailscale IP, build toolchain, Syncthing pairing, Claude Code, and the shared-box arrangement for dad (graphical.target + lightdm enabled — supersedes headless-default on this box). Firmware note: UEFI Network Stack / PXE / HTTP-boot options left **disabled** — not needed for disk boot, and off = faster POST + no rogue-DHCP boot surface; unrelated to WoL, which rides NIC standby power, not the UEFI network stack.
Why: desktop install in progress; sequence given in-session and pinned to the doc.
Impact: P0 execution is now one document end-to-end; next gate = the six P0 checks incl. `container_pressure_*` via cadvisor.
Links: P0_DESKTOP_SETUP.md Part 4b; D-008; LOG-015.

## LOG-019 · 2026-06-12 · STEP + REVERT (OS choice)
What: Desktop OS switched: **Xubuntu 26.04 LTS (minimal)** instead of Ubuntu Server 24.04. During install attempts the Ubuntu Server USB hung post-microcode (suspected i915 handoff or bad stick), and a subsequent BIOS-settings session left the box unable to POST — recovered via **CMOS clear**. Decision: take the desktop-installer path (built-in safe-graphics option; desktop session was wanted for the shared-box arrangement anyway).
Why: pragmatism over installer pride (per the standing guidance); Xubuntu 26.04 = same apt/kernel family, PSI/BTF/cgroup-v2 all present, P0's six checks remain the gate.
Impact: P0 doc deltas (Part 4c): install `openssh-server` first; WoL via `nmcli ... wake-on-lan magic` (NetworkManager renderer); skip the xubuntu-core/lightdm install steps (native now). Post-CMOS-clear checklist: BIOS at defaults → re-apply **one setting per reboot**: AC BACK=Always On → ErP=Disabled → Fast Boot=**Disabled** (never Ultra Fast — it skips USB init at POST and locks you out of Del; prime suspect for the lockout). Verify date/time after clear. Fresh-LTS caveat: if K3s misbehaves on 26.04, fallback is reinstall 24.04 — decision point at the P0 gate.
Links: LOG-018, P0_DESKTOP_SETUP.md.

## LOG-020 · 2026-06-12 · STEP — **P0 GATE PASSED**
What: Desktop (i7-10700, Xubuntu 26.04, dual-boot) is a live K3s node with all six checks green: kernel **7.0.0-22-generic**, BTF present, cgroup2fs, `/proc/pressure` active, clock synchronized (local-RTC warning expected and accepted — dual-boot choice, chrony owns system time), and **`container_pressure_cpu_stalled_seconds_total` served from kubelet cadvisor** — KubeletPSI gate confirmed working. K3s installed with `--disable traefik --kubelet-arg=feature-gates=KubeletPSI=true --tls-san <tailscale-ip>,<hostname>`. Tailscale up (100.93.123.48); SSH from laptop over tailnet verified; WoL armed (`Wake-on: g`, MAC recorded) — drill pending (block 13). En route: CMOS-clear time reset broke apt ("Release file not valid yet") — fixed via timezone+NTP restore; logged as a reminder that the lag engine's clock dependency starts at install time.
Why: the gate decides everything downstream; it passed on first K3s install.
Impact: P1 unblocked — clone/sync repo onto the desktop, build 15 images, `skctl up`. Watch-item for P2: kernel 7.0 is very new — verify Caretta/OBI eBPF programs load (CO-RE should cope; Otterize fallback stands).
Links: BUILD_GUIDE P0 done-when (all ticked), LOG-019, D-008.

## LOG-021 · 2026-06-12 · BLOCKER (accepted) + DECISION (D-011)
What: **Wake-on-LAN unresolved after full diagnosis; smart plug adopted as the remote-power path (D-011).** Evidence trail: `Wake-on: g` armed (ethtool + nmcli persistent), `/sys/.../power/wakeup = enabled`, BIOS verified (ErP Disabled, WoL item Enabled, AC BACK Always On), NIC standby LED active in S5, and tcpdump on eno1 captured the magic packets perfectly formed (102B, FF×6 + MAC×16, ports 9+7, subnet-correct, sender pinned to the WiFi NIC after discovering the multi-homed-laptop wrong-interface trap). NIC receives the packet awake; firmware ignores it in S5. Remaining suspects (I219 NVM APM bit, board firmware, kernel 7.0 e1000e shutdown path) judged not worth the evening — fwupdmgr shows pending firmware updates as a future avenue; the Windows-shutdown isolation test remains optional.
D-011: **Wipro WiFi smart plug (cloud-controlled) + AC BACK=Always On** is the official resurrection mechanism — works from any network incl. mobile data, no LAN relay. Protocol: plug stays ON always; cut only when the box is already off (or hung beyond SSH); sequence OFF → 10s → ON → board boots on AC-return. Routine shutdowns stay `sudo poweroff` via SSH. WoL config left in place at zero cost.
Why: remote power-on is a hard requirement for the AIC↔home split; WoL was the means, not the end. The plug is means-equivalent and network-independent.
Impact: P0_DESKTOP_SETUP WoL drill marked "superseded by plug protocol"; pending verification: full plug-cycle test over mobile data.
Links: LOG-020, D-008, P0_DESKTOP_SETUP Part 4b.

## LOG-022 · 2026-06-12 · STEP — **P1 FIRST BOOT: the factory is running**
What: All 15 images built first-try on the desktop (docker → `k3s ctr images import`, legacy-builder warnings only) and deployed via `./deploy/skctl up --mode solo`. 45 seconds after install: 13/13 Deployments Running across factory-core/data/edge, zero restarts, both PVCs provisioned, and the analytics-batch CronJob fired its first scheduled CPU burst within the first minute (Completed on schedule). log-archiver correctly dormant until its nightly slot. En-route fixes worth remembering: k3s's bundled kubectl ignores `~/.kube/config` → `export KUBECONFIG=$HOME/.kube/config` in `.bashrc`; Windows→Linux Syncthing strips exec bits → `chmod +x deploy/skctl scenarios/*/*.sh` after first sync.
Why: BUILD_GUIDE P1 steps 1–3.
Impact: pending for P1 close: smoke tests (MQTT sub, DB row growth, kubectl top ≈ 2.5–3 GB) + 1-hour zero-restart soak + manual pathology smoke (30s fio, leak toggle on/off). Then P2 (telemetry stack) — first checkpoint there is Caretta/OBI eBPF loading on kernel 7.0 (LOG-020 watch-item).
Links: LOG-020, BUILD_GUIDE P1 done-when.

## LOG-023 · 2026-06-13 · STEP — **P1 CLOSED: overnight soak passed**
What: 8h18m soak, zero unplanned restarts, zero Warning events, pipeline lossless at ~2,000 rows/s throughout (3.8M rows at the 32-min mark, count still climbing on schedule). CronJob rhythm exact (analytics-batch every 5 min, Completed history clean). Bonus: **S1 trigger mechanism verified live** at 07:25 — the FLUSH-flag → fio storm path works on real hardware (unobserved; telemetry doesn't exist yet). Lesson: distroless pods (dcim-bridge, all Go workloads) have **no shell** — `kubectl exec ... sh` is impossible by design; shell-based smoke checks must target Python/Node pods. timescaledb RAM 120→314Mi overnight = shared_buffers cache fill (plateau, not leak) — the textbook `shift`-vs-`leak` contrast the classifier exists for.
Why: BUILD_GUIDE P1 done-when, all boxes ticked.
Impact: P2 begins — `skctl up --components telemetry` (kube-prometheus-stack + Loki), then Alloy/Caretta/OBI manual steps; first checkpoint is eBPF program load on kernel 7.0 (LOG-020 watch-item).
Links: LOG-022; BUILD_GUIDE P2.

## LOG-024 · 2026-06-13 · STEP + BLOCKER + FIX — P2 telemetry core up; `--components` footgun tore down the factory
What: `skctl up --components telemetry` installed kube-prometheus-stack (`prom`) + loki-stack (`loki`) in observability — prometheus 2/2, kube-state-metrics, node-exporter, alertmanager 2/2, loki-0 all Running; prom-grafana crashlooping (Grafana 12 apiserver, exit 1 — debug lens, non-blocking). THEN verify_taps showed every kubelet-sourced metric (all `container_*`, PSI, `kubelet_volume_stats_*`) absent for factory-* while node-exporter/kube-state worked. diag_scrape.sh isolated it: scrapes are **healthy** (kubelet 3/3 up, cadvisor-fast 1/1 up, `container_pressure_*` present, 71 series across kube-system/observability) — factory-* was absent because the workloads were **gone**. Root cause: `--components` is exclusive (skctl `has()` sets unlisted groups=false), so the command rolled `factory` to REV2 with core/storage/compute/edge all false → 15 pods removed and pvcs.yaml (guarded by `if groups.storage`, no resource-policy) deleted → tsdb-pvc + shared-logs-pvc deleted (`kubectl get pvc -A` = No resources found); ~57M synthetic rows lost. FIX: `skctl up --mode solo` → factory REV3 (all groups on), prom/loki REV2; pods + fresh PVCs returning.
Why: the documented P2 command (LOG-023) was itself the footgun — telemetry add silently disabled the workloads it was meant to observe.
Impact: data was synthetic, so the cost was time not work; the P2 scrape path is proven healthy (container PSI — the differentiator — is scrapeable; it was blocked only by the now-recovered workloads). Permanent guard = D-012.
Links: LOG-023; D-006; BUILD_GUIDE P2; appendix/verify_taps.sh, appendix/diag_scrape.sh.

## LOG-025 · 2026-06-13 · DECISION (D-012) — skctl subset-runs must never delete data
What: Two rulings from LOG-024. (1) `--components <subset>` is exclusive and destructive to unlisted groups; in **solo mode always run `skctl up` with no --components** (COMPONENTS defaults to "all"). BUILD_GUIDE P2's `--components telemetry` is superseded by `skctl up --mode solo`. (2) Every PVC in charts/factory/templates/pvcs.yaml gets annotation `helm.sh/resource-policy: keep` so Helm skips deletion even when groups.storage=false. Proven mechanically: `helm template factory --set groups.*=false` renders **0 documents (0 PVCs)** — that empty render is exactly what Helm applied as REV2. Trade-off accepted: `keep` also means `skctl down`/uninstall won't wipe the volumes — manual `kubectl delete pvc` to truly clear.
Why: a data volume must survive a workload toggle; the fence belongs on the PVC, not on operator discipline alone.
Impact: pvcs.yaml gains the annotation (apply, then `skctl up --mode solo` = REV4 to stamp live PVCs); an optional skctl guard (warn when a subset run would scale a live group to zero) is noted as future. Fleet mode (each box flips its own switches) is unaffected — exclusivity is correct there.
Links: LOG-024; D-005/D-006; BUILD_GUIDE P2; charts/factory/templates/pvcs.yaml.

## LOG-026 · 2026-06-13 · STEP + NOTE — stabilization audit; new tooling; working-agreement update
What: Cluster-independent stabilization pass (Cowork sandbox, throwaway copies — no repo pollution): correlation engine **13/13 green on numpy 2.2.6 / scipy 1.15.3** (newer than the build's 3.10 set — engine not pinned to lucky deps); `helm template` factory = **28 manifests** (13 Deploy / 2 CronJob / 11 Svc / 2 PVC, matches LOG-017); 15/15 workloads carry Dockerfiles and pass Python/Node syntax; aggregator event.schema.json + queries.yaml valid; scenario S1 complete, S2–S5 runbooks/resets still stubs (P7 work, expected). Added read-only diagnostics in `appendix/`: verify_taps.sh (the §2.7 P2 tap gate, `--strict` for full close, via `kubectl get --raw` service-proxy) and diag_scrape.sh (per-job `up` + metric existence). Found: prometheus.yaml has **no channel=truth job** — l0-fast scrapes app /metrics unseparated; add a relabel before P3 (D-004). Register backfilled with D-010/D-011 (present in entries, missing from the index).
Why: operator asked to confirm the whole project is working and coherent before resuming the build.
Impact (working agreement): Cowork/Claude now holds **full editorial access** to the repo folder; **running is deferred to the operator** (cluster lives on the home desktop over tailnet). Claude **appends** to this log — never deletes or edits prior entries — and logs an entry whenever a serious project question or decision arises. `/engineering` skills active; GitHub MCP needs manual `/mcp` auth (server lacks dynamic client registration).
Links: LOG-014/016/017; LOG-024/025; BUILD_GUIDE P2/P3; appendix/.

## LOG-027 · 2026-06-13 · STEP — P2 fine-tune + L2 aggregator built to v1 (sandbox-verified)
What: Recursive pathway check (metric→query→schema→engine) surfaced two breaks, both fixed. (1) D-004 leak: queries.yaml `latency_p95` pulled `ccr_actuation_seconds_bucket` (the CCR's own app histogram = ground-truth channel) → re-sourced to OBI eBPF RED (`http_server_request_duration_seconds_bucket`, pending OBI install). (2) aggregator was a 1-query skeleton → built aggregator/main.go to v1: loads the full queries.yaml pack (dependency-free parser), 5s poll, per-pod 15-min ring (capN=180) at /window, threshold→`anomaly_candidate` events conforming to the FROZEN event.schema.json (v1/kind/ns/pod/signal∈enum/value/robust-z/threshold), /events + optional POST to L3, /healthz. Added aggregator/main_test.go (golden: pack parse, threshold→schema event, idle-silent-but-ring-fills). P2 fine-tune: prometheus.yaml grafana enabled:false (Grafana-12 crashloop LOG-024) + channel=truth relabel on l0-fast (D-004); pvcs.yaml gains helm.sh/resource-policy:keep (D-012).
Modeling notes (v0, tune on box): events fire on psi_* + latency only; cpu rate needs per-pod-limit normalization (deferred — cpu suffering surfaces via psi_cpu); pvc_capacity/pvc_io_util are PVC-keyed (no `pod` label) so they need a PVC→pod join before emitting — psi_io is S1's primary witness meanwhile.
Verify (sandbox, no cluster): `go build`+`go vet` clean, `go test` 3/3; `helm template`=28 manifests with resource-policy:keep on both PVCs; engine kernel 13/13; prometheus/queries/loki YAML valid. **Nothing P0–P2 broke.**
Why: operator asked to fine-tune P2 and set the framework up cleanly through the aggregator; build+verify autonomously.
Impact: L2 deployable at P3 — build image, mount queries.yaml as ConfigMap at /etc/aggregator/queries.yaml, set PROM_URL (+ optional L3_URL). Confirm cpu/pvc thresholds + OBI latency label on the box.
Links: LOG-024/025/026; BUILD_GUIDE P2/P3; aggregator/main.go+main_test.go; MASTER_PLAN §1.3/§2.7; D-004.

## LOG-028 · 2026-06-13 · NOTE + open DECISION — restart/reboot retention & the 14-day window
What: Operator wants factory data to survive a desktop restart + a 14-day rolling window (demo richness; engine baselines are live-window not 14-day, so detection is unaffected by a wipe). Findings: (a) timescaledb on tsdb-pvc (local-path) DOES survive pod restart AND host reboot — local-path data sits on the SSD and reattaches on the single node; now doubly safe with resource-policy:keep. The earlier loss was the helm footgun (LOG-024), not a reboot. (b) init.sql creates `readings` with NO retention/compression/continuous-aggregate → unbounded growth; 8Gi fills in ~12h at ~2000 rows/s (57M rows at the 8h soak). 14 days raw ≈ 2.4B rows ≈ tens of GB → will NOT fit 8Gi. (c) Prometheus has no storageSpec → emptyDir → metrics wiped on restart, 12h retention (fine for live causal analysis; flag if metric history is wanted → needs a PVC).
OPEN DECISION (operator pick): 14-day window via [A] compression + 1-min continuous aggregate retained 14d + raw retention ~48h (fits 8Gi, recommended) OR [B] raw 14d → bump tsdb-pvc to ~48–64Gi + compression + 14d retention. Either way init.sql needs a retention/compression policy soon (8Gi near-fills daily).
Why: prevent a silent ENOSPC and give the demo a credible rolling history.
Impact: pending the pick → edit timescaledb/init.sql (+ maybe values.yaml PVC size); restart-test script for the operator to run on the desktop.
Links: workloads/timescaledb/init.sql; charts/factory values.yaml; D-012; LOG-023 (row rate).

## LOG-029 · 2026-06-13 · DECISION (D-013) — 14-day raw window (resolves LOG-028)
What: Operator picked [B] raw 14-day retention (desktop disk 196GiB, ~170 free). tsdb-pvc 8Gi→64Gi (values.yaml); timescaledb/init.sql now sets 1h chunk_time_interval, native compression (segmentby=topic, orderby=ts DESC) after 1h, and a retention policy dropping chunks >14 days. 14d raw ≈2.4B rows ≈290GB uncompressed → ~15-30GB compressed, fits 64Gi with headroom. Added appendix/restart_test.sh (record→reboot→verify: PVC-uid rebind + row-count persistence) and appendix/component_check.sh (P0/P1/P2 per-component sweep).
Apply: local-path can't resize in place → `kubectl delete pvc tsdb-pvc -n factory-data` (it's keep-annotated, so manual) then `skctl up --mode solo` recreates it at 64Gi; the DB re-inits and init.sql installs the policies (one-time synthetic-data reset). Confirm after ~1h: `SELECT * FROM timescaledb_information.compression_settings;` + compressed chunks in timescaledb_information.chunks.
Why: bounded storage + a credible 14-day demo history; engine detection is live-window so a reset doesn't hurt it.
Impact: prevents the ~12h ENOSPC on 8Gi; restart_test proves reboot persistence (PVC lives on the SSD, rebinds on one node). Prometheus stays emptyDir/12h (separate concern; flag if metric history is wanted).
Links: LOG-028; workloads/timescaledb/init.sql; charts/factory values.yaml; D-011/D-012; appendix/restart_test.sh, component_check.sh.

## LOG-030 · 2026-06-13 · STEP — 64Gi resize applied on box; README; component_check fix
What: D-013 applied — scaled timescaledb to 0 to release the pvc-protection finalizer (a `kubectl delete pvc` had hung while the pod mounted it), then `skctl up --mode solo` recreated tsdb-pvc at **64Gi (Bound, fresh uid)**; DB re-init ran init.sql (Dockerfile COPYs it to /docker-entrypoint-initdb.d/90-init.sql) installing compression + 14-day retention. Data reset to ~0 (synthetic, repopulating). component_check.sh P0–P2 sweep green except two explained non-failures: "cadvisor has no container_pressure" was a `grep -q`+pipefail SIGPIPE false-FAIL (FIXED → `set -u` not pipefail; PSI confirmed present via verify_taps GREEN, PASS=14), and "tsdb-pvc not Bound" during the delete window. restart_test record+verify ran back-to-back (no real reboot) → its PASS isn't yet a persistence proof; real reboot test pending. Wrote README.md (overview + build + deploy + verify + guardrails) for GitHub publish.
Why: operator chose [B] raw-14d and asked for GitHub-ready docs.
Impact: data-generation→collection→aggregation framework is set through L2; next P2 = Alloy + Caretta/OBI (kernel-7.0 eBPF). Confirm retention jobs: `SELECT application_name FROM timescaledb_information.jobs WHERE application_name ~* 'compress|retention';` (expect 2).
Links: LOG-029 (D-013); README.md; appendix/component_check.sh; BUILD_GUIDE P2/P3.

## LOG-031 · 2026-06-13 · BLOCKER + FIX — retention policies didn't install (init.sql is image-baked)
What: After the 64Gi recreate, `timescaledb_information.jobs` showed only the built-in "Job History Log Retention Policy" — NOT the D-013 compression/retention jobs. Root cause: init.sql is COPYed into the image at build time (Dockerfile → /docker-entrypoint-initdb.d/90-init.sql); `skctl up` reused the OLD P1 image (built before the init.sql edit), so the fresh DB re-inited with the pre-policy SQL. The 64Gi size took (chart-level) but the policies didn't (image-level).
FIX (no data loss): apply to the live DB — `set_chunk_time_interval('readings','1 hour')` + `ALTER TABLE readings SET (timescaledb.compress,...)` + `add_compression_policy(1h)` + `add_retention_policy(14d)`. Durable: rebuild `skn/timescaledb:v0.1` + `k3s ctr images import` so the baked init.sql carries the policies for any future fresh init / air-gap tarball.
Lesson: **init.sql changes need an image rebuild, not just `skctl up`.** Added appendix/psi_watch.sh (live per-pod PSI snapshot — S1/S3 verification + demo).
Why: operator's verify query surfaced the gap.
Impact: re-verify jobs query shows Compression + Retention Policy (2 rows). Add the image-rebuild note to BUILD_GUIDE P1.
Links: LOG-029/030 (D-013); workloads/timescaledb/{init.sql,Dockerfile}; appendix/psi_watch.sh.

## LOG-032 · 2026-06-13 · STEP — S1 tuned demo-grade + made L4-triggerable; skctl pause/resume
What: Original S1 fio (1 job, 2g, buffered/direct=0) finished in ~1.5s on the NVMe → baseline PSI only. Sustained tuning proven on box (manual fio: 4 jobs ×512m, time_based 45s, fsync=8, O_DIRECT) → disk util 48%→**88.69%**, 63GB written, **timescaledb psi_io 0.034→0.1882** = cross-pod contention through the shared physical disk (S1's thesis, no network edge). Baked into cooling-monitor/main.py: sustained fio with **env-tunable knobs** (FIO_SIZE/JOBS/RUNTIME/FSYNC/DIRECT — retune via Helm values, no rebuild) + an **HTTP trigger** (POST :8080/flush) alongside the FLUSH-flag touch, so L4's scenario console can fire it over HTTP (no kubectl-exec-from-dashboard). values.yaml: cooling-monitor gains port 8080 + the FIO_* env. Heavy load runs ONLY on trigger; steady state stays a light ~64KB/s journal. Added **`skctl pause|resume`** (scale factory deploys→0 + suspend cronjobs / restore) to fully idle the home box between sessions — PVCs + observability untouched.
Apply: rebuild + import the cooling-monitor image (init.sql lesson — main.py is image-baked): `docker build -t skn/cooling-monitor:v0.1 workloads/cooling-monitor/ && docker save skn/cooling-monitor:v0.1 | sudo k3s ctr images import -`, then `kubectl rollout restart deploy/cooling-monitor -n factory-data`. Then trigger.sh (or the HTTP POST) yields the demo-grade cascade.
Verify (sandbox): main.py py_compiles; skctl `bash -n` OK; `helm template` = 29 manifests (cooling-monitor Service added); values.yaml valid.
Why: operator — S1 must be loud for the demo, and heavy loads must be on-demand (it's a home PC).
Impact: S1 is demo-grade + L4-ready; to nudge psi_io clearly past 0.2, bump FIO_JOBS→6 or FIO_FSYNC→4 via Helm (no rebuild). Same trigger pattern extends to S3/S5 sources during P7/L4. Next: finish P2 (Alloy + Caretta/OBI).
Links: LOG-024 (NVMe-too-fast first seen); LOG-031 (image-rebuild lesson); workloads/cooling-monitor/main.py; deploy/skctl; scenarios/S1/runbook.md; MASTER_PLAN §2.5.

## LOG-033 · 2026-06-13 · STEP — P2 finish wired: Alloy + Caretta + OBI/Beyla
What: Wired BUILD_GUIDE P2 steps 2-4 into skctl's telemetry component. New deploy/values/: alloy.yaml (Grafana Alloy ships pod logs → in-cluster Loki via loki.source.kubernetes; Promtail EOL), caretta.yaml (eBPF service-flow map; bundled VictoriaMetrics+Grafana off; scraped via annotation), beyla.yaml (OBI/Beyla eBPF RED → supplies latency_p95 for the pack, D-004). prometheus.yaml gains a tool-agnostic `ebpf-exporters` scrape job (keeps any pod annotated prometheus.io/scrape=true) so Caretta/OBI land in our Prometheus without per-tool ServiceMonitors. skctl telemetry now installs prom→loki→alloy→caretta→beyla.
Verified (file-tool; the sandbox mount was stale/torn post-edit AGAIN — bash saw a truncated skctl/prometheus, real files are correct): all 4 values parse; skctl functions+case intact; ebpf-exporters is the 3rd additionalScrapeConfig.
FLAGGED for the box (couldn't web-fetch chart READMEs — timed out): Caretta metrics port (prometheus.io/port 7117 is a guess), Beyla 2.x config schema + whether the chart is `grafana/beyla` (else deploy Beyla via Alloy), Alloy pods/log RBAC if logs don't flow. The real test is **CO-RE eBPF load on kernel 7.0** (LOG-020 watch; Otterize network-mapper is Caretta's fallback). Inspektor Gadget stays on-demand (A5 tool call), not wired here.
Why: operator — finish P2.
Impact: `./deploy/skctl up --mode solo` installs the eBPF layer; then `verify_taps.sh --strict` should turn Caretta/OBI/Loki green. Watch-item: kernel 7.0 CO-RE.
Links: BUILD_GUIDE P2 steps 2-4; MASTER_PLAN §1.2/§2.7; deploy/values/{alloy,caretta,beyla,prometheus}.yaml; deploy/skctl; LOG-020.

## LOG-034 · 2026-06-13 · STEP — faults gated on-demand (cronjobs suspended); P2 core verify_taps 15/15
What: verify_taps --strict: all 15 core taps PASS (cadvisor CPU/mem/throttle + PSI cpu/mem/io, kubelet PVC stats, node-exporter, kube-state, l0-fast, cadvisor-fast, channel=truth). 3 FAIL = Caretta + OBI + Loki streams (eBPF/Alloy not yet emitting — kernel-7.0 CO-RE load and/or the LOG-033 flagged tweaks; deferred). Operator flagged constant load: analytics-batch CPU burst auto-fired every 5 min. Fix: chart CronJob template gains `suspend: {{ .suspend | default false }}`; values.yaml sets suspend:true on analytics-batch (S3) + log-archiver (S2) → they no longer auto-fire; triggered ONLY on demand via the existing scenarios/S{2,3}/trigger.sh (`kubectl create job --from=cronjob/...`), which also serves L4 buttons. Chart/values only — no image rebuild (skctl up applies). Now ALL heavy load is on-demand: S1 fio (FLUSH/HTTP), S2/S3 (suspended cron + create-job), S5 (LEAK_ENABLED off); the steady baseline stays light and `skctl pause` kills even that between sessions.
Why: operator — "make writes and faults triggerable, don't run them constantly."
Impact: apply with `skctl up --mode solo`. Enacted-layers explanation logged to EXPLANATIONS.md. Then: git commit; then chase the 3 eBPF/Loki reds.
Links: deploy/charts/factory/templates/workloads.yaml; values.yaml; scenarios/S2,S3/trigger.sh; LOG-032 (S1 trigger); EXPLANATIONS.md.

## LOG-035 · 2026-06-13 · STEP — reboot persistence PASSED; clock-reset assessment; compression-policy gap
What: Desktop hard-rebooted (PC clock reset briefly, now corrected by chrony). Recheck: node Ready (k3s v1.35.5), core verify_taps **15/15 PASS** (gate GREEN), tsdb-pvc (64Gi, uid 5d5dd5c5) + shared-logs Bound and rebound to the SAME volumes — **reboot data-persistence test PASSED** (readings min ts 07:40 predates the reboot, max=now, downtime ~0.02s; local-path data on the SSD survived). Closes task #7. Clock-reset impact judged negligible: readings min/max both today + contiguous (no future/ancient ts); Prometheus is emptyDir (wiped on reboot → fresh, no clock artifacts); TLS/k3s already recovered. Cleanup = verify no `ts > now()` rows, delete if any.
Findings: (1) timescaledb_information.jobs shows **Retention Policy [1001]** but NO compression policy — only retention applied earlier; without compression 14d raw (~290GB) won't fit 64Gi → add ALTER compress + add_compression_policy(1h). (2) **alloy CrashLoopBackOff** (19 restarts) = the Loki red; config/RBAC, debug with the eBPF reds. (3) Every factory pod RESTARTS=1 = the reboot (normal, not a fault); component_check flags it strictly. (4) Orphaned analytics-batch pod in Unknown — delete; suspend gating (LOG-034) applies on next `skctl up`.
Why: operator rebooted + asked about clock inconsistencies before committing.
Impact: add compression policy; optional future-row cleanup; then commit (chart renders OK on the box). eBPF/Loki + alloy crashloop deferred.
Links: LOG-029/030/031 (retention); LOG-033 (alloy); LOG-034 (suspend); appendix/restart_test.sh.

## LOG-036 · 2026-06-13 · STEP — repo prepped for first GitHub push; buildable for teammates
What: First-push prep. **.gitignore extended** — the ~52MB of locally-built Go binaries (aggregator/aggregator + workloads/{ccr,dcim-bridge,notify-gateway,plc-gateway,safety-interlock}) now ignored (Docker rebuilds them via each Dockerfile), plus Syncthing (.stfolder/.stignore), venvs (abb-env/venv), OS/editor junk; existing ignores kept (pycache, ppt_pages_images, old.version, .obsidian). .gitattributes already enforces eol=lf repo-wide (handles Windows CRLF for the whole team — better than per-clone autocrlf, LOG-008). **Makefile** upgraded from TODO stubs to real targets: `test` (pytest + go test), `images`/`import` (docker build + `k3s ctr images import` all 15 workloads as $(REG)/<name>:$(TAG)), `charts` (helm lint+template), `demo`/`pause`/`resume`. No secrets in-tree (values POSTGRES_PASSWORD=factory is a demo cred; kubeconfig stays in $HOME). Repo is machine-agnostic: service-DNS only, skctl uses relative $HERE paths.
Why: operator's first push; teammates must clone→build→deploy on any Linux+K3s box.
Impact: flow = git init -b main → add → (confirm binaries/pycache NOT staged) → commit → add GitHub remote → push. Teammate path: README prereqs → `make import` → `make demo`. Rebuild note: cooling-monitor (S1 fio) + timescaledb (retention init.sql) images changed this session — a fresh `make import` carries them.
Links: .gitignore; Makefile; README; .gitattributes; LOG-008 (CRLF).

## LOG-037 · 2026-06-13 · NOTE — git workflow finalized: laptop = master, desktop = Syncthing-runtime
What: Operator's rule: **all git runs on the laptop (Git Bash); laptop is the data master**. The desktop only receives the working copy via Syncthing and runs it — no git on the desktop. Refines D-008. Guards in place: `.git` excluded from Syncthing (.stignore) so the desktop's earlier stray `git init` can't cross-sync/corrupt (it's now an orphan — optional `rm -rf .git` on the desktop); `.gitattributes` pins eol=lf (Windows CRLF-safe); shell scripts marked executable in the git index via `git add --chmod=+x` (deploy/skctl, appendix/*.sh, scenarios/*/*.sh) so Linux *clones* get +x. Caveat: Syncthing still strips exec bits to the desktop (LOG-022) → the desktop runs via `bash …` / chmod-after-sync; the git +x only helps teammate clones. Remote: github.com/GreaseMonkeyIT/ABB_Accelerator_Proto.
Why: operator chose laptop-master / desktop-runtime for the first push.
Impact: all commits/pushes from the laptop only; teammates clone from GitHub.
Links: D-008 (LOG-011); LOG-022 (exec bits); LOG-036 (.gitignore/Makefile); .stignore; .gitattributes.

## LOG-038 · 2026-06-13 · STEP — P3 started: L2 aggregator containerized + deploy wired
What: Proceeding to P3 (P2 core taps green; the 3 eBPF/Loki reds feed L3/L4, not the L2 aggregator, so they don't block). Added aggregator/Dockerfile (multi-stage, CGO_ENABLED=0 static Go on distroless/static, nonroot, :9000); deploy/aggregator.yaml (Deployment+Service in ns aiops; mounts queries.yaml from an aggregator-queries ConfigMap; PROM_URL → in-cluster Prometheus; /healthz readiness; 100m/96Mi→300m/150Mi per §1.3). skctl `engine` step now: create ns aiops → build the aggregator-queries configmap from aggregator/queries.yaml → `kubectl apply deploy/aggregator.yaml` (correlation engine L3 left as TODO). Makefile images/import now also build/import skn/aggregator:v0.1.
Verify (sandbox): aggregator builds static (CGO_ENABLED=0 → statically-linked ELF, matches the Dockerfile); deploy/aggregator.yaml = valid Deployment+Service; skctl engine block well-formed (file-tool; mount-tear false EOF again); Makefile tabs OK.
Why: operator — proceed to P3.
Impact: operator runs `make import` then `skctl up --mode solo` to deploy. P3 done-when: events flow on a manual S1 within ~10s, silent at idle, /window serves per-pod vectors. latency_p95 stays empty until OBI is up (psi_* drive events meanwhile). Distroless image has no shell → inspect via `kubectl logs` + the API service-proxy (/window, /events).
Links: BUILD_GUIDE P3; MASTER_PLAN §1.3; aggregator/{main.go,Dockerfile}; deploy/aggregator.yaml; deploy/skctl; LOG-027 (aggregator v1).

## LOG-039 · 2026-06-13 · FIX — eBPF installs made non-fatal in skctl (were aborting the aggregator deploy)
What: `skctl up --mode solo` never reached the `engine` step (aggregator) because the caretta install failed (`repo caretta not found` — the groundcover helm repo add did not register) and skctl runs under `set -e`, so the script aborted at the caretta line. Fix: alloy/caretta/beyla installs are now `|| echo`-guarded (non-fatal); a flaky or deferred eBPF collector can no longer block the L2/L3/L4 deploys. The caretta repo URL and beyla chart coordinates remain to be confirmed when the eBPF reds are addressed.
Why: operator's P3 deploy run aborted before the aggregator step.
Impact: after `docker build`/import of skn/aggregator:v0.1, re-run `skctl up --mode solo`; caretta/beyla now fail non-fatally and the engine step deploys the aggregator to aiops. Then run the P3 verify gate.
Links: LOG-033 (eBPF wiring); LOG-038 (P3 aggregator); deploy/skctl.

## LOG-040 · 2026-06-13 · NOTE — no OS downgrade needed; caretta error is a helm-repo issue, not kernel 7.0
What: Operator asked whether to downgrade 26.04→24.04 (kernel 7.0) to fix caretta + the aggregator. No. "repo caretta not found" is a helm chart-repo problem (the groundcover repo URL did not register), unrelated to the kernel; the aggregator-not-deployed was skctl aborting at the caretta line under set -e (fixed in LOG-039). Kernel-7.0 eBPF CO-RE load for Caretta/OBI is still UNTESTED (the install fails before the load is attempted); even if 7.0 were a problem, fallbacks exist (Otterize flows, OBI-via-Alloy, or PSI-only — the core L0–L3 path needs no eBPF, and verify_taps core is green on 7.0). Unblock used: deploy the aggregator directly with kubectl (ns aiops + configmap + apply deploy/aggregator.yaml), bypassing skctl's telemetry block — aggregator now Running, /window serving vectors.
Why: operator worried a downgrade would wipe the dual-boot setup.
Impact: stay on Xubuntu 26.04 / kernel 7.0; defer caretta/OBI to the eBPF-reds work.
Links: LOG-019/020 (26.04/kernel 7.0); LOG-039 (skctl non-fatal); LOG-038 (aggregator).

## LOG-041 · 2026-06-13 · FIX — aggregator emitted no events: PSI was per-container, not per-pod
What: P3 deploy live (aggregator Running, /window serving per-pod vectors) but /events returned [] on S1. Cause: queries.yaml psi_cpu/mem/io used `rate(container_pressure_*{...})` which returns one series **per container**; a pod's total stall splits across its container series, so no single series crossed 0.20 even though the per-pod sum (what psi_watch showed = 0.22) did. Fix: wrap the three PSI queries in `sum by (namespace, pod) (...)` so the aggregator compares the per-pod stall to the threshold; lowered psi_some_avg 0.20→0.15 for margin (baseline ~0.03, S1 ~0.22). queries.yaml only — no image rebuild; apply = recreate the aggregator-queries configmap + `kubectl rollout restart deploy/aggregator -n aiops`.
Why: P3 done-when requires events on S1 within ~10s.
Impact: after configmap update + aggregator restart + an S1, /events should carry a psi_io anomaly_candidate for timescaledb. If still marginal, raise FIO_JOBS (louder S1) or drop the threshold further.
Links: LOG-038 (P3); LOG-032 (S1 0.22); aggregator/queries.yaml; appendix/psi_watch.sh.

## LOG-042 · 2026-06-13 · STEP — **P3 GATE PASSED: L2 aggregator live, events on S1**
What: After the per-pod PSI fix (LOG-041) + configmap reload, S1 produced a schema-conformant event from /events: `{v:1, kind:anomaly_candidate, namespace:factory-data, pod:timescaledb-..., signal:psi_io, value:0.268, threshold:0.15, window_s:60}`. /window serves per-pod vectors; idle is silent. The full L0→L1→L2 path now runs live on the cluster: cooling-monitor fio storm → timescaledb shared-disk I/O stall (psi_io 0.268) → aggregator emits the anomaly_candidate. P3 done-when met.
Why: P3 close.
Impact: L2 deployed in ns aiops (skn/aggregator:v0.1, configmap-driven queries, /window + /events + /healthz). Next: P4 — deploy the correlation engine to consume /window + /events and draw the S1 causal chain (cooling-monitor → dcim → tsdb → ccr). Still deferred: the 3 P2 eBPF/Loki reds (Caretta/OBI/Alloy).
Links: LOG-041 (PSI fix); LOG-038 (P3 deploy); BUILD_GUIDE P3 done-when; aggregator/.

## LOG-043 · 2026-06-13 · STEP — P4 started: L3 correlation engine service built + wired (chain proven)
What: Wrapped the engine in correlation/service.py: polls the aggregator's /window (per-pod signal vectors) + /events (anomaly seeds), builds run_pass inputs, serves the CausalGraph at /graph. v0 witness without eBPF: shared_relation from the storage-domain workloads (cooling-monitor/dcim-bridge/log-archiver/timescaledb share one local-path disk), psi_copressure from pods whose recent signal is elevated, ebpf_edges empty until Caretta/OBI land, slo_breach from the aggregator's anomaly_candidate pods. Added correlation/Dockerfile (python:3.12-slim + numpy/scipy/networkx), deploy/engine.yaml (Deployment+Service in aiops, 250m/384Mi→1c/512Mi, pulls the aggregator over HTTP), skctl engine step now applies engine.yaml after the aggregator, Makefile builds skn/correlation-engine:v0.1.
Engine robustness fix: run_pass took the FIRST cusum onset, but non-negative real signals (psi_io) emit weak ~1σ spurious onsets before the real one → wrong onset time, scrambled temporal gate, zero edges. Now filters onsets to |zpeak|≥3 before taking the first; unit suite stays 13/13.
Verify (sandbox; real pipeline.py reconstructed past a mount-tear): engine 13/13; service smoke on a mock recent-S1 /window → edges=3, **root=cooling-monitor**, blast=[dcim-bridge, timescaledb], innocent edge-ui excluded. Full /window→engine→causal-graph path works.
Why: operator — proceed to P4.
Impact: operator builds skn/correlation-engine:v0.1, `skctl up --mode solo` (or `kubectl apply -f deploy/engine.yaml`), then on an S1 the /graph endpoint should rank cooling-monitor #1 with the chain. Live tuning may need FIO/threshold nudges; dcim-bridge must stall for the full 3-hop chain.
Links: BUILD_GUIDE P4; correlation/{service.py,Dockerfile,engine/pipeline.py}; deploy/engine.yaml; deploy/skctl; LOG-014 (engine kernel).

## LOG-044 · 2026-06-14 · NOTE — **SESSION HANDOFF** (P4 in progress: engine live, causal chain not yet drawn)
Session result: P3 CLOSED (L2 aggregator live, schema events on S1, LOG-042). P4 STARTED: L3 correlation-engine built, containerized, deployed to aiops, polling the aggregator, serving /graph (LOG-043). Repo GitHub-ready (LOG-036/037, remote GreaseMonkeyIT/ABB_Accelerator_Proto), README reworded formal, 14-day retention applied (LOG-029/035), S1 demo-grade + faults on-demand (LOG-032/034).

LIVE on the cluster:
- L0 factory (15 pods) + L1 telemetry-core (Prometheus/PSI/kube-state/node-exporter) — verify_taps core 15/15 green.
- L2 **aggregator** (skn/aggregator:v0.1, ns aiops) — /window + /events + /healthz; emits anomaly_candidate when psi_io>0.15.
- L3 **correlation-engine** (skn/correlation-engine:v0.1, ns aiops) — /graph; polls the aggregator every 10s.

**OPEN P4 ISSUE — resume here.** On S1, /graph = `findings=[cooling-monitor (x2), alert-dispatcher], active=3, edges=0, root=none`: the engine detects the SOURCE (cooling-monitor) but the disk VICTIMS (timescaledb, dcim-bridge) never enter findings, so no causal edges form. Intermittent `status=error` mid-storm (likely the 5s urllib /window fetch timing out while the node is disk-saturated; self-recovers).
Hypothesis: timescaledb's psi_io baseline is NOISY (constant checkpoints), so its S1 onset's |zpeak| sits under the |zpeak|≥3 filter (added LOG-043) → not registered → no victim → no chain. cooling-monitor (clean baseline) registers fine.

NEXT STEPS (exact):
1. Diagnose in-pod during an S1 (fire S1, sleep ~22s): `kubectl exec -n aiops deploy/correlation-engine -- python -c "import urllib.request,json,numpy as np; from engine import detectors; w=json.load(urllib.request.urlopen('http://aggregator.aiops.svc:9000/window',timeout=5)); [print(n,[(o['idx'],round(o['zpeak'],1)) for o in detectors.cusum_onsets(np.array([x['value'] for x in s]))[:3]]) for n in ['cooling-monitor','timescaledb','dcim-bridge'] for k,s in w.items() if n in k and k.endswith('psi_io') and s]"`. And read the error: `kubectl get --raw .../correlation-engine:9100/proxy/graph | python3 -c "import sys,json;print(json.load(sys.stdin)['meta'])"`.
2. If timescaledb max>0.15 but zpeak ~2 → lower correlation/engine/pipeline.py `abs(o["zpeak"]) >= 3.0` to 2.0, rebuild+reimport skn/correlation-engine:v0.1, `kubectl rollout restart deploy/correlation-engine -n aiops`, re-run S1. If max is low → S1 needs more FIO_JOBS (mind SSD wear). Optionally raise the _fetch timeout in service.py.
3. Gate met when /graph ranks cooling-monitor #1 with edges to timescaledb (+dcim) and a blast radius. Then → L4 (Ollama narrator + dashboard, P5/P6).

DEFERRED (P2 eBPF/Loki reds, NOT blockers): caretta install fails (`repo caretta not found`, wrong helm URL; non-fatal in skctl per LOG-039); OBI/Beyla chart coords unconfirmed; alloy CrashLoopBackOff (config/RBAC). They enrich L3 (network map, latency); the PSI causal path works without them.

REMINDERS for whoever resumes: laptop = git master (commit/push there only, LOG-037); desktop = Syncthing runtime (`chmod +x` scripts after sync; `skctl pause` stops SSD writes between sessions). **Any code change needs an image rebuild + `k3s ctr images import`** (init.sql, all main.go/main.py, pipeline.py, service.py are baked into images). After a cross-machine sync, `helm template deploy/charts/factory >/dev/null` before deploying (sync can truncate files mid-write). The laptop still owes a commit of the P4 work (correlation/{service.py,Dockerfile}, deploy/engine.yaml, deploy/skctl, Makefile, engine/pipeline.py fix).
Links: LOG-042 (P3); LOG-043 (P4 engine); LOG-039 (caretta non-fatal); correlation/{service.py,engine/pipeline.py}; deploy/engine.yaml; tasks #10 (P2 eBPF), #12 (P4 deploy).
