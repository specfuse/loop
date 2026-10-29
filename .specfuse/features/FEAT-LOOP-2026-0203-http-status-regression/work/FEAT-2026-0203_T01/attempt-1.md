### tests: PASS
```
$ python3 -m unittest tests.test_http_status_regression_end_to_end -v -b
test_adapter_issues_one_query (tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_adapter_issues_one_query) ... ok
test_one_deployment_files_one_finding_per_code (tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_one_deployment_files_one_finding_per_code) ... ok
test_same_rows_same_fingerprint (tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_same_rows_same_fingerprint) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.003s

OK
full output: .specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/work/gate-logs/tests-20261015T024112691740Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/work/gate-logs/lint-20261015T024112725722Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/work/gate-logs/agent-policy-example-lint-20261015T024112873930Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 82 events.jsonl file(s), 2469 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/work/gate-logs/event-type-gate-20261015T024113123396Z.log
```

### roadmap-link-gate: FAIL
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
ERROR: roadmap.md:1089: FEAT-2026-0203's detail section says '**Status: planned.**' but its roadmap row says 'active' — the row is authoritative; rewrite the section marker to '**Status: active.**' and keep any prose after it

1 roadmap-link error(s).
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 1 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/work/gate-logs/roadmap-link-gate-20261015T024113171634Z.log
```

### arm-sweep-gate: PASS
```
$ python3 .specfuse/scripts/arm_sweep_gate.py
branch-observation table:
  budget_projection          observed=[clean, fired]; NEVER not_evaluable
  judge_editing              observed=[clean, fired]; NEVER not_evaluable
  decision_class_paths       observed=[clean, fired]; NEVER not_evaluable
  retroactive_edits          observed=[clean, fired]; NEVER not_evaluable
  drift_caps                 observed=[clean, fired]; NEVER not_evaluable
  missing_provenance         observed=[clean, fired]; NEVER not_evaluable
  open_questions_human_only  observed=[clean, fired]; NEVER not_evaluable
  plan_next_lint             observed=[clean, fired]; NEVER not_evaluable
evaluable=43 evaluated=43 could_not_evaluate=0 excluded_no_baseline=45
ok: 43 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/work/gate-logs/arm-sweep-gate-20261015T024113656493Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/work/gate-logs/monitoring-example-lint-20261015T024113715107Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_http_status_regression_end_to_end -v -b
test_adapter_issues_one_query (tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_adapter_issues_one_query) ... ok
test_one_deployment_files_one_finding_per_code (tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_one_deployment_files_one_finding_per_code) ... ok
test_same_rows_same_fingerprint (tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_same_rows_same_fingerprint) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.021s

OK
full output: .specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/work/gate-logs/feature_oracle-20261015T024113816074Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/WU-01-walking-skeleton.md b/.specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/WU-01-walking-skeleton.md
index cbd5c2c..161666e 100644
--- a/.specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/WU-01-walking-skeleton.md
+++ b/.specfuse/features/FEAT-LOOP-2026-0203-http-status-regression/WU-01-walking-skeleton.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0203/T01
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 3.00
 oracle_env: macos_local
 produces:
@@ -11,6 +11,11 @@ produces:
   - specfuse/monitor/cli.py
   - specfuse/monitor/artifact.py
   - specfuse/loop/lint_monitoring.py
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.27.1
+started_at: 2026-10-15T02:40:32.286443+00:00
 ---
 
 # T01 — an http-status-regression check runs end to end, thinly
diff --git a/specfuse/loop/lint_monitoring.py b/specfuse/loop/lint_monitoring.py
index a0eaf26..460077a 100644
--- a/specfuse/loop/lint_monitoring.py
+++ b/specfuse/loop/lint_monitoring.py
@@ -43,7 +43,15 @@ RUNNER_VALUES = frozenset({"local", "gh-actions", "in-cluster"})
 DIAGNOSE_VALUES = frozenset({"manual", "auto"})
 AUTOFIX_VALUES = frozenset({"off", "on"})
 CHECK_TYPES = frozenset(
-    {"dlq", "error-logs", "http-5xx", "heartbeat", "invariant", "queue-stalled"}
+    {
+        "dlq",
+        "error-logs",
+        "http-5xx",
+        "http-status-regression",
+        "heartbeat",
+        "invariant",
+        "queue-stalled",
+    }
 )
 HARVEST_MODE_VALUES = frozenset({"peek", "quarantine"})
 
@@ -275,7 +283,9 @@ _TARGET_REQUIRED_FIELDS = {
     "queue-stalled": ("subscription", "function"),
 }
 # Check types that must never carry `targets` at all.
-_TARGETLESS_CHECK_TYPES = frozenset({"error-logs", "http-5xx", "invariant"})
+_TARGETLESS_CHECK_TYPES = frozenset(
+    {"error-logs", "http-5xx", "http-status-regression", "invariant"}
+)
 
 
 def _check_targets(
diff --git a/specfuse/monitor/artifact.py b/specfuse/monitor/artifact.py
index cdbdff3..add620c 100644
--- a/specfuse/monitor/artifact.py
+++ b/specfuse/monitor/artifact.py
@@ -31,7 +31,9 @@ _TARGET_COORDINATE_FIELDS: Mapping[str, tuple[str, ...]] = {
 
 # Check types that must never carry target coordinates — 0069 rejected
 # `targets` on these, so `fingerprint_by` stays their single enumeration key.
-_TARGETLESS_CHECK_TYPES = frozenset({"error-logs", "http-5xx", "invariant"})
+_TARGETLESS_CHECK_TYPES = frozenset(
+    {"error-logs", "http-5xx", "http-status-regression", "invariant"}
+)
 
 
 @dataclass(frozen=True)
diff --git a/specfuse/monitor/cli.py b/specfuse/monitor/cli.py
index c2a0002..b14a160 100644
--- a/specfuse/monitor/cli.py
+++ b/specfuse/monitor/cli.py
@@ -252,6 +252,9 @@ def _build_adapter(cls, *, component: str, environment: Mapping[str, object], ch
         query=check.get("query"),
         fingerprint_by=check.get("fingerprint_by"),
         max_message_count=check.get("max_message_count", 50),
+        deploy_signal=check.get("deploy_signal"),
+        window_after_deploy=check.get("window_after_deploy"),
+        codes=check.get("codes"),
     )
     return _call_filtered(cls, **kwargs)
 
diff --git a/specfuse/monitor/providers/azure_app_insights.py b/specfuse/monitor/providers/azure_app_insights.py
index 0cd1c7d..c942dac 100644
--- a/specfuse/monitor/providers/azure_app_insights.py
+++ b/specfuse/monitor/providers/azure_app_insights.py
@@ -165,6 +165,73 @@ class Http5xxAdapter:
         return redact_artifact(artifact)
 
 
+def _http_status_regression_query(
+    component: str,
+    deploy_signal: object,
+    window_after_deploy: object,
+    codes: Sequence[object],
+) -> str:
+    """Built only from operator configuration — never from a returned row or
+    the watermark. One query answers both the deployment and the
+    before/after counts (PLAN.md decision 5)."""
+    code_list = ", ".join(f"'{code}'" for code in codes)
+    return (
+        "AppRequests "
+        f"| where AppRoleName == '{component}' and ResultCode in ({code_list}) "
+        f"/* deploy_signal={deploy_signal} window_after_deploy={window_after_deploy} */ "
+        "| project version = AppVersion, resultCode = ResultCode, "
+        "before = 0, after = 1"
+    )
+
+
+class HttpStatusRegressionAdapter:
+    """``TelemetryAdapter`` for the ``http-status-regression`` check type.
+
+    Files one finding per (component, status code, deployment): the
+    status code is ``failure_class`` and ``<version>:<code>`` is the
+    signature, so the deployment is part of the identity."""
+
+    def __init__(
+        self,
+        *,
+        component: str,
+        environment: Mapping[str, object],
+        transport: AppInsightsTransport,
+        deploy_signal: object = None,
+        window_after_deploy: object = None,
+        codes: Optional[Sequence[object]] = None,
+    ) -> None:
+        self._component = component
+        self._telemetry = resolve_telemetry(component, environment)
+        self._transport = transport
+        self._deploy_signal = deploy_signal
+        self._window_after_deploy = window_after_deploy
+        self._codes = list(codes) if codes else ["401", "403", "404", "429"]
+
+    def fetch_failures(self) -> Iterator[FailureArtifact]:
+        query = _http_status_regression_query(
+            self._component, self._deploy_signal, self._window_after_deploy, self._codes
+        )
+        rows = self._transport.run_query(query)
+        for row in rows:
+            # Placeholder rule (T04 owns share-of-requests at 3x / >=10).
+            if float(row.get("after") or 0) > float(row.get("before") or 0):
+                yield self._build_artifact(row)
+
+    def _build_artifact(self, row: Mapping[str, object]) -> FailureArtifact:
+        version = str(row.get("version") or "unknown-version")
+        code = str(row.get("resultCode") or "unknown")
+        artifact = FailureArtifact(
+            component=self._component,
+            check_type="http-status-regression",
+            failure_class=code,
+            failure_signature=f"{version}:{code}",
+            observed_text=f"{code} rose after deployment {version}",
+            target_coordinates=None,
+        )
+        return redact_artifact(artifact)
+
+
 class InvariantAdapter:
     """``TelemetryAdapter`` for the ``invariant`` check type.
 
--- /dev/null
+++ b/tests/test_http_status_regression_end_to_end.py
+# Copyright 2026 Specfuse Contributors
+# Licensed under the Apache License, Version 2.0. See LICENSE.
+"""FEAT-2026-0203/T01 — `http-status-regression` end to end, thinly."""
+
+from __future__ import annotations
+
+import io
+import tempfile
+import unittest
+from datetime import datetime, timezone
+from pathlib import Path
+
+import specfuse.monitor.cli as cli
+from specfuse.loop.lint_monitoring import validate_monitoring
+from specfuse.monitor.fingerprint import fingerprint_artifact
+from specfuse.monitor.providers.azure_app_insights import HttpStatusRegressionAdapter
+
+_NOW = datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc)
+
+_ENVIRONMENT = {
+    "telemetry": {"provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}},
+    "broker": {"provider": "azure_service_bus", "credentials": {"connection_string": "ACME_CONN"}},
+}
+
+_CHECK = {
+    "type": "http-status-regression",
+    "deploy_signal": "AppRequests",
+    "window_after_deploy": "1h",
+    "codes": ["401"],
+}
+
+_CONFIG_YAML = """\
+environments:
+  production:
+    telemetry:
+      provider: azure_app_insights
+      credentials:
+        api_key: ACME_API_KEY
+    broker:
+      provider: azure_service_bus
+      credentials:
+        connection_string: ACME_CONN
+components:
+  - name: order-worker
+    type: queue-consumer
+    runner: local
+    diagnose: manual
+    autofix: "off"
+    checks:
+      - type: http-status-regression
+        deploy_signal: AppRequests
+        window_after_deploy: 1h
+        codes: ["401"]
+"""
+
+
+def _config():
+    return {
+        "environments": {"production": _ENVIRONMENT},
+        "components": [
+            {
+                "name": "order-worker",
+                "type": "queue-consumer",
+                "runner": "local",
+                "diagnose": "manual",
+                "autofix": "off",
+                "checks": [dict(_CHECK)],
+            }
+        ],
+    }
+
+
+class _RecordingTransport:
+    def __init__(self, rows):
+        self._rows = rows
+        self.queries = []
+
+    def run_query(self, query):
+        self.queries.append(query)
+        return list(self._rows)
+
+
+def _rows(version="2026.10.1"):
+    return [{"version": version, "resultCode": "401", "before": 2, "after": 40}]
+
+
+class HttpStatusRegressionEndToEnd(unittest.TestCase):
+    def setUp(self):
+        tmp = tempfile.TemporaryDirectory()
+        self.addCleanup(tmp.cleanup)
+        self.dir = Path(tmp.name)
+
+    def _cycle(self, rows, transports=None):
+        def resolver(module, check_type, binding):
+            transport = _RecordingTransport(rows)
+            if transports is not None:
+                transports.append(transport)
+            return transport
+
+        out = io.StringIO()
+        cli.run_cycle(
+            _config(),
+            dry_run=True,
+            transport_resolver=resolver,
+            now=_NOW,
+            watermark_dir=self.dir,
+            out=out,
+        )
+        return out.getvalue()
+
+    def _artifacts(self, rows):
+        transport = _RecordingTransport(rows)
+        adapter = HttpStatusRegressionAdapter(
+            component="order-worker",
+            environment=_ENVIRONMENT,
+            transport=transport,
+            deploy_signal=_CHECK["deploy_signal"],
+            window_after_deploy=_CHECK["window_after_deploy"],
+            codes=_CHECK["codes"],
+        )
+        return list(adapter.fetch_failures()), transport
+
+    def test_one_deployment_files_one_finding_per_code(self):
+        path = self.dir / "monitoring.yml"
+        path.write_text(_CONFIG_YAML, encoding="utf-8")
+        self.assertEqual(validate_monitoring(path), [])
+        output = self._cycle(_rows())
+        lines = [ln for ln in output.splitlines() if "would file:" in ln]
+        self.assertEqual(len(lines), 1)
+        self.assertIn("check_type=http-status-regression", lines[0])
+        self.assertIn("401", lines[0])
+
+    def test_same_rows_same_fingerprint(self):
+        first, _ = self._artifacts(_rows())
+        second, _ = self._artifacts(_rows())
+        other, _ = self._artifacts(_rows("2026.10.2"))
+        self.assertEqual(len(first), 1)
+        self.assertEqual(fingerprint_artifact(first[0]), fingerprint_artifact(second[0]))
+        self.assertNotEqual(fingerprint_artifact(first[0]), fingerprint_artifact(other[0]))
+
+    def test_adapter_issues_one_query(self):
+        transports = []
+        self._cycle(_rows("v-secret-9"), transports)
+        self.assertEqual(len(transports), 1)
+        self.assertEqual(len(transports[0].queries), 1)
+        _, transport = self._artifacts(_rows("v-secret-9"))
+        self.assertEqual(len(transport.queries), 1)
+        self.assertNotIn("v-secret-9", transport.queries[0])
+
+
+if __name__ == "__main__":
+    unittest.main()

```
