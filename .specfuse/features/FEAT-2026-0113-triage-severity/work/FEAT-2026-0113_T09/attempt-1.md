### tests: PASS
```
$ python3 -m unittest tests.test_severity_backfill_apply -v -b
test_an_issue_already_carrying_a_severity_is_never_written (tests.test_severity_backfill_apply.BackfillApply.test_an_issue_already_carrying_a_severity_is_never_written) ... ok
test_failed_label_write_is_recorded_and_marker_stays (tests.test_severity_backfill_apply.BackfillApply.test_failed_label_write_is_recorded_and_marker_stays) ... ok
test_failed_marker_write_leaves_label_unwritten (tests.test_severity_backfill_apply.BackfillApply.test_failed_marker_write_leaves_label_unwritten) ... ok
test_marker_is_amended_before_the_label_is_added (tests.test_severity_backfill_apply.BackfillApply.test_marker_is_amended_before_the_label_is_added) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/tests-20260918T111345201729Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/lint-20260918T111345261384Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/agent-policy-example-lint-20260918T111345357658Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 77 events.jsonl file(s), 2279 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/event-type-gate-20260918T111345533111Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/roadmap-link-gate-20260918T111345579461Z.log
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
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/arm-sweep-gate-20260918T111345965553Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/monitoring-example-lint-20260918T111346015558Z.log
```

### feature_oracle: FAIL
```
$ python3 -m unittest tests.test_severity_backfill_end_to_end -v -b
test_the_conductor_cannot_reach_the_backfill (tests.test_severity_backfill_end_to_end.SeverityBackfill.test_the_conductor_cannot_reach_the_backfill) ... ok

======================================================================
FAIL: test_import_exposes_backfill_severity_and_the_named_stub (tests.test_severity_backfill_end_to_end.SeverityBackfill.test_import_exposes_backfill_severity_and_the_named_stub)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christian/Specfuse/loop/tests/test_severity_backfill_end_to_end.py", line 150, in test_import_exposes_backfill_severity_and_the_named_stub
    self.assertTrue(hasattr(mod, "_amend_marker"))
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true

----------------------------------------------------------------------
Ran 4 tests in 0.066s

FAILED (failures=1)
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/feature_oracle-20260918T111346146997Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-09-backfill-write-path.md b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-09-backfill-write-path.md
index 262f689..21dd4aa 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-09-backfill-write-path.md
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-09-backfill-write-path.md
@@ -1,12 +1,17 @@
 ---
 id: FEAT-2026-0113/T09
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 3.00
 produces:
   - specfuse/agent/severity_backfill.py
   - tests/test_severity_backfill_apply.py
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.20.1
+started_at: 2026-09-18T11:10:49.092900+00:00
 ---
 
 # T09 — the backfill write path: marker amended first, label projected second
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl b/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl
index 1615c37..ebd50e0 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl
@@ -75,3 +75,7 @@
 {"timestamp": "2026-09-18T11:06:12.897536+00:00", "correlation_id": "FEAT-2026-0113/T07", "event_type": "task_started", "source": "driver", "source_version": "0.20.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
 {"timestamp": "2026-09-18T11:09:04.677529+00:00", "correlation_id": "FEAT-2026-0113/T07", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.20.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 171.625, "cost_usd": 0.8651910000000002, "input_tokens": 46, "output_tokens": 13720, "cache_read_input_tokens": 1922545, "cache_creation_input_tokens": 85085, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0113-triage-severity/WU-07-backfill-walking-skeleton.md", "pyproject.toml", "specfuse/agent/severity_backfill.py", "tests/test_severity_backfill_end_to_end.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
 {"timestamp": "2026-09-18T11:09:04.677782+00:00", "correlation_id": "FEAT-2026-0113/T07", "event_type": "task_completed", "source": "driver", "source_version": "0.20.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 171.625, "cost_usd": 0.8651910000000002, "input_tokens": 46, "output_tokens": 13720, "cache_read_input_tokens": 1922545, "cache_creation_input_tokens": 85085}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.865191, "cumulative_cost_usd": 0.865191, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
+{"timestamp": "2026-09-18T11:09:04.697524+00:00", "correlation_id": "FEAT-2026-0113/T08", "event_type": "task_started", "source": "driver", "source_version": "0.20.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-18T11:10:49.048659+00:00", "correlation_id": "FEAT-2026-0113/T08", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.20.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 104.236, "cost_usd": 0.5233986, "input_tokens": 42, "output_tokens": 7321, "cache_read_input_tokens": 1271978, "cache_creation_input_tokens": 48249, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0113-triage-severity/WU-08-backfill-selection-and-amend.md", ".specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl", "specfuse/loop/triage.py", "tests/test_severity_backfill_marker.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
+{"timestamp": "2026-09-18T11:10:49.048822+00:00", "correlation_id": "FEAT-2026-0113/T08", "event_type": "task_completed", "source": "driver", "source_version": "0.20.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 104.236, "cost_usd": 0.5233986, "input_tokens": 42, "output_tokens": 7321, "cache_read_input_tokens": 1271978, "cache_creation_input_tokens": 48249}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.523399, "cumulative_cost_usd": 0.523399, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
+{"timestamp": "2026-09-18T11:10:49.054739+00:00", "correlation_id": "FEAT-2026-0113", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.20.1", "payload": {"gate": 3, "wu_id": "FEAT-2026-0113/T08", "driver_paths": ["specfuse/loop/triage.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "71e9ac456232717a5444bdab39314d156b77cb32", "next_pin_tree": "7e7881682e06476507d34f334a82b309164dbafc"}}
diff --git a/specfuse/agent/severity_backfill.py b/specfuse/agent/severity_backfill.py
index 8e4a925..a466fe5 100644
--- a/specfuse/agent/severity_backfill.py
+++ b/specfuse/agent/severity_backfill.py
@@ -19,14 +19,16 @@ unattended run uses.
 
 - selection breadth -- takes a single issue number rather than T08's
   predicate over the whole open-issue listing;
-- the marker amendment -- `_amend_marker` below, which T08's
-  `amend_marker_severity` (`specfuse.loop.triage`) replaces and T09 deletes;
 - classification -- `_STUB_SEVERITY` stands in for T10's classification
   session.
 
 **Not stubbed:** the write order. The marker's `severity=` field is
 authoritative and is written before the `severity:<value>` label, mirroring
 `specfuse.loop.triage.apply_triage`'s own marker-first sequence.
+`apply_severity_backfill` (FEAT-2026-0113/T09) is the real, decision-batch
+write path this module's real callers use; `backfill_severity` above stays
+the single-issue CLI shape and now amends its marker through
+`triage.amend_marker_severity` rather than a local stub.
 """
 
 from __future__ import annotations
@@ -46,21 +48,6 @@ def _default_runner(argv: list, check: bool = False):
     return subprocess.run(argv, check=check, capture_output=True, text=True)
 
 
-def _amend_marker(body: str, category: str, confidence: str, severity: str) -> str:
-    """Replace *body*'s two-field triage marker with the three-field form
-    carrying *severity*.
-
-    Stub: assumes *body* carries the marker in exactly the form
-    `triage.render_marker(category, confidence)` renders it, with no other
-    fields. `specfuse.loop.triage.amend_marker_severity` (T08) is the real
-    amendment this is stood in for; T09 deletes this function when it
-    switches the call site over (§9).
-    """
-    old_marker = triage.render_marker(category, confidence)
-    new_marker = triage.render_marker(category, confidence, severity)
-    return body.replace(old_marker, new_marker, 1)
-
-
 def _find_issue(runner: Callable, repo: str, issue_number: int) -> Optional[dict]:
     result = runner(
         [
@@ -126,7 +113,7 @@ def backfill_severity(
             "would_set_severity": chosen_severity,
         }
 
-    new_body = _amend_marker(body, category, confidence, chosen_severity)
+    new_body = triage.amend_marker_severity(body, chosen_severity)
     runner(
         ["gh", "issue", "edit", str(issue_number), "--repo", repo, "--body", new_body],
         check=True,
@@ -139,6 +126,74 @@ def backfill_severity(
     return {"number": issue_number, "amended": True, "severity": chosen_severity}
 
 
+def apply_severity_backfill(runner: Callable, repo: str, decisions: list) -> list:
+    """Write each decision in `decisions` against its GitHub issue, marker
+    first, label second.
+
+    Each decision is a mapping carrying `number`, `body` (the issue's
+    current body, read at selection time) and `severity`. Mirrors
+    `specfuse.loop.triage.apply_triage`'s marker-first shape, but as a
+    second write path rather than a branch inside that one: a decision whose
+    body's marker already carries `severity=` is the idempotency check --
+    it produces no `gh` call at all and is reported `skipped` on its row,
+    the stop condition that bounds a repeat run over the same candidates.
+
+    The marker write happens through `triage.amend_marker_severity`, so the
+    amended body's `category=`/`confidence=` are exactly what was read, never
+    re-derived. A failed marker write is recorded and never raised, and
+    leaves the label unwritten -- no issue is ever labelled with a severity
+    its marker does not carry. A failed label write is likewise recorded and
+    never raised, leaving the already-written marker in place.
+    """
+    results = []
+    for decision in decisions:
+        number = decision["number"]
+        body = decision.get("body") or ""
+        severity = decision["severity"]
+
+        fields = triage.parse_marker_fields(body)
+        if fields is None or fields.get("severity"):
+            results.append(
+                {
+                    "number": number,
+                    "skipped": True,
+                    "marker_written": False,
+                    "label_written": False,
+                }
+            )
+            continue
+
+        new_body = triage.amend_marker_severity(body, severity)
+        row = {"number": number, "severity": severity, "skipped": False}
+        try:
+            runner(
+                ["gh", "issue", "edit", str(number), "--repo", repo, "--body", new_body],
+                check=True,
+            )
+        except Exception as exc:  # noqa: BLE001 - recorded, not raised
+            row["marker_written"] = False
+            row["marker_error"] = str(exc)
+            row["label_written"] = False
+            results.append(row)
+            continue
+        row["marker_written"] = True
+
+        label = triage.severity_label_for(severity)
+        try:
+            runner(
+                ["gh", "issue", "edit", str(number), "--repo", repo, "--add-label", label],
+                check=True,
+            )
+        except Exception as exc:  # noqa: BLE001 - recorded, not raised
+            row["label_written"] = False
+            row["label_error"] = str(exc)
+        else:
+            row["label_written"] = True
+
+        results.append(row)
+    return results
+
+
 def build_parser() -> argparse.ArgumentParser:
     parser = argparse.ArgumentParser(
         prog="specfuse-backfill-severity",
--- /dev/null
+++ b/tests/test_severity_backfill_apply.py
+# Copyright 2026 Specfuse Contributors
+# Licensed under the Apache License, Version 2.0. See LICENSE.
+"""Tests for FEAT-2026-0113/T09's backfill write path."""
+
+from __future__ import annotations
+
+import unittest
+from types import SimpleNamespace
+
+from specfuse.agent.severity_backfill import apply_severity_backfill
+from specfuse.loop.triage import parse_marker_fields, render_marker
+
+_REPO = "acme-widget/example"
+
+
+class _StubRunner:
+    def __init__(self, outcomes):
+        self._outcomes = list(outcomes)
+        self.calls = []
+
+    def __call__(self, argv, check=False):
+        self.calls.append(argv)
+        outcome = self._outcomes.pop(0)
+        if isinstance(outcome, Exception):
+            raise outcome
+        return outcome
+
+
+_OK = SimpleNamespace(returncode=0, stdout="", stderr="")
+
+
+class BackfillApply(unittest.TestCase):
+    def test_marker_is_amended_before_the_label_is_added(self):
+        body = render_marker("bug", "low") + "\n\nSomething broke."
+        decisions = [{"number": 1, "body": body, "severity": "high"}]
+        runner = _StubRunner([_OK, _OK])
+
+        results = apply_severity_backfill(runner, _REPO, decisions)
+
+        self.assertEqual(2, len(runner.calls))
+        body_call, label_call = runner.calls
+        self.assertIn("--body", body_call)
+        self.assertIn("--add-label", label_call)
+        self.assertLess(runner.calls.index(body_call), runner.calls.index(label_call))
+        self.assertEqual(["gh", "issue", "edit", "1", "--repo", _REPO], body_call[:6])
+        amended_body = body_call[body_call.index("--body") + 1]
+        fields = parse_marker_fields(amended_body)
+        self.assertEqual("bug", fields["category"])
+        self.assertEqual("low", fields["confidence"])
+        self.assertEqual("high", fields["severity"])
+        self.assertIn("severity:high", label_call)
+        self.assertFalse(results[0]["skipped"])
+        self.assertTrue(results[0]["marker_written"])
+        self.assertTrue(results[0]["label_written"])
+
+    def test_an_issue_already_carrying_a_severity_is_never_written(self):
+        body = render_marker("bug", "high", "high") + "\n\nAlready done."
+        decisions = [{"number": 2, "body": body, "severity": "medium"}]
+        runner = _StubRunner([])
+
+        results = apply_severity_backfill(runner, _REPO, decisions)
+
+        self.assertEqual([], runner.calls)
+        self.assertTrue(results[0]["skipped"])
+        self.assertFalse(results[0]["marker_written"])
+        self.assertFalse(results[0]["label_written"])
+
+    def test_failed_label_write_is_recorded_and_marker_stays(self):
+        body = render_marker("feature", "high") + "\n\nBody."
+        decisions = [{"number": 3, "body": body, "severity": "low"}]
+        runner = _StubRunner([_OK, RuntimeError("label API error")])
+
+        results = apply_severity_backfill(runner, _REPO, decisions)
+
+        self.assertEqual(2, len(runner.calls))
+        self.assertTrue(results[0]["marker_written"])
+        self.assertFalse(results[0]["label_written"])
+        self.assertIn("label_error", results[0])
+
+    def test_failed_marker_write_leaves_label_unwritten(self):
+        body = render_marker("feature", "high") + "\n\nBody."
+        decisions = [{"number": 4, "body": body, "severity": "low"}]
+        runner = _StubRunner([RuntimeError("body API error")])
+
+        results = apply_severity_backfill(runner, _REPO, decisions)
+
+        self.assertEqual(1, len(runner.calls))
+        self.assertFalse(results[0]["marker_written"])
+        self.assertFalse(results[0]["label_written"])
+        self.assertIn("marker_error", results[0])
+
+
+if __name__ == "__main__":
+    unittest.main()

```
