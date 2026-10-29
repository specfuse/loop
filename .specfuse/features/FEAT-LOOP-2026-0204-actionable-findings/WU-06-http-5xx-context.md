---
id: FEAT-LOOP-2026-0204/T06
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - specfuse/monitor/providers/azure_app_insights.py
  - tests/test_monitor_finding_context_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T15:52:08.437870+00:00
duration_seconds: 71.756
cost_usd: 0.427201
input_tokens: 28
output_tokens: 9942
---

# T06 — an `http-5xx` finding names the exception and the dependency behind it

**Objective.** An `http-5xx` finding carries the exception that produced the 5xx and
the failing or slowest dependency of that request, from its one query.

**Context.** `FEAT-LOOP-2026-0204/T06`; T05's `context` model and renderer. Today
`_http_5xx_query` projects route and result code only. Extend it with joins inside
the one query on `OperationId`: `AppExceptions` (type, outer message, top in-app frame
— reuse T05's frame helper) and `AppDependencies` (target, type, result code,
duration; prefer a failed dependency, else the slowest). Add request duration,
`AppRoleInstance` and up to 3 samples. The dry run's Auth0 500 is the motivating
case: its finding should say the outbound management-API call returned 401.

**Acceptance criteria.**

1. `tests/test_monitor_finding_context_end_to_end.py::Http5xxContext` (skipped by T01,
   naming this unit) has its skip removed and passes: fixture rows of a 500 whose
   request has one failed dependency (`401` from an external HTTP target) and one
   exception render Exception, Where, Dependency (target, type, 401), Duration,
   Samples and Reproduce.
2. A 5xx with no exception and no dependency still files, with those sections absent
   rather than empty.
3. `_http_5xx_query` passes `schema_violations` and the adapter issues exactly one
   `run_query`.

**Do not touch.** `http-status-regression` (it has its own body, #3477). The
fingerprint (`route:status`).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_app_insights_adapters tests.test_app_insights_query_schema_check -b`.

**Escalation triggers.** If joining both tables in one query multiplies rows (one row
per exception × dependency), stop and escalate with the measured shape rather than
filing duplicates; per-cycle aggregation (T05) dedupes only by fingerprint.
