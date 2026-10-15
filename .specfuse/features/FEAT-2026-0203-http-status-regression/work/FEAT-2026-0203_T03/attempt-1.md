### tests: PASS
```
$ python3 -m unittest tests.test_lint_monitoring -v -b
test_queue_stalled_target_missing_function_is_rejected (tests.test_lint_monitoring.TestQueueStalled.test_queue_stalled_target_missing_function_is_rejected) ... ok
test_queue_stalled_target_missing_subscription_is_rejected (tests.test_lint_monitoring.TestQueueStalled.test_queue_stalled_target_missing_subscription_is_rejected) ... ok
test_queue_stalled_without_targets_is_rejected (tests.test_lint_monitoring.TestQueueStalled.test_queue_stalled_without_targets_is_rejected) ... ok
test_wellformed_stall_after_is_clean (tests.test_lint_monitoring.TestQueueStalled.test_wellformed_stall_after_is_clean) ... ok
test_dlq_with_targets_still_validates_clean (tests.test_lint_monitoring.TestTargetsRequired.test_dlq_with_targets_still_validates_clean) ... ok
test_dlq_without_targets_finding_names_the_fix (tests.test_lint_monitoring.TestTargetsRequired.test_dlq_without_targets_finding_names_the_fix) ... ok
test_dlq_without_targets_is_rejected (tests.test_lint_monitoring.TestTargetsRequired.test_dlq_without_targets_is_rejected) ... ok
test_error_logs_still_rejects_targets (tests.test_lint_monitoring.TestTargetsRequired.test_error_logs_still_rejects_targets) ... ok
test_heartbeat_without_targets_still_validates_clean (tests.test_lint_monitoring.TestTargetsRequired.test_heartbeat_without_targets_still_validates_clean) ... ok
test_http_5xx_still_rejects_targets (tests.test_lint_monitoring.TestTargetsRequired.test_http_5xx_still_rejects_targets) ... ok

----------------------------------------------------------------------
Ran 59 tests in 0.143s

OK
full output: .specfuse/features/FEAT-2026-0203-http-status-regression/work/gate-logs/tests-20261015T025910261486Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0203-http-status-regression/work/gate-logs/lint-20261015T025910301514Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0203-http-status-regression/work/gate-logs/agent-policy-example-lint-20261015T025910484183Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 82 events.jsonl file(s), 2483 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0203-http-status-regression/work/gate-logs/event-type-gate-20261015T025910783011Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0203-http-status-regression/work/gate-logs/roadmap-link-gate-20261015T025910855890Z.log
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
full output: .specfuse/features/FEAT-2026-0203-http-status-regression/work/gate-logs/arm-sweep-gate-20261015T025911578264Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0203-http-status-regression/work/gate-logs/monitoring-example-lint-20261015T025911660826Z.log
```

### feature_oracle: FAIL
```
$ python3 -m unittest tests.test_http_status_regression_end_to_end -v -b
FAIL: test_one_deployment_files_one_finding_per_code (tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_one_deployment_files_one_finding_per_code)
Traceback (most recent call last):
... (8 line(s) elided) ...
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ["component 'order-api': checks[0]: 'http-[97 chars]'])"] != []

First list contains 1 additional elements.
First extra element 0:
"component 'order-api': checks[0]: 'http-status-regression' check requires 'deploy_signal' — a mapping with a 'kind' (one of ['app-version'])"

+ []
- ["component 'order-api': checks[0]: 'http-status-regression' check requires "
-  "'deploy_signal' — a mapping with a 'kind' (one of ['app-version'])"]

----------------------------------------------------------------------
Ran 3 tests in 0.028s

FAILED (failures=1)
full output: .specfuse/features/FEAT-2026-0203-http-status-regression/work/gate-logs/feature_oracle-20261015T025911807859Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0203-http-status-regression/WU-03-schema-and-lint.md b/.specfuse/features/FEAT-2026-0203-http-status-regression/WU-03-schema-and-lint.md
index 667d115..055257e 100644
--- a/.specfuse/features/FEAT-2026-0203-http-status-regression/WU-03-schema-and-lint.md
+++ b/.specfuse/features/FEAT-2026-0203-http-status-regression/WU-03-schema-and-lint.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0203/T03
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 2.50
 produces:
   - specfuse/loop/lint_monitoring.py
@@ -12,6 +12,11 @@ produces:
   - specfuse/loop/data/monitoring.yml.example
   - .specfuse/rules/design-for-diagnosis.md
   - specfuse/loop/data/rules/design-for-diagnosis.md
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.27.1
+started_at: 2026-10-15T02:57:54.791353+00:00
 ---
 
 # T03 — the http-status-regression schema is validated and documented
diff --git a/.specfuse/features/FEAT-2026-0203-http-status-regression/events.jsonl b/.specfuse/features/FEAT-2026-0203-http-status-regression/events.jsonl
index 8266a2e..73d1acc 100644
--- a/.specfuse/features/FEAT-2026-0203-http-status-regression/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0203-http-status-regression/events.jsonl
@@ -9,3 +9,7 @@
 {"timestamp": "2026-10-15T02:55:47.693548+00:00", "correlation_id": "FEAT-2026-0203/T01", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.27.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 52.026, "cost_usd": 0.3354488, "input_tokens": 22, "output_tokens": 6872, "cache_read_input_tokens": 509804, "cache_creation_input_tokens": 41181, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0203-http-status-regression/WU-01-walking-skeleton.md", "specfuse/loop/lint_monitoring.py", "specfuse/monitor/artifact.py", "specfuse/monitor/cli.py", "specfuse/monitor/providers/azure_app_insights.py", "tests/test_http_status_regression_end_to_end.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
 {"timestamp": "2026-10-15T02:55:47.693825+00:00", "correlation_id": "FEAT-2026-0203/T01", "event_type": "task_completed", "source": "driver", "source_version": "0.27.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 52.026, "cost_usd": 0.3354488, "input_tokens": 22, "output_tokens": 6872, "cache_read_input_tokens": 509804, "cache_creation_input_tokens": 41181}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.335449, "cumulative_cost_usd": 0.335449, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
 {"timestamp": "2026-10-15T02:55:47.705300+00:00", "correlation_id": "FEAT-2026-0203", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.27.1", "payload": {"gate": 1, "wu_id": "FEAT-2026-0203/T01", "driver_paths": ["specfuse/loop/lint_monitoring.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "97ab0dc95ff035ab39198b8dafd9360fb7f65f4f", "next_pin_tree": "5998e41d6d9fbce040a94c5c0fe18b9e58573bb8"}}
+{"timestamp": "2026-10-15T02:55:47.842257+00:00", "correlation_id": "FEAT-2026-0203/T02", "event_type": "task_started", "source": "driver", "source_version": "0.27.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-10-15T02:57:54.632570+00:00", "correlation_id": "FEAT-2026-0203/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.27.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 126.578, "cost_usd": 0.25005360000000004, "input_tokens": 18, "output_tokens": 5869, "cache_read_input_tokens": 347778, "cache_creation_input_tokens": 30443, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0203-http-status-regression/WU-02-shared-duration-grammar.md", ".specfuse/features/FEAT-2026-0203-http-status-regression/events.jsonl", "docs/concepts/monitoring-schema.md", "specfuse/loop/lint_monitoring.py", "specfuse/monitor/durations.py", "specfuse/monitor/providers/azure_service_bus.py", "tests/test_lint_monitoring.py", "tests/test_monitor_durations.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
+{"timestamp": "2026-10-15T02:57:54.632894+00:00", "correlation_id": "FEAT-2026-0203/T02", "event_type": "task_completed", "source": "driver", "source_version": "0.27.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 126.578, "cost_usd": 0.25005360000000004, "input_tokens": 18, "output_tokens": 5869, "cache_read_input_tokens": 347778, "cache_creation_input_tokens": 30443}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.250054, "cumulative_cost_usd": 0.250054, "attempts_lifetime": 1, "planned_cost_usd": 2.5}}
+{"timestamp": "2026-10-15T02:57:54.645269+00:00", "correlation_id": "FEAT-2026-0203", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.27.1", "payload": {"gate": 1, "wu_id": "FEAT-2026-0203/T02", "driver_paths": ["specfuse/loop/lint_monitoring.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "97ab0dc95ff035ab39198b8dafd9360fb7f65f4f", "next_pin_tree": "5b4221937a29c79b1f86f81ac2559077e1d4efdf"}}
diff --git a/.specfuse/monitoring.yml.example b/.specfuse/monitoring.yml.example
index 9742398..4c37f84 100644
--- a/.specfuse/monitoring.yml.example
+++ b/.specfuse/monitoring.yml.example
@@ -81,6 +81,16 @@ components:
       # Use for any component that serves HTTP traffic directly.
       - type: http-5xx
 
+      # http-status-regression: alerts when a 4xx code that was rare before a
+      # deploy turns common after it (a contract break that raises no 5xx).
+      # `deploy_signal.kind` must be app-version; `window_after_deploy` is a
+      # duration. `codes` is optional (default 401, 403, 405, 410, 412, 415,
+      # 428). Fires at >= 3x the pre-deploy count and >= 10 occurrences.
+      - type: http-status-regression
+        deploy_signal:
+          kind: app-version
+        window_after_deploy: 30m
+
       # heartbeat: alerts when the component stops reporting in at all —
       # the check that catches "it didn't error, it just went silent."
       - type: heartbeat
diff --git a/.specfuse/rules/design-for-diagnosis.md b/.specfuse/rules/design-for-diagnosis.md
index 1911ad9..12c168b 100644
--- a/.specfuse/rules/design-for-diagnosis.md
+++ b/.specfuse/rules/design-for-diagnosis.md
@@ -7,8 +7,8 @@ Licensed under the Apache License, Version 2.0. See LICENSE.
 
 This rule governs the *target application's* code — not this loop's own
 execution. It states what a deployed component must do so the check types a
-`monitoring.yml` admits (`dlq`, `error-logs`, `http-5xx`, `heartbeat`,
-`invariant`) produce a diagnosable finding instead of a bare alert. A check that
+`monitoring.yml` admits (`dlq`, `error-logs`, `http-5xx`, `http-status-regression`,
+`heartbeat`, `invariant`, `queue-stalled`) produce a diagnosable finding instead of a bare alert. A check that
 fires without one of these properties tells an operator only that something is
 wrong, not what or where.
 
diff --git a/docs/concepts/monitoring-schema.md b/docs/concepts/monitoring-schema.md
index 9e23fcc..74ad9da 100644
--- a/docs/concepts/monitoring-schema.md
+++ b/docs/concepts/monitoring-schema.md
@@ -85,7 +85,7 @@ confidence in the checks grows.
 
 ## Check types
 
-Every check has a required `type`, one of six neutral values. This set is
+Every check has a required `type`, one of seven neutral values. This set is
 provider-agnostic by construction: a check type names a concept
 (a dead-letter queue, a heartbeat), never a vendor.
 
@@ -94,6 +94,7 @@ provider-agnostic by construction: a check type names a concept
 | `dlq` | `harvest_mode` (`peek` or `quarantine`), `targets` | Alerts on messages landing in this component's dead-letter queue. `peek` reads without removing; `quarantine` removes after reading. `targets` is **required**: a dead-lettered message is attributed to a subscription, and a target-less `dlq` check on a multi-subscription host cannot say which one. |
 | `error-logs` | none | Scans structured application logs for error-level entries. |
 | `http-5xx` | none | Alerts when the rolling 5xx rate crosses a threshold. For HTTP-serving components. |
+| `http-status-regression` | `deploy_signal`, `window_after_deploy` (optional: `codes`) | Alerts when a 4xx status code that was rare before a deploy turns common after it — the signature of a client/server contract break (a removed route, a tightened validator) that raises no 5xx, so `http-5xx` sees nothing. `deploy_signal` is a mapping with a required `kind`; the only accepted kind is `app-version` (the field exists for future kinds, and lint stays conservative until one ships). `window_after_deploy` is a duration (`<integer><unit>`, e.g. `30m`). `codes` is a non-empty list of unique integers in 400–499; absent means the default `[401, 403, 405, 410, 412, 415, 428]` (400, 404 and 409 are excluded — too noisy in normal traffic). A regression fires when a code's post-deploy count is at least 3× its pre-deploy count and at least 10; both thresholds are fixed constants, not fields. Per-component: `targets` is forbidden. |
 | `heartbeat` | none | Alerts when the component stops reporting in at all. |
 | `invariant` | `query`, `fingerprint_by` | Runs an operator-supplied query (opaque to this schema — not parsed or executed here) and alerts on unexpected rows. `fingerprint_by` names the field used to dedupe repeat findings into one issue. |
 | `queue-stalled` | `targets` | Alerts when a consumer stops consuming from a subscription — no message failed (so `dlq` sees nothing), the host is still alive (so `heartbeat` sees nothing), and the symptom is a broker coordinate (queue depth / age of oldest message), not a telemetry query, so `invariant` cannot express it either. `targets` is required from birth: a wedged consumer on a multi-subscription host raises the identical "which one" question `dlq`/`heartbeat` targets already answer. |
@@ -149,6 +150,7 @@ triggers as `targets[]` is what keeps that property satisfiable.
 | `invariant` | **forbidden** | — | `fingerprint_by` is already this check type's enumeration key; permitting `targets` too would give it two competing enumeration keys. |
 | `error-logs` | **forbidden** | — | Role-name keyed and genuinely component-scoped; the validator rejects `targets` here. |
 | `http-5xx` | **forbidden** | — | Same reason as `error-logs`. |
+| `http-status-regression` | **forbidden** | — | Per-component, like `http-5xx`: keyed by the component's role name and deploy signal, so the validator rejects `targets` here. |
 
 Where `targets` is present it must be a non-empty list of mappings, and every
 entry must carry that check type's required coordinates. An empty list is a
diff --git a/specfuse/loop/data/monitoring.yml.example b/specfuse/loop/data/monitoring.yml.example
index 9742398..4c37f84 100644
--- a/specfuse/loop/data/monitoring.yml.example
+++ b/specfuse/loop/data/monitoring.yml.example
@@ -81,6 +81,16 @@ components:
       # Use for any component that serves HTTP traffic directly.
       - type: http-5xx
 
+      # http-status-regression: alerts when a 4xx code that was rare before a
+      # deploy turns common after it (a contract break that raises no 5xx).
+      # `deploy_signal.kind` must be app-version; `window_after_deploy` is a
+      # duration. `codes` is optional (default 401, 403, 405, 410, 412, 415,
+      # 428). Fires at >= 3x the pre-deploy count and >= 10 occurrences.
+      - type: http-status-regression
+        deploy_signal:
+          kind: app-version
+        window_after_deploy: 30m
+
       # heartbeat: alerts when the component stops reporting in at all —
       # the check that catches "it didn't error, it just went silent."
       - type: heartbeat
diff --git a/specfuse/loop/data/rules/design-for-diagnosis.md b/specfuse/loop/data/rules/design-for-diagnosis.md
index 1911ad9..12c168b 100644
--- a/specfuse/loop/data/rules/design-for-diagnosis.md
+++ b/specfuse/loop/data/rules/design-for-diagnosis.md
@@ -7,8 +7,8 @@ Licensed under the Apache License, Version 2.0. See LICENSE.
 
 This rule governs the *target application's* code — not this loop's own
 execution. It states what a deployed component must do so the check types a
-`monitoring.yml` admits (`dlq`, `error-logs`, `http-5xx`, `heartbeat`,
-`invariant`) produce a diagnosable finding instead of a bare alert. A check that
+`monitoring.yml` admits (`dlq`, `error-logs`, `http-5xx`, `http-status-regression`,
+`heartbeat`, `invariant`, `queue-stalled`) produce a diagnosable finding instead of a bare alert. A check that
 fires without one of these properties tells an operator only that something is
 wrong, not what or where.
 
diff --git a/specfuse/loop/lint_monitoring.py b/specfuse/loop/lint_monitoring.py
index 1c3344d..ab5202a 100644
--- a/specfuse/loop/lint_monitoring.py
+++ b/specfuse/loop/lint_monitoring.py
@@ -260,6 +260,10 @@ def _check_checks(checks: object, component_label: str) -> list[str]:
                     f"'queue-stalled' check requires 'targets' — each target "
                     f"needs 'subscription' and 'function'"
                 )
+        elif check_type == "http-status-regression":
+            findings.extend(
+                _check_http_status_regression(check, component_label, index)
+            )
         elif check_type == "invariant":
             for field in ("query", "fingerprint_by"):
                 if not check.get(field):
@@ -275,6 +279,67 @@ def _check_checks(checks: object, component_label: str) -> list[str]:
     return findings
 
 
+# `deploy_signal.kind` values an `http-status-regression` check accepts. The
+# field exists for future kinds; lint stays conservative until one ships.
+DEPLOY_SIGNAL_KINDS = frozenset({"app-version"})
+
+
+def _check_http_status_regression(
+    check: dict, component_label: str, index: int
+) -> list[str]:
+    """Validate the per-check fields of an `http-status-regression` check.
+
+    `targets` is rejected by `_check_targets` (the type is per-component).
+    """
+    where = f"component '{component_label}': checks[{index}]: 'http-status-regression' check"
+    findings: list[str] = []
+
+    deploy_signal = check.get("deploy_signal")
+    if not isinstance(deploy_signal, dict):
+        findings.append(
+            f"{where} requires 'deploy_signal' — a mapping with a 'kind' "
+            f"(one of {sorted(DEPLOY_SIGNAL_KINDS)})"
+        )
+    else:
+        kind = deploy_signal.get("kind")
+        if kind not in DEPLOY_SIGNAL_KINDS:
+            findings.append(
+                f"{where} has unknown 'deploy_signal.kind' {kind!r} — "
+                f"must be one of {sorted(DEPLOY_SIGNAL_KINDS)}"
+            )
+
+    window = check.get("window_after_deploy")
+    if window is None:
+        findings.append(f"{where} requires 'window_after_deploy'")
+    else:
+        try:
+            parse_duration_seconds(str(window))
+        except ValueError:
+            findings.append(
+                f"{where} 'window_after_deploy' value {window!r} is not a "
+                f"valid duration — expected {DURATION_GRAMMAR}"
+            )
+
+    if "codes" in check:
+        codes = check["codes"]
+        if (
+            not isinstance(codes, list)
+            or not codes
+            or not all(
+                isinstance(c, int) and not isinstance(c, bool) and 400 <= c <= 499
+                for c in codes
+            )
+        ):
+            findings.append(
+                f"{where} 'codes' must be a non-empty list of integers in "
+                f"400-499 — omit the key for the default set"
+            )
+        elif len(set(codes)) != len(codes):
+            findings.append(f"{where} 'codes' must not contain duplicates")
+
+    return findings
+
+
 # Per check-type target coordinates: the fields a `targets[]` entry must
 # carry. `error-logs` and `http-5xx` are absent from this map on purpose —
 # they are role-name keyed and therefore genuinely component-scoped; see
diff --git a/tests/test_lint_monitoring.py b/tests/test_lint_monitoring.py
index 3f888a5..e8856fa 100644
--- a/tests/test_lint_monitoring.py
+++ b/tests/test_lint_monitoring.py
@@ -771,6 +771,51 @@ class TestQueueStalled(unittest.TestCase):
                 self.assertEqual(validate_monitoring(self._write(text)), [])
 
 
+class TestHttpStatusRegression(unittest.TestCase):
+    def setUp(self):
+        self._tmpdir = tempfile.TemporaryDirectory()
+        self.addCleanup(self._tmpdir.cleanup)
+        self.tmp_path = Path(self._tmpdir.name)
+
+    def _findings(self, check_body: str) -> list[str]:
+        text = VALID_CONFIG.replace(
+            "      - type: heartbeat\n",
+            "      - type: heartbeat\n"
+            "      - type: http-status-regression\n" + check_body,
+        )
+        p = self.tmp_path / "monitoring.yml"
+        p.write_text(text)
+        return validate_monitoring(p)
+
+    def test_field_rules(self):
+        ok_signal = "        deploy_signal:\n          kind: app-version\n"
+        ok_window = "        window_after_deploy: 30m\n"
+        self.assertEqual(self._findings(ok_signal + ok_window), [])
+        bad = {
+            "missing deploy_signal": ok_window,
+            "unknown kind": (
+                "        deploy_signal:\n          kind: ci-annotation\n" + ok_window
+            ),
+            "missing window": ok_signal,
+            "malformed window": (
+                ok_signal + "        window_after_deploy: 30 minutes\n"
+            ),
+            "codes out of range": ok_signal + ok_window + "        codes: [500]\n",
+            "codes empty": ok_signal + ok_window + "        codes: []\n",
+            "codes duplicate": (
+                ok_signal + ok_window + "        codes: [401, 401]\n"
+            ),
+            "targets": (
+                ok_signal + ok_window + "        targets:\n          - name: x\n"
+            ),
+        }
+        for label, body in bad.items():
+            with self.subTest(case=label):
+                findings = self._findings(body)
+                self.assertEqual(len(findings), 1, findings)
+                self.assertIn("http-status-regression", findings[0])
+
+
 class TestInvariantTargetsRejected(unittest.TestCase):
     def setUp(self):
         self._tmpdir = tempfile.TemporaryDirectory()

```
