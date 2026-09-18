### tests: PASS
```
$ python3 -m unittest tests.test_triage_severity_write -v -b
test_severity_appends_as_third_field (tests.test_triage_severity_write.RenderMarker.test_severity_appends_as_third_field) ... ok
test_two_field_form_is_byte_identical (tests.test_triage_severity_write.RenderMarker.test_two_field_form_is_byte_identical) ... ok
test_marked_issue_missing_severity_label_retries_label_only (tests.test_triage_severity_write.SeverityRepairIsIdempotent.test_marked_issue_missing_severity_label_retries_label_only) ... ok
test_marked_issue_with_severity_label_already_present_does_nothing (tests.test_triage_severity_write.SeverityRepairIsIdempotent.test_marked_issue_with_severity_label_already_present_does_nothing) ... ok
test_marker_is_written_before_label (tests.test_triage_severity_write.SeverityWrite.test_marker_is_written_before_label) ... ok
test_no_severity_key_produces_identical_argv (tests.test_triage_severity_write.SeverityWrite.test_no_severity_key_produces_identical_argv) ... ok
test_severity_label_failure_recorded_not_raised (tests.test_triage_severity_write.SeverityWrite.test_severity_label_failure_recorded_not_raised) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.000s

OK
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/tests-20260918T015456065906Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/lint-20260918T015456083407Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/agent-policy-example-lint-20260918T015456198612Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 77 events.jsonl file(s), 2230 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/event-type-gate-20260918T015456385839Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/roadmap-link-gate-20260918T015456431016Z.log
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
evaluable=38 evaluated=38 could_not_evaluate=0 excluded_no_baseline=45
ok: 38 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/arm-sweep-gate-20260918T015456780153Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/monitoring-example-lint-20260918T015456830012Z.log
```

### feature_oracle: FAIL
```
$ python3 -m unittest tests.test_triage_severity_end_to_end -v -b

======================================================================
ERROR: test_triage_severity_end_to_end (unittest.loader._FailedTest.test_triage_severity_end_to_end)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_triage_severity_end_to_end
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
ModuleNotFoundError: No module named 'tests.test_triage_severity_end_to_end'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/feature_oracle-20260918T015456877136Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-04-marker-then-label-write-path.md b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-04-marker-then-label-write-path.md
index 009d352..7197a71 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-04-marker-then-label-write-path.md
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-04-marker-then-label-write-path.md
@@ -1,12 +1,17 @@
 ---
 id: FEAT-2026-0113/T04
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 3.00
 produces:
   - specfuse/loop/triage.py
   - tests/test_triage_severity_write.py
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.20.1
+started_at: 2026-09-18T01:53:23.859462+00:00
 ---
 
 # T04 — the write path records severity: marker first, label second
diff --git a/specfuse/loop/triage.py b/specfuse/loop/triage.py
index 9f81e5e..dc6f7c3 100644
--- a/specfuse/loop/triage.py
+++ b/specfuse/loop/triage.py
@@ -62,6 +62,9 @@ CATEGORY_LABEL_MAP = {
 }
 
 _MARKER_TEMPLATE = "<!-- specfuse:triage category={category} confidence={confidence} -->"
+_MARKER_TEMPLATE_WITH_SEVERITY = (
+    "<!-- specfuse:triage category={category} confidence={confidence} severity={severity} -->"
+)
 _MARKER_RE = re.compile(r"<!-- specfuse:triage (?P<fields>.*?) -->")
 _MARKER_FIELD_RE = re.compile(r"(\S+)=(\S+)")
 
@@ -105,14 +108,21 @@ def labels_for(category: str) -> tuple:
     return (label,)
 
 
-def render_marker(category: str, confidence: str) -> str:
-    """Render the triage marker for `category`/`confidence`.
+def render_marker(category: str, confidence: str, severity: Optional[str] = None) -> str:
+    """Render the triage marker for `category`/`confidence`, plus a third
+    `severity=<value>` field when `severity` is given.
 
     Mirrors `monitor/issues.py`'s `_MARKER_TEMPLATE` convention: an
     HTML-comment marker embedded in the issue body, parsed back by
-    `parse_marker`.
+    `parse_marker`/`parse_marker_fields`. Byte-identical to the two-field
+    form when `severity` is `None` -- every marker already written in the
+    wild is read against that exact string.
     """
-    return _MARKER_TEMPLATE.format(category=category, confidence=confidence)
+    if severity is None:
+        return _MARKER_TEMPLATE.format(category=category, confidence=confidence)
+    return _MARKER_TEMPLATE_WITH_SEVERITY.format(
+        category=category, confidence=confidence, severity=severity
+    )
 
 
 def parse_marker_fields(body: str) -> Optional[dict]:
@@ -202,7 +212,10 @@ def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = F
         marker = parse_marker(body)
         if marker is not None:
             marked_category, _marked_confidence = marker
-            target_labels = labels_for(marked_category) if marked_category in CATEGORIES else ()
+            marked_severity = (parse_marker_fields(body) or {}).get("severity")
+            target_labels = list(labels_for(marked_category)) if marked_category in CATEGORIES else []
+            if marked_severity:
+                target_labels.append(f"severity:{marked_severity}")
             existing_labels = {
                 label.get("name") for label in decision.get("labels") or []
             }
@@ -235,6 +248,8 @@ def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = F
         if auto and confidence != "high":
             applied_category = "question"
 
+        severity = decision.get("severity")
+
         row = {
             "number": number,
             "category": applied_category,
@@ -242,8 +257,11 @@ def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = F
             "route": route_for(applied_category),
             "skipped": False,
         }
+        if severity is not None:
+            row["severity"] = severity
 
-        new_body = f"{body}\n\n{render_marker(applied_category, confidence)}" if body else render_marker(applied_category, confidence)
+        marker = render_marker(applied_category, confidence, severity)
+        new_body = f"{body}\n\n{marker}" if body else marker
         try:
             runner(
                 ["gh", "issue", "edit", str(number), "--repo", repo, "--body", new_body],
@@ -253,6 +271,8 @@ def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = F
             row["marker_written"] = False
             row["marker_error"] = str(exc)
             row["label_written"] = False
+            if severity is not None:
+                row["severity_label_written"] = False
             results.append(row)
             continue
         row["marker_written"] = True
@@ -272,6 +292,22 @@ def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = F
         else:
             row["label_written"] = True
 
+        if severity is not None:
+            try:
+                runner(
+                    [
+                        "gh", "issue", "edit", str(number),
+                        "--repo", repo,
+                        "--add-label", f"severity:{severity}",
+                    ],
+                    check=True,
+                )
+            except Exception as exc:  # noqa: BLE001 - severity label failure never raises
+                row["severity_label_written"] = False
+                row["severity_label_error"] = str(exc)
+            else:
+                row["severity_label_written"] = True
+
         results.append(row)
     return results
 
--- /dev/null
+++ b/tests/test_triage_severity_write.py
+# Copyright 2026 Specfuse Contributors
+# Licensed under the Apache License, Version 2.0. See LICENSE.
+"""Tests for the severity write path (FEAT-2026-0113/T04)."""
+
+from __future__ import annotations
+
+import unittest
+
+from specfuse.loop.triage import apply_triage, render_marker
+
+
+_REPO = "acme-widget/example"
+
+
+class _StubRunner:
+    """Records every call; raises on calls matching a scripted predicate."""
+
+    def __init__(self, raise_on=None):
+        self.calls = []
+        self._raise_on = raise_on
+
+    def __call__(self, args, check=True):
+        self.calls.append(args)
+        if self._raise_on is not None and self._raise_on(args):
+            raise RuntimeError("gh call failed")
+        return None
+
+
+class RenderMarker(unittest.TestCase):
+    def test_two_field_form_is_byte_identical(self):
+        self.assertEqual(
+            render_marker("bug", "high"),
+            "<!-- specfuse:triage category=bug confidence=high -->",
+        )
+
+    def test_severity_appends_as_third_field(self):
+        self.assertEqual(
+            render_marker("bug", "high", "major"),
+            "<!-- specfuse:triage category=bug confidence=high severity=major -->",
+        )
+
+
+class SeverityWrite(unittest.TestCase):
+    def test_marker_is_written_before_label(self):
+        runner = _StubRunner()
+        decisions = [{
+            "number": 7,
+            "body": "Body text.",
+            "category": "bug",
+            "confidence": "high",
+            "severity": "major",
+        }]
+
+        apply_triage(runner, _REPO, decisions)
+
+        body_index = next(i for i, c in enumerate(runner.calls) if "--body" in c)
+        severity_label_index = next(
+            i for i, c in enumerate(runner.calls)
+            if "--add-label" in c and "severity:major" in c
+        )
+        self.assertLess(body_index, severity_label_index)
+
+    def test_no_severity_key_produces_identical_argv(self):
+        runner_with = _StubRunner()
+        runner_without = _StubRunner()
+        base_decision = {
+            "number": 7,
+            "body": "Body text.",
+            "category": "feature",
+            "confidence": "high",
+        }
+
+        apply_triage(runner_without, _REPO, [dict(base_decision)])
+        apply_triage(runner_with, _REPO, [dict(base_decision)])
+
+        self.assertEqual(runner_without.calls, runner_with.calls)
+
+    def test_severity_label_failure_recorded_not_raised(self):
+        runner = _StubRunner(raise_on=lambda args: "severity:major" in args)
+        decisions = [{
+            "number": 9,
+            "body": "Body text.",
+            "category": "bug",
+            "confidence": "high",
+            "severity": "major",
+        }]
+
+        results = apply_triage(runner, _REPO, decisions)
+
+        self.assertTrue(results[0]["marker_written"])
+        self.assertFalse(results[0]["severity_label_written"])
+        self.assertTrue(any("--body" in c for c in runner.calls))
+        body_call = next(c for c in runner.calls if "--body" in c)
+        self.assertIn(
+            "<!-- specfuse:triage category=bug confidence=high severity=major -->",
+            body_call[body_call.index("--body") + 1],
+        )
+
+
+class SeverityRepairIsIdempotent(unittest.TestCase):
+    def test_marked_issue_missing_severity_label_retries_label_only(self):
+        runner = _StubRunner()
+        marked_body = (
+            "Body text.\n\n"
+            "<!-- specfuse:triage category=bug confidence=high severity=high -->"
+        )
+        decisions = [{
+            "number": 796,
+            "body": marked_body,
+            "category": "bug",
+            "confidence": "high",
+            "labels": [{"name": "triage:bug"}],
+        }]
+
+        results = apply_triage(runner, _REPO, decisions)
+
+        self.assertTrue(results[0]["skipped"])
+        self.assertTrue(results[0]["label_written"])
+        self.assertTrue(any(
+            "--add-label" in c and "severity:high" in c for c in runner.calls
+        ))
+        self.assertFalse(any("--body" in c for c in runner.calls))
+
+    def test_marked_issue_with_severity_label_already_present_does_nothing(self):
+        runner = _StubRunner()
+        marked_body = (
+            "Body text.\n\n"
+            "<!-- specfuse:triage category=bug confidence=high severity=high -->"
+        )
+        decisions = [{
+            "number": 248,
+            "body": marked_body,
+            "category": "bug",
+            "confidence": "high",
+            "labels": [{"name": "triage:bug"}, {"name": "severity:high"}],
+        }]
+
+        results = apply_triage(runner, _REPO, decisions)
+
+        self.assertTrue(results[0]["skipped"])
+        self.assertFalse(runner.calls)
+
+
+if __name__ == "__main__":
+    unittest.main()

```
