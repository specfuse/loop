---
id: FEAT-LOOP-2026-0253/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/progress.py
  - tests/test_gate_parallel_cache.py
produces_driver_helper:
  - _run_gate_set
model: sonnet
effort: medium
gate_set: code
driver_version: 0.33.2
started_at: 2026-11-27T04:42:53.181834+00:00
duration_seconds: 185.384
cost_usd: 0.42244
input_tokens: 20
output_tokens: 10813
---

# T02 — timeouts, events and the status file under parallel gates

**Objective.** Turn Definition-of-done clause 4 green.

**Context.** `FEAT-LOOP-2026-0253/T02`; decision 3 in `PLAN.md`. FEAT-LOOP-2026-0252 added
`gate_started` / `gate_finished` events and `STATUS.json` (`specfuse/loop/progress.py`), written
assuming one gate at a time.

- A gate that times out is killed with its process group and reported as today while the
  other running gates continue.
- Writes to `events.jsonl` and `STATUS.json` from worker threads are serialised (one lock in
  `specfuse/loop/progress.py`), so every line is whole and each event is written once.
- `STATUS.json` gains `gates_running` (the names of the gates running, in start order; `[]`
  outside the gate phase); `gate` stays one running gate's name (the most recently started),
  or null.

**Acceptance criteria.**

1. `tests.test_gate_parallel_cache.TestParallelSafety` fails on HEAD and passes after (remove its
   skip). With `max_parallel: 3` and `GATE_TIMEOUT_SECONDS` patched to 1 s, a stub that sleeps
   5 s is reported as a timeout and its process group is gone, while two 0.2 s gates pass.
2. With four parallel gates, `events.jsonl` has exactly one `gate_started` and one
   `gate_finished` per gate, and every line parses as JSON.
3. A stub gate reading `STATUS.json` while another gate runs sees `phase: gate` and both names
   in `gates_running`.
4. `python3 -m unittest tests.test_run_progress tests.test_gate_timings -b` passes.

**Do not touch.** The scheduler's ordering (T01). Caching (T03). Configuration errors and docs
(T04). `dispatch()`.

**Verification.** The narrow tier for `implementation`, plus AC4's command.

**Escalation triggers.** If serialising the writes needs a lock held across a gate's whole run,
block rather than serialising the gates.
