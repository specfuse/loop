---
id: FEAT-2026-0108/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
model: sonnet
effort: medium
oracle_env: macos_local
produces:
  - specfuse/agent/invoke.py
  - plugins/specfuse/skills/fix-bug/SKILL.md
  - tests/test_agent_invoke_timeout.py
---

# Gate commands run in the foreground, and the invocation has a real timeout

**Objective.** Twenty of 72 escalations in the 2026-09-02 run were finished
fixes whose headless session ended while it "waited for the background test
run's completion notification" (#3178). Make the headless `/fix-bug` session
run its gate commands in the foreground, and give every agent-lane invocation
a wall-clock timeout the runner enforces, sized from policy rather than left to
the session.

**Context.** FEAT-2026-0108/T03; read `PLAN.md`. `_default_runner`
(`agent/run.py:221`) is a bare `subprocess.run` with no timeout; the session's
own turn or wall limit is what ended those items. Two changes. (1) `/fix-bug`
step 6 (canonical `plugins/specfuse/skills/fix-bug/SKILL.md`, synced by
`scripts/sync-scaffold.sh`) gains a headless-mode rule: gate commands run in
the foreground with the skill waiting on their exit; never as a background
task awaiting a notification, because a headless session that ends its turn
waiting has ended. (2) `run_claude` (T01) accepts `timeout_seconds`, passes it
to the runner, and returns `timed_out=True` with whatever text was captured;
`agent-policy.yml` `budgets:` gains `item_timeout_minutes` (default 45), read
by `agent_policy.py` beside the other budget keys. A timed-out item escalates
`could_not_proceed` with the elapsed time in the detail. Red test first.

**Acceptance criteria.**

- `tests/test_agent_invoke_timeout.py::test_runner_timeout_is_reported_not_raised` fails on HEAD and passes after: a runner raising `subprocess.TimeoutExpired` yields `timed_out=True`, captured text intact, no exception.
- `tests/test_agent_invoke_timeout.py::test_item_timeout_comes_from_policy`: a policy file with `budgets.item_timeout_minutes: 7` produces a `run_claude` call with `timeout_seconds=420`; absent key gives the default.
- `grep -c "foreground" plugins/specfuse/skills/fix-bug/SKILL.md` reports at least 1, in the headless-mode section, and `grep -c "run_in_background\|background task" plugins/specfuse/skills/fix-bug/SKILL.md` reports 0 outside that prohibition.
- `tests/test_agent_provider_bugs.py` gains `test_timed_out_item_escalates_with_elapsed_time`.
- `bash scripts/sync-scaffold.sh` leaves `git status --porcelain .specfuse/skills` empty.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** the WU driver module (everything under `specfuse/loop/` not named in `produces:`); the worktree module (T02);
`bug_lane.py` (T04); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if the CLI offers no way to
bound a headless session that the runner's timeout does not already cover;
name what was tried.
