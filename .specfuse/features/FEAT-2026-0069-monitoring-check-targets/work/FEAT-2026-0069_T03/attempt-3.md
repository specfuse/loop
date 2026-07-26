### tests: FAIL
```
$ python3 -m unittest discover -s tests -v
   [13:20:16] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 9c1f490d157a00539608e297461a7b8b44d4f506

[13:20:16] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [13:20:16] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 7a8b0099ddf78e75c9c57534542923091c8659c4

[13:20:16] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [13:20:16] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 95d798a90c456b39c1f5671167c0689717e382a3

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
   [13:21:11] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 3b09d0bcb8baa38e01e66d61bf94306d5e8fa6c7

[13:21:11] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [13:21:11] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 603e7e1dae8aae4ca6eff6e25573cfaf22324561

[13:21:11] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [13:21:11] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 49b4f6f3e7eae8b393e752e7fee06f57d82f2758

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
  - component 'order-worker': checks[0]: 'dlq' check requires 'targets' — each target needs 'subscription' and 'function'
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
index d1a3c49..1bf1c5b 100644
--- a/.specfuse/features/FEAT-2026-0069-monitoring-check-targets/WU-03-dlq-targets-required.md
+++ b/.specfuse/features/FEAT-2026-0069-monitoring-check-targets/WU-03-dlq-targets-required.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0069/T03
 type: implementation
 status: pending
-attempts: 0
+attempts: 3
 planned_cost_usd: 3.00
 produces:
   - specfuse/loop/lint_monitoring.py
diff --git a/.specfuse/skills/derive-monitoring/SKILL.md b/.specfuse/skills/derive-monitoring/SKILL.md
index 1a37380..1281b56 100644
--- a/.specfuse/skills/derive-monitoring/SKILL.md
+++ b/.specfuse/skills/derive-monitoring/SKILL.md
@@ -197,10 +197,13 @@ components:
       - type: error-logs
 ```
 
-`targets[]` appears only where discovery found more than one subscription or
-schedule feeding one deployable — the shape the schema doc's "Check targets"
-section documents. A single-subscription consumer stays target-less; adding
-`targets` there would just restate the component's own name.
+A `dlq` check always carries `targets` — even a single-subscription consumer
+gets a one-entry `targets[]`, since a DLQ always belongs to a specific
+subscription and omitting it would be underspecified. `heartbeat` is the
+opposite case: its `targets[]` appears only where discovery found more than
+one schedule feeding one deployable — the shape the schema doc's "Check
+targets" section documents — and a single-schedule component stays
+target-less, since the component *is* the thing that went silent.
 
 #### 4b. The proposed `.specfuse/monitoring.overrides.yml`
 
@@ -237,6 +240,11 @@ components:
     checks:
       - type: dlq
         harvest_mode: peek
+        targets:
+          - subscription: acme-orders-created-sub
+            function: ProcessOrderCreated
+          - subscription: acme-orders-cancelled-sub
+            function: ProcessOrderCancelled
 ```
 
 #### 4c. A filled-in reading of `monitoring-secrets-checklist.md`
diff --git a/plugins/specfuse/skills/derive-monitoring/SKILL.md b/plugins/specfuse/skills/derive-monitoring/SKILL.md
index 1a37380..1281b56 100644
--- a/plugins/specfuse/skills/derive-monitoring/SKILL.md
+++ b/plugins/specfuse/skills/derive-monitoring/SKILL.md
@@ -197,10 +197,13 @@ components:
       - type: error-logs
 ```
 
-`targets[]` appears only where discovery found more than one subscription or
-schedule feeding one deployable — the shape the schema doc's "Check targets"
-section documents. A single-subscription consumer stays target-less; adding
-`targets` there would just restate the component's own name.
+A `dlq` check always carries `targets` — even a single-subscription consumer
+gets a one-entry `targets[]`, since a DLQ always belongs to a specific
+subscription and omitting it would be underspecified. `heartbeat` is the
+opposite case: its `targets[]` appears only where discovery found more than
+one schedule feeding one deployable — the shape the schema doc's "Check
+targets" section documents — and a single-schedule component stays
+target-less, since the component *is* the thing that went silent.
 
 #### 4b. The proposed `.specfuse/monitoring.overrides.yml`
 
@@ -237,6 +240,11 @@ components:
     checks:
       - type: dlq
         harvest_mode: peek
+        targets:
+          - subscription: acme-orders-created-sub
+            function: ProcessOrderCreated
+          - subscription: acme-orders-cancelled-sub
+            function: ProcessOrderCancelled
 ```
 
 #### 4c. A filled-in reading of `monitoring-secrets-checklist.md`
diff --git a/specfuse/loop/lint_monitoring.py b/specfuse/loop/lint_monitoring.py
index 37ce8cc..18ff275 100644
--- a/specfuse/loop/lint_monitoring.py
+++ b/specfuse/loop/lint_monitoring.py
@@ -225,6 +225,12 @@ def _check_checks(checks: object, component_label: str) -> list[str]:
                     f"check has unknown 'harvest_mode' {harvest_mode!r} — "
                     f"must be one of {sorted(HARVEST_MODE_VALUES)}"
                 )
+            if check.get("targets") is None:
+                findings.append(
+                    f"component '{component_label}': checks[{index}]: 'dlq' "
+                    f"check requires 'targets' — each target needs "
+                    f"'subscription' and 'function'"
+                )
         elif check_type == "invariant":
             for field in ("query", "fingerprint_by"):
                 if not check.get(field):
@@ -257,10 +263,13 @@ def _check_targets(
 ) -> list[str]:
     """Validate an optional `checks[].targets` list.
 
-    Structural only, per T01's scope: a target's required coordinates must
-    be present, but coordinate *contents* (a cron expression, a timezone
-    name) are opaque here, exactly as `invariant.query` is. Requiredness of
-    `targets` itself is not enforced yet — that is T03.
+    Structural only: a target's required coordinates must be present, but
+    coordinate *contents* (a cron expression, a timezone name) are opaque
+    here, exactly as `invariant.query` is. `dlq`'s `targets` requiredness
+    itself is enforced in `_check_checks` (T03) — a DLQ always belongs to a
+    specific subscription, so a target-less `dlq` is underspecified.
+    `heartbeat` has no such requirement: a single-process HTTP service
+    genuinely has nothing to enumerate.
     """
     if targets is None:
         return []
diff --git a/tests/test_derive_monitoring_discovery.py b/tests/test_derive_monitoring_discovery.py
index eb4937d..9faa1be 100644
--- a/tests/test_derive_monitoring_discovery.py
+++ b/tests/test_derive_monitoring_discovery.py
@@ -82,6 +82,7 @@ def discover_components(tree: dict, patterns: dict) -> list[dict]:
             "http_serving": bool(candidate.get("http_serving")),
             "message_consuming": bool(candidate.get("message_consuming")),
             "evidence": evidence,
+            "subscriptions": list(candidate.get("subscriptions", [])),
         })
     records.sort(key=lambda r: r["name"])
     return records
@@ -91,16 +92,30 @@ def suggest_checks(component: dict) -> list[dict]:
     """Map one neutral component record to a conservative check list.
 
     Every component gets ``heartbeat`` and ``error-logs``. An HTTP-serving
-    component also gets ``http-5xx``; a message-consuming component also gets
-    ``dlq`` with ``harvest_mode: peek``. ``invariant`` is never suggested —
+    component also gets ``http-5xx``. A message-consuming component gets
+    ``dlq`` with ``harvest_mode: peek`` and one ``targets`` entry per known
+    ``subscriptions`` entry on the record — each carrying the ``subscription``
+    and ``function`` names discovery already knows. A message-consuming
+    component with no known ``subscriptions`` gets **no** ``dlq`` check at
+    all: a target-less ``dlq`` is required to carry a real subscription and
+    function, and inventing either would be fabricating evidence, which the
+    `derive-monitoring` skill never does. ``invariant`` is never suggested —
     its ``query`` is operator-supplied by definition, so inventing one would
-    be fabricating evidence.
+    likewise be fabricating evidence.
     """
     checks = []
     if component.get("http_serving"):
         checks.append({"type": "http-5xx"})
-    if component.get("message_consuming"):
-        checks.append({"type": "dlq", "harvest_mode": "peek"})
+    subscriptions = component.get("subscriptions") or []
+    if component.get("message_consuming") and subscriptions:
+        checks.append({
+            "type": "dlq",
+            "harvest_mode": "peek",
+            "targets": [
+                {"subscription": s["subscription"], "function": s["function"]}
+                for s in subscriptions
+            ],
+        })
     checks.append({"type": "heartbeat"})
     checks.append({"type": "error-logs"})
     return checks
@@ -172,7 +187,10 @@ def render_monitoring_yml(components_with_checks: list[dict]) -> str:
     ``suggest_checks``). One placeholder environment supplies the required
     ``telemetry``/``broker`` provider bindings. ``autofix`` is emitted quoted
     (``"off"``) — ``_miniyaml`` rejects the bare ``off``/`on` spellings as
-    forbidden boolean-like tokens.
+    forbidden boolean-like tokens. A check's ``targets`` (a list of mappings,
+    e.g. a ``dlq`` check's per-subscription targets) renders as a nested
+    block sequence at ``indent + 2`` from the ``targets:`` line, matching
+    ``_miniyaml``'s continuation-key rule.
     """
     lines = [
         "environments:",
@@ -200,6 +218,15 @@ def render_monitoring_yml(components_with_checks: list[dict]) -> str:
             for key, value in check.items():
                 if key == "type":
                     continue
+                if key == "targets":
+                    lines.append("        targets:")
+                    for target in value:
+                        items = list(target.items())
+                        first_key, first_value = items[0]
+                        lines.append(f"          - {first_key}: {first_value}")
+                        for k, v in items[1:]:
+                            lines.append(f"            {k}: {v}")
+                    continue
                 lines.append(f"        {key}: {value}")
     return "\n".join(lines) + "\n"
 
@@ -256,6 +283,9 @@ _STACK_A_PATTERNS = {
             "http_serving": False,
             "message_consuming": True,
             "evidence_markers": ["ACME_A_CONSUMER_MARKER"],
+            "subscriptions": [
+                {"subscription": "orders.queue", "function": "ProcessOrder"},
+            ],
         },
     ],
     "diagnosability": {
@@ -300,6 +330,9 @@ _STACK_B_PATTERNS = {
             "http_serving": False,
             "message_consuming": True,
             "evidence_markers": ["ACME_B_SUBSCRIBER_TAG"],
+            "subscriptions": [
+                {"subscription": "shipments.topic", "function": "ProcessShipment"},
+            ],
         },
     ],
     "diagnosability": {
@@ -458,6 +491,76 @@ class TestSuggestChecksNeverInvariant(unittest.TestCase):
         self.assertNotIn("invariant", types)
 
 
+class TestSuggestChecksDlqTargets(unittest.TestCase):
+    """FEAT-2026-0069/T03 AC6/AC7: `suggest_checks` reads `subscriptions`
+    off the component record and emits one `dlq` target per entry, honestly
+    emitting no `dlq` check at all when there are none to report."""
+
+    def test_dlq_target_per_known_subscription(self):
+        component = {
+            "name": "acme-order-worker",
+            "type": "queue-consumer",
+            "http_serving": False,
+            "message_consuming": True,
+            "subscriptions": [
+                {"subscription": "orders.queue", "function": "ProcessOrder"},
+                {"subscription": "orders.retry", "function": "RetryOrder"},
+            ],
+        }
+        checks = suggest_checks(component)
+        dlq = next(c for c in checks if c["type"] == "dlq")
+        self.assertEqual(dlq["targets"], [
+            {"subscription": "orders.queue", "function": "ProcessOrder"},
+            {"subscription": "orders.retry", "function": "RetryOrder"},
+        ])
+
+    def test_no_dlq_check_when_no_known_subscriptions(self):
+        component = {
+            "name": "acme-mystery-worker",
+            "type": "queue-consumer",
+            "http_serving": False,
+            "message_consuming": True,
+        }
+        types = {c["type"] for c in suggest_checks(component)}
+        self.assertNotIn("dlq", types)
+
+    def test_no_dlq_check_when_subscriptions_empty(self):
+        component = {
+            "name": "acme-mystery-worker",
+            "type": "queue-consumer",
+            "http_serving": False,
+            "message_consuming": True,
+            "subscriptions": [],
+        }
+        types = {c["type"] for c in suggest_checks(component)}
+        self.assertNotIn("dlq", types)
+
+
+class TestRenderTargetsRoundTrip(unittest.TestCase):
+    """AC8: rendered `targets` list-of-mappings survives `_miniyaml.parse`
+    unchanged. Asserted on the parsed structure, not the rendered string."""
+
+    def test_dlq_targets_round_trip_through_miniyaml(self):
+        targets = [
+            {"subscription": "orders.queue", "function": "ProcessOrder"},
+            {"subscription": "orders.retry", "function": "RetryOrder"},
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
+        parsed_checks = parsed["components"][0]["checks"]
+        dlq = next(c for c in parsed_checks if c["type"] == "dlq")
+        self.assertEqual(dlq["targets"], targets)
+
+
 class TestAuditFindingsAreAllWarn(unittest.TestCase):
     """AC6: every finding audit_diagnosability can emit is WARN; the
     function exposes no ERROR severity at all."""
diff --git a/tests/test_lint_monitoring.py b/tests/test_lint_monitoring.py
index aff35bc..5dea794 100644
--- a/tests/test_lint_monitoring.py
+++ b/tests/test_lint_monitoring.py
@@ -37,6 +37,9 @@ components:
       - type: heartbeat
       - type: dlq
         harvest_mode: peek
+        targets:
+          - subscription: orders-sub
+            function: ProcessOrder
       - type: invariant
         query: "select count(*) from orders"
         fingerprint_by: order_id
@@ -307,30 +310,28 @@ class LintMonitoringTests(unittest.TestCase):
         findings = validate_monitoring(p)
         self.assertTrue(any("component[0]: must be a mapping" in f for f in findings))
 
+    _ALL_CHECKS = (
+        "    checks:\n"
+        "      - type: heartbeat\n"
+        "      - type: dlq\n"
+        "        harvest_mode: peek\n"
+        "        targets:\n"
+        "          - subscription: orders-sub\n"
+        "            function: ProcessOrder\n"
+        "      - type: invariant\n"
+        "        query: \"select count(*) from orders\"\n"
+        "        fingerprint_by: order_id\n"
+    )
+
     def test_checks_not_a_list(self):
-        text = VALID_CONFIG.replace(
-            "    checks:\n"
-            "      - type: heartbeat\n"
-            "      - type: dlq\n"
-            "        harvest_mode: peek\n"
-            "      - type: invariant\n"
-            "        query: \"select count(*) from orders\"\n"
-            "        fingerprint_by: order_id\n",
-            "    checks: nope\n",
-        )
+        text = VALID_CONFIG.replace(self._ALL_CHECKS, "    checks: nope\n")
         p = self._write(text)
         findings = validate_monitoring(p)
         self.assertTrue(any("'checks' must be a list" in f for f in findings))
 
     def test_check_not_a_mapping(self):
         text = VALID_CONFIG.replace(
-            "    checks:\n"
-            "      - type: heartbeat\n"
-            "      - type: dlq\n"
-            "        harvest_mode: peek\n"
-            "      - type: invariant\n"
-            "        query: \"select count(*) from orders\"\n"
-            "        fingerprint_by: order_id\n",
+            self._ALL_CHECKS,
             "    checks:\n"
             "      - nope\n",
         )
@@ -399,9 +400,17 @@ class TestCheckTargets(unittest.TestCase):
         p.write_text(text)
         return p
 
+    _DLQ_WITH_TARGETS = (
+        "      - type: dlq\n"
+        "        harvest_mode: peek\n"
+        "        targets:\n"
+        "          - subscription: orders-sub\n"
+        "            function: ProcessOrder\n"
+    )
+
     def test_dlq_target_missing_function_is_rejected(self):
         text = VALID_CONFIG.replace(
-            "      - type: dlq\n        harvest_mode: peek\n",
+            self._DLQ_WITH_TARGETS,
             "      - type: dlq\n"
             "        harvest_mode: peek\n"
             "        targets:\n"
@@ -414,7 +423,7 @@ class TestCheckTargets(unittest.TestCase):
 
     def test_dlq_target_missing_subscription_is_rejected(self):
         text = VALID_CONFIG.replace(
-            "      - type: dlq\n        harvest_mode: peek\n",
+            self._DLQ_WITH_TARGETS,
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
@@ -489,10 +490,6 @@ class TestCheckTargets(unittest.TestCase):
         self.assertEqual(len(findings), 1)
         self.assertIn("http-5xx", findings[0])
 
-    def test_targetless_dlq_check_still_validates_clean(self):
-        """T03 flips this; T01 must not — see PLAN.md escalation-predicate section."""
-        p = self._write(VALID_CONFIG)
-        self.assertEqual(validate_monitoring(p), [])
 
     def test_targets_not_a_list_is_rejected(self):
         text = VALID_CONFIG.replace(
@@ -527,7 +524,7 @@ class TestCheckTargets(unittest.TestCase):
 
     def test_findings_are_deterministically_ordered(self):
         text = VALID_CONFIG.replace(
-            "      - type: dlq\n        harvest_mode: peek\n",
+            self._DLQ_WITH_TARGETS,
             "      - type: dlq\n"
             "        harvest_mode: peek\n"
             "        targets:\n"
@@ -539,5 +536,83 @@ class TestCheckTargets(unittest.TestCase):
         self.assertEqual(first, second)
 
 
+class TestTargetsRequired(unittest.TestCase):
+    """FEAT-2026-0069/T03: a `dlq` check without `targets` is now rejected —
+    a DLQ always belongs to a specific subscription, so a target-less `dlq`
+    is always underspecified. `heartbeat` keeps no requirement — a
+    single-process HTTP service genuinely has nothing to enumerate."""
+
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
+            "      - type: dlq\n"
+            "        harvest_mode: peek\n"
+            "        targets:\n"
+            "          - subscription: orders-sub\n"
+            "            function: ProcessOrder\n",
+            "      - type: dlq\n        harvest_mode: peek\n",
+        )
+        p = self._write(text)
+        findings = validate_monitoring(p)
+        self.assertTrue(
+            any("'dlq' check requires 'targets'" in f for f in findings)
+        )
+
+    def test_finding_names_both_target_coordinates(self):
+        text = VALID_CONFIG.replace(
+            "      - type: dlq\n"
+            "        harvest_mode: peek\n"
+            "        targets:\n"
+            "          - subscription: orders-sub\n"
+            "            function: ProcessOrder\n",
+            "      - type: dlq\n        harvest_mode: peek\n",
+        )
+        p = self._write(text)
+        findings = validate_monitoring(p)
+        finding
… (diff truncated)

```
