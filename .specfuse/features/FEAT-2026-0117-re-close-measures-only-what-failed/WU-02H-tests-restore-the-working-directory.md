---
id: FEAT-2026-0117/T02H
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.50
produces:
  - tests/test_carried_green_invalidated_by_diff.py
---

# The covers tests restore the working directory

**Objective.** Stop `tests/test_carried_green_invalidated_by_diff.py` from
leaking its working directory into every later test in the suite.

**Context.** FEAT-2026-0117/T02H, hygiene for T02 (gate 1 entry probe before
T04, 2026-09-26): `TestDeriveCriterionCovers.test_maven_dtest_oracle_resolves_existing_class_file`
and `test_maven_dtest_oracle_with_no_matching_file` call `os.chdir(root)`
inside `integration_workspace()` and never restore the previous directory, so
once the temp workspace is deleted, 30-odd later tests that run git in the
current directory fail with `exit status 128` or `FileNotFoundError`
(reproduced: `python3 -m unittest tests.test_carried_green_invalidated_by_diff tests.test_changed_file_test_selection -b`
errors 3 in the second module). Give `TestDeriveCriterionCovers` the same
`setUp` / `tearDown` cwd guard the module's e2e class already has (save
`os.getcwd()`, restore it), and touch nothing else. Red-test exempt: the
reproduction command above is the oracle (red on HEAD, green after).

**Acceptance criteria.**

1. `python3 -m unittest tests.test_carried_green_invalidated_by_diff tests.test_changed_file_test_selection -v -b`
   exits 0 (3 errors on HEAD before this unit's edit).
2. `python3 -m unittest tests.test_carried_green_invalidated_by_diff -v -b`
   still exits 0 with every test present and unchanged in its assertions.

**Do not touch.** Any assertion in that module; `criteria_state.py` and
`loop.py`; `tests/_workspace.py`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
criterion 1. The broad tier is the driver's, once per gate — never run
in-session.

**Escalation triggers.** Stop with `status: blocked` (one-line `blocked_reason`)
if the reproduction command still errors after the cwd guard — name the test
that leaks.
