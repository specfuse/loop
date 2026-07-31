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

## Gate 3 — Terminal: docs, methodology, and the result made legible

Gate 3 made the feature readable by someone who did not build it, and closed the
one hop gate 2 found missing. Four substantive work units shipped:

- **T10 — `docs/methodology.md` §9 rewritten.** The old §9 was eleven lines
  written before any of this feature existed; its four auto-arm conditions
  described a design that was never built. §9 now describes the eight-class
  predicate, the single flip site that can arm, the one-commit-plus-tag
  guarantee (concept here, procedure in `docs/dev/auto-arm-recovery.md`), the
  three real human checkpoints, and the two `auto`-only artifacts. **The two
  claims with no implementation are recorded as unbuilt rather than deleted:**
  the per-gate tightening-only override (nothing reads a per-gate autonomy
  field) and `supervised` as a level distinct from `review` (every consumer
  branches on `== "auto"`).
- **T11 — `docs/concepts/autonomy-stop-classes.md`.** One section per class in
  `CLASS_NAMES` order, each naming what it measures, what makes it fire, whether
  it is a veto channel, and **the concrete operator action that clears it** —
  eight classes, eight clearing actions. The three statuses are explained with
  `not_evaluable` named as the fail-closed path an operator will actually meet,
  and the page teaches reading an `arm_predicate_evaluated` event, including the
  trap gate 2's Findings §2 recorded: a payload's `gate` field means "the
  predicate was evaluated at a flip involving gate N", not "gate N closed and
  would not arm gate N+1".
- **T12 — `docs/concepts/adopting-auto-mode.md`.** The artifact inventory, the
  three consumer-breakage items gate 2 flagged for acknowledgment, the mid-life
  baseline hazard stated as a property of every feature predating this one
  rather than a quirk of `FEAT-2026-0053`, and a numbered opt-in procedure with
  both back-out paths. Merge stays human, stated without exception.
- **T13 — `FEATURE-REVIEW.md` reaches the PR.** `/wrap-feature`'s step 3 no
  longer relies on `gh pr create --fill`; when the feature folder holds
  `FEATURE-REVIEW.md` and/or `LEARNINGS-pending.md` it opens the PR with an
  explicit `--body-file` carrying their content plus the promotion pointer. Both
  skill copies edited in lockstep. This is the scope-boundary revision G2-PLAN
  declared and the operator accepted at arming; it closes gate 2's Findings §5.

**What a green suite proves here, and what it does not.** Three of the four
units deliver prose. `python3 -m unittest discover -s tests -v` at 1969 tests
proves that the mirrored scaffold copies byte-match their canonical originals,
that every new page is registered in all four scaffold registries, that both
`/wrap-feature` copies are identical, and that nothing regressed. **It proves
nothing about whether the prose is correct.** `GATE-03.md`'s definition of done
says so in the same words and names the human at PR review as the oracle for
correctness; this close repeats it rather than letting a green suite imply more
than it carries. One concrete instance found while reading the shipped text:
methodology §9 cross-references its siblings as "T11's stop-class reference" and
"T12's migration guide" — correlation IDs that mean nothing to a downstream
reader who has only the docs — and describes `FEATURE-REVIEW.md` as "the
closing-gate review a human would otherwise have written by hand" when it is in
fact the accumulated per-gate doubt. Both are prose defects that every oracle
passed. Neither is fixed here: `docs/methodology.md` is T10's surface and this
close does not edit source files owned by T01–T13.

### Oracle re-runs (close-discipline §1)

Every oracle T10–T13 name, re-run fresh in this session against the working
tree, exit codes read directly (`$?` after the command, never after a pipe).
Interpreter: `.venv/bin/python` (3.14.6).

| Oracle | Exit | Result |
| --- | --- | --- |
| `python3 -m unittest discover -s tests -v` | 0 | Ran 1969 tests — OK (skipped=3) |
| `python3 -m unittest tests.test_scaffold_data_in_sync -v` | 0 | Ran 4 tests — OK |
| `python3 -m unittest tests.test_skills_vendored_in_sync -v` | 0 | Ran 4 tests — OK |
| T11 AC#1 class-coverage assertion (`CLASS_NAMES` vs the page) | 0 | printed `[]` — all eight classes present |
| T10 AC#1 `grep -c "not-yet-reached skeleton was not revised" docs/methodology.md` | 1 | printed `0` — zero matches, which is the criterion; grep exits 1 on no match |
| T13 AC#1 `grep -rn "FEATURE-REVIEW" plugins/specfuse/skills/wrap-feature/SKILL.md` | 0 | 3 matches (lines 135, 143, 239) — the zero-match finding no longer reproduces |
| T12 AC#1 inventory greps (eight literal names) | 0 | all eight present in `docs/concepts/adopting-auto-mode.md` |
| `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0053-auto-mode` | 0 | structurally valid |

**One honesty note about how the suite was run, because close-discipline §1 is
about exit codes actually observed.** The first full-suite run in this session
exited **1** with 11 errors — every one of them `git commit` returning 128 with
`error: Couldn't get agent socket` inside a test's throwaway temp repo. The
cause is environmental, not a regression: this session's sandbox denies access
to the SSH signing-agent socket, and the temp repos inherit the host's
`commit.gpgsign`. The env-var escape is closed by design — `tests/__init__.py`'s
`scrub_git_env()` deletes `GIT_CONFIG_GLOBAL` at import so no injected config
survives. The suite was therefore re-run with the sandbox lifted, which is the
same environment the driver verifies in, and exited **0** across 1969 tests. The
table above records that run. The 11 sandbox errors were confined to
`test_autosync_no_cwd_leak` (3) and `test_lint_closing` (8) and touched nothing
this gate produced.

**Two oracles beyond the named set**, run because both prior gates' lessons say
a fixture-only proof is a proof of unknown power:

1. **The corpus sweep, third consecutive run.** `evaluate_arm_predicate(d, 1)`
   over all **43** real `FEAT-*` directories: zero exceptions, zero `would_arm`,
   **1 evaluable and 42 `not_evaluable: no_baseline`** on every class. Unchanged
   from gate 2, and the count of features carrying a `PLAN.baseline.json` is
   still **1 of 43** — this feature. `plan_next_lint` remains 0 fired / 1 clean /
   42 not_evaluable; its firing path has still never executed on a real folder.
2. **The predicate run live against this feature at the terminal gate.**
   `evaluate_arm_predicate(<this feature>, 3)` returns **`would_arm: True`** with
   all eight classes clean — `open_questions_human_only` reads "terminal gate: no
   drafted successor". Recorded because it is the first `would_arm: True` this
   feature has ever produced against a real folder, and because it is
   inconsequential: at a terminal gate there is nothing to arm, and the feature
   runs `review`.

**The predicate's firing path did execute on real input during this gate, and
the event is on disk.** The `arm_predicate_evaluated` event at
`2026-07-31T03:06:03.211684+00:00` — emitted at gate 2's close against gate 3's
drafted WUs — carries `judge_editing: fired` naming T10, T11 and T12 by the
mirrored copies they produce under `specfuse/loop/data/docs/`, and
`open_questions_human_only: fired` on `GATE-03-REVIEW.md`'s five open questions.
That is the v1 path-prefix approximation `GATE-03.md` predicted, observed firing
on a real feature folder rather than on a fixture, and it is the strongest
evidence this feature produced that the refusal path works end to end on real
input. It also demonstrates the limit in *What the loop did NOT verify* below:
under `auto`, that verdict would have parked this gate.

### Consumer-visible contract changes (close-discipline §3)

Gate 3 adds three items. It is **not** `n/a`: T13 changes what a shipped skill
does, and two new pages ship to every downstream project.

1. **`/wrap-feature` opens PRs differently.** Step 3 previously ran
   `gh pr create --fill --base <resolved_base>` unconditionally. It now checks
   the feature folder for `FEATURE-REVIEW.md` and `LEARNINGS-pending.md` and,
   when either is present, opens the PR with an explicit `--body-file` carrying
   their content and the promotion pointer. **When neither file is present the
   behavior is byte-for-byte what it was** — `--fill`, same resolved base, same
   single-confirm posture — so every `review` and `supervised` feature's wrap is
   provably untouched. The change ships in both copies
   (`plugins/specfuse/skills/wrap-feature/SKILL.md` canonical,
   `.specfuse/skills/` vendored) and therefore reaches every downstream project
   on its next upgrade, including projects that will never run `auto`. Skill
   version block goes to `v0.4`.
2. **Two new pages under `docs/concepts/`** —
   `autonomy-stop-classes.md` and `adopting-auto-mode.md` — each mirrored into
   `specfuse/loop/data/docs/concepts/` and registered in **four** scaffold
   registries (`DOCS_TRACKED` in `test_scaffold_data_in_sync.py`, plus the
   expected-file lists in `test_init_integration.py`, `test_scaffold_init.py`
   and `test_scaffold_resources.py`). They appear in every downstream project's
   `docs/` tree on the next `init.sh` / upgrade.
3. **`docs/methodology.md` §9 replaced.** A shipped, mirrored document whose
   content changed substantively rather than being extended. Anyone who quoted,
   linked into, or diffed §9 sees a rewrite, and two statements it used to make
   (the per-gate tightening-only override, `supervised` as a distinct level) are
   now explicitly labelled unbuilt.

Nothing was removed or renamed. The item needing explicit human acknowledgment
is **1** — a behavior change in a skill that ships to projects which never opted
into `auto`, gated on a file's presence rather than on the autonomy dial.

### Consolidated contract-change list — all three gates (close-discipline §3)

Eighteen items, presented here as one list for the explicit human acknowledgment
§3 requires. Gate 1's five and gate 2's ten are stated verbatim in their own
sections above and are **not** re-derived here; this is the index plus the
acknowledgment set.

| # | Gate | Item | Shape |
| --- | --- | --- | --- |
| 1 | 1 | `specfuse/loop/plan_baseline.py` — new module | additive |
| 2 | 1 | `specfuse/loop/arm_eval.py` — new module, constants published | additive |
| 3 | 1 | `human_only`, `provenance`, `open_questions` template fields | additive, WARN-only |
| 4 | 1 | **`arm_predicate_evaluated` — new event type on `events.jsonl`** | additive, **acknowledge** |
| 5 | 1 | `PLAN.baseline.json` — new per-feature artifact + its commit | additive |
| 6 | 2 | `specfuse/loop/arm_txn.py` — new module | additive |
| 7 | 2 | **`classes` map goes 7 keys → 8 (`plan_next_lint`)** | **changed payload, acknowledge** |
| 8 | 2 | `gate_auto_armed` — new event type | additive |
| 9 | 2 | **`pre-arm/<feature-id>/gate-<N>` tags, created with `-f`** | **new repo objects, acknowledge** |
| 10 | 2 | `FEATURE-REVIEW.md` — new per-feature artifact (`auto` only) | additive |
| 11 | 2 | `LEARNINGS-pending.md` — new per-feature artifact (`auto` only) | additive |
| 12 | 2 | `LEARNINGS-pending.template.md` — ships to every downstream project | additive |
| 13 | 2 | **Bookkeeping commit message changes on an auto-armed gate** | **changed string, acknowledge** |
| 14 | 2 | `close-e` / `close-intermediate-e`, `learnings_not_staged` | additive |
| 15 | 2 | `docs/dev/auto-arm-recovery.md` — new operator doc | additive |
| 16 | 3 | **`/wrap-feature` opens PRs with `--body-file` when the two `auto` artifacts exist** | **changed behavior, acknowledge** |
| 17 | 3 | Two new `docs/concepts/` pages, mirrored and registered in four registries | additive |
| 18 | 3 | `docs/methodology.md` §9 rewritten | changed content |

**The acknowledgment set is five items: 4, 7, 9, 13, 16.** Gate 1 named 4; gate 2
named 7, 9 and 13 by name and this close carries them forward unchanged; gate 3
adds 16. Items 7, 9 and 13 are the ones that can break a working consumer
silently — a length assertion on the `classes` map, a tag namespace that moves
under `-f`, and a grep on the old bookkeeping string. Item 16 is the one that
reaches projects with no `auto` feature at all. Item 4's exposure has grown since
gate 1 stated it: two unregistered event types now exist rather than one, which
is why FEAT-2026-0060 costs more than it did.

## Cost analysis

**Gate 3.** `planned_cost_usd` for gate 3 is **$17.00** across five units (T10
$3.00, T11 $3.00, T12 $3.00, T13 $3.00, `G3-CLOSE` $5.00), against `GATE-03.md`'s
`cost_budget_usd: 22.00`. Actuals are summed from `attempt_outcome` payloads in
`events.jsonl` across **all** attempts, including the non-passing one (the #221
discipline: blocked burn is spend).

| Unit | Planned | Actual | Delta |
| --- | --- | --- | --- |
| T10 methodology §9 | $3.00 | $0.437655 | −$2.56 (−85.4%) |
| T11 stop-class reference | $3.00 | $1.761523 | −$1.24 (−41.3%) |
| T12 migration + opt-in | $3.00 | $0.884682 | −$2.12 (−70.5%) |
| T13 `FEATURE-REVIEW.md` reaches the PR | $3.00 | $0.827049 | −$2.17 (−72.4%) |
| **Substantive subtotal** | **$12.00** | **$3.910909** | **−$8.09 (−67.4%)** |
| G3-CLOSE | $5.00 | in flight | — |

**The named delta: substantive work came in $8.09 under a $12.00 estimate, a
67.4% under-run — the largest of the three gates in both directions.** Gate-3
spend against the $22.00 brake stands at **$3.91, 17.8% consumed**, with only
this close left. No attempt in this gate exceeded $2.00.

**This is the fifth data point on issue #260, and it splits the same way gate 2
predicted.** Gate 1 (four largely independent modules) ran −35.8%; gate 2 (five
units wiring behavior into a live driver and into each other) ran +58.3%; gate 3
(three documentation units and one narrow skill edit, sharing only two append-only
lists) runs −67.4%. Gate 2's Finding 4 argued the rule should be scoped to
*independent-module* work rather than to "implementation" as a type; gate 3 is
independent-surface work and it under-ran harder than gate 1 did. **The model is
not the variable:** every substantive WU across all three gates ran
`sonnet`/`medium`, and every closing WU ran `opus`/`high`. The variable is
coupling.

**Feature level.** `planned_cost_usd` is **$66.00**. Lifetime actual from
`events.jsonl`, summed over every `attempt_outcome` of all 17 completed units
including every non-passing attempt and every dispatch cycle before a re-arm, is
**$58.731832** — with this close still in flight.

| Gate | Planned | Actual | Delta |
| --- | --- | --- | --- |
| Gate 1 (6 units) | $23.50 | $18.379824 | −$5.12 (−21.8%) |
| Gate 2 (7 units) | $25.50 | $36.441099 | +$10.94 (+42.9%) |
| Gate 3 (4 of 5 units) | $17.00 | $3.910909 | — (close in flight) |
| **Feature to date** | **$66.00** | **$58.731832** | **89.0% of plan consumed** |

Gate 2 is the whole story: it alone exceeded its own `cost_budget_usd: 31.50`
brake by **$4.94 (15.7% over)**, and the brake never fired. Gate 2's close
predicted "roughly $2.3 over" on the assumption its closing pair would repeat
gate 1's actuals; the pair instead cost $12.701054 against $10.50 planned
(+21.0%) versus gate 1's $10.029213, so the overrun landed at more than double
the prediction. **The structural reason is confirmed rather than merely
restated:** `_should_halt_for_budget` is evaluated *before* each WU dispatch, so
spend inside the final WU of a gate is invisible to it. A brake that cannot
observe the last unit cannot stop a gate from ending over budget. If this close
lands in the range the two prior closes did ($3.35 and $5.67), the feature
finishes between **$62.1 and $64.4 — under the $66.00 plan** on the strength of
gate 3's under-run offsetting gate 2's over-run.

**Gate 2's Findings §1, carried forward and re-measured at terminal — not
re-derived.** The finding is gate 2's and stands as written: the arm predicate's
`budget_projection` class reads only `cost_usd` (`arm_eval.py:124` in `_read_wu`,
summed at `arm_eval.py:202`), never `cumulative_cost_usd` and never
`re_arm_history[].prior_cost_usd`, so it under-reads lifetime spend on every
re-armed unit. Gate 2 measured $6.23 (14.8%). Re-measured in this session:

| Quantity | Gate 2 close | Terminal |
| --- | --- | --- |
| Predicate-visible lifetime spend | $35.891552 | **$52.503515** |
| `events.jsonl` lifetime spend | $42.119869 | **$58.731832** |
| Under-read | **$6.228317 (14.8%)** | **$6.228317 (10.6%)** |

**The absolute error did not move by a cent.** It is still exactly
$1.220458 + $5.007859 — T04's fold-path spend parked in `cumulative_cost_usd`,
and T07's operator-path spend recorded only in `re_arm_history[].prior_cost_usd`
after `cost_usd` was zeroed. The percentage fell from 14.8% to 10.6% purely
because gate 3 added $3.91 of clean, never-re-armed spend to the denominator.
**The error does not decay; it is diluted.** On a feature that keeps re-arming it
grows, which is the failure mode gate 2 named: the error concentrates in exactly
the over-budget work the class exists to catch.

The live verdict at this gate reads `projected spend $57.50 within 2.0x baseline
planned total $54.00 (cap $108.00)`. The true projection is **$63.73** — still far
under the cap, so **no verdict flips on this feature at terminal either**, and
the class remains under-informed rather than wrong. One adjacent observation this
re-measurement surfaced, which gate 2 did not record: the cap is computed from
the *baseline* planned total of **$54.00**, not from PLAN.md's current $66.00,
because `PLAN.baseline.json` was snapshotted before G2-PLAN's re-baseline. That
is `write_baseline_if_absent` behaving exactly as designed — the baseline is the
drift reference and must not move — but it means the ceiling tracks the plan as
first snapshotted, and any close reading the verdict string should not mistake
`$54.00` for the current plan.

**A home for the fix, named and not taken.** This close does not fix it: a driver
behavior change inside a terminal close is unreviewable, and the WU forbids it.
The fix is two small changes in two different owners' surfaces — have `arm_eval`
sum `cost_usd + cumulative_cost_usd + re_arm_history[].prior_cost_usd`, and have
the operator re-arm path fold rather than zero (which would also unblind
`gate_spent_usd`, whose `cost_usd == 0 means already folded` guard misreads a
never-folded unit). **Recommended home: a bug issue against `arm_eval.py` and
`loop.py`'s re-arm path, not a roadmap feature.** It is a two-function
correctness fix with a mechanical oracle — reconcile the predicate's sum against
`events.jsonl` on this feature and expect $58.731832 — and the bug workflow (one
bug, one branch, one PR, test-first) fits it exactly, where a feature folder would
cost more ceremony than the change. `GATE-03-REVIEW.md`'s open question 4 asked
for this decision and it is now recorded; **the operator's acceptance of the
recommendation is still required**, because the fix touches the predicate that
decides arming.

### Failure-class breakdown

One non-passing attempt in gate 3, on one work unit, **$0.786872 — 20.1% of
substantive gate spend**.

| failure_class | non-passed attempts | dominant signature | spend |
| --- | --- | --- | --- |
| `tests` | 1 | `$ python3 -m unittest discover -s tests -v` (T11 attempt 1; `coverage` failed as a consequence of the same break) | $0.786872 |

**The class, named by hand:** *a new shipped file registered in one of four
registries that assert the shipped file set*. T11 attempt 1's `files_touched`
records exactly two paths — `docs/concepts/autonomy-stop-classes.md` and its
mirror under `specfuse/loop/data/docs/concepts/`. The passing attempt touched
those two plus **four** test files:
`tests/test_scaffold_data_in_sync.py`, `tests/test_init_integration.py`,
`tests/test_scaffold_init.py` and `tests/test_scaffold_resources.py`. Each of the
four carries its own independent list naming every doc the scaffold ships; adding
a page without appending to all four fails the suite. **T11's AC#8 named only
`DOCS_TRACKED` in `test_scaffold_data_in_sync.py`** — it was precise, it was
correct, and it was one quarter of the actual contract. The first attempt did
what the criterion asked and the suite refused it.

Two observations:

- **The cost was one cheap attempt, and the reason is that the guard is fast and
  loud.** $0.79 and 489 seconds bought the discovery; the re-attempt passed. Set
  against T07's $5.01 spin in gate 2, the distinguishing property is that the
  failing assertion names the missing path directly rather than surfacing three
  files away in a sibling WU's fixture.
- **T12 inherited the fix for free and passed first attempt.** It `depends_on`
  T11 precisely so the two shared-list edits would be sequential, and by the time
  it ran, all four lists already had an entry to append beside. The declared
  dependency did the work PLAN.md said it would — which is the counter-example to
  gate 2's Finding 3, where undeclared fixture coupling cost $5.01.

## What the loop did NOT verify

Ten entries, consolidated across all three gates as criterion 5 requires. Gate 1
listed two and gate 2 listed six; this close records which of those eight closed,
which remain open, and adds gate 3's own. **Two closed, six remain open, two are
new.** No predecessor auto-close debt markers exist anywhere in this feature
(`grep -rn "specfuse:autoclose-debt"` over the feature folder returns nothing),
so `close-g` has nothing to name.

**Closed since they were recorded — stated so a reader does not carry them
forward:**

1. **~~Gate 1 #1: no live `arm_predicate_evaluated` emission.~~ Closed.** Two
   such events now exist in `events.jsonl`
   (`2026-07-30T21:22:08.614225+00:00` and `2026-07-31T03:06:03.211684+00:00`),
   both emitted by driver processes launched after T04's commit. Gate 1's
   Findings §1 disambiguation was right and `GATE-01.md`'s "no event = the claim
   is false" inference was wrong.
2. **~~Gate 1 #2: the baseline write never fired on a real driver run.~~
   Closed.** `.specfuse/features/FEAT-2026-0053-auto-mode/PLAN.baseline.json`
   exists. Confirmed this session: **1 of 43** feature directories has one, this
   feature's.

**Open — the real oracle lies outside this feature:**

3. **"A four-gate feature costs one human touch (the PR review) instead of
   four"** (PLAN.md `roadmap_goal`; GATE-02.md definition of done). *Verified
   in-loop:* the entire arm path, by `tests/test_arm_wiring.py` (7 tests),
   including a run against `_copy_real_feature` — a copy of this feature's real
   folder with its real baseline, real WU frontmatter and real `events.jsonl` —
   rewound to the moment gate 1 is about to close, asserting one commit via a real
   `git rev-list --count`. *Not verified:* **one production ride. Zero gates have
   ever been armed by the predicate.** **Why:** this feature runs
   `autonomy_default: review` by decision (`[FEAT-2026-0007/G2-LESSONS]` — an
   enforcement mechanism cannot be exercised by the gate that builds it).
   **Where it is actually verified:** the first feature dispatched with
   `autonomy_default: auto` after this branch merges.
4. **"The drift caps measure real drift"** (T03 AC; GATE-01.md definition of
   done). *Verified in-loop:* every class's firing and quiet behavior by
   `tests/test_arm_eval.py` (19 cases). *Not verified:* a meaningful `drift_caps`
   verdict on any real feature. **Why:** this feature's `PLAN.baseline.json` was
   captured after its own gate-2 drafting — gate 1's Findings §2 predicted it and
   gate 2 confirmed it on disk — so the baseline already contains gate 2 and gate
   3's `G3-CLOSE` placeholder. Comparing gate 2 to a baseline containing gate 2
   returns clean and means nothing. **Where it is actually verified:** a feature
   whose **first dispatch** postdates this branch. T12's page states this as a
   property of every pre-existing feature, not of this one.
5. **"`plan_next_lint` blocks a non-compliant plan-next draft under `auto`"**
   (GATE-02.md definition of done, T07). *Verified in-loop:* firing, quiet, and
   malformed-frontmatter behavior by `tests/test_arm_eval_lint_class.py` (4
   tests). *Not verified:* the **firing** path on a real folder. The corpus sweep
   re-run this session is unchanged at **0 fired / 1 clean / 42 not_evaluable**
   across 43 real directories. **Where it is actually verified:** the first `auto`
   feature that reaches a gate boundary with a genuinely non-compliant draft —
   which, by design, is the case where a human is most needed and least present.
6. **"Every auto-armed gate's doubt reaches the PR read"** (GATE-02.md
   definition of done; GATE-03.md, T13). **Status changed but not closed.** Gate
   2 recorded this as *unowned* — `grep -rn "FEATURE-REVIEW" .specfuse/skills
   specfuse/loop/data` returned zero. T13 built the last hop and that grep now
   returns matches. *Verified in-loop:* both skill copies byte-match
   (`tests/test_skills_vendored_in_sync.py`, 4 tests) and the instructions say
   what they should say. *Not verified:* **that the instructions produce a good PR
   body.** The deliverable is prose a model executes; no test can run it. **Where
   it is actually verified:** the first `auto` feature's PR. T13's own
   Verification section says this in the same words.
7. **"Lessons from an unread gate are staged, not landed"** (GATE-02.md
   definition of done, T09). *Verified in-loop:* the invariant that forces
   staging, by `tests/test_learnings_staging.py` (7 tests). *Not verified:* the
   four-step **human promotion procedure** the template documents. Confirmed
   again this session: `ls .specfuse/features/*/LEARNINGS-pending.md` matches
   nothing — **zero such files have ever existed in this repo, so no human has
   ever performed the step.** **Where it is actually verified:** the PR review of
   the first `auto` feature.
8. **"`budget_projection` stops a feature heading past 2× its baseline"** (T03
   AC; GATE-01.md definition of done). *Verified in-loop:* the arithmetic and the
   threshold, by `tests/test_arm_eval.py`. *Not verified:* that the class reads
   the right spend — it does not, by $6.228317, re-measured above. **The class
   has also never fired on anything.** Its projection on this feature ($63.73
   true, $57.50 as read) is under a $108.00 cap, so even a corrected input would
   not have exercised the firing path. **Where it is actually verified:** a
   feature that genuinely approaches 2× its baseline — and the fix must land
   first, or the class will under-read exactly the re-armed feature most likely
   to get there.

**New in gate 3:**

9. **"`docs/methodology.md` §9 describes the autonomy dial the run loop actually
   implements", "a parked `auto` feature is diagnosable from documentation
   alone", and "an operator can adopt `auto` without reading source"**
   (GATE-03.md definition of done, T10/T11/T12). *Verified in-loop:* that the
   mirrored copies byte-match, that all eight `CLASS_NAMES` appear in the
   reference, that all eight inventory names appear in the migration guide, that
   the four-condition sketch is gone, and that both pages are registered in all
   four scaffold registries. *Not verified:* **that any of the prose is correct,
   or that a real operator can actually diagnose a parked feature from it.** No
   test can assert either. **Where it is actually verified:** the human at PR
   review, which `GATE-03.md` names explicitly, and the first operator who has to
   use the pages under pressure. Two prose defects already found by reading, both
   in text every oracle passed, are named in the gate-3 narrative above.
10. **"Under `auto`, no gate that ships a documentation file can arm"** — the
    `judge_editing` v1 approximation, accepted as open question 2 at arming.
    *Verified in-loop:* that the class **does** fire on exactly this input, by the
    real `arm_predicate_evaluated` event at `2026-07-31T03:06:03Z` naming T10, T11
    and T12 by their mirrored `specfuse/loop/data/docs/` paths. *Not verified:*
    what happens next — **that the fired verdict actually parks an `auto`
    feature, and that the operator, meeting it, finds the answer on T11's page
    instead of in `arm_eval.py`.** **Why:** this feature runs `review`, so the
    fired verdict cost nothing and stopped nothing. **Where it is actually
    verified:** the first `auto` feature that ships any documentation — which,
    given that every gate of every feature tends to touch docs, is likely to be
    the *first* `auto` feature, making this the most probable first encounter any
    operator will have with the predicate refusing to arm.

## Findings

Three, all surfaced by this close.

**1. The most likely first experience of `auto` is a refusal to arm, caused by an
accepted approximation rather than by a hazard.** `judge_editing` matches any path
under the `specfuse/loop/` prefix; every shipped doc in this repo is mirrored into
`specfuse/loop/data/docs/`; therefore any gate that ships documentation fires the
class. This is not a prediction — the event on disk shows it firing on this
gate's own three documentation WUs. Gate 3's arming discipline named it, T11's
page documents it with "the human arm, not a code change" as the clearing action,
and the operator accepted it as a v1 limit at arming. All correct. **The finding
is about the resulting first impression:** a feature whose entire premise is
"four human touches become one" will, on its first real outing, most likely stop
at its first documentation-shipping gate and ask for a human — for a reason that
is a path-prefix artifact. The documentation is in place, so the operator will
not be confused. They may reasonably conclude the dial does not work. Narrowing
`JUDGE_PATHS` to exclude `specfuse/loop/data/` is the obvious candidate and it is
**not** obviously safe: package data is what downstream projects receive, and a WU
that edits a shipped template is editing something a judge reads. This needs a
decision with evidence, not a one-line prefix edit, and it has no home yet.

**2. A criterion can name a real registry, be satisfied exactly, and still fail
the gate, when the contract is spread across registries that do not reference each
other.** T11's AC#8 named `DOCS_TRACKED`. Three further test files carry
independent copies of the same shipped-doc list, and none of the four names the
others. The attempt that satisfied AC#8's letter failed the suite; the cost was
$0.79. This is the same *shape* as gate 2's Finding 3 — a contract nobody had
enumerated — but a different and much cheaper *class*: the assertion named the
missing path directly, rather than surfacing in a sibling WU's fixture three files
away. **The cheapness is a property of the guard, not of the drafting.** A
drafting-time check would have cost nothing: grep the repo for an existing entry
of the same kind and count how many files match, before writing the criterion.

**3. Gate 3 spent 22.3% of gate 2's dollars on four units of comparable declared
size, and the coupling explanation now has enough data points to be predictive
rather than descriptive.** $3.91 against $23.74 substantive, same model, same
effort, same author process, four units against five. Gate 2's Finding 4 proposed
scoping issue #260's estimate rule to independent-module work; gate 3 is the
confirming case from the other direction, and it under-ran by nearly twice gate
1's margin. The three gates form a clean ordering by coupling: independent
documentation (−67.4%) < independent modules (−35.8%) < wiring into a live driver
and into siblings (+58.3%). **Estimating by WU *type* is the error; estimating by
how many surfaces a WU shares with its siblings is the correction.** Five data
points on one feature, all `sonnet`/`medium`, is the strongest evidence issue #260
has had.

## What I'd change

**Write the definition-of-done criterion against the enforcing surface, not
against the surface you edited.** Both of this gate's avoidable costs are the same
mistake at different sizes: T11's AC#8 named one of four registries, and gate 2's
brake was declared against a plan total the brake cannot observe the end of. The
drafting-time check is mechanical — before writing "verified by X", grep for every
file that asserts the same property and either name them all or name the *suite*
rather than one member of it. This is the registry-facing sibling of gate 2's
fixture-facing lesson, and both belong next to `authoring-work-units` §8's
cross-surface check.

**Give the gate budget brake a post-gate reconciliation, or stop calling it a
brake.** Gate 2 exceeded its declared `cost_budget_usd` by $4.94 and the brake did
not fire, because `_should_halt_for_budget` runs before each dispatch and the
overrun happened inside the last unit. Gate 3's `cost_budget_usd: 22.00` carries a
frontmatter comment saying exactly this, which means the defect is now documented
in the artifact rather than fixed in the driver. A brake that structurally cannot
observe the final unit of a gate is an estimate-checker, and the honest options are
to check spend *after* the last WU as well as before it, or to rename the field.
This is issue #260's neighbour and belongs to the same owner; this retrospective
adds the second measured overrun rather than proposing the change.

**Nothing about gate 3's execution.** Four units, one cheap correctable failure,
67% under budget, every deliverable shipped including the scope revision the
operator accepted at arming. The gate did what it was drafted to do.

## Feature-arc verdict

**Verdict: `met_locally`.** Every drafted work unit across all three gates
shipped and every local oracle passes — 1969 tests at exit 0, all four named
oracles re-run fresh in this session, both drift guards green, the plan
structurally valid. The mechanism is complete: the predicate, the baseline, the
atomic one-commit arm with its pre-arm tag, the severity flip, the doubt
accumulation, the LEARNINGS staging, the operator documentation, and — from gate
3 — the reader that carries accumulated doubt into the one human read. Nothing
drafted was dropped, and the one scope revision (T13) was surfaced for an explicit
operator decision rather than absorbed.

**The roadmap goal is "a four-gate feature costs one human touch (the PR review)
instead of four". That claim is built and unproven, and it must not be reported
as delivered.** Stated plainly:

- **No feature has ever ridden `auto`. Zero gates have been armed by the
  predicate.** This feature runs `review` by deliberate decision — an enforcement
  mechanism cannot be exercised by the gate that builds it — so the arm path's
  only executions are in tests, one of which does drive the real `loop.run()`
  against a copy of this feature's own folder and asserts one commit by real
  `git rev-list --count`. That is a genuine driver invocation and it is not a
  production ride.
- **The predicate's *refusal* path is well evidenced; its *approval* path on real
  input is not.** Three corpus sweeps across 43 real feature directories have
  returned zero `would_arm: True` and zero exceptions, and one real event shows
  `judge_editing` and `open_questions_human_only` firing correctly on real drafted
  WUs. The single `would_arm: True` this feature has ever produced came from this
  close's own terminal-gate run, where there is nothing to arm.
- **A structural limit stands between the mechanism and the headline number.**
  Under `auto`, no gate shipping a documentation file can arm (Findings §1). A
  four-gate feature whose gates touch docs — most of them — would stop for a human
  at those gates today. The one-touch claim is therefore not merely unproven; it
  is **currently unreachable for a large class of features** until `JUDGE_PATHS`
  is narrowed with evidence.
- **This feature is itself a three-gate feature, not a four-gate one**, and its
  own gate boundaries were all human-armed. It cost the four human touches the
  goal exists to eliminate.

`met_locally` is the honest verdict and it is deliberately not `met`: the
criteria in *What the loop did NOT verify* §3–§10 are unverifiable in this
environment, not satisfied. It is deliberately not `partially_met` either —
nothing drafted is missing or half-built, and every gap above is an environmental
oracle (no production `auto` ride) rather than an unfinished deliverable. **The
single condition that upgrades this feature to `met`: one feature dispatched with
`autonomy_default: auto` after this branch merges, arming at least one gate
boundary without a human, with its `gate_auto_armed` event and its
`FEATURE-REVIEW.md` reaching a PR body.** Until that has happened, `auto` is a
mechanism that works in tests.

## Lessons promoted

**This feature runs `autonomy_default: review`, so T09's staging invariant is
inert here and these lessons go to the durable `.specfuse/LEARNINGS.md` as
usual** — no `LEARNINGS-pending.md` was created, and none should have been.
Verified rather than assumed: `ls .specfuse/features/*/LEARNINGS-pending.md`
matches nothing anywhere in this repo. Gate 2's close said this for the same
reason and it is worth repeating at the terminal close of the feature that
*built* the staging mechanism, because this is exactly where a reader will wonder
whether it was bypassed. **It was not bypassed; it correctly did not apply.** Its
first real exercise belongs to the first `auto` feature, and no human has yet
performed the promotion step its template documents.

Three entries appended to `.specfuse/LEARNINGS.md` under
`[FEAT-2026-0053/G3-CLOSE]`: a path-prefix approximation that is correct as a
safety property can still make the feature's headline case unreachable, and the
close must say so where the prose says "accepted v1 limit"; a definition-of-done
criterion must name the surface that *enforces* a property rather than the one
that *declares* it, because contracts spread across unreferencing registries are
satisfied exactly and still fail; and a budget brake evaluated only before
dispatch cannot observe the unit that overruns, so a gate can exceed its declared
budget with the brake reporting clean.

