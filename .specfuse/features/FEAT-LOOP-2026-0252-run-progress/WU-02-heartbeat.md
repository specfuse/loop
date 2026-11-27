---
id: FEAT-LOOP-2026-0252/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/loop/progress.py
  - specfuse/loop/loop.py
  - .specfuse/verification.yml.example
  - specfuse/loop/data/verification.yml.example
  - tests/test_run_progress.py
produces_driver_helper:
  - resolve_heartbeat_seconds
model: sonnet
effort: medium
---

# T02 — heartbeat while an attempt runs

**Objective.** Turn Definition-of-done clause 3 green.

**Context.** `FEAT-LOOP-2026-0252/T02`; decisions 3 and 7 in `PLAN.md`.

- In `specfuse/loop/progress.py`, a daemon thread that rewrites `STATUS.json` every
  `heartbeat_seconds` with `updated_at`, `elapsed_seconds` and `files_touched`. Files touched
  come from `_paths_differing_from(head_before)` in `loop.py`, minus the driver's bookkeeping
  (the unit file, `events.jsonl`, `PROGRESS.md` in the feature folder, by full path).
- Start it in `loop.py` when an attempt starts and stop it in a `finally`, so it never
  outlives the attempt, including when the attempt raises.
- `resolve_heartbeat_seconds(verification_cfg)` next to `resolve_fail_fast_deliverables`:
  `defaults.heartbeat_seconds`, 30 when missing, not an integer or not positive. Document the
  key in `.specfuse/verification.yml.example` and `specfuse/loop/data/verification.yml.example`.

**Acceptance criteria.**

1. `tests.test_run_progress.TestHeartbeat` fails on HEAD and passes after (remove its skip).
   With `defaults.heartbeat_seconds: 1`, a stubbed session that writes `notes/a.txt` and runs
   for 3 s observes `updated_at` change at least twice while `phase` is `agent`, and
   `files_touched` includes `notes/a.txt` and not `events.jsonl`.
2. After `run()` returns, and after an attempt whose stubbed session raises, no thread started
   by `progress.py` is alive (`threading.enumerate()`).
3. `resolve_heartbeat_seconds` returns 30 for a missing key, `"x"`, `0` and `-5`, and 7 for `7`.
4. `python3 -m unittest tests.test_fail_fast_deliverables tests.test_dispatch_skeleton -b`
   passes.

**Do not touch.** `dispatch()`. Phase events (T01). `--watch` (T03). Notification and docs
under `docs/` (T04).

**Verification.** The narrow tier for `implementation`, plus AC4's command.

**Escalation triggers.** If `git` calls from the heartbeat thread contend with the driver's own
`git` calls (index lock errors), block with the evidence rather than adding a lock around
every driver `git` call.
