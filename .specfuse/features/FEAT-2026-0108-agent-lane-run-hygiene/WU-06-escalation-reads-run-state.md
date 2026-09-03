---
id: FEAT-2026-0108/T06
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
model: sonnet
effort: medium
oracle_env: macos_local
produces:
  - specfuse/agent/providers/bugs.py
  - tests/test_agent_escalation_run_state.py
---

# An escalation says what the run actually left behind

**Objective.** Item #1481 in the 2026-09-02 run had already opened PR #1532
and still escalated with text saying the lane "never reached a guardrail or
merge decision" (#3178). Two items left commits on unpushed branches that no
issue mentioned. Make every escalation payload read run state: an open PR is
named and linked; an unpushed branch or a `wip/<item_id>` ref (T02) is named
with its commit count; the generic "no PR existed" sentence appears only when
that is true.

**Context.** FEAT-2026-0108/T06; read `PLAN.md`. `_fix_bug_stopped_payload`
and `_abandoned_work_payload` in `providers/bugs.py` already branch on
`result.unpushed_work`; extend `BugLaneResult` with `pr_number` populated from
T05 even on a stopped outcome (a session can open a PR and then stop) and the
`wip_ref` T02 records, and let the payloads render whichever exist. Red test
first; mirror `tests/test_agent_provider_bugs.py`'s patching of
`run_bug_lane`.

**Acceptance criteria.**

- `tests/test_agent_escalation_run_state.py::test_stopped_item_with_open_pr_links_it` fails on HEAD and passes after: `outcome=could_not_proceed, pr_number=1532` yields a payload containing `PR #1532` and not "never reached a guardrail".
- `tests/test_agent_escalation_run_state.py::test_wip_ref_is_named_with_commit_count`.
- `tests/test_agent_escalation_run_state.py::test_nothing_left_behind_keeps_generic_text`.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** the WU driver module (everything under `specfuse/loop/` not named in `produces:`); `bug_lane.py`; the invoke modules;
`.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if `BugLaneResult` cannot gain
the fields without breaking a positional construction in an existing test;
name the test rather than reordering fields.
