---
id: FEAT-LOOP-2026-0252/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/loop/progress.py
  - specfuse/loop/loop.py
  - specfuse/loop/arm_eval.py
  - specfuse/loop/data/schemas/driver-event.schema.json
  - tests/test_run_progress.py
produces_driver_helper:
  - execute_unit_attempt
  - _run_gate_set
model: sonnet
effort: medium
---

# T01 — walking skeleton: phase events, the status file and plain driver lines

**Objective.** Make the gate's `feature_oracle` runnable and turn Definition-of-done clauses 1,
2 and 4 green. This is the tracer bullet: stubs are allowed here only.

**Context.** `FEAT-LOOP-2026-0252/T01`; decisions 2 and 4 in `PLAN.md`.

- Create `specfuse/loop/progress.py` with the status-file writer (atomic replace of
  `<feature>/work/STATUS.json`) and one function per phase change that appends the event to
  `events.jsonl` at once (one-event `flush_events`, not the `wu_events` buffer), rewrites the
  status file, and prints the plain line. Register the module in `NON_JUDGE_MODULES` in
  `specfuse/loop/arm_eval.py` ("reports progress; changes no verdict").
- Call it from `loop.py`: around the agent session in `execute_unit_attempt()` (not inside
  `dispatch()`, which stays unchanged), and around each gate command in `_run_gate_set()`.
  Between units the phase is `between`; when `run()` returns it is `stopped` (T04 adds
  `stop_reason`; here write `stop_reason: null`).
- Add `agent_session_started`, `agent_session_finished`, `gate_started` and `gate_finished` to
  `specfuse/loop/data/schemas/driver-event.schema.json`, with a `$comment` line like the
  existing ones.

Create `tests/test_run_progress.py`, one class per clause: `TestPhaseEvents`, `TestStatusFile`,
`TestHeartbeat`, `TestDriverLines`, `TestWatch`, `TestStopNotification`. Implement the first
two and `TestDriverLines`; skip the rest naming T02, T03, T04.

**Acceptance criteria.**

1. `tests.test_run_progress.TestPhaseEvents` fails on HEAD and passes after. Through
   `loop.run()` with a stubbed session and two stub gate commands, `events.jsonl` gains
   `agent_session_started`, `agent_session_finished`, then `gate_started`/`gate_finished` for
   each gate, in that order, each validating against the packaged schema. The stubbed session
   finds its own `agent_session_started` in `events.jsonl` while it runs, and the second gate
   command finds its own `gate_started`.
2. `TestStatusFile` passes: during the session the stub reads `STATUS.json` with every field
   clause 2 names, `phase: agent` and `gate: null`; a stub gate reads `phase: gate` and its own
   name; after `run()` returns, `phase` is `stopped`; `git ls-files` does not list the file.
3. `TestDriverLines` passes: captured driver output has one line per phase change and contains
   no `\r` and no `\x1b`.
4. `python3 -m unittest tests.test_judge_path_registry tests.test_driver_event_registry_covers_emitters tests.test_validate_event_driver_types tests.test_gate_timings tests.test_dispatch_skeleton -b`
   passes. Any existing test changed because it matches driver output text is listed in the
   RESULT's notes.

**Do not touch.** `dispatch()` and `parse_claude_json_output()`. The `attempt_outcome` payload
and `gate_result` events. The heartbeat thread (T02), `--watch` (T03), notification and docs
(T04).

**Verification.** The narrow tier for `implementation`, plus AC4's command.

**Escalation triggers.** If a phase event written mid-attempt is lost by a reset, or lands in
the unit's squash commit in a way a guard reads as the agent's own change, block with the
evidence rather than routing it through the `wu_events` buffer.
