---
id: FEAT-LOOP-2026-0252/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - specfuse/loop/progress.py
  - specfuse/loop/loop.py
  - tests/test_run_progress.py
produces_driver_helper:
  - main
model: sonnet
effort: medium
gate_set: code
driver_version: 0.33.2
started_at: 2026-11-27T03:15:51.138811+00:00
duration_seconds: 137.331
cost_usd: 0.446936
input_tokens: 24
output_tokens: 11063
---

# T03 — `specfuse-loop --watch`

**Objective.** Turn Definition-of-done clause 5 green.

**Context.** `FEAT-LOOP-2026-0252/T03`; decision 4 in `PLAN.md`.

- Add `--watch` to `main()` in `loop.py`; with `--feature` it resolves the feature as a run
  does, without it it uses the single active feature. The reader lives in
  `specfuse/loop/progress.py` and only reads files: it never takes the run lock and never
  writes.
- On a terminal it redraws one line in place; when stdout is not a terminal it prints a line
  only when the unit, attempt, phase or gate changes. Staleness is three heartbeat intervals
  (`resolve_heartbeat_seconds`, T02).

**Acceptance criteria.**

1. `tests.test_run_progress.TestWatch` fails on HEAD and passes after (remove its skip). Given
   a status file, the non-terminal output names the unit, attempt, phase, elapsed time and
   gate; a rewrite that changes only `elapsed_seconds` prints nothing new, a phase change
   prints one line.
2. An `updated_at` older than three heartbeat intervals prints `no update for Ns`.
3. `phase: stopped` ends the watch with exit 0; no status file exits 1 with a message naming
   the expected path.
4. `python3 -m unittest tests.test_dispatch_skeleton -b` passes.

**Do not touch.** `dispatch()`. Phase events and the status file's fields (T01). The heartbeat
thread (T02). Notification and docs (T04).

**Verification.** The narrow tier for `implementation`, plus AC4's command.

**Escalation triggers.** If `--watch` cannot be added without changing how `--feature` resolves
for a run, block rather than changing run resolution.
