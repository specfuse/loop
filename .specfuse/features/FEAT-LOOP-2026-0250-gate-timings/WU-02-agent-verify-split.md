---
id: FEAT-LOOP-2026-0250/T02
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 3.00
produces:
  - specfuse/loop/loop.py
  - tests/test_gate_timings.py
produces_driver_helper:
  - execute_unit_attempt
  - emit_attempt_outcome
model: sonnet
effort: medium
---

# T02 — `agent_seconds` and `verify_seconds` on `attempt_outcome`

**Objective.** Split each attempt's time between the agent session and verification, so
clause 2 of `GATE-01.md` goes green.

**Context.** `FEAT-LOOP-2026-0250/T02`; decision 5 in `PLAN.md`.

- In `execute_unit_attempt()`, time the agent-session call (`dispatch_fn`) and the gate-set call
  (`verify_fn`) with `time.monotonic()` and return both in the attempt's usage dict as
  `agent_seconds` and `verify_seconds`. A path that returns before `verify_fn` runs (blocked,
  zero-token, prep halted) records `verify_seconds: 0`.
- `emit_attempt_outcome()` adds both to the payload, defaulting to `0.0` when absent.
  `duration_seconds` keeps its current meaning: the attempt loop's own total.

**Acceptance criteria.**

1. `tests.test_gate_timings.TestAttemptSplit` fails on HEAD and passes after. With a stubbed
   agent session that sleeps a known time and a real gate that sleeps a known time, it asserts
   `agent_seconds` and `verify_seconds` are each at least their sleep and their sum is at most
   `duration_seconds`.
2. The same class asserts an attempt whose agent reports `blocked` records `verify_seconds: 0`.
3. `python3 -m unittest tests.test_dispatch_skeleton tests.test_files_changed_auto_repair -b`
   passes unchanged.

**Do not touch.** `_run_gate_set()` beyond reading what T01 added. `probe_baseline()` and
`gate_broad_run_check` (T03). `events_stats.py` and docs (T04).

**Verification.** The narrow tier for `implementation`, plus AC3's command.

**Escalation triggers.** If any `attempt_outcome` consumer (`gate_eval.py`, `events_stats.py`,
`learnings_suggest`) rejects or misreads the two new keys, block with the evidence.
