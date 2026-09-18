### tests: PASS
```
$ python3 -m unittest tests.test_severity_rubric -v -b
test_empty_description_on_a_recognized_value_gets_shipped_definition_only (tests.test_severity_rubric.SeverityRubric.test_empty_description_on_a_recognized_value_gets_shipped_definition_only) ... ok
test_failed_label_creation_is_not_raised_and_rubric_stays_usable (tests.test_severity_rubric.SeverityRubric.test_failed_label_creation_is_not_raised_and_rubric_stays_usable) ... ok
test_missing_gh_binary_returns_empty_dict (tests.test_severity_rubric.SeverityRubric.test_missing_gh_binary_returns_empty_dict) ... ok
test_no_severity_labels_provisions_the_four_labels (tests.test_severity_rubric.SeverityRubric.test_no_severity_labels_provisions_the_four_labels) ... ok
test_no_severity_labels_returns_shipped_default_rubric (tests.test_severity_rubric.SeverityRubric.test_no_severity_labels_returns_shipped_default_rubric) ... ok
test_nonzero_list_exit_returns_empty_dict (tests.test_severity_rubric.SeverityRubric.test_nonzero_list_exit_returns_empty_dict) ... ok
test_own_label_with_recognized_value_issues_zero_create_calls (tests.test_severity_rubric.SeverityRubric.test_own_label_with_recognized_value_issues_zero_create_calls) ... ok
test_repo_defined_severity_labels_issue_zero_create_calls (tests.test_severity_rubric.SeverityRubric.test_repo_defined_severity_labels_issue_zero_create_calls) ... ok
test_rubric_reads_label_descriptions (tests.test_severity_rubric.SeverityRubric.test_rubric_reads_label_descriptions) ... ok
test_unparseable_list_output_returns_empty_dict (tests.test_severity_rubric.SeverityRubric.test_unparseable_list_output_returns_empty_dict) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.000s

OK
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/tests-20260918T015322975503Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/lint-20260918T015322991012Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/agent-policy-example-lint-20260918T015323080273Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 77 events.jsonl file(s), 2227 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/event-type-gate-20260918T015323209285Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/roadmap-link-gate-20260918T015323249249Z.log
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
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/arm-sweep-gate-20260918T015323545079Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/monitoring-example-lint-20260918T015323589569Z.log
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
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/feature_oracle-20260918T015323634211Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/GATE-02.md b/.specfuse/features/FEAT-2026-0113-triage-severity/GATE-02.md
index 2760679..a22ca7b 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/GATE-02.md
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/GATE-02.md
@@ -2,6 +2,13 @@
 gate: 2
 status: open
 feature_oracle: "python3 -m unittest tests.test_triage_severity_end_to_end -v -b"
+baseline:
+  sha: 4dc467ed4483cf3d46d959c92ba7371ba729d77a
+  probed_at: 2026-09-18T01:44:39.762290+00:00
+  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:079d7d0f34d28da94dfc12d029c2811895aedaaa:1243e6b0132b414c07fe5cbe686e160a4037550a:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:1e7eddd5a3fb006c5435e947cd08d29e4f2b3d83:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4acc6dfc5e8cece358c167d876515eba4a39a500:5d728025305dbcbc973444ab63766194217eee09:5f9026863810e1e3137208731988d399091684f0:5ff66b6e4d8a264f23709ea60706111a4c59ed11:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:a2e0ab09b92e5f9fb2297b90c91a8e671835590c:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
+  entry_sha: 4dc467ed4483cf3d46d959c92ba7371ba729d77a
+  source: attributed:FEAT-2026-0113/T03
+  failing: []
 ---
 
 # Gate 2 — triage classifies severity and writes it
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-03-severity-rubric-reader.md b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-03-severity-rubric-reader.md
index c3ab69a..069c3fe 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-03-severity-rubric-reader.md
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-03-severity-rubric-reader.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0113/T03
 type: implementation
 status: pending
-attempts: 0
+attempts: 2
 planned_cost_usd: 3.00
 produces:
   - specfuse/loop/labels.py
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl b/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl
index 0b25505..2cc1800 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/events.jsonl
@@ -25,3 +25,5 @@
 {"timestamp": "2026-09-18T01:06:57.379398+00:00", "correlation_id": "FEAT-2026-0113", "event_type": "arm_predicate_evaluated", "source": "driver", "source_version": "0.20.1", "payload": {"gate": 1, "would_arm": false, "predicate_version": "v1", "classes": {"budget_projection": {"status": "clean", "reason": "projected spend $37.53 within 2.0x baseline planned total $20.50 (cap $41.00)"}, "judge_editing": {"status": "fired", "reason": "FEAT-2026-0113/T04 produces specfuse/loop/triage.py"}, "decision_class_paths": {"status": "clean", "reason": "no drafted WU touches a recognised dependency manifest (pyproject.toml, package.json, pom.xml, build.gradle, build.gradle.kts, Cargo.toml, go.mod, Gemfile, composer.json, requirements*.txt, *.csproj)"}, "retroactive_edits": {"status": "clean", "reason": "no passed-gate baseline WU altered or removed"}, "drift_caps": {"status": "fired", "reason": "added WU count 7 exceeds 0.5x baseline count 5 (cap 2.5); added planned cost $23.00 exceeds 0.5x baseline planned total $20.50 (cap $10.25)"}, "missing_provenance": {"status": "fired", "reason": "added WU(s) missing provenance: FEAT-2026-0113/G2-CLOSE-INTERMEDIATE, FEAT-2026-0113/G2-PLAN, FEAT-2026-0113/T01H, FEAT-2026-0113/T03, FEAT-2026-0113/T04, FEAT-2026-0113/T05, FEAT-2026-0113/T06"}, "open_questions_human_only": {"status": "fired", "reason": "GATE-02-REVIEW.md open_questions non-empty: [\"Q1 (T03, flagged as uncertain in PLAN.md's Assumptions): does the rubric reader belong in gate 2 at all, or should the pure extraction have landed in gate 1? Drafted into gate 2 \u2014 reasoning and the counter-argument below.\", \"Q2 (T03, T05): the rubric is vocabulary-only \u2014 a `severity:<value>` label whose value is outside SEVERITY_VALUES is not offered to the classifier even when `rules.bugs.severity_aliases` maps it (#3349). Should an operator's declared alias widen the rubric too?\", 'Q3 (T04, T05): one `confidence` field governs both category and severity; no `severity_confidence` field is added. A low-confidence answer drops the severity entirely \u2014 no marker field, no label. Is a fourth field worth it?', 'Q4 (T06 criterion 2): the opt-out is proved by `gh` argv equality, with the one read-only label listing excluded from the comparison. That listing is a real new API call per run for every repository, including those that opted out. Acceptable?', \"Q5 (T05): a repository that defines a `severity:*` label with an empty description gets an undefined rubric entry, and T05 escalates rather than defaulting. Should the label's own value be allowed to stand in as its definition?\"]"}, "plan_next_lint": {"status": "clean", "reason": "plan-next lint: no findings"}}}}
 {"timestamp": "2026-09-18T01:06:57.369295+00:00", "correlation_id": "FEAT-2026-0113", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.20.1", "payload": {"gate": 1, "edits": [{"wu_id": "FEAT-2026-0113/T01H", "driver_paths": ["specfuse/loop/triage.py"]}], "dispatched_after": ["FEAT-2026-0113/T02", "FEAT-2026-0113/G1-CLOSE-INTERMEDIATE", "FEAT-2026-0113/G1-PLAN"]}}
 {"timestamp": "2026-09-18T01:42:04.715193+00:00", "correlation_id": "FEAT-2026-0113", "event_type": "driver_build_pinned", "source": "driver", "source_version": "0.20.1", "payload": {"tree": "fa8269da8ced047bee31e1617c098e81f07b956c", "path": "/private/var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/specfuse-pins/fa8269da8ced047bee31e1617c098e81f07b956c/specfuse/loop"}}
+{"timestamp": "2026-09-18T01:42:04.995361+00:00", "correlation_id": "FEAT-2026-0113/T03", "event_type": "task_started", "source": "driver", "source_version": "0.20.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-18T01:44:39.659190+00:00", "correlation_id": "FEAT-2026-0113/T03", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.20.1", "payload": {"attempt": 1, "outcome": "failed", "duration_seconds": 154.589, "cost_usd": 0.8390382, "input_tokens": 52, "output_tokens": 16724, "cache_read_input_tokens": 1948261, "cache_creation_input_tokens": 69760, "model": "sonnet", "effort": "medium", "failure_class": "other", "failure_signature": "ERROR: test_triage_severity_end_to_end (unittest.loader._FailedTest.test_triage_severity_end_to_end)", "failure_excerpt": "test_failed_label_creation_is_not_raised_and_rubric_stays_usable (tests.test_severity_rubric.SeverityRubric.test_failed_label_creation_is_not_raised_and_rubric_stays_usable) ... ok\nok: no validation errors across 77 events.jsonl file(s), 2225 even\n...\nFailedTest.test_triage_severity_end_to_end)\nImportError: Failed to import test module: test_triage_severity_end_to_end\nTraceback (most recent call last):\nModuleNotFoundError: No module named 'tests.test_triage_severity_end_to_end'\nFAILED (errors=1)", "files_touched": ["tests/test_severity_rubric.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
diff --git a/specfuse/loop/labels.py b/specfuse/loop/labels.py
index 69b4bf4..709f772 100644
--- a/specfuse/loop/labels.py
+++ b/specfuse/loop/labels.py
@@ -17,7 +17,8 @@ from pathlib import Path
 from typing import Callable, Optional
 
 from specfuse.loop import (
-    bug_lane, closing_requirements, escalation, gh_features, notify_sla, triage,
+    agent_policy, bug_lane, closing_requirements, escalation, gh_features,
+    notify_sla, triage,
 )
 from specfuse.monitor import autofix_state, issues
 
@@ -217,6 +218,152 @@ def _default_runner(args: list, cwd=None, check: bool = True):
     return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)
 
 
+def _list_repo_labels(
+    target: str | Path,
+    *,
+    runner: Optional[Callable] = None,
+    repo: Optional[str] = None,
+) -> tuple[Optional[list], str]:
+    """Issue the repo's one `gh label list` call (#2081's injected-runner shape).
+
+    Returns ``(labels, "")`` on success, where *labels* is the parsed
+    ``[{"name", "color", "description"}, ...]`` list. On any failure — no
+    `gh` binary, a non-zero exit, or unparseable output — returns
+    ``(None, reason)``. Never raises; every caller of this module's `gh
+    label list` gets identical fail-soft handling by sharing this helper.
+    """
+    runner = runner if runner is not None else _default_runner
+
+    def _invoke(argv: list):
+        if repo is not None:
+            return runner(argv + ["--repo", repo], check=False)
+        return runner(argv, cwd=target, check=False)
+
+    try:
+        listed = _invoke(
+            ["gh", "label", "list", "--json", "name,color,description", "--limit", "1000"]
+        )
+    except FileNotFoundError:
+        return None, "gh binary not found on PATH"
+    except Exception as exc:  # noqa: BLE001 - never raise out of this helper
+        return None, f"gh label list raised: {exc}"
+
+    if listed.returncode != 0:
+        stderr = (getattr(listed, "stderr", "") or "").strip()
+        return None, stderr or "gh label list failed"
+
+    try:
+        existing = json.loads(listed.stdout or "[]")
+    except (ValueError, TypeError) as exc:
+        return None, f"could not parse gh label list output: {exc}"
+
+    return existing, ""
+
+
+#: One-line shipped definitions for every `agent_policy.SEVERITY_VALUES` entry,
+#: used when a repository has not defined its own `severity:*` scheme (#3352).
+DEFAULT_SEVERITY_RUBRIC: dict = {
+    "low": "Cosmetic or suboptimal; no functional impact.",
+    "medium": "Wrong behavior or a missing element; a workaround exists.",
+    "high": "Broken feature or major regression with no workaround.",
+    "critical": "Does not compile, or crashes at runtime; blocks the product.",
+}
+
+#: Colour used when provisioning the four shipped `severity:*` labels.
+_SEVERITY_LABEL_COLOUR = "5319e7"
+
+
+def _provision_default_severity_labels(
+    target: str | Path,
+    *,
+    runner: Optional[Callable] = None,
+    repo: Optional[str] = None,
+) -> list:
+    """Create the four shipped `severity:*` labels, idempotent and fail-soft.
+
+    Uses the `gh label create <name> --color --description --force` shape
+    (#3244) — distinct from `provision_labels`' own create call, which never
+    passes `--force` (#2081's registry path is left untouched). Returns the
+    names whose create call failed; never raises.
+    """
+    runner = runner if runner is not None else _default_runner
+
+    def _invoke(argv: list):
+        if repo is not None:
+            return runner(argv + ["--repo", repo], check=False)
+        return runner(argv, cwd=target, check=False)
+
+    failed: list = []
+    for value, description in DEFAULT_SEVERITY_RUBRIC.items():
+        name = f"{agent_policy.SEVERITY_LABEL_PREFIX}{value}"
+        argv = [
+            "gh", "label", "create", name,
+            "--color", _SEVERITY_LABEL_COLOUR,
+            "--description", description,
+            "--force",
+        ]
+        try:
+            created = _invoke(argv)
+        except Exception:  # noqa: BLE001 - keep provisioning remaining labels
+            failed.append(name)
+            continue
+        if getattr(created, "returncode", 1) == 0:
+            continue
+        failed.append(name)
+    return failed
+
+
+def read_severity_rubric(
+    target: str | Path,
+    *,
+    runner: Optional[Callable] = None,
+    repo: Optional[str] = None,
+) -> dict:
+    """Read the repository's severity rubric from its `severity:*` labels.
+
+    A repository that defines any `severity:*` label whose value is in
+    `agent_policy.SEVERITY_VALUES` is declaring its own scheme: the rubric is
+    built from those labels alone, one entry per value the repository
+    describes. A value described with an empty string gets the shipped
+    `DEFAULT_SEVERITY_RUBRIC` definition for that value only — every other
+    repository-authored description stands untouched.
+
+    A repository that defines **none** gets `DEFAULT_SEVERITY_RUBRIC` in full,
+    and the four labels are provisioned (fail-soft, never raised) so a later
+    `gh issue edit --add-label severity:high` has something to attach to.
+
+    Returns `{}` on any `gh label list` failure — absent binary, non-zero
+    exit, or unparseable output — rather than raising.
+    """
+    labels, error = _list_repo_labels(target, runner=runner, repo=repo)
+    if labels is None:
+        return {}
+
+    has_own_scheme = False
+    own: dict = {}
+    try:
+        for item in labels:
+            name = item.get("name", "")
+            if not name.startswith(agent_policy.SEVERITY_LABEL_PREFIX):
+                continue
+            has_own_scheme = True
+            value = name[len(agent_policy.SEVERITY_LABEL_PREFIX):]
+            if value not in agent_policy.SEVERITY_VALUES:
+                continue
+            own[value] = item.get("description") or ""
+    except (AttributeError, TypeError):
+        return {}
+
+    if not has_own_scheme:
+        _provision_default_severity_labels(target, runner=runner, repo=repo)
+        return dict(DEFAULT_SEVERITY_RUBRIC)
+
+    return {
+        value: (description if description else DEFAULT_SEVERITY_RUBRIC[value])
+        for value, description in own.items()
+    }
+
+
 def provision_labels(
     target: str | Path,
     *,
@@ -262,29 +409,15 @@ def provision_label
… (diff truncated)
--- /dev/null
+++ b/tests/test_severity_rubric.py
+# Copyright 2026 Specfuse Contributors
+# Licensed under the Apache License, Version 2.0. See LICENSE.
+"""Tests for `labels.read_severity_rubric` (FEAT-2026-0113/T03).
+
+No test invokes the real `gh` binary: every test injects a stub runner.
+"""
+
+from __future__ import annotations
+
+import json
+import unittest
+
+from specfuse.loop import agent_policy
+from specfuse.loop.labels import DEFAULT_SEVERITY_RUBRIC, read_severity_rubric
+
+
+class _Result:
+    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
+        self.returncode = returncode
+        self.stdout = stdout
+        self.stderr = stderr
+
+
+def _list_result(labels):
+    return _Result(returncode=0, stdout=json.dumps(labels))
+
+
+class _StubRunner:
+    """Records calls; returns canned results for `gh label list` / `... create`."""
+
+    def __init__(self, labels=(), create_failures=(), raise_on=None):
+        self.labels = list(labels)
+        self.create_failures = set(create_failures)
+        self.raise_on = raise_on or {}
+        self.calls: list = []
+
+    def __call__(self, args, cwd=None, check=False):
+        self.calls.append(args)
+        if args[:3] == ["gh", "label", "list"]:
+            if "list" in self.raise_on:
+                raise self.raise_on["list"]
+            return _list_result(self.labels)
+        if args[:3] == ["gh", "label", "create"]:
+            name = args[3]
+            if name in self.create_failures:
+                return _Result(returncode=1, stderr=f"failed to create {name}")
+            return _Result(returncode=0)
+        raise AssertionError(f"unexpected call: {args}")
+
+
+class SeverityRubric(unittest.TestCase):
+    def test_rubric_reads_label_descriptions(self):
+        runner = _StubRunner(
+            labels=[
+                {"name": "severity:high", "color": "b60205", "description": "Broken feature"},
+                {"name": "severity:low", "color": "0e8a16", "description": "Cosmetic"},
+            ]
+        )
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+        self.assertEqual(rubric, {"high": "Broken feature", "low": "Cosmetic"})
+
+    def test_repo_defined_severity_labels_issue_zero_create_calls(self):
+        runner = _StubRunner(
+            labels=[{"name": "severity:major", "color": "b60205", "description": "Major"}]
+        )
+        read_severity_rubric("/tmp/repo", runner=runner)
+        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
+        self.assertEqual(create_calls, [])
+
+    def test_own_label_with_recognized_value_issues_zero_create_calls(self):
+        runner = _StubRunner(
+            labels=[
+                {"name": "severity:high", "color": "b60205", "description": "Broken"},
+            ]
+        )
+        read_severity_rubric("/tmp/repo", runner=runner)
+        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
+        self.assertEqual(create_calls, [])
+
+    def test_no_severity_labels_returns_shipped_default_rubric(self):
+        runner = _StubRunner(labels=[])
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+        self.assertEqual(rubric, DEFAULT_SEVERITY_RUBRIC)
+
+    def test_no_severity_labels_provisions_the_four_labels(self):
+        runner = _StubRunner(labels=[])
+        read_severity_rubric("/tmp/repo", runner=runner)
+        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
+        created_names = {c[3] for c in create_calls}
+        expected = {
+            f"{agent_policy.SEVERITY_LABEL_PREFIX}{value}"
+            for value in agent_policy.SEVERITY_VALUES
+        }
+        self.assertEqual(created_names, expected)
+        for call in create_calls:
+            self.assertIn("--force", call)
+
+    def test_empty_description_on_a_recognized_value_gets_shipped_definition_only(self):
+        runner = _StubRunner(
+            labels=[
+                {"name": "severity:high", "color": "b60205", "description": ""},
+                {"name": "severity:low", "color": "0e8a16", "description": "Own text"},
+            ]
+        )
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+        self.assertEqual(rubric["high"], DEFAULT_SEVERITY_RUBRIC["high"])
+        self.assertEqual(rubric["low"], "Own text")
+
+    def test_failed_label_creation_is_not_raised_and_rubric_stays_usable(self):
+        runner = _StubRunner(
+            labels=[],
+            create_failures={f"{agent_policy.SEVERITY_LABEL_PREFIX}high"},
+        )
+        try:
+            rubric = read_severity_rubric("/tmp/repo", runner=runner)
+        except Exception as exc:  # noqa: BLE001 - pragma: no cover - failure path
+            self.fail(f"read_severity_rubric raised: {exc}")
+        self.assertEqual(rubric, DEFAULT_SEVERITY_RUBRIC)
+
+    def test_missing_gh_binary_returns_empty_dict(self):
+        runner = _StubRunner(raise_on={"list": FileNotFoundError("gh not found")})
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+        self.assertEqual(rubric, {})
+
+    def test_nonzero_list_exit_returns_empty_dict(self):
+        class _AuthFailRunner(_StubRunner):
+            def __call__(self, args, cwd=None, check=False):
+                self.calls.append(args)
+                if args[:3] == ["gh", "label", "list"]:
+                    return _Result(returncode=1, stderr="gh: authentication required")
+                raise AssertionError("should not reach create")
+
+        runner = _AuthFailRunner()
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+        self.assertEqual(rubric, {})
+
+    def test_unparseable_list_output_returns_empty_dict(self):
+        class _BadJsonRunner(_StubRunner):
+            def __call__(self, args, cwd=None, check=False):
+                self.calls.append(args)
+                if args[:3] == ["gh", "label", "list"]:
+                    return _Result(returncode=0, stdout="not json")
+                raise AssertionError("should not reach create")
+
+        runner = _BadJsonRunner()
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+        self.assertEqual(rubric, {})
+
+
+if __name__ == "__main__":
+    unittest.main()

```
