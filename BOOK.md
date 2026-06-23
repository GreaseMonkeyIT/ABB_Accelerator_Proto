# THE BOOK — SiliconKnights Edge Causal AIOps

*A complete, plain-language reference to the system we built for ABB Accelerator 2026,
Theme 2: "Beyond monitoring — AI agents for real-time pod resource discovery and dependency
mapping."*

**Team:** Soumyadip Das · Shivam Kumar · B Kishan · Aaryan Shyam Pillai

---

## How to read this book

This is the one document you can hand to anyone on the team — or to yourself six months from
now — and walk away understanding the whole system: what it does, *why* it works, how to run it,
and what is honestly finished versus still on the wishlist.

It assumes **no Kubernetes or systems background**. Whenever a new technical idea shows up for the
first time, there's a short plain-English explanation right there. If you already know the basics,
skim **Part 0** and start at **Part 1**.

The book is organised as a staircase — each part stands on the one before it:

- **Part 0 — The Primer.** Every concept you need, explained from scratch (containers, pods,
  Kubernetes, CPU/memory/disk, PSI, eBPF, "causal"). Read this once and the rest reads easily.
- **Part 1 — The Problem & Our Answer.** What we were asked to build and the one idea that makes
  our solution different.
- **Part 2 — The Architecture.** The five layers (L0→L4), each as its own chapter.
- **Part 3 — How the Detective Thinks.** The reasoning engine in detail, still in plain language.
- **Part 4 — Walkthroughs.** Trace a real incident end-to-end; the six scenarios; the four judge
  questions answered honestly.
- **Part 5 — Running It.** Prerequisites, build, deploy, verify, tune, troubleshoot.
- **Part 6 — The Honest Record.** What's built, what's roadmap, the known gaps in detail, and the
  history of every major decision.
- **Appendices.** Glossary, file map, API reference, query cheat sheet.

> **A note on honesty.** This is an *internal* reference, so it tells the truth, including the
> parts that are unfinished or imperfect. Three of the six scenarios are fully demonstrable; one
> needs more tuning; two are out of scope on our hardware. We say exactly why in **Part 6**. The
> public-facing version of these claims (the submission repository) is phrased more softly — that's
> deliberate and appropriate — but inside the team we keep it blunt.

### The companion documents (and where this book sits among them)

This book *consolidates* a family of working documents. When you need the raw, append-only detail,
go to the source:

| Document | What it is | When to open it |
|---|---|---|
| **THE BOOK** (this) | The complete, readable, plain-language reference | First. To understand anything. |
| `MASTER_PLAN.md` | The original architecture spec & competitive analysis | The "why we chose X" deep dive |
| `EXPLANATIONS.md` | The code map — file by file | When editing a specific file |
| `BUILD_LOG.md` | Append-only journal; 102 dated entries + decision register | "When/why did we change X?" |
| `BUILD_GUIDE.md` | The phase-by-phase build path (P0→P8) | Rebuilding from scratch |
| `ROAD_TO_COMPLETION.md` | The forward plan — what's left, stage by stage | Planning the next work |
| `DESIGN_stateful_engine_and_case_library.md` | The engine's memory design | Working on the case library |
| `QUICKSTART.md` / `DEMO_RUNBOOK.md` | Clone-to-running / press-this-say-this | Setting up / demoing |

---

# PART 0 — THE PRIMER (everything from scratch)

You can't understand a tool that watches Kubernetes pods without knowing what those words mean.
This part builds the vocabulary. It's short on purpose — just enough to make the rest click.

## 0.1 Containers, images, and pods

A **container** is a way to package a program together with everything it needs to run (its code,
its libraries, its settings) into one sealed box, so it runs the same way on any machine. Think of
it as a shipping container: the contents are standardised, and the ship (the computer) doesn't care
what's inside.

A container is started from an **image** — a frozen snapshot of that sealed box, like a template.
You build an image once, then start many identical containers from it.

A **pod** is Kubernetes' name for "one or more containers that run together as a unit." In our
system, almost every pod is just one container, so for most of this book you can read "pod" and
"the running program" as the same thing.

> **Our system watches 15 pods** that together pretend to be a small factory (Part 2, L0).

## 0.2 Kubernetes, K3s, nodes, and namespaces

**Kubernetes** (often written "K8s") is the software that runs and babysits containers at scale: it
starts them, restarts them if they crash, gives them network addresses, and shares the machine's
resources between them. It's the "operating system for containers."

**K3s** is a lightweight version of Kubernetes — same ideas, much smaller, designed to run on a
single small machine (an "edge box" on a factory floor, exactly the scenario ABB cares about). We
use K3s.

A **node** is one physical (or virtual) machine that Kubernetes runs on. Our whole system runs on
**one node** — a single desktop computer. This is the deliberately hard case: when everything
shares one machine's CPU, memory, and disk, the pods interfere with each other in ways that are
invisible to most tools. Catching that interference is our entire thesis.

A **namespace** is just a folder for organising pods. We use a few:
- `factory-core`, `factory-data`, `factory-edge` — the 15 factory pods we *watch*.
- `aiops` — our own tool (the aggregator, the engine, the API, the dashboard).
- `observability` — the telemetry collectors (Prometheus, etc.).

## 0.3 The four resources every pod competes for

Every pod needs four things from the machine, and they're all finite:

1. **CPU** — processing power (how fast the program can compute).
2. **Memory (RAM)** — fast working space (how much the program can hold at once).
3. **Disk** — slow permanent storage (where data is saved so it survives a restart).
4. **Network** — talking to other pods or the outside world.

When many pods share one node, they fight over these four. That fight is what we detect.

**A "limit"** is a cap Kubernetes puts on a pod ("you may use at most 512 MB of memory"). Hit the
memory limit and the pod gets killed (an **OOM kill** — "Out Of Memory"). Hit the CPU limit and the
pod gets **throttled** (slowed down on purpose). These caps are how one greedy pod is *supposed* to
be contained — but, as we'll see, the disk has no such cap, which is where the interesting failures
live.

## 0.4 PVC — shared storage, and the hidden trap

A **PVC** ("Persistent Volume Claim") is a pod's request for a chunk of disk that survives even if
the pod restarts. Think of it as a labelled hard-drive partition handed to a pod.

Here's the trap that powers our hero demo: **two different PVCs can physically live on the same
disk.** Pod A writes hard to its PVC; pod B, with a *completely separate* PVC and *no network
connection* to A, suddenly slows down — because the one physical disk underneath both is saturated.
To almost every monitoring tool, A and B look unrelated. They share nothing visible. But they're
strangling each other through the disk. We catch exactly this.

## 0.5 Metrics, time-series, and Prometheus

A **metric** is a number a program reports about itself or its environment — "CPU usage = 40%,"
"memory = 300 MB." Measured repeatedly over time, a metric becomes a **time-series**: a list of
(timestamp, value) pairs you can plot as a line.

**Prometheus** is the standard tool that goes around every few seconds, collects all these numbers
from every pod, and stores them. It's the "scraper." We don't reinvent it; we use it as our raw
data source. (We collect a new sample every **5 seconds** for the factory pods — fast enough to see
a cascade unfold.)

The key thing Prometheus reads comes from the **kubelet** (the Kubernetes agent on each node) via a
built-in component called **cAdvisor**, which already knows each container's CPU, memory, and — the
star of the show — its PSI.

## 0.6 PSI — the secret weapon (busy vs. suffering)

This is the single most important idea in the whole system, so it gets its own section.

Ordinary metrics tell you a pod is **busy**: "CPU is at 90%." But busy isn't bad — a healthy pod
doing real work *should* be busy. What you actually want to know is whether a pod is **suffering**:
stuck *waiting* for a resource it can't get.

**PSI** ("Pressure Stall Information") is a number the Linux kernel itself keeps for every
container: *the fraction of time the pod spent stalled, waiting* for CPU, for memory, or for I/O
(disk). The kernel measures three PSI values per pod — `psi_cpu`, `psi_mem`, `psi_io`.

The difference is everything:

- **Utilization** ("busy") says: *this pod is using the disk a lot.* That might be totally fine.
- **PSI** ("suffering") says: *this pod is stuck waiting for the disk it can't get.* That is a
  victim.

PSI is how we can claim — with kernel-level proof — that one pod is being *hurt* by another, even
when the two never exchange a single network packet. No service-mesh or network-tracing tool can do
that, because there's no network conversation to observe. The harm travels through shared hardware,
and PSI is the only witness.

> **Plain version:** CPU usage tells you who's *working hard*. PSI tells you who's *struggling*.
> Our tool is built around finding who's struggling and tracing it back to who's causing it.

## 0.7 eBPF — watching from inside the kernel, changing nothing

**eBPF** is a modern Linux feature that lets approved programs safely run *inside the kernel* to
observe what's happening — for example, "which pod just opened a network connection to which other
pod." It does this without modifying or even touching the applications being watched.

We use an eBPF tool called **Caretta** to automatically discover the "who-talks-to-whom" map of the
factory: which pods send messages to which others. This becomes the faint background skeleton of our
dashboard graph — drawn with *zero configuration*, just by watching the kernel.

The phrase you'll hear is **"zero instrumentation"**: we never edit, recompile, or inject anything
into the factory apps. Everything we know, we learned from the outside — from the kernel, via the
kubelet and eBPF. That keeps the tool honest (it has to *discover* the story, not be told it) and
means it would work on software you can't modify.

## 0.8 What "causal" means here, and why it's hard

**Correlation** is "these two things moved together." **Causation** is "this one *made* that one
move." The famous warning is *correlation ≠ causation* — two things can rise together by
coincidence, or because a third thing drives both.

A monitoring dashboard shows you twelve lines wiggling. *You*, the human, squint and guess which
caused which. Our tool's job is to do that guessing **automatically and defensibly** — to draw an
arrow "cooling-monitor → timescaledb" and be able to justify it.

How do we avoid the *correlation ≠ causation* trap? Every causal arrow we draw must pass **three
independent tests** (detailed in Part 3):

1. **Statistics** — the two genuinely move together, strongly.
2. **A physical witness** — there's a real shared thing (a shared disk, or an observed network
   link) through which the influence *could* travel. Coincidence across unrelated pods is rejected.
3. **Time order** — the cause's trouble started *before* the victim's. Effects don't precede
   causes.

Only when all three agree do we draw the arrow. That triple gate is our answer to any judge who
says "but correlation isn't causation."

## 0.9 The one-LLM rule

An **LLM** ("Large Language Model") is an AI like the one writing this — good at producing fluent
human language, but prone to making things up ("hallucinating").

A trendy way to build an "AI agent" is to throw all your data at an LLM and ask it to figure
everything out. We deliberately **do not** do that, because an LLM that *invents* causality is
worse than useless in an industrial control room.

Instead:

- **All the reasoning is done by deterministic math** — statistics and graph algorithms that give
  the *same answer every time* from the same data. No AI in the reasoning loop.
- **Exactly one LLM exists in the whole system,** and it sits right at the very end. Its only job is
  to translate the finished verdict into a readable English sentence. It **narrates**; it never
  decides. If it's slow or broken, a plain template writes the sentence instead and nothing else
  changes.

This is the line we repeat: *"Our LLM is not the detective. It's the spokesperson for a
deterministic detective."*

> **When people say "multi-agent AI," they imagine many LLMs.** Ours are *inference engines* — a
> changepoint detector, a correlation analyser, an evidence gate, a ranker, a forecaster. Each is an
> "agent" in the real sense (an autonomous component with an input contract, a decision policy, and a
> structured output) — just built from math, not language models. That choice (decision **D-002**)
> is why the system is fast, reproducible, and trustworthy.

---

# PART 1 — THE PROBLEM & OUR ANSWER

## 1.1 What ABB asked for

The challenge (Theme 2) is, in plain terms: *modern container platforms give you a flood of raw
numbers, but no understanding.* A single edge box can run hundreds of pods, all sharing CPU, memory,
disk, and network. When something slows down, engineers are left correlating metrics by hand. The
brief names four questions operators struggle to answer:

1. **Which pod is causing unexpected CPU spikes?**
2. **How are PVC I/O patterns linked to pod restarts?**
3. **Are different services influencing each other's resource consumption?**
4. **Which workloads need optimization?**

And it asks for a real, running prototype on a lightweight Kubernetes platform, with multi-agent AI
analysis, dependency mapping, a live dashboard, intelligent recommendations, and a technical report.

## 1.2 Why the existing tools don't close it

- **Prometheus + Grafana** (what most people have): stores and charts the numbers. Correlation is
  "a human squinting at twelve panels." No causality, no dependency map.
- **Datadog / Dynatrace / New Relic** (cloud APM): expensive per box, and they *phone home* — an
  instant disqualification for an air-gapped industrial floor. They correlate *alerts*, not raw
  multi-resource behavior, and their disk/storage causality is weak.
- **Service meshes (Istio/Linkerd + Kiali):** see only what crosses the network. The whole class of
  failures where pods strangle each other through a *shared disk* with **no network link** is
  literally invisible to them.
- **Pixie** (eBPF APM): explicitly does **not** support K3s, and needs 1–2 GB of RAM per node.
- **Causely** (the closest in spirit — genuine causal AIOps): a closed cloud service that *cannot
  run air-gapped*, and its causal model is pre-built rather than learned from your live system.

No existing tool covers all of: **edge/single-node + causal root cause + storage-aware + local AI +
offline.** That intersection is our defensible ground.

## 1.3 Our answer in one breath

> A single Kubernetes node runs many pods sharing one CPU, memory, and disk. When something slows
> down, ordinary tools show you *what* is hot — never *who made it hot* or *who it will hurt next*.
> We watch the cluster from the outside, change nothing inside the applications, and turn raw kernel
> signals into a causal story: *"this pod's disk storm is starving that pod, which is why a third pod
> misses its deadline."* The reasoning is deterministic math. Exactly one language model exists in
> the whole system, and it only writes the final sentence, citing evidence the math already found.

The contrast that *is* the whole pitch: **it fires when something is truly wrong, and stays silent
when nothing is** — even when a pod is using a lot of memory but not suffering. We alert on
*causality*, not on thresholds.

## 1.4 Where we stand apart — anomaly vs. causality, real vs. scripted

It helps to be precise about *what class of system* this is, because the obvious-looking peers (and
the other entries in the same competition) are usually a different, easier class underneath. Two
distinctions matter, and both are in our favour by design.

**Distinction 1 — anomaly detection vs. causal attribution.** The common pattern is *per-entity
anomaly detection*: score each machine (or pod) on its own, against its own history, and raise a
flag when it looks unusual. That's genuinely useful, and a well-built version of it (a calibrated,
online, per-entity model with honest warm-up) is respectable engineering. **But it can only ever say
*"this one looks abnormal."*** It cannot say *who made it abnormal*, because it never reasons across
entities. When five pods all stall on a saturated disk, an anomaly detector flags all five — and the
loudest flag is usually the *victim* (the database), not the *cause* (the writer). Our engine does
the strictly harder thing: it reasons *across* pods to produce a **directed causal claim** — "*this*
pod's disk storm is starving *that* one" — defended by the three-clause gate (statistics + physical
witness + time order) and oriented by source attribution (writer → staller). Anomaly detection is a
*detector*; ours is a *detective*. Dependency mapping — a core requirement of the brief — falls out
of that reasoning for free, and is something a per-entity anomaly tool structurally cannot produce.

**Distinction 2 — real faults vs. scripted faults.** The other common shortcut is a *simulator that
scripts the fault*: a data generator decides "machine 7 is now degrading," grows the number on a
curve, labels it, and the detector "catches" the thing the generator already announced. That demos
beautifully and proves very little — the tool is grading a test it wrote. **Our faults are real
kernel physics.** A real `fio` process really saturates a real disk; the real Linux kernel really
makes the neighbours wait; the real OOM-killer really fires. Nothing is labelled or injected as a
number. The tool has to *discover* the story blind, from kernel signals it didn't author. That is
the difference between a demonstration and a measurement — and it's the only kind of evidence that
survives a sceptical "but did you just script that?"

> **The honest trade-off — and why we own it rather than fix it.** Real data is *harder to run and
> harder to demo than scripted data, by its nature* — and we accept that deliberately. A scripted
> simulator starts in seconds on any laptop and replays an identical, flawless incident on command.
> Ours needs a real Linux kernel with PSI, a slow disk for honest contention, and a ~15–20 minute
> warm-up while the engine *learns each pod's normal* — and on real physics, some faults (S2's
> invisible CronJob, S3's CPU contention our box can't force) genuinely don't reproduce cleanly. We
> **cannot** make this as turnkey as a scripted demo "come what may," because the moment we could,
> we'd no longer be using real data. The friction is the *receipt* for the credibility: easy-to-run
> and proven-on-real-physics are in tension, and for an industrial-reliability claim we choose
> proven. The right answer to "it's harder to run" is not to weaken the evidence — it's to say so
> plainly and let the result speak.

So the one-sentence positioning against an anomaly-only, scripted-data peer: **they detect that a
machine looks odd in a world they scripted; we prove which pod is causing another's failure in a
world we only observe.** Same surface (industrial, MQTT, a dashboard, an AI assistant), different
class of problem solved.

> **The one capability they have that we don't — and how we answer it without rebuilding — is the
> "what to do next" action loop (see Part 6.5).** Their dispatch-a-technician workflow is a real
> strength. Our answer is not to copy a human-routing UI, but to close the loop the
> Kubernetes-native, causal way: a fine-tuned narrator that turns the verdict into a *bounded
> remedy intent*, dispatched to purpose-built **remedy agents**. That's roadmap, deliberately — but
> it's the principled version of the same idea, and it's only *possible* because we know the cause,
> not just the symptom.

---

# PART 2 — THE ARCHITECTURE (L0 → L4)

The system is five layers stacked on top of each other. Data flows up: the bottom layer *produces*
behavior, the next *collects* it, the middle *interprets* it, the top *presents* it. Each layer only
talks to its neighbours through a small, stable, agreed-upon data shape — so any one layer can be
rebuilt without breaking the others.

```
 L0  factory (15 pods)        the system we WATCH — produces REAL faults (disk storms, OOM, throttle)
  │
 L1  telemetry               Prometheus scrapes the kernel every 5s: PSI, CPU, memory, eBPF links
  │
 L2  aggregator (Go)         turns the flood of raw metrics into clean, typed JSON events
  │
 L3  correlation engine (Py) the DETECTIVE: detect → correlate → gate → rank → forecast  ⇒ a causal graph
  │
 L4  narrator + dashboard    one local AI writes the verdict; the screen shows the graph + buttons
```

Generation → collection → **interpretation** → presentation. The middle layer (L3) is where the
intelligence lives; everything else feeds it or shows its output.

The rest of Part 2 is one chapter per layer.

---

## 2.1 L0 — The Factory (the system we watch)

**What it is.** A pretend "smart factory" made of **15 pods** across three namespaces. It looks like
a real industrial edge deployment: sensors stream data over a message bus into a database; a cooling
system journals logs; analytics and a vision-inspection model crunch data; a critical control relay
actuates machinery on a tight deadline; alerts page operators.

**Why we built our own factory.** We need a system that *breaks in realistic, controllable ways* on
demand, so we can prove our tool catches each kind of failure. Building it ourselves means every
demo run is identical and every fault is one we understand completely.

**The honesty rule (the most important thing about L0):** **every fault is a real kernel mechanism,
never a faked number.** When we trigger a "disk storm," a real program (`fio`) really hammers a real
disk, and the real Linux kernel really makes the neighbours wait. We never inject a fake "PSI = 0.9"
value. If we faked the numbers, we'd only be testing our own assumptions — by producing the real
physics, the tool has to genuinely *discover* the story. This is what makes any accuracy claim we
make believable.

### The 15 pods (the cast)

Grouped by what they do in the story:

**The spine (factory-core + factory-data) — the steady heartbeat:**
- **`plc-gateway`** — pretends to be 200 factory sensors, publishing readings over the message bus.
  Its publish rate is also the database's write-load dial. (We deliberately turned this *down* so the
  database normally idles with headroom — that's what lets it be a *clean victim* when a storm hits,
  rather than something that's always struggling.)
- **`mqtt-broker`** — the message bus (Mosquitto). Every sensor reading passes through it.
- **`telemetry-ingest`** — drains messages off the bus and saves them into the database in batches.
  When the database slows down, its internal queue grows — a visible sign of back-pressure.
- **`timescaledb`** — the time-series database. Stores all the sensor readings on its own PVC. It's
  the **classic victim**: when the shared disk is saturated, *its* writes stall first.
- **`critical-control-relay` (CCR)** — the latency-sensitive actuator with a 100-millisecond
  deadline. The pod every cascade eventually hurts — the "so what" at the end of the chain.
- **`safety-interlock`** — trips to safe-mode if the control relay's heartbeat misses. The unmissable
  end-state of a cascade.

**The storage trio — the hidden coupling (this is where S1 lives):**
- **`cooling-monitor`** — normally writes a light thermal journal. On trigger, it unleashes a
  sustained, fsync-heavy disk storm. **This is the source of the S1 incident.**
- **`dcim-bridge`** — writes small steady snapshots to the *same shared disk volume*. First in line
  to feel contention.
- **`log-archiver`** — a scheduled job that compresses logs (the S2 trigger). Off until fired.

The crucial geometry: `cooling-monitor`, `dcim-bridge`, and `log-archiver` all write to the **same
shared volume** (`shared-logs-pvc`), and `timescaledb` writes to its *own* volume (`tsdb-pvc`) — but
**both volumes live on the same physical disk.** So when cooling-monitor storms, the contention
crosses the volume boundary and hurts the database, with no network link between them. That's the
invisible-to-everyone-else interference we're built to catch.

**The pathology carriers (factory-data + factory-edge):**
- **`analytics-batch`** — a scheduled CPU-heavy job; demands ~2 cores under a tight limit, forcing
  CPU throttling (the S3 trigger). Off until fired.
- **`vision-qc`** — "defect detection." With a leak flag on, it grows memory until it hits its limit
  and the kernel kills it (the S5 trigger).

**The bystanders (factory-edge) — mostly steady ballast, and the credibility check:**
- **`alert-dispatcher`** → **`notify-gateway`** — the alerting chain (the S4 path: a slow gateway
  causes the dispatcher to retry, amplifying load).
- **`edge-ui`** — operator kiosk. The **control pod that must stay green** — if our tool ever blames
  it, that's a false positive.
- **`firmware-cache`** — serves firmware from memory. The **"innocent high-RAM pod"**: it uses a lot
  of memory but isn't *suffering*. If our tool alerts on it just because its memory is high, we've
  failed the "usage ≠ pressure" test. It staying silent is a feature.

### The three planes (a useful mental model)

The factory is designed as three overlaid maps:
- **Plane 1 — Data flow:** who sends messages to whom (sensors → bus → database; commands → relay).
- **Plane 2 — Storage:** who shares which disk volume (the hidden coupling — the storage trio and the
  database, two volumes on one disk).
- **Plane 3 — Observation:** the kernel/eBPF taps where we pick up every metric.

The rule that keeps the whole thing honest: **planes 1 and 2 are what we built; plane 3 must
rediscover them blind.** Caretta's eBPF map should redraw plane 1 within minutes of install. S1
should redraw plane 2's hidden disk coupling as a causal arrow. If either fails, our discovery claim
fails.

---

## 2.2 L1 — Telemetry (watching from outside)

**What it is.** The collection layer. **No application is instrumented** — everything is read from
the kernel via the kubelet.

- **Prometheus** scrapes the kubelet's cAdvisor endpoint **every 5 seconds** for the factory pods,
  pulling per-container CPU, memory, throttling counters, and — the differentiator — **PSI** (cpu,
  mem, io). It also pulls kube-state-metrics (pod restarts, OOM reasons, which PVC belongs to which
  pod) and node-exporter (node-level disk and network).
- **Caretta** is the eBPF tool that discovers the network service map (`caretta_links_observed`) —
  who talks to whom over MQTT, SQL, HTTP. This feeds the faint backbone of the dashboard graph and
  the `/api/topology` endpoint.
- **Loki + Grafana Alloy** (the log pipeline) is only **partially** working — Alloy has a tendency to
  crash-loop on our setup. Logs are not a load-bearing part of the demo today; the log-analysis
  agent that would consume them is roadmap (Part 6).

**A note on zero-instrumentation honesty.** The factory apps *do* expose their own metrics (the
control relay's true latency, the ingest queue depth), but our engine is **forbidden from looking at
them** (decision **D-004**). They exist only as a separate "ground-truth" channel we could use to
*score* our detection accuracy — to check whether the tool, working blind from kernel signals,
rediscovered what the app already knew. The engine must reconstruct the story from the outside.

**Why this matters — the ladder of credibility.** It's worth being precise about *why* we tie our own
hands here, because reading those app metrics would be easier and is tempting. There's a ladder of
how convincing a "we caught the fault" claim actually is:

| Approach | Is the fault real? | What you read | What it proves |
|---|---|---|---|
| **Scripting** (faked) | No — a generator fabricates and *labels* the fault | a number the generator authored | nothing — the tool catches its own homework |
| **Reading app metrics** ("kinda cheating") | **Yes** — real `fio`, real OOM | the app's own symptom readout (latency, queue depth) | detection works — *but only for apps that expose the right metric* |
| **Ours** (kernel-blind) | **Yes** | PSI / cgroup / eBPF the app never emitted | the real product claim *plus* a measured accuracy number |

The middle rung is the interesting one, and it's where your instinct lands: using the apps' own
metrics would **not** be scripting — the physics stays real (a real disk storm, a real stall), you'd
just be reading a cleaner, more direct signal. So it *is* better than scripting. But it's a quieter
kind of cheating, because those app metrics are the **effect spelled out**: the relay's latency
histogram *literally says* "I'm slow"; the ingest queue depth *literally says* "I'm backing up."
Detection becomes near-trivial — you wouldn't need PSI, the changepoint detector, or most of the
reasoning engine to see it. And it only works if every app is instrumented and cooperative, which is
exactly the assumption a factory-floor edge box breaks. Reading them would buy an easier demo at the
cost of the two things that make this defensible: the **zero-instrumentation generality** (it works
on software you can't touch) and the **measured-accuracy claim** (you can't score yourself against a
signal you're already using). Quarantining the app metrics as ground truth is the harder road that
actually proves something — the same discipline as "real faults, not fake metrics" (Part 1.4), one
rung higher.

**What got dropped and why.** The original plan also wanted OBI/Beyla (for HTTP latency tracing) and
Inspektor Gadget (for per-pod disk attribution). OBI was dropped (**LOG-078**) because the factory
talks MQTT and SQL, not HTTP, so OBI's HTTP-only view had nothing useful to add to the core path.
Inspektor Gadget stays an on-demand tool, not an always-on collector. None of these are needed for
the L0→L3 causal path that actually runs.

---

## 2.3 L2 — The Aggregator (raw numbers → clean events)

**What it is.** A small **Go** service (one pod in `aiops`) that sits between the wall of raw
Prometheus numbers and the brain. Its whole job is to be a **firewall and a translator**: the brain
should never see two thousand raw metric strings — only a few dozen clean, typed events.

**What it does, every interval:**
1. Runs each query in its **query pack** (`queries.yaml`) — one PromQL query per signal: CPU, the
   three PSI signals, **`io_write`** (per-pod disk-write throughput — the source-attribution signal),
   memory, network, PVC usage, restarts, and more.
2. Keeps the **last 15 minutes** of every pod's signals in a ring buffer, served to the engine at
   **`/window`**.
3. Applies simple threshold rules; when a pod crosses a floor, it emits an **`anomaly_candidate`**
   event, served at **`/events`**.

**Two things to understand about L2:**

- **The thresholds are only a hint.** L2's threshold rules ("PSI above 0.15") are a cheap, coarse
  alarm that says "hey, *something* might be happening here." The actual *causal* reasoning in L3 does
  **not** depend on them at all — L3 reaches its verdict from correlation, shared-disk topology, and
  time order, never from "value > limit." This is central to the "threshold-free" claim (Part 3).
- **The event schema is frozen.** The exact shape of an event (`version`, `kind`, `namespace`, `pod`,
  `signal`, `value`, `zscore`, `threshold`, `window`) is locked as a v1 contract
  (`event.schema.json`). Freezing it means L2 and L3 can evolve independently without breaking each
  other — a discipline that makes the whole system maintainable.

There's one subtlety the engine has to handle: the ring buffer appends samples by position, and PSI
data is "gappy" (samples arrive irregularly and pods restart), so samples for different pods can
drift apart in time. The engine re-aligns everything onto one clock before doing any math (see L3).

---

## 2.4 L3 — The Correlation Engine (the detective)

This is the heart of the system, and the next part of the book (Part 3) is devoted to *how it
thinks*. Here we just lay out *what it is* and the pieces it's made of.

**What it is.** A **Python** service (one pod in `aiops`) that takes the 15-minute window of clean
signals from L2 and produces a **causal graph**: a set of nodes (pods), arrows (causal edges, each
backed by evidence), a ranked list of root causes, and a predicted blast radius. It serves this at
**`/graph`**. **There is no LLM anywhere in this layer** — it's all deterministic math.

It's built from five core ideas, each in its own file:

- **`detectors.py`** — *changepoints.* Finds the exact moment each pod's signal "turned bad" and
  names the shape of the trouble (a burst, a leak, a saturation, a flap).
- **`lagcorr.py`** — *who leads whom.* Measures, for any two pods, whether one's trouble consistently
  *precedes* the other's, and by how many seconds.
- **`gate.py`** — *the false-positive killer.* The three-clause test (statistics + physical witness +
  time order) that an arrow must pass to enter the graph.
- **`ranking.py`** — *naming the culprit.* Among all the connected trouble, decides which pod best
  *explains* the whole mess (the root cause), and walks forward to predict who gets hurt next (the
  blast radius).
- **`forecast.py`** — *seeing the OOM coming.* Projects a memory leak forward to its limit and warns
  "OOM in ~N seconds" *before* the kill.

Two more files do the supporting work:

- **`service.py`** — the input/output shell. It fetches the window, re-aligns every pod onto one
  shared clock by timestamp (fixing the drift mentioned in L2), figures out which pods share a disk
  (the "physical witnesses"), runs the analysis once per signal (`psi_io`, `psi_cpu`, `psi_mem`) and
  merges the results into one graph, runs the OOM forecaster, and serves `/graph`.
- **`state.py`** — the engine's **permanent memory** (stored in a small SQLite database on its own
  volume). This is what makes the engine more than a calculator — it remembers what "normal" looks
  like for each pod (so it can tell a real incident from background noise), holds confirmed
  relationships steady so the graph doesn't flicker, and builds a library of *case families* it has
  seen before. Detailed in Part 3.7.

**The pure-function discipline (why this stays correct).** The core reasoning (`run_pass`) is a
**pure function**: same input, same output, no hidden state, no side effects. This is locked by 13
test fixtures that must never break. All the *memory* and *I/O* live in `service.py` and `state.py`,
*around* the pure core. This separation is the single most important engineering rule in the
codebase — it means we can change how the engine remembers things without ever risking the math that
produces a verdict.

---

## 2.5 L4 — Narrator + Dashboard (the human face)

**What it is.** Two pieces that turn the engine's JSON verdict into something a person reads and
clicks.

**The API (`api/main.py`)** — a **FastAPI** gateway in `aiops`. It's a clean, frontend-agnostic seam:
any dashboard (ours or a future one) consumes `/api/*` without ever touching the internal services or
needing to know about pod-hash names. Its endpoints (full list in Appendix C) include the causal
graph, the per-pod signals, the topology map, the recommendations, the scenario triggers, and —

**The narrator (`/api/narrative`)** — **the one and only LLM in the system.** A local model
(**`gemma4:e4b-it-qat`**, run via **Ollama on the host machine**, *not* as a cluster pod) takes the
finished verdict and writes a one-line English summary. Three things keep it safe:
- When nothing is wrong (no root cause), it returns a plain "steady" line and **skips the model
  entirely** — no AI is even invoked at idle.
- When a memory leak is climbing, it can write a model-free "OOM in ~N seconds" line from the
  forecaster's number.
- If the model is slow or fails on a real incident, a **deterministic template** writes a serviceable
  sentence instead. **The demo never blocks on the model.**

The hard rule (decision **D-002**): the model narrates the deterministic graph; it **never invents
causality.** It only gets the structured findings the math already produced.

**The dashboard (`dashboard/`)** — a **Next.js** web app served over the local network. Its
centrepiece is **one unified causal graph**: the eBPF-discovered topology drawn as a faint grey
backbone, with live causal edges overlaid hot and thick when an incident is happening. Around it: the
gemma4 verdict card, stat tiles, an embedded PSI panel, a recommendations panel (right-sizing +
fairness), the blast radius, and a **scenario console** with buttons to fire and reset S1/S2/S5 live.
Pressing buttons and watching the graph light up is the demo.

---

# PART 3 — HOW THE DETECTIVE THINKS

Part 2 listed the engine's pieces. This part explains *how* each one reasons — still in plain
language, but deep enough that you could defend any claim the system makes. This is the intellectual
core of the project.

The pipeline, in order: **detect** the trouble → **correlate** to find who-leads-whom → **gate**
each candidate arrow through three tests → **rank** to name the culprit and forecast the victims.
Wrapped around all of it: a **deviation check** (so normal load stays silent) and a **memory** (so
the verdict is stable and the engine learns).

## 3.1 Detection — finding the moment it turned bad

**The problem:** given a wiggly line of PSI values over 15 minutes, when (if ever) did this pod start
genuinely struggling, as opposed to just jittering normally?

**The method (in `detectors.py`):**
- An **EWMA** ("exponentially weighted moving average") tracks the pod's recent "normal" level — a
  running average that weights recent samples more. Think of it as the line's expected position.
- A **CUSUM** ("cumulative sum") adds up how far the real value drifts away from that expectation,
  and only fires when the drift is **sustained** — not a single spike, but a real, persistent
  departure. This pinpoints the **onset** (the moment it turned) accurately to one 5-second sample.
- Then `classify` names the *shape* of the trouble:
  - **burst** — rises, then returns (a transient).
  - **leak** — keeps climbing and doesn't come back (a memory leak).
  - **saturation** — pinned at a ceiling (hit a limit).
  - **flap** — oscillating / restart loops.

Naming the shape matters: a *leak* gets forecast forward to an OOM; a *burst* doesn't.

## 3.2 The deviation gate — why S0 is silent

**The problem this solves:** different pods have different "normal." The database normally does some
disk I/O; the kiosk does almost none. A fixed threshold ("PSI > 0.2 = bad") would either miss the
quiet pod's real trouble or scream at the busy pod's healthy work.

**The method:** the engine learns, *per pod*, what that pod's steady-state PSI looks like — its
typical level and its typical wobble (using a robust median-and-spread that deliberately skips past
storm periods so a past incident doesn't poison the baseline). This learned baseline lives in
`state.py` and persists.

Then an onset only counts as an **incident** if the pod's recent sustained PSI **deviates** from
*its own* learned baseline. A pod doing its normal busy work never deviates from its normal, so it's
never flagged. This is **why S0 (the idle control scenario) is silent**, and why the innocent
high-memory `firmware-cache` never trips an alarm: high usage is not deviation, and not suffering.

There's a timing refinement too. The deviation is judged over the **recent tail** of the window (set
by `RESET_WINDOW`), so when a storm *ends*, the verdict clears within a couple of minutes — instead
of lingering until the storm scrolls out of the 15-minute buffer. Fast to light up, fast to clear.

> **The standout property:** we don't detect "this number is high." We detect "this pod is behaving
> abnormally *for itself*, right now." That's what makes the system quiet when it should be quiet —
> and being quiet at the right time is what makes anyone believe it when it finally speaks.

## 3.3 Correlation — who leads whom

**The problem:** two pods both went bad around the same time. Did A's trouble cause B's, or the
reverse, or neither?

**The method (in `lagcorr.py`):** compare the two pods' signals at several time-shifts — 0, 5, 15,
30, 60, 120 seconds. We use **Pearson correlation** (a standard measure of how strongly two lines
move together, from −1 to +1), with a robust fallback (**Spearman**) for spiky data. The shift where
the two lines best line up is the **lag**, and the *sign* of that lag tells the **direction**:

> *"cooling-monitor's trouble at time T best matches timescaledb's trouble at time T+30s"* ⟹
> cooling-monitor **leads** timescaledb by 30 seconds ⟹ cooling-monitor is upstream.

A subtle but important rule: we only accept **positive** correlation as a sign of a cascade. If two
pods are *anti*-correlated (one up when the other's down), that's *competition*, not one feeding the
other — and we reject it as a causal edge.

## 3.4 The gate — three tests every arrow must pass

This is the **false-positive killer** (`gate.py`), and the direct answer to "correlation ≠
causation." An arrow enters the causal graph only if **all three** hold:

1. **Statistical** — the correlation is strong (peak |r| ≥ 0.6) *and* holds up at the neighbouring
   time-shift too (so it's not a one-window fluke), *and* it's positive (a cascade, not competition).
2. **Physical witness** — there is a *real* shared thing through which influence could travel:
   - a **shared PVC / disk** (for I/O contention), or
   - an **observed eBPF network link** (for things that talk over the network).
   - PSI co-pressure (both pods stalling on the same resource at the same time) only *corroborates* —
     by itself it never creates an arrow. **Coincidence between unrelated pods is rejected.**
3. **Temporal** — the cause's onset came *before* the victim's, consistent with the measured lag.

Correlation alone never makes an arrow. The witness requirement is what kills the classic false
positive (two pods that happen to wiggle together but share nothing).

> **One refinement for the no-network case (decision D-015).** Pure CPU or memory contention between
> two pods on the same node has *no* shared PVC and *no* network link — yet it's real (they're
> fighting over the same cores). So for the **source edge specifically** (a clearly-identified
> aggressor → its victim), we admit "same node" as a physical witness. This is what makes the S3 CPU
> scenario *architecturally* possible to detect — while a bare pair of co-wiggling pods still never
> forms an arrow without a clear source. (S3 is still blocked by *hardware physics* on our box — see
> Part 6 — but the engine is ready for it.)

## 3.5 Source attribution — blaming the writer, not just the victim

**The problem PSI alone can't solve:** PSI only shows you *victims*. Every pod stalling on the
saturated disk has high `psi_io` — including the database. PSI cannot tell you *who saturated the
disk*, because the aggressor isn't necessarily stalling itself.

**The method:** we bring in a second signal, **`io_write`** — per-pod disk-write throughput, *how
much each pod is actually writing*. The **source** of a disk storm is the pod that:
- is the **dominant writer** (writing far more than anyone else), **and**
- actually **deviated** (its writing genuinely spiked above its own normal — so the database's steady
  baseline writes are never mistaken for a source), **and**
- is positively correlated with, and *leads*, the victim's stall over the shared disk.

We orient the arrow **writer → staller**. This is the difference between "the database is stalling"
(useless — it's the victim) and "cooling-monitor's write storm is starving the database" (the actual
root cause). The `write` token in S1's evidence list `[write, pvc, temporal]` *is* this source
attribution — it's why we can blame the aggressor, not just point at the victim.

## 3.6 Ranking — naming the culprit and forecasting the victims

**The problem:** the gate gives us a web of accepted arrows. Which pod is *the* root cause?

**The method (in `ranking.py`): explanatory reach.** For each candidate pod, walk forward along the
accepted arrows (with influence decaying at each hop) and add up *how much of the total observed
trouble that pod explains.* Penalise any candidate that is itself explained by something upstream
(if A → B → C, then B isn't the root — A explains B). The pod that explains the most, and is itself
unexplained, is the **root cause.** The same forward walk gives the **blast radius**: who's already
hurt and who's predicted to be hurt next, with ETAs from the edge lags.

> **Why not PageRank?** We tried the famous PageRank algorithm first and it *failed* (decision
> **D-010**): seeding it at the symptoms handed the symptom all the "importance" and ranked the
> *victim* above its own cause. Explanatory reach is both more correct here *and* narratable — we can
> say "cooling-monitor explains 42% of the observed degradation," which a PageRank score can't.

## 3.7 Memory and the case library — the engine that learns

Everything above describes a single *pass*. But the engine runs continuously, and a naive version
would **flicker**: an arrow appears in the pass where everything aligns, then vanishes the next pass
when a sample is missing or the storm momentarily dips. That's useless on a dashboard.

So `state.py` wraps the pure reasoning in **persistent memory** (a small SQLite database on the
engine's own volume — deliberately separate from the factory's storm-prone disks). It holds:

- **Edge confidence with a structural floor.** A confirmed relationship is *held* across the gappy
  passes and decays *smoothly* instead of blinking out. A witnessed coupling settles to a faint
  baseline rather than vanishing, and *brightens* under load — so the dashboard graph holds steady at
  rest and visibly *morphs* when an incident hits, instead of strobing.
- **Per-pod PSI baselines** — the "normal" each pod is judged against (the engine of the deviation
  gate, Part 3.2). These persist, so a pod's learned normal survives a restart.
- **Case families.** When the same *kind* of incident recurs, the engine recognises it as a *variant
  of a type* it has seen — not a brand-new mystery each time. It uses a similarity measure (over which
  pods are stressors, which are victims, the shape of the arrow-subgraph, and the typical lags) rather
  than an exact match, so "S1, but this time dcim-bridge was also a co-victim" folds into the S1
  *family* as a variant. Each recurrence sharpens the case's signature, its typical lead-time (useful
  for forecasting), and — eventually — the remediation that resolved it.

Crucially, all of this is keyed by **workload name**, not by the ephemeral pod-hash. Kubernetes gives
a restarted pod a new random name; keying memory by the stable workload means confidence and
baselines *survive restarts*, which a pod-hash key would lose every time.

> **The design vision vs. what's built.** The full design (`DESIGN_stateful_engine_and_case_library.md`)
> also imagines pre-generating "hypothetical" cases from the topology (so the engine recognises a
> contention pattern the *first* time it occurs) and a learned classifier once enough labelled runs
> accumulate. The edge memory, deviation gating, and similarity-merged case families are **built and
> cluster-verified**; the topology-generated hypotheticals and the learned classifier remain
> proposals. Part 6 keeps this distinction honest.

## 3.8 Forecasting — telling you before the kernel does

**The problem:** detection tells you something *is* wrong. Can we warn *before* it goes wrong?

**The method (in `forecast.py`):** for memory specifically, we watch each pod's working memory climb
and, when it's rising on a steady ramp, **extrapolate the line forward to the pod's memory limit** —
emitting an "OOM in ~N seconds" warning before the kill actually happens. A memory leak is
*self-caused* (no other pod is doing it to you), so this rides as a standalone forecast rather than a
causal arrow. A flat memory level, or a database cache that fills and then plateaus, has ~zero recent
slope and correctly stays silent.

This is the **S5** beat: the card says "OOM in ~3 seconds," then the kernel kills the pod — *"we told
you before the kernel did."*

## 3.9 The five principles that make it defensible

Everything above reduces to five rules we never break:

1. **Zero application instrumentation** — every signal comes from the kernel via the kubelet. We
   change nothing inside the apps.
2. **Real faults, not fake metrics** — `fio` storms, the real OOM-killer, real CPU throttling. The
   tool *discovers*; it is never told.
3. **Threshold-free causal path** — arrows rest on correlation + a physical witness + time order,
   never on "value > limit." Thresholds exist only as a coarse L2 hint.
4. **Search, don't poll** — the engine *locates* the disturbance in the stored 15-minute series and
   analyses it where it sits, so storm duration and check timing stop mattering.
5. **Deterministic core, one LLM at the edge** — the same input yields the same verdict every time;
   the model only narrates evidence the math already produced.

---

# PART 4 — WALKTHROUGHS

## 4.1 End to end: what happens when you fire S1

S1 is "PVC I/O contention cascade" — our hero scenario. Trace a single button-press through the
whole stack:

1. **The trigger.** You press **S1 Fire** on the dashboard (or run `scenarios/S1/trigger.sh`). This
   touches a flag on **cooling-monitor**.
2. **The real fault (L0).** `cooling-monitor` sees the flag and launches a sustained, fsync-heavy
   `fio` disk storm against its directory on the shared volume — a *real* storm on a *real* (slow,
   spinning) disk.
3. **The physics (the kernel).** The one physical disk saturates. **timescaledb** — a different pod,
   with its own separate volume and *no network link* to cooling-monitor — starts stalling on that
   saturated disk. Its `psi_io` climbs. *This is the invisible coupling, now happening for real.*
4. **Collection (L1→L2).** Prometheus scrapes the rising PSI every 5 seconds. The aggregator sums it
   per pod, notices timescaledb crossing its hint-threshold, emits an `anomaly_candidate`, and keeps
   the last 15 minutes of every pod's signals in its ring at `/window`.
5. **Interpretation (L3).** The engine polls `/window`, aligns every pod onto one clock, and runs its
   pass: `detectors` finds timescaledb's onset (and cooling-monitor's write spike); `lagcorr` measures
   that cooling-monitor *leads* by ~30s; the `gate` checks all three clauses (strong positive
   correlation ✓, shared physical disk ✓, cause-before-effect ✓); source attribution sees
   cooling-monitor is the dominant *writer* that deviated, and orients **cooling-monitor →
   timescaledb**; `ranking` names cooling-monitor the root and timescaledb (plus dcim-bridge) the
   blast radius.
6. **The verdict (`/graph`).** Root = **cooling-monitor**; edge **cooling-monitor → timescaledb**,
   evidence **`[write, pvc, temporal]`**; blast radius = timescaledb, dcim-bridge. **No resource
   threshold anywhere in the causal path** — only correlation, the shared-disk witness, and time
   order.
7. **Presentation (L4).** The dashboard lights the edge hot; the verdict card pins cooling-monitor;
   gemma4 narrates it in a plain English sentence naming the source and the victim.
8. **Reset.** Press reset (or let it be). A few minutes after the storm ends, the recency gate decays
   the hot edge back to its faint structural floor — the graph self-clears, no manual cleanup.

Source correctly blamed, victim correctly predicted, the whole thing in well under a minute, and it
clears itself afterwards. That single clean cascade is the strongest thing we demonstrate.

## 4.2 The six scenarios — and their honest status

Each scenario lives under `scenarios/<id>/` with a runbook and a reset script. Heavy load runs
**only on trigger**.

| ID | Name | What it triggers | Status (internal truth) |
|----|------|------------------|--------------------------|
| **S0** | Steady-state control | nothing — 10 min idle | **✅ Verified.** The engine stays silent (`findings: []`), no root, even with firmware-cache using lots of memory. The credibility scenario. |
| **S1** | PVC I/O contention cascade | cooling-monitor `fio` storm | **✅ Verified, the hero.** Roots cooling-monitor on baked defaults (no env tuning), evidence `[write,pvc,temporal]`, self-clears in ~3–5 min. |
| **S2** | Large-file I/O starvation | log-archiver tar storm | **◐ Attribution tuning (mark-two).** The engine *detects* the disk stress, but doesn't yet pinpoint the on-demand source. See below. |
| **S3** | CPU throttle interference | analytics-batch CPU burst | **○ Out of scope (physics).** The engine is ready; our 16-thread box can't actually starve co-residents. See below. |
| **S4** | Network degradation + retry | injected latency on notify-gateway | **○ Out of scope.** Needs Chaos Mesh + a network signal, not built. |
| **S5** | Memory leak → OOM forecast | vision-qc leak flag | **✅ Verified.** Forecasts "OOM in ~N s" before the kill. |

**Demonstrable set: S0, S1, S5** (+ recommendations + the eBPF topology map). Lead the demo with
these.

**Why S2 isn't clean yet (the honest detail).** S2 fires `log-archiver`, a *scheduled job* (a
CronJob) that writes a huge file. Three things conspire against clean attribution:
- A short-lived job has **no steady-state PSI baseline** to deviate from — so it can't become a
  "finding" at all (the deviation gate, Part 3.2, has nothing to compare it against).
- The way it writes (asynchronous, direct I/O) means it doesn't *itself* stall, so PSI doesn't see it
  as a victim either — it's nearly invisible.
- Meanwhile, a *held* backbone edge from a previous S1 run (cooling-monitor → timescaledb, sitting in
  memory) can out-rank the real-but-invisible source. The tell is `onset_s: null` on the "winner" —
  it won on held structure, not a live deviation.

So S2 today gives a **confident but wrong root**, which is *worse* than "no root" for a demo. The fix
(a held edge must not win the root unless there's a *live deviating source* behind it, plus a path for
a no-baseline job to still be a finding) is real engine work, slated for **mark-two**. We keep S2 out
of the live demo and frame it publicly as "attribution refinement in progress" — which is honest:
the engine reliably *sees* the disk stress; it's the *pinpointing* that needs tuning.

**Why S3 is out of scope (hardware physics, not a bug).** S3 needs one pod to starve another of CPU.
On our 16-thread reference box, a CPU-hungry pod under a tight limit only *throttles itself* — it
physically cannot consume enough to starve its co-residents, because there are plenty of spare
threads. The engine is *proven* to draw the edge the instant a co-resident genuinely stalls (we've
tested that); the box just won't produce the real contention. Forcing it would require deliberately
shrinking the node's usable cores, which risks starving our own observability. Parked for mark-two.

**Why S4 is out of scope.** It needs Chaos Mesh (a fault-injection tool) installed and a network
degradation signal wired into the engine — neither is built. Cleanly future work.

## 4.3 The four judge questions — answered honestly

| Question | Status | How |
|---|---|---|
| **Q3 — Are services influencing each other?** | **✅ Live** | S1: cooling-monitor starves timescaledb over a shared disk, with no network link — the headline. |
| **Q4 — Which workloads need optimization?** | **✅ Live** | `/api/recommendations`: right-sizing in scheduler verbs (reclaim/resize) + a per-namespace fairness index. |
| **Q1 — Which pod causes CPU spikes?** | **◐ Engine-ready, physics-gated** | The engine is multi-signal (psi_cpu works); a true cross-pod CPU demo needs the node-saturation we can't force (S3). |
| **Q2 — How is PVC I/O linked to pod restarts?** | **◐ Partial** | The I/O cascade is live (S1); the specific restart-probe linkage is future work. |

So the truthful claim is: **two of the four answered live and on stage; the other two are
engine-ready but gated on hardware physics / one piece of future plumbing.** We don't claim all four
are live.

---

# PART 5 — RUNNING IT

> **Reminder on who does what.** The cluster runs on the home desktop (reachable over Tailscale). In
> our workflow, **the operator runs everything** — builds, deploys, fires scenarios — while edits to
> the code happen on the laptop (git master). Commands below are what the operator runs on the box.

## 5.1 Prerequisites — the kernel gate

The system needs a **real Linux kernel** — bare metal or a full virtual machine. **WSL2 is not
supported** (decision **D-003**): its custom kernel lacks the per-pod PSI we depend on. Recommended:
Ubuntu/Xubuntu 24.04+, kernel 5.15+, 16 GB RAM, ~64 GB free disk.

Before anything else, confirm all five kernel checks pass — these *are* the foundation:

```bash
uname -r                         # >= 5.15  (Ubuntu 24.04 ships 6.8+)
ls /sys/kernel/btf/vmlinux       # must exist  (eBPF needs this)
stat -fc %T /sys/fs/cgroup       # must print: cgroup2fs
cat /proc/pressure/cpu           # must show 'some'/'full' lines  (PSI is ON)
timedatectl | grep synchronized  # yes  (the lag math needs a synced clock)
```

Then install K3s **with the PSI feature gate** (this kubelet flag is mandatory — it's what exposes
per-pod PSI):

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik --kubelet-arg=feature-gates=KubeletPSI=true" sh -
```

And confirm per-pod PSI actually reaches Kubernetes (the whole differentiator):

```bash
kubectl get --raw "/api/v1/nodes/$(kubectl get no -o name | cut -d/ -f2)/proxy/metrics/cadvisor" | grep -m1 container_pressure
```

If that last line returns nothing, **stop** — nothing downstream will work. (Usual cause: a typo in
the feature-gate flag.)

## 5.2 Storage — set this up first (it's a real gotcha)

The two factory volumes (`tsdb-pvc`, `shared-logs-pvc`) bind to a **`slowdisk`** storage class:
static volumes on a **dedicated spinning HDD** (decision **D-014**). This is deliberate — a slow disk
is what makes the S1 source *actually stall* and produces realistic contention, while the K3s control
plane stays fast on the SSD.

`skctl up` does **not** create these for you. Set storage up *before* deploying:

- **On the reference box (with the dedicated HDD):** prep the HDD (see the header of
  `deploy/slowdisk.yaml`), then apply the static volumes:
  ```bash
  NODE=$(kubectl get node -o jsonpath='{.items[0].metadata.labels.kubernetes\.io/hostname}')
  sed "s/<NODE_NAME>/$NODE/g" deploy/slowdisk.yaml | kubectl apply -f -
  ```
  These volumes use a `Retain` policy: after a teardown that deletes the claims they go `Released` and
  won't rebind — delete them (`kubectl delete pv tsdb-pv-slowdisk shared-logs-pv-slowdisk`) and
  re-apply before redeploying.
- **On a plain single-disk PC (no spare HDD):** skip slowdisk — change both `storageClass: slowdisk`
  to `local-path` under `pvcs:` in `deploy/charts/factory/values.yaml` before deploying.

## 5.3 Build & deploy

Images are built per component and imported straight into the K3s runtime (no image registry needed):

```bash
git clone https://github.com/GreaseMonkeyIT/ABB_Accelerator_Submission.git && cd ABB_Accelerator_Submission
chmod +x deploy/skctl appendix/*.sh scenarios/*/*.sh   # restore exec bits (harmless if already set)

make test            # optional: engine tests + aggregator tests
make import          # build all 15 workloads + aggregator/engine/api/dashboard, import into k3s
make charts          # lint + render the factory chart
./deploy/skctl up --mode solo
```

`make import` and `skctl up` are both idempotent — safe to re-run after any change.

## 5.4 Verify — and the cold-start warm-up

```bash
kubectl get pods -A | grep -vE 'Running|Completed'   # ideally only the header line
kubectl get pvc -n factory-data                      # tsdb-pvc + shared-logs-pvc -> Bound
bash appendix/component_check.sh                      # per-component sweep
bash appendix/verify_taps.sh                          # telemetry taps
```

**The warm-up (don't skip this understanding).** A *fresh, cold* deploy needs **~15–20 minutes**
before it's demo-ready. Three things have to settle: the database finishes its initial population I/O,
the aggregator's 15-minute ring fills, and — the slow part — **the engine learns each pod's
steady-state PSI baseline.** Detection is deviation-based, so the engine only goes *silent* once it
has a baseline to deviate *from*. Until then, `/api/graph` shows transient database-initialisation
findings that clear on their own to `findings: []` (that *is* S0). A *warm* redeploy (keeping the
engine's memory volume) is silent in ~5 minutes. **Don't fire S1 until S0 is silent**, or the warm-up
noise muddies the result.

## 5.5 Operating, day to day

```bash
./deploy/skctl pause     # scale the factory to 0, keep PVCs + telemetry (idle between sessions)
./deploy/skctl resume
./deploy/skctl status

# rebuild ONE component after a code change, then roll it:
docker build -t skn/<name>:v0.1 <path>/ && docker save skn/<name>:v0.1 | sudo k3s ctr images import -
kubectl rollout restart deploy/<name> -n <namespace>
#   engine:  correlation/  -> deploy/correlation-engine -n aiops
#   api:     api/          -> deploy/api               -n aiops
#   workload: workloads/<name>/ -> deploy/<name>       -n factory-core|data|edge
```

> **In solo mode never pass `--components <subset>`** — that flag is *exclusive* and disables every
> group you don't list (decision **D-012**). Solo always runs the full `skctl up`. (All volumes carry
> a `keep` policy, so a toggle can never delete your data — but the flag will still take services
> down.)

## 5.6 What you can change without a rebuild

The cardinal rule: **anything baked into a container image needs a full rebuild** (`docker build` +
`k3s ctr images import` + rollout restart). That includes any `main.py`/`main.go`, the database's
`init.sql`, and the engine's core files (`pipeline.py`, `service.py`). Everything else is a knob you
can turn live:

- **Engine behavior** (env on `deploy/correlation-engine`): `ENGINE_SIGNALS` (which signals to
  analyse), `ANALYSIS_WINDOW` (correlation span), `RESET_WINDOW` (how fast a verdict clears), `DEV_K`
  (deviation-gate sensitivity), `FORECAST_HORIZON_S` (OOM warn window), and the edge-memory knobs
  (`EDGE_ALPHA/DECAY/SHOW/HIDE`).
- **Narrator + recommendations** (env on `deploy/api`): `OLLAMA_HOST` / `OLLAMA_MODEL`, `PROM_URL`,
  `RECLAIM_FRAC` / `RESIZE_FRAC`.
- **S1 storm intensity** (cooling-monitor env in `values.yaml`): `FIO_JOBS / RUNTIME / FSYNC / SIZE /
  DIRECT`. (The verified defaults are baked: 6 jobs / 120s / fsync on.)
- **Database write load** (plc-gateway env in `values.yaml`): `PLC_PERIOD_MS`, `PLC_CHANNELS`.
- **L2 queries & thresholds** (`aggregator/queries.yaml`): reload the config map + restart the
  aggregator — no rebuild.

**Every change gets logged** in `BUILD_LOG.md`. That discipline is why we can always answer "why did
we change X?"

## 5.7 Troubleshooting — symptom to fix

| Symptom | Likely cause / where to look |
|---|---|
| No `container_pressure` lines from cadvisor | The PSI feature-gate flag is wrong; check `/etc/systemd/system/k3s.service`, restart k3s (§5.1). |
| `/api/graph` shows findings on a fresh deploy | Normal cold-start noise; wait the ~15–20 min warm-up until it's `findings: []` (§5.4). |
| A factory pod is `ImagePullBackOff` | Its image wasn't imported; re-run `make import` (the api/dashboard images were a past gap). |
| PVCs stuck `Pending` | slowdisk volumes not applied, or `Released` after a teardown — re-apply (§5.2). |
| S1 fires but no clean root | Triggered on un-settled pods (needs ~60s of samples), or S0 wasn't silent first. Wait, retry. |
| Verdict won't clear after a storm | The hot edge takes ~3–5 min to decay below the hot threshold; wait or hit reset. |
| Narrator slow / cold | The verdict card always renders from the deterministic template; gemma4 prose is additive — never blocks. |
| "When/why did we change X?" | Search `BUILD_LOG.md` for the component name. If it's not logged, that's the bug — log it. |

---

# PART 6 — THE HONEST RECORD

This part is the candid internal accounting: what is genuinely built and verified, what is
roadmap, the gaps in detail, and the history of every major decision.

## 6.1 Built vs. roadmap

**Built and solid:**
- The full L0→L4 spine, end to end.
- The S1 disk-causality cascade: threshold-free, correct root, source-attributed, self-clearing.
- The deviation-gated engine (S0 silent), with persistent per-pod baselines.
- The stateful memory + similarity-merged case families (beyond the original plan).
- Multi-signal analysis (psi_io / psi_cpu / psi_mem) merged into one graph.
- Source attribution via `io_write` (writer → staller).
- The OOM forecaster (S5), firing before the kill.
- The recommendation engine (right-sizing + fairness, answering Q4).
- The Caretta eBPF topology map (Q-style dependency discovery, zero config).
- The gemma4 narrator with an always-on deterministic fallback.
- The dashboard: unified causal-over-topology graph, verdict card, PSI panel, recommendations,
  scenario console (S1/S2/S5 fire + reset).

**Roadmap (honestly not built):**
- **S2 clean attribution** — the held-edge / no-baseline-source problem (Part 4.2, mark-two).
- **S3 live** — blocked by hardware physics on our box (Part 4.2).
- **S4** — needs Chaos Mesh + a network signal.
- **The restart-probe link (Q2)** — a DB liveness probe tight enough that a storm induces a restart.
- **A2 Log Detective** — the log-analysis agent (needs the Loki pipeline working).
- **A5 bounded tool-calls** — the orchestrator making a few read-only Kubernetes queries mid-incident.
- **The topology-generated hypothetical cases** and **the learned case classifier** (DESIGN Part C).
- Dashboard extras: incident timeline + replay slider, pod detail drawer, full PSI heatmap, a
  fairness header widget.
- The rehearsal ledger (≥35 runs → a precision/recall accuracy table).

## 6.2 The named agents — design vs. reality

The plan describes five "agents" (A1–A5). To keep the public story honest, here's exactly which are
implemented:

| Agent | Role | Built? |
|---|---|---|
| **A1 Resource** | Changepoint detection + OOM forecast | ✅ Built (`detectors.py`, `forecast.py`) |
| **A2 Log Detective** | Mining error logs for corroborating evidence | ○ Roadmap (needs Loki) |
| **A3 Topology** | Dependency map / edge health | ◐ The eBPF map is built (Caretta); engine using it as a "witness" is future |
| **A4 Correlator** | Lag-correlation + gate + graph assembly | ✅ Built (`lagcorr.py`, `gate.py`) |
| **A5 Verdict/Orchestrator** | Ranking + confidence + bounded tool-calls | ◐ Ranking built (`ranking.py`); the bounded tool-calls are roadmap |

And two framing corrections the public docs now reflect (the **MASTER_PLAN honesty pass**, LOG-102):
- **LangGraph/LangChain is NOT used.** The engine is plain in-process Python (`run_pass` composing the
  modules). The original plan named LangGraph; we never needed an orchestration runtime.
- **The LLM runs on the host, not as a cluster pod** — `gemma4:e4b-it-qat` via an external Ollama,
  reached over the LAN. (The plan's "Ollama pod / phi3.5-qwen" phrasing was the early design vision.)

## 6.3 The decision register — every major ruling, in plain terms

These are the `D-numbers` from `BUILD_LOG.md` — the choices that shaped the system. When someone asks
"why is it built this way?", the answer is one of these.

| # | The decision | In plain terms |
|---|---|---|
| **D-001** | Prometheus as the metrics store (VictoriaMetrics as a documented fallback) | At our small scale, the famous "Prometheus uses too much RAM" problem doesn't bite, and Prometheus is the familiar, standard choice. |
| **D-002** | The L3 agents are *inference engines*; exactly one LLM, at the language edge | The reasoning is deterministic math, reproducible and trustworthy. The AI only writes the final sentence. *The* foundational decision. |
| **D-003** | Demo on a real Ubuntu VM / bare metal, **never WSL2** | WSL2's kernel lacks the per-pod PSI we depend on. |
| **D-004** | The factory apps' own metrics are **never** fed to the engine | Keeps "zero instrumentation" honest; the apps' true numbers are only used to *score* our accuracy. |
| **D-006** | Machine-agnostic packaging: one chart + on/off switches; solo or fleet mode | The same package runs whole on one box or spread across several, by flipping switches. |
| **D-007** | Primary build host = a Linux desktop; the `language` switch accepts an external Ollama | The reference box is the headless desktop; the GPU laptop can serve the model over the LAN. |
| **D-008** | Remote topology: Tailscale mesh + Syncthing for file sync; **git is the source of truth** | The laptop edits, the desktop runs; files sync, but git is authoritative. |
| **D-010** | Root-cause ranking = **explanatory reach**, not PageRank | PageRank seeded at symptoms ranked the *victim* above its cause. Explanatory reach is correct *and* narratable. |
| **D-011** | Remote power-on via a cloud smart plug | The desktop's firmware ignores Wake-on-LAN, so a smart plug + "always-on after power" resurrects it from anywhere. |
| **D-012** | `skctl --components` is exclusive; solo mode always runs the full bring-up; all PVCs carry a `keep` policy | A subset flag disables everything else — and a toggle can never delete your data. |
| **D-013** | A 14-day raw telemetry window (bigger DB volume + compression + retention) | The rolling history the demo shows; baked into the database's `init.sql`. |
| **D-014** | S1's contention disk is a **dedicated spinning HDD**, off the fast SSD | A slow disk makes the storm source *actually stall* — realistic contention; the control plane stays fast on the SSD. |
| **D-015** | Same-node PSI re-admitted as a witness **for the source-edge path only** | Lets CPU/memory contention with no network link (S3) form an edge, without re-opening the false-positive floodgates. |

(D-005 and D-009 were superseded/withdrawn — see `BUILD_LOG.md` for the full trail. The log is
append-only; every revert links what it undoes.)

## 6.4 The mark-two backlog (the next real build work)

When the team picks the build back up, this is the ordered wishlist (from `ROAD_TO_COMPLETION.md` and
LOG-102):

1. **S2 attribution fix** — a held edge must not win the root unless a *live deviating source* backs
   it (the `onset_s: null` tell), **plus** a path for a no-baseline scheduled job to still register as
   a finding. (Alternative: make the job write *synchronously* so it stalls itself and becomes visible.)
2. **The structural-backbone root-promotion fix** — the general version of the S2 problem (extends the
   precedents in LOG-074/075/090).
3. **The restart-probe link (Q2)** — a tight database liveness probe so a storm induces a real restart
   the engine can attribute.
4. **`io_read`** as a signal (S2 is a write storm; reads are a separate dimension).
5. **Dashboard completion** — pod drawer, full PSI heatmap, fairness header widget, timeline replay.
6. **The rehearsal ledger** — ≥35 scripted runs → a precision/recall accuracy table vs ground truth.
7. **A2 Log Detective** (once Loki is healthy) and **A5 bounded tool-calls**.

Explicitly *out of scope* even for mark-two: S3 physics (would require crippling the node), S4 + Chaos
Mesh. *Parked* (revisit anytime): fine-tuning the gemma4 incident prose; a CPU "usage-coupling"
backbone.

## 6.5 The closed loop — a fine-tuned narrator + bounded "remedy agents" (roadmap)

> **Status: roadmap / design vision, NOT built.** This section exists so the team has a written,
> defensible answer to the one capability a polished competitor app has and we don't today: an
> *action* layer — "here's what to do, now do it." It is the principled, Kubernetes-native, causal
> version of that idea. See also `MASTER_PLAN.md` §6 (the architecture-level spec).

**The three steps of a complete loop.** A mature operations tool does three things: **explain** (what
broke and why), **recommend** (what to do), and **act** (do it, safely). Today we do the first two:
the deterministic engine *explains* with a causal verdict, and `/api/recommendations` *recommends* in
scheduler verbs (reclaim / consolidate / throttle / resize) plus a fairness index. The missing third
step is **act** — and crucially, we are uniquely positioned to add it *safely*, because **we act on a
known cause, not a guessed symptom.** You cannot responsibly automate a fix when all you have is "this
looks abnormal"; you can when you have "*this* pod is the root, with this evidence."

**The idea — remedy agents.** A **remedy agent** is a small, purpose-built, *bounded* component that
can perform — or *restrict* — exactly **one** class of operation, behind hard guardrails. Examples,
each mapped to an existing recommendation verb:

| Remedy agent | What it does | "Restrict" flavour |
|---|---|---|
| `throttle` | Tighten the aggressor's CPU/IO limits temporarily | Restricts the offender's resource take |
| `qos-demote` | Drop a best-effort hog below latency-sensitive pods | Restricts scheduling priority |
| `resize` / `reclaim` | Right-size requests/limits toward measured p95 | — |
| `cordon` / `evict` | Move a noisy neighbour off the contended node | Restricts where it may run |
| `restart` | Recycle a pod stuck in a confirmed leak/flap | — |
| `page-human` | Escalate to an on-call engineer with the full evidence chain | (the safe default) |

The "restrict a specific operation" cases are the important half: instead of only *scaling things
up*, several remedy agents *constrain the offending workload* — throttle it, demote it, fence it —
which is exactly what you want when one pod is harming others.

**How it stays safe (and keeps our core principle intact).** The remedy layer must not undermine the
"deterministic core, one LLM at the edge" rule (decision D-002). So the division of labour is strict:

1. **The deterministic engine decides *what is wrong*** — the causal verdict, with a confidence gate.
   Unchanged. The model never gets a vote on the diagnosis.
2. **A *fine-tuned* narrator/orchestrator translates that verdict into a *bounded intent*** — it picks
   one action from a **fixed, closed vocabulary** (the verbs above) and fills in its parameters. It
   cannot invent an action outside the set, and every proposed action must **cite the causal evidence**
   that justifies it (cite-or-die, extended from prose to actions). *Why fine-tune?* A small model
   tuned on our own `verdict → intent` pairs makes this extraction reliable and tightly constrained —
   far fewer malformed or out-of-vocabulary suggestions than a general prompt — while staying **local
   and air-gap-clean** (no cloud LLM, unlike a competitor's cloud-chatbot dispatch).
3. **The remedy agent executes within hard rails.** Each agent holds a **least-privilege Kubernetes
   permission** (it can do its one verb and nothing else), and runs under guardrails: **dry-run by
   default**, a **human-approval gate** for anything destructive, **rate limits**, a **blast-radius
   cap**, and **automatic rollback** if the verdict doesn't improve within a window. The loop is
   closed but *governed* — the system proposes, a human (or a strict policy) disposes.

**Why this is the right answer to the competitor's dispatch feature.** A predictive-maintenance app
routes a *human technician* to a *physical machine* based on skills and shift. That's good product
design — but it stops at "a person looks abnormal-ish, send someone." Our loop routes a *bounded
remedy* (or a human approval) to the *causally-identified root pod* — and it can, because the engine
produced a cause, not just a flag. We answer the same operator need ("what now?") one level deeper:
**not "who do I send," but "what is the smallest safe action on the actual culprit, and shall I take
it?"**

**What it's gated on (honesty).** This is deliberately *not* a quick add. Acting automatically is only
responsible once two things are true: (a) the **rehearsal ledger** shows the verdict is accurate
enough to trust (the precision/recall evidence in the mark-two backlog), and (b) the **confidence
gate** reliably suppresses low-certainty verdicts. Until then, the only "remedy agent" that should run
without a human in the loop is `page-human`. It builds directly on the already-planned A5 *read-only*
bounded tool-calls — this extends read-only → *bounded write*, behind the guardrails above.

---

# APPENDICES

## Appendix A — Glossary

- **Air-gapped** — a machine with no internet connection. Industrial floors often require this; our
  tool runs fully offline, which most cloud tools can't.
- **Blast radius** — the set of pods an incident has hurt or is predicted to hurt next.
- **cAdvisor** — the component inside the kubelet that exposes per-container metrics, including PSI.
- **Cascade** — a chain of cause-and-effect across pods (A hurts B hurts C).
- **CronJob** — a pod that runs on a schedule (or on demand) rather than continuously.
- **CUSUM / EWMA** — the two statistical tools that detect when a signal "turned bad" (Part 3.1).
- **Container / image / pod** — see Part 0.1.
- **Deviation gate** — the rule that an incident must depart from a pod's *own* learned normal (Part
  3.2). Why S0 is silent.
- **eBPF** — a Linux feature for safely observing the kernel without touching the apps (Part 0.7).
- **Edge / edge box** — a small computer running on-site (e.g., a factory floor), not in a cloud.
- **fio** — a real disk-stress tool; how cooling-monitor produces the S1 storm for real.
- **Kubernetes / K3s / kubelet / node / namespace** — see Part 0.2.
- **Lag correlation** — measuring which pod's trouble *precedes* another's, to find direction (Part 3.3).
- **LLM** — Large Language Model; our one AI, used only to narrate (Part 0.9).
- **OOM** — "Out Of Memory"; the kernel kills a pod that exceeds its memory limit.
- **Ollama** — the tool that runs the local LLM (gemma4) on the host machine.
- **PromQL / Prometheus** — the query language / the tool that collects all metrics (Part 0.5).
- **PSI** — Pressure Stall Information; the kernel's "is this pod *suffering*?" signal (Part 0.6). The
  single most important concept.
- **PVC** — Persistent Volume Claim; a pod's chunk of durable disk (Part 0.4). Two PVCs can share one
  physical disk — the hidden coupling.
- **Root cause** — the pod that best *explains* the whole incident (Part 3.6).
- **Throttling** — the kernel deliberately slowing a pod that hit its CPU limit.
- **Time-series** — a metric measured repeatedly over time; a line on a chart.
- **Witness** — the physical shared thing (a disk or a network link) that makes a causal arrow
  plausible. No witness, no arrow.
- **Workload** — the stable name of a service, independent of which restarted pod is currently
  running it. The engine keys its memory by workload, not pod.
- **Zero instrumentation** — we change nothing inside the watched apps; everything is read from
  outside.

## Appendix B — Repository map (where everything lives)

| Path | What's in it |
|---|---|
| `workloads/` | The 15 factory pods (L0), one folder + Dockerfile each |
| `deploy/` | The Helm chart (`charts/factory`), the `skctl` bootstrap script, telemetry values, `slowdisk.yaml`, the L2/L3/L4 manifests |
| `aggregator/` | The L2 Go service, the frozen `event.schema.json`, the PromQL query pack |
| `correlation/` | The L3 engine: `engine/{detectors,lagcorr,gate,ranking,pipeline,forecast,merge,state}.py`, `service.py`, and the unit tests |
| `api/` | The L4 FastAPI gateway |
| `dashboard/` | The Next.js dashboard |
| `scenarios/` | S0–S5 triggers, runbooks, reset scripts, the rehearsal ledger |
| `appendix/` | Read-only diagnostic scripts (`verify_taps`, `component_check`, `diag_scrape`, `psi_watch`, `restart_test`) |
| `*.md` (root) | All the documentation (this book + the companions in "How to read this book") |

## Appendix C — The API (what the dashboard, or any frontend, consumes)

All under `/api/`, clean JSON, CORS-open, with a live OpenAPI spec at `/docs`:

| Method + path | Returns |
|---|---|
| `GET /api/graph` | The causal verdict: root cause, edges (+ evidence), blast radius, findings, OOM forecasts |
| `GET /api/pods` | Per-workload snapshot, hot-sorted, with an `anomalous` flag |
| `GET /api/signal/{pod}?signal=psi_io` | One workload's (timestamp, value) series |
| `GET /api/events` | The L2 anomaly-candidate stream |
| `GET /api/narrative` | The one-line verdict in prose (gemma4; deterministic fallback; OOM forecast woven in) |
| `GET /api/topology` | The eBPF-discovered service map (Caretta) |
| `GET /api/recommendations` | Right-sizing in scheduler verbs + per-namespace fairness (Q4) |
| `GET /api/scenarios` | The scenario catalogue |
| `POST /api/scenarios/{id}/trigger` | Fire S1 / S2 / S5 (via a bounded, read-only service account) |
| `POST /api/scenarios/{id}/reset` | Reset S2 / S5 |
| `GET /api/health` | Upstream L2/L3 reachability |

## Appendix D — PromQL cheat sheet (the raw signals)

The actual metric expressions behind the signals (for anyone querying Prometheus directly):

```promql
# CPU burst + throttling
rate(container_cpu_usage_seconds_total{namespace=~"factory-.*"}[30s])
rate(container_cpu_cfs_throttled_periods_total[1m]) / rate(container_cpu_cfs_periods_total[1m])

# Memory leak + OOM
container_memory_working_set_bytes
kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}

# PVC + disk
kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes
rate(node_disk_io_time_seconds_total[30s])

# PSI — the differentiator (busy vs suffering)
rate(container_pressure_cpu_stalled_seconds_total[30s])
rate(container_pressure_memory_stalled_seconds_total[30s])
rate(container_pressure_io_stalled_seconds_total[30s])

# The eBPF service map (Caretta)
caretta_links_observed_total
```

## Appendix E — The team & credits

**SiliconKnights** — Soumyadip Das · Shivam Kumar · B Kishan · Aaryan Shyam Pillai.
ABB Accelerator 2026, Theme 2: *Beyond monitoring — AI agents for real-time pod resource discovery
and dependency mapping.* Finalist (6 of 1000+).

Built on the shoulders of (and crediting honestly): the Linux kernel's PSI; Prometheus & the
kube-prometheus-stack; Caretta (groundcover) for eBPF flows; Ollama + gemma; K3s. Conceptual debts:
Koordinator (PSI as causal evidence), Causely (deterministic graph + LLM-as-narrator), K8sGPT
(analyzer pre-filtering), NVIDIA KAI (scheduler-verb recommendations + fairness framing).

---

*This book consolidates MASTER_PLAN, EXPLANATIONS, BUILD_GUIDE, BUILD_LOG, ROAD_TO_COMPLETION, the
DESIGN doc, QUICKSTART, and DEMO_RUNBOOK into one readable reference. When the source documents and
this book disagree, the source documents — especially the latest BUILD_LOG entries — are
authoritative; update this book to match. Last consolidated: 2026-06-22 (build state per BUILD_LOG
LOG-102).*
