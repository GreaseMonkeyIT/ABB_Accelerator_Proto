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
| D-014 | **S1 contention storage on a dedicated HDD** (`/dev/sdb` `slowdisk` static PVs); k3s control plane stays on NVMe so the slow disk makes the source actually stall | Active | LOG-046/047/048 |
| D-015 | **Same-node PSI re-admitted as a coupling witness for the SOURCE-edge path only** (`Witness.same_node` + `couples_source`); the bare psi-correlation path stays pvc/ebpf — enables S3 (CPU/mem contention, no network edge) without eBPF, preserving the LOG-061 false-positive fix | Active | LOG-073 |

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

## LOG-045 · 2026-06-14 · DIAGNOSIS + FIX — P4 chain: LOG-044 hypothesis wrong; 3 layered faults, crash fixed in code
What: Ran the LOG-044 in-pod S1 diagnostic. `/graph` meta = `status=error: all the input array dimensions except for the concatenation axis must match exactly ... index 0 size 180 ... index 1 size 57`; per-pod psi_io over a fresh S1 = cooling-monitor max 0.002 (onsets [(68,2.8),(169,3.0),(169,14.4)]), **timescaledb max 0.147 med 0.047 onsets []**, dcim-bridge max 0.003 onsets []. Both LOG-044 guesses (fetch-timeout; lower the |zpeak|≥3 filter) are wrong. Real picture — three distinct faults:
(1) CRASH (the actual intermittent `status=error`, NOT a timeout): unequal-length per-pod windows (180 vs a partially-filled 57) reach scipy in `lagcorr.corr_at_lag`; heavy-tailed psi_io takes the `spearmanr` branch → `np.column_stack` needs equal length → numpy shape error → the whole pass aborts. FIX (code, done): tail-align the pair at the top of `lagcorr.best_directed` (`n=min(len(s),len(d)); v[-n:]`). No-op when lengths already match → 13/13 fixtures untouched by construction. Also `service._fetch` timeout 5→10s for storm resilience.
(2) VICTIM INVISIBLE: timescaledb's real rise (0.047→0.147) gives ZERO raw cusum onsets, so the pipeline |zpeak|≥3 filter is irrelevant (nothing to filter). Cause in detectors.py: the one-step EWMA(α=0.3) residual adapts a *sustained* plateau away in ~3 samples, and the noisy checkpoint baseline inflates robust σ → +0.1 is ~2σ for ~2 effective samples < h=5. Lowering the filter (LOG-044) is a no-op here and would only fabricate onsets on noise-floor pods — explicitly NOT done; |zpeak|≥3 kept.
(3) SOURCE psi-INVISIBLE / storm too soft: cooling-monitor *causes* the I/O so it barely stalls (max 0.002 — registers only via noise); dcim-bridge at 0.003 isn't stalling at all. No psi_io on the source + a sub-noise victim set → no honest edge can form regardless of detector tuning.
DECISION: honest fix is physical, not a softer detector. Make S1 loud + fsync-heavy via the cooling-monitor Helm knobs (LOG-032: FIO_JOBS 4→6, FIO_FSYNC 8→4, FIO_RUNTIME→~90s; keep O_DIRECT) so (a) timescaledb clears its baseline noise and registers honestly, (b) dcim-bridge actually stalls → becomes a victim, (c) the writer's own fsync stalls lift cooling-monitor's psi_io a beat earlier → it leads → directional edge cooling-monitor→timescaledb(+dcim). Keep |zpeak|≥3. Mind SSD wear (LOG-044).
Impact: crash fix in `correlation/{lagcorr.py,service.py}` → needs image rebuild + `k3s ctr images import` + `kubectl rollout restart deploy/correlation-engine -n aiops`. Storm knobs are Helm-only (no rebuild). Gate met when /graph ranks cooling-monitor #1 with edges to timescaledb (+dcim) and a blast radius. The 4th hop to critical-control-relay (latency_p95) still needs OBI (deferred eBPF red), so the achievable chain now is the storage domain (source → disk victims). README/BUILD_GUIDE P4 status unchanged ("tuning").
Links: LOG-044 (superseded); LOG-032 (S1 knobs); LOG-043 (|zpeak| filter); LOG-041 (per-pod PSI); correlation/{lagcorr.py,service.py,engine/detectors.py}.

## LOG-046 · 2026-06-14 · DECISION (D-014) — S1 contention disk → dedicated /dev/sdb HDD (off the NVMe)
What: Crash fix verified live (meta clean: pods 13/active 2/accepted_edges 0, no status=error). But the victim is STILL invisible: storm 40s old, /graph findings = alert-dispatcher (onset_s 55s, noise) + cooling-monitor (onset_s 540s = idx 108, an OLD onset, not the storm tail near idx 172); timescaledb absent again. Root reason = the recurring "NVMe-too-fast" (LOG-024): fio can't hold a deep enough stall on the SSD for the victim's psi_io to separate from its noisy checkpoint baseline. Operator offered an empty 500GB 7200rpm disk (/dev/sdb, ST500DM002-1BD14) — format freely.
DECISION (D-014): put the S1 shared-contention storage on /dev/sdb; keep the k3s control plane (etcd/sqlite under /var/lib/rancher/k3s/server) on the NVMe. Mechanism = relocate ONLY the local-path root (/var/lib/rancher/k3s/storage) onto the HDD, so BOTH local-path PVCs that constitute S1 — tsdb-pvc (timescaledb data) and shared-logs-pvc (cooling-monitor fio target /shared/cooling + dcim /shared/dcim, confirmed via values.yaml mounts) — co-locate on the spinning disk and contend there, while control-plane I/O stays fast. No chart rewiring (PVCs stay default local-path). Zero SSD wear; a slow disk gives deep, sustained, variable stalls → the victim's psi_io should separate honestly (no detector softening). FIO retune (values.yaml, Helm-only no rebuild): FIO_FSYNC 8→4, FIO_RUNTIME 45→60; JOBS kept at 4 (HDD saturates at modest depth).
Apply (operator, box): skctl pause → kubectl delete pvc tsdb-pvc shared-logs-pvc -n factory-data (keep-annotated) → systemctl stop k3s → wipefs+mkfs.ext4 -L slowdisk /dev/sdb → mv the old storage dir aside + mount the HDD at /var/lib/rancher/k3s/storage (fstab LABEL=slowdisk) → systemctl start k3s → skctl up --mode solo (PVCs re-provision on the HDD; DB re-inits, synthetic). Verify: df -h /var/lib/rancher/k3s/storage = /dev/sdb; both PVCs Bound; re-run S1 → in-pod onset check shows timescaledb onsets; /graph ranks cooling-monitor #1 with edges to timescaledb(+dcim).
Watch (only if edges still 0 after the HDD): (a) detector fallback — add a sustained-level onset path in detectors.py gated by an ABSOLUTE floor so noise-floor pods (0.002) never fire; verify 13/13 before applying. (b) run_pass takes the FIRST |zpeak|≥3 onset — an early noise onset on the source can trip gate clause-3 "onsets too far apart" and reject the edge; a clean HDD source baseline should remove it. Cosmetic: alert-dispatcher fires spurious psi_io onsets but has no storage witness so it forms no edges (harmless to the chain).
Links: LOG-045 (3-fault diagnosis); LOG-032 (S1 fio knobs); LOG-024 (NVMe-too-fast first seen); D-012/D-013 (PVC keep + sizing); values.yaml (cooling-monitor FIO env); workloads/cooling-monitor/main.py (fio → /shared/cooling).

## LOG-047 · 2026-06-14 · D-014 MECHANISM REFINED — static `local` PVs on /mnt/slowdisk (no k3s stop, no addon edit)
What: Pre-move check on the box: local-path root still NVMe (`df` = /dev/nvme0n1p6, 197G), the just-recreated PVCs rebound on NVMe, and `local-path-config` is a **k3s Addon** (objectset owner-name local-storage) — so a hand-edit of its path would be reverted on k3s restart, and LOG-046's "relocate the whole storage root" needs `systemctl stop k3s` and would also move observability's local-path data. Refined mechanism (supersedes LOG-046's apply steps; D-014 unchanged): pin ONLY tsdb-pvc + shared-logs-pvc to the HDD with static `local` PVs, leaving the k3s addon and observability untouched, no restart.
Changes (laptop, committed-pending): deploy/slowdisk.yaml = StorageClass `slowdisk` (kubernetes.io/no-provisioner, WaitForFirstConsumer, Retain) + two `local` PVs on /mnt/slowdisk/{tsdb,shared-logs} with nodeAffinity `<NODE_NAME>`; templates/pvcs.yaml storageClassName now `{{ .storageClass | default "local-path" }}` (portable — a single-disk clone still gets local-path); values.yaml pins both factory PVCs to `storageClass: slowdisk`. cooling-monitor FIO already retuned (FSYNC 8→4, RUNTIME 45→60, LOG-046).
Apply (box, no k3s restart): `sudo mkfs.ext4 -L slowdisk /dev/sdb` → mount at /mnt/slowdisk (fstab LABEL=slowdisk) → `sudo mkdir -p /mnt/slowdisk/{tsdb,shared-logs}` → `./deploy/skctl pause` → `kubectl delete pvc tsdb-pvc shared-logs-pvc -n factory-data` → `NODE=$(kubectl get node -o jsonpath='{.items[0].metadata.labels.kubernetes\.io/hostname}'); sed "s/<NODE_NAME>/$NODE/g" deploy/slowdisk.yaml | kubectl apply -f -` → `./deploy/skctl up --mode solo`. **Sync the laptop chart edits to the desktop BEFORE skctl up** (else PVCs render local-path/NVMe again and FIO stays old); `helm template deploy/charts/factory >/dev/null` to catch a truncated sync. Verify: `kubectl get pv | grep slowdisk` Bound; pvc STORAGECLASS = slowdisk; `du -sh /mnt/slowdisk/tsdb` grows as the DB re-inits. Then re-run the S1 onset+/graph test.
Note: PVs are Retain — to recreate the PVCs later, re-apply slowdisk.yaml (delete+apply) to reset the PVs to Available.
Links: LOG-046 (D-014; mechanism superseded here); deploy/slowdisk.yaml; deploy/charts/factory/{templates/pvcs.yaml,values.yaml}; local-path-config (k3s Addon).

## LOG-048 · 2026-06-14 · STEP — D-014 applied & validated; blocker moves from physics to the engine
What: HDD storage live and confirmed. SSD util 1-2% vs HDD 100% under S1 (wear concern closed; both factory PVCs Bound on slowdisk static PVs, timescaledb pgdata initializing on /mnt/slowdisk). The slow disk transformed the signals: on a clean 13-pod window (after a `kubectl rollout restart deploy/aggregator` — see stale-pod note), **timescaledb psi_io max 0.504 / med 0.259** (was 0.147 on NVMe), **dcim-bridge max 0.119** with a real onset (idx 66, |z|4.5), cooling-monitor 0.077. Physical contention is now demo-grade.
BUT chain still not drawn (edges 0, root []). Two engine-level causes identified, both now the real P4 work (physics is done):
(1) timescaledb registers NO cusum onset despite a 0.5 stall — its baseline is **chronically high** on the slow disk (med 0.259), so there is no clean baseline→storm transition for the change-point detector; dcim-bridge (quiet baseline 0.027) onsets fine. The detector is blind to a sustained-high victim. Fix (planned): a floor-gated **sustained-level** onset path so a real ≥~0.15 sustained stall registers without a step.
(2) suspected **correlation dilution**: best_directed/corr_at_lag run Pearson/Spearman over the full 180-sample (15-min) vector, but the storm is only ~12 samples → r collapses toward baseline noise → no edge even when victims co-move. Fix (planned): correlate over the recent active window, not the whole ring. Pinpoint diagnostic (per-pair r + accept_edge clause) queued to confirm before editing.
Aggregator STALE-POD gotcha (operational): the aggregator never evicts dead pods, so across the migration's restarts /window reached **meta.pods=39** (3 replicaset generations), fragmenting correlation and giving spurious findings. `kubectl rollout restart deploy/aggregator -n aiops` flushes it (→13). Durable fix offered: evict a pod's ring after N missed scrapes (main.go, needs rebuild).
Impact: next = run the pinpoint diagnostic → implement detector sustained-level + correlation-window fixes in correlation/{detectors.py,lagcorr.py/pipeline.py} → verify 13/13 in sandbox → rebuild skn/correlation-engine:v0.1 + import + rollout restart → re-run S1. Watch: timescaledb's chronic 0.26 baseline may mean the HDD is near the DB's throughput ceiling (ingestion-lag risk); dial FIO/ingest if it destabilizes.
Links: LOG-047 (D-014 mechanism); LOG-045 (3-fault diagnosis; sustained-level + correlation-window foreseen); LOG-041 (aggregator PSI); correlation/{detectors.py,lagcorr.py,pipeline.py}; aggregator/main.go (stale-pod eviction).

## LOG-049 · 2026-06-14 · DECISION + STEP — threshold-free causal fix: windowed correlation + topology-witnessed pairs (sandbox-validated)
What: Operator raised the core architecture point — the engine must attribute by causal correlation + known topology, NOT by comparing to preset resource limits (psi>0.15 etc.), else it's just threshold monitoring (which exists). This killed the planned "mark victim active when psi>0.15" idea (rightly). Reframed the fix to stay fully adaptive.
Pinpoint diagnostic (live) confirmed the real blocker: correlations are NOISE over the 15-min ring — cool~tsdb r=0.15, cool~dcim 0.15, tsdb~dcim −0.18 (all « R_PEAK 0.6); a window sweep showed r climbing to **0.67 (cool~tsdb) at the last 24 samples**. The storm is ~12 of 180 samples, so the full-ring Pearson drowns; timescaledb additionally anti-correlates because it's chronically stalled (med 0.25) while the quiet source sits near 0 between events.
Root insight from the fixtures (correlation/tests/test_engine.py): every fixture plants its disturbance MID-window in low noise (onset=100, noise 0.2) — that unrealistic, high-SNR placement is exactly why the suite went 13/13 yet the engine failed on a real recent, low-SNR storm.
FIX (threshold-free, correlation/{pipeline.py,service.py}):
 (1) **Windowed attribution** — run_pass gains `corr_window: int|None=None`; when set it correlates the recent slice `v[-corr_window:]` (detection still uses full history). Default None ⇒ every fixture identical (13/13 preserved by construction). service.py sets it from env `CORR_WINDOW` (default 24, ~2min) — a signal-processing window matched to the event timescale, not a resource limit.
 (2) **Topology-witnessed pair eval** — a pair is now evaluated if it touches an anomalous pod OR (once the system is disturbed) if `witness.kinds(a,b)` shows a physical coupling (shared disk / same node). This pulls a chronically-loaded victim with no clean onset of its own into the graph by CORRELATION over a shared disk — never by a threshold. Idle stays empty (disturbed=False ⇒ no edges); non-witnessed innocents still excluded.
Validation (sandbox, mount healthy): `pytest tests/` = **13/13**. End-to-end sim on real-shaped data (chronic victim + recent storm + stale decorrelating history): corr_window=None ⇒ edges [], root [] (reproduces the live failure); corr_window=24 ⇒ **cooling-monitor→timescaledb (r 0.76) + dcim-bridge→timescaledb (r 0.75), root=cooling-monitor, evidence [stat,pvc]** (no threshold in the path).
Impact / apply: sync to the box → `make test` (must stay 13/13) → rebuild skn/correlation-engine:v0.1 + `k3s ctr images import` + `kubectl rollout restart deploy/correlation-engine -n aiops` → re-run S1 and check ~50s after the trigger (the window must contain the storm's RISING edge; a late check that catches only the plateau won't correlate — onset-centred windowing is the robustness follow-up if this proves fiddly). 
Still-preset bits flagged for the same adaptive treatment later (operator's point): aggregator thresholds in values.yaml/queries.yaml (L2 alert hint only — L3 causal path no longer depends on them), service COPR_MIN (psi_copressure witness), gate R_PEAK 0.6. None gate the S1 causal path now (shared_relation topology + windowed correlation do).
Links: LOG-048 (blocker→engine); LOG-045 (correlation-window foreseen); correlation/{pipeline.py,service.py,tests/test_engine.py}; gate.py (R_PEAK); values.yaml (aggregator thresholds).

## LOG-050 · 2026-06-14 · STEP — windowing must wrap the WHOLE pass, not just correlation (post-rebuild fix)
What: First windowed build deployed; live /graph still edges=[] but now **active=3 incl. timescaledb** (detection improved). Root cause of the remaining empty graph: the 15-min ring holds SEVERAL past S1 firings (onsets came back at 165s / 695s / 800s = three different storms), and LOG-049 windowed only the *correlation* — detection + temporal still ran on the full ring, so each pod's onset pinned to a different event and the temporal gate rejected every pair (onsets 100-600s apart). 
FIX (correlation/pipeline.py): the `window` now slices the vectors **once at the top of run_pass**, so detection, correlation AND ordering all see the same recent slice — one coherent disturbance. Bonus: over a ~3-min slice a chronically-loaded pod (timescaledb) shows a clean local step instead of a flat-high baseline, so it onsets honestly. Renamed param corr_window→`window`; service env CORR_WINDOW→`ANALYSIS_WINDOW` (default **36** ≈ 3min). Default None ⇒ full ring ⇒ fixtures unchanged.
Validation: sandbox multi-storm sim (an OLD storm at idx ~40 + the recent one + chronic tsdb) — whole-pass W=36 ⇒ **root=[cooling-monitor], edges = cooling→dcim→timescaledb (0.97/0.84/0.85)**; W=24 too short (detection finds nothing), W=48 works but root muddier (cooling+dcim). 13/13 fixtures pass (window=None default). NOTE: the just-now re-run was blocked by a recurring Syncthing mount-tear in the bash sandbox (truncated pipeline.py / stale import) — file tool confirms the real source is correct, and the identical behaviour was validated in the prior healthy run on pre-sliced vectors; box `make test` is the authoritative gate.
Apply: sync → `make test` (13/13) → rebuild skn/correlation-engine:v0.1 + import + `kubectl rollout restart deploy/correlation-engine -n aiops` → fire S1, read /graph ~50s later. Tunable live (no rebuild): `kubectl set env deploy/correlation-engine -n aiops ANALYSIS_WINDOW=48`. Optional: `kubectl rollout restart deploy/aggregator` before the run to start with a cleaner ring (the whole-pass window also handles it). Follow-up if still fiddly: onset-centred window (centre on the detected disturbance rather than the clock).
Links: LOG-049 (correlation-only windowing, superseded); correlation/{pipeline.py,service.py}; LOG-041 (aggregator ring); gate.py (temporal clause).

## LOG-051 · 2026-06-14 · STEP — FIRST causal edge drawn live (threshold-free); root-accuracy + ops gotchas remain
What: Whole-pass-window build (LOG-050) deployed. On S1, /graph produced a real edge: **dcim-bridge→timescaledb, r=0.654, evidence=[stat,psi,pvc]** (statistical correlation + PSI co-pressure + shared-disk topology — three independent witnesses, NO resource threshold anywhere), root_cause_ranking=[dcim-bridge score 1.0], blast_radius=[timescaledb 0.458], timescaledb in findings (onset, shift). The "beyond-monitoring" causal mechanism is alive end-to-end on real cluster data. timescaledb detection confirmed fixed by whole-pass windowing (chronic baseline → clean local step).
GAPS (honest, not bugs): (1) Root is dcim-bridge (a victim), not cooling-monitor (the true source). cooling-monitor is the fio WRITER — it causes the I/O rather than stalling on it, so its psi_io is weak/intermittent and it never entered the graph; the engine then ranks the most-upstream VISIBLE pod (dcim) as root. (2) lag_s=0 on the edge: at the 5s scrape cadence the cascade is sub-sample, so direction is ~undetermined (the dcim→tsdb orientation is effectively a coin-flip from zero-lag). psi_io fundamentally can't separate a non-stalling source from its victims.
OPS GOTCHA: `kubectl rollout restart deploy/aggregator` right before a run STARVES the analysis window — a fresh ring (~90s) < the 36-sample (3-min) window's baseline need; run 1 was active=0 for exactly this. DON'T restart before a run; let the ring sit ≥5min, fire S1 once, read ~45s later (the whole-pass window already tolerates old storms).
NEXT (cheap→deep): (a) values.yaml FIO_FSYNC 4→2 so the writer stalls + co-moves with the victims → cooling-monitor correlates with MULTIPLE victims → wins root by explanatory reach even at lag 0 (Helm-only, no rebuild; raise back to 4 if the node drags). Re-run with a filled ring. (b) if still mis-rooted: the principled fix is a per-pod write-rate signal (the source writes, victims stall — that's what truly distinguishes them) → multi-signal engine, a real extension. (c) faster scrape (5s→2s) to resolve the cascade lags so direction is real. Try (a) first.
Links: LOG-050 (whole-pass window); LOG-032 (FIO knobs); values.yaml (cooling-monitor env); aggregator queries.yaml interval_s (scrape cadence); service.py (single-signal psi_io, ENGINE_SIGNAL).

## LOG-052 · 2026-06-14 · STEP — time-alignment of the window (operator-spotted correctness bug; likely the intermittency)
What: Operator's catch: the engine correlates POSITIONALLY (index i of pod A vs index i of pod B) but the two are not the same wall-clock instant. Confirmed in aggregator/main.go — Sample.TS is `time.Now()` at poll time (L209) and Ring is a blind positional append (L40-48); `series()` (L50) hands L3 bare values with the ts stripped. psi_io is gappy (a quiet pod emits a stall sample only when it stalls) and pods restart (fresh short ring), so column i drifts pod-to-pod (operator saw ~1-min skew at sample #100). Lagged cross-correlation across that skew is garbage → exactly the run-to-run intermittency we kept hitting (edges appear only when the skew happens to be small).
FIX (correlation/service.py build_inputs — engine-side, no aggregator rebuild): resample every pod onto ONE shared wall-clock grid (n=180 @ GRID_STEP_S=5s ending at the newest ts) by parsing each sample's `ts` (Go RFC3339 → epoch). Sample-and-hold within one step; psi_io gaps→0 (no stall). Stale pods (last sample older than the grid) drop automatically — this ALSO retires the LOG-048 ghost-pod accumulation (no aggregator restart needed before a run). New env POLL_S (grid step).
Verified (inline heredoc, mount torn again for service.py — file tool confirms the real file is complete): a RESTARTED pod (120 samples, offset start) lands its storm at the SAME grid columns (168-179) as a full-ring pod; a dead pod (stale ts) is dropped. The 13 engine fixtures are untouched (build_inputs is service I/O, not exercised by tests/).
Apply: sync → rebuild skn/correlation-engine:v0.1 + import + `kubectl rollout restart deploy/correlation-engine -n aiops`. (FIO_FSYNC=2 from LOG-051 still pending a skctl up if not yet applied.) Re-run S1 with a filled ring, no aggregator restart. Expect markedly more reliable edges now that correlation sees time-correct vectors.
Architecture note (operator's "an array/db should hold the time scale"): done engine-side for now; the cleaner home is the aggregator maintaining a bucketed time grid natively (or a TimescaleDB-backed buffer) so /window is aligned at the source and the L4 dashboard shares it — logged as a P6/hardening follow-up, not needed for the causal path.
Links: LOG-051 (root accuracy); LOG-048 (ghost pods, now retired); aggregator/main.go (Sample.TS/Ring); correlation/service.py (build_inputs, _epoch, GRID_STEP_S).

## LOG-053 · 2026-06-14 · NOTE — time-alignment cleared (no regression); `active=0` was storm transience, not a bug
What: After the LOG-052 build, two S1 runs read active=0 — looked like a regression. It isn't. In-pod diagnostic on the live /window: all pods n=180, **fromisoformat_ok=180/180** (the 3.12 image parses Go RFC3339Nano fine; the earlier sandbox FAIL was Python 3.10), timestamps clean + already grid-aligned (cooling & tsdb ts[0]/ts[-1] identical to the microsecond, newest_age 2s), and the data is rich — **timescaledb max 1.307**, cooling 0.145, dcim 0.103. Sandbox check on real-shaped data: the aligned last-36 vector is **identical** to the old positional one (`np.allclose` True) and CUSUM fires the **same** onset (idx 23, |z|33.6). So build_inputs is a no-op on already-aligned data (steady state) and only helps on restart/gap skew — correct and harmless. The two active=0 reads were simply check moments where the transient storm had aged out of the 3-min window (60s fio + 30s psi_io rate-lag = a narrow detectable window).
ROOT-ACCURACY reality (from the same dump): psi_io magnitudes are tsdb 1.307 ≫ cooling 0.145 ≈ dcim 0.103 — the heavy DB writer (a VICTIM) stalls hardest; the fio SOURCE barely stalls. psi_io alone still can't crown the source. Unchanged from LOG-051.
FIX (reliability, values.yaml, Helm-only): FIO_RUNTIME 60→120 so the storm outlasts the rate-lag + check jitter → reliably present in the recent window on any check. Re-run: apply (skctl up), fire S1, wait ~50-60s, read /graph WHILE it's still running (don't check minutes later — it's a live window, not a log).
Status: engine + alignment correct and working (multi-evidence threshold-free edges proven, LOG-051). Open: (1) reliable repro = sustained storm (this entry); (2) source-as-root = needs the write-rate signal (multi-signal, operator go-ahead) or faster scrape — both still open from LOG-051.
Links: LOG-052 (alignment); LOG-051 (root accuracy + write-rate plan); values.yaml (FIO_RUNTIME); aggregator scrape rate-lag (queries.yaml rate windows).

## LOG-054 · 2026-06-14 · STEP — event-centred analysis (operator's "search the series, don't poll a slice"); supersedes fixed-window
What: Operator's point: lengthening the storm is a band-aid — the data already lives in the ring; the periodic calculation should SEARCH the series for the disturbance (where + how long) instead of staring at the last 3 min. Correct, and it removes the transience that caused LOG-053's active=0. Replaces the LOG-050 fixed last-N window.
FIX (correlation/pipeline.py): (1) DETECT over the FULL ring (find onsets wherever they are; cusum gets its clean pre-event baseline) and record the strongest onset = the event centre. (2) CORRELATE on a slice CENTRED on that event (`lo=center-window//3`, width=window) so the storm dominates r AND an event minutes old is still analysed. Key gotcha proven in-sandbox: do NOT re-detect inside the slice — the event lands before cusum's warmup(12)/sig_n(24) and vanishes; keep the full-ring onsets, narrow only the correlation. window=None ⇒ full-ring correlation (fixtures unchanged).
Validation (sandbox, mount healthy): an AGED storm (~7 min back, idx ~100, well outside any recent window) ⇒ fixed-last-36 finds NOTHING; event-centred(36) ⇒ **root=[cooling-monitor], edges cooling→dcim(0.94)/cooling→timescaledb(0.97)/timescaledb→dcim(0.95)**. Fixture chain (window=None) ⇒ edges≥3 & root==coolmon. `pytest tests/` = **13/13**.
Also: reverted FIO_RUNTIME 120→60 (LOG-053 band-aid no longer needed — duration is not load-bearing now).
Apply: sync → make test (13/13) → rebuild skn/correlation-engine:v0.1 + import + rollout restart engine. Then S1: fire, wait ~45-50s, read /graph — and it should hold even if you read a couple minutes later (the engine locates the event by detection, not by clock).
Open (unchanged): source-as-root still rides on FIO_FSYNC + ultimately the write-rate signal (LOG-051); but event-centring already put cooling-monitor first in the strong-storm sandbox case.
Links: LOG-050 (fixed window, superseded); LOG-053 (transience this fixes); LOG-051 (root accuracy); correlation/engine/pipeline.py (peak/cvec); QUICKSTART.md (from-scratch run).

## LOG-055 · 2026-06-14 · STEP — timescaledb chronic baseline is VOLUME-bound; cut the ingest rate so it's a clean S1 victim
What: After the event-centred build, /graph still drew no edge: only cooling-monitor onsets (weak, |z|3.7); timescaledb max 0.958 but **onsets=[] with med 0.477** — chronically saturated, even higher than before. A chronically-stalled victim can't onset (no clean baseline) and won't correlate (always-high vs the source's brief spike). 
Root cause (from the source, NOT commit-fsync): `synchronous_commit=off` is a red herring — telemetry-ingest/main.py batches ~500 rows and commits only ~4×/s (line 28-32), far under the HDD's fsync limit. The real load is VOLUME: plc-gateway/main.go publishes **200 channels × 10 Hz = 2000 rows/s** (100ms ticker), and that continuous WAL + checkpoint stream on the 7200rpm disk pins timescaledb at ~45% psi_io baseline. (Operator's earlier ALTER SYSTEM also errored — can't share a `-c` with another statement — but it wouldn't have helped anyway.)
FIX (workloads/plc-gateway/main.go + values.yaml): made the publish rate env-tunable — `PLC_PERIOD_MS` (default 100=10Hz) and `PLC_CHANNELS` (default 200); set `PLC_PERIOD_MS: "1000"` (1 Hz → ~200 rows/s, 10× less). timescaledb should now idle quiet (target recent med < ~0.1) and only stall under the fio storm = a CLEAN victim with a real onset, which is also the more faithful S1 cascade story (calm baseline → contention causes the stall, not a permanently-pinned DB). 14-day data still ample at 200 rows/s.
Apply: rebuild skn/plc-gateway:v0.1 + import → `skctl up --mode solo` (applies the env) → `kubectl rollout restart deploy/plc-gateway -n factory-core`. Wait ~5 min, confirm timescaledb recent med drops < ~0.1, then fire S1 — expect a clean tsdb onset + the cooling→tsdb/dcim edge. If med stays high at 200 rows/s, it's checkpoint-bound → next lever is an UNLOGGED `readings` table (init.sql, no WAL) or lower the rate further (PLC_PERIOD_MS 2000+).
Links: LOG-051/053 (root accuracy + transience); workloads/{plc-gateway/main.go,telemetry-ingest/main.py}; values.yaml (plc-gateway env); timescaledb init.sql (UNLOGGED fallback).

## LOG-056 · 2026-06-14 · STEP — **P4 GATE MET: S1 causal chain drawn live, correct root, threshold-free**
What: After the rate cut (LOG-055), timescaledb recent med 0.477→**0.128** (clean baseline). S1 → /graph:
  root_cause_ranking = [**cooling-monitor** score 1.0]; edge **cooling-monitor→timescaledb r=0.693 lag_s=30 evidence=[stat,pvc,temporal]**; blast_radius=[timescaledb impact 0.485 eta 30s]; findings = cooling-monitor(flap, onset 70s) + timescaledb(shift, onset 105s); active=2, accepted_edges=1.
Everything correct: (1) the true SOURCE (the fio writer, cooling-monitor) is ranked #1 — not a victim; (2) direction is causal — lag 30s AND onset ordering (cooling 70s precedes tsdb 105s) agree, so `temporal` joins the evidence for the first time; (3) three independent witnesses, **no resource threshold anywhere** (stat correlation + shared-disk topology + temporal precedence); (4) timescaledb onsets honestly now that it idles quiet. The whole stack proven end-to-end on real cluster data.
This closes the loop on the long P4 debug arc: crash (LOG-045) → HDD so the source is visible (D-014/LOG-046-48) → threshold-free windowed+witnessed correlation (LOG-049) → whole-pass then EVENT-CENTRED analysis (LOG-050/054, operator's "search the series") → time-alignment (LOG-052) → and finally a clean victim baseline (LOG-055). The write-rate multi-signal (LOG-051) is NOT needed — a clean baseline gave correct source attribution on psi_io alone.
Impact: **P4 done-when met** (engine ranks cooling-monitor #1 with a victim edge + blast radius, live). Confirm repeatability over a few S1 runs. Then: README/BUILD_GUIDE P4 → done; remaining enrichment (not blockers): pull dcim-bridge in as a co-victim (slightly louder S1 or it onsets on its own run), the 4th hop to critical-control-relay needs OBI latency (deferred eBPF red), and L4 (Ollama narrator + dashboard, P5/P6) renders this verdict.
Links: LOG-055 (rate cut); LOG-054 (event-centring); LOG-049 (threshold-free); LOG-052 (alignment); BUILD_GUIDE P4 done-when; MASTER_PLAN §1.4.

## LOG-057 · 2026-06-14 · STEP — P4 status squared in docs; EXPLANATIONS rebuilt; L4 API gateway added (P6 seam)
What: Operator asked to (1) square the status docs, (2) recreate EXPLANATIONS as a per-file end-to-end reference, (3) add a frontend-agnostic API.
(1) README intro + status table and BUILD_GUIDE P4 now read DONE with the live result (cooling-monitor root, threshold-free edge to timescaledb); P2 row clarified (core taps live, eBPF/Loki deferred).
(2) EXPLANATIONS.md rewritten from the chronological Q&A journal into a structured "how it works" map: the idea, the L0→L4 flow, an end-to-end S1 trace through the files, then every significant editable file by layer (workloads, telemetry values, aggregator, engine modules, deploy/skctl/chart/slowdisk, scenarios), the no-rebuild knobs, and the 5 design principles. Decision history stays in BUILD_LOG.
(3) **api/** = FastAPI gateway (skn/api:v0.1, ns aiops, :8088): proxies + NORMALIZES the L3 engine + L2 aggregator into clean JSON with permissive CORS and auto OpenAPI (/docs) so any frontend consumes it without knowing internal services. Endpoints: GET /api/health, /api/graph (root/edges/blast/findings, pod names collapsed to workloads), /api/pods (hot-sorted snapshot + anomalous flag), /api/signal/{pod}, /api/events, /api/scenarios, POST /api/scenarios/S1/trigger (arms cooling-monitor /flush; S2-S5 still via trigger.sh). Files: api/{main.py,Dockerfile,requirements.txt}, deploy/api.yaml; skctl `engine` step now also applies api.yaml. Verified in-sandbox: imports clean, workload-name normalization + /api/graph + /api/pods shaping correct against mock upstreams.
Apply: `docker build -t skn/api:v0.1 api/ && docker save … | sudo k3s ctr images import -` → `skctl up --mode solo` → `kubectl port-forward svc/api -n aiops 8088:8088` → http://localhost:8088/docs. Add api to `make import` when convenient.
Links: README/BUILD_GUIDE (P4 done); EXPLANATIONS.md; api/main.py; deploy/{api.yaml,skctl}; QUICKSTART.md.

## LOG-058 · 2026-06-16 · STEP + DECISION — L3 permanent evolutionary memory split from 14-day telemetry
What: L3 now has a persistent SQLite memory layer (`correlation/engine/state.py`) mounted on `engine-memory-pvc` by `deploy/engine.yaml`. It stores edge confidence/hysteresis, held/decaying graph edges, encountered case fingerprints, graph snapshots, model-version rows, and mistake/correction records. The service bootstraps `/graph` from this memory before fresh samples arrive, then evolves it on every `run_pass` output. Added focused tests in `correlation/tests/test_state.py` and documented the lifetime split in README/EXPLANATIONS.
Why: Operator clarified that the telemetry DB may be a 14-day rolling store, but the agent must remember indefinitely and evolve across the entire project timeline. Learned cases and corrections must not disappear with raw telemetry retention, and L3 should not rebuild the whole graph from scratch when persisted memory is already valid.
Impact: L2's current `/window` remains a 15-minute live ring; the planned 14-day absolute-time sample/event store is still the next ingestion slice. L3 memory is permanent by default and intentionally uses `local-path`, not the HDD-backed `slowdisk` L0 storm volumes. New env knobs: `MEMORY_DB`, `EDGE_ALPHA`, `EDGE_DECAY`, `EDGE_SHOW`, `EDGE_HIDE`.
Links: correlation/engine/state.py; correlation/service.py; deploy/engine.yaml; correlation/tests/test_state.py; README.md; EXPLANATIONS.md.

## LOG-059 · 2026-06-19 · FIX (A1) — edge_memory keyed by workload, not pod-hash; ghosts killed at render
What: `state.py` now keys `edge_memory` by `stable_workload(src/dst)` instead of the full pod name (pod names carry a ReplicaSet+pod hash that changes on every restart). `_confirm_edge`, `observe`, and `_decay_absent_edges` work in workload space; `_render` looks edges up by workload but **remaps held edges back to the CURRENT pod** for `/graph`, and **skips any whose workload has no live pod** (a gone generation can never be served as active). `SCHEMA_VERSION` → `l3-memory-v2` with a one-time `_migrate()` that clears `edge_memory` on the version bump — the permanent archive (`cases`, `case_observations`, `graph_snapshots`) is preserved. Two regression tests added (persistence across a pod-hash change; absent-workload edge not rendered as a ghost). `run_pass` + its 13 fixtures, `service.py`, `build_inputs`, and `api/` are all untouched (17/17 tests pass locally and on the box).
Why: Live memory DB showed `edge_memory` keyed by ephemeral pod names: a dead generation's edge `dcim-bridge-…-9knkf → timescaledb-…-sxrvp` sat at conf 0.87, **last seen 38 h ago**, and was being served as the *active* root cause, while the live pods' edges had reset to conf 0. Pod identity is throwaway; the workload is the stable identity (cases were already workload-keyed — only `edge_memory` wasn't). Keying by workload lets confidence accumulate and persist across restarts; rendering to the current pod keeps `/graph`'s pod-name contract (and `api/main.py`) intact while never showing a stale name.
Impact: Verified on cluster — after rollout the migration left `edge_memory: 0` / `cases: 22`; idle `/graph` is clean (ghost gone); after S1 the row is keyed `{'src':'dcim-bridge','dst':'timescaledb'}` (no hash) and `/graph` renders the current pods. Chosen approach is **render-skip-and-preserve**, not decay-the-ghost: a stale edge is kept in the DB (for retraining) but withheld from `/graph` — this honours the permanent-memory intent. The fix **exposed (did not cause)** the pre-existing direction/detection problem: the verdict blames the victim `dcim-bridge`, not the source `cooling-monitor`, and the acceptance flaps. Deferred to iterative R&D (unchanged by A1): the Route-1 case **merge/matcher**, the 14-day **time-matrix store**, the **structural baseline / default edge weights** (A2), and **direction stability**.
Links: correlation/engine/state.py; correlation/tests/test_state.py; DESIGN_stateful_engine_and_case_library.md §1.2/§3.2; LOG-058 (memory layer this builds on).

## LOG-060 · 2026-06-19 · FIX (R&D step 1) — source signal (io_write) + writer→staller attribution; the SOURCE is now blamed
What: Added a per-pod disk-WRITE signal and cross-signal source attribution. `aggregator/queries.yaml` gains `io_write = sum by (namespace,pod) rate(container_fs_writes_bytes_total[30s])` (ConfigMap reload, no L2 rebuild). `service.py build_inputs` now resamples io_write onto the same grid as psi_io and returns `write_vectors`. `engine/pipeline.py run_pass` takes an optional `write_vectors=None`; when present it adds **source edges** via `_writer_edge`: `lag_profile(write[src], psi[dst])` over a shared-disk/eBPF witness, |r|≥`R_SRC`(0.5) + adjacent support, writer-leads-staller temporal check, **direction FIXED src→dst**. A dedup keeps one edge per unordered pair and lets a write-evidenced (source) edge win direction conflicts over a victim↔victim psi edge (direction stability). New env `WRITE_SIGNAL=io_write`. New test `test_source_attribution_blames_writer_not_staller`; the 13 run_pass fixtures are untouched (optional param ⇒ identical default path), 18/18 green local + on the box.
Why: The diagnostic proved psi_io sees only *stallers* (victims). The S1 aggressor cooling-monitor writes **60–126 MB/s with psi_io ≈ 0.008** — invisible to the stall signal — so the engine correlated victim↔victim and blamed the victim (dcim-bridge). A source-side write signal makes the aggressor visible; orienting writer→staller grounds direction in physics instead of a near-simultaneous lag coin-flip. cAdvisor `container_fs_writes_bytes_total` is per-pod, so **no eBPF/Inspektor Gadget needed** for basic source attribution.
Impact: Verified on cluster (S1 watch): root flips to **cooling-monitor (1.00)** with `cooling-monitor→timescaledb [write+pvc+temporal]` r≈0.84–0.93 and `cooling-monitor→dcim-bridge [write+pvc]`, stable for the whole storm; A1 memory holds the edge through gaps. **Open:** post-storm the edge decays to nothing (no structural baseline yet — that is step 2). Remaining R&D queue: step 2 structural baseline / default edge weights (A2), step 3 Route-1 case-merge, step 4 14-day time-matrix store.
Links: aggregator/queries.yaml; correlation/service.py; correlation/engine/pipeline.py; correlation/tests/test_engine.py; LOG-059 (A1 persistence this builds on).

## LOG-061 · 2026-06-19 · FIX (R&D step 2 + source/gate hardening) — structural baseline; causal edges require a real contention signature
What: (Step 2) `state.py` gains a learned per-edge **structural floor** (`base_conf`, schema v3 with auto-`ALTER` migration): a confirmed edge ratchets `base_conf = floor_frac·peak`, decay floors there instead of zero, and `_seed_structural` (fed the `witness` from `service.py`) maintains every shared-disk pair at AT LEAST the topology prior — so the steady-state coupling backbone exists at idle and edges brighten under load instead of fading to nothing. `_render` shows the backbone (`state=steady`) + `render_weight`, deduped one-per-pair. New env `EDGE_PRIOR`, `EDGE_FLOOR_FRAC`. (Hardening, found while verifying Step 2 on the cluster) source edges now require **(a)** the source out-writes the victim, **(b)** the source actually deviated (a write onset — a routine pod that *starts* storming still qualifies), **(c)** positive write→stall coupling; and `gate.accept_edge` now also requires **positive** psi coupling (`r ≥ R_PEAK`, not `abs`). Also adopted **(A)**: present the scored `root_cause_ranking` + `blast_radius` distribution, not a single hard root. 25 tests; 13 run_pass fixtures untouched.
Why: Step 2 — edges decayed to zero on quiet because there was no normal-state baseline to settle onto. Hardening — psi_io sees only *stallers*, so the source signal (io_write) plus the cross-signal gate could mis-attribute: a database's tiny baseline writes (timescaledb), or an anti-correlated pair, looked like causal sources. Three distinct false positives (victim-as-source, minor-writer-as-source, anti-correlated edge) surfaced ONLY on real cluster data — the clean positive-correlation unit fixtures never exercised the sign/magnitude cases. A real contention edge has a signature: the dominant hog that deviated, positively coupled to the victim's stall.
Impact: Verified on S1 — `root=cooling-monitor`, all edges positive `[write+pvc(+temporal)]`, graduated steady backbone at learned floors, blast-radius distribution (tsdb/dcim). Migrated DB needed a one-time clear of one reversed legacy row; a from-scratch DB is clean by construction. Remaining: R&D step 3 (Route-1 case-merge) is the last fix; then the from-scratch test + mark-one/mark-zero branch. time-store (step 4) deferred to mark-two.
Links: correlation/engine/{state,pipeline,gate}.py; correlation/service.py; correlation/tests/{test_state,test_engine}.py; DESIGN §1.1/§1.3/§3.2; LOG-060 (source signal this builds on).

## LOG-062 · 2026-06-19 · FIX (R&D step 3, last engine fix) — Route-1 conservative case-merge replaces exact-hash identity
What: `_promote_case` no longer keys a case by an exact SHA1 of its fingerprint. It computes a structured fingerprint (stressors/victims/motif as sets + signal + physical witness), finds the nearest stored case by **weighted Jaccard** similarity (`_case_sim`: victims 0.40, motif 0.40, stressors 0.20; hard-gated by signal + witness_kind), and: **recurrence** (sim ≥ `tau_merge` 0.85) folds into it; **variant** (≥ `tau_family` 0.60) opens a new case sharing the matched `family_id`; **novel** (< 0.60) opens a new case + family. The prototype is kept **stable** (a fold bumps occurrences + averages `typical_lead_time_s`, it does NOT churn victims/motif), so a case doesn't drift toward its last variant and lose its own family; full per-incident history stays in `case_observations`. New `cases.family_id` (schema v4, auto-`ALTER`; legacy cases each become their own family). `/graph.meta` gains `case_register` (recurrence|variant|novel), `case_family`, `case_sim`; `stats` gains `families`. `_dominant_witness` now ignores `write` so witness_kind stays the physical coupling (pvc/ebpf/psi). New env `CASE_TAU_MERGE`, `CASE_TAU_FAMILY`. 28 tests; 13 run_pass fixtures untouched.
Why: the exact-hash identity minted a brand-new case for every motif/victim/lead permutation, so the live DB held 22 near-duplicate + wrong-direction cases for what is really ~2 problem types. A variation is an **alteration of a type, not a new type** — the engine must recognize that and say so (`case_register`). Lead/lag time is an averaged *attribute*, not an identity feature, so it no longer splits structurally-identical incidents.
Impact: local simulation — 32 incidents across 4 S1-shaped fingerprints collapse to **3 cases / 2 families**; structural variants group under one family, the wrong-direction pattern stays a separate family. This completes the four engine fixes (A1 persistence, source attribution, structural baseline, case-merge). Conservative thresholds can be tuned once the P7 labeled runs exist; a learned classifier stays deferred (DESIGN §3.2). Deviation from §3.2 as written: dropped the lag term from similarity (averaged attribute) and use 0.40/0.40/0.20 weights. Next: the from-scratch test, then mark-one (this corrected engine) / mark-zero (baseline 1d4315a) / mark-two (time-store).
Links: correlation/engine/state.py; correlation/tests/test_state.py; DESIGN §3.2; LOG-061 (structural baseline this builds on).

## LOG-063 · 2026-06-19 · FIX (R&D step 4) — incident = deviation from a learned per-pod baseline (S0 is now silent)
What: A psi onset only becomes an incident **finding** if the pod's sustained psi (p90) exceeds **its own** learned steady-state by `dev_k` robust deviations (`median + dev_k*MAD`). `state.py` learns a persistent per-workload baseline (`baselines` table, schema v5; robust median+MAD slow-EWMA, `base_alpha`; a storming workload is skipped so the baseline stays the NORMAL); `baseline_threshold()` returns the per-pod incident threshold once mature (`base_min_n`), else None. `service.py` passes per-pod thresholds into `run_pass(..., baselines=)`; `pipeline.py` gates onsets (None arg = fixtures, ungated; None value = still-learning ⇒ not an incident). Gating at *detection* silences everything downstream at once. New env `BASE_ALPHA/DEV_K/MAD_FLOOR/BASE_MIN_N`. 30 tests; 13 run_pass fixtures untouched.
Why: The from-scratch test exposed that S0 was NOT silent — at steady-state the engine rooted on the routine DB writer (timescaledb), because it detected *any* disturbance, not *deviation from the established normal*: normal factory I/O genuinely contends on the shared HDD, and timescaledb's baseline psi is elevated. This is the "Case 0 deviation" principle (DESIGN §4) and is threshold-free in the resource sense — the band is self-calibrated per pod (a z-test vs the pod's own history), not a fixed `value > limit`.
Impact: Verified on cluster — after ~10 min warmup, **S0 silent** (`findings=0, root=[], cases=0`; learned baselines: timescaledb med 0.13/mad 0.035, dcim 0.028, cooling 0.003, others 0) and **S1 live verdict roots cooling-monitor (0.71)** via `cooling→timescaledb [write+pvc+temporal]`. Requires a warmup (baseline maturity) — by design the engine is "silent + learning" until then. **Open residual** (tracked in REMAINING.md §1): between storm pulses the live source edges decay to the floor and a stale victim-cascade edge can transiently win the root → an occasional wrong-direction case; fix = promote a case only from a source-rooted verdict.
Links: correlation/engine/{state,pipeline}.py; correlation/service.py; correlation/tests/{test_state,test_engine}.py; REMAINING.md; LOG-061 (structural baseline this builds on).

## LOG-064 · 2026-06-19 · STEP (P5 + P6 scaffold) — narrator endpoint + custom causal dashboard (local-verified, box-pending)
What: L4 work, three slices. (A) `api/main.py` `/api/graph` now FORWARDS the engine's per-edge enrichment it was silently dropping — `confidence`, `state`, `render_weight`, `source` (workload-name collapse unchanged); root/blast/findings + meta (incl. `case_register/family/sim`) already passed through. (B) NEW `GET /api/narrative` — the one LLM: reads the normalized graph, builds a compact evidence prompt, calls Ollama at `OLLAMA_HOST` (`OLLAMA_MODEL` default `gemma4:e4b`), returns `{text, source: llm|fallback, model, ts}`. A deterministic `_template_narrative()` is always available — unset/unreachable/slow Ollama ⇒ template sentence, so the verdict never depends on the model (REMAINING.md P5). `deploy/api.yaml` gains `OLLAMA_MODEL` + (empty) `OLLAMA_HOST` knobs. (C) NEW `dashboard/` = Next.js STATIC EXPORT (`output:'export'`, all data client-fetched) served by nginx that reverse-proxies `/api/` → `api.aiops.svc:8088` (single origin, no CORS, no 2nd exposed port). Causal graph = React Flow + dagre (edge width = `render_weight`, animated/hot when `state=active`, grey when `source=memory`, root node highlighted), verdict card from `/api/narrative`, blast-radius list, S1 scenario button, Grafana link for PSI. `deploy/dashboard.yaml` = Deployment + NodePort 30080; `skctl` `has dashboard` now applies it (was a TODO); `has language` echo corrected (narrator lives in the api, not a separate ollama deploy). `next` pinned `^14.2.35` (patched; 14.2.5 carried a CVE).
Why: The "beyond monitoring" story is the causal graph + narrated verdict; the API was flattening exactly the fields that show edges shifting under load (`render_weight`) and steady-backbone-vs-live-incident (`state`/`source`). Presentation decision (operator): custom SPA on `/api/*` for the causal/narrator story + Grafana (Prometheus datasource) for PSI panels; Loki dropped (it stores logs, not the engine verdict). Frontend stack: Next.js static export, exposed over the EXISTING Tailscale tailnet (box `soumyadip-b460md3h` = 100.93.123.48 is already a peer of the laptop) via NodePort — private, no public ingress, no router config.
Impact / Apply (box): rebuild api (`docker build -t skn/api:v0.1 api/` + `k3s ctr images import` + `kubectl rollout restart deploy/api -n aiops`); build dashboard (`docker build -t skn/dashboard:v0.1 dashboard/` + import); `./deploy/skctl up --mode solo` (applies dashboard.yaml); point the narrator at host Ollama: `kubectl set env deploy/api -n aiops OLLAMA_HOST=http://<NODE_IP>:11434` (Ollama must listen on 0.0.0.0; `gemma4:e4b` pulled). Verify: `/api/graph` edges carry `state`/`render_weight` during S1; `/api/narrative` `source=llm` with Ollama up, `=fallback` without; dashboard at `http://100.93.123.48:30080` from the laptop, fire S1 → graph lights up + narrated cooling-monitor root. Local verification (laptop, no cluster): `py_compile` clean; `graph()`+`narrative()` exercised against mock engine output (S1 prose + S0 steady, fallback path); `npm run build` emits `out/` static export. NOT yet cluster-verified — README/REMAINING status unchanged until the box run passes.
Links: api/main.py; deploy/{api.yaml,dashboard.yaml,skctl}; dashboard/{package.json,next.config.mjs,app/*,Dockerfile,nginx.conf}; REMAINING.md P5/P6; LOG-063 (deviation gate); LOG-057 (api gateway this extends).

## LOG-065 · 2026-06-19 · DECISION — Grafana pinned to v11 (defer v12/v13); reverses LOG-024 disable
What: Re-enable Grafana for the P6 PSI panels (`deploy/values/prometheus.yaml`), pinned to `image.tag: 11.3.0`, served behind the dashboard nginx at `/grafana/` (subpath) with anonymous Viewer. Decision: stay on the **Grafana 11 line for now**, upgrade later.
Why: Web research (tools, not memory) traced the LOG-024 "Grafana 12 apiserver crashloops (exit 1)" to the **App Platform rework** — Grafana 12's embedded **apiserver + unified storage** for folders/dashboards, gated behind feature toggles (`grafanaAPIServer`, `kubernetesDashboards`, `kubernetesClientDashboardsFolders`, `provisioning`, `dashboardNewLayouts`): startup crashes + dashboard-edit memory leaks (grafana#105808). Severe enough that **Grafana 13.0.0 was pulled from distribution; fixed in 13.0.1**. v13 is GA (GrafanaCON Apr 2026) but keeps that architecture (Scenes mandatory, auto SQL→unified-storage migration on startup, `/apis`). For our use — embedding a few PSI `d-solo` panels — none of v12/v13's features help and the apiserver/migration is pure added risk. v11 predates the whole class and supports everything we need (Prometheus datasource, subpath, panel embed).
Future-upgrade recipe (when we revisit "upgrade forever"): use **Grafana 13.0.1+** (never 13.0.0); explicitly disable the `kubernetes*`/`provisioning` Git-Sync toggles unless we actually want GitOps dashboards; expect a one-time SQL→unified-storage migration at first boot; back up the Grafana DB first. To confirm the original exit-1 on the box: `kubectl logs -n observability <grafana-pod> -c grafana --previous`.
Status: code pinned; NOT yet box-verified (Grafana coming up clean on v11 + `/grafana/` rendering is the open check, with LOG-064). Sources: grafana#105808; whats-new/upgrade-v13.0; unified-storage notes.
Links: deploy/values/prometheus.yaml; dashboard/nginx.conf (/grafana/ proxy); LOG-024 (disable, reversed here); LOG-064 (dashboard/narrator this supports).

## LOG-066 · 2026-06-20 · STEP — P5 + P6 DONE: gemma4 narrator + launcher dashboard + 3D causal graph + Grafana PSI embed (cluster-verified, IST)
What: L4 language + dashboard complete, verified live on the box and reachable from the laptop over Tailscale at `http://100.93.123.48:30080`.
 (P5) `api/main.py` `GET /api/narrative` — the one LLM: renders the normalized `/graph` into one operator sentence via local **gemma4** (Ollama at host `OLLAMA_HOST`), grounded to the resource word (disk I/O) with source/victim roles, `think:false` for speed, a verdict-signature **cache** so the 5s poll doesn't re-run the model, and an always-on **deterministic template fallback** (the demo never depends on the model). `/api/graph` forwards the engine's per-edge `confidence/state/render_weight/source`.
 (P6) NEW `dashboard/` = Next.js **static export** served by nginx (reverse-proxies `/api/`). A **component launcher** (Causal API :30088, Grafana :30030, Prometheus :30090 — each its own NodePort, individually testable) over a live causal view: stat tiles, gemma4 verdict (+ case register), a **3D force-directed causal graph** (`react-force-graph-3d`/three.js — red source / amber victims / teal idle; edges coloured by contention grey→orange; particles on live edges; fit-on-settle camera), blast radius, scenario console (Fire S1 with armed/error feedback), and an **embedded Grafana PSI panel** (`d-solo` iframe; dashboard provisioned as code in `deploy/grafana-psi-dashboard.yaml`, `sum by (workload)` legend). Grafana re-enabled on v11 (LOG-065), exposed direct **and** embedded (`allow_embedding`); datasource sidecar label scoped to dodge loki-stack's default-Loki clash.
 Clocks set to **IST / Asia/Kolkata** (Grafana default + dashboard tz + page clock + embed URL). Ship hardening: engine `WINDOW/EVENTS_URL` → FQDN-with-trailing-dot (immune to the Tailscale MagicDNS search-list leak), `DEV_K=4` (idle stays green under real background HDD noise), `TZ` on aiops pods.
Why: P5/P6 were the last build phases. The long tail was operational, not algorithmic: **Tailscale MagicDNS** leaked `*.ts.net` into pod `resolv.conf` → intermittent `EAI_AGAIN` on the engine's aggregator lookup (fixed by `sudo tailscale up --accept-dns=false` + FQDN URLs); **loki-stack's default Loki datasource** clashed with Prometheus' default → Grafana crashloop (fixed by scoping the datasource sidecar label); the factory had been **paused** (`skctl resume`); the embed needed a **saved/provisioned** dashboard (anonymous Viewer can't author in the UI).
Impact: S1 verified end-to-end from the laptop — Fire S1 → `cooling-monitor` roots (red) via `write+pvc+temporal`, `timescaledb`/`dcim-bridge` victims (amber), gemma4 prose + blast radius, then decays to steady **green** (`DEV_K=4`); the PSI panel shows the storm beside the verdict. Remaining: P7 (S2–S5 + rehearsal ledger), P8 (hardening), the Loki **logs panel** (pending the `alloy → promtail` fix), and the §1 residual (deep fix deferred; `DEV_K=4` mitigates the idle flicker). Next: branch **mark-zero** (baseline `1d4315a`) + **mark-one** (this P5/P6 work) on `ABB_Accelerator_Proto`.
Links: api/main.py; dashboard/{app/*,Dockerfile,nginx.conf,package.json}; deploy/{api,engine,dashboard,grafana-psi-dashboard}.yaml; deploy/values/prometheus.yaml; LOG-064 (API+launcher), LOG-065 (Grafana v11); REMAINING.md.

## LOG-067 · 2026-06-20 · STEP — code/plan audit; ROAD_TO_COMPLETION.md; doc reorg (archive/)
What: Full file-by-file audit of the code against MASTER_PLAN (what/why) and BUILD_GUIDE (phase path), then a forward plan. Findings (the "skeleton vs muscle" picture): the running engine is **single-signal (psi_io) and couples only the shared-disk quartet** — so S1 is end-to-end and correct, but the breadth the deck promises is not yet built. Specifically unbuilt/partial: multi-signal (psi_cpu/psi_mem never analyzed though scraped); A2 Log Detective (absent), A3 topology (static `STORAGE` heuristic, no eBPF), A5 Verdict/Orchestrator + bounded K8s tools (absent); `forecast_to_limit` is dead code (S5 OOM-forecast not wired); the gate demotes PSI co-pressure to corroboration-only (gate.couples = pvc/ebpf), which **architecturally blocks S3** (CPU contention, no network edge); recommendation engine (right-sizing/KAI verbs/fairness index) absent; dashboard ~3 of 6 §1.6 panels; Chaos Mesh is a skctl TODO (S4 can't run); rehearsal ledger empty; no DB probe so the PVC-I/O↔restart link (PS-Q2) doesn't exist. Of the four judge questions, **only Q3-for-disk is demonstrable today**. Net-positive beyond the plan: the stateful memory/case-library/deviation-baseline engine (state.py) and io_write source attribution.
Created **ROAD_TO_COMPLETION.md** — Stage 0 (source-rooted case promotion = REMAINING §1 "item 1") → 1 (multi-signal engine) → 2 (eBPF witnesses + the S3 PSI-coupling decision) → 3 (A2/A5/forecaster) → 4 (scenarios+Chaos Mesh+ledger, P7) → 5 (recommendation engine, parallel) → 6 (full dashboard) → 7 (hardening/air-gap, P8), plus a continuous docs workstream (root README + per-component "component dive" READMEs + refresh EXPLANATIONS/BUILD_GUIDE/runbooks). Each stage carries goal/missing/work-items/done-when/depends-on/touches; four open design decisions flagged for the operator.
Doc reorg (operator decision): new **archive/** holds retired docs — **P0_DESKTOP_SETUP.md** (P0 done) and **REMAINING.md** (folded into and superseded by ROAD). agents/README.md kept but flagged stale (to be rewritten in the docs workstream); root README.md noted absent. BUILD_LOG/MASTER_PLAN/QUICKSTART/EXPLANATIONS/DESIGN/BUILD_GUIDE stay active.
Why: operator asked to correlate the MASTER_PLAN goal vs what's actually built, plan the remaining work in stages, then start filling gaps. "The skeleton is there, it needs all the muscles now."
Impact: ROAD_TO_COMPLETION.md is now the single forward-plan doc (REMAINING retired). Next: Stage 0 (item 1) — source-rooted case promotion in state.py + a test_state.py case, run_pass fixtures untouched. Stages 1/2/3 have open decisions to settle before they start.
Links: ROAD_TO_COMPLETION.md; archive/{P0_DESKTOP_SETUP,REMAINING}.md; MASTER_PLAN §0/§1.4/§2.5; correlation/engine/{gate,pipeline,state,detectors}.py; correlation/service.py; aggregator/queries.yaml; deploy/skctl; LOG-063 (deviation gate), LOG-066 (P5/P6).

## LOG-068 · 2026-06-20 · FIX (ROAD Stage 0) — case promotion requires a source-rooted verdict
What: `state.py._promote_case` now promotes a case ONLY when the ranked root owns an outgoing edge carrying **source (`write`) evidence** — a real aggressor. Added module constant `SOURCE_EVIDENCE = ("write",)` (the extension point where Stage 1/2 CPU/mem source tags will be added). Updated the shared `_graph()` test fixture to a source-rooted edge `[write, pvc, temporal]` (this matches the real post-LOG-060 S1 verdict, where the winning edge is the writer→staller source edge, not a `stat` psi edge). New test `test_case_not_promoted_from_victim_cascade` (a psi-only `dcim-bridge→timescaledb` cascade promotes nothing; the same pair with a `write` edge does). `run_pass` and its 13 fixtures untouched. **31/31 local (Tier-0).**
Why: REMAINING §1 (now archived) residual — between S1 storm pulses the live source edge decays to its structural floor and a stale psi-only victim↔victim cascade (`dcim→timescaledb`, evidence `stat`) could transiently outrank and get promoted as a **wrong-direction case**. The deviation gate keeps S0 silent but cannot catch this (both pods are genuine victims). Gating promotion on a source-rooted verdict closes it; it only changes *which* incidents become cases, nothing else.
Impact: apply on the box = rebuild `skn/correlation-engine:v0.1` + `k3s ctr images import` + `kubectl rollout restart deploy/correlation-engine -n aiops`. Verify: a multi-pulse S1 soak grows `cases` only with `cooling-monitor`-rooted rows; S0 stays silent. The live memory DB may still hold legacy wrong-direction case rows from before this fix — clear them once (as in LOG-061/062) or start from a fresh DB. **ROAD Stage 0 complete; next is Stage 1 (multi-signal engine), which has an open output-shape decision.**
Links: ROAD_TO_COMPLETION.md (Stage 0); archive/REMAINING.md §1; correlation/engine/state.py; correlation/tests/test_state.py; LOG-060 (source attribution), LOG-063 (deviation gate), LOG-067 (ROAD).

## LOG-069 · 2026-06-20 · STEP (ROAD Stage 1) — multi-signal engine (psi_io + psi_cpu + psi_mem), merged graph
What: The engine now fans out over `ENGINE_SIGNALS` (default `psi_io,psi_cpu,psi_mem`) instead of only psi_io. `service.build_inputs` collects every psi signal plus each resource's source/aggressor signal (`io_write` for psi_io, `cpu` for psi_cpu; psi_mem has none — a leak is self-caused, its forecast is Stage 3) and resamples all onto the one shared wall-clock grid. The loop runs ONE `run_pass` per signal with a **per-signal witness** and a **per-signal GraphMemory**, then merges. New pure module `engine/merge.py` unions the per-signal rendered graphs, tags every edge/finding with its `signal`, and **re-ranks root cause + blast radius over the union** (a multi-resource aggressor wins). Per-signal SQLite memory: the PRIMARY (psi_io) keeps the original `l3-memory.db` (history preserved); others get `l3-memory.<signal>.db`. `api/main.py`: `/api/graph` carries per-edge `signal`; the narrator grounds its resource word in the **root edge's** signal; `/api/pods` spans all signals (reports each workload's hottest class). Operator decision (this session): one merged graph with a per-edge `signal` tag (not per-signal graphs).
Correctness ruling: the witness is built **per signal**. A shared disk (pvc) couples I/O stalls, NOT CPU or memory stalls — so disk coupling admits ONLY psi_io edges. psi_cpu/psi_mem therefore produce **findings but no edges** until Stage 2 gives them a coupling witness (same-node PSI / eBPF). This is deliberate: it prevents false cross-resource edges (a shared disk "explaining" a CPU stall). A bug surfaced and fixed in merge: when findings exist on one signal but the only edges are another signal's steady backbone, `rank_root_causes` falls back to all nodes and blames the backbone → merge now seeds ranking ONLY with findings that sit on the causal graph.
Why: ROAD Stage 1 — psi_cpu/psi_mem were scraped but never analyzed; this is the foundation for S3 (CPU), S5 (mem), and PS-Q1. `run_pass` stays a pure function (the fan-out is caller-side, exactly as its docstring always promised) — the 13 fixtures are untouched.
Verify: **36/36 local** (13 run_pass fixtures + state suite + 5 new `test_merge.py`), `py_compile` clean on service.py/api.py. Integration smoke (synthetic 16-pass baseline warmup + storm, psi_io+psi_cpu): root=`cooling-monitor (1.00)` via `cooling→timescaledb [write,pvc,temporal]` + `cooling→dcim [write,pvc]` (all tagged psi_io); `analytics-batch` surfaces as a **psi_cpu finding with no edge** — exactly the intended separation; merge tags every edge by signal and ranks over the union.
Impact / apply on box: rebuild `skn/correlation-engine:v0.1` AND `skn/api:v0.1` + `k3s ctr images import` + `kubectl rollout restart deploy/{correlation-engine,api} -n aiops`. **queries.yaml needs NO change** (psi_cpu/psi_mem/cpu/io_write already scraped). New env `ENGINE_SIGNALS` (engine + api). New per-signal memory dbs are created on engine-memory-pvc. Expected on box: S1 unchanged (psi_io edge, cooling-monitor root); S3/S5 now produce psi_cpu/psi_mem **findings**; cross-resource EDGES arrive in Stage 2 (the open same-node-PSI-coupling decision). KNOWN Stage-2 prerequisite: the `cpu` query is per-container (not `sum by (namespace,pod)`), so the psi_cpu source vector is noisy — fine for Stage 1 (cpu source is unused without coupling), must be summed-by-pod before Stage 2 uses it.
Links: ROAD_TO_COMPLETION.md (Stage 1); correlation/{service.py, engine/merge.py, tests/test_merge.py}; api/main.py; aggregator/queries.yaml; LOG-060 (source attribution), LOG-063 (deviation gate), LOG-068 (Stage 0).

## LOG-070 · 2026-06-20 · STEP — Stage 0 + Stage 1 BOX-VERIFIED; idle signal-label fix
What: Operator rebuilt/imported the correlation-engine image and verified on the live cluster (dashboard at 100.93.123.48:30080). On S1: root=**cooling-monitor (score 1.00)**, edge **cooling-monitor→timescaledb tagged `signal=psi_io`** with evidence **[write, pvc, temporal]**, gemma4 verdict "Disk I/O contention originating from cooling-monitor and affecting timescaledb… evidence … write, pvc, and temporal", **case_register=recurrence** — confirming Stage 0 (source-rooted promotion) and Stage 1 (multi-signal merge + per-edge `signal` tag) live. At steady state the engine correctly showed `root []`, `ACTIVE 0`, and only the **pvc steady-backbone** edges (`source=memory`, the seeded topology prior) — "fires when true, silent when not" intact. Early `trigger + sleep 50` CLI reads caught steady moments (live `/graph` window + psi_io `[30s]` rate lag + post-memory-wipe baseline warmup); the incident surfaced a poll later, as expected (LOG-053).
Cosmetic fix (this session): `merge_graphs` idle topbar label was the alphabetically-first signal (showed `psi_cpu` at steady); now `merge_graphs(per_signal, primary=PRIMARY)` prefers the active signal, else the primary. 5/5 merge tests green; compiles.
Why: operator box-verification of Stage 0/1; the idle label was misleading.
Impact: detection unaffected — the label fix rides the NEXT correlation-engine rebuild (no need to rebuild for it alone). **Stage 0 + Stage 1 confirmed working on the cluster. Paused before Stage 2 per operator** ("check if it even is working"). Optional remaining closeouts: 3d (cases table shows only cooling-monitor-rooted rows) and 3e (S3 → a `psi_cpu` finding with no edge).
Links: LOG-068 (Stage 0), LOG-069 (Stage 1); correlation/engine/merge.py; correlation/service.py.

## LOG-071 · 2026-06-20 · FIX — recency gate (fast verdict reset) + DEV_K 4→3.5
What: The causal verdict now resets ~2 min after a storm ends instead of when it scrolls out of the 15-min ring. `run_pass` gains an optional `recent: int|None=None`: when set, the **deviation gate** (p90 vs the learned baseline) is judged over the last `recent` samples only — DETECTION still scans the full ring for the onset (clean pre-event baseline preserved), but an onset is a *current incident* only if the pod is still deviating in the recent tail. `service.py` passes `recent=RESET_WINDOW` (new env, default 24 ≈ 2 min). `deploy/engine.yaml`: `DEV_K 4→3.5` (slightly faster confirm; raise back if idle flickers), added `RESET_WINDOW=24`, and switched `ENGINE_SIGNAL`→`ENGINE_SIGNALS=psi_io,psi_cpu,psi_mem` (Stage 1). New test `test_recent_window_clears_a_stale_storm` — appended LAST because `noise()` draws from a shared module RNG, so a mid-file insertion shifts later tests' sequence (this exposed, then avoided, an order-coupling that briefly failed `test_source_attribution`). **37/37 local.** `run_pass` default path (`recent=None`) is byte-identical → the 13 fixtures + the 2 baseline tests are untouched.
Why: operator — after S1 the graph stayed "hot" up to ~15 min because both detection and the p90 deviation gate ran over the full 15-min ring (LOG-054 event-centred). Recency-gating the *incident decision* (not detection) clears a cooled storm fast and also confirms a short single storm faster (recent p90 captures a 60s storm that full-ring p90 dilutes below the bar). Fixture-safe by being opt-in.
Impact / apply on box: rebuild `skn/correlation-engine:v0.1` + import + `kubectl apply -f deploy/engine.yaml` + `kubectl rollout restart deploy/correlation-engine -n aiops` (this rebuild also carries the LOG-070 idle-label fix). Live tunables (no rebuild): `RESET_WINDOW` (smaller = faster reset; keep ≳ storm length ~12 samples so a live storm isn't cleared early), `DEV_K` (`kubectl set env deploy/correlation-engine -n aiops DEV_K=4` if S0 flickers). Confirm ≈45-50s after S1 (psi_io is a 30s rate); reset ≈2-2.5 min after the storm ends.
Links: LOG-054 (event-centred), LOG-063 (deviation gate), LOG-066 (DEV_K=4), LOG-069/070 (Stage 1 + idle label); correlation/engine/pipeline.py; correlation/service.py; correlation/tests/test_engine.py; deploy/engine.yaml.

## LOG-072 · 2026-06-20 · NOTE — recency reset confirmed near-realtime on box; two standing directives recorded
What: Operator confirmed on the cluster that the recency gate (LOG-071) makes the verdict reset near-realtime — S1 lights up fast and clears shortly after the storm, no 15-min lag. Two forward directives captured so they bind the rest of the build: (1) **the same fast / clear / self-resetting outcome must hold for S2–S5**, not just S1 → added as ROAD **constraint 7** and folded into the **Stage 4 done-when** (each scenario: detect ~50s → single clear root → self-reset ~2–3 min). (2) **gemma4 LLM verdict prose needs fine-tuning but is parked** (non-blocking, "anytime") → added to ROAD **Parked**; the demo never depends on the model (template fallback).
Why: record standing acceptance criteria + the deferred item before moving on.
Impact: Stages 0 + 1 + recency reset are complete and box-verified; the "fast/clear/self-reset" bar is now an explicit gate for every upcoming scenario. Next: Stage 2 (eBPF witnesses + same-node PSI coupling for psi_cpu/psi_mem edges).
Links: LOG-071 (recency gate); ROAD_TO_COMPLETION.md (constraint 7, Stage 4, Parked).

## LOG-073 · 2026-06-20 · STEP + DECISION (D-015, ROAD Stage 2 slice 1) — same-node PSI coupling enables S3 (no eBPF)
What: First slice of Stage 2 (no eBPF dependency): re-admitted same-node PSI as a coupling witness for the **source-attributed edge path only**, so S3 (CPU contention, no network edge) draws a guarded causal edge from PSI alone. Changes — `gate.py`: `Witness` gains `same_node` + kind `node`; new `SOURCE_COUPLING_KINDS=(ebpf,pvc,node)` and `couples_source()`; `COUPLING_KINDS` (the bare `accept_edge` path) stays `(ebpf,pvc)` so a same-node pair can NEVER form a victim↔victim psi cascade. `pipeline.py`: `_writer_edge` admits `node`; the source loop gates on `couples_source`. `service._witness_for`: psi_io keeps disk(pvc) coupling; psi_cpu/psi_mem get same-node coupling (single node = one contention domain; multi-node will scope by node label). `queries.yaml`: `cpu` → `sum by (namespace,pod)` (clean per-pod source vector — the LOG-069 Stage-2 prerequisite). Tests +2 (same-node CPU source edge carries `node`/no pvc/ebpf; bare same-node psi forms no edge); **39/39**.
Why: on a single node, an explicit same-node `shared_relation` would couple EVERY pair (over-permissive), and eBPF can't witness CPU contention (no network edge) — PSI is the only physical witness for S3 (MASTER_PLAN §1.4.4-2b). Confining same-node to the source path keeps the witness honest while the source guard (usage leads stall + out-hogs + deviated) prevents the false victim↔victim edges that demoting psi in LOG-061 fixed. D-015.
Verify: 39/39 local; end-to-end service smoke with S1+S3 together → merged graph shows `cooling-monitor→timescaledb [write,pvc,temporal] (psi_io)` AND `analytics-batch→vision-qc [write,node,temporal] (psi_cpu)`, ranks both roots (cooling 0.57 / analytics 0.29), zero false same-node edges.
Impact / apply on box: rebuild `skn/correlation-engine:v0.1` + import + `kubectl rollout restart deploy/correlation-engine -n aiops`; reload the aggregator-queries ConfigMap (cpu query) + `kubectl rollout restart deploy/aggregator -n aiops` (no aggregator image rebuild). Then S3: `bash scenarios/S3/trigger.sh` → expect a `psi_cpu` edge analytics-batch→(vision-qc/CCR) with `node` evidence and no network path, self-resetting per the recency gate (constraint 7). STILL DEFERRED (next Stage 2 slices): the eBPF collectors (Caretta network witnesses, OBI `latency_p95` for the CCR hop, Inspektor Gadget block-io) — S3 needs none of them.
Links: D-015; MASTER_PLAN §1.4.4-2b, §2.5 (S3); LOG-061 (psi demotion this carefully re-admits), LOG-069 (cpu-query prereq), LOG-072; correlation/engine/{gate,pipeline}.py; correlation/service.py; aggregator/queries.yaml; correlation/tests/test_engine.py.

## LOG-074 · 2026-06-21 · FIX — same-node source attribution: false-edge storm killed (real-victim + live-only)
What: First box S3 run exposed a **false-edge storm** — ~7 stable `psi_cpu` `write+node` edges between unrelated pods (safety→cooling, vision→mqtt, telemetry→mqtt, critical→dcim, …), root flapping — while `psi_watch` proved there was **no real co-resident CPU stall** (only the burst pod self-throttled at psi_cpu 2.79; every co-resident ~0). Two engine causes, both fixed: (1) the source-edge loop's `disturbed` escape let a source point at ANY co-located pod once anything was active — harmless under pvc (couples 4 pods) but a storm under `same_node` (couples everything); a source edge now requires the **victim ∈ active** (a real deviating finding). (2) cpu/mem edges were taking the **structural floor/prior** (a persistent backbone) — wrong for a transient, topology-less domain; `service._config` now sets `prior=floor_frac=0` for non-psi_io signals, so cpu/mem edges are **purely live** (form during real contention, vanish after). Only psi_io keeps the disk backbone. New regression test `test_source_edge_requires_a_real_victim_not_a_bystander` (a correlating non-deviating bystander gets NO edge); **40/40**. `run_pass` default path unaffected (the existing source fixtures all have active victims).
Why: `same_node` removes the topological constraint that disciplined the io source path (STORAGE scoping + a single massive fio writer). The clean unit fixtures never exercised "something active + everything coupled + noisy cpu usage" — the box did. A source edge must point at a REAL victim, and a domain with no stable topology must not accrete a backbone.
Verify: 40/40; the S1+S3 service smoke still draws the legitimate `analytics-batch→vision-qc [write,node,temporal]` (real victim) + the S1 chain; the regression test proves a bystander is excluded.
Impact / apply on box: rebuild `skn/correlation-engine:v0.1` + import + rollout restart; **clear the polluted per-signal memory** — `kubectl exec -n aiops deploy/correlation-engine -- sh -c 'rm -f /var/lib/skn/memory/l3-memory.psi_cpu.db /var/lib/skn/memory/l3-memory.psi_mem.db'` then rollout restart (keep `l3-memory.db` — psi_io history is good). Re-warm ~10 min. **PHYSICS NOTE:** on the 16-thread box S3 has no real victim (the 2-core burst only self-throttles), so the HONEST result is now **no cpu edges** (clean, like S0) — the engine is correct; *demonstrating* S3 needs Stage 4 to make co-residents actually stall (more burst pods / tighter cpu limits / cpuset / fewer allocatable CPUs) — the CPU analogue of D-014's HDD move for S1.
Links: LOG-073 (Stage 2 slice 1), D-015; correlation/engine/pipeline.py; correlation/service.py; correlation/tests/test_engine.py; appendix/psi_watch.sh.

## LOG-075 · 2026-06-21 · FIX + NOTE — narrator says steady when no root; held cpu garbage must be cleared; s3-run explained
What: Box dashboard (psi_io view) showed ~10 merged "causal edges" at idle spanning NON-storage pods (safety↔cooling, vision↔mqtt, telemetry↔mqtt, critical↔dcim …) and a self-contradictory gemma4 verdict ("Disk I/O contention is observed from timescaledb to dcim-bridge … The system is steady"); on S1 the blast radius was polluted (critical-control-relay ETA 65s). Root cause: those are **leftover psi_cpu false edges still held in `l3-memory.psi_cpu.db`** with a structural floor from BEFORE LOG-074 — a rebuild doesn't drop held rows, only the `rm` does. The merge unions all signals, so they render in the psi_io view AND pollute the unified ranking/blast/narrative. Actions: (1) **clear** `l3-memory.psi_cpu.db` + `l3-memory.psi_mem.db` (the LOG-074 step) — with LOG-074's no-floor + real-victim fixes they won't reform. (2) **Narrator fix** (`api/main.py`): `/api/narrative` now returns the deterministic steady line when there is **no root** and skips the LLM — the steady-state backbone is normal coupling and must never be narrated as contention. py_compile clean.
The deeper incident-verdict prose (it called the victim `timescaledb` a "source") stays the PARKED LLM-tuning item; it also improves once the garbage is gone (cleaner graph fed to the model).
NOTE (operator Q): the **`s3-run-*` pod** is a one-off Job that `scenarios/S3/trigger.sh` creates from the **suspended `analytics-batch` CronJob** (LOG-034 made cronjobs on-demand: `kubectl create job --from=cronjob/analytics-batch s3-run-<ts>`). Side effects: the CPU source is attributed to the ephemeral `s3-run` workload, not `analytics-batch`, and the burst pod is the *self*-staller (CFS throttle at its own limit), not a cross-pod victim. S3 rework (Stage 4): name the job so it resolves to `analytics-batch` (e.g. `analytics-batch-s3`) AND engineer real cross-pod CPU contention (saturate the node) so co-residents actually stall.
Why: held garbage persists until cleared and pollutes the merged psi_io verdict; the narrator must not call steady coupling "contention".
Impact / apply: rebuild `skn/api:v0.1` (narrator) + `skn/correlation-engine:v0.1` (LOG-074) + import; `kubectl exec -n aiops deploy/correlation-engine -- sh -c 'rm -f /var/lib/skn/memory/l3-memory.psi_cpu.db /var/lib/skn/memory/l3-memory.psi_mem.db'`; `kubectl rollout restart deploy/correlation-engine deploy/api -n aiops`. After: idle → "Steady state…" with a clean ~3-edge psi_io backbone; S1 → cooling-monitor root, blast = tsdb/dcim only (no CCR-from-garbage).
Links: LOG-073/074 (same-node + false-edge fix), LOG-034 (cronjob on-demand), ROAD Parked (LLM tuning); api/main.py; scenarios/S3/trigger.sh.

## LOG-076 · 2026-06-21 · NOTE — cleanup confirmed on box; S3 physics finding; CPU usage-vs-stall model
What: After the rebuild + clearing the per-signal memory dbs, an S3 run reads `cpu_edges []` for the whole burst — the false-edge garbage is gone (LOG-074/075 confirmed on the box; the engine is silent because nothing real is contending). That empty result + `psi_watch` (only the burst pod self-stalls at psi_cpu 2.79; co-residents ~0) crystallized two things:
(1) **S3 mechanism is physically self-contradictory as written.** A `500m`-CPU-capped aggressor is CFS-throttled to 0.5 cores → it only **self-throttles**; it cannot starve co-residents. Cross-pod CPU stall needs the node (or a cpuset) genuinely saturated by an aggressor that actually **consumes** many cores (high/no limit). So MASTER_PLAN §2.3's "2-core demand under 500m → co-residents stall" can't happen — the cap prevents the starvation. Self-throttle (per-pod, any tool sees it) ≠ noisy-neighbor (the differentiator).
(2) **CPU usage vs stall — the determination model.** CPU **usage** (`cpu`) is constant + coupled in a real edge system (DMA offloads byte transfer, but interrupt/stack/deserialize/app/control-loop processing is real CPU) → it has a standing baseline and a *pipeline* coupling. CPU **stall** (`psi_cpu`) stays ~0 until saturation. So: **usage finds the SOURCE, stall finds the VICTIM, need both**; the contention witness is `same_node` (the run-queue is shared by all co-residents, not just pipeline neighbors). For an idle-baseline pod the deviation gate collapses to ≈`DEV_K*mad_floor` (~0.035) = "any sustained real stall."
Conclusions folded into ROAD: Stage 4 S3 = make the box **edge-like** (cpuset/reduced-allocatable contention cell, PROTECTING observability+engine cores per Risk #4, OR a transient full-node saturation burner) + an aggressor that truly consumes cores; Parked = a **CPU usage-coupling backbone** (observed pipeline map = the CPU "Case 0"; replaces the earlier ghost-map idea; additive, contention stays stall-based). Engine needs NO change — it draws the correct `analytics→victim [write,node,temporal]` edge the instant a co-resident really stalls (unit test + S1+S3 smoke prove it).
Why: operator's edge-realism question ("CPU is busy from sensors/PLC; what determines contention?") + the clean S3 box run.
Impact: S3 is an engine-ready / physics-blocked scenario. Decision pending (operator): which physical mechanism to stage real cross-pod CPU contention safely (cpuset cell [faithful, safe, infra] vs transient node saturation [no infra, risks starving the monitoring path] vs reduce-allocatable [risks idle stall everywhere]). Unrelated standing red: `alloy` CrashLoopBackOff (1107 restarts) = the Loki/logs path (deferred Stage 2/3).
Links: LOG-074/075; MASTER_PLAN §2.3 (S3 mechanism — needs correction), §4.3 (Koordinator PSI/CPI); ROAD Stage 4 + Parked; appendix/psi_watch.sh.

## LOG-077 · 2026-06-21 · STEP (ROAD Stage 2 eBPF) — Caretta install coords corrected; cleanup confirmed on box
What: Continuing the eBPF slice. Researched the Caretta chart (README, current): **repo `groundcover` @ `https://helm.groundcover.com/`, chart `groundcover/caretta`** — skctl had `caretta/caretta` @ `groundcover-com.github.io/caretta` (wrong on both; the LOG-039 "repo caretta not found" blocker). Metric is **`caretta_links_observed`** (Gauge; labels `client_name/client_namespace/server_name/server_namespace/server_port/role`), NOT `_total`. Beyla's `grafana/beyla` coords are correct (it's Running 1/1). Fixed `deploy/skctl` (repo+chart) and `deploy/values/caretta.yaml` (metric name + a grounded scrape caveat: the README routes Caretta metrics through its bundled VictoriaMetrics, so with VM disabled the agent must expose its own `/metrics` on the annotated port — verify on install, else set the real port or re-enable VM and query it).
Also confirmed on the box this session: the LOG-074/075 cleanup worked — idle narrates "Steady state: no causal contention" over a clean 3-edge psi_io backbone; S1 gives a clean correct verdict (root cooling-monitor 1.00; impacts timescaledb ETA 5s, dcim-bridge ETA 15s; evidence stat/pvc/write/temporal); the psi_cpu garbage is gone and the blast no longer pulls in CCR. The narrator reads well even before the parked LLM tuning.
Why: Caretta never installed (wrong helm coords); it's the network-flow witness + the auto-discovered topology map.
Impact: operator runs `./deploy/skctl up --mode solo` (corrected coords) or the helm install directly; THEN confirm the two real unknowns on the box: (a) the eBPF CO-RE program loads on **kernel 7.0** (Otterize / beyla-network are fallbacks); (b) `caretta_links_observed` actually reaches our Prometheus (the VM/port caveat). ENGINE CONSUMPTION is the NEXT step, built against the *confirmed* metric output (not the schema guess): Caretta links → the auto-discovered **topology map** + a witness for a future **network/latency** signal — NOT psi_io/cpu/mem (network ≠ disk/cpu coupling, so it must be resource-class-matched like pvc→io and node→cpu). Beyla `latency_p95` → the CCR SLO signal (physics of the S1→CCR hop still uncertain — CCR isn't I/O-bound).
Links: LOG-039 (broken coords this fixes), LOG-033 (eBPF wiring), LOG-074/075 (cleanup, confirmed here); deploy/skctl; deploy/values/caretta.yaml; Caretta README (helm.groundcover.com).

## LOG-078 · 2026-06-21 · NOTE — eBPF install results: Caretta pending; Beyla captures monitoring HTTP (CCR hop not instrumentable)
What: With the corrected coords, **Caretta installs** (helm deployed rev 2) — agent pod still `ContainerCreating` at check time, so `caretta_links_observed` empty so far; kernel-7.0 CO-RE verdict + the topology-map source PENDING the pod going Running (re-check). **Beyla emits** `http_server_request_duration_seconds_bucket` with rich k8s labels, BUT two findings: (1) it instruments HTTP **monitoring traffic** — the sample is `mqtt-broker` `http_route=/metrics status=499` (= Prometheus scraping the pod's /metrics) and `/healthz` probes — NOT the factory's real inter-service traffic, which is **MQTT (1883) + SQL (5432)**; beyla's HTTP RED is **blind to MQTT**. So `latency_p95` scoped to `critical-control-relay` is noise: **CCR actuates over MQTT, so the S1 4th hop (CCR actuation p95) is NOT eBPF-instrumentable** — corrects MASTER_PLAN §1.2/§2.5's "OBI latency → CCR p95" (CCR's own histogram is the only source = the D-004 ground-truth channel, deliberately kept out of the engine). (2) beyla labels are `k8s_pod_name`/`k8s_namespace_name`, NOT the `pod`/`namespace` the aggregator extracts → `latency_p95` wouldn't ring without a `label_replace`/relabel.
Conclusion: the eBPF slice's clean deliverable is the **Caretta L4 topology map** (all TCP flows regardless of protocol → the auto-discovered "zero-config, eBPF found every edge" service graph) — pending Caretta Running on kernel 7.0. Beyla RED is secondary/messier (real app-HTTP only `alert-dispatcher→notify-gateway` + `edge-ui→firmware-cache`; SQL if it decodes Postgres; needs monitoring-route exclusion + a pod-label map). **CCR-latency hop deprioritized.**
Impact: wait for the caretta pod Running (CrashLoop = CO-RE fail → fallback beyla-network/Otterize), re-run the `caretta_links_observed` query; then build the topology-map consumption against the real output. No code changed this turn (operator-gated on the pod).
Links: LOG-077; MASTER_PLAN §1.2 (OBI), §2.5 (S1 4th hop — corrected), §2.7 (plane-1 = MQTT/SQL); D-004; aggregator/queries.yaml (latency_p95).

## LOG-079 · 2026-06-21 · FIX — Caretta OOMKilled on the default 500Mi; raised the limit
What: Caretta's agent `OOMKilled` (4 restarts in ~2min), NOT a CO-RE/BTF crash — so **kernel 7.0 eBPF loads fine**; the agent just exceeds its memory limit. Confirmed the chart key (groundcover-com/caretta `chart/values.yaml`): top-level `resources.{requests,limits}`, **default limit cpu 150m / mem 500Mi**, requests cpu 10m / mem 50Mi. Set `deploy/values/caretta.yaml` `resources` to requests 50m/256Mi, limits 300m/**1Gi**. Note: that's already ~3× the MASTER_PLAN §1.7 budget for Caretta (~150MB) — a real cost finding; if it still OOMs at 1Gi it's a leak/churn issue → fall back to **beyla-network** (already running, no extra cost) for the topology map.
Why: get Caretta Running so it can emit `caretta_links_observed` (the topology-map source); the OOM was the only thing stopping it (kernel is fine).
Impact / apply: `helm upgrade --install caretta groundcover/caretta -n caretta -f deploy/values/caretta.yaml` (or re-sync + `skctl up`); then confirm the agent stays Running (no OOM) and `caretta_links_observed` returns client/server pairs. Open item still: the agent's actual Prometheus metrics port (7117 is a guess; the chart routes via its bundled VM's scrape — once Running, check the agent's container ports / VM scrape config and set `prometheus.io/port` to match, or re-enable VM and query it). Then I build the topology-map consumption.
Links: LOG-077/078; deploy/values/caretta.yaml; Caretta chart/values.yaml (resources); MASTER_PLAN §1.7 (RAM budget — Caretta heavier than budgeted).

## LOG-080 · 2026-06-21 · STEP (ROAD Stage 2 eBPF) — auto-discovered topology map (Caretta → /api/topology → dashboard)
What: Caretta is **Running on kernel 7.0** (after the 1Gi bump, LOG-079) and emitting `caretta_links_observed` with REAL flows — incl. `plc-gateway → mqtt-broker:1883` (MQTT, the app traffic beyla is blind to); scrape works on port 7117; labels are clean workload names. Built the topology-map consumption against this confirmed schema:
 (a) `api/main.py`: new `GET /api/topology` (+ `PROM_URL` env) queries Prometheus for `caretta_links_observed`, collapses Caretta's per-role/per-kind duplicate series into ONE directed workload edge per client→server, scopes to the **factory** namespaces (drops monitoring/infra flows), returns `{edges:[{src,dst,src_ns,dst_ns,port,bytes}], source}`; graceful (`source:unavailable` if Caretta/Prom down). The pure `_parse_caretta` was sanity-checked against the real sample (roles deduped to max-bytes; a monitoring edge and a self-edge correctly filtered).
 (b) `dashboard`: new `Topology.jsx` (3D force map — nodes coloured by tier core/data/edge, edges labelled `:port · bytes`) + a "Discovered topology · eBPF" panel, fetched in the 5s poll (graceful). This is the deck's "zero-config, eBPF found every edge" map (MASTER_PLAN §2.6/§2.7 plane-1).
Why: the clean eBPF deliverable (CCR-latency hop dropped per LOG-078 as not-instrumentable). Caretta's L4 capture sees all protocols (MQTT/SQL/HTTP), which is the right topology source.
Verify: api `py_compile` + `_parse_caretta` sanity check pass; dashboard `npm run build` clean (static export 4/4).
Impact / apply on box: rebuild `skn/api:v0.1` + `skn/dashboard:v0.1` + import + `kubectl rollout restart deploy/api deploy/dashboard -n aiops`. Then `/api/topology` should list plc→mqtt, telemetry-ingest→timescaledb (5432), alert-dispatcher→notify-gateway, edge-ui→firmware-cache, etc. (the discovered plane-1), and the dashboard panel renders it. Open: the **engine A3-witness** use of `ebpf_edges` stays future (a network signal only — network ≠ disk/cpu coupling); Caretta at 1Gi is heavy vs the §1.7 budget (watch; beyla-network is the lighter fallback if needed); beyla RED for the S4 HTTP paths is a later sub-item.
Links: LOG-077/078/079; api/main.py; dashboard/app/{Topology.jsx,page.jsx}; MASTER_PLAN §2.6/§2.7; Caretta `caretta_links_observed`.

## LOG-081 · 2026-06-21 · STEP — unified graph (causal over discovered topology); topology stops re-heating; Grafana window
What: Three operator UX fixes on the dashboard. (1) **Merged the two graphs into one** (MASTER_PLAN §1.4.5 intent — causal edges overlaid on the steady topology): `Graph.jsx` now takes a `topo` prop, unions nodes from causal ∪ topology, and renders **causal edges** (edgeColor by weight, hot particles on a live incident) over the **eBPF-discovered network backbone** (thin grey, labelled `:port`); the standalone `Topology.jsx` + its panel are removed. `/api/topology` confirmed returning the real factory flows (telemetry-ingest→timescaledb:5432 2.1GB, plc/telemetry/safety/ccr/vision→mqtt:1883, alert→timescaledb). (2) **Killed the 5s churn:** the graph re-lays-out only on a STRUCTURAL signature — roles + causal state/weight-bucket + the network edge SET, NOT its byte counts — so the topology no longer re-heats every poll. (3) **Grafana PSI embed** window 30m→15m (it refreshes every 5s and is now-pinned; on a 30-min span the advance was imperceptible — 15m reads as live).
Why: operator — wanted one graph, no per-5s topology re-render, and the Grafana window to look live.
Verify: `npm run build` clean (static export 4/4). API unchanged this turn.
Impact / apply: rebuild `skn/dashboard:v0.1` + import + `kubectl rollout restart deploy/dashboard -n aiops` (no api rebuild). Expect ONE "Causal graph" panel = grey discovered-topology backbone with causal edges overlaid (hot on S1), stable layout, Grafana PSI on a live 15-min window. If the Grafana window still doesn't read as moving, fallback = React-driven absolute-window updates (accepts a periodic iframe reload).
Links: LOG-080 (/api/topology); MASTER_PLAN §1.4.5 (causal overlaid on topology); dashboard/app/{Graph.jsx,page.jsx}.

## LOG-082 · 2026-06-21 · STEP (ROAD Stage 5 DONE) — recommendation engine (PS-Q4): right-sizing + fairness index
What: Built the deterministic recommendation engine — the last uncovered judge question (PS-Q4 "which workloads need optimization?"). `api/main.py`: new `GET /api/recommendations` queries Prometheus (reusing the `PROM_URL` added for topology) for per-pod requests/limits (kube-state) and **p95 usage** (`quantile_over_time(0.95, …[1h:5m])` for cpu rate + working_set), then emits **KAI scheduler verbs**: `reclaim` (p95 < ½ request → over-provisioned) and `resize` (p95 > 85% limit → throttle/OOM risk), plus a per-namespace **fairness index** (Gini over total PSI stall). Pure helpers `_rightsize`/`_gini`/`_fairness` sanity-checked: matches the §1.5.6 example (`analytics-batch 1.0 CPU, p95 80m → reclaim 896m`) and flags the over-provisioned RAM pod (`firmware-cache → reclaim 638 MB`). Graceful (`source:unavailable` if Prometheus down). `dashboard`: a "Recommendations · right-sizing" panel (verb-coloured cards + fairness line), polled **every 30s** (the subqueries are heavy and change slowly). No physics/infra/eBPF dependency — pure analysis of already-scraped metrics.
Why: PS-Q4 had zero machinery; this is the highest value-per-risk close (no S3-style physics wall). ROAD Stage 5.
Verify: api `py_compile` + helper unit-sanity (gini known values; reclaim/resize/right-sized rules); dashboard `npm run build` clean (static export). Box-apply pending.
Impact / apply on box: rebuild `skn/api:v0.1` + `skn/dashboard:v0.1` + import + `kubectl rollout restart deploy/api deploy/dashboard -n aiops`. Then `curl :30088/api/recommendations` → right-sizing cards + per-ns Gini; the dashboard panel renders them. Tunables: `RECLAIM_FRAC`/`RESIZE_FRAC` (env on api). Note: CronJob pods (analytics-batch/log-archiver) only appear if they ran within the 1h p95 window. **PS-Q4 now answered.** Deferred (optional): feed cards into `/api/narrative` + `cases.remediation`; `consolidate`/`throttle` verbs tied to a causal root.
Links: LOG-080 (PROM_URL); MASTER_PLAN §1.5.6 (right-sizing), §4.1 (KAI verbs + fairness); api/main.py; dashboard/app/page.jsx; ROAD Stage 5.

## LOG-083 · 2026-06-21 · FIX — Stage 5 finish-up: fairness index populated; idle verdict label "steady" not "fallback"
What: Two corrections after the box run. (1) **Fairness was empty** — the single `rate({__name__=~"container_pressure_(io|cpu|memory)_stalled_seconds_total",...}[5m])` query returned nothing on the live Prometheus (the right-sizing queries worked, so it's that regex-name form). Replaced with **3 explicit** `sum by(namespace,pod)(rate(container_pressure_{io,cpu,memory}_stalled_seconds_total{namespace=~"factory-.*"}[5m]))` queries summed per pod in Python — the exact form the aggregator already proves works. (2) **Dashboard mislabel** — `source:"steady"` (the by-design idle path, LOG-075) showed as "template fallback"; the Verdict panel now reads **"steady"** for that source ("gemma4" for llm, "template fallback" only for an actual model fallback). Clarified in ROAD Parked: gemma4 tuning goal = an *incident* verdict reliably renders via the model (minimize fallback); the idle "steady" line is template-by-design (we skip the model with no root), NOT a failure — gemma4 IS used on incidents (S1 prose confirmed earlier).
Why: operator — fairness `[]`, the misleading "template fallback" at idle, and a re-flag to fine-tune gemma4 / rely on fallbacks less.
Verify: api `py_compile` + dashboard `npm run build` clean.
Impact / apply: rebuild `skn/api:v0.1` + `skn/dashboard:v0.1` + import + `kubectl rollout restart deploy/api deploy/dashboard -n aiops`. Then `/api/recommendations.fairness` lists per-ns Gini; the idle Verdict panel labels "steady". **Stage 5 complete** (right-sizing + fairness live; PS-Q4 answered).
Links: LOG-082 (Stage 5), LOG-075 (steady narrator); api/main.py; dashboard/app/page.jsx; ROAD Stage 5 + Parked.

## LOG-084 · 2026-06-21 · NOTE — **SESSION HANDOFF** (mark-one: audit → Stages 0/1/2/5 + recency; next = #2 S5-forecast, then #3 S2+DB-probe)
Read first on resume: **ROAD_TO_COMPLETION.md** (forward plan + the current status matrix) and this entry. ROAD supersedes REMAINING.md (archived to `archive/`).

SESSION ARC (this window): code/plan audit vs MASTER_PLAN/BUILD_GUIDE → wrote ROAD_TO_COMPLETION.md → executed, each piece logged + box-verified:
- LOG-067 audit + ROAD + doc reorg (`archive/` = P0_DESKTOP_SETUP + REMAINING).
- LOG-068 **Stage 0** — source-rooted case promotion (only a `write`-evidenced root mints a case).
- LOG-069 **Stage 1** — multi-signal engine psi_io/cpu/mem; merged graph w/ per-edge `signal`; new `engine/merge.py`.
- LOG-071 recency reset (`RESET_WINDOW`) + DEV_K 4→3.5 + idle-label → near-realtime verdict reset.
- LOG-073/074 **Stage 2 slice 1** (D-015) — same-node PSI coupling for the SOURCE-edge path → S3 drawable via PSI w/o eBPF; false-edge storm fixed (victim∈active; cpu/mem edges purely live, no backbone).
- LOG-075 narrator: idle returns "steady", skips the LLM.
- LOG-077→081 **Stage 2 slice 2** — Caretta installed (coords fixed; kernel-7.0 eBPF OK @1Gi after an OOM) → `/api/topology` (real MQTT/SQL/HTTP flows) → ONE unified causal+topology graph (topology stopped re-heating every 5s); Grafana window 15m.
- LOG-082/083 **Stage 5** — recommendation engine `/api/recommendations` (right-sizing in KAI verbs + per-ns fairness Gini) + dashboard panel. **PS-Q4 answered.**

LIVE on the cluster (box `soumyadip-b460md3h`, tailnet 100.93.123.48; **everything through LOG-083 is rebuilt + applied**):
- L0 factory 15 pods · L1 Prometheus+PSI + **Caretta** (ns `caretta`, Running) · L2 aggregator · L3 correlation-engine (multi-signal; memory on `engine-memory-pvc`) · L4 api(:30088)+dashboard(:30080)+Grafana(:30030)+Prometheus(:30090).
- Box-verified this session: S1 → root cooling-monitor + clean blast + gemma4 prose; S0/idle → "steady" + clean ~3-edge backbone; S3 → honest empty (no real victim on this box); `/api/topology` → factory map; `/api/recommendations` → right-sizing + fairness (core 0.746 / data 0.613 / edge 0.778).
- Known reds (deferred, non-blocking): **alloy CrashLoop** (Loki/logs → blocks A2); **S3 physics** (16-thread box can't saturate cpu → no cross-pod stall).

NEXT — agreed order, **pause after each** (operator says continue):
- **#2 S5 OOM-forecast** — wire `detectors.forecast_to_limit` onto psi_mem/working_set → emit an `incipient` finding ("OOM in ~Ns") before vision-qc's leak kills it. Engine already runs psi_mem (Stage 1); the forecaster is dead code. Physically reliable here (leak is deterministic, unlike S3).
- **#3 S2 + DB probe** — verify S2 (log-archiver tar; rides the S1 psi_io path) as a distinct root; add a tight `timescaledb` tcpSocket/exec probe so the storm induces a restart → mechanizes **PS-Q2** (PVC-I/O↔restart); feed restarts as evidence.
- then per ROAD: Stage 3 (A2 needs the alloy/Loki fix; A5 verdict + bounded K8s tools), Stage 4 (S3 physics, S4+Chaos Mesh, rehearsal ledger), Stage 6 (timeline/replay, pod drawer, full PSI heatmap, insight feed), Stage 7 (hardening/air-gap/golden run). **Parked:** gemma4 *incident*-prose tuning (idle=template by-design, not a failure); CPU usage-coupling backbone.

WORKING AGREEMENT (unchanged): laptop = git master (commit/push there only); desktop = Syncthing runtime over tailnet; **any baked-code change (any `main.go`/`main.py`/`pipeline.py`/`service.py`/`api/`/`init.sql`/Dockerfile, dashboard JSX) needs `docker build` + `k3s ctr images import` + `kubectl rollout restart`**; chart/values/configmap/env changes apply via `skctl up`/`kubectl apply` (no rebuild); **`run_pass` stays a PURE function — fixtures must stay green** (currently `correlation/` 40+ tests across test_engine/state/merge); tune via env/values and log every change here; running is the operator's.
Links: ROAD_TO_COMPLETION.md; LOG-067 (session start), LOG-082/083 (last applied); MASTER_PLAN (architecture); EXPLANATIONS.md (code map).

## LOG-085 · 2026-06-21 · STEP (ROAD #2 / Stage 3 forecaster) — S5 OOM early-warning: working_set→limit forecast wired
What: Turned the dead-code A1 forecaster (`detectors.forecast_to_limit`, unused since LOG-014) into a
live **OOM early-warning**. New PURE module `correlation/engine/forecast.py` (`incipient_findings`,
sibling to `merge.py`): projects each pod's **`working_set`** ramp to its **memory limit** and emits an
`incipient` finding (`{pod, signal:mem, kind:incipient, class:leak, eta_s, value, limit, headroom_frac}`)
when the climb will breach within `FORECAST_HORIZON_S` (default 900s). Decision: forecast
**working_set→limit**, NOT psi_mem — a memory *stall* has no clean cap to extrapolate to, while
working_set→limit is the deterministic OOM predictor MASTER_PLAN §2.3 names ("working_set ramp"). A leak
is **self-caused** (source == victim), so it forms no cross-pod edge — it rides as a separate
`merged["incipient"]` list, not a graph edge. Wiring (all caller-side; `run_pass` byte-identical):
 - `aggregator/queries.yaml`: `mem` now `sum by(namespace,pod)(working_set…)` (one clean per-pod series),
   + new `mem_limit` = `sum by(namespace,pod)(kube_pod_container_resource_limits{resource="memory"})`.
   Both threshold-less → no spurious L2 events (the aggregator rings every query but only emits for
   schema+threshold signals). **ConfigMap-only — no aggregator image rebuild.**
 - `service.py`: `build_inputs` also collects `mem`+`mem_limit`; `loop()` computes incipient post-merge
   (`limit = mem_limit[-1]`), attaches `merged["incipient"]`. New env `FORECAST_SIGNAL/LIMIT/HORIZON_S`.
 - `api/main.py`: `/api/graph` passes `incipient` through (workload-normalized); `/api/narrative`
   returns a **deterministic, model-free** forecast line on the no-root path (`source:"forecast"`) — the
   "before the kernel did" beat must never depend on Ollama (P5 discipline, cf. LOG-075 steady path).
 - `dashboard/app/page.jsx`: Verdict sub-label maps `forecast` (else it read "template fallback", the
   LOG-083 class of mislabel).
Why: S5's headline ("forecast OOM before it happens", §5.5 demo beat 5) was unbuilt — the forecaster
existed but nothing called it. Physically reliable here (vision-qc's leak is a deterministic ~6 MB/s
ramp, unlike the physics-blocked S3). The recent-tail slope fit (24 samples ≈ 2 min) naturally plateaus
out timescaledb's shared_buffers cache-fill (LOG-023) → no false alarm; firmware-cache near its limit but
FLAT stays silent (usage ≠ pressure).
Verify: **45/45 local** (`correlation/` — was 40; +5 in new `tests/test_forecast.py`: leak→ETA before the
limit; flat-near-limit→silent; plateau cache-fill→silent; missing/zero limit→skipped; ETA-beyond-horizon
filtered but fires with a wider horizon). 13 kernel fixtures intact (`run_pass` untouched). `py_compile`
service/forecast/api clean; dashboard `npm run build` 4/4.
Impact / apply on box (box-apply pending):
 - aggregator: reload the queries ConfigMap + `kubectl rollout restart deploy/aggregator -n aiops` (NO rebuild).
 - engine: rebuild `skn/correlation-engine:v0.1` + import + `kubectl rollout restart deploy/correlation-engine -n aiops`.
 - api+dashboard: rebuild `skn/api:v0.1` + `skn/dashboard:v0.1` + import + `kubectl rollout restart deploy/api deploy/dashboard -n aiops`.
 - Tunable (no rebuild): `kubectl set env deploy/correlation-engine -n aiops FORECAST_HORIZON_S=600` (lower
   if any slow climber false-fires; raise to warn earlier). Verify S5: arm vision-qc's leak (`LEAK_ENABLED=true`
   / its trigger) → BEFORE the OOMKill, `/api/graph.incipient` shows vision-qc with an `eta_s` and
   `/api/narrative` reads "Early warning: vision-qc … projected OOM in ~Ns" (source forecast); it re-arms each
   leak cycle after the restart. S0/idle + S1 unaffected (no incipient when nothing ramps to a limit).
Links: ROAD_TO_COMPLETION.md (#2, Stage 3 forecaster, S5 row); MASTER_PLAN §1.4.2 (forecaster), §2.3/§2.5 (S5),
§5.5 (demo beat 5); DESIGN §3.3 (forecast_to_limit); LOG-069 (Stage 1 psi_mem), LOG-014 (forecaster shipped
unused), LOG-075/083 (model-free narrator paths), LOG-084 (handoff #2); correlation/engine/forecast.py,
correlation/service.py, aggregator/queries.yaml, api/main.py, dashboard/app/page.jsx, correlation/tests/test_forecast.py.

## LOG-086 · 2026-06-21 · STEP + FIX (complete S0/S1/S2/S5) — idle-write silence, S5 ETA polish + insight feed, S2 self-contained distinct-root
What: Four coordinated changes to make S0/S1/S2/S5 demo-clean.
 (1) **S0 idle silence (FIX).** Operator saw a `cooling-monitor` root-cause verdict at idle WITHOUT firing
 S1 -- the steady journal in `workloads/cooling-monitor/main.py` wrote 800 lines **+ `os.fsync()` every 1s**
 on the dedicated slow HDD (D-014), i.e. the most aggressive idle writer on the shared disk, which the
 `io_write` source-attribution legitimately latched onto. Now a **bare-minimum heartbeat**: ~10 lines every
 ~10s, **truncating** (`"w"`, bounded -- was unbounded append) with **NO idle fsync** (page cache only -> no
 device stall). Env-gated `JOURNAL_LINES/JOURNAL_PERIOD_S/JOURNAL_FSYNC_EVERY`. The FLUSH poll stays 1s so S1
 is unchanged; the fio storm path is untouched.
 (2) **S5 ETA polish.** `engine/forecast.py` now fits the slope over the **active climb** (`_fit_segment`:
 from the latest upward CUSUM onset, capped at `tail`, floored at 6 samples) instead of the full 2-min tail,
 so early in a leak the ETA reflects the real ~5-6 MB/s rate instead of the ~6x-diluted **397s** the operator
 saw (box: leak died in ~70s). +1 test (anchored ETA < diluted-tail ETA). The 5 existing forecast tests hold
 (the cap means a full-window or stale-onset climber still uses the recent tail).
 (3) **S5 visibility.** Dashboard **AI insight feed** panel (`dashboard/app/page.jsx`) renders
 `/api/graph.incipient` (forecasts) + `findings` (onsets) **always** -- so the OOM warning shows even while a
 disk incident holds the causal verdict (the gap the operator hit: `/api/narrative` suppresses the forecast
 when a causal root exists, by design; the feed is the always-on surface).
 (4) **S2 self-contained + distinct root.** Two fixes. (a) `workloads/log-archiver/archive.sh` now generates
 its OWN bulk payload (`dd` of `S2_SEED_MB`, default 2048 MB) then `tar czf`s it (sequential write + read) --
 necessary because the S0 fix removed the unbounded `thermal.log` that S2 used to tar. (b)
 `scenarios/S2/trigger.sh` names the job **`log-archiver-s2`** (fixed, no timestamp) so `workload()` (drops
 the last 2 name segments) resolves pod `log-archiver-s2-<hash>` back to **`log-archiver`** -- a STORAGE
 member that couples to the shared disk and is blamed as source; the old `s2-run-<ts>` resolved to `s2-run`
 (not in STORAGE) and could never form an edge (the LOG-075 job-naming trap). + `scenarios/S2/reset.sh` (new),
 `S2_SEED_MB` Helm-tunable on the cronjob (values.yaml).
 (5) **Runbooks.** S1 refreshed (stale `fsync=8/runtime=45` -> live `fsync=2/runtime=60`; the OBI->CCR hop
 removed per LOG-078; box-measured verdict from LOG-070); S2 + S5 authored; S0 gains the idle-write guarantee.
Why: the idle verdict was a real false positive (a steady fsync'd writer on a slow HDD is a believable
source); the S5 ETA was embarrassingly long; the insight feed makes the forecast visible during a concurrent
incident; S2 needed both a distinct root (job naming) and its own bulk (the journal is now tiny).
Verify: **46/46 local** (was 45; +1 onset-anchoring in test_forecast.py; `run_pass` untouched -> 13 fixtures
intact); `py_compile` cooling-monitor/forecast clean; dashboard `npm run build` 4/4; values.yaml = one inline
env (helm verify on the box).
Impact / apply on box (box-apply pending):
 - cooling-monitor: rebuild `skn/cooling-monitor:v0.1` + import + `kubectl rollout restart deploy/cooling-monitor -n factory-data` (baked main.py).
 - log-archiver: rebuild `skn/log-archiver:v0.1` + import (baked archive.sh) + `./deploy/skctl up --mode solo` (applies S2_SEED_MB).
 - engine: rebuild `skn/correlation-engine:v0.1` + import + rollout restart (forecast.py).
 - dashboard: rebuild `skn/dashboard:v0.1` + import + rollout restart (insight feed).
 - scenario scripts synced, no rebuild.
 - Verify: **S0** idle -> insight feed "no active findings", verdict "steady", NO cooling-monitor root.
   **S1** -> root cooling-monitor (unchanged). **S2** `bash scenarios/S2/trigger.sh` -> root **log-archiver**
   -> timescaledb `[write,pvc,temporal]` (DISTINCT from S1); raise `S2_SEED_MB` / `dd oflag=direct` if the
   write is too weak to register (or add an `io_read` source for a pure read-starvation root -- see the S2
   runbook). **S5** -> insight feed `forecast · vision-qc · OOM in ~Ns` with a realistic ETA before the kill.
Links: LOG-085 (#2 forecaster), LOG-075 (job-naming trap + idle garbage), LOG-070 (S1 box verdict),
LOG-054/051 (S1 params), LOG-078 (CCR hop dropped), LOG-023 (cache-fill plateau), D-014 (slow HDD);
workloads/cooling-monitor/main.py, workloads/log-archiver/archive.sh, correlation/engine/forecast.py,
correlation/tests/test_forecast.py, dashboard/app/page.jsx, deploy/charts/factory/values.yaml,
scenarios/S{0,1,2,5}/*.

## LOG-087 · 2026-06-21 · FIX (S2 OOMKill + forecaster false-fires) + NOTE (timescaledb idle-stall diagnosed)
What: Two box-found refinements on top of LOG-086, plus a diagnosis of a third issue.
 (1) **S2 OOMKill fixed.** First box S2 run: `log-archiver-s2-<hash>` **OOMKilled in ~8s** (Job backoff
 looped three of them) -> the storm never ran, so the root fell back to `cooling-monitor` (NOT the distinct
 root S2 needs). Cause: `archive.sh`'s `dd … conv=fsync` syncs only at the END, so writing the 2 GB payload
 accumulated dirty page cache against log-archiver's **256Mi** memory limit -> cgroup OOM before ~256 MB was
 written. FIX: `conv=fsync` -> **`oflag=direct`** (O_DIRECT bypasses the page cache -> real device I/O that
 saturates the spindle AND no dirty-page pile-up). LOG-086's verify already named this as the remedy.
 (2) **Forecaster false-fires fixed.** The insight feed showed bogus OOM warnings — `cooling-monitor OOM ~46s`
 during S1 (working_set 116 MB / 256Mi = **43%**, transient fio-driven growth) and `safety-interlock OOM ~710s`
 (**24%** of limit, slow drift). The forecaster fired on ANY working_set trending to its limit. FIX:
 `engine/forecast.py` gains a **proximity gate** `min_frac` (default **0.6**, env `FORECAST_MIN_FRAC`): only warn
 once working_set is already past 60% of the limit — a real OOM risk is CLOSE to the cap; a 43% transient / a
 24% drift is not. vision-qc's true leak climbs past 60% en route to OOM, so it still fires (box: 82% ->
 "OOM ~12s"). +1 test (below-min_frac skipped, fires at a lower bar); the operator's onset-anchoring test
 passes `min_frac=0` (its fixture tops out at 50%, below the gate). **47/47 local**, 13 run_pass fixtures intact.
 (3) **NOTE — timescaledb chronic psi_io keeps re-lighting a `cooling-monitor` verdict at idle (NOT yet fixed).**
 The PSI/IO panel shows timescaledb at a SUSTAINED ~0.15 psi_io (right at the 0.15 L2 threshold) from its
 deliberately-aggressive checkpointing (`max_wal_size=256MB -c checkpoint_timeout=60s`, the Dockerfile CMD —
 "honest PVC stress", MASTER_PLAN 2.2#5). That keeps it borderline-active, and the structural
 `cooling-monitor->timescaledb` psi_io backbone edge then names cooling-monitor root with no scenario firing —
 so S0 is not RELIABLY silent. Likely mechanism: the baseline storm-skip (`state.update_baselines`, line ~644)
 excludes a *sustained*-elevated level, so the baseline never learns 0.15 as timescaledb's normal and it reads
 as a perpetual deviation. Recommended fix (operator's call — a realism trade-off): relax the checkpoint cadence
 (`checkpoint_timeout 60s->300s`, `max_wal_size 256MB->1GB`) so idle is quiet — S1/S2 still stall it via the
 EXTERNAL storm, so the victim story survives (in fact sharpens). Deeper alt: let the baseline learn a
 long-sustained level as the new normal (riskier; could mask real sustained incidents).
Why: S2 must produce a distinct root (the archiver has to actually run, not OOM); the insight feed must not cry
wolf; S0 silence is the credibility scenario.
Verify: 47/47 local (13 run_pass fixtures intact); `py_compile` service/forecast clean.
Impact / apply on box:
 - log-archiver: rebuild `skn/log-archiver:v0.1` + import; re-run `bash scenarios/S2/trigger.sh` (no OOM; expect root=log-archiver).
 - engine: rebuild `skn/correlation-engine:v0.1` + import + `kubectl apply -f deploy/engine.yaml` + rollout restart (forecast.py + FORECAST_MIN_FRAC).
 - Tunable (no rebuild): `kubectl set env deploy/correlation-engine -n aiops FORECAST_MIN_FRAC=0.5` (lower = warn earlier / more lead).
 - timescaledb (NOTE 3): NOT changed this turn — pending the operator's checkpoint-cadence call.
Links: LOG-086 (S0/S1/S2/S5 base), LOG-085 (forecaster), LOG-075 (job-naming), D-014 (slow HDD), MASTER_PLAN
2.2#5 (aggressive checkpoint); workloads/log-archiver/archive.sh, correlation/engine/forecast.py,
correlation/service.py, deploy/engine.yaml, correlation/tests/test_forecast.py.

## LOG-088 · 2026-06-21 · FIX (implements LOG-087 NOTE 3) — timescaledb checkpoint relaxed for a truly silent S0
What: `workloads/timescaledb/Dockerfile` CMD: `max_wal_size 256MB->1GB`, `checkpoint_timeout 60s->300s`
(`shared_buffers=256MB` unchanged). The deliberately-aggressive 60s/256MB checkpointing flushed WAL to the
slow HDD constantly -> timescaledb's idle psi_io sat at a SUSTAINED ~0.15 (the 0.15 alert line), the
structural `cooling-monitor->timescaledb` psi_io backbone then named cooling-monitor root with NO scenario
firing (operator screenshot). At 300s/1GB and the current 1Hz plc write load, idle WAL barely grows, so
checkpoints are rare/timeout-driven -> idle psi_io drops to ~0 -> baseline learns it -> S0 silent.
Why: S0 silence is the credibility scenario; the chronic self-checkpoint stall was a standing false positive.
The victim story is INTACT (in fact sharper): under S1/S2 timescaledb stalls from the EXTERNAL shared-disk
storm (cooling-monitor fio / log-archiver), so the stall is cleanly attributable to the aggressor rather than
muddied by self-checkpoints. Only IDLE checkpoint I/O is reduced; the WAL/fsync victim path under contention
is unchanged.
Impact / apply on box: rebuild `skn/timescaledb:v0.1` + import + `kubectl rollout restart deploy/timescaledb
-n factory-data` (data persists on tsdb-pvc; new CMD applies on restart). If S0 still flickers every ~5 min
(a timeout checkpoint), raise `checkpoint_timeout` further (e.g. 600s). **DOC FLAG:** MASTER_PLAN §2.2 #5 +
§2.3 still describe 60s/256MB — fold into the next-session docs pass (stale-flags).
Links: LOG-087 NOTE 3 (this implements it), LOG-023 (shared_buffers cache fill, untouched), D-014 (slow HDD),
MASTER_PLAN §2.2 #5 (now stale); workloads/timescaledb/Dockerfile.

## LOG-089 · 2026-06-21 · NOTE — **SESSION HANDOFF** (S0/S1/S2/S5 code-complete; next = docs workstream)
Read first on resume: **ROAD_TO_COMPLETION.md** + this entry. Scope locked with the operator: finish
**S0/S1/S2/S5** end-to-end (NOT S3/S4/DB-probe); `io_read` source signal deferred to the next operations turn.

DONE this session (LOG-085→088), all local-verified (`correlation/` **47/47**, 13 run_pass fixtures intact):
- **LOG-085** #2 — S5 OOM forecaster wired (`engine/forecast.py`, working_set→limit `incipient`).
- **LOG-086** S0/S1/S2/S5 pass — cooling-monitor idle-write silence (heartbeat, no idle fsync, bounded);
  S5 ETA onset-anchored (`_fit_segment`); dashboard **AI insight feed**; S2 self-contained payload + fixed
  `log-archiver-s2` job name (distinct root); S1 runbook refreshed, S2/S5 runbooks authored.
- **LOG-087** S2 `dd conv=fsync`→`oflag=direct` (the archiver OOMKilled in ~8s, dirty-page flood of the 256Mi
  limit → storm never ran → root fell back to cooling-monitor); forecaster **`min_frac` proximity gate**
  (default 0.6, env `FORECAST_MIN_FRAC`) kills the false `cooling-monitor`(43%)/`safety-interlock`(24%) OOM cards.
- **LOG-088** timescaledb checkpoint relaxed 60s/256MB → **300s/1GB** (idle psi_io was chronically ~0.15 →
  structural cooling-monitor→timescaledb backbone re-lit a phantom root at idle → S0 not reliably silent).

BOX-APPLY PENDING (operator applying all together): rebuild `skn/{log-archiver,correlation-engine,timescaledb}:v0.1`
(+ cooling-monitor/api/dashboard if not already), reload aggregator-queries ConfigMap, `kubectl apply -f
deploy/engine.yaml`, rollout restart. Box-verified earlier this session: S0 silent (post cool-mon fix), S1 root
cooling-monitor, S5 forecast with realistic ETA. RE-VERIFY after this apply: S2 distinct root=log-archiver (was
OOMing), S0 stays silent with the timescaledb checkpoint change, no false OOM cards.

NEXT SESSION — **docs workstream** (the gap: docs capture architecture/rationale but NOT the demo-as-it-runs):
- **Current demo runbook** — what works today (S0/S1/S2/S5 + topology + recommendations + forecast), press-this/
  say-this, fallbacks, and honest answers to the judge Qs (Q3+Q4 live; Q1/Q2 = engine-ready/gated; the S3
  "no-network" ask is the exposed flank).
- **README refresh** — API table missing `/api/narrative`,`/api/topology`,`/api/recommendations`; fix the two
  stale `REMAINING.md` links (it's archived → ROAD supersedes); surface forecast/incipient + recommendations.
- **MASTER_PLAN stale-flags** — §2.2#5/§2.3 timescaledb now 300s/1GB (LOG-088); §1.2/§2.5 OBI→CCR hop dropped
  (LOG-078); §2.3/§2.5 S3 mechanism physically wrong (LOG-076); §5.5 demo script aspirational (S3 blocked, S5
  forecast is new, ~3 of 6 panels). Correct via the runbook/report, not by editing the normative plan in place.
- **Runbooks** — verify S2/S5 runbooks against the box post-apply; refresh as built.
- (Then, per ROAD/scope, the remaining P5/P6/P7 items I listed: forecast-in-narrative + warm/keep_alive, S2/S5
  console buttons, pod drawer, full PSI heatmap, fairness widget, rehearsal ledger.)

WORKING AGREEMENT (unchanged): laptop = git master; baked-code change (`main.py`/`main.go`/`pipeline.py`/
`service.py`/`api/`/Dockerfile/dashboard JSX) needs docker build + `k3s ctr images import` + rollout restart;
chart/values/configmap/env apply via `skctl up`/`kubectl apply` (no rebuild); **`run_pass` stays PURE — fixtures
green**; tune via env/values and log every change; running is the operator's.
Links: ROAD_TO_COMPLETION.md; LOG-085→088 (this session); LOG-084 (prior handoff); MASTER_PLAN; EXPLANATIONS.md.

## LOG-090 · 2026-06-21 · NOTE — box-apply result: S2 OOM fixed + forecasts clean; root-attribution gaps found
What: Operator applied LOG-087/088 on the box. Confirmed:
 - **S2 OOMKill FIXED** — `log-archiver-s2-<hash>` now reaches `Completed` (was OOMKilled in 8s); `oflag=direct`
   bypasses the page cache so the 2GB write no longer floods the 256Mi limit. The storm runs.
 - **Forecaster clean** — `/api/graph.incipient = []` at idle/post-S2; the `min_frac` gate removed the
   cooling-monitor(43%)/safety-interlock(24%) false OOM cards. gemma4 incident prose reads well.
Two REMAINING root-attribution gaps (NOT yet fixed):
 1. **S2 root still `cooling-monitor`, not `log-archiver` — TIMING.** The verdict was read **2m12s AFTER** the
    Job Completed. log-archiver is a ~2-min Job that out-writes everyone *while running* (2GB @ ~15-30MB/s
    direct), but once it Completes the pod is gone -> its edge render-skips (no live pod) -> the lingering
    timescaledb stall is misattributed to the persistent shared-disk writers (cooling-monitor/dcim-bridge),
    whose io_write spiked under the contention it caused. FIX (operational): read `/graph` DURING the storm
    (~t+60-90s, pod still Running); raise `S2_SEED_MB` 2048->4096 (values.yaml + skctl up) so the storm lasts
    long enough to catch + fill the 12-sample window. Expect root=log-archiver mid-storm.
 2. **Structural backbone promoted to ROOT with stale evidence (the remaining S0-silence gap).** Even with
    cooling-monitor quieted (tiny flat heartbeat ~40B/s, no live write correlation possible), it resurfaces as
    #1 root with stale **"write"** evidence whenever timescaledb stalls — the HELD structural psi_io edge
    (`l3-memory.db`, high floor from past S1 runs) carries its historical evidence and the merge ranks it as
    root. timescaledb's checkpoint relax (LOG-088) cut how OFTEN this triggers but not the mechanism; dcim-bridge
    (4MB fdatasync/5s, unchanged) is still a real steady writer. **Engine fix (next work session, after docs):**
    a held/structural edge must NOT win ROOT without a LIVE deviating source this pass (a structural edge is
    descriptive coupling, not blame — extends LOG-074/075). Keep `run_pass` pure; the gate is in the
    merge/ranking or `state._render` promotion. Until then S0 is silent only between timescaledb's I/O ticks.
Why: record the box result + the two precise gaps so the next session resumes without re-deriving them.
Links: LOG-087/088 (applied), LOG-074/075 (source-edge real-victim + held-garbage precedents), LOG-070 (S1
backbone), D-014 (slow HDD); scenarios/S2/*, correlation/engine/{state,merge,pipeline}.py.

## LOG-091 · 2026-06-21 · FIX (S2 root [] — the storm saturated bandwidth but produced no victim) — concurrent fsync-heavy fio storm
What: Box re-run of S2 reading `/graph` DURING the storm (LOG-090 gap-#1 remedy; S2_SEED_MB raised 2048->6144)
returned `root: []` for the WHOLE storm (t+30s..t+165s, pod `Running`; `Succeeded` by t+180s) and a steady "no
causal contention" verdict — even though Grafana shows `log-archiver`'s psi_io spiking to ~2.6. So gap #1 was
NOT the (only) cause: even read mid-storm, no root forms. Diagnosis: the LOG-087 `dd oflag=direct` is a SINGLE
sequential O_DIRECT stream — it saturates the archiver's OWN bandwidth (it self-stalls -> the 2.6 spike) but does
NOT create the concurrent small-fsync IOPS contention that stalls a co-resident DB. `timescaledb`'s WAL fsync
(continuous from telemetry-ingest commits) slips through between the big sequential blocks, never crosses DEV_K
-> no victim -> the engine (correctly, by the LOG-074 real-victim rule) forms no edge -> no root. Both PVCs are
on the same `slowdisk` HDD (deploy/slowdisk.yaml), so it is the I/O *character*, not the device: S1's storm is
`fio --numjobs=4 --fsync=2 --direct=1` (concurrent, fsync-heavy) and DOES stall timescaledb. The timescaledb
Dockerfile comment ("under S1/S2 timescaledb still stalls") held for S1's fio but was wrong for S2's dd. Also
found: S2_SEED_MB=6144 on a 5Gi PVC was hitting ENOSPC mid-write (swallowed by `2>/dev/null`; the no-`set -e`
script still exited 0 -> Job "Succeeded").
Fix (baked, rebuild log-archiver): replace the single `dd` with the proven S1 fio recipe rooted at log-archiver —
`fio --rw=write --bs=1M --numjobs=$S2_JOBS(4) --fsync=$S2_FSYNC(2) --direct=1 --ioengine=libaio --time_based
--runtime=$S2_RUNTIME(120) --unlink=1`, per-job size = S2_SEED_MB/JOBS (TOTAL footprint bounded < the 5Gi PVC).
O_DIRECT keeps it OOM-safe (preserves LOG-087). Dockerfile: `apk add --no-cache fio` (fallback `--ioengine=psync`
if the alpine fio build lacks libaio). values.yaml: S2_SEED_MB 6144->2048 (footprint, not duration — duration is
now S2_RUNTIME). Storm character/duration env-tunable, no rebuild (mirrors the cooling-monitor knob pattern).
Impact / apply on box: rebuild `skn/log-archiver:v0.1` + `sudo k3s ctr images import` (the suspended CronJob
picks up the new image on the next `create job --from`; no rollout needed) + `deploy/skctl up` (applies the
S2_SEED_MB values change to the CronJob). Re-verify: `bash scenarios/S2/trigger.sh`, read `/graph` during the
storm -> expect root=log-archiver, edge `log-archiver->timescaledb` `[write,pvc,temporal]`, victim=timescaledb;
**confirm timescaledb psi_io actually stalls in Grafana** (the fio recipe's whole point); self-clears ~2-3 min
after via the recency gate. `run_pass` untouched (this is a workload script, not engine code — fixtures unaffected).
Side note (box health): btop showed swap 100% full (3.99Gi) + mem 69% during the run — not the S2 cause (the
engine answered cleanly every 15s) but a standing watch-item.
Links: LOG-090 (gap #1 timing — superseded as the sole cause; the deeper cause is storm character), LOG-087
(oflag=direct OOM fix, preserved), LOG-074 (real-victim rule — why no-victim => no-root is correct), LOG-051
(FSYNC=2 = writer+victim stall), D-014 (slow HDD); workloads/log-archiver/{Dockerfile,archive.sh},
deploy/charts/factory/values.yaml, scenarios/S2/runbook.md.

## LOG-092 · 2026-06-22 · STEP (mark-one polish: P5 narrator + P6 scenario console) — operator pulled these into the submission branch
What: Operator decision — mark-one needs a minimum polish level, so these P5/P6 "required" items land on the
submission branch (not deferred to mark-two): (1) **Scenario console S2/S5 + reset** — `/api/scenarios/{sid}/trigger`
extended beyond S1; new `/api/scenarios/{sid}/reset`. S2 clones the suspended `log-archiver` CronJob into the
fixed-name Job `log-archiver-s2` (faithful to scenarios/S2/trigger.sh; name fixed so workload() -> `log-archiver`,
LOG-075); S5 strategic-merge-patches `vision-qc` env `LEAK_ENABLED` true/false. Both via a **minimal in-cluster
k8s call** (`_k8s`, SA token + ca.crt over urllib+ssl — no client lib, no new deps) under a **bounded ServiceAccount**:
new `api` SA + per-namespace Roles in api.yaml (factory-data: jobs get/create/delete + cronjobs get; factory-edge:
deployments get/patch). Dashboard: `scenario(sid, action)` with S1/S2/S5 fire + S2/S5 reset buttons. (2) **forecast-in-
narrative** — the OOM `incipient` line now appends to the INCIDENT verdict too (was no-root path only); deterministic,
model-free, computed each call so the ETA stays current under the verdict cache (cache stores base text). (3)
**keep_alive "10m"** in the `_ollama` request → model stays warm through an incident (warm-on-anomaly is then just the
5s narrative poll loading it on the first finding; pre-warm once before the demo for the very first render).
DROPPED from scope: **io_read source signal** — the LOG-091 S2 fix is now an fio WRITE storm, so `io_write` already
attributes log-archiver as source; io_read would be an engine change (run_pass/fixtures risk) for no gain. Revisit on
mark-two only if a pure read-starvation scenario is added.
Impact / apply on box: rebuild `skn/api:v0.1` + `skn/dashboard:v0.1` + `k3s ctr images import` (this is the LOG-091
log-archiver rebuild's sibling — do all three at once); `kubectl apply -f deploy/api.yaml` (creates SA+Roles+Bindings,
restarts api on the new SA) — or `deploy/skctl up` (it applies api.yaml + dashboard.yaml); `kubectl rollout restart
deploy/dashboard -n aiops` if the image tag is unchanged. Verify: console buttons fire S1/S2/S5 + reset; S5 narrative
shows the OOM line DURING an S1/S2 storm; narrator warm (<30s) after the first render. `run_pass` untouched (api/dashboard
only). py_compile clean (laptop).
Links: LOG-091 (S2 fio fix — io_write makes io_read moot), LOG-075 (fixed Job name -> workload), ROAD Stage 3 (A5
bounded K8s tools — this SA is the groundwork) + Stage 6 (scenario console), §1.6 (six panels); api/main.py,
deploy/api.yaml, dashboard/app/page.jsx.

## LOG-093 · 2026-06-22 · NOTE — box-verify of the full set (S0/S1/S5 good; S2 clean-root is physics+baseline gated -> mark-two); env tunes; ABB submission cut
What: Box session after applying LOG-091/092. Results + one hard finding.
 - **S1 — FIXED via env (no rebuild).** Root was flipping cooling-monitor -> **dcim-bridge** mid-run: the storm was
   only 60s (FIO_RUNTIME=60) so it ended before the read window, and cooling-monitor (O_DIRECT) self-stalls weakly
   (~0.018) while dcim-bridge's loud fdatasync baseline (~0.04, victim spike to ~0.068) out-ranked it once the source
   stopped writing (the lingering edge was `[stat,pvc]`, NO `write`). Fix: `kubectl set env deploy/cooling-monitor
   FIO_RUNTIME=120 FIO_FSYNC=1 FIO_JOBS=6` -> cooling-monitor stays the live write-source across the whole window ->
   roots correctly, evidence `[stat,pvc,write,temporal]`, gemma4 prose correct. Onset ~90s was partly a TEST ARTIFACT:
   triggering right after the env rollout meant ~60s of sample warm-up (build_inputs needs >=12 samples); on settled
   pods S1 lights up ~45-50s. Optional faster onset: DEV_K 4->3.5.
 - **S5 — tuned.** `FORECAST_MIN_FRAC 0.6->0.5` -> the OOM card fires earlier (eta ~9.5s at 85% of limit, was 0.6s at
   99%). Still brief (a ~6MB/s leak crosses the gate fast, then OOM resets working_set) but a valid pre-kill warning.
   Do NOT go below 0.5 (re-admits the cooling-monitor(0.43)/safety-interlock(0.24) false cards LOG-087 killed).
 - **S2 — clean root NOT achieved; deferred to mark-two (physics + baseline, NOT a bug).** fio image confirmed live
   (`which fio`; archive.sh has rw=write). log-archiver writes **73-119 MB/s** (io_write dominant, ~40x everyone) — the
   source signal is unambiguous. BUT it never roots, because: (a) it **self-stalls ~0 (psi 0.007)** — O_DIRECT+libaio is
   async bandwidth, the submitter never blocks; (b) its **psi baseline never matures** (on-demand CronJob ->
   `baseline_threshold`=None -> run_pass skips it -> it can NEVER be a finding -> no `+1.0` self-explanation bonus in
   ranking, the path S1 uses); (c) **no victim stalls enough**: timescaledb=0 (LOG-088 checkpoint relax made it do
   almost no disk I/O -> not a stallable victim), dcim only 0.067 (marginal vs DEV_K=4). Best result: log-archiver
   reached 0.325 (#2), out-ranked by cooling-monitor's held backbone (0.675). **Disk confirmed spinning HDD**
   (`/sys/block/sdb/queue/rotational`=1) — so it is NOT disk speed; it is the S0-silence/S2-victim tension (the LOG-088
   quieting that made S0 silent also removed timescaledb as a victim) + the CronJob baseline gap. Same family as the S3
   physics block (LOG-076). **mark-two fix:** make log-archiver SELF-stall via synchronous fio (`--ioengine=psync
   --iodepth=1`) so it's a finding directly, + a baseline-gate tweak so a no-baseline CronJob with a strong onset can
   still be a finding; OR re-aggravate timescaledb I/O (more ingest / tighter checkpoint), which re-risks S0. For the
   demo, S1 is the disk-causality flagship; S2's honest beat is the engine's restraint (dominant writer, no stalling
   victim -> no false root = the threshold-free discipline).
 - **Env-tune persistence WARNING:** the S1/S5 fixes above are LIVE `kubectl set env` only. `deploy/skctl up` / helm
   upgrade RESET deploy env to chart values and WIPE them. To persist: bake `FIO_RUNTIME=120/FIO_FSYNC=1/FIO_JOBS=6`
   into cooling-monitor's env in `values.yaml`, and `FORECAST_MIN_FRAC=0.5` into the engine env in `deploy/engine.yaml`.
 - **hot-edge curl quirk (cosmetic):** `state!="steady"` is the wrong "hot" filter — a live incident edge often renders
   via the held backbone (`render_weight`~1.0, state steady). The dashboard colors by `render_weight`, so the 3D graph
   shows hot edges correctly; use `render_weight>0.4` for CLI checks. No code change.
 - **ABB submission cut.** Pushed a curated copy to a NEW repo (`GreaseMonkeyIT/ABB_Accelerator_Submission`) via an
   ORPHAN branch (fresh single-commit history -> the leaky 8-commit history + internal docs do not follow) + a
   `.gitignore` that excludes `BUILD_LOG/BUILD_GUIDE/ROAD_TO_COMPLETION/P0_DESKTOP_SETUP/RULES/archive/agents/` + scratch.
   This repo (codex, mark-one) keeps everything — it is the internal master.
Why: complete the box record; pin S2 as a mark-two physics/baseline item (not a regression) so it is not re-chased;
flag that the live env tunes must be baked or a redeploy loses them.
Links: LOG-091 (S2 fio), LOG-092 (console), LOG-088 (timescaledb quieting — the S2-victim tension), LOG-087
(FORECAST_MIN_FRAC + false cards), LOG-076 (S3 physics block — same family), LOG-074 (real-victim rule), D-014 (HDD);
deploy/charts/factory/values.yaml (cooling-monitor env to bake), deploy/engine.yaml (FORECAST_MIN_FRAC to bake).

## LOG-094 · 2026-06-22 · STEP (bake the LOG-093 S1/S5 tunes as code defaults) — survive skctl up/helm without env
What: Baked the box-verified LOG-093 env tunes into the image defaults + the committed manifests so a redeploy can
no longer wipe them (LOG-093 warned `skctl up`/helm RESET deploy env to chart values). Operator chose code defaults
over values-only.
 - **cooling-monitor (S1):** `workloads/cooling-monitor/main.py` defaults FIO_JOBS 4->6, FIO_RUNTIME 45->120, FIO_FSYNC
   8->1; `deploy/charts/factory/values.yaml` cooling-monitor env mirrored to the same (6/120/1) so the chart no longer
   overrides the baked defaults with the old 4/60/2. (120s outlasts the read window -> cooling-monitor stays the live
   write-source -> roots correctly; FSYNC=1 = writer+victim both stall; JOBS=6 louder.)
 - **engine forecast (S5):** `correlation/service.py` FORECAST_MIN_FRAC default 0.6->0.5; `deploy/engine.yaml` env
   mirrored to 0.5 (earlier OOM card; do NOT go below 0.5 -> re-admits the LOG-087 false cards). forecast.py
   `DEFAULT_MIN_FRAC` (the pure-function/library default the tests pin) left at 0.6 — untouched, run_pass + 47/47 intact.
 - **DEV_K** already 3.5 in engine.yaml (the LOG-093 "optional faster onset" — no change needed).
 - Refreshed `scenarios/S1/runbook.md` (4x60s/fsync=2 -> 6x120s/fsync=1; notes the bake; supersedes the LOG-054
   "duration not load-bearing" note that LOG-093 disproved on settled pods).
Impact / apply on box: baked-code change -> rebuild `skn/cooling-monitor:v0.1` + `skn/correlation-engine:v0.1` + `sudo
k3s ctr images import -`; `deploy/skctl up` (applies the mirrored values.yaml) + `kubectl apply -f deploy/engine.yaml`
+ `kubectl rollout restart deploy/cooling-monitor -n factory-data deploy/correlation-engine -n aiops`. Then S1 should
root cooling-monitor on a FRESH deploy with NO `kubectl set env`, and the S5 card fires at ~85% of the limit. `run_pass`
untouched; py_compile clean expected.
Why: the LOG-093 fixes were live `kubectl set env` only -> a single redeploy before the demo would silently break S1/S5.
Links: LOG-093 (the tunes + the wipe warning), LOG-091 (S2 fio), LOG-051 (FSYNC writer+victim stall), LOG-054
(duration-not-load-bearing — superseded for settled-pod timing), LOG-087 (MIN_FRAC false cards); workloads/cooling-monitor/main.py,
correlation/service.py, deploy/charts/factory/values.yaml, deploy/engine.yaml, scenarios/S1/runbook.md.

## LOG-095 · 2026-06-22 · STEP (submission docs polish: README honesty + demo runbook + fresh-clone build fix)
What: Pre-submission pass on the public-facing docs (operator's 4-item list) so the repo a judge reads/clones is
honest and runnable.
 - **README honesty pass:** L1 telemetry no longer claims OBI (dropped, LOG-078) or a working Loki (partial) — now
   PSI / kube-state / node-exporter / Caretta + "logs partial"; L4 "PSI heatmap" -> the actual panel set (the full
   heatmap is mark-two); S1 expected evidence gains the `write` token (io_write source attribution, was undersold);
   Scenarios section gains a "live today = S0/S1/S5; S2 = engine restraint; S3/S4 out of scope" note. Clone URL
   Proto -> Submission (also done earlier this turn).
 - **DEMO_RUNBOOK.md (new):** press-this/say-this for S0->S1->S5 + honest answers to the four judge Qs (Q3-disk +
   Q4 live; Q1/Q2 engine-ready/future) + fallbacks. Linked from the README. Closes the LOG-089 demo-runbook gap.
 - **Fresh-clone build fix (Makefile):** `make images`/`make import` now also build + import `skn/api` and
   `skn/dashboard` (both have self-contained Dockerfiles) — previously `make import` + `skctl up` left api/dashboard
   in ImagePullBackOff on a clean clone (skctl applies api.yaml + dashboard.yaml). README `make test (13/13)` ->
   `(47/47)` (the target runs the whole suite).
Impact / apply: docs + Makefile only — NO image rebuild, NO box change; affects the next clean `make import`. Lands
in the same pre-submission commit as LOG-093/094 and feeds the Submission re-cut.
Open (operator call): Ollama/gemma4 install is not in the README (the narrator has a deterministic fallback, so a
clone still runs) — add a one-line optional setup note if you want the prose live out-of-the-box. Deck
(SiliconKnights_Final.*) NOT reviewed (Submission folder, off-limits) — offer: read-only overclaim scan on request.
Links: LOG-089 (demo-runbook gap), LOG-078 (OBI dropped), LOG-093 (S1/S5 verified — what the runbook demos), ROAD
Stage 6 + docs workstream; README.md, DEMO_RUNBOOK.md, Makefile.
