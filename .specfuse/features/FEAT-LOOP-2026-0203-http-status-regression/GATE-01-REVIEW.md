# Gate-1 arming review — FEAT-LOOP-2026-0203

Pre-arming record required by `GATE-01.md` § Arming discipline. Gate 1 is the
feature's only gate; there is no `plan-next`, so this file is written by hand at
arming time, not by a closing unit.

## Runtime probe (`planning-discipline.md` §4) — T02's severity flip

- **Date:** 2026-10-14, on `main` at the commit this feature branched from.
- **Change applied (throwaway worktree, discarded after):** in
  `specfuse/loop/lint_monitoring.py`, the `queue-stalled` branch of the check
  validation emitted an error for any target whose `stall_after` does not match
  `^(\d+)([smhd])$` — the grammar `parse_stall_after_seconds` already enforces at
  runtime.
- **Command:** `python3 -m unittest discover -s tests -b`
- **Result:** `Ran 4533 tests` — `FAILED (failures=1, skipped=4)`.
- **Failure list:**
  - `test_lint_monitoring.TestQueueStalled.test_queue_stalled_threshold_coordinate_is_opaque`

This is the expected list and nothing else: the one test that pins the old
"opaque" position, which T02 replaces by design. No shipped example, fenced
block or fixture carries a `stall_after` the grammar rejects, which confirms
PLAN.md's satisfiability answer. T02 is cleared to arm.
