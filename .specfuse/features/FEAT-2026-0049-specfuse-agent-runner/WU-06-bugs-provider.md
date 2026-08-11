---
id: FEAT-2026-0049/T06
type: implementation
status: done
attempts: 2
planned_cost_usd: 5.50
produces:
  - specfuse/agent/providers/bugs.py
  - tests/test_agent_provider_bugs.py
duration_seconds: 1091.65
cost_usd: 1.899535
input_tokens: 76
output_tokens: 27184
---

# T06 — the bugs provider

**Context.** The first real action class. This unit implements T05's provider
protocol (`advertise` / `execute` / `reconcile`) over one shipped function:

> `specfuse.loop.bug_lane_run.run_bug_lane(runner, repo, issue_number, *,
> working_dir, policy_path, now) -> BugLaneResult(outcome, reason, pr_number)`
> — "Run the bug lane for one issue: fix, PR, guarded merge."

**`run_bug_lane` is consumed unmodified.** PLAN.md's scope boundary forbids
modifying any surface the agent drives; the bug lane is the canonical example. A
provider that needs `run_bug_lane` to change is a plan change, not a WU detail —
see the escalation triggers.

The lane already owns everything downstream of the invocation: it evaluates
`evaluate_merge_guardrails` regardless of the `rules.bugs.automerge` dial, merges
only when the dial is `on` *and* the guardrails are eligible, and **files the
needs-human issue itself** on `refused` / `could_not_proceed`
(`bug_lane_run.py:306-308`). The provider therefore adds selection and outcome
mapping and nothing else. Its four outcome constants are `merged`, `declined`,
`refused`, `could_not_proceed`.

Selection input is T02's snapshot: `AgentSnapshot.issues` carries
`IssueSummary.triage_category`, already parsed from each issue body's triage
marker by `state._to_issue_summary` via `triage.parse_marker`. A bug is an open
issue whose category is `"bug"`. Untriaged issues are *not* this provider's
business — that is T07's.

**Acceptance criteria.**

1. `tests/test_agent_provider_bugs.py::TestBugsProvider::test_declined_outcome_escalates_without_second_issue`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_provider_bugs.TestBugsProvider.test_declined_outcome_escalates_without_second_issue`.
2. `specfuse/agent/providers/bugs.py` implements T05's protocol over
   `run_bug_lane`, importing and calling it — not vendoring it, not
   re-implementing any part of the lane, and not editing `specfuse/loop/`.
3. The same test passes after this WU's edits.
4. `advertise` returns one `kind="bug"` item per open snapshot issue whose triage
   category is `"bug"`, and returns nothing for an untriaged issue or an issue
   triaged to any other category. One test per case.
5. `execute` maps `merged` to a completed outcome and `declined` / `refused` /
   `could_not_proceed` to an escalated outcome whose detail names
   `BugLaneResult.reason` — the guardrail's own reason string, not a paraphrase.
6. **No second escalation.** For `refused` / `could_not_proceed` the lane has
   already filed the needs-human issue, so `reconcile` files none: a test asserts
   the injected runner receives no `gh issue create` from this module.
7. The provider is registered in `default_providers()` and the provider performs
   no git mutation of its own — it passes the injected runner through and issues
   no `git` command. A test asserts both.

**Do not touch.** `specfuse/loop/` entirely, and `specfuse/loop/bug_lane_run.py`
in particular — it is driven, not edited. `specfuse/monitor/`.
`specfuse/agent/state.py` and `specfuse/agent/budget.py` (gate-1 surfaces,
consumed). `specfuse/agent/run.py` **except** the one-line registration in
`default_providers()` — T05 owns that function's shape; this unit adds itself to
the list and changes nothing else in the file. The sibling gate-2 WU files
(`WU-05`, `WU-07`, `WU-08`) and their modules. The driver owns all git; this
session edits files only and runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol checks:
`python3 -c "from specfuse.agent.providers.bugs import BugsProvider; print(BugsProvider)"`
and `python3 -c "from specfuse.agent.run import default_providers; print([type(p).__name__ for p in default_providers(repo='o/r')])"`
naming the provider.

**Escalation triggers.** If mapping an outcome cleanly requires a change inside
`run_bug_lane` — a new return field, a changed constant, a seam that does not
exist — stop and name the change: PLAN.md's scope boundary makes that a plan
change, not a WU detail. If `IssueSummary` does not carry enough to decide
whether an issue is a bug (for instance if the issue number or state needed at
execute time is absent from the snapshot), stop and say what is missing rather
than issuing extra `gh` reads to paper over it — extending T02's snapshot is a
gate-1 surface change and is out of this unit's bounds.
