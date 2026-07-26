### tests: FAIL
```
$ python3 -m unittest discover -s tests -v
   [13:05:56] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed f53103bd6eff14d9b6e1bd2eeed63a019780b31b

[13:05:57] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [13:05:57] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 3f61ae9c2635c56e32de457e0f1b7113242414fc

[13:05:57] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [13:05:57] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 02b5e17ca1d9fc5c4b27d408736af5b86e1b6d83

Gate 1 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet `done`.
Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / events.jsonl. Likely fix: manually flip PLAN.md `status: active -> done`, then `/wrap-feature`.
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
```

### security: PASS
```
$ bandit -r specfuse .specfuse/scripts -ll
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 6

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 75
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 75
Files skipped (0):
```

### coverage: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
   [13:06:51] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed a65e90cb20e7d80098fa331eaee84152d4f197c9

[13:06:51] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [13:06:51] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 5aca6df56572f60c70d796748ad396edeb6f8708

[13:06:51] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [13:06:51] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed c9b4238feb19c00f1e68509df77924f57d30262e

Gate 1 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet `done`.
Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / events.jsonl. Likely fix: manually flip PLAN.md `status: active -> done`, then `/wrap-feature`.
```

### leak-scan: PASS
```
$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: clean
```

### monitoring-example-lint: FAIL
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
FAIL — 1 finding(s):
  - component 'order-worker': checks[0]: 'dlq' check requires 'targets' — a DLQ always belongs to a specific subscription; add a 'targets' list with each entry carrying 'subscription' and 'function'
```

### leak-scan-hook: PASS
```
$ bats tests/leak_scan_hook.bats
1..3
ok 1 hook exits 0 when the scanner is clean
ok 2 hook exits 1 when the scanner reports a leak
ok 3 hook exits 1 when the scanner is missing
```

### sync-scaffold-bats: PASS
```
$ bats tests/sync_scaffold.bats
1..5
ok 1 sync copies all canonical files to specfuse/loop/data/
ok 2 sync copies file contents correctly
ok 3 sync is idempotent (second run exits 0 and reports unchanged)
ok 4 sync updates a stale file and reports it
ok 5 sync exits non-zero if canonical source dir is missing
```

### init-sh-shim-bats: PASS
```
$ bats tests/init_sh_shim.bats
1..5
ok 1 init mode: delegates to 'specfuse init <target>'
ok 2 upgrade mode: delegates to 'specfuse upgrade <target>'
ok 3 upgrade --dry-run: forwards --dry-run flag to specfuse upgrade
ok 4 specfuse absent: exits non-zero with pip install hint
ok 5 no target: exits non-zero with usage
```

### init-skills-bats: PASS
```
$ bats tests/init_skills_idempotent.bats
1..1
ok 1 source repo holds skill content in .specfuse (real), not .claude
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0069-monitoring-check-targets/WU-03-dlq-targets-required.md b/.specfuse/features/FEAT-2026-0069-monitoring-check-targets/WU-03-dlq-targets-required.md
index d1a3c49..38cbb1e 100644
--- a/.specfuse/features/FEAT-2026-0069-monitoring-check-targets/WU-03-dlq-targets-required.md
+++ b/.specfuse/features/FEAT-2026-0069-monitoring-check-targets/WU-03-dlq-targets-required.md
@@ -1,14 +1,19 @@
 ---
 id: FEAT-2026-0069/T03
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 3.00
 produces:
   - specfuse/loop/lint_monitoring.py
   - tests/test_lint_monitoring.py
   - tests/test_derive_monitoring_discovery.py
 oracle_env: macos_local
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.4.0
+started_at: 2026-07-26T17:00:42.496087+00:00
 ---
 
 # Contract: make `targets` required on `dlq` checks
diff --git a/specfuse/loop/lint_monitoring.py b/specfuse/loop/lint_monitoring.py
index 37ce8cc..976a5dd 100644
--- a/specfuse/loop/lint_monitoring.py
+++ b/specfuse/loop/lint_monitoring.py
@@ -225,6 +225,13 @@ def _check_checks(checks: object, component_label: str) -> list[str]:
                     f"check has unknown 'harvest_mode' {harvest_mode!r} — "
                     f"must be one of {sorted(HARVEST_MODE_VALUES)}"
                 )
+            if check.get("targets") is None:
+                findings.append(
+                    f"component '{component_label}': checks[{index}]: 'dlq' "
+                    f"check requires 'targets' — a DLQ always belongs to a "
+                    f"specific subscription; add a 'targets' list with each "
+                    f"entry carrying 'subscription' and 'function'"
+                )
         elif check_type == "invariant":
             for field in ("query", "fingerprint_by"):
                 if not check.get(field):
@@ -260,7 +267,7 @@ def _check_targets(
     Structural only, per T01's scope: a target's required coordinates must
     be present, but coordinate *contents* (a cron expression, a timezone
     name) are opaque here, exactly as `invariant.query` is. Requiredness of
-    `targets` itself is not enforced yet — that is T03.
+    `targets` on `dlq` checks is enforced separately, in `_check_checks`.
     """
     if targets is None:
         return []
diff --git a/tests/test_derive_monitoring_discovery.py b/tests/test_derive_monitoring_discovery.py
index eb4937d..c03942a 100644
--- a/tests/test_derive_monitoring_discovery.py
+++ b/tests/test_derive_monitoring_discovery.py
@@ -91,16 +91,27 @@ def suggest_checks(component: dict) -> list[dict]:
     """Map one neutral component record to a conservative check list.
 
     Every component gets ``heartbeat`` and ``error-logs``. An HTTP-serving
-    component also gets ``http-5xx``; a message-consuming component also gets
-    ``dlq`` with ``harvest_mode: peek``. ``invariant`` is never suggested —
+    component also gets ``http-5xx``. A message-consuming component gets a
+    ``dlq`` check only if its record carries a neutral ``subscriptions`` list
+    (populated by discovery) — one ``targets`` entry per known subscription,
+    each carrying ``subscription`` and ``function``. A message-consuming
+    component with no known subscriptions gets no ``dlq`` check at all: a
+    target-less `dlq` is exactly what T03 made invalid, and fabricating a
+    subscription or function name would violate the `derive-monitoring`
+    skill's no-invented-evidence rule. ``invariant`` is never suggested —
     its ``query`` is operator-supplied by definition, so inventing one would
-    be fabricating evidence.
+    also be fabricating evidence.
     """
     checks = []
     if component.get("http_serving"):
         checks.append({"type": "http-5xx"})
-    if component.get("message_consuming"):
-        checks.append({"type": "dlq", "harvest_mode": "peek"})
+    subscriptions = component.get("subscriptions")
+    if component.get("message_consuming") and subscriptions:
+        targets = [
+            {"subscription": sub["subscription"], "function": sub["function"]}
+            for sub in subscriptions
+        ]
+        checks.append({"type": "dlq", "harvest_mode": "peek", "targets": targets})
     checks.append({"type": "heartbeat"})
     checks.append({"type": "error-logs"})
     return checks
@@ -200,6 +211,14 @@ def render_monitoring_yml(components_with_checks: list[dict]) -> str:
             for key, value in check.items():
                 if key == "type":
                     continue
+                if key == "targets" and isinstance(value, list):
+                    lines.append("        targets:")
+                    for target in value:
+                        prefix = "          - "
+                        for t_key, t_value in target.items():
+                            lines.append(f"{prefix}{t_key}: {t_value}")
+                            prefix = "            "
+                    continue
                 lines.append(f"        {key}: {value}")
     return "\n".join(lines) + "\n"
 
@@ -330,10 +349,21 @@ _STACK_B_TREE = {
 
 
 class TestDiscoveredConfigPassesLint(unittest.TestCase):
-    """AC1: discovery + suggestion output satisfies gate 1's validator."""
+    """AC1/AC9: discovery + suggestion output satisfies gate 1's validator,
+    now that a target-less `dlq` is a finding. The message-consuming
+    component's discovered record is augmented in-test with the minimum
+    `subscriptions` data it needs to render a valid `dlq` check — this is
+    fixture data on an already-discovered record, not a change to
+    `discover_components()` or `_STACK_A_PATTERNS`; gate 2 is what teaches
+    discovery itself to populate `subscriptions`."""
 
     def test_discovered_config_passes_lint_monitoring(self):
         components = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
+        for component in components:
+            if component["name"] == "acme-order-worker":
+                component["subscriptions"] = [
+                    {"subscription": "orders.queue", "function": "ProcessOrder"}
+                ]
         rendered = [
             {"name": c["name"], "type": c["type"], "checks": suggest_checks(c)}
             for c in components
@@ -411,6 +441,23 @@ class TestNeutralRecordsSurviveASecondStack(unittest.TestCase):
         evidence_b = {ev for r in stack_b for ev in r["evidence"]}
         self.assertEqual(evidence_a.isdisjoint(evidence_b), True)
 
+    def test_second_stack_render_passes_lint_monitoring(self):
+        """AC10: T03's flip must not have broken the second stack's render.
+        Its message-consuming component has no `subscriptions` fixture data,
+        so honestly it gets no `dlq` check at all — and the render must
+        still validate clean."""
+        stack_b = discover_components(_STACK_B_TREE, _STACK_B_PATTERNS)
+        rendered = [
+            {"name": c["name"], "type": c["type"], "checks": suggest_checks(c)}
+            for c in stack_b
+        ]
+        text = render_monitoring_yml(rendered)
+        with tempfile.TemporaryDirectory() as tmp:
+            path = Path(tmp) / "monitoring.yml"
+            path.write_text(text)
+            findings = validate_monitoring(path)
+        self.assertEqual(findings, [], f"unexpected findings: {findings}")
+
 
 class TestCoreNamesNoStackTokens(unittest.TestCase):
     """AC5 boundary test: the core functions' own source contains no
@@ -458,6 +505,64 @@ class TestSuggestChecksNeverInvariant(unittest.TestCase):
         self.assertNotIn("invariant", types)
 
 
+class TestSuggestChecksDlqTargets(unittest.TestCase):
+    """AC6/AC7: suggest_checks reads a neutral `subscriptions` list off the
+    component record and emits one `dlq` target per entry; a
+    message-consuming component with no known subscriptions gets no `dlq`
+    check at all — never a fabricated placeholder target."""
+
+    def test_one_dlq_target_per_known_subscription(self):
+        component = {
+            "name": "acme-order-worker",
+            "type": "queue-consumer",
+            "http_serving": False,
+            "message_consuming": True,
+            "subscriptions": [
+                {"subscription": "orders.queue", "function": "ProcessOrder"},
+                {"subscription": "refunds.queue", "function": "ProcessRefund"},
+            ],
+        }
+        checks = suggest_checks(component)
+        dlq_checks = [c for c in checks if c["type"] == "dlq"]
+        self.assertEqual(len(dlq_checks), 1)
+        self.assertEqual(dlq_checks[0]["targets"], component["subscriptions"])
+
+    def test_no_dlq_check_for_message_consumer_without_subscriptions(self):
+        component = {
+            "name": "acme-order-worker",
+            "type": "queue-consumer",
+            "http_serving": False,
+            "message_consuming": True,
+        }
+        types = {c["type"] for c in suggest_checks(component)}
+        self.assertNotIn("dlq", types)
+
+
+class TestRenderRoundTripsTargets(unittest.TestCase):
+    """AC8: render_monitoring_yml renders a nested targets list-of-mappings
+    at correct indentation; asserted via a render -> parse round-trip, not
+    string shape."""
+
+    def test_targets_round_trip_through_parse(self):
+        targets = [
+            {"subscription": "orders.queue", "function": "ProcessOrder"},
+            {"subscription": "refunds.queue", "function": "ProcessRefund"},
+        ]
+        rendered = [{
+            "name": "acme-order-worker",
+            "type": "queue-consumer",
+            "checks": [
+                {"type": "dlq", "harvest_mode": "peek", "targets": targets},
+                {"type": "heartbeat"},
+                {"type": "error-logs"},
+            ],
+        }]
+        text = render_monitoring_yml(rendered)
+        parsed = _miniyaml.parse(text)
+        dlq_check = parsed["components"][0]["checks"][0]
+        self.assertEqual(dlq_check["targets"], targets)
+
+
 class TestAuditFindingsAreAllWarn(unittest.TestCase):
     """AC6: every finding audit_diagnosability can emit is WARN; the
     function exposes no ERROR severity at all."""
diff --git a/tests/test_lint_monitoring.py b/tests/test_lint_monitoring.py
index aff35bc..e0dfc4e 100644
--- a/tests/test_lint_monitoring.py
+++ b/tests/test_lint_monitoring.py
@@ -37,11 +37,22 @@ components:
       - type: heartbeat
       - type: dlq
         harvest_mode: peek
+        targets:
+          - subscription: orders-sub
+            function: ProcessOrder
       - type: invariant
         query: "select count(*) from orders"
         fingerprint_by: order_id
 """
 
+DLQ_CHECK_BLOCK = (
+    "      - type: dlq\n"
+    "        harvest_mode: peek\n"
+    "        targets:\n"
+    "          - subscription: orders-sub\n"
+    "            function: ProcessOrder\n"
+)
+
 
 def _config_with_components(defect_index: int, defect_field: str) -> str:
     lines = ["environments:", "  staging:", "    telemetry:",
@@ -311,8 +322,7 @@ class LintMonitoringTests(unittest.TestCase):
         text = VALID_CONFIG.replace(
             "    checks:\n"
             "      - type: heartbeat\n"
-            "      - type: dlq\n"
-            "        harvest_mode: peek\n"
+            + DLQ_CHECK_BLOCK +
             "      - type: invariant\n"
             "        query: \"select count(*) from orders\"\n"
             "        fingerprint_by: order_id\n",
@@ -326,8 +336,7 @@ class LintMonitoringTests(unittest.TestCase):
         text = VALID_CONFIG.replace(
             "    checks:\n"
             "      - type: heartbeat\n"
-            "      - type: dlq\n"
-            "        harvest_mode: peek\n"
+            + DLQ_CHECK_BLOCK +
             "      - type: invariant\n"
             "        query: \"select count(*) from orders\"\n"
             "        fingerprint_by: order_id\n",
@@ -401,7 +410,7 @@ class TestCheckTargets(unittest.TestCase):
 
     def test_dlq_target_missing_function_is_rejected(self):
         text = VALID_CONFIG.replace(
-            "      - type: dlq\n        harvest_mode: peek\n",
+            DLQ_CHECK_BLOCK,
             "      - type: dlq\n"
             "        harvest_mode: peek\n"
             "        targets:\n"
@@ -414,7 +423,7 @@ class TestCheckTargets(unittest.TestCase):
 
     def test_dlq_target_missing_subscription_is_rejected(self):
         text = VALID_CONFIG.replace(
-            "      - type: dlq\n        harvest_mode: peek\n",
+            DLQ_CHECK_BLOCK,
             "      - type: dlq\n"
             "        harvest_mode: peek\n"
             "        targets:\n"
@@ -426,15 +435,7 @@ class TestCheckTargets(unittest.TestCase):
         self.assertIn("subscription", findings[0])
 
     def test_dlq_target_with_both_coordinates_validates_clean(self):
-        text = VALID_CONFIG.replace(
-            "      - type: dlq\n        harvest_mode: peek\n",
-            "      - type: dlq\n"
-            "        harvest_mode: peek\n"
-            "        targets:\n"
-            "          - subscription: orders-sub\n"
-            "            function: ProcessOrder\n",
-        )
-        p = self._write(text)
+        p = self._write(VALID_CONFIG)
         self.assertEqual(validate_monitoring(p), [])
 
     def test_heartbeat_target_missing_name_is_rejected(self):
@@ -489,11 +490,6 @@ class TestCheckTargets(unittest.TestCase):
         self.assertEqual(len(findings), 1)
         self.assertIn("http-5xx", findings[0])
 
-    def test_targetless_dlq_check_still_validates_clean(self):
-        """T03 flips this; T01 must not — see PLAN.md escalation-predicate section."""
-        p = self._write(VALID_CONFIG)
-        self.assertEqual(validate_monitoring(p), [])
-
     def test_targets_not_a_list_is_rejected(self):
         text = VALID_CONFIG.replace(
             "      - type: heartbeat\n",
@@ -527,7 +523,7 @@ class TestCheckTargets(unittest.TestCase):
 
     def test_findings_are_deterministically_ordered(self):
         text = VALID_CONFIG.replace(
-            "      - type: dlq\n        harvest_mode: peek\n",
+            DLQ_CHECK_BLOCK,
             "      - type: dlq\n"
             "        harvest_mode: peek\n"
             "        targets:\n"
@@ -539,5 +535,46 @@ class TestCheckTargets(unittest.TestCase):
         self.assertEqual(first, second)
 
 
+class TestTargetsRequired(unittest.TestCase):
+    def setUp(self):
+        self._tmpdir = tempfile.TemporaryDirectory()
+        self.addCleanup(self._tmpdir.cleanup)
+        self.tmp_path = Path(self._tmpdir.name)
+
+    def _write(self, text: str) -> Path:
+        p = self.tmp_path / "monitoring.yml"
+        p.write_text(text)
+        return p
+
+    def test_dlq_without_targets_is_rejected(self):
+        text = VALID_CONFIG.replace(
+            DLQ_CHECK_BLOCK,
+            "      - type: dlq\n        harvest_mode: peek\n",
+        )
+        p = self._write(text)
+        findings = validate_monitoring(p)
+        self.assertEqual(len(findings), 1)
+        self.assertIn("targets", findings[0])
+
+    def test_dlq_without_targets_finding_names_the_fix(self):
+        text = VALID_CONFIG.replace(
+            DLQ_CHECK_BLOCK,
+            "      - type: dlq\n        harvest_mode: peek\n",
+        )
+        p = self._write(text)
+        findings = validate_monitoring(p)
+        self.assertEqual(len(findings), 1)
+        self.assertIn("subscription", findings[0])
+        self.assertIn("function", findings[0])
+
+    def test_heartbeat_remains_valid_with_no_targets(self):
+        p = self._write(VALID_CONFIG)
+        self.assertEqual(validate_monitoring(p), [])
+
+    def test_dlq_with_targets_still_validates_clean(self):
+        p = self._write(VALID_CONFIG)
+        self.assertEqual(validate_monitoring(p), [])
+
+
 if __name__ == "__main__":
     unittest.main()

```
