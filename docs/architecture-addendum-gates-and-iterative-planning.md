# Architecture Addendum — Gates and the iterative planning cycle

> **Status: proposal for review, not yet normative.** This addendum extends
> `orchestrator-architecture.md` with the gate / closing-sequence / plan-next /
> learnings layer prototyped in the single-repo Specfuse loop kit. It is written to
> be folded into the architecture document section-by-section once accepted. Until
> it is folded in and the dependent agent configs are version-bumped, the current
> frozen behavior (whole-feature planning, single `plan_review`) remains in force.
>
> **Why this is a deliberate decision, not a mechanical merge.** The orchestrator
> ships features today without gates. Adding them changes a frozen PM baseline and
> the feature state machine. The change is small (see §A.2) but it is real, so it
> goes through the architecture document first, per the implementation plan's own
> rule: *resolve architectural ambiguity in the architecture document before
> continuing.*

---

## A.1 Motivation and the reconciliation principle

The PM agent's `task-decomposition` skill drafts a feature's **entire** task graph in
one pass, the human reviews that whole graph once at `plan_review`, and
`dependency-recomputation` thereafter only flips pre-existing tasks `pending → ready`.
This is a whole-feature-up-front model. It is the part of the design most likely to be
wrong on multi-repo work, where cross-repo dependencies and interface shapes are
predicted before any of the repos exist.

The gate layer replaces "plan the whole feature, then execute" with "plan to the next
checkpoint, execute, learn, re-plan the next checkpoint from what was learned." A
**gate** is a milestone partition of a feature: an ordered batch of tasks followed by a
mandatory closing sequence (retrospective → lessons → docs → plan-next) and a human
review-and-arm checkpoint. Gate *milestones* are defined up front when the feature is
planned; the *task detail* for gate N+1 is drafted by the gate-N closing sequence, not
predicted at feature start.

**Reconciliation principle: reuse the existing machinery; do not bolt on a parallel
one.** Every mechanism the gate layer needs already exists in the orchestrator — a
human approval gate (`plan_review → generating`), a planning skill that decomposes and
validates a task graph, a dependency recomputation that releases ready work, and a
notion of a task that exists in the graph but has not yet been materialized as an
issue. The gate layer threads through these rather than introducing new states, new
statuses, or a new agent. The cost of the feature is therefore much smaller than its
conceptual weight suggests.

---

## A.2 Amendment to §6.1 — Feature state machine

The feature state machine gains **exactly one new transition** and no new states:

```
in_progress → plan_review     (NEW)
```

Owned by the **PM agent**, fired when a gate's closing sequence completes *and* a
later gate exists in the feature's gate skeleton. It carries the feature back into the
existing `plan_review` state so the human reviews and arms the next gate through the
same flow they already use for the first gate.

The feature therefore **oscillates** once per gate instead of passing through
`plan_review` a single time:

```
drafting → validating → planning → plan_review → generating → in_progress
   → [gate 1 closing sequence runs as tasks; plan-next drafts gate 2]
   → in_progress → plan_review          (NEW edge; PM-owned, gate 1 complete, gate 2 exists)
   → [human reviews + arms gate 2]
   → plan_review → generating → in_progress
   → … repeat per gate …
   → in_progress → done                 (existing edge; last gate, no next gate)
```

Notes for the §6.1 table and §6.3 ownership list:

- The existing `plan_review → generating` (human approval) is unchanged and now serves
  as the **per-gate arm checkpoint**. The human reviews the drafted next gate, edits or
  accepts its tasks, and approves — exactly the existing plan-review interaction,
  scoped to one gate.
- **Under feature autonomy `auto`, the `in_progress → plan_review` stop may be skipped**
  (the PM agent auto-arms the next gate and proceeds toward `generating`) — but only when
  the auto-arm conditions in §A.6.1 all hold. Under `review`/`supervised`, the stop
  always fires. So the new edge is conditional on autonomy mode; §A.6.1 is the governing
  rule.
- The feature's **gate skeleton** is authored during `planning`, before the first
  `plan_review` (§A.5.0). The first `plan_review` therefore reviews the gate skeleton
  *and* gate 1's tasks together; subsequent `plan_review` stops review one gate's tasks
  each.
- `generating` per gate may be a **no-op pass-through** for gates that introduce no new
  generated surfaces. Specfuse runs only when a gate's tasks declare new
  `generated_surfaces`/`required_templates`; otherwise the state is transited without a
  generator run. State this explicitly so a no-op `generating` is not read as an error.
- `in_progress → done` (existing, PM-owned) fires only on the **final** gate's
  completion. The PM agent distinguishes "gate complete, next gate exists" (→
  `plan_review`) from "gate complete, no next gate" (→ `done`) by reading the feature's
  gate skeleton (§A.5).
- `in_progress → blocked` (existing, any-agent) is unchanged and applies within any
  gate.

No other feature-state edge changes. The task state machine (§6.2) is **unchanged**.

---

## A.3 Amendment to §3 — Vocabulary

### A.3.1 New task types

§3's task-type set expands from four to **eight**. The original four
(`implementation`, `qa_authoring`, `qa_execution`, `qa_curation`) are unchanged. Four
**closing task types** are added; every gate contains exactly one of each, in order, as
its closing sequence:

- **`retrospective`** — authors the feature-local `RETROSPECTIVE.md`: per-task, what
  worked, what failed and why, attempts taken, and any missing or ambiguous rule,
  template, or boundary observed in the gate. Synthesis against the gate's event-log
  slice and commits; no code.
- **`lessons`** — promotes the *generalizable* subset of the retrospective into the
  cross-feature `LEARNINGS.md` (§A.4). Feature-specific observations stay in
  `RETROSPECTIVE.md`; only reusable rules graduate.
- **`docs`** — reconciles project/product documentation and the feature's roadmap/registry
  status with what the gate actually delivered.
- **`plan-next`** — drafts the next gate's tasks and produces the human review summary
  (§A.6). The one act of forward design in the cycle.

All eight task types share the **same task state machine** (§6.2); type affects only
which agent handles the work and what the work unit contains — the existing §3 rule,
now spanning eight types.

### A.3.2 Closing-type handling

The four closing types are handled by the **PM agent** (§A.5). No new agent role is
introduced. `retrospective`, `lessons`, and `docs` are synthesis against a concrete log
and are appropriate for the cheaper production model; `plan-next` is forward design and
takes the strongest model, consistent with the implementation plan's existing
model-selection logic.

### A.3.3 Gate vocabulary

- **Gate** — an ordered partition of a feature's task graph: a batch of substantive
  tasks (`implementation`/`qa_*`) followed by the four-type closing sequence. A feature
  has an ordered list of gates (its **gate skeleton**), defined when the feature is
  planned.
- **Gate skeleton** — the ordered list of gate milestones for a feature (gate number +
  a one-line objective + a status, optionally a per-gate autonomy override), **authored
  by the PM agent during `planning`, co-authored with the human** (§A.5.0). Present from
  the start of planning. Only the current gate's tasks are detailed; later gates carry a
  milestone line and an empty task set until plan-next fills them. The skeleton is a
  living plan, not a contract frozen at `planning`: plan-next may revise *not-yet-reached*
  gates (§A.5.2).
- **Arming** — the human action, during the per-gate `plan_review`, of accepting the
  drafted next-gate tasks so the PM agent will create their issues at `generating`. An
  un-armed task is one present in the `task_graph` with no GitHub issue yet — a state
  the orchestrator already has.

---

## A.4 Amendment to §4.2 — Orchestration repo layout

Two additions to the orchestration repo:

- **`/LEARNINGS.md`** (repo root) — a cross-feature, append-only log of durable,
  reusable rules distilled by every gate's `lessons` task. Read at planning time
  (task-decomposition and plan-next both consult it) so each feature's plan is informed
  by every prior gate's experience. This is **process, not product**, and lives in the
  orchestration repo. It is distinct from the per-phase walkthrough retrospectives under
  `/docs/walkthroughs/` — those concern *building* the orchestrator; `LEARNINGS.md`
  concerns *using* it to ship features. Both coexist.
- **Per-feature gate artifacts** under `/features/` (alongside the existing
  `FEAT-YYYY-NNNN.md` registry and `FEAT-YYYY-NNNN-plan.md` plan file):
  - `FEAT-YYYY-NNNN-RETROSPECTIVE.md` — feature-local raw observations (authored by
    `retrospective` tasks; one section appended per gate).
  - `FEAT-YYYY-NNNN-gate-NN-review.md` — plan-next's human review summary for gate N+1
    (§A.6). Advisory; owns no state; regenerated if plan-next reruns.

The feature registry (`FEAT-YYYY-NNNN.md`) frontmatter remains the source of truth for
the task graph; the gate artifacts are produced *during* `in_progress` and consumed at
the per-gate `plan_review`.

---

## A.5 Amendment to §5 — PM agent

The PM agent's remit extends from whole-feature planning to **gate-scoped, iterative
planning plus gate closing**. This is the behavioral change that requires a version bump
(§A.8). Four changes:

### A.5.0 Gate identification (Step 0 of `task-decomposition`)

The gate skeleton has a single point of origin: it is authored at the **start of
`planning`**, as a new **Step 0** of the `task-decomposition` skill, before any gate's
tasks are decomposed. The PM agent partitions the feature into an ordered list of gates,
co-authoring with the human (the same co-authoring posture as work-unit prompts today —
the PM proposes, the human refines, the result is one the human endorses). Each gate
entry is `{ gate: <int>, objective: <one line>, status: open }`, written to the
feature-frontmatter `gates` array (§A.7). The PM agent then runs the existing
decomposition procedure scoped to **gate 1 only** (§A.5.1).

Gate identification is assigned to the PM, not the specs agent, because a gate boundary
is only meaningful in terms of task structure — "gate 1 is the persistence layer, gate 2
is the API surface that depends on it" — and the agent that understands task structure is
the PM. Asking the specs agent to draw gate lines would force it to reason about
implementation batching it otherwise never touches. The specs agent's `drafting →
validating → planning` ownership is unchanged; gate identification happens *after* the
hand-off, as the PM's first planning act.

The initial skeleton is a **prediction** and is therefore explicitly revisable
downstream (§A.5.2) — without that, the gate model would merely move whole-feature-up-front
prediction from the task level to the gate level and keep the same brittleness. Gates
already *passed* are immutable; gates not yet reached may be split, merged, or re-scoped
by plan-next.

### A.5.1 `task-decomposition` is scoped to a gate, not a feature

Currently `task-decomposition` decomposes the whole feature in one pass (its §"The
decomposition procedure" produces every implementation and QA task for the feature).
Amended behavior: it decomposes **the current gate only** — the tasks realizing the
current gate's milestone — and appends that gate's four-type closing sequence. Later
gates in the skeleton remain milestone-only (empty task sets) until their turn.

The decomposition machinery itself (capability identification, target-repo assignment,
dependency edges, validation, autonomy overrides) is unchanged; only its **scope per
invocation** narrows from "the feature" to "this gate." The skill reads the gate
skeleton to know which milestone it is decomposing.

### A.5.2 New PM skill: `plan-next`

A new skill, sibling to `task-decomposition`, run as the `plan-next` closing task of
each gate. It is `task-decomposition` *plus* two things: its inputs include the gate
`RETROSPECTIVE.md` and the root `LEARNINGS.md` (so the next gate is shaped by what the
last gate taught), and its outputs include the human review summary (§A.6). It:

1. Reads the gate skeleton to identify the next gate's milestone (the lowest-numbered
   gate with an empty task set).
2. Decomposes that milestone into draft tasks — added to the feature `task_graph` with
   their `gate` field set (§A.7) but **no issues created** (the "draft, not armed"
   state). Appends that gate's own four-type closing sequence.
3. Writes `FEAT-YYYY-NNNN-gate-NN-review.md` (§A.6).
4. **May revise the not-yet-reached skeleton.** If what gate N taught implies later gates
   should be split, merged, or re-scoped, plan-next edits those future skeleton entries
   and surfaces the change **loudly in the review summary as a flagged decision** — never
   silently. It may **not** touch any gate already passed (immutable). A skeleton revision
   is itself a signal that forces human review even under autonomy `auto` (§A.6.1).
5. Validates structurally (the same schema/cycle/orphan checks `task-decomposition`
   runs, plus: every drafted task has the five mandatory work-unit sections once its
   issue body is drafted; the closing sequence is present and ordered; any per-gate
   autonomy override is no looser than the feature default — §A.7). A malformed draft
   fails here, at the human's review point.
6. Terminal case: if no next gate exists in the skeleton, drafts nothing, notes feature
   completion in the review summary, and signals the PM agent to take `in_progress →
   done` rather than `in_progress → plan_review`.

`plan-next` **drafts but never arms**. It does not create issues and does not approve a
plan. Arming and approval are the human's, through the existing `plan_review` flow. This
preserves the highest-leverage human checkpoint — catching a misframed gate before it
becomes merged code — which is the boundary the whole orchestrator exists to keep human.

### A.5.3 `plan-review` skill runs per gate

The existing `plan-review` skill (Phase A emission, Phase B re-ingest) is invoked once
per gate rather than once per feature. Its mechanics are unchanged; it now materializes
and re-ingests the *current gate's* slice of the task graph. The per-gate review file is
where the human reads plan-next's `gate-NN-review.md` summary, edits or accepts the
drafted tasks, and arms them.

### A.5.4 New PM anti-pattern

Add to the PM agent's anti-pattern list:

- **Arming a gate it just planned.** The `plan-next` task drafts the next gate; it must
  not create the next gate's issues or approve the plan. Issue creation happens at
  `generating`, after the human's `plan_review → generating` approval. A PM agent that
  plans and self-arms a gate has removed the human checkpoint the gate cycle exists to
  provide.

---

## A.6 The gate review summary (`gate-NN-review.md`)

`plan-next` produces a human-facing review artifact weighted toward **doubt**, not
completeness. Its purpose is to spend the human's review attention where a wrong call is
most expensive — not to demonstrate the planner did good work. A summary that says
"planned 4 tasks, all good" is worse than none: it manufactures false confidence and
trains rubber-stamping. Required parts, in priority order:

- **Decisions & rationale** — the non-obvious calls (task boundaries, ordering, model
  and autonomy choices) and which retrospective/lessons entries drove them.
- **Flagged for attention** — "if you check only three things, check these": where the
  planner was least certain, every assumption made to proceed, each mapped to the task
  it affects.
- **Roadmap anchor** — how this gate serves the feature's stated goal; if the
  retrospective implies the goal itself should change, flagged loudly as an escalation
  rather than silently steering toward a new target. (This is the drift guard: iterative
  per-gate planning can wander from the original intent across many hops; the anchor
  forces the alignment claim into the open where the human can challenge it.)
- **Open questions** — what plan-next could not resolve, each mapped to the draft task
  it affects.

The summary is **advisory and owns no state** (same posture as the RESULT block being
advisory while verification decides done). The `task_graph` owns the graph; the review
points at it.

---

## A.6.1 Autonomy and the per-gate checkpoint

The per-gate arm checkpoint (`in_progress → plan_review`, §A.2) inherits the feature's
existing `autonomy_default` — it is not a new config axis, just the existing `auto` /
`review` / `supervised` vocabulary reaching the gate boundary. Under `review` and
`supervised`, the checkpoint always stops for the human. Under `auto`, plan-next may
**auto-arm** the next gate (create its issues and advance toward `generating`) without
the stop.

### A.6.1.1 Auto-arm is conjunctive and the dangerous edges are non-suppressible

The "automatic" promise is *run unattended through the safe stretches, never through the
dangerous ones.* So auto-arm under `auto` proceeds **only when all of** the following
hold; if **any** fails, the feature drops to the `plan_review` stop regardless of mode:

1. **Structural lint passes** — the drafted gate is dispatchable (schema/cycle/orphan
   checks, five mandatory sections, ordered closing sequence). This is the existing exit
   oracle; it covers "a critical structural element is missing."
2. **The skeleton was not revised** for any not-yet-reached gate (§A.5.2). A revision is
   the mechanical signal of a "major shift" — plan-next noticing it changed the downstream
   plan, rather than introspecting on whether a shift "feels" major.
3. **No task in the drafted gate carries a `supervised` (or auto-forbidden) autonomy
   override.** The existing task-decomposition overrides — sensitive-path tasks (auth,
   PII, payments, key management) forced to `supervised`, `qa_execution` never `auto` —
   survive into auto-armed gates untouched. Auto-arming a *gate* never downgrades the
   per-*task* autonomy the planner already assigned; auth code still stops for the human
   even inside an auto-armed gate.
4. **plan-next raised no `spec_level_blocker`.** This is the irreducible "a critical
   element needs a human decision" case. It is handled by the orchestrator's existing
   escalation mechanism, not by a special auto-mode carve-out: **escalation overrides
   autonomy** everywhere in the system, so an escalating plan-next pulls the human back in
   regardless of mode. The design does not make escalation autonomy-suppressible — which
   it would never want to.

The reason the exception is built from mechanical conditions rather than plan-next's
self-judgment: the agent that drafted the gate is the worst-positioned actor to decide
its own draft is too risky to execute without review — the same reason verification is
the driver's job and not the agent's say-so. A self-assessed "nothing major shifted"
would recreate the premature-`complete` failure mode at the planning layer, where the
blast radius is a whole gate of merged code.

### A.6.1.2 The merge floor sits above autonomy mode

Auto-arm advances a gate toward `generating` and execution; it **never auto-merges.**
The §10 merge gate (branch protection + human on the merge button until the QA loop is
trusted) is unchanged and applies inside every gate, autonomous or not. So even a fully
autonomous feature cannot land code on `main` without the merge checkpoint. Automatic
mode removes the *planning* pause between gates; it does not remove the *merge* pause.

### A.6.1.3 Per-gate autonomy override — tightening only

Autonomy is configurable per gate as well as per feature, but a per-gate override **may
only tighten, never loosen.** The feature's `autonomy_default` is the **ceiling**; a
gate's effective autonomy is the *more restrictive* of (feature default, gate override).
An `auto` feature may force human review on a known load-bearing gate (e.g. the auth
surface); a `review` feature may **not** declare a gate that silently auto-arms. A
per-gate value looser than the feature default is a validation error (§A.7), not an
honored setting.

The override is set at the **arm checkpoint**, not at feature start. At `planning`,
nobody yet knows which gates are load-bearing — that is precisely the prediction the
gate model avoids. But when the human arms gate N+1 (reviewing plan-next's draft and
`gate-NN-review.md`), they have maximum information — the retrospective, the planner's
flagged doubts, the actual drafted tasks — and may tighten *that* gate, or pre-mark a
*later* skeleton gate as review-required, on the spot. A future gate pre-marked
`review` is exactly what makes an `auto` feature stop at that gate (condition 3's
sibling at the gate level). Default inheritance is the feature level; the human tightens
where the information warrants.

This axis is safe to add because it gives no one a new way to *remove* a checkpoint — it
only adds ways to *insert* one, on top of the already-non-loosenable floor of §A.6.1.1.

---

## A.7 Amendment to the feature-frontmatter schema

`feature-frontmatter.schema.json` changes, all additive and backwards-compatible:

1. **`task.type` enum** gains the four closing types: `retrospective`, `lessons`,
   `docs`, `plan-next` (joining the existing four).
2. **`task.gate`** — new optional integer on each task object, naming the gate the task
   belongs to. Absent is treated as gate 1 (so pre-gate features remain valid).
3. **Feature-level `gates`** — new optional array describing the gate skeleton. Each
   entry: `{ gate: <int>, objective: <string>, status: <open|awaiting_review|passed>,
   autonomy?: <auto|review|supervised> }`. The optional `autonomy` is a per-gate
   **tightening-only** override (§A.6.1.3). Absent `gates` means a single implicit gate
   (current whole-feature behavior preserved).
4. **`task.status`** is *not* added — "draft vs armed" continues to be expressed by
   whether the task has a GitHub issue, exactly as today. A drafted-but-unarmed task is
   one present in `task_graph` (with its `gate`) but not yet materialized at
   `generating`.
5. **Per-gate autonomy validation constraint.** A gate's `autonomy`, when present, must be
   **no looser** than the feature-level `autonomy_default`, on the ordering
   `supervised` (most restrictive) > `review` > `auto` (least). A looser value is a
   validation error. JSON Schema cannot express this cross-field comparison directly, so
   it is enforced by `lint_plan.py` / the PM agent's self-check rather than by the schema
   alone — note this explicitly so the gap is not mistaken for permissiveness.

Because every change is additive and the new fields are optional, **a feature with no
`gates` array and only the four original task types validates exactly as before.** The
gate layer is opt-in per feature.

---

## A.8 Amendment to §7.3 — Event types

Minimal additions to the event-type enum, following the existing F3.15 precedent
(register the type and envelope; defer per-type payload schemas):

- **`gate_completed`** — emitted by the PM agent when a gate's closing sequence finishes;
  payload names the gate number and whether a next gate exists.
- **`gate_planned`** — emitted by `plan-next` when it has drafted the next gate;
  payload names the gate number and drafted task count. *(Alternatively, reuse the
  existing `task_graph_drafted` with a `gate` field in its payload — preferred if you
  want zero new event types for the drafting step. `gate_completed` is the only strictly
  new type required.)*
- **`lessons_promoted`** — emitted by a `lessons` task when it appends to `LEARNINGS.md`;
  payload names the count of promoted entries (may be zero). Optional; reuse
  `task_completed` if you prefer not to add it.

`retrospective`, `lessons`, `docs`, and `plan-next` tasks emit the existing
`task_started` / `task_completed` like any task; only the gate-cycle transitions
(`gate_completed`, optionally `gate_planned`) are genuinely new. The
`in_progress → plan_review` feature transition reuses the existing
`feature_state_changed` event with a new `trigger` value (e.g. `gate_completed`).

---

## A.9 Frozen-baseline impact (requires sign-off)

These are the changes to frozen artifacts. They are flagged separately because amending a
frozen baseline requires deliberate sign-off and a version bump, per the project's own
discipline — unlike refining the unexercised single-repo kit, which is free.

- **PM agent → v1.7.0.** Gate identification (Step 0), gate-scoped `task-decomposition`,
  new `plan-next` skill, per-gate `plan-review`, gate-closing remit, the auto-arm
  conjunction (§A.6.1), the per-gate tightening-only autonomy rule, and the new
  anti-pattern. The largest change.
- **`task-decomposition` skill → v1.3** — gains Step 0 (gate identification) and scope
  narrowing to one gate per pass. **`plan-review` skill → v1.3** — runs per gate and is
  the surface where the per-gate autonomy override is set at arm time. **New `plan-next`
  skill → v1.0.**
- **`feature-frontmatter.schema.json`** — additive (§A.7), including the `gates` array
  with optional per-gate `autonomy`. Schemas version with the repo, so no independent
  bump, but it is a contract change all PM skills depend on.
- **`lint_plan.py` / PM self-check** — enforces the per-gate "autonomy no looser than the
  feature default" constraint the schema cannot express (§A.7 item 5), and the auto-arm
  conjunction (§A.6.1.1) as a gate on whether to skip the `plan_review` stop under `auto`.
- **`state-vocabulary.md`** (shared rule) — mirror the one new feature transition and the
  oscillation note; keep it in lock-step with the amended §6.1.
- **`event.schema.json`** — add `gate_completed` (and optionally `gate_planned`,
  `lessons_promoted`) to the enum.
- **`labels.md`** — add `type:retrospective`, `type:lessons`, `type:docs`,
  `type:plan-next` to the type label set.

**What stays frozen and unchanged:** the task state machine (§6.2); the work-unit issue
template's five mandatory sections (§8); `verify-before-report.md`; the component and QA
agent configs and skills; `dependency-recomputation` (it operates on whatever tasks have
issues, gate-agnostic); the merge-gating model (§10). The gate layer sits *above* task
execution and does not perturb it.

**Note on point 1 (orchestrator not yet exercised on real feature work).** The frozen
baselines were frozen against synthetic build-the-orchestrator walkthroughs, not real
feature delivery. That makes them well-formed hypotheses rather than proven behavior, and
it argues for settling the gate model *before* first real use rather than retrofitting it
after the first features bake in the whole-feature planning model.

---

## A.10 Reconciliation with the single-repo kit

The single-repo loop kit and the orchestrator are **two execution surfaces of one
methodology**, sharing one canonical artifact set and one vocabulary. After this addendum
is folded in:

- **Canonical artifacts live in the orchestrator's `/shared/`** and the architecture
  document. The kit consumes them; it does not maintain divergent copies. The kit's
  `WU.template.md` is replaced by `work-unit-issue.md` v1.3; its `result-contract.md`
  becomes a thin emitter of the existing `task_completed` event shape; its
  `verification/SKILL.md` defers to the component agent's frozen verification skill.
- **The gate layer is shared vocabulary**, defined here once and consumed by both
  surfaces. The kit's `PLAN.md` graph, `GATE-NN.md`, closing-WU prompts, `plan-next`
  prompt, and `LEARNINGS.md` are the single-repo *expression* of the concepts this
  addendum makes normative.
- **`loop.py` stays the single-repo implementation** and serves as the reference for the
  orchestrator's still-unbuilt polling loop (no dispatcher exists in `/scripts/` yet).
  Its dispatch/verify/retry/gate-stop semantics are the contract the poller must honor;
  in the orchestrator those behaviors decompose across the poller, PM dependency
  recomputation, and the merge watcher, which the design already separates.
- **The two environment-specific seams remain:** state backend (kit: WU/GATE file
  frontmatter; orchestrator: GitHub issue labels + feature registry) and dispatch (kit:
  subprocess; orchestrator: inbox + poller). The branch/merge strategy genuinely differs
  (a multi-repo feature cannot be one branch) and is meant to.

---

## A.11 Suggested fold-in order

1. Fold §A.2, §A.3, §A.4 into the architecture document (vocabulary, state machine,
   repo layout) — these are definitional and low-risk.
2. Fold §A.7 (schema) and §A.8 (events, labels) — additive contracts.
3. Fold §A.5 / §A.6 into §5 and bump the PM agent and its skills (§A.9) — the behavioral
   change; do this only when you are ready to exercise the gate cycle.
4. Prove the loop single-repo first (it already runs); promote what the single-repo
   gates teach into the orchestrator's `plan-next` skill before first multi-repo use.
