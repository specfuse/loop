---
id: FEAT-LOOP-2026-0203/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces:
  - specfuse/monitor/providers/azure_app_insights.py
  - tests/test_http_status_regression_adapter.py
  - tests/test_app_insights_query_schema_check.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.27.1
started_at: 2026-10-15T03:38:08.814112+00:00
duration_seconds: 116.518
cost_usd: 0.537765
input_tokens: 28
output_tokens: 15439
---

# T04 — the adapter detects the deployment and applies the regression rule

**Objective.** `HttpStatusRegressionAdapter` replaces T01's stubs with the real query
and the real rule: one KQL query, share of requests, 3× and at least 10, evaluated
only on a fully elapsed window.

**Context.** `FEAT-LOOP-2026-0203/T04`, gate 1. PLAN.md decisions 2, 5, 6 and 7 are the
specification; read them, do not re-derive them. The query is built from
configuration only (component, `codes`, `window_after_deploy`, a lookback) and runs
against the Log Analytics workspace schema (`AppRequests`, `AppRoleName`,
`AppVersion`, `ResultCode`, `TimeGenerated` — #3468). In **one** query it finds each
version's first-seen time for the component, keeps the deployments whose
after-window has fully elapsed, and returns per (version, code) the after-window and
before-window counts of that code plus each window's total request count. The
adapter computes the shares in Python.

The thresholds are module constants (for example `REGRESSION_FACTOR = 3` and
`REGRESSION_MIN_COUNT = 10`), named once and used once. A zero before-share fires on
at least 10 after-occurrences (decision 7). The before-window is the same length as
the after-window and ends at the deployment's first-seen time. #3471's
`tests/test_app_insights_query_schema_check.py` enumerates the built-in queries and
checks their tables and columns against the workspace schema reference: add this
query to that enumeration.

**Acceptance criteria.**

1. `tests/test_http_status_regression_adapter.py::RegressionRule::test_share_threshold`
   fails on HEAD (T01's stub fires on any increase) and passes after: over stub
   aggregates, a code at 2.9× the before-share with 50 occurrences yields nothing; at
   3.0× with 10 occurrences yields one artifact; at 5× with 9 occurrences yields
   nothing; a before-share of 0 with 10 occurrences yields one.
2. `test_traffic_ramp_is_not_a_regression`: the after-window has 4× the total requests
   and 4× the 401 count of the before-window (equal shares) and yields nothing.
3. `test_partial_window_is_not_evaluated`: aggregates for a deployment whose window
   has not elapsed at the adapter's reference time yield nothing; the same
   aggregates at a later reference time yield the artifact.
4. `test_query_is_configuration_only`: the one query names `AppRequests`,
   `AppRoleName`, `AppVersion`, `ResultCode` and `TimeGenerated`, contains each
   configured code, and contains no value from the stub's returned rows.
5. `python3 -m unittest tests.test_app_insights_query_schema_check -b` exits 0 with
   the new query in its enumeration, and the gate's `feature_oracle` still exits 0.

**Do not touch.** The other App Insights query builders and their tests (`#3469`,
`#3470` pinned them). `build_app_insights_transport`'s `timespan` argument — the
window lives in the KQL, not in the transport. The lint rules (T03). `cli.py` beyond
what T01 wired.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_app_insights_adapters tests.test_app_insights_workspace_schema tests.test_heartbeat_adapter -b`.

**Escalation triggers.** If one KQL query cannot return the per-version, per-code
window aggregates, stop and escalate with the query you tried: splitting it into two
queries folds a returned value into a query (PLAN.md decision 5), and that is not this
unit's call to make. If a column the query needs is absent from #3471's schema
reference, stop rather than adding it to the reference unsourced.
