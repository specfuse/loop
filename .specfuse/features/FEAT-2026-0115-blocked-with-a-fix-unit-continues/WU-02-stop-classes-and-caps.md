---
id: FEAT-2026-0115/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
produces_driver_helper:
  - evaluate_fix_unit_insertion
produces:
  - specfuse/loop/loop.py
  - tests/test_fix_unit_insertion_refused.py
escalation_reason: spinning_signature_repeat
escalation_failure_class: tests
escalation_failure_signature: "ERROR: test_fix_unit_insertion_refused (unittest.loader._FailedTest.test_fix_unit_insertion_refused)"
re_arm_override: true
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-09-26T16:35:05+00:00
    prior_status: blocked_human
    prior_attempts: 2
    prior_cost_usd: 1.258667
    prior_duration_seconds: 359.74
    reason: "Both sessions reported status: blocked with a real reason (the unit forbade the edits its own design needed); the driver read the block-scalar RESULT as complete (#3436) and escalated as a spin. Unit re-scoped to write-then-evaluate; override because the escalated signature is the parse defect, not the unit."
cumulative_cost_usd: 0.0
cumulative_duration_seconds: 0.0
cumulative_input_tokens: 0
cumulative_output_tokens: 0
cumulative_attempts: 2
cost_usd: 3.124199
duration_seconds: 685.709
input_tokens: 156
output_tokens: 58420
folded_through_re_arm: 1
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T16:35:06.002763+00:00
---

# The arm predicate's stop classes and two caps decide whether the draft is inserted

**Objective.** Before a drafted fix unit is armed, judge it the way a gate arm
would: the feature lint, the arm predicate's stop classes with the draft on
disk, an insertion cap per blocked unit, and the gate's cost budget; refuse
with the class named and fall back to today's escalation.

**Context.** FEAT-2026-0115/T02, re-scoped after two honest blocks: neither
`evaluate_arm_predicate` nor `lint_plan_next_draft` takes a projected graph,
and this unit may not add entry points to `arm_eval.py` or `lint_plan.py`. So
evaluate **after writing, before arming**. Split T01's `insert_fix_unit` in
`specfuse/loop/loop.py` into two steps: (1) write the draft into the gate's
graph in `PLAN.md` with `status: draft` unchanged on the file, add its id to the
blocked unit's `depends_on`; (2) call the new
`evaluate_fix_unit_insertion(feature_dir, gate, blocked_wu, draft, cfg)`; only on
`ok` flip the draft to `pending`, re-arm the blocked unit, emit
`fix_unit_inserted` and continue. On refusal, remove the draft's graph entry
and the `depends_on` edge again (the draft file stays on disk, `status:
draft`), record `insertion_refused: {class, reason}` on the blocked unit's
`human_escalation` payload, and escalate as today. The evaluator runs, in
order: `plan_baseline.write_baseline_if_absent(feature_dir, plan)` so the
predicate is evaluable; `lint_plan._lint_impl(feature_dir)`, refusing with
class `lint` when any returned line names the draft's file or id;
`arm_eval.evaluate_arm_predicate(feature_dir, gate - 1)`, which collects the
drafts of gate `gate`, refusing with the first class whose status is not
`clean` among `missing_provenance`, `judge_editing`, `decision_class_paths`,
`drift_caps`, `plan_next_lint`, and with class `baseline_missing` when every
class is `not_evaluable`; the count of prior `fix_unit_inserted` events for the
blocked unit against `defaults.max_fix_units_per_unit` (default 2, class
`max_fix_units_per_unit`); and the draft's `planned_cost_usd` plus the gate's
spend against the gate's `cost_budget_usd` when declared (class
`cost_budget`). Returns `(ok, refusing_class, reason)`. Red test first:
`tests/test_fix_unit_insertion_refused.py`, same harness as
`tests/test_fix_unit_insertion_e2e.py` (its fixture must write a
`PLAN.baseline.json` for the feature, or let the evaluator write it).

**Acceptance criteria.**

1. `tests/test_fix_unit_insertion_refused.py` fails on HEAD before this unit's
   edits (the module is absent); after,
   `python3 -m unittest tests.test_fix_unit_insertion_refused -v -b` exits 0.
2. That module asserts, through `loop.run()`, one refusal per class: a draft
   without `provenance` (`missing_provenance`), a draft whose `produces:`
   names `specfuse/loop/loop.py` (`judge_editing`), a third insertion for the
   same unit (`max_fix_units_per_unit`), and a draft whose cost would exceed
   the gate's `cost_budget_usd` (`cost_budget`) — each ends `blocked_human`
   with `human_escalation` carrying `insertion_refused.class` equal to that
   name, the draft file still `status: draft`, and `PLAN.md`'s graph without
   the draft.
3. A fifth case asserts a clean draft still inserts and the gate continues
   (T01's oracle is not narrowed by the checks).
4. `python3 -m unittest tests.test_fix_unit_insertion_e2e tests.test_arm_eval tests.test_lint_plan_next_draft -v -b`
   exits 0 with no edit to the last two modules.

**Do not touch.** `arm_eval.py`, `arm_txn.py`, `lint_plan.py`, `plan_baseline.py`
(call, do not edit); `gate_eval.py` and the brief wording (T03, already
landed — read `insertion_refused` as T03 renders it); `.specfuse/rules/` and
`docs/` (T04); plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. The broad
tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` (one-line `blocked_reason`,
no block scalar — #3436) if `evaluate_arm_predicate` cannot see a gate-1 draft
when called with `just_closed_gate=0` (say what it collected); or if T03's
brief rendering expects a payload shape this unit cannot produce.
