<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# FEAT-2026-0204 — follow-ups

Written by `FEAT-2026-0204/G1-CLOSE` under `close-discipline.md` §2: the terminal
verdict is `not_met`, and each entry below is one tracked follow-up the driver
files as a `specfuse:follow-up` issue. Both entries are the same failed Definition-of-done
clause, split by check type because each needs a different change.

### A `heartbeat` finding does not carry the component's earliest heartbeat

**Tracked as #3504.**

**Criterion, verbatim (`GATE-01.md`, Definition of done, clause 7):**

> For each of `error-logs`, `http-5xx`, `dlq`, `heartbeat` and `queue-stalled`, a
> finding built from fixture rows carries the sections `PLAN.md`'s "Diagnostic
> context" names for that check; each check still issues exactly one query, every
> query passes the workspace schema check, and every section is redacted before
> egress.

`PLAN.md`'s "Diagnostic context" names, for `heartbeat`: "the schedule's cron and
timezone; the function's last execution from `AppRequests` and its result; the
component's earliest heartbeat; whether the role sent any telemetry in the silent
gap".

**Evidence.** `_heartbeat_context` (`specfuse/monitor/providers/azure_app_insights.py`)
builds `Schedule`, `Last run`, `Host last seen` and `Host silent`. The earliest
heartbeat is read from each row's `first_heartbeat` (line 842) and used only to
decide the grace; it is never put in `context`.
`tests.test_monitor_finding_context_end_to_end.HeartbeatContext.test_sections_present`
asserts those four sections and has no needle for the earliest heartbeat. No unit
records dropping it: `WU-08`'s criteria name the other four sections only.

**Re-run condition.** A rendered `heartbeat` finding from a fixture whose rows carry
`first_heartbeat` shows the component's earliest heartbeat in UTC (for example an
`Earliest heartbeat` section), `HeartbeatContext.test_sections_present` asserts it,
the heartbeat query still issues one `run_query` and passes `schema_violations`, and
`docs/concepts/monitoring-runners.md`'s "What a finding contains" table and its
closing sentence are updated to match.

### A `queue-stalled` finding does not carry the subscription's last completed message

**Tracked as #3505.**

**Criterion, verbatim (`GATE-01.md`, Definition of done, clause 7):** as in the
entry above.

`PLAN.md`'s "Diagnostic context" names, for `queue-stalled`: "oldest active message
age and the subscription's last completed message, in addition to today's depth".

**Evidence.** `QueueStalledAdapter` (`specfuse/monitor/providers/azure_service_bus.py`)
builds `Where` and `Queue` (oldest active message age, depth, `stall_after`).
Its transport protocol has `get_active_message_count` and
`get_oldest_message_enqueued_time` and nothing that reads when a message was last
completed, so there is no value to render.
`HeartbeatContext`'s sibling `QueueStalledContext.test_sections_present` asserts the
age and depth only. `WU-08` names only the oldest age, and no unit records why the
last completed message was left out.

**Re-run condition.** Either the transport gains a read for the subscription's last
completed message (or a documented reason it cannot be read from the runtime
properties the transport already holds, recorded in `PLAN.md` and the docs) and a
rendered `queue-stalled` finding shows it, with `QueueStalledContext` asserting it;
or the plan's list is amended to drop it with that reason. The queue-stalled check
must still never receive, complete or abandon a message.
