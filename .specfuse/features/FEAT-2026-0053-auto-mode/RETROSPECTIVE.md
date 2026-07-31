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

## Gate 2 — Live arming behind the dial

Gate 2 made `auto` real. Five substantive work units shipped, and the shape
repeated gate 1's module-then-wiring split:

- **T05 — `specfuse/loop/arm_txn.py`.** The pure arm transaction:
  `plan_arm_transaction(feature_dir, just_closed_gate, arm_payload, timestamp)`
  computes the complete write set an arm consists of — every gate-`N+1` draft WU
  flipping to `pending`, gate `N`'s file flipping `awaiting_review → passed`,
  `events.jsonl`, and (T08) `FEATURE-REVIEW.md` — and returns it as one `paths`
  tuple plus the revert tag *name*. `apply_arm_transaction` performs the writes
  and is idempotent. **The module performs no git operation at all**, not even
  creating the tag; that is what makes the one-commit guarantee testable.
- **T06 — the dial goes live.** `loop.py` now reads `autonomy_default` at the
  single `awaiting_review` flip site that can arm, and on `auto` +
  `would_arm: True` it tags `pre-arm/<feature-id>/gate-<N>` at the pre-arm HEAD,
  applies the transaction, and carries every write into the one existing
  bookkeeping commit. The two escalation flip sites `return` before that line, so
  **escalation overrides autonomy by control flow, not by a check that could be
  forgotten**. `docs/dev/auto-arm-recovery.md` documents the reset-to-tag
  recovery.
- **T07 — the severity flip.** `plan_next_lint` is the eighth predicate class and
  the third veto class: under `auto`, `lint_plan_next_draft`'s findings block the
  arm. `lint_plan.py`'s CLI is unchanged and every non-`auto` feature is
  unchanged — the flip lives entirely in the predicate. A `GATE-{N+1}-REVIEW.md`
  whose frontmatter will not parse produces a *fired* verdict naming the parse
  failure rather than an exception, matching T04's `evaluation_error` precedent.
- **T08 — `FEATURE-REVIEW.md` accumulation.** Each auto-arm appends one
  append-only section for the just-closed gate carrying the verbatim
  `open_questions` list, the verbatim `## Doubt` prose, and the per-class verdict
  line — inside the same single arm commit. A `review` or `supervised` feature
  writes no such file. The doubt prose is written *into* the file and is never
  read *by* the predicate; the decoupling PLAN.md required survived contact.
- **T09 — LEARNINGS staging.** Under `auto`, a closing WU whose diff touches
  `.specfuse/LEARNINGS.md` fails the post-pass invariant
  (`assert_learnings_staged_under_auto`, reason `learnings_not_staged`); lessons
  go to a feature-local `LEARNINGS-pending.md` instead, from a new template that
  spells out the human's promotion step at PR review. An unread gate cannot write
  a durable cross-feature rule.

The organizing principle held again, and gained a data point: the eighth class is
a veto class, so the three model-authored channels (`open_questions`,
`human_only`, `provenance`, plus now every plan-next contract finding) can still
only subtract. Every approval input remains a counter, a path, or a hardcoded
constant.

**Gate entry was not clean.** The driver's baseline probe found seven checks
already failing before any gate-2 WU was dispatched (`tests`, `coverage`, and
five bats suites) and escalated `preexisting_gate_failure` at
2026-07-30T21:22:08Z. Zero work units were dispatched for that halt; the operator
probed and cleared it (`chore(loop): gate 2 baseline probed clean`). It cost no
attempt spend, and it is the reason gate 2's first recorded event is an
escalation.

### Oracle re-runs (close-discipline §1)

Every oracle named by T05–T09, re-run fresh in this session against the working
tree, exit codes read directly (`$?` after each command, not after a pipe).
Interpreter: `.venv/bin/python` (3.14.6).

| Oracle | Exit | Result |
| --- | --- | --- |
| `python3 -m unittest tests.test_arm_txn -v` | 0 | Ran 10 tests — OK |
| `python3 -m unittest tests.test_arm_wiring -v` | 0 | Ran 7 tests — OK |
| `python3 -m unittest tests.test_arm_eval_lint_class -v` | 0 | Ran 4 tests — OK |
| `python3 -m unittest tests.test_arm_eval -v` | 0 | Ran 19 tests — OK |
| `python3 -m unittest tests.test_feature_review_accumulation -v` | 0 | Ran 7 tests — OK |
| `python3 -m unittest tests.test_learnings_staging -v` | 0 | Ran 7 tests — OK |
| `python3 -m unittest tests.test_scaffold_data_in_sync -v` | 0 | Ran 4 tests — OK |
| `python3 -c "import specfuse.loop.arm_txn as m; ..."` | 0 | `plan_arm_transaction`, `apply_arm_transaction` both present |
| `python3 -c "from specfuse.loop.arm_eval import CLASS_NAMES, VETO_CLASSES; assert 'plan_next_lint' in CLASS_NAMES and 'plan_next_lint' in VETO_CLASSES"` | 0 | assertion holds; `CLASS_NAMES` now 8 entries, `VETO_CLASSES` 3 |

58 tests, nine commands, zero failures. `tests.test_arm_wiring` runs the real
`loop.run()` inside a temporary git repo, so T06's one-commit claim is verified by
an actual driver invocation and an actual `git rev-list --count`, not by a mock.

**Two oracles beyond the named set**, both run because gate 1's lessons say a
fixture-only proof is a proof of unknown power:

1. **The §4 severity-flip sweep, re-run as a regression check.**
   `evaluate_arm_predicate(d, 1)` over all **43** real `FEAT-*` directories in
   `.specfuse/features/`: `plan_next_lint` returned **0 fired, 1 clean, 42
   not_evaluable, 0 exceptions**. The one `clean` is this feature — the only one
   with a `PLAN.baseline.json`. This is the satisfiability answer T07's body gave
   ("zero on an input already in its intended final state") confirmed on the real
   corpus, and it is also the finding in *What the loop did NOT verify* below: the
   veto's **firing** path has still never executed on a real feature folder.
   (A `*`-glob sweep instead of a `FEAT-*` glob raises `FileNotFoundError` on the
   stray `.specfuse/features/.claude/` scratch directory. Not a defect in the
   predicate — it is not a feature folder — but sweeps should glob `FEAT-*`.)
2. **The predicate run live against this feature.**
   `evaluate_arm_predicate(<this feature>, 2)` returns `would_arm: False` with
   seven classes clean and `open_questions_human_only` fired on
   `GATE-03-REVIEW.md missing` — correct fail-closed behavior at a gate whose
   plan-next has not run. This run is also what surfaced Finding 1 below.

### Consumer-visible contract changes (close-discipline §3)

Gate 2's list is larger than gate 1's and **not purely additive**: item 2 changes
the shape of an existing payload, and items 4, 8 and 9 change existing behavior
rather than adding beside it. Ten items.

1. **New module `specfuse/loop/arm_txn.py`** — public surface
   `arm_tag_name(feature_id, gate)`, `plan_arm_transaction(...)`,
   `apply_arm_transaction(txn)`, `append_feature_review_entry(...)`, dataclass
   `ArmTransaction`, constant `FEATURE_REVIEW_FILENAME`.
2. **The eighth predicate class `plan_next_lint` — the one changed payload.**
   `CLASS_NAMES` goes from 7 entries to 8 and `VETO_CLASSES` from 2 to 3, both
   published from `specfuse/loop/arm_eval.py`. The consequence reaches the wire:
   **every `arm_predicate_evaluated` event's `classes` map now carries eight keys
   instead of seven.** Any consumer that enumerates that map, asserts its length,
   or switches exhaustively over class names sees a changed shape — as does
   anyone diffing two events emitted either side of this commit. Nothing was
   removed or renamed, but this is an existing payload that changed, not a new one
   beside it.
3. **New event type `gate_auto_armed`** in `events.jsonl`, payload
   `{gate, tag, armed_wu_ids, predicate_version}`, appended once per auto-arm.
   Like `arm_predicate_evaluated` it is deliberately absent from
   `event.schema.json`'s `event_type` enum and from `PER_TYPE_SCHEMA_DIR`,
   following the `gate_reached` / `attempt_outcome` precedent. **This is now the
   second unregistered type this feature has added**, which raises the cost of
   FEAT-2026-0060 rather than leaving it flat.
4. **New git tag namespace `pre-arm/<feature-id>/gate-<N>`.** Created with
   `git -c tag.gpgSign=false tag -f` — lightweight, unsigned, and **`-f`, so a
   re-arm of the same gate silently moves an existing tag of that name**. These
   are repo objects: every `git tag`, every `git push --tags`, and every tooling
   pass over the tag list in any Specfuse project running an `auto` feature will
   see them accumulate, one per armed gate.
5. **New per-feature artifact `FEATURE-REVIEW.md`**, written only under `auto`,
   append-only, one section per auto-armed gate.
6. **New per-feature artifact `LEARNINGS-pending.md`**, written only under
   `auto`, the staging destination for lessons an unread gate produced.
7. **New template `LEARNINGS-pending.template.md`**, in *both* scaffold copies
   (`specfuse/loop/data/templates/` and `.specfuse/templates/`, kept in lockstep
   by `test_scaffold_data_in_sync`). It ships to every downstream project on the
   next `init.sh` / upgrade, whether or not that project ever runs `auto`.
8. **New behavior: an `auto` feature's gate flips to `passed` without a human.**
   The bookkeeping commit message changes with it — `chore(loop): gate N
   awaiting_review` becomes `chore(loop): gate N auto-armed gate N+1 (tag
   pre-arm/...)`. Anything grepping the bookkeeping trail for the old string
   (dashboards, `/attention`, ad-hoc operator greps) will miss auto-armed gates.
9. **New closing requirement and a new failure reason.**
   `closing_requirements.py` gains `close-e` / `close-intermediate-e` and the
   constant `LEARNINGS_PENDING_FILENAME`; `loop.py` gains the post-pass invariant
   `assert_learnings_staged_under_auto`, whose refusal reason string is
   `learnings_not_staged`. `specfuse-lint --closing` output changes accordingly.
   Inert outside `auto`, but the requirement registry is a published surface.
10. **New operator doc `docs/dev/auto-arm-recovery.md`** — the one-commit
    atomicity guarantee and the exact `git reset --hard pre-arm/<id>/gate-<N>`
    recovery for the committed-arm case.

The items needing explicit human acknowledgment are **2** (a changed payload on a
stream several tools parse), **4** (repo-visible tags created with `-f`), and
**8** (a commit-message string that existing greps depend on).

## Cost analysis

**Gate 2.** `planned_cost_usd` for gate 2 is **$25.50** across seven units
(T05 $3.50, T06 $3.50, T07 $3.00, T08 $2.50, T09 $2.50,
`G2-CLOSE-INTERMEDIATE` $4.50, `G2-PLAN` $6.00). Actuals are summed from
`attempt_outcome` payloads in `events.jsonl` across **all** attempts, including
every non-passing one and every dispatch cycle before a re-arm (the #221
discipline: blocked burn is spend).

| Unit | Planned | Actual | Delta |
| --- | --- | --- | --- |
| T05 arm transaction | $3.50 | $1.896870 | −$1.60 (−45.8%) |
| T06 dial + verdict wiring | $3.50 | $5.047327 | +$1.55 (+44.2%) |
| T07 lint blocking under `auto` | $3.00 | $9.289682 | **+$6.29 (+209.7%)** |
| T08 `FEATURE-REVIEW.md` | $2.50 | $3.201158 | +$0.70 (+28.0%) |
| T09 LEARNINGS staging | $2.50 | $4.305008 | +$1.81 (+72.2%) |
| **Substantive subtotal** | **$15.00** | **$23.740045** | **+$8.74 (+58.3%)** |
| G2-CLOSE-INTERMEDIATE | $4.50 | in flight | — |
| G2-PLAN | $6.00 | not yet run | — |

**The named delta: substantive work came in $8.74 over a $15.00 estimate, a 58.3%
over-run, and it does not reduce to the one spin.** T07's three wasted attempts
account for $5.01 of it; strip them and the subtotal is still $18.73 against
$15.00, **+24.9%**. T06 and T09 each passed on their **first attempt** and still
landed 44% and 72% over. That is estimate error, not execution error.

**This reverses gate 1's pattern and the three features before it.** Gate 1 came
in −35.8%; `[FEAT-2026-0069/G1-CLOSE]` and `[FEAT-2026-0055/G1-CLOSE]` recorded
the same under-run, and this retrospective's gate-1 section added the third data
point to issue #260 ("implementation estimates read high by roughly a third").
Gate 2 is the fourth data point and it points the other way. The distinguishing
property is legible: gate 1's units were four largely independent modules; gate
2's five units all wire behavior into a live driver and into each other — T07's
new veto class evaluated T06's test fixtures, and T08 extended T05's transaction
after T05 had shipped. **Issue #260's rule should be scoped to independent-module
work rather than to "implementation" as a type**, or it will underestimate every
wiring gate.

**Gate spend against the brake.** `GATE-02.md` sets `cost_budget_usd: 31.50`.
True gate-2 spend to date, from `events.jsonl`, is **$23.74 — 75.4% of the
brake consumed with both closing units still to run** against $10.50 of remaining
plan. If the closing pair repeats gate 1's actuals ($3.35 + $6.68 = $10.03), gate
2 lands near **$33.8, roughly $2.3 over its declared budget**, and the brake will
not have fired: `_should_halt_for_budget` is evaluated *before* each WU dispatch,
so an overrun that happens inside the last WU is structurally invisible to it.

**And the brake is not reading $23.74.** `gate_spent_usd` currently returns
**$18.732186** for gate 2 — $5.01 low. See Finding 1: the same under-count
afflicts the arm predicate's own `budget_projection` class, on this feature, by
$6.23.

### Failure-class breakdown

Six non-passing attempts in gate 2, across three work units, $9.010432 — **38.0%
of substantive gate spend**.

| failure_class | non-passed attempts | dominant signature | spend |
| --- | --- | --- | --- |
| `tests` | 3 | `$ python3 -m unittest discover -s tests -v` (T07, all three) | $5.007859 |
| `lint` | 3 | `$ ruff check specfuse .specfuse/scripts tests scripts` (T07, T08); `B905` (T05) | $4.002573 |

**The `tests` class, named:** *a new validation class firing on a sibling work
unit's fixture*. T07 introduced `plan_next_lint`, which requires a positive
`planned_cost_usd` on every drafted WU. T06's fixture builder in
`tests/test_arm_wiring.py` — authored one work unit earlier, and deliberately
setting `open_questions: []` to be arm-clean — emitted WU frontmatter with no
`planned_cost_usd` at all. So T07's own new veto fired on T06's fixture,
`would_arm` went `False`, and **T06's**
`test_auto_feature_arms_next_gate_in_one_commit` failed. Three attempts across two
dispatch cycles chased it, all reporting the same signature, until the driver
escalated `spinning_signature_repeat` at $5.01 / 774 seconds. The operator
diagnosed the root cause directly against `lint_plan_next_draft`, amended T07's
**Do not touch** to permit adding that one field to the fixture builder, and
re-armed with `re_arm_override: true` (the escalated tree had been discarded on
each attempt, so the signature itself was no longer reproducible). The re-armed
cycle passed on its second attempt.

Two observations:

- **The failing test was in the file the WU was forbidden to touch.** T07's Do-not-touch
  named T06's tests; the signature named the whole suite; nothing in either
  pointed at the fixture builder. Three fresh sessions each re-derived the same
  wrong hypothesis because the evidence available to them was identical and
  misleading. This is the gate's most expensive lesson and it generalizes.
- **The `lint` class is unremarkable and cheap per attempt** ($1.33 average) —
  `B905` (`zip()` without `strict=`), `BLE001` (blind `except`), and one further
  ruff failure on the T07 re-arm. Three separate WUs tripped ruff on first
  submission. That is a pre-flight gap, not a design problem.

## What the loop did NOT verify

Six entries. The first two were known at dispatch and are confirmed, not
displaced, by what this gate found.

1. **No live arm happened on this feature.** FEAT-2026-0053 runs
   `autonomy_default: review` by decision (`[FEAT-2026-0007/G2-LESSONS]` — an
   enforcement mechanism cannot be exercised by the gate that builds it). *Verified
   in-loop:* the whole arm path, by `tests/test_arm_wiring.py` (7 tests) —
   including a run against `_copy_real_feature`, a copy of **this feature's own
   real folder** with its real `PLAN.baseline.json`, real WU frontmatter and real
   `events.jsonl`, rewound to the moment gate 1 is about to close. That satisfies
   T06 AC#6 and it is a genuine driver invocation. *Not verified:* one production
   ride. **Where it is actually verified:** the first `auto` feature dispatched
   after this branch merges.
2. **`drift_caps` is unproven on this feature, and the evidence for that is now
   on disk.** Gate 1's Findings §2 predicted that `PLAN.baseline.json` would be
   captured after this feature's own gate-2 drafting. It was:
   `.specfuse/features/FEAT-2026-0053-auto-mode/PLAN.baseline.json` exists and its
   `gates` list contains gate 1, **gate 2's seven work units, and gate 3's
   `G3-CLOSE` placeholder**. A `drift_caps` verdict measured against that baseline
   compares gate 2 to a baseline that already contains gate 2. **Do not cite this
   feature's clean `drift_caps` as evidence drift detection works.** The honest
   first test is a feature whose first dispatch happens after this branch merges.
3. **`plan_next_lint`'s firing path has never executed on a real feature.** The
   corpus sweep above returns 0 fired / 1 clean / 42 not_evaluable across 43 real
   directories. *Verified in-loop:* firing, quiet, and malformed-frontmatter
   behavior by `tests/test_arm_eval_lint_class.py` (4 tests). *Not verified:* that
   the class fires correctly on a real `GATE-{N+1}-REVIEW.md` and a real drafted
   gate. **Where it is actually verified:** the first `auto` feature that reaches
   a gate boundary with a genuinely non-compliant plan-next draft — which, by
   design, is the case where a human is most needed and least present.
4. **`FEATURE-REVIEW.md` has no reader.** T08's accumulation is verified end to
   end (7 tests, and the file joins the single arm commit). But
   `grep -rn "FEATURE-REVIEW" .specfuse/skills specfuse/loop/data` returns **zero
   matches**: nothing surfaces the file into a PR body, and `/wrap-feature` does
   not know it exists. GATE-02.md's definition of done — "every auto-armed gate's
   doubt reaches the PR read" — is delivered as far as *accumulation*; the last
   hop is unbuilt and currently unowned. **Where it is actually verified:**
   nowhere yet. Flagged for `G2-PLAN` as candidate gate-3 scope.
5. **The `LEARNINGS-pending.md` promotion step has never been performed.** T09's
   template documents a four-step human procedure at PR review; zero
   `LEARNINGS-pending.md` files exist in this repo, so no human has ever run it.
   *Verified in-loop:* the invariant that forces staging, by
   `tests/test_learnings_staging.py` (7 tests). **Where it is actually verified:**
   the PR review of the first `auto` feature.
6. **`budget_projection`'s spend input has never been reconciled against
   `events.jsonl` on any feature.** Until this close, nothing compared the number
   the predicate computes to the number the event log records. Finding 1 is what
   that comparison found.

## Findings

Five, all surfaced by this close.

**1. `budget_projection` under-reads this feature's lifetime spend by $6.23
(14.8%), and the per-gate brake under-reads gate 2 by $5.01.** `arm_eval.py:202`
computes `lifetime_spend = sum(wu["cost_usd"] ...)` and `arm_eval.py:124` reads
only `fm.get("cost_usd")`. It never reads `cumulative_cost_usd` (where
`fold_cumulative_on_rearm` parks a prior dispatch cycle's spend, zeroing
`cost_usd` as it goes) and never reads `re_arm_history[].prior_cost_usd`. On this
feature that is two separate holes:

- **T04** was re-armed through the driver's own fold path:
  `cost_usd: 2.536497`, `cumulative_cost_usd: 1.220458`. The predicate sees
  $2.54 of a $3.76 spend.
- **T07** was re-armed through the operator path, which zeroed `cost_usd` and
  recorded `prior_cost_usd: 5.01` in `re_arm_history` instead. Because
  `detect_rearm_dispatch` returns `False` when `cost_usd == 0`, the fold never
  ran and **no `cumulative_cost_usd` field was ever written**. The predicate sees
  $4.28 of a $9.29 spend — and so does `gate_spent_usd`, which *does* read
  `cumulative_cost_usd` and is therefore blind to this second hole too.

Measured, not inferred: predicate-visible lifetime spend **$35.891552**;
`events.jsonl` lifetime spend **$42.119869**; difference **$6.228317**, exactly
$1.220458 + $5.007859. The live verdict reads `projected spend $51.39 within 2.0x
baseline planned total $54.00 (cap $108.00)` — the true projection is $57.62,
still under the $108.00 cap, so no verdict flips here. **The class is not wrong on
this feature; it is under-informed on every feature, and the error grows with
exactly the thing it exists to catch — re-armed, over-budget work.** Two fixes,
both small: have `arm_eval` sum `cost_usd + cumulative_cost_usd`, and have the
operator re-arm path fold rather than zero. Neither belongs in this close.

**2. The first live `arm_predicate_evaluated` event fired, and gate 1's Findings
§1 disambiguation was right.** The event exists at
`2026-07-30T21:22:08.614225+00:00`, emitted by a driver process launched after
T04's commit. Gate 1 closed with no such event and `GATE-01.md` said to read that
absence as "T04's central claim is false — do not arm; escalate"; gate 1's
retrospective overrode that with "check whether the closing process predates
T04's commit." It did, the mechanism was fine, and the event appeared on the next
invocation. Both corroborating tells resolved the same way:
`PLAN.baseline.json` now exists too. **One caveat for anyone consuming these
events:** this firing came from an *escalation* flip site (the
`preexisting_gate_failure` halt at gate-2 entry), so its payload reads `gate: 2`
and `open_questions_human_only: fired — GATE-03-REVIEW.md missing` for a gate that
had dispatched zero work units. The event means "the predicate was evaluated at a
flip involving gate 2", not "gate 2 closed and would not arm gate 3". T04 wired
all three flip sites deliberately, and T06 keeps escalation sites from arming —
but the payload does not distinguish which site emitted it, and a consumer
grouping these events by gate will mis-read this one.

**3. T07's spin was a cross-work-unit fixture collision that no available
evidence pointed at.** PLAN.md declared T07, T08 and T09 "independent of each
other" because they touch different *source* surfaces. They are not independent
of each other's *fixtures*: T07 introduced a validation class that reads WU
frontmatter, and T06's fixture builder — written before that class existed —
emitted frontmatter the class rejects. The failure surfaced in T06's test file,
which T07 was forbidden to touch, under a whole-suite signature. $5.01 and three
sessions. The fix was one field in one fixture builder.

**4. Gate 2's estimates were wrong in a way gate 1's were not, and the difference
is structural.** Detailed in *Cost analysis*: two first-attempt passes came in 44%
and 72% over. Wiring work that mutates a live driver and interacts with sibling
units does not price like independent-module work, and issue #260's "implementation
runs a third under" rule was derived entirely from the latter.

**5. `FEATURE-REVIEW.md` is written and never read.** The accumulation half of
PLAN.md's "per-gate doubt summaries surfaced in the PR body" shipped; the
surfacing half has no owner in any gate of this feature. Under `auto` this is the
mechanism that replaces four human gate reads with one PR read — so an unread
accumulation file is not a cosmetic gap, it is the checkpoint value silently not
being delivered. `G2-PLAN` should either scope it into gate 3 or record a
deliberate deferral with a home.

## What I'd change

**Draft a new validation class against the fixtures that already exist, before
declaring its work unit independent.** Finding 3 cost $5.01 and one escalation.
The drafting-time check is mechanical and cheap: *this WU adds a rule that reads
artifact X — grep the repo's existing fixtures that produce X, and either confirm
they satisfy the rule or write the fixture amendment into the WU's scope up
front.* T07's body already carried an excellent §2 satisfiability answer for
*real* inputs ("zero on an input already in its intended final state"); the gap
was that test fixtures are inputs too, and they are the ones the gate actually
runs against. This belongs next to `authoring-work-units` §8's cross-surface
check, as its fixture-facing sibling.

**Scope issue #260's estimate rule to independent-module work.** Four data points
now: three under-runs of roughly a third on independent modules, one 58% over-run
on wiring. Leaving the rule attached to "implementation WUs" makes it actively
harmful on the next wiring gate. This is a one-line qualification in
`planning-discipline.md` §5 and in `WU.template.md`'s comment quoting it — but it
is issue #260's owner's call, and this retrospective is adding evidence, not
editing the rule.

**Nothing about the spin's handling.** The driver escalated at exactly the right
point, the operator's root-cause diagnosis was correct, and `re_arm_override:
true` with a written reason was the right instrument for a tree that had been
discarded. The cost was in the drafting, not the recovery.

## Lessons promoted

**This feature runs `autonomy_default: review`, so T09's staging invariant is
inert here and these lessons go to the durable `.specfuse/LEARNINGS.md` as
usual** — no `LEARNINGS-pending.md` was created, and none should have been. Saying
so explicitly because this gate is the one that built the staging mechanism:
the mechanism was not bypassed, it correctly did not apply. Its first real
exercise belongs to the first `auto` feature.

Three entries appended to `.specfuse/LEARNINGS.md` under
`[FEAT-2026-0053/G2-CLOSE]`: a new validation rule must be drafted against the
fixtures that already exist, not only against real inputs; a cost aggregate that
reads a per-cycle field silently under-counts every re-armed unit, and the error
concentrates in exactly the work the aggregate exists to catch; and an
accumulation artifact with no reader delivers none of the checkpoint value it was
built to preserve.

