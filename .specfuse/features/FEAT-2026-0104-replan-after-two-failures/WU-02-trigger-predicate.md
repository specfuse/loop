---
id: FEAT-2026-0104/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces_driver_helper:
  - should_replan_instead_of_retry
produces:
  - tests/test_replan_trigger.py
---

# Decide when a re-plan fires instead of a retry

**Objective.** Replace T01's stubbed trigger with the real predicate: a unit
re-plans when its next attempt would be its last permitted one, unless it
declared `iterate_on_failure`.

**Context.** FEAT-2026-0104/T02. The ceiling is not a constant — 
`resolve_max_attempts` (`loop.py:267`) resolves it unit, then project, then
`MAX_ATTEMPTS = 3`, on the premise that a unit's author knows that unit's
oracle. A hard count of two would re-plan a unit that deliberately declared a
higher ceiling, which is the case that dial exists for (#2650). Ceiling-relative
firing yields "after two failures" at the default that every unit in the corpus
actually runs at, while respecting any unit that said otherwise. Units
declaring `iterate_on_failure` are exempt outright: they fail on purpose
against a convergent validator.

**Acceptance criteria.**

- `python3 -m unittest tests.test_replan_trigger -v -b` fails on HEAD before
  this unit's edits and passes after.
- The test covers, as separate cases: default ceiling 3 fires the re-plan
  after the 2nd failure; a unit declaring `max_attempts: 10` fires after its
  9th and not its 2nd; a unit declaring `max_attempts: 1` never fires; and a
  unit declaring `iterate_on_failure: true` never fires at any ceiling.
- A unit whose attempt tripped `detect_deterministic_refusal_repeat` escalates
  there and does **not** re-plan — asserted directly, since both paths key off
  a repeated failure and only one of them can own the outcome.
- This unit carries a flag-scope table naming every path that reaches a retry
  today and whether the new decision gates it (`planning-discipline.md` §3).

**Do not touch.** `MAX_ATTEMPTS`' value at `loop.py:137` — the default of 3 is
out of scope by PLAN.md. `resolve_max_attempts`' resolution order.
`gate_eval.py`. The sibling WU files in this gate.

**Verification.** Narrow tier for `implementation`, plus
`python3 -m unittest tests.test_replan_trigger tests.test_replan_end_to_end -v -b`
— T01's oracle must still pass with the real predicate behind it.

**Escalation triggers.** Stop with `status: blocked` if the refusal-repeat
interaction cannot be resolved without changing
`detect_deterministic_refusal_repeat`'s own behaviour: which check owns a
repeated guard refusal is a design question this unit is not authorized to
settle alone.
