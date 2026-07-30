# Retrospective — FEAT-2026-0053, Autonomous feature mode

## Gate 1 — Arm predicate + machine-readable contract (shadow trail live)

Gate 1 built the machinery `auto` needs and wired none of its behavior. Four
substantive work units shipped:

- **T01 — `specfuse/loop/plan_baseline.py`.** `write_baseline_if_absent` /
  `load_baseline` over a `PLAN.baseline.json` snapshot of the as-activated plan
  graph (per gate: gate number; per WU: `id`, `type`, goal line,
  `planned_cost_usd`). Write-once by construction — a second call against an
  existing file is a byte-identical no-op even after PLAN.md mutates, because a
  refreshable baseline is a drift detector that can be gamed by drifting.
- **T02 — plan-next contract fields.** `open_questions` (required list in
  `GATE-{N+1}-REVIEW.md` frontmatter), `human_only`, `provenance` documented in
  both `WU.template.md` copies and covered by WARN-only checks in
  `lint_plan_next_draft`. Nothing blocks in this gate.
- **T03 — `specfuse/loop/arm_eval.py`.** `evaluate_arm_predicate(feature_dir,
  just_closed_gate) -> ArmDecision`, pure and side-effect-free, mirroring
  `gate_eval.py`'s shape without sharing its code. Seven classes —
  `budget_projection`, `judge_editing`, `decision_class_paths`,
  `retroactive_edits`, `drift_caps`, `missing_provenance`,
  `open_questions_human_only` — each returning fired / clean / not_evaluable
  with a human-readable reason. `baseline is None` short-circuits every class to
  `not_evaluable: no_baseline` and the overall verdict to `would_arm: False`.
- **T04 — shadow wiring.** `write_baseline_if_absent` at the top of `run()`;
  `build_arm_predicate_event` at all three `awaiting_review` flip sites in
  `loop.py`, appending one `arm_predicate_evaluated` event per close. Control
  flow after the append is verdict-independent, and a predicate exception
  degrades to an `evaluation_error` payload rather than crashing the close.

The organizing principle held: nothing model-authored can approve. The two veto
classes (`missing_provenance`, `open_questions_human_only`) are the only places
a drafting model's output reaches the verdict, and both can only subtract.

### Oracle re-runs (close-discipline §1)

Every oracle named by T01–T04, re-run fresh in this session against the working
tree, exit codes read directly. Interpreter: `.venv/bin/python` (3.14.6).

| Oracle | Exit | Result |
| --- | --- | --- |
| `python3 -m unittest tests.test_plan_baseline -v` | 0 | Ran 4 tests — OK |
| `python3 -m unittest tests.test_lint_plan_contract_fields -v` | 0 | Ran 5 tests — OK |
| `python3 -m unittest tests.test_arm_eval -v` | 0 | Ran 19 tests — OK |
| `python3 -m unittest tests.test_arm_eval_wiring -v` | 0 | Ran 3 tests — OK |
| `python3 -m unittest tests.test_scaffold_data_in_sync -v` | 0 | Ran 4 tests — OK |
| `python3 -c "from specfuse.loop.plan_baseline import write_baseline_if_absent, load_baseline"` | 0 | both symbols import |
| `python3 -c "from specfuse.loop.arm_eval import evaluate_arm_predicate"` | 0 | symbol imports |

35 tests, seven commands, zero failures. T03's AC3 (≥14 focused cases, one
firing and one quiet per class) is satisfied at 19.

**One oracle beyond the named set,** run because `[FEAT-2026-0055/G1-CLOSE]`'s
lesson says a rule proven only on fixtures is a rule of unknown power: this
close ran `evaluate_arm_predicate` over **all 43 real feature directories in
`.specfuse/features/`**. Result: 43 of 43 returned `would_arm: False` with all
seven classes `not_evaluable: no_baseline`, zero exceptions. That is the
designed fail-closed behavior (T03 AC4) confirmed on the real corpus rather than
on fixtures — and it is also the finding in *What the loop did NOT verify*
below: the predicate's approval path has never executed against a real feature
directory, only against fixtures, because no feature has a baseline yet.

### Consumer-visible contract changes (close-discipline §3)

Additive across the board — nothing removed, nothing renamed, no existing
behavior altered. Five items, of which items 4 and 5 are visible to every
downstream Specfuse project, not just this repo:

1. **New module `specfuse/loop/plan_baseline.py`** — public surface
   `write_baseline_if_absent(feature_dir, plan)`, `load_baseline(feature_dir)`,
   `load_plan_graph(feature_dir)`, constant `BASELINE_FILENAME`.
2. **New module `specfuse/loop/arm_eval.py`** — public surface
   `evaluate_arm_predicate(feature_dir, just_closed_gate)`, dataclasses
   `ArmDecision` / `ClassVerdict`, constants `PREDICATE_VERSION = "v1"`,
   `BUDGET_PROJECTION_MULTIPLIER = 2.0`, `DRIFT_CAP_RATIO = 0.5`,
   `ADDED_GATE_CAP = 1`, `JUDGE_PATHS`, `CLASS_NAMES`, `VETO_CLASSES`.
3. **Three template-documented frontmatter fields.** `human_only` (optional,
   per-WU) and `provenance` (optional, per-WU) in `WU.template.md`;
   `open_questions` documented there as living in `GATE-{N+1}-REVIEW.md`
   frontmatter. Both template copies carry them. All three are advisory in gate
   1 — the lint WARNs, never blocks. **Gate 2 flips `open_questions` to blocking
   under `auto` only; that is the severity flip and it needs its own
   satisfiability answer and runtime probe.**
4. **New event type `arm_predicate_evaluated`** in `events.jsonl`, payload
   `{gate, would_arm, predicate_version, classes: {<name>: {status, reason}}}`
   or `{gate, would_arm: null, evaluation_error}` on a degraded evaluation.
   Every consumer that walks `events.jsonl` (`gate-status`,
   `learnings-suggest`, the harvester, any project-local reader) will now see
   this type. It is deliberately absent from `event.schema.json`'s
   `event_type` enum and from `PER_TYPE_SCHEMA_DIR`, matching the existing
   precedent of `gate_reached` and `attempt_outcome` — see the deferral note in
   *Findings* below and FEAT-2026-0060.
5. **New per-feature artifact `PLAN.baseline.json`**, written once at the first
   dispatch of any feature and committed by the driver as
   `chore(loop): <feature-id> plan baseline snapshot`. Every Specfuse project
   that runs a driver at or past 0.7.1 will start seeing this file appear in
   its feature folders and in its git history.

Consumer-visible does not mean breaking here: every existing consumer that
ignores an unknown event type or an unknown file is unaffected, and no field
was removed from any existing payload. The item needing explicit human
acknowledgment is **4** — a new event type on a stream several tools parse.

## Cost analysis

`planned_cost_usd` for gate 1 is **$23.50** across six units (T01 $2.50, T02
$3.00, T03 $4.50, T04 $3.00, `G1-CLOSE-INTERMEDIATE` $4.50, `G1-PLAN` $6.00).
Actuals below are read from `attempt_outcome` payloads in `events.jsonl`, summed
across **all** attempts including the non-passing one (the #221 discipline:
blocked burn is spend).

| Unit | Planned | Actual | Delta |
| --- | --- | --- | --- |
| T01 plan baseline | $2.50 | $1.128055 | −$1.37 (−54.9%) |
| T02 contract fields | $3.00 | $1.444301 | −$1.56 (−51.9%) |
| T03 arm predicate | $4.50 | $2.021300 | −$2.48 (−55.1%) |
| T04 shadow wiring | $3.00 | $3.756955 | +$0.76 (+25.2%) |
| **Substantive subtotal** | **$13.00** | **$8.350611** | **−$4.65 (−35.8%)** |
| G1-CLOSE-INTERMEDIATE | $4.50 | in flight | — |
| G1-PLAN | $6.00 | not yet run | — |

**The named delta: substantive work came in $4.65 under a $13.00 estimate, a
35.8% under-run, and the entire T04 overrun is one blocked attempt.** T04's
$3.76 splits as $1.220458 on the attempt that blocked and $2.536497 on the
re-armed pass; without the block it would have landed at $2.54 against $3.00,
in family with its three siblings. Gate spend against `GATE-01.md`'s
`cost_budget_usd: 28.00` brake stands at $8.35 — 30% consumed with two closing
units left.

The shape is the same one `[FEAT-2026-0069/G1-CLOSE]` and
`[FEAT-2026-0055/G1-CLOSE]` recorded: implementation WUs run well under
estimate (three first-attempt passes at ~45–48% of estimate), and the variance
that matters is elsewhere. This is the third consecutive feature where
implementation estimates read high by roughly a third. That is now a pattern
with three data points, tracked as **issue #260** against
`planning-discipline.md` §5 and `WU.template.md`'s comment quoting it; this
retrospective adds the third point rather than re-opening the argument.

Whether the closing floor over-runs again is not knowable from inside this unit
— `G1-CLOSE-INTERMEDIATE` cannot read its own final cost, and `G1-PLAN` has not
run. G1-PLAN should state the closing-pair actual against $10.50 in
`GATE-02-REVIEW.md`, which is the first surface that can see both.

### Failure-class breakdown

One non-passing attempt in gate 1.

| failure_class | non-passed attempts | dominant signature |
| --- | --- | --- |
| null (agent-reported block, driver assigns no class) | 1 | `FEAT-2026-0053/T04` attempt 1 — cross-surface contract mismatch: per-type event-schema registry |

**The class, named:** *undeclared cross-surface contract*. T04 attempt 1 fired
escalation trigger 2 correctly. It found that `validate_event.py`'s
`PER_TYPE_SCHEMA_DIR` holds four schemas, all core-orchestrator types vendored
from another repo, and that `event.schema.json`'s `event_type` enum is a closed
28-entry list this repo does not own — so there was no sanctioned in-repo
mechanism to register `arm_predicate_evaluated`. It stopped instead of inventing
one. Cost: **$1.220458, 209.9 seconds, 14.6% of substantive gate spend.**

Resolution was an operator decision, not a fix: AC#2 was narrowed to drop the
schema requirement (`re_arm_dispatched`, reason *"AC#2 narrowed to drop the
schema requirement; registry gap tracked separately"*), on the ground that
`gate_reached` and `attempt_outcome` already sit outside both surfaces and the
driver's emit path never invokes the validator. The gap itself became
**FEAT-2026-0060** on the roadmap.

Two observations worth carrying, neither of which is a criticism of the WU:

- **The block was correct and cheap, and the cost is still real.** $1.22 bought
  the discovery that the event-schema registry is unowned — which is exactly
  what a drafting-time cross-surface check (authoring §8) is supposed to buy for
  free. The WU body cited `close-discipline.md` §4 for the review-file naming
  contract but not the event-schema surface, because nobody knew to look there.
- **The driver recorded `failure_class: null` for it.** An agent-reported block
  produces `outcome: blocked` with no class, so this attempt is invisible to
  any cost analysis grouped by `failure_class` — the same blind spot
  `[FEAT-2026-0055/G1-CLOSE]` recorded from the other direction. The class
  above is named by this close, by hand; nothing mechanical produced it.

## What the loop did NOT verify

Two entries, and they share one root cause.

1. **"Every gate close on any feature in this repo emits one
   `arm_predicate_evaluated` event carrying the full per-class evaluation"**
   (GATE-01.md definition of done, T04 AC#2). *Verified in-loop:* the emission
   path, the payload shape, verdict-independence of control flow, and the
   `evaluation_error` degradation, all by `tests/test_arm_eval_wiring.py` (3
   tests, exit 0). *Not verified:* a single live emission. **Why:** the event
   for gate 1 fires at the `awaiting_review` flip, which happens after this unit
   and after `G1-PLAN` — this unit cannot observe it by construction, as the WU
   body states. **Where it is actually verified:** the human's *First-firing
   check* in `GATE-01.md`'s arming discipline, before gate 2 is armed. **Read
   the caveat in Findings §1 before treating an absent event as a false claim.**

2. **"The plan baseline snapshot exists and is immutable after first dispatch"**
   (GATE-01.md definition of done). *Verified in-loop:* the module — write,
   no-op-on-second-call, byte-identity after PLAN mutation, `None` on absence —
   by `tests/test_plan_baseline.py` (4 tests, exit 0). *Not verified:* that the
   T04 wiring actually produces a baseline on a real driver run. **Evidence it
   has not yet happened:** `PLAN.baseline.json` exists in **0 of 43** feature
   directories, this feature's included. The call site sits at the top of
   `run()` and the currently-running driver process was launched before T04's
   code landed, so it is executing the pre-T04 module. **Where it is actually
   verified:** the next driver invocation on any feature — the file appears, or
   the wiring is wrong. Confirmable in one command:
   `ls .specfuse/features/*/PLAN.baseline.json`.

Both entries are the same shape: **a work unit that wires new code into the
driver cannot be verified by the driver run that produced it.** That is not a
WU authoring defect; it is a property of editing a long-running process's
source from inside it. Two of gate 1's five definition-of-done criteria (40%)
land here, which crosses this unit's 30% threshold — flagged under *What I'd
change*.

Everything else in the gate was verified in-loop: the contract fields
(`tests/test_lint_plan_contract_fields.py`, `tests/test_scaffold_data_in_sync.py`),
the predicate's seven classes (`tests/test_arm_eval.py`, 19 cases), and this
close's own obligations.

## Findings

Three, all surfaced by this close, all of which change what the human should do
at the arming checkpoint.

**1. An absent `arm_predicate_evaluated` event at gate 1 is ambiguous, and
`GATE-01.md` currently reads it as unambiguous.** The arming discipline says:
*"No event = T04's central claim is false — do not arm; escalate."* That
inference does not hold on this gate. The driver imports `loop.py` at process
start; the process now running was launched at the T04 re-arm (2026-07-30
~20:40 UTC) and T04's edits landed inside it (~20:50 UTC), so this process is
running pre-T04 bytecode and **will not call `build_arm_predicate_event` no
matter how correct T04 is.** The corroborating evidence is item 2 of the
deferral list: the baseline write, wired at the same time into the same `run()`,
has also not fired.

*Disambiguation before escalating:* if `events.jsonl` carries no
`arm_predicate_evaluated` event for gate 1, check whether the driver process
that closed the gate predates T04's commit. If it does, the correct response is
to re-run the driver, not to escalate — the first-firing check then belongs to
gate 2's close. If a driver process started *after* T04's commit closes a gate
and still emits nothing, the escalation stands as written.

**2. This feature's own baseline will be captured after its own drift.**
`write_baseline_if_absent` snapshots at first dispatch. FEAT-2026-0053's first
dispatch was 2026-07-30T19:13Z, long before T04 landed the call site, so no
snapshot exists. The next driver invocation will write one — from PLAN.md *as it
then reads*, which after `G1-PLAN` runs will already contain gate 2's drafted
work units. The "as-activated graph" recorded for this feature will therefore
be the post-drift graph, and `drift_caps` / `retroactive_edits` will measure
gate 2's arming against a baseline that already contains gate 2. The predicate
will report clean and mean nothing.

This is not a defect in T01 or T04 — both do exactly what they say. It is the
self-reference every mechanism has on the feature that installs it, and it is
worth naming here because gate 2 is where the dial goes live. **Gate 2 must not
treat this feature's own baseline as evidence that drift detection works.** The
honest first test of `drift_caps` is a feature whose first dispatch happens
after this branch merges.

**3. The predicate's approval path has never run on real input.** 43 of 43 real
feature directories return `not_evaluable: no_baseline` on every class. The
fixture suite proves each class can fire and stay quiet; the corpus proves the
fail-closed path is correct at scale. Neither proves that a real feature
directory — with its actual WU frontmatter shapes, its real `events.jsonl`, its
real review file — reaches `would_arm: True` for the right reasons. Given
`[FEAT-2026-0055/G1-CLOSE]`'s finding that a document-parsing rule tested only
on hand-authored fixtures fired on zero real work units, this is the gate-2
risk to plan against: the first real baseline is also the first real input the
seven classes have ever parsed.

## What I'd change

**Size the gate so its own wiring can be observed.** Two of five
definition-of-done criteria (40%, over this unit's 30% threshold) could only be
verified by tests, because both assert runtime behavior of the driver process
that was executing the gate. The gate cut is defensible — T04 genuinely
belonged in gate 1, and splitting "wire it" from "watch it fire" across gates
would have been worse — but the *definition of done* was written as though the
close could observe them, and it cannot. The fix is at drafting: when a DoD
criterion asserts driver runtime behavior, write the observation point into the
criterion ("verified at the next driver invocation / by the human at the arming
checkpoint"), so the close is not left choosing between a false claim and an
unexplained gap. `GATE-01.md`'s first-firing check half-anticipated this and
then drew the wrong inference from an absent event, which is the same mistake in
a different place.

**Add the event-schema surface to the drafting cross-surface check.** T04's
$1.22 block was a correct stop on a contract nobody had enumerated. The WU body
verified the review-file naming contract against `close-discipline.md` §4 before
locking a check — exactly right — but no equivalent existed for "this WU emits a
new event type." One line in the authoring guidance ("emitting a new event type?
check `event.schema.json`'s enum and `PER_TYPE_SCHEMA_DIR` first") would have
converted a blocked attempt into a drafting-time scope decision.

**Nothing about the estimates.** The 35.8% under-run is the third data point on
issue #260 and needs no per-feature response.

## Lessons promoted

Three entries appended to `.specfuse/LEARNINGS.md` under `[FEAT-2026-0053/G1-CLOSE]`:
the driver cannot verify its own freshly-wired code within the run that wired it;
a lifecycle-triggered baseline is meaningless for the feature that installs it;
and a predicate whose corpus sweep is uniformly `not_evaluable` has a proven
refusal path and an unproven approval path.
