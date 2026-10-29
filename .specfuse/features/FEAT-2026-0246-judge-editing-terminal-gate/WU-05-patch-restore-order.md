---
id: FEAT-2026-0246/T05
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.00
provenance: "Gate 1's broad run failed twice (events.jsonl human_escalation reason broad_run_gate_failure at 12:11:28 and 12:26:57) on the identical 14 tests in test_verify_empty_gate_set, test_tiered_verification_e2e and test_timeout_kill_portable. Operator diagnosis: EveryAutonomyLevelStops calls _stub_agent() once per autonomy level, and _Base.tearDown restores self._patches in forward order, so the last setattr leaves loop.verify stubbed to (True, '(stub)') for the rest of the suite. Reproduced: that class followed by the two failing modules in one process gives FAILED (failures=9); a single-stub class gives OK. Added by the operator after the halt."
produces:
  - tests/test_terminal_judge_editing_end_to_end.py
model: sonnet
effort: low
gate_set: code
oracle_env: macos_local
driver_version: 0.30.0
started_at: 2026-10-29T12:32:16.771266+00:00
duration_seconds: 45.265
cost_usd: 0.133686
input_tokens: 12
output_tokens: 1953
---

# T05 — the oracle's patch helper restores the driver it found

**Objective.** Stop `tests/test_terminal_judge_editing_end_to_end.py` leaking stubbed
driver functions into every test that runs after it, so gate 1's broad run is green.

**Context.** `FEAT-2026-0246/T05`. This unit **edits** the oracle module T01
created and T03 extended; it does not create it. `_Base._patch` records `(name, getattr(loop, name))`
on every call, and `_Base.tearDown` restores the records **in recording order**.
`EveryAutonomyLevelStops` calls `self._stub_agent()` three times in one test (once per
`subTest`), so the records for `verify` are `(real, stub1, stub2)` and the last restore
writes `stub2`. `loop.verify` then returns `(True, "(stub)")` for the rest of the
process. The same holds for `dispatch` and `run_judge_session`. That is the whole of
the gate 1 broad-run failure: 14 unrelated tests asserting a verify failure see
`True is not false`.

Fix the helper, not the caller: restore in reverse recording order (or record only
the first original per name). Either is a correct last-in-first-out restore for any
number of `_patch` calls. Leave `EveryAutonomyLevelStops`' per-level stubbing as it
is; re-stubbing per `subTest` is legitimate once restore is correct.

Add a regression test **in the same module**, so the narrow tier, which runs only this
module, catches a recurrence: call `_stub_agent()` at least twice, run the cleanup
path, and assert that `loop.verify`, `loop.dispatch` and `loop.run_judge_session` are
the very objects captured before the first stub (`assertIs`).

**Acceptance criteria.**

1. The new regression test fails on the current tree and passes after the fix.
2. `python3 -m unittest tests.test_terminal_judge_editing_end_to_end.EveryAutonomyLevelStops tests.test_verify_empty_gate_set tests.test_timeout_kill_portable tests.test_tiered_verification_e2e -b`
   passes in one process; it fails on the current tree.
3. `python3 -m unittest tests.test_terminal_judge_editing_end_to_end -v -b` (the
   gate's `feature_oracle`) still passes, with no `unittest.skip` in the module.

**Do not touch.** Anything under `specfuse/` (the driver is correct; only the test
fixture leaks). Other test modules. The assertions of the existing oracle classes.

**Verification.** The narrow tier for `implementation`, plus the combined command in
acceptance criterion 2.

**Escalation triggers.** If criterion 2 still fails after the restore fix, another
patch is leaking (for example `os.chdir` or an environment variable). Name it and stop
rather than widen scope into other modules.
