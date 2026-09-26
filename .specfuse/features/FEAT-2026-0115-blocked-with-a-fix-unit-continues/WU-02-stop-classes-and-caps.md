---
id: FEAT-2026-0115/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
produces_driver_helper:
  - evaluate_fix_unit_insertion
produces:
  - specfuse/loop/loop.py
  - tests/test_fix_unit_insertion_refused.py
---

# The arm predicate's stop classes and two caps decide whether the draft is inserted

**Objective.** Before inserting, judge the draft the way an arm would: the
plan-next draft lint, the arm predicate's stop classes on the added unit, an
insertion cap per blocked unit, and the gate's cost budget; refuse with the
class named and fall back to today's escalation.

**Context.** FEAT-2026-0115/T02. Add `evaluate_fix_unit_insertion(feature_dir,
gate, blocked_wu, draft, cfg)` in `specfuse/loop/loop.py`, called by T01's
branch before `insert_fix_unit`. It runs, in order: `lint_plan_next_draft`'s
per-unit checks on the draft (five sections, `produces:` shape, red-test
bullet) — blocking here, not warn-only; `evaluate_arm_predicate` from
`arm_eval.py` against a projected graph that includes the draft, refusing on
any `VETO_CLASSES` hit or on `drift_caps`, `judge_editing`,
`decision_class_paths`; `insertion_count` for the blocked unit (from prior
`fix_unit_inserted` events) against `defaults.max_fix_units_per_unit` (default
2); and the draft's `planned_cost_usd` plus the gate's spend against the gate's
`cost_budget_usd` when declared. It returns `(ok, refusing_class, reason)`. A
refusal is recorded on the blocked unit's `human_escalation` payload as
`insertion_refused: {class, reason}` (T03 renders it) and the escalation is
today's.

**Acceptance criteria.**

1. `tests/test_fix_unit_insertion_refused.py` fails on HEAD before this unit's
   edits (the module is absent); after,
   `python3 -m unittest tests.test_fix_unit_insertion_refused -v -b` exits 0.
2. That module asserts, through `loop.run()`, one refusal per class: a draft
   missing `provenance` (`missing_provenance`), a draft whose `produces:`
   names `specfuse/loop/loop.py` (`judge_editing`), a third insertion for the
   same unit (`max_fix_units_per_unit`), and a draft whose cost would exceed
   the gate's `cost_budget_usd` — each ends `blocked_human` with
   `human_escalation` carrying `insertion_refused.class` equal to that name,
   and the draft stays `draft`.
3. A fifth case asserts a clean draft still inserts (T01's path is not
   narrowed by the checks).
4. `python3 -m unittest tests.test_arm_eval tests.test_lint_plan_next_draft tests.test_fix_unit_insertion_e2e -v -b`
   exits 0 with no edit to the first two modules.

**Do not touch.** `arm_eval.py`, `arm_txn.py`, `lint_plan.py` (call, do not
edit; if a check needs a new entry point there, block and name it);
`gate_eval.py` (T03); `.specfuse/rules/` and `docs/` (T04); plus
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. The broad
tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if `evaluate_arm_predicate`
cannot be run against a projected graph without `PLAN.baseline.json` (the
feature under test has none — say whether the fixture or the predicate needs
the change); or if `lint_plan_next_draft` has no per-unit entry point separable
from the review-file checks.
