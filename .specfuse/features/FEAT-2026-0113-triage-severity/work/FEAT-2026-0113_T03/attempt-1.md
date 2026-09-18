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
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/tests-20260918T014438693465Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/lint-20260918T014438745700Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/agent-policy-example-lint-20260918T014438841969Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 77 events.jsonl file(s), 2225 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/event-type-gate-20260918T014439015022Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/roadmap-link-gate-20260918T014439061876Z.log
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
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/arm-sweep-gate-20260918T014439473253Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/monitoring-example-lint-20260918T014439532398Z.log
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
full output: .specfuse/features/FEAT-2026-0113-triage-severity/work/gate-logs/feature_oracle-20260918T014439584877Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-03-severity-rubric-reader.md b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-03-severity-rubric-reader.md
index c3ab69a..d73947d 100644
--- a/.specfuse/features/FEAT-2026-0113-triage-severity/WU-03-severity-rubric-reader.md
+++ b/.specfuse/features/FEAT-2026-0113-triage-severity/WU-03-severity-rubric-reader.md
@@ -1,12 +1,17 @@
 ---
 id: FEAT-2026-0113/T03
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 3.00
 produces:
   - specfuse/loop/labels.py
   - tests/test_severity_rubric.py
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.20.1
+started_at: 2026-09-18T01:42:04.995161+00:00
 ---
 
 # T03 — extract the label listing, and read the severity rubric from it
diff --git a/specfuse/loop/labels.py b/specfuse/loop/labels.py
index 69b4bf4..2000944 100644
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
 
@@ -201,6 +202,31 @@ LABEL_REGISTRY: tuple[LabelSpec, ...] = (
 )
 
 
+#: The published default rubric (#T03): one entry per value in
+#: `agent_policy.SEVERITY_VALUES`, used only when a repository defines no
+#: `severity:*` label of its own -- see `read_severity_rubric`.
+DEFAULT_SEVERITY_RUBRIC: dict = {
+    "low": "Cosmetic or trivial; no functional impact.",
+    "medium": "A real defect with a workaround or limited blast radius.",
+    "high": "A defect that breaks a primary workflow with no workaround.",
+    "critical": "Data loss, security exposure, or a total outage.",
+}
+
+#: Severity labels provisioned on demand, only when a repository defines no
+#: `severity:*` label of its own (#T03). Kept separate from `LABEL_REGISTRY`
+#: so no existing `provision_labels` caller starts creating these as a side
+#: effect -- see this unit's "Do not touch".
+SEVERITY_LABEL_SPECS: tuple[LabelSpec, ...] = tuple(
+    LabelSpec(
+        name=f"{agent_policy.SEVERITY_LABEL_PREFIX}{value}",
+        colour="ededed",
+        description=DEFAULT_SEVERITY_RUBRIC[value],
+        consumer="loop/agent_policy.py",
+    )
+    for value in agent_policy.SEVERITY_ORDER
+)
+
+
 @dataclass
 class ProvisionReport:
     """Outcome of a provision_labels run. Never raised; always returned."""
@@ -217,6 +243,48 @@ def _default_runner(args: list, cwd=None, check: bool = True):
     return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)
 
 
+def _list_labels(
+    target: str | Path,
+    *,
+    runner: Callable,
+    repo: Optional[str] = None,
+) -> tuple[Optional[list], str]:
+    """Issue the single `gh label list` call this module makes.
+
+    Returns ``(labels, reason)``: ``labels`` is a list of
+    ``{"name", "color", "description"}`` dicts on success, or ``None`` on any
+    failure (absent `gh`, non-zero exit, unparseable output) with ``reason``
+    describing why. Never raises -- every caller gets a report, not an
+    exception (#T03, extracted from `provision_labels`).
+    """
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
+    except Exception as exc:  # noqa: BLE001 - never raise out of _list_labels
+        return None, f"gh label list raised: {exc}"
+
+    if listed.returncode != 0:
+        stderr = (getattr(listed, "stderr", "") or "").strip()
+        return None, stderr or "gh label list failed"
+
+    try:
+        existing = json.loads(listed.stdout or "[]")
+        {item["name"] for item in existing}  # validate shape eagerly
+    except (ValueError, TypeError, KeyError) as exc:
+        return None, f"could not parse gh label list output: {exc}"
+
+    return existing, ""
+
+
 def provision_labels(
     target: str | Path,
     *,
@@ -262,32 +330,13 @@ def provision_labels(
             return runner(argv + ["--repo", repo], check=False)
         return runner(argv, cwd=target, check=False)
 
-    try:
-        listed = _invoke(
-            ["gh", "label", "list", "--json", "name,color,description", "--limit", "1000"]
-        )
-    except FileNotFoundError:
+    existing, reason = _list_labels(target, runner=runner, repo=repo)
+    if existing is None:
         report.skipped = True
-        report.reason = "gh binary not found on PATH"
-        return report
-    except Exception as exc:  # noqa: BLE001 - never raise out of provision_labels
-        report.skipped = True
-        report.reason = f"gh label list raised: {exc}"
+        report.reason = reason
         return report
 
-    if listed.returncode != 0:
-        report.skipped = True
-        stderr = (getattr(listed, "stderr", "") or "").strip()
-        report.reason = stderr or "gh label list failed"
-        return report
-
-    try:
-        existing = json.loads(listed.stdout or "[]")
-        existing_names = {item["name"] for item in existing}
-    except (ValueError, TypeError, KeyError) as exc:
-        report.skipped = True
-        report.reason = f"could not parse gh label list output: {exc}"
-        return report
+    existing_names = {item["name"] for item in existing}
 
     for spec in LABEL_REGISTRY:
         if spec.name in existing_names:
@@ -310,3 +359,69 @@ def provision_labels(
             report.failed.append(spec.name)
 
     return report
+
+
+def read_severity_rubric(
+    target: str | Path,
+    *,
+    runner: Optional[Callable] = None,
+    repo: Optional[str] = None,
+) -> dict:
+    """Read ``{severity_value: description}`` for the repo at ``target`` (#T03).
+
+    A repository that defines any ``severity:*`` label is declaring its own
+    scheme: the rubric is built from those labels alone, and a value whose
+    description is empty gets the shipped one-line definition for that value
+    only -- the rest of the repository's own descriptions stand untouched.
+
+    A repository that defines none gets the shipped `DEFAULT_SEVERITY_RUBRIC`,
+    and the four `severity:*` labels are provisioned (`gh label create ...
+    --force`, idempotent) so a later `--add-label severity:high` does not fail
+    against a label that does not exist. Provisioning failures are fail-soft:
+    the returned rubric is usable either way.
+
+    A listing failure (no `gh`, non-zero exit, unparseable output) returns
+    ``{}`` rather than raising or guessing -- same posture as
+    `provision_labels`.
+    """
+    runner = runner if runner is not None else _default_runner
+
+    existing, _reason = _list_labels(target, runner=runner, repo=repo)
+    if existing is None:
+        return {}
+
+    own: dict = {}
+    defines_any_severity_label = False
+    for item in existing:
+        name = item.get("name", "")
+        if not name.startswith(agent_policy.SEVERITY_LABEL_PREFIX):
+            continue
+        defines_any_severity_label = True
+        value = name[len(agent_policy.SEVERITY_LABEL_PREFIX):]
+        if value not in agent_policy.SEVERITY_VALUES:
+            continue
+        description = (item.get("description") or "").strip()
+        own[value] = description or DEFAULT_SEVERITY_RUBRIC[value]
+
+    if defines_any_severity_label:
+        return own
+
+    def _invoke(argv: list):
+        if repo is not None:
+            return runner(argv + ["--repo", repo], check=False)
+        return runner(argv, cwd=target, check=False)
+
+    for spec in SEVERITY_LABEL_SPECS:
+        try:
+            _invoke(
+                [
+                    "gh", "label", "create", spec.name,
+                    "--color", spec.colour,
+                    "--description", spec.description,
+                    "--force",
+                ]
+            )
+        except Exception:  # noqa: BLE001, S110 - fail-soft, rubric stays usable
+            pass
+
+    return dict(DEFAULT_SEVERITY_RUBRIC)
diff --git a/tests/test_caller_check_ratchet.py b/tests/test_caller_check_ratchet.py
index 1cf731e..6ac0eb0 100644
--- a/tests/test_caller_check_ratchet.py
+++ b/tests/test_caller_check_ratchet.py
@@ -46,6 +46,10 @@ BASELINE = {
     "list_promoted",
     "migrate_legacy",
     "ratified_after_override",
+    # Registered ahead of its consumer (FEAT-2026-0113/T03) on purpose, same
+    # as `autofix_state.AUTOFIX_FAILED_LABEL` above: `triage.py` (T04) wires
+    # the caller in a later work unit.
+    "read_severity_rubric",
     "released_section_drift",
     "stamp_release",
     "sweep_arm_predicate",
--- /dev/null
+++ b/tests/test_severity_rubric.py
+# Copyright 2026 Specfuse Contributors
+# Licensed under the Apache License, Version 2.0. See LICENSE.
+"""Tests for read_severity_rubric: repo-defined severity:* labels win; the
+shipped DEFAULT_SEVERITY_RUBRIC is the fallback, provisioned on first use.
+
+No test invokes the real gh binary: every test injects a stub runner.
+"""
+
+from __future__ import annotations
+
+import json
+import unittest
+
+from specfuse.loop import agent_policy
+from specfuse.loop.labels import (
+    DEFAULT_SEVERITY_RUBRIC,
+    SEVERITY_LABEL_SPECS,
+    read_severity_rubric,
+)
+
+
+class _Result:
+    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
+        self.returncode = returncode
+        self.stdout = stdout
+        self.stderr = stderr
+
+
+def _list_result(items):
+    return _Result(returncode=0, stdout=json.dumps(items))
+
+
+class _StubRunner:
+    """Records calls; returns canned results for `gh label list` / `gh label create`."""
+
+    def __init__(self, existing=(), create_failures=(), raise_on=None):
+        self.existing = list(existing)
+        self.create_failures = set(create_failures)
+        self.raise_on = raise_on or {}
+        self.calls: list[list] = []
+
+    def __call__(self, args, cwd=None, check=False):
+        self.calls.append(args)
+        if args[:3] == ["gh", "label", "list"]:
+            if "list" in self.raise_on:
+                raise self.raise_on["list"]
+            return _list_result(self.existing)
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
+            existing=[
+                {"name": "severity:high", "color": "b60205", "description": "Blocks release."},
+                {"name": "severity:low", "color": "0e8a16", "description": "Cosmetic only."},
+            ]
+        )
+
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+
+        self.assertEqual(
+            rubric,
+            {"high": "Blocks release.", "low": "Cosmetic only."},
+        )
+
+    def test_no_severity_labels_returns_shipped_default_rubric(self):
+        runner = _StubRunner(existing=[])
+
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+
+        self.assertEqual(rubric, DEFAULT_SEVERITY_RUBRIC)
+        self.assertEqual(set(rubric), set(agent_policy.SEVERITY_VALUES))
+
+    def test_no_severity_labels_provisions_the_four_labels(self):
+        runner = _StubRunner(existing=[])
+
+        read_severity_rubric("/tmp/repo", runner=runner)
+
+        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
+        self.assertEqual(len(create_calls), len(SEVERITY_LABEL_SPECS))
+        for call in create_calls:
+            self.assertIn("--force", call)
+
+    def test_repo_defined_severity_labels_issue_zero_create_calls(self):
+        runner = _StubRunner(
+            existing=[{"name": "severity:major", "color": "fff", "description": "d"}]
+        )
+        # `severity:major` is not in SEVERITY_VALUES, but the repo still
+        # defines *a* severity:* label, so specfuse contributes nothing.
+
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+
+        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
+        self.assertEqual(create_calls, [])
+        self.assertEqual(rubric, {})
+
+    def test_own_label_with_recognized_value_issues_zero_create_calls(self):
+        runner = _StubRunner(
+            existing=[{"name": "severity:high", "color": "fff", "description": "Ours."}]
+        )
+
+        read_severity_rubric("/tmp/repo", runner=runner)
+
+        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
+        self.assertEqual(create_calls, [])
+
+    def test_empty_description_on_a_recognized_value_gets_shipped_definition_only(self):
+        runner = _StubRunner(
+            existing=[
+                {"name": "severity:high", "color": "fff", "description": ""},
+                {"name": "severity:low", "color": "fff", "description": "Ours, kept."},
+            ]
+        )
+
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+
+        self.assertEqual(rubric["high"], DEFAULT_SEVERITY_RUBRIC["high"])
+        self.assertEqual(rubric["low"], "Ours, kept.")
+
+    def test_failed_label_creation_is_not_raised_and_rubric_stays_usable(self):
+        failing = SEVERITY_LABEL_SPECS[0].name
+        runner = _StubRunner(existing=[], create_failures={failing})
+
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+
+        self.assertEqual(rubric, DEFAULT_SEVERITY_RUBRIC)
+
+    def test_missing_gh_binary_returns_empty_dict(self):
+        runner = _StubRunner(raise_on={"list": FileNotFoundError("gh not found")})
+
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+
+        self.assertEqual(rubric, {})
+
+    def test_nonzero_list_exit_returns_empty_dict(self):
+        class _FailingListRunner(_StubRunner):
+            def __call__(self, args, cwd=None, check=False):
+                self.calls.append(args)
+                if args[:3] == ["gh", "label", "list"]:
+                    return _Result(returncode=1, stderr="gh: authentication required")
+                raise AssertionError("should not reach create")
+
+        runner = _FailingListRunner()
+
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+
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
+
+        rubric = read_severity_rubric("/tmp/repo", runner=runner)
+
+        self.assertEqual(rubric, {})
+
+
+if __name__ == "__main__":
+    unittest.main()

```
