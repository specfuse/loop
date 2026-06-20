# Architecture Addendum — Gates and the iterative planning cycle (Model B)

> **Status: adopted (2026-06).** Gate placement is resolved as **Model B — gates live in the
> loop, per component, NOT in the orchestrator PM.** The gate cycle was proven on a real
> multi-gate feature (loop `FEAT-2026-0003`: plan-next drafted real, armable next gates across
> three cycles). This addendum records that decision and what it means for the orchestrator.
>
> **This supersedes the earlier Model-A proposal** (an earlier revision of this file that
> proposed folding gate identification / `plan-next` / per-gate `plan_review` into the PM agent as
> a `v1.7.0` behavioral change). That fold-in was **not adopted**; the PM does not gain gate
> machinery. See the orchestrator repo's `docs/gate-placement-proposal.md` (Model A vs B, decision
> criteria) and `docs/naming-convention.md` for the canonical contracts.

---

## 1. The decision

The orchestrator coordinates one level above a single-repo goal. An **initiative**
(`INIT-YYYY-NNNN`) is decomposed by the PM into a **`feature_graph`** of **features**
(`INIT-YYYY-NNNN/FNN`), each a single-repo goal dispatched to one component. **Each dispatched
implementation feature == a loop feature**: the receiving component's loop decomposes it into
**gates** and **work units** and grinds it through its gate cycle.

So gates are **internal to the loop**, not orchestrator state. The orchestrator owns
`initiative → feature` decomposition, cross-repo dependency ordering, and the spec/generated
interface contracts between features; it does **not** identify gates, run `plan-next`, or hold a
per-gate `plan_review`. The loop owns all of that, per [`methodology.md`](methodology.md).

**Why Model B (summary).** The loop is single-repo + edit-and-commit; codegen freezes the
cross-repo interface (generated `emit-*`/`on-*` contracts are immutable `_generated/`), so
component-loops grind hand-code against frozen boundaries and cannot break each other. This
dissolves the hardest part of Model A (predicting cross-repo gate boundaries inside the PM) and
keeps the gate cycle built once, in the loop. Full rationale + the rejected Model A:
`gate-placement-proposal.md`.

## 2. What changed in the orchestrator (minimal — no PM gate machinery)

The orchestrator change is the **initiative/feature reframe**, already folded into
`orchestrator-architecture.md` §1A and `naming-convention.md`:

- **Vocabulary / IDs:** initiative → feature → gate → work unit; `INIT-YYYY-NNNN/FNN/TNN`
  (legacy/component-local `FEAT-…/TNN`). Root token = origin.
- **State machines (unchanged in shape):** the "feature state machine" is the **initiative**
  lifecycle; the "task state machine" is the **feature** lifecycle. Gates/WUs do **not** appear in
  the orchestrator's state machines — they are loop-internal.
- **PM agent (reframed, not gate-extended):** `feature-decomposition` (was task-decomposition)
  produces a `feature_graph`; `issue-drafting` files feature issues labelled by type;
  `plan-review` reviews the `feature_graph`; `dependency-recomputation` (runtime `scripts/poller.py`)
  flips features `pending → ready`. **No** gate identification, `plan-next`, or per-gate
  `plan_review` in the PM — those were the Model-A additions and are dropped.
- **Dispatch by feature type:** `implementation` → the component-loop (loop GitHub feature-pick on
  `specfuse:feature`); `qa_*` → the QA agent (`specfuse:qa-feature`), a distinct cross-repo role,
  **not** a loop. QA is the exception to uniform-loop dispatch.
- **Per-gate autonomy / arming** lives in the loop (not the PM): autonomy flows orchestrator →
  loop (`review`/`supervised` stop at each gate for a human arm; `auto` self-arms safe gates under
  the methodology §9 conjunction). The merge gate stays human until the QA loop is trusted.

The orchestrator's earlier "no gates" behavior is therefore not changed by *adding* gates to it —
gates were placed in the loop instead.

## 3. What the loop owns (the gate layer)

Per [`methodology.md`](methodology.md): the gate cycle (plan → execute → close → review&arm), the
four-type closing sequence (`retrospective → lessons → docs → plan-next`), `plan-next` drafting
the next gate (never arming it), `LEARNINGS.md`, and per-gate autonomy. These are **loop-internal**
to each dispatched feature; the orchestrator sees only the feature's overall state (via issue
labels) and its completion (PR merge → merge-watcher → `state:done`).

## 4. Reconciliation with the orchestrator (the surface-specific seams)

Per the collaboration charter §2 / methodology §10, only these differ between surfaces:

| Concern        | Loop (single-repo)                       | Orchestrator (multi-repo)                         |
|----------------|------------------------------------------|---------------------------------------------------|
| State backend  | WU/GATE/PLAN frontmatter, git-tracked    | GitHub issue labels + the initiative registry     |
| Dispatch       | driver shells out (`claude -p`)          | poller routes by type → loop / QA agent           |
| Branch / merge | one branch, squash per WU                | branch + PR per **feature**, merge watcher        |
| Report-back    | RESULT block                             | `task_completed` event (+ `state:*` labels) via the loop's `GitHubBackend` |

The loop's `loop.py` is the reference for the orchestrator's poller (its dispatch/verify/retry/
gate-stop semantics decompose across the poller, PM dependency-recomputation, and the merge
watcher); the orchestrator does not import `loop.py`.

## 5. Status of the old Model-A sections

The prior revision's §A.2–§A.11 (feature-state `in_progress → plan_review` oscillation, gate
skeleton in the PM, `plan-next` as a PM skill, per-gate `plan_review`, the auto-arm conjunction in
the PM, PM `v1.7.0`, the `gates`/`task.gate` frontmatter fields) described **Model A and are not
implemented.** The `feature-frontmatter.schema.json` `gates` array is not used by the orchestrator
(gates are loop-internal). If a future need arises to surface gate state at the orchestrator level,
re-open this addendum deliberately.

## 6. Remaining (gated)

- `specfuse/methodology` extraction — once the gate-cycle contracts stop changing run-to-run
  (charter §4; two contract fixes landed during the FEAT-2026-0003 dogfood — let them soak).
- Loop kit → `stable` in the orchestrator distribution manifest (same soak gate).
