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
Ran 12 tests in 3.267s

FAILED (errors=1)
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/tests-20261028T005255716400Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/lint-20261028T005255952057Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/agent-policy-example-lint-20261028T005256154373Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 85 events.jsonl file(s), 2597 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/event-type-gate-20261028T005256737553Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/roadmap-link-gate-20261028T005256818800Z.log
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
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/arm-sweep-gate-20261028T005258171531Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/monitoring-example-lint-20261028T005258289531Z.log
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
Ran 6 tests in 1.047s

OK
full output: .specfuse/features/FEAT-2026-0224-project-configurable-layout/work/gate-logs/feature_oracle-20261028T005259460922Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/GATE-01.md b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/GATE-01.md
index c2153f8..0aab281 100644
--- a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/GATE-01.md
+++ b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/GATE-01.md
@@ -3,6 +3,13 @@ gate: 1
 status: open
 feature_oracle: "python3 -m unittest tests.test_layout_end_to_end -v -b"
 cost_budget_usd: 26.00
+baseline:
+  sha: f9a6840c4d01a00c8d955b70caedf2b090ce56e0
+  probed_at: 2026-10-28T00:43:40.283505+00:00
+  tree: 054923b0bea95ba720a9a42a693f4da9e9ea960f:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:1fea2572bb182d4233b903d016587fe6aeb4b58a:243d8e82854c7b3f2eebefd227ea009bf7a342ea:27968248a450a842ccd187b7dce0fb0ded934866:4acc6dfc5e8cece358c167d876515eba4a39a500:56bb22809af19d9fe40ed1755749bbb055c02a2a:5ff66b6e4d8a264f23709ea60706111a4c59ed11:61870de6daffa7805d95dacfc69772c1b19f3f8b:73c4d26fbe049c6b96d135925660ea06bff57a3b:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:c62635fbdf4ae125576060093c34caeaca4342e0:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:fa2f4f88657587b6e3b560977858810846b1d366
+  entry_sha: f9a6840c4d01a00c8d955b70caedf2b090ce56e0
+  source: attributed:FEAT-2026-0224/T04
+  failing: []
 ---
 
 # Gate 1 — a project can declare its decision records, and nothing changes without one
diff --git a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-04-no-layout-goldens.md b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-04-no-layout-goldens.md
index 69e6cd8..62fb8d2 100644
--- a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-04-no-layout-goldens.md
+++ b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-04-no-layout-goldens.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0224/T04
 type: implementation
 status: pending
-attempts: 0
+attempts: 2
 planned_cost_usd: 2.00
 produces:
   - tests/test_layout_no_layout_goldens.py
diff --git a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl
index f302af3..0b6a476 100644
--- a/.specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl
@@ -7,3 +7,9 @@
 {"timestamp": "2026-10-28T00:41:57.366523+00:00", "correlation_id": "FEAT-2026-0224/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.29.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 62.847, "cost_usd": 0.24650939999999996, "input_tokens": 16, "output_tokens": 7476, "cache_read_input_tokens": 301367, "cache_creation_input_tokens": 27861, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-02-layout-validation.md", ".specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl", "specfuse/loop/layout.py", "tests/test_layout_end_to_end.py", "tests/test_layout_validation.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
 {"timestamp": "2026-10-28T00:41:57.366799+00:00", "correlation_id": "FEAT-2026-0224/T02", "event_type": "task_completed", "source": "driver", "source_version": "0.29.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 62.847, "cost_usd": 0.24650939999999996, "input_tokens": 16, "output_tokens": 7476, "cache_read_input_tokens": 301367, "cache_creation_input_tokens": 27861}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.246509, "cumulative_cost_usd": 0.246509, "attempts_lifetime": 1, "planned_cost_usd": 2.5}}
 {"timestamp": "2026-10-28T00:41:57.382732+00:00", "correlation_id": "FEAT-2026-0224", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.29.1", "payload": {"gate": 1, "wu_id": "FEAT-2026-0224/T02", "driver_paths": ["specfuse/loop/layout.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "fe2bd4b91e2e4cb04e63b61f9937985063a21010", "next_pin_tree": "040e5b63823c913fea72ac97256e3575ac20597f"}}
+{"timestamp": "2026-10-28T00:41:57.567582+00:00", "correlation_id": "FEAT-2026-0224/T03", "event_type": "task_started", "source": "driver", "source_version": "0.29.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-10-28T00:42:33.082514+00:00", "correlation_id": "FEAT-2026-0224/T03", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.29.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 35.045, "cost_usd": 0.168622, "input_tokens": 10, "output_tokens": 3858, "cache_read_input_tokens": 167550, "cache_creation_input_tokens": 24128, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0224-project-configurable-layout/WU-03-link-function.md", ".specfuse/features/FEAT-2026-0224-project-configurable-layout/events.jsonl", "specfuse/loop/layout.py", "tests/test_layout_end_to_end.py", "tests/test_layout_link.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
+{"timestamp": "2026-10-28T00:42:33.082822+00:00", "correlation_id": "FEAT-2026-0224/T03", "event_type": "task_completed", "source": "driver", "source_version": "0.29.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 35.045, "cost_usd": 0.168622, "input_tokens": 10, "output_tokens": 3858, "cache_read_input_tokens": 167550, "cache_creation_input_tokens": 24128}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.168622, "cumulative_cost_usd": 0.168622, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
+{"timestamp": "2026-10-28T00:42:33.094194+00:00", "correlation_id": "FEAT-2026-0224", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.29.1", "payload": {"gate": 1, "wu_id": "FEAT-2026-0224/T03", "driver_paths": ["specfuse/loop/layout.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "fe2bd4b91e2e4cb04e63b61f9937985063a21010", "next_pin_tree": "dd323a93d693de024f26856f5a9fc9af048a8aa7"}}
+{"timestamp": "2026-10-28T00:42:33.252996+00:00", "correlation_id": "FEAT-2026-0224/T04", "event_type": "task_started", "source": "driver", "source_version": "0.29.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-10-28T00:43:40.004875+00:00", "correlation_id": "FEAT-2026-0224/T04", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.29.1", "payload": {"attempt": 1, "outcome": "failed", "duration_seconds": 66.572, "cost_usd": 0.3133744, "input_tokens": 22, "output_tokens": 6029, "cache_read_input_tokens": 493622, "cache_creation_input_tokens": 38579, "model": "sonnet", "effort": "medium", "failure_class": "tests", "failure_signature": "(errors=1)", "failure_excerpt": "### tests: FAIL\nERROR: ** (unittest.loader._FailedTest.**)\nImportError: Failed to import test module: **\nTraceback (most recent call last):\nModuleNotFoundError: No module named 'tests.fixtures.layout_goldens.**'\nFAILED (errors=1)\nok: no validation\n...\nve.md link graph \u2014 0 error(s), 1 warning(s)\nNO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output \u2014 the lines above are the tail only, and may be unrelated to the failure. Run the command directly.", "files_touched": ["tests/fixtures/layout_goldens/clean/repo/.specfuse/roadmap-archive.md", "tests/fixtures/layout_goldens/clean/repo/.specfuse/roadmap.md", "tests/fixtures/layout_goldens/dangling/repo/.specfuse/roadmap-archive.md", "tests/fixtures/layout_goldens/dangling/repo/.specfuse/roadmap.md", "tests/fixtures/layout_goldens/expected/get-decisions.link.txt", "tests/fixtures/layout_goldens/expected/get-decisions.location.txt", "tests/fixtures/layout_goldens/expected/get-decisions.style.txt", "tests/fixtures/layout_goldens/expected/link-block-feature.txt", "tests/fixtures/layout_goldens/expected/lint-clean.txt", "tests/fixtures/layout_goldens/expected/lint-dangling.txt", "tests/fixtures/layout_goldens/expected/lint-resolves.txt", "tests/fixtures/layout_goldens/resolves/repo/.specfuse/roadmap-archive.md", "tests/fixtures/layout_goldens/resolves/repo/.specfuse/roadmap.md", "tests/fixtures/layout_goldens/resolves/repo/docs/adr/0001-real.md", "tests/test_layout_no_layout_goldens.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": ["(errors=1)"]}}
diff --git a/tests/test_layout_end_to_end.py b/tests/test_layout_end_to_end.py
index cc18ab7..313345c 100644
--- a/tests/test_layout_end_to_end.py
+++ b/tests/test_layout_end_to_end.py
@@ -79,9 +79,19 @@ class EntriesLinkRenders(unittest.TestCase):
             self.assertEqual(r.stdout.strip(), "[D-0007: x](../docs/decisions/decisions.md#D-0007)")
 
 
-@unittest.skip("owned by FEAT-2026-0224/T04")
 class NoLayoutGoldens(unittest.TestCase):
-    pass
+    def test_non_clean_fixture(self):
+        from tests import test_layout_no_layout_goldens as g
+
+        repo = g.GOLDENS / "dangling" / "repo"
+        self.assertEqual(
+            g.render_findings(repo), (g.EXPECTED / "lint-dangling.txt").read_text()
+        )
+        for key in g.KEYS:
+            r = run_layout(repo, "get", key)
+            self.assertEqual(r.stdout, (g.EXPECTED / f"get-{key}.txt").read_text())
+        r = run_layout(repo, *g.LINK_ARGS)
+        self.assertEqual(r.stdout, (g.EXPECTED / "link-block-feature.txt").read_text())
 
 
 @unittest.skip("owned by FEAT-2026-0224/T05")
--- /dev/null
+++ b/tests/fixtures/layout_goldens/clean/repo/.specfuse/roadmap-archive.md
+# Roadmap archive
--- /dev/null
+++ b/tests/fixtures/layout_goldens/clean/repo/.specfuse/roadmap.md
+---
+project: acme-widget
+---
+
+# Roadmap
+
+| Feature ID     | Title | Status | Folder | Detail |
+|----------------|-------|--------|--------|--------|
+| FEAT-2026-0002 | Widget polish | planned | — | [→ detail](#feat-2026-0002) |
+
+<a id="feat-2026-0002"></a>
+## FEAT-2026-0002 — Widget polish
+
+**Status: planned.** Polish the widget.
--- /dev/null
+++ b/tests/fixtures/layout_goldens/dangling/repo/.specfuse/roadmap-archive.md
+# Roadmap archive
--- /dev/null
+++ b/tests/fixtures/layout_goldens/dangling/repo/.specfuse/roadmap.md
+---
+project: acme-widget
+---
+
+# Roadmap
+
+| Feature ID     | Title | Status | Folder | Detail |
+|----------------|-------|--------|--------|--------|
+| FEAT-2026-0004 | Widget import | blocked | — | [→ detail](#feat-2026-0004) |
+| FEAT-2026-0005 | Widget audit | planned | — | — |
+
+<a id="feat-2026-0004"></a>
+## FEAT-2026-0004 — Widget import
+
+**Status: blocked.**
+
+**Blocked by.** [ADR-0009: import format](../docs/adr/0009-import-format.md) — awaiting approval.
+
+<a id="feat-2026-0005"></a>
+## FEAT-2026-0005 — Widget audit
+
+**Status: planned.**
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
+[ADR-0007: event-schema versioning](../docs/adr/0007-event-schema-versioning.md)
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/lint-clean.txt
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/lint-dangling.txt
+error roadmap.md:17 FEAT-2026-0004's Blocked-by link '../docs/adr/0009-import-format.md' does not resolve to a file on disk and is not a well-formed URL — fix the path
+warn roadmap.md:10 FEAT-2026-0005's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0005)' or '[→ archive](roadmap-archive.md#feat-2026-0005)'
--- /dev/null
+++ b/tests/fixtures/layout_goldens/expected/lint-resolves.txt
--- /dev/null
+++ b/tests/fixtures/layout_goldens/resolves/repo/.specfuse/roadmap-archive.md
+# Roadmap archive
--- /dev/null
+++ b/tests/fixtures/layout_goldens/resolves/repo/.specfuse/roadmap.md
+---
+project: acme-widget
+---
+
+# Roadmap
+
+| Feature ID     | Title | Status | Folder | Detail |
+|----------------|-------|--------|--------|--------|
+| FEAT-2026-0003 | Widget export | blocked | — | [→ detail](#feat-2026-0003) |
+
+<a id="feat-2026-0003"></a>
+## FEAT-2026-0003 — Widget export
+
+**Status: blocked.**
+
+**Blocked by.** [ADR-0007: event-schema versioning](../docs/adr/0007-event-schema-versioning.md) — awaiting approval.
--- /dev/null
+++ b/tests/fixtures/layout_goldens/resolves/repo/docs/adr/0007-event-schema-versioning.md
+# ADR-0007: event-schema versioning
--- /dev/null
+++ b/tests/test_layout_no_layout_goldens.py
+#
+# Copyright 2026 Specfuse contributors
+# Licensed under the Apache License, Version 2.0. See LICENSE.
+#
+"""FEAT-2026-0224/T04: with no `layout.yml`, output equals the committed goldens.
+
+Goldens under `tests/fixtures/layout_goldens/expected/` were recorded once from
+HEAD before any consumer edit; this module only reads them, never writes them.
+"""
+
+import unittest
+from pathlib import Path
+
+from specfuse.loop.layout import KEYS
+from specfuse.loop.lint_roadmap import lint_roadmap
+from tests.test_layout_end_to_end import run_layout
+
+GOLDENS = Path(__file__).resolve().parent / "fixtures" / "layout_goldens"
+EXPECTED = GOLDENS / "expected"
+FIXTURES = ("clean", "resolves", "dangling")
+LINK_ARGS = (
+    "link",
+    "--target", "docs/adr/0007-event-schema-versioning.md",
+    "--label", "ADR-0007: event-schema versioning",
+)
+
+
+def render_findings(repo):
+    return "".join(
+        f"{f.severity} {f.file}:{f.line} {f.message}\n" for f in lint_roadmap(repo)
+    )
+
+
+class NoLayoutGoldens(unittest.TestCase):
+    def test_fixtures_have_no_layout_yml(self):
+        for name in FIXTURES:
+            self.assertFalse((GOLDENS / name / "repo" / ".specfuse" / "layout.yml").exists())
+
+    def test_get_every_key(self):
+        repo = GOLDENS / "clean" / "repo"
+        for key in KEYS:
+            with self.subTest(key=key):
+                r = run_layout(repo, "get", key)
+                self.assertEqual(r.returncode, 0, r.stderr)
+                self.assertEqual(r.stdout, (EXPECTED / f"get-{key}.txt").read_text())
+
+    def test_link_block_feature_example(self):
+        r = run_layout(GOLDENS / "clean" / "repo", *LINK_ARGS)
+        self.assertEqual(r.returncode, 0, r.stderr)
+        self.assertEqual(r.stdout, (EXPECTED / "link-block-feature.txt").read_text())
+
+    def test_lint_roadmap_findings(self):
+        for name in FIXTURES:
+            with self.subTest(fixture=name):
+                self.assertEqual(
+                    render_findings(GOLDENS / name / "repo"),
+                    (EXPECTED / f"lint-{name}.txt").read_text(),
+                )
+
+    def test_dangling_golden_has_error_and_warn(self):
+        lines = (EXPECTED / "lint-dangling.txt").read_text().splitlines()
+        self.assertTrue(any(line.startswith("error ") for line in lines))
+        self.assertTrue(any(line.startswith("warn ") for line in lines))
+
+
+if __name__ == "__main__":
+    unittest.main()

```
