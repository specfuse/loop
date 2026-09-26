---
id: FEAT-2026-0117/T02H2
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.50
produces:
  - tests/test_carried_green_invalidated_by_diff.py
  - tests/test_reclose_carries_narrow_greens_e2e.py
---

# The e2e helpers restore their patches in reverse order

**Objective.** Stop the two e2e modules from leaving a fake `dispatch` /
`verify` installed on `loop` after each test.

**Context.** FEAT-2026-0117/T02H2, hygiene for T01/T02 (gate 1 tests gate
before T04, 2026-09-26, 29 failures in unrelated modules such as
`test_claude_resolution`, `test_dispatch_skills_index`, `test_verify_empty_gate_set`:
`fake_dispatch() got an unexpected keyword argument 'cost_tracking'`). Both
`TestCarriedGreenInvalidatedByCoveredPathDiffE2E` in
`tests/test_carried_green_invalidated_by_diff.py` and the e2e class in
`tests/test_reclose_carries_narrow_greens_e2e.py` keep a `self._patches` list
and restore it in `tearDown` in insertion order; every test calls
`self._patch("dispatch", …)` twice (one fake per close), so the restore sets
the original and then the first fake back. Change both `tearDown` loops to
iterate `reversed(self._patches)`. Nothing else changes. Red-test exempt: the
reproduction is the oracle —
`python3 -m unittest tests.test_carried_green_invalidated_by_diff tests.test_reclose_carries_narrow_greens_e2e tests.test_claude_resolution tests.test_dispatch_skills_index -b`
errors on HEAD and exits 0 after.

**Acceptance criteria.**

1. The reproduction command above exits 0 (errors on HEAD before this
   unit's edit).
2. `python3 -m unittest tests.test_carried_green_invalidated_by_diff tests.test_reclose_carries_narrow_greens_e2e -v -b`
   exits 0 with every test present and its assertions unchanged.

**Do not touch.** Any assertion in either module; `loop.py`,
`criteria_state.py`, `judge.py`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
criterion 1. The broad tier is the driver's, once per gate — never run
in-session.

**Escalation triggers.** Stop with `status: blocked` (one-line `blocked_reason`)
if the reproduction still errors after the reverse restore — name the test
and the leaked attribute.
