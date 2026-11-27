---
id: FEAT-LOOP-2026-0253/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/loop/loop.py
  - tests/test_gate_parallel_cache.py
produces_driver_helper:
  - _run_gate_set
  - resolve_max_parallel
model: sonnet
effort: medium
---

# T01 — walking skeleton: a scheduler for `_run_gate_set()` bounded by `max_parallel`

**Objective.** Make the gate's `feature_oracle` runnable and turn Definition-of-done clauses 1,
2 and 3 green. This is the tracer bullet: stubs are allowed here only.

**Context.** `FEAT-LOOP-2026-0253/T01`; decisions 2 and 3 in `PLAN.md`.

- In `specfuse/loop/loop.py`, split the body of the `for gate in gate_set:` loop in
  `_run_gate_set()` into a per-gate function that returns the result dict it builds today, and
  drive it from a scheduler: a gate is ready once every gate it `needs` has ended; at most
  `max_parallel` run at once (a thread pool; each gate is still its own subprocess with its
  own process group and timeout); a gate whose dependency failed is `SKIP` without running.
  With `max_parallel` 1 the scheduler must start gates in exactly the order the loop did.
- `resolve_max_parallel(verification_cfg)` next to `resolve_fail_fast_deliverables`:
  `defaults.max_parallel`, 1 when missing. Validation of bad values is T04's; here anything
  that is not an integer ≥ 1 means 1.
- Return results in the declared order whatever the finishing order. `_capture_returncodes`
  keeps its contract.

Create `tests/test_gate_parallel_cache.py`, one class per clause group: `TestDefaultUnchanged`,
`TestParallel`, `TestResultOrder`, `TestParallelSafety`, `TestCacheHit`, `TestCacheMiss`,
`TestNeverForAVerdict`, `TestConfigurationErrors`. Implement the first three; skip the rest
naming T02, T03, T04. Stub gates are small Python commands that append their start and end
time to a file outside the tree and sleep.

**Acceptance criteria.**

1. `tests.test_gate_parallel_cache.TestParallel` fails on HEAD and passes after: with
   `max_parallel: 2`, two independent stub gates' recorded intervals overlap; with 1 they do
   not; with 3 independent gates and `max_parallel: 2`, no instant has three running. A gate
   with `needs: [a]` starts after `a` ends; with `a` failing it is `SKIP` and its stub never
   records a start.
2. `TestDefaultUnchanged` passes: for a set of a passing gate, a failing gate and a gate that
   `needs` the failing one, the results without `max_parallel` equal (names, `ok`, `skipped`,
   report text with durations removed) those produced by the loop before this unit. Show it
   fails or diverges with the scheduler starting gates out of order.
3. `TestResultOrder` passes: when a later-declared gate finishes first, results, the joined
   report and `parse_gate_failure_signature`'s output follow declared order.
4. `python3 -m unittest tests.test_gate_timings tests.test_run_progress tests.test_dispatch_skeleton -b`
   passes; any test changed because of new report text is listed in the RESULT's notes.

**Do not touch.** `order_gate_set`'s ordering rules. `STATUS.json` fields and timeout handling
beyond moving them (T02). Caching (T03). Configuration errors and docs (T04).

**Verification.** The narrow tier for `implementation`, plus AC4's command.

**Escalation triggers.** If a gate's subprocess cannot be run from a worker thread with its
process-group kill intact on any supported platform (the Windows Git-Bash path included),
block with the evidence rather than dropping the kill.
