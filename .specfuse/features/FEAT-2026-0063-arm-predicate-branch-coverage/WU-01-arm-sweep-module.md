---
id: FEAT-2026-0063/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.50
produces:
  - specfuse/loop/arm_sweep.py
  - tests/test_arm_sweep.py
produces_driver_helper:
  - sweep_arm_predicate
  - BranchObservation
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T15:48:38.530981+00:00
duration_seconds: 665.639
cost_usd: 1.620276
input_tokens: 54
output_tokens: 19087
---

# One sweep, one report: what the predicate has actually said on real input

**Objective.** Ship `specfuse/loop/arm_sweep.py` with a function that walks this
repository's feature folders, evaluates the arm predicate on every feature that can
be evaluated, and returns a per-class record of which verdict branches have been
observed on real input — with the features it could *not* evaluate named and counted
rather than silently absent.

**Context.** Correlation ID `FEAT-2026-0063/T01`. Read `PLAN.md` first — it records
the 2026-08-03 measurement, why this feature reports rather than verifies, and the
existing-mechanism search that found no prior sweep. Do not reopen those decisions.

**Why a new module.** `arm_eval.py`'s module docstring states the dependency runs
`loop.py → arm_eval`; `arm_eval` must not import `loop`. This sweep is a *reader* of
the predicate and must not become a dependency of it. `arm_sweep.py` imports
`arm_eval` and `plan_baseline`, and must not be imported by either.

**Why the package and not `.specfuse/scripts/`.** `event_type_gate.py` is repo-local
hygiene because it validates this repository's own event logs against a vendored
schema. This sweep answers a question every project running `auto` has, so it ships
with the driver. It must be importable without any repo-specific path assumption —
the feature root is an argument, not a constant.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The contract

`sweep_arm_predicate(features_root)` returns a report object with three parts.

1. **Evaluable set.** A feature is evaluable when it carries `PLAN.baseline.json`.
   Anything else is *excluded*, not *failing*: features predating
   `write_baseline_if_absent` are `done` and will never be dispatched again, so
   `no_baseline` is the correct answer about them rather than blindness. The report
   carries the excluded count and that reason as data, not prose.
2. **Per-class branch observation.** For each of `arm_eval.CLASS_NAMES`, the set of
   statuses observed (`clean` / `fired` / `not_evaluable`), a count per status, and
   the first (feature_id, gate) at which each status was seen. A class with a status
   it has never produced is the point of the whole report — the absence must be
   representable, not inferred from a missing key.
3. **Evaluation ledger.** Every evaluable feature appears exactly once as either
   `evaluated` (with the gates swept) or `could_not_evaluate` (with the exception
   text). Nothing may be dropped from the denominator.

Gates come from the feature's own `PLAN.md` graph, not a fixed range: a feature with
three gates is swept at three, one with a single gate at one.

**The trap, stated so it is not rediscovered.**
`LEARNINGS [FEAT-2026-0072/G1-CLOSE]` — a sweep that walks many inputs must classify
every non-zero outcome as *this check fired* or *this check never ran*, and must not
let one raising input silently shrink the set it claims to have covered. A feature
whose `PLAN.md` is malformed must land in `could_not_evaluate` with its error, not
vanish. "38 of 39 clean" understates it and "one failure, ignore it" drops an input
the report says was total.

**Acceptance criteria.**

1. `tests/test_arm_sweep.py::TestArmSweep::test_excluded_features_reported_not_dropped`
   exists and **fails on HEAD before this WU runs** (`specfuse/loop/arm_sweep.py`
   does not exist, which counts as red).
2. That test builds a fixture root holding two features — one with
   `PLAN.baseline.json`, one without — and asserts the report evaluates exactly one,
   reports exactly one excluded, and carries the exclusion reason. It passes after
   this WU's edits.
3. A test asserts a feature whose `PLAN.md` raises during evaluation appears in the
   ledger as `could_not_evaluate` carrying the exception text, and that the evaluable
   count still includes it — it is not dropped from the denominator.
4. A test asserts per-class observation records the *absence* of a status: a fixture
   where no class ever reports `not_evaluable` yields, for every class, an explicit
   "never observed" for that branch rather than a missing entry.
5. A test asserts gates are read from each feature's own `PLAN.md` graph — a
   three-gate fixture is swept at three gates, a one-gate fixture at one.
6. A test asserts first-observation is recorded as (feature_id, gate) and is the
   *earliest* in a deterministic ordering, not whichever the walk hit last.
7. `specfuse/loop/arm_sweep.py` does not import `loop.py`, and neither `arm_eval.py`
   nor `plan_baseline.py` imports `arm_sweep`. Assert with
   `grep -n "^from \.\|^import \|^from specfuse" specfuse/loop/arm_sweep.py` and
   `grep -rn "arm_sweep" specfuse/loop/arm_eval.py specfuse/loop/plan_baseline.py`,
   quoting both outputs in the result.
8. **Run against the real tree and record the numbers.** Sweep
   `.specfuse/features/` and record in the result: evaluable count, excluded count,
   class-verdict totals, and the per-class never-observed list. As of 2026-08-03 this
   should read 4 evaluable, 41 clean / 7 fired / 0 not_evaluable, with five classes
   never-fired and eight never-`not_evaluable`. **If the numbers differ, report what
   they actually are** — the corpus grows by one per baselined feature and these
   figures are dated by construction. A mismatch is new data, not a failure.
9. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/loop/arm_eval.py` — this feature reads the predicate and
does not change it; a sweep that edits its own subject cannot report on it.
`.specfuse/verification.yml` — T02 owns the gate wiring.
`docs/concepts/autonomy-stop-classes.md` — T03 owns the record.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Beyond the gates, criterion 8's
real-tree sweep is the oracle that matters — a module that passes its fixtures and
cannot walk `.specfuse/features/` has verified nothing. Run it against the real tree
and quote the counts.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
report cannot represent a never-observed branch without inventing a sentinel that
collides with a real status; sweeping the real tree raises on a feature in a way that
cannot be classified as either `evaluated` or `could_not_evaluate`; or `arm_eval`
turns out to need a change for the sweep to read it, which this WU's Do-not-touch
list forbids. Do **not** narrow the evaluable set to make the sweep pass — an
incomplete sweep reported as complete is the defect this feature exists to remove.
A real-tree count that differs from `PLAN.md`'s dated figures is **not** a block:
report the new numbers and continue.
