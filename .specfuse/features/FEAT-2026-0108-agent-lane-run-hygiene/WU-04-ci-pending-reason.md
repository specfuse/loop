---
id: FEAT-2026-0108/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
model: sonnet
effort: medium
oracle_env: macos_local
produces_driver_helper: REASON_CI_PENDING
produces:
  - specfuse/loop/bug_lane.py
  - specfuse/loop/bug_lane_run.py
  - specfuse/loop/labels.py
  - tests/test_bug_lane_ci_pending.py
---

# A pending CI run is declined as `ci_pending`, never as `ci_not_green`

**Objective.** Seven escalations in the 2026-09-02 run said the `ci_not_green`
guardrail declined a PR whose build was still queued; all seven went green
minutes later and were merged by hand (#3177). Give the pending state its own
declining reason and label so the escalation says "retry", not "red".

**Context.** FEAT-2026-0108/T04; read `PLAN.md` § Escalation-predicate
satisfiability. `pr_ci_conclusion` (`bug_lane_run.py`) already polls to
`CI_WAIT_SECONDS`; its docstring says a pending-at-deadline result is still
reported as `_CI_UNKNOWN` and that splitting it out "is safe whenever someone
wants it". Return the public string `"pending"` at the deadline instead.
`evaluate_merge_guardrails` (`bug_lane.py:174`) declines `"pending"` as
`REASON_CI_PENDING = "ci_pending"` before the generic `!= "success"` check;
`DECLINE_LABELS` gains `bug-lane:ci-pending`; `labels.py` registers it with a
description saying the run was still pending at the deadline and a retry is
the response. Make `CI_WAIT_SECONDS` overridable from `agent-policy.yml`
`budgets.ci_wait_minutes` so a repository with an 8-minute CI can set 12. The
provider's declined payload for this reason should say "CI had not concluded
after N minutes; re-run the lane" rather than the generic guardrail text. Red
test first.

**Acceptance criteria.**

- `tests/test_bug_lane_ci_pending.py::test_pending_at_deadline_declines_ci_pending` fails on HEAD and passes after: a runner whose checks stay `pending` past the deadline yields `reason == "ci_pending"` and the label call names `bug-lane:ci-pending`.
- `tests/test_bug_lane_ci_pending.py::test_red_run_still_declines_ci_not_green`.
- `tests/test_bug_lane_labels_registered.py` passes unchanged (the registry test finds the new label).
- `tests/test_bug_lane_ci_pending.py::test_ci_wait_comes_from_policy`: `budgets.ci_wait_minutes: 12` yields a 720 s deadline.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `specfuse/loop/loop.py`; `specfuse/agent/` except the
provider's declined-payload branch for this one reason; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus
`python3 -c "from specfuse.loop.bug_lane import REASON_CI_PENDING, DECLINE_LABELS; assert DECLINE_LABELS[REASON_CI_PENDING]"` exits 0.

**Escalation triggers.** Emit `status: blocked` if any consumer treats the
declining-reason set as closed in a way a ninth value breaks (an enum, a
schema, a docs table asserted by test); name it.
