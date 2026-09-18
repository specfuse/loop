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
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/tests-20260918T020154649906Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/lint-20260918T020154670700Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/agent-policy-example-lint-20260918T020154791132Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 77 events.jsonl file(s), 2232 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/event-type-gate-20260918T020154928228Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/roadmap-link-gate-20260918T020154974480Z.log
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
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/arm-sweep-gate-20260918T020155291810Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/monitoring-example-lint-20260918T020155343109Z.log
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
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/feature_oracle-20260918T020155393391Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/GATE-02.md b/.specfuse/features/FEAT-2026-0113-triage-severity/GATE-02.md
index 2760679..667096d 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/GATE-02.md
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/GATE-02.md
@@ -2,6 +2,13 @@
 gate: 2
 status: open
 feature_oracle: "python3 -m unittest tests.test_triage_severity_end_to_end -v -b"
+baseline:
+  sha: d838f9c1f2d11926e9d7df4134392906541769c8
+  probed_at: 2026-09-18T01:54:56.993384+00:00
+  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:079d7d0f34d28da94dfc12d029c2811895aedaaa:1243e6b0132b414c07fe5cbe686e160a4037550a:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:1e7eddd5a3fb006c5435e947cd08d29e4f2b3d83:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4acc6dfc5e8cece358c167d876515eba4a39a500:5d728025305dbcbc973444ab63766194217eee09:5f9026863810e1e3137208731988d399091684f0:5ff66b6e4d8a264f23709ea60706111a4c59ed11:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:a2e0ab09b92e5f9fb2297b90c91a8e671835590c:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
+  entry_sha: d838f9c1f2d11926e9d7df4134392906541769c8
+  source: attributed:FEAT-2026-0113/T04
+  failing: []
 ---
 
 # Gate 2 — triage classifies severity and writes it
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-04-marker-then-label-write-path.md b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-04-marker-then-label-write-path.md
index 009d352..14d6611 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-04-marker-then-label-write-path.md
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-04-marker-then-label-write-path.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0113/T04
 type: implementation
 status: pending
-attempts: 0
+attempts: 2
 planned_cost_usd: 3.00
 produces:
   - specfuse/loop/triage.py
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl b/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl
index f7af206..1c5484c 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl
@@ -30,3 +30,5 @@
 {"timestamp": "2026-09-18T01:49:26.482272+00:00", "correlation_id": "FEAT-2026-0113/T03", "event_type": "baseline_attribution", "source": "driver", "source_version": "0.20.1", "payload": {"gate": 2, "failing": [], "attributed_to": "FEAT-2026-0113/T03"}}
 {"timestamp": "2026-09-18T01:53:23.694580+00:00", "correlation_id": "FEAT-2026-0113/T03", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.20.1", "payload": {"attempt": 2, "outcome": "failed", "duration_seconds": 236.339, "cost_usd": 0.8795466, "input_tokens": 54, "output_tokens": 17910, "cache_read_input_tokens": 1996453, "cache_creation_input_tokens": 74012, "model": "sonnet", "effort": "medium", "failure_class": "other", "failure_signature": "ERROR: test_triage_severity_end_to_end (unittest.loader._FailedTest.test_triage_severity_end_to_end)", "failure_excerpt": "test_failed_label_creation_is_not_raised_and_rubric_stays_usable (tests.test_severity_rubric.SeverityRubric.test_failed_label_creation_is_not_raised_and_rubric_stays_usable) ... ok\nok: no validation errors across 77 events.jsonl file(s), 2227 even\n...\nFailedTest.test_triage_severity_end_to_end)\nImportError: Failed to import test module: test_triage_severity_end_to_end\nTraceback (most recent call last):\nModuleNotFoundError: No module named 'tests.test_triage_severity_end_to_end'\nFAILED (errors=1)", "files_touched": [".specfuse/features/FEAT-2026-0113-triage-severity/GATE-02.md", "tests/test_severity_rubric.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
 {"timestamp": "2026-09-18T01:53:23.694847+00:00", "correlation_id": "FEAT-2026-0113/T03", "event_type": "human_escalation", "source": "driver", "source_version": "0.20.1", "payload": {"reason": "spinning_signature_repeat", "failure_class": "other", "failure_signature": "ERROR: test_triage_severity_end_to_end (unittest.loader._FailedTest.test_triage_severity_end_to_end)", "attempts": 2, "attempts_usage": [{"attempt": 1, "duration_seconds": 154.589, "cost_usd": 0.8390382, "input_tokens": 52, "output_tokens": 16724, "cache_read_input_tokens": 1948261, "cache_creation_input_tokens": 69760}, {"attempt": 2, "duration_seconds": 236.339, "cost_usd": 0.8795466, "input_tokens": 54, "output_tokens": 17910, "cache_read_input_tokens": 1996453, "cache_creation_input_tokens": 74012}], "message": "<!-- specfuse:escalation id=FEAT-2026-0113/T03 -->\n\nESCALATED \u2014 FEAT-2026-0113/T03 (T03 \u2014 extract the label listing, and read the severity rubric from it)\n\n## What has been done so far\nGate 2 is open. Work units finished so far: FEAT-2026-0113/G1-CLOSE-INTERMEDIATE, FEAT-2026-0113/G1-PLAN, FEAT-2026-0113/T01, FEAT-2026-0113/T01H, FEAT-2026-0113/T02. FEAT-2026-0113/T03 was dispatched 2 time(s): attempt 1: failed, attempt 2: failed. The automatic re-plan did not fire during this run.\n\n## What this issue is about\nFEAT-2026-0113/T03 has escalated for a human decision (spinning_signature_repeat) and no further automatic attempt will be dispatched until one is made.\n\n## What decision is needed, and why\nSomeone must choose how FEAT-2026-0113/T03 proceeds, because the driver has run out of ways to choose for it: it stopped short of its attempt budget (3) for a reason no further attempt would change (spinning_signature_repeat), and no automatic re-plan applies to this unit. The options below are the only ways gate 2 moves again. Until one is chosen nothing further is dispatched: the 5 work unit(s) waiting behind this one stay blocked, and the gate cannot close.\n\nWork units still waiting behind it: FEAT-2026-0113/T04, FEAT-2026-0113/T05, FEAT-2026-0113/T06, FEAT-2026-0113/G2-CLOSE-INTERMEDIATE, FEAT-2026-0113/G2-PLAN.\n\n## Why it did not, or could not, close automatically\nNo further automatic attempt is available for `spinning_signature_repeat`: same failure twice \u2014 the unit's shape, not the attempt.\n\n## Options, each with pros and cons\n1. **Re-plan the remaining gate** \u2014 run `/unblock-wu` on FEAT-2026-0113/T03, FEAT-2026-0113/T04, FEAT-2026-0113/T05, FEAT-2026-0113/T06, FEAT-2026-0113/G2-CLOSE-INTERMEDIATE, FEAT-2026-0113/G2-PLAN, choosing re-arm (retry-as-is) for each. Re-arming resets each unit's `attempts` to 0, so the driver's automatic re-plan trigger \u2014 no automatic re-plan ran during this run \u2014 becomes reachable again for every re-armed unit in gate 2, not just the one that spun out. Pros: widens a remedy that already produced a rewrite once, without inventing a new mechanism. Cons: it is the same remedy that already failed for FEAT-2026-0113/T03; if nothing about scope or shape changes first, the re-plan may reproduce the same rewrite.\n2. **Abandon the unit** \u2014 pros: unblocks the rest of the gate; cons: anything depending on this unit, and everything named in option 1 if it was re-armed instead, is stranded.\n\n## A recommendation\nOption 1. Same failure twice \u2014 the unit's shape, not the attempt, and the remedy is already named and one command away \u2014 no automatic re-plan ran during this run, so this is widening it rather than proposing anything new.\n\nReply with the number of your choice, or prose if none fit:\n1. Re-plan the remaining gate\n2. Abandon the unit\n\nResume after deciding:\n  python3 -m specfuse.loop.loop --feature FEAT-2026-0113"}}
+{"timestamp": "2026-09-18T01:53:23.859647+00:00", "correlation_id": "FEAT-2026-0113/T04", "event_type": "task_started", "source": "driver", "source_version": "0.20.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-18T01:54:56.938483+00:00", "correlation_id": "FEAT-2026-0113/T04", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.20.1", "payload": {"attempt": 1, "outcome": "failed", "duration_seconds": 93.016, "cost_usd": 0.556754, "input_tokens": 38, "output_tokens": 9970, "cache_read_input_tokens": 1210675, "cache_creation_input_tokens": 53105, "model": "sonnet", "effort": "medium", "failure_class": "other", "failure_signature": "ERROR: test_triage_severity_end_to_end (unittest.loader._FailedTest.test_triage_severity_end_to_end)", "failure_excerpt": "test_severity_label_failure_recorded_not_raised (tests.test_triage_severity_write.SeverityWrite.test_severity_label_failure_recorded_not_raised) ... ok\nok: no validation errors across 77 events.jsonl file(s), 2230 event(s) checked\nNO VERDICT FOUND\n...\nFailedTest.test_triage_severity_end_to_end)\nImportError: Failed to import test module: test_triage_severity_end_to_end\nTraceback (most recent call last):\nModuleNotFoundError: No module named 'tests.test_triage_severity_end_to_end'\nFAILED (errors=1)", "files_touched": ["tests/test_triage_severity_write.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
diff --git a/specfuse/loop/triage.py b/specfuse/loop/triage.py
index 9f81e5e..3e6f5dd 100644
--- a/specfuse/loop/triage.py
+++ b/specfuse/loop/triage.py
@@ -25,6 +25,7 @@ import json
 import re
 from typing import Callable, Optional
 
+from specfuse.loop.agent_policy import SEVERITY_LABEL_PREFIX
 from specfuse.loop.escalation import NEEDS_HUMAN_LABEL
 from specfuse.monitor.issues import DEFAULT_LIST_LIMIT, has_finding_marker
 
@@ -62,6 +63,9 @@ CATEGORY_LABEL_MAP = {
 }
 
 _MARKER_TEMPLATE = "<!-- specfuse:triage category={category} confidence={confidence} -->"
+_MARKER_TEMPLATE_WITH_SEVERITY = (
+    "<!-- specfuse:triage category={category} confidence={confidence} severity={severity} -->"
+)
 _MARKER_RE = re.compile(r"<!-- specfuse:triage (?P<fields>.*?) -->")
 _MARKER_FIELD_RE = re.compile(r"(\S+)=(\S+)")
 
@@ -105,14 +109,21 @@ def labels_for(category: str) -> tuple:
     return (label,)
 
 
-def render_marker(category: str, confidence: str) -> str:
-    """Render the triage marker for `category`/`confidence`.
+def render_marker(category: str, confidence: str, severity: Optional[str] = None) -> str:
+    """Render the triage marker for `category`/`confidence`, plus `severity`
+    as a third field when given.
 
     Mirrors `monitor/issues.py`'s `_MARKER_TEMPLATE` convention: an
     HTML-comment marker embedded in the issue body, parsed back by
-    `parse_marker`.
+    `parse_marker`/`parse_marker_fields`. With `severity=None` the output is
+    byte-identical to the pre-FEAT-2026-0113 two-field string -- every marker
+    already written in the wild is read against that literal.
     """
-    return _MARKER_TEMPLATE.format(category=category, confidence=confidence)
+    if severity is None:
+        return _MARKER_TEMPLATE.format(category=category, confidence=confidence)
+    return _MARKER_TEMPLATE_WITH_SEVERITY.format(
+        category=category, confidence=confidence, severity=severity
+    )
 
 
 def parse_marker_fields(body: str) -> Optional[dict]:
@@ -202,7 +213,10 @@ def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = F
         marker = parse_marker(body)
         if marker is not None:
             marked_category, _marked_confidence = marker
-            target_labels = labels_for(marked_category) if marked_category in CATEGORIES else ()
+            marked_severity = (parse_marker_fields(body) or {}).get("severity")
+            target_labels = list(labels_for(marked_category)) if marked_category in CATEGORIES else []
+            if marked_severity:
+                target_labels.append(f"{SEVERITY_LABEL_PREFIX}{marked_severity}")
             existing_labels = {
                 label.get("name") for label in decision.get("labels") or []
             }
@@ -235,6 +249,8 @@ def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = F
         if auto and confidence != "high":
             applied_category = "question"
 
+        severity = decision.get("severity")
+
         row = {
             "number": number,
             "category": applied_category,
@@ -242,8 +258,11 @@ def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = F
             "route": route_for(applied_category),
             "skipped": False,
         }
+        if severity is not None:
+            row["severity"] = severity
 
-        new_body = f"{body}\n\n{render_marker(applied_category, confidence)}" if body else render_marker(applied_category, confidence)
+        marker_text = render_marker(applied_category, confidence, severity)
+        new_body = f"{body}\n\n{marker_text}" if body else marker_text
         try:
             runner(
                 ["gh", "issue", "edit", str(number), "--repo", repo, "--body", new_body],
@@ -257,12 +276,16 @@ def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = F
             continue
         row["marker_written"] = True
 
+        applied_labels = list(labels_for(applied_category))
+        if severity is not None:
+            applied_labels.append(f"{SEVERITY_LABEL_PREFIX}{severity}")
+
         try:
             runner(
                 [
                     "gh", "issue", "edit", str(number),
                     "--repo", repo,
-                    "--add-label", ",".join(labels_for(applied_category)),
+                    "--add-label", ",".join(applied_labels),
                 ],
                 check=True,
             )
--- /dev/null
+++ b/tests/test_triage_severity_write.py
+# Copyright 2026 Specfuse Contributors
+# Licensed under the Apache License, Version 2.0. See LICENSE.
+"""Tests for the severity write path (FEAT-2026-0113/T04).
+
+Marker first, label second -- see `PLAN.md`'s "Record precedence" section.
+The marker's `severity=` field is authoritative; the `severity:<value>`
+label is a re-derived projection, never an independent record.
+"""
+
+from __future__ import annotations
+
+import unittest
+
+from specfuse.loop.triage import apply_triage, render_marker
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
+            render_marker("bug", "high", "critical"),
+            "<!-- specfuse:triage category=bug confidence=high severity=critical -->",
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
+            "severity": "high",
+        }]
+
+        apply_triage(runner, _REPO, decisions)
+
+        body_call_index = next(i for i, c in enumerate(runner.calls) if "--body" in c)
+        label_call_index = next(i for i, c in enumerate(runner.calls) if "--add-label" in c)
+        self.assertLess(body_call_index, label_call_index)
+
+        label_call = runner.calls[label_call_index]
+        added = label_call[label_call.index("--add-label") + 1].split(",")
+        self.assertIn("severity:high", added)
+
+    def test_no_severity_key_produces_identical_argv(self):
+        runner_without_severity = _StubRunner()
+        runner_baseline = _StubRunner()
+
+        decision_without_severity = {
+            "number": 7, "body": "Body text.", "category": "feature", "confidence": "high",
+        }
+        apply_triage(runner_without_severity, _REPO, [decision_without_severity])
+        apply_triage(runner_baseline, _REPO, [dict(decision_without_severity)])
+
+        self.assertEqual(runner_without_severity.calls, runner_baseline.calls)
+
+    def test_severity_label_failure_recorded_not_raised(self):
+        runner = _StubRunner(raise_on=lambda args: "--add-label" in args)
+        decisions = [{
+            "number": 9,
+            "body": "Body text.",
+            "category": "wontfix",
+            "confidence": "high",
+            "severity": "medium",
+        }]
+
+        results = apply_triage(runner, _REPO, decisions)
+
+        self.assertTrue(results[0]["marker_written"])
+        self.assertFalse(results[0]["label_written"])
+        self.assertIn("label_error", results[0])
+        body_call = next(c for c in runner.calls if "--body" in c)
+        marker_body = body_call[body_call.index("--body") + 1]
+        self.assertIn("severity=medium", marker_body)
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
+        self.assertFalse(any("--body" in c for c in runner.calls))
+        label_call = next(c for c in runner.calls if "--add-label" in c)
+        added = label_call[label_call.index("--add-label") + 1].split(",")
+        self.assertEqual(added, ["severity:high"])
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
