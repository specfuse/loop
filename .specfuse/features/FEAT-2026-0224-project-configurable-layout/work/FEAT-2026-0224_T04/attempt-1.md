### tests: FAIL
```
$ python3 -m unittest tests.test_layout_no_layout_goldens tests.fixtures.layout_goldens.** tests.test_layout_end_to_end -v -b

======================================================================
ERROR: ** (unittest.loader._FailedTest.**)
----------------------------------------------------------------------
ImportError: Failed to import test module: **
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
ModuleNotFoundError: No module named 'tests.fixtures.layout_goldens.**'


----------------------------------------------------------------------
Ran 10 tests in 2.408s

FAILED (errors=1)
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/tests-20261028T004336596741Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/lint-20261028T004336725218Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/agent-policy-example-lint-20261028T004336897681Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 85 events.jsonl file(s), 2595 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/event-type-gate-20261028T004337225006Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/roadmap-link-gate-20261028T004337319832Z.log
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
evaluable=46 evaluated=46 could_not_evaluate=0 excluded_no_baseline=45
ok: 46 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/arm-sweep-gate-20261028T004338228952Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/monitoring-example-lint-20261028T004338350276Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_layout_end_to_end -v -b
test_entries (tests.test_layout_end_to_end.EntriesLayoutGet.test_entries) ... ok
test_link_cli (tests.test_layout_end_to_end.EntriesLinkRenders.test_link_cli) ... ok
test_absolute_location_exits_1_naming_path (tests.test_layout_end_to_end.InvalidLayoutIsReported.test_absolute_location_exits_1_naming_path) ... ok
test_paths_block_exits_0_with_warn (tests.test_layout_end_to_end.InvalidLayoutIsReported.test_paths_block_exits_0_with_warn) ... ok
test_defaults (tests.test_layout_end_to_end.NoLayoutGetIsToday.test_defaults) ... ok
test_non_clean_fixture (tests.test_layout_end_to_end.NoLayoutGoldens.test_non_clean_fixture) ... ok

----------------------------------------------------------------------
Ran 6 tests in 1.353s

OK
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/feature_oracle-20261028T004339825153Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-04-no-layout-goldens.md b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-04-no-layout-goldens.md
index 69e6cd8..654bfc8 100644
--- a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-04-no-layout-goldens.md
+++ b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-04-no-layout-goldens.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0224/T04
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 2.00
 produces:
   - tests/test_layout_no_layout_goldens.py
@@ -11,6 +11,8 @@ produces:
 model: sonnet
 effort: medium
 gate_set: code
+driver_version: 0.29.1
+started_at: 2026-10-28T00:42:33.252776+00:00
 ---
 
 # T04 — no-layout goldens, recorded before any consumer changes
diff --git a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl
index f302af3..10e6bc2 100644
--- a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl
@@ -7,3 +7,7 @@
 {"timestamp": "2026-10-28T00:41:57.366523+00:00", "correlation_id": "FEAT-2026-0224/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.29.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 62.847, "cost_usd": 0.24650939999999996, "input_tokens": 16, "output_tokens": 7476, "cache_read_input_tokens": 301367, "cache_creation_input_tokens": 27861, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-02-layout-validation.md", ".specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl", "specfuse/loop/layout.py", "tests/test_layout_end_to_end.py", "tests/test_layout_validation.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
 {"timestamp": "2026-10-28T00:41:57.366799+00:00", "correlation_id": "FEAT-2026-0224/T02", "event_type": "task_completed", "source": "driver", "source_version": "0.29.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 62.847, "cost_usd": 0.24650939999999996, "input_tokens": 16, "output_tokens": 7476, "cache_read_input_tokens": 301367, "cache_creation_input_tokens": 27861}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.246509, "cumulative_cost_usd": 0.246509, "attempts_lifetime": 1, "planned_cost_usd": 2.5}}
 {"timestamp": "2026-10-28T00:41:57.382732+00:00", "correlation_id": "FEAT-2026-0224", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.29.1", "payload": {"gate": 1, "wu_id": "FEAT-2026-0224/T02", "driver_paths": ["specfuse/loop/layout.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "fe2bd4b91e2e4cb04e63b61f9937985063a21010", "next_pin_tree": "040e5b63823c913fea72ac97256e3575ac20597f"}}
+{"timestamp": "2026-10-28T00:41:57.567582+00:00", "correlation_id": "FEAT-2026-0224/T03", "event_type": "task_started", "source": "driver", "source_version": "0.29.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-10-28T00:42:33.082514+00:00", "correlation_id": "FEAT-2026-0224/T03", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.29.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 35.045, "cost_usd": 0.168622, "input_tokens": 10, "output_tokens": 3858, "cache_read_input_tokens": 167550, "cache_creation_input_tokens": 24128, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-03-link-function.md", ".specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl", "specfuse/loop/layout.py", "tests/test_layout_end_to_end.py", "tests/test_layout_link.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
+{"timestamp": "2026-10-28T00:42:33.082822+00:00", "correlation_id": "FEAT-2026-0224/T03", "event_type": "task_completed", "source": "driver", "source_version": "0.29.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 35.045, "cost_usd": 0.168622, "input_tokens": 10, "output_tokens": 3858, "cache_read_input_tokens": 167550, "cache_creation_input_tokens": 24128}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.168622, "cumulative_cost_usd": 0.168622, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
+{"timestamp": "2026-10-28T00:42:33.094194+00:00", "correlation_id": "FEAT-2026-0224", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.29.1", "payload": {"gate": 1, "wu_id": "FEAT-2026-0224/T03", "driver_paths": ["specfuse/loop/layout.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "fe2bd4b91e2e4cb04e63b61f9937985063a21010", "next_pin_tree": "dd323a93d693de024f26856f5a9fc9af048a8aa7"}}
diff --git a/tests/test_layout_end_to_end.py b/tests/test_layout_end_to_end.py
index cc18ab7..4f8fe8c 100644
--- a/tests/test_layout_end_to_end.py
+++ b/tests/test_layout_end_to_end.py
@@ -79,9 +79,11 @@ class EntriesLinkRenders(unittest.TestCase):
             self.assertEqual(r.stdout.strip(), "[D-0007: x](../docs/decisions/decisions.md#D-0007)")
 
 
-@unittest.skip("owned by FEAT-2026-0224/T04")
 class NoLayoutGoldens(unittest.TestCase):
-    pass
+    def test_non_clean_fixture(self):
+        from tests.test_layout_no_layout_goldens import assert_no_layout_goldens
+
+        assert_no_layout_goldens(self, "dangling")
 
 
 @unittest.skip("owned by FEAT-2026-0224/T05")
--- /dev/null
+++ b/tests/fixtures/layout_goldens/clean/repo/.specfuse/roadmap-archive.md
+---
+project: test
+---
+
+# Archived feature details
+
+<!-- Archived sections appended below -->
--- /dev/null
+++ b/tests/fixtures/layout_goldens/clean/repo/.specfuse/roadmap.md
+---
+project: test
+---
+
+# Roadmap
+
+| Feature ID | Title | Status | Folder | Detail |
+|---|---|---|---|---|
+| FEAT-2026-0001 | Alpha | active | — | [→ detail](#feat-2026-0001) |
+
+<a id="feat-2026-0001"></a>
+## FEAT-2026-0001 — Alpha
+
+**Status: active.**
--- /dev/null
+++ b/tests/fixtures/layout_goldens/dangling/repo/.specfuse/roadmap-archive.md
+---
+project: test
+---
+
+# Archived feature details
+
+<!-- Archived sections appended below -->
--- /dev/null
+++ b/tests/fixtures/layout_goldens/dangling/repo/.specfuse/roadmap.md
+---
+project: test
+---
+
+# Roadmap
+
+| Feature ID | Title | Status | Folder | Detail |
+|---|---|---|---|---|
+| FEAT-2026-0010 | Gamma | blocked | — | [→ detail](#feat-2026-0010) |
+| FEAT-2026-0011 | Delta | active | — | — |
+
+<a id="feat-2026-0010"></a>
+## FEAT-2026-0010 — Gamma
+
+**Status: blocked.**
+
+**Blocked by.** [ADR-0099](../docs/adr/0099-does-not-exist.md) — pending.
+
+<a id="feat-2026-0011"></a>
+## FEAT-2026-0011 — Delta
+
+**Status: active.**
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/get-decisions.link.txt
+{path}
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/get-decisions.location.txt
+docs/adr
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/get-decisions.style.txt
+adr
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/link-block-feature.txt
+[ADR-0001](../docs/adr/0001-real.md)
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/lint-clean.txt
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/lint-dangling.txt
+error roadmap.md:17 FEAT-2026-0010's Blocked-by link '../docs/adr/0099-does-not-exist.md' does not resolve to a file on disk and is not a well-formed URL — fix the path
+warn roadmap.md:10 FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/lint-resolves.txt
--- /dev/null
+++ b/tests/fixtures/layout_goldens/resolves/repo/.specfuse/roadmap-archive.md
+---
+project: test
+---
+
+# Archived feature details
+
+<!-- Archived sections appended below -->
--- /dev/null
+++ b/tests/fixtures/layout_goldens/resolves/repo/.specfuse/roadmap.md
+---
+project: test
+---
+
+# Roadmap
+
+| Feature ID | Title | Status | Folder | Detail |
+|---|---|---|---|---|
+| FEAT-2026-0010 | Gamma | blocked | — | [→ detail](#feat-2026-0010) |
+
+<a id="feat-2026-0010"></a>
+## FEAT-2026-0010 — Gamma
+
+**Status: blocked.**
+
+**Blocked by.** [ADR-0001](../docs/adr/0001-real.md) — pending.
--- /dev/null
+++ b/tests/fixtures/layout_goldens/resolves/repo/docs/adr/0001-real.md
+# ADR 1
--- /dev/null
+++ b/tests/test_layout_no_layout_goldens.py
+#
+# Copyright 2026 Specfuse contributors
+# Licensed under the Apache License, Version 2.0. See LICENSE.
+#
+"""No-layout goldens for FEAT-2026-0224 (oracle clause 1).
+
+With no `layout.yml`, the layout CLI and `lint_roadmap` must keep producing the
+bytes recorded under `tests/fixtures/layout_goldens/expected/`. The goldens were
+generated once against the pre-consumer-change code; this module only compares,
+it never regenerates.
+"""
+
+import os
+import subprocess
+import sys
+import unittest
+from pathlib import Path
+
+from specfuse.loop.lint_roadmap import lint_roadmap
+
+GOLDENS = Path(__file__).resolve().parent / "fixtures" / "layout_goldens"
+EXPECTED = GOLDENS / "expected"
+FIXTURES = ("clean", "resolves", "dangling")
+KEYS = ("decisions.style", "decisions.location", "decisions.link")
+
+
+def _layout(repo, *args):
+    env = dict(os.environ)
+    root = str(Path(__file__).resolve().parent.parent)
+    env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
+    return subprocess.run(
+        [sys.executable, "-m", "specfuse.loop.layout", "--repo", str(repo), *args],
+        capture_output=True,
+        text=True,
+        env=env,
+        check=False,
+    )
+
+
+def render_findings(repo):
+    return "".join(
+        f"{f.severity} {f.file}:{f.line} {f.message}\n" for f in lint_roadmap(repo)
+    )
+
+
+def fixture_repo(name):
+    return GOLDENS / name / "repo"
+
+
+def assert_no_layout_goldens(case, name):
+    repo = fixture_repo(name)
+    case.assertFalse((repo / ".specfuse" / "layout.yml").exists())
+    for key in KEYS:
+        r = _layout(repo, "get", key)
+        case.assertEqual(r.returncode, 0, r.stderr)
+        case.assertEqual(r.stdout, (EXPECTED / f"get-{key}.txt").read_text(), key)
+    r = _layout(
+        repo, "link", "--target", "docs/adr/0001-real.md", "--label", "ADR-0001"
+    )
+    case.assertEqual(r.returncode, 0, r.stderr)
+    case.assertEqual(r.stdout, (EXPECTED / "link-block-feature.txt").read_text())
+    case.assertEqual(
+        render_findings(repo), (EXPECTED / f"lint-{name}.txt").read_text(), name
+    )
+
+
+class NoLayoutGoldens(unittest.TestCase):
+    def test_every_fixture(self):
+        for name in FIXTURES:
+            with self.subTest(fixture=name):
+                assert_no_layout_goldens(self, name)
+
+    def test_dangling_golden_has_error_and_warn(self):
+        text = (EXPECTED / "lint-dangling.txt").read_text()
+        self.assertTrue(any(ln.startswith("error ") for ln in text.splitlines()))
+        self.assertTrue(any(ln.startswith("warn ") for ln in text.splitlines()))
+
+    def test_no_fixture_link_has_fragment(self):
+        import re
+
+        for name in FIXTURES:
+            text = (fixture_repo(name) / ".specfuse" / "roadmap.md").read_text()
+            self.assertIsNone(re.search(r"\]\([^)]*\.md#", text), name)
+
+
+if __name__ == "__main__":
+    unittest.main()

```
