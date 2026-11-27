---
id: FEAT-LOOP-2026-0252/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/loop/progress.py
  - specfuse/loop/loop.py
  - specfuse/loop/agent_policy.py
  - .specfuse/agent-policy.yml.example
  - docs/getting-started.md
  - specfuse/loop/data/docs/getting-started.md
  - tests/test_run_progress.py
produces_driver_helper:
  - main
model: sonnet
effort: medium
---

# T04 — one notification when the run stops, and the docs

**Objective.** Turn Definition-of-done clause 6 green and document the feature.

**Context.** `FEAT-LOOP-2026-0252/T04`; decision 5 in `PLAN.md`.

- In `specfuse/loop/progress.py`, `notify_stop(...)`: work out `stop_reason` from the events
  this run appended to `events.jsonl` (remember the file's size when `run()` starts) and
  `PLAN.md`, in the order clause 6 gives; write it to `STATUS.json`; send the message once
  through `notify.post_notification` and once through `escalation.notify_command`, each only
  when configured.
- The command runs as `subprocess.run(shlex.split(cmd), env=..., timeout=30)`, never
  `shell=True`. The message is passed only in `SPECFUSE_MESSAGE`, never on the command line.
  Every failure (non-zero exit, timeout, missing program) is logged and swallowed.
- Call it from `main()` in `loop.py` in a `finally` around `run()`, skipped under `--dry-run`
  and `--watch`.
- In `specfuse/loop/agent_policy.py`, add `notify_command` to the known `escalation` keys:
  optional, a string. Add it to `.specfuse/agent-policy.yml.example` with a comment and a
  desktop-notifier example.
- In `docs/getting-started.md`, document the driver's phase lines, `--watch`, the status file,
  `defaults.heartbeat_seconds` and the stop notification; refresh the packaged copy
  `specfuse/loop/data/docs/getting-started.md` with `scripts/sync-scaffold.sh`.

**Acceptance criteria.**

1. `tests.test_run_progress.TestStopNotification` fails on HEAD and passes after (remove its
   skip). Each of the five stop reasons is produced by a run that reaches it, with a counting
   stub poster and a stub command each called exactly once, and the command receiving the four
   `SPECFUSE_*` variables.
2. A command that exits 1, one that sleeps past the timeout (patched to 1 s in the test) and
   one naming a missing program each leave `run()`'s exit code unchanged. With neither channel
   configured, and under `--dry-run`, the poster and the command are called zero times.
3. A message containing `; touch pwned` does not create `pwned`.
4. `python3 -m unittest tests.test_agent_policy_schema tests.test_notify tests.test_notify_escalation -b`
   passes; `agent_policy`'s validator accepts a string `notify_command` and reports an ERROR for
   a list.
5. `tests.test_run_progress` has no `unittest.skip` left.

**Do not touch.** `dispatch()`. `notify.py`'s existing behaviour. Phase events (T01), the
heartbeat (T02), `--watch` (T03), except to call `notify_stop`.

**Verification.** The narrow tier for `implementation`, plus AC4's command.

**Escalation triggers.** If two stop reasons apply to one run in a way clause 6's order does
not settle, block and name the case rather than choosing.
