---
id: FEAT-LOOP-2026-0204/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - specfuse/monitor/providers/azure_app_insights.py
  - tests/test_heartbeat_adapter.py
  - tests/test_monitor_finding_lifecycle_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T15:45:03.214493+00:00
duration_seconds: 78.121
cost_usd: 0.294099
input_tokens: 22
output_tokens: 6598
---

# T04 — a schedule is not "silent" before heartbeats began on its component

**Objective.** The `heartbeat` check ignores expected firings that precede the
component's earliest observed heartbeat, and a schedule that has never emitted reads
"pending first firing" rather than "silent" until its first expected firing after
emission began has passed.

**Context.** `FEAT-LOOP-2026-0204/T04`, gate 1; #3496 point 2. `_heartbeat_query`
(`specfuse/monitor/providers/azure_app_insights.py:509`) returns
`max(TimeGenerated)` per schedule name. A weekly schedule whose only expected firing
since the check began predates heartbeat emission therefore files a guaranteed false
`silent-schedule` (Backend#1019 `RescoreDisplacementJob`, #1020
`RollRosterHorizonJob`; both diagnosed as false positives). Add a second aggregate in
the **same** query — the component's earliest heartbeat across all schedules
(`min(TimeGenerated)` over the component's `ScheduleHeartbeat` events, e.g. via
`summarize … by name` plus a component-wide `min` joined or computed with
`toscalar` inside the one query; PLAN.md decision 7). In the adapter, an expected
firing earlier than that instant is not evaluated. If the component has **no**
heartbeat at all, every target is pending and nothing is filed — the check cannot
distinguish "never deployed" from "silent" without a liveness signal, which is gate
2's evidence, not this unit's.

**Acceptance criteria.**

1. `tests/test_monitor_finding_lifecycle_end_to_end.py::HeartbeatGrace`, skipped by
   T01 with a reason naming this unit, has its skip removed and passes: rows where the
   component's earliest heartbeat is 2026-10-14T13:50Z and a weekly target's latest
   expected firing is 2026-10-12T08:00Z with no heartbeat for that target → **no**
   finding.
2. `tests/test_heartbeat_adapter.py::TestHeartbeatGrace::test_missed_firing_after_emission_still_fires`:
   a target that emitted on 2026-10-14 and then missed its 2026-10-15 firing still
   files `silent-schedule`.
3. `tests/test_heartbeat_adapter.py::TestHeartbeatGrace::test_component_without_any_heartbeat_files_nothing` passes.
4. The query passes `tests/test_app_insights_query_schema_check.py`'s
   `schema_violations` with no new findings, and the adapter still issues exactly one
   `run_query` per `fetch_failures`.
5. The `observed_text` of a real silent finding still names the expected firing and
   the last heartbeat, unchanged in shape.

**Do not touch.** `specfuse/monitor/schedule.py`'s cron evaluation. Other adapters.
The finding-meta marker and `record_finding` (T01–T03).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_heartbeat tests.test_heartbeat_adapter tests.test_app_insights_query_schema_check -b`.

**Escalation triggers.** If the earliest-heartbeat value cannot be computed in the
same query without a construct the workspace schema check rejects, stop and escalate
with the candidate KQL rather than adding a second query.
