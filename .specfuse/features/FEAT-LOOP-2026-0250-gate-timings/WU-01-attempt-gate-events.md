---
id: FEAT-LOOP-2026-0250/T01
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 4.00
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/data/schemas/driver-event.schema.json
  - tests/test_gate_timings.py
produces_driver_helper:
  - _run_gate_set
model: sonnet
effort: medium
duration_seconds: 67.084
cost_usd: 0.384186
input_tokens: 28
output_tokens: 8642
gate_set: code
driver_version: 0.33.2
started_at: 2026-11-25T15:27:11.734142+00:00
---

# T01 — walking skeleton: attempt-phase `gate_result` events

**Objective.** Make the gate's `feature_oracle` runnable and turn clause 1 and clause 5's
schema half green. This is the tracer bullet: stubs are allowed here only.

**Context.** `FEAT-LOOP-2026-0250/T01`; decisions 4 and 6 in `PLAN.md`.

- `_run_gate_set()` (`loop.py`) times each gate it actually spawns with `time.monotonic()` and
  adds `duration_seconds` to that gate's result dict. A gate skipped for a failed dependency
  gets `duration_seconds: 0` and `skipped: True`. Existing keys and the return contract are
  otherwise unchanged.
- Per attempt, the driver appends one `gate_result` event per gate to `wu_events` (correlation
  ID: the unit's), payload `{attempt, gate, ok, skipped, duration_seconds, phase: "attempt"}`,
  flushed with `attempt_outcome`. How the per-gate results reach the attempt loop from
  `verify()` is your call; existing `verify_fn` stubs must keep working unchanged.
- Add `gate_result` to `event_types` in `specfuse/loop/data/schemas/driver-event.schema.json`
  and append a `FEAT-LOOP-2026-0250/T01` sentence to its `$comment`, in the existing style.

Create `tests/test_gate_timings.py`, one class per Definition-of-done clause in `GATE-01.md`:
`TestAttemptGateEvents`, `TestAttemptSplit`, `TestBaselineAndBroadPhases`, `TestStatsReport`,
`TestNothingExistingChanges`. Implement clause 1 and the schema half of clause 5; skip the rest
naming T02, T03, T04.

**Acceptance criteria.**

1. `tests.test_gate_timings.TestAttemptGateEvents` fails on HEAD and passes after. It drives one
   attempt with a stubbed agent session and three real gates (one passing with a known sleep,
   one failing, one depending on the failing gate) plus a `feature_oracle`, and asserts one
   `gate_result` per gate with the payload above and each spawned gate's duration at least
   its sleep.
2. `TestNothingExistingChanges` asserts `gate_result` is in the schema's `event_types`.
3. `python3 -m unittest tests.test_dispatch_skeleton tests.test_loop_worklist_injection -b`
   passes unchanged.

**Do not touch.** `execute_unit_attempt()`'s agent/verify timers and `emit_attempt_outcome()`
(T02). `probe_baseline()` and `gate_broad_run_check` (T03). `events_stats.py` and docs (T04).

**Verification.** The narrow tier for `implementation`, plus AC3's command.

**Escalation triggers.** If per-gate results cannot reach the attempt loop without changing the
`verify_fn` call signature that existing stubs implement, block with the evidence.
