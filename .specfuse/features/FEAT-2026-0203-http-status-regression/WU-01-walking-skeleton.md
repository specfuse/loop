---
id: FEAT-2026-0203/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
oracle_env: macos_local
produces:
  - tests/test_http_status_regression_end_to_end.py
  - specfuse/monitor/providers/azure_app_insights.py
  - specfuse/monitor/cli.py
  - specfuse/monitor/artifact.py
  - specfuse/loop/lint_monitoring.py
---

# T01 — an http-status-regression check runs end to end, thinly

**Objective.** The gate's `feature_oracle` goes from red to green: an
`http-status-regression` check passes lint, reaches its adapter through
`run_cycle`, and files one finding per (component, status code, deployment).

**Context.** `FEAT-2026-0203/T01`, gate 1. **This unit is the walking skeleton**
(`/authoring-work-units` §14) and the only unit in the gate permitted to stub. Write
the oracle module **first**: `GATE-01.md`'s `feature_oracle` is appended to every
attempt's gate list, so it must exist before anything else lands.

Wire the thinnest path through every layer the check crosses:
`specfuse/loop/lint_monitoring.py` (`CHECK_TYPES` at l.45; the targetless set at
l.278), `specfuse/monitor/artifact.py` (its own `_TARGETLESS_CHECK_TYPES` at l.34,
duplicated on purpose), `specfuse/monitor/cli.py` (`_build_adapter` at l.244 must pass
`deploy_signal`, `window_after_deploy` and `codes` through to the adapter), and a new
`HttpStatusRegressionAdapter` in `specfuse/monitor/providers/azure_app_insights.py`,
which `cli._find_adapter_class` resolves by name. The fingerprint is
`fingerprint.py`'s existing model: `failure_class` is the status code and
`failure_signature` is `<version>:<code>`, so the deployment is part of the identity.

Stubbable here, and only here: the KQL text (T04 owns the one real query — this unit
may build a placeholder from configuration only); the regression rule (T04 owns
share-of-requests at 3× / ≥10 — this unit may fire on any after-count above the
before-count); lint of the new fields (T03 owns `deploy_signal`, `window_after_deploy`
and `codes` — this unit only adds the type to `CHECK_TYPES` and the targetless sets).
**Not** stubbable: PLAN.md decision 5. The adapter issues exactly one
`run_query` call per `fetch_failures`, built from configuration only.

**Acceptance criteria.**

1. `tests/test_http_status_regression_end_to_end.py::HttpStatusRegressionEndToEnd::test_one_deployment_files_one_finding_per_code`
   fails on HEAD (absent module) and passes after: `run_cycle(config, dry_run=True,
   transport_resolver=<stub>, now=..., watermark_dir=<tmp>, out=StringIO())` over a
   config whose component declares the check prints exactly one
   `would file:` line containing `check_type=http-status-regression` and `401`, and
   `validate_monitoring` returns no errors for that config.
2. `test_same_rows_same_fingerprint`: two cycles over the same stub rows yield
   artifacts whose `fingerprint_artifact` values are equal, and differ when only the
   deployment's version string changes.
3. `test_adapter_issues_one_query`: the stub transport records exactly one query per
   `fetch_failures` call, and no returned row value appears in it.
4. `GATE-01.md`'s `feature_oracle` command exits 0 at this unit's tree.

**Do not touch.** The `http-5xx`, `error-logs`, `heartbeat` and `invariant` query
builders and adapters. `specfuse/monitor/issues.py` and `fingerprint.py` (read
through their published names only). Sibling units' surfaces: the duration grammar
(T02), the schema doc and example files (T03), `derive-monitoring` and the design rule
(T05).

**Verification.** The narrow tier for `implementation`, with `tests` narrowed to this
unit's `produces:` test module, plus
`python3 -m unittest tests.test_monitor_cli tests.test_app_insights_adapters -b`
(existing dispatch unbroken) and
`python3 -c "from specfuse.monitor.providers.azure_app_insights import HttpStatusRegressionAdapter"`.

**Escalation triggers.** If `cli._find_adapter_class` or `_find_transport_factory`
cannot resolve the new type without changing how the six existing types resolve,
stop and escalate rather than special-casing. If threading the new fields through
`_build_adapter` appears to require passing the watermark `since` or any returned
value into the query, stop: that is PLAN.md decision 5.
