---
id: FEAT-LOOP-2026-0204/T08
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - specfuse/monitor/providers/azure_app_insights.py
  - specfuse/monitor/providers/azure_service_bus.py
  - tests/test_monitor_finding_context_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T15:54:20.760618+00:00
duration_seconds: 115.864
cost_usd: 0.544787
input_tokens: 32
output_tokens: 12549
---

# T08 — a silent schedule says whether the job ran and the host was up; a stalled queue says how stale

**Objective.** A `heartbeat` finding shows the schedule, the function's last execution
and whether the role sent any telemetry during the gap; a `queue-stalled` finding
shows the oldest active message's age alongside today's depth.

**Context.** `FEAT-LOOP-2026-0204/T08`; T04's grace (already in `_heartbeat_query`), T05's
`context` model. Backend#1019's diagnosis needed four queries to learn that the job
had run late after a four-day worker outage nobody detected. Extend
`_heartbeat_query` — still **one** query — with, per schedule name, the function's
last `AppRequests` execution (name match on the target's configured function, when
the target names one; otherwise omitted) and its result, and, for the component, the
latest `AppRequests` row of any kind (the host's last sign of life). The adapter adds
Schedule (cron, dialect, timezone from the target), Last run, Host last seen and, when
the host's last sign of life precedes the expected firing, a **Host silent** line
naming the gap. For `queue-stalled`
(`specfuse/monitor/providers/azure_service_bus.py`), add the oldest active message's
age from the runtime properties the transport already reads.

**Acceptance criteria.**

1. `tests/test_monitor_finding_context_end_to_end.py::HeartbeatContext` and
   `::QueueStalledContext` (skipped by T01, naming this unit) have their skips removed
   and pass: a heartbeat fixture where the host's last request precedes the expected
   firing renders Schedule, Last run and a Host silent line; a queue-stalled fixture
   renders depth and oldest message age.
2. `_heartbeat_query` passes `schema_violations` and the heartbeat adapter still issues
   exactly one `run_query`; T04's grace tests still pass.
3. `grep -n 'unittest.skip' tests/test_monitor_finding_context_end_to_end.py tests/test_monitor_finding_lifecycle_end_to_end.py`
   reports nothing at this unit's tree: every check type's oracle class runs.

**Do not touch.** `schedule.py`. T04's grace logic. The fingerprint.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_heartbeat_adapter tests.test_queue_stalled_adapter tests.test_app_insights_query_schema_check -b`.

**Escalation triggers.** If the host-liveness aggregate makes the heartbeat query
scan the component's whole `AppRequests` history, bound it to the lookback the
expected firing implies and say so; if that is not expressible in one query, escalate.
