declared produces path(s) not in this WU's squash diff: tests/test_ids_migrate_all.py

Two escape hatches: `produces_unchanged:` — the deliverable already holds at HEAD; `produces_amended:` — the plan named a path this solution did not need.

Each listed path is a deliverable this WU declared in `produces:` but did not change. Either make the declared change this attempt, or — if the deliverable already holds at HEAD — say so in the RESULT block under `produces_unchanged:` with the command and output that show it (result-contract.md, closing obligation 1). Do not declare done while a deliverable is untouched and unjustified.

```result
produces_unchanged:
  - path: tests/test_ids_migrate_all.py
    justification: <the command you ran and its output showing the deliverable already holds>
produces_amended:
  - path: tests/test_ids_migrate_all.py
    reason: <why this WU no longer needs this produces: path>
```

A bookkeeping guard refused this attempt's pass. The previous attempt's edits are STILL PRESENT in the working tree, and verification already PASSED on them — re-authoring them is the one thing not to do. Apply only the mechanical fix below, then re-emit the RESULT block in full. Make the declared `produces:` change this attempt, or justify it as already satisfied under `produces_unchanged:` in the RESULT block, before declaring done.

Retained diff (your tree is still here):

```diff
diff --git a/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/PROGRESS.md b/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/PROGRESS.md
index 8fbd7ff..65ad2e9 100644
--- a/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/PROGRESS.md
+++ b/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/PROGRESS.md
@@ -1,3 +1,5 @@
 - **FEAT-LOOP-2026-0248/T01**: attempt 1 outcome=passed
 - **FEAT-LOOP-2026-0248/T02**: `_rewrite_line` treats `<old ID>-<slug>` as structural only when `.specfuse/features/<old ID>-<slug>` exists. This holds with or without a leading `features/`. Other `features/<ID>-…` is prose. Clause-3 test un-skipped.
 - **FEAT-LOOP-2026-0248/T02**: _rewrite_line treats <old ID>-<slug> as structural only when .specfuse/features/<old ID>-<slug> exists, with or without a leading features/. Clause-3 test un-skipped. Added test_structural_only_when_folder_exists to tests/test_ids_migrate_all.py. Narrow tests pass (15 ran, OK, 2 skipped for T03).
+- **FEAT-LOOP-2026-0248/T03**: attempt 1 outcome=passed
+- **FEAT-LOOP-2026-0248/T03**: `--include-prose` takes optional paths, `--exclude-id` is repeatable and validated, dry run ends with a per-directory prose count, and clause-4 oracle tests are un-skipped.
diff --git a/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/WU-03-scoped-prose.md b/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/WU-03-scoped-prose.md
index be0ab0b..2be1b99 100644
--- a/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/WU-03-scoped-prose.md
+++ b/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/WU-03-scoped-prose.md
@@ -1,14 +1,23 @@
 ---
 id: FEAT-LOOP-2026-0248/T03
 type: implementation
-status: pending
-attempts: 0
+status: done
+attempts: 2
 oracle_env: macos_local
 planned_cost_usd: 2.00
 produces:
   - specfuse/loop/ids.py
   - tests/test_ids_migrate_all.py
   - tests/test_migrate_all_repo_stays_valid.py
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.30.0
+started_at: 2026-10-29T15:14:29.643382+00:00
+duration_seconds: 88.399
+cost_usd: 0.376264
+input_tokens: 24
+output_tokens: 6469
 ---
 
 # T03 — `--include-prose` takes paths; `--exclude-id` protects shared numbers
diff --git a/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/events.jsonl b/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/events.jsonl
index 5ebcc56..f67732f 100644
--- a/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/events.jsonl
+++ b/.specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/events.jsonl
@@ -3,3 +3,8 @@
 {"timestamp": "2026-10-29T15:13:15.708903+00:00", "correlation_id": "FEAT-LOOP-2026-0248/T01", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.30.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 57.562, "cost_usd": 0.39702879999999996, "input_tokens": 24, "output_tokens": 6897, "cache_read_input_tokens": 631014, "cache_creation_input_tokens": 50452, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/WU-01-policy-resolves-and-apply-validates.md", "specfuse/loop/agent_policy.py", "specfuse/loop/ids.py", "tests/test_migrate_all_repo_stays_valid.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
 {"timestamp": "2026-10-29T15:13:15.709096+00:00", "correlation_id": "FEAT-LOOP-2026-0248/T01", "event_type": "task_completed", "source": "driver", "source_version": "0.30.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 57.562, "cost_usd": 0.39702879999999996, "input_tokens": 24, "output_tokens": 6897, "cache_read_input_tokens": 631014, "cache_creation_input_tokens": 50452}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.397029, "cumulative_cost_usd": 0.397029, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
 {"timestamp": "2026-10-29T15:13:15.716467+00:00", "correlation_id": "FEAT-LOOP-2026-0248", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.30.0", "payload": {"gate": 1, "wu_id": "FEAT-LOOP-2026-0248/T01", "driver_paths": ["specfuse/loop/agent_policy.py", "specfuse/loop/ids.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "e97183eb79f76aedcc0d02efb81434e915caf4e6", "next_pin_tree": "793dd460832390cf8a7ebda37f3fecbad7f07fe3"}}
+{"timestamp": "2026-10-29T15:13:15.821119+00:00", "correlation_id": "FEAT-LOOP-2026-0248/T02", "event_type": "task_started", "source": "driver", "source_version": "0.30.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-10-29T15:13:53.103643+00:00", "correlation_id": "FEAT-LOOP-2026-0248/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.30.0", "payload": {"attempt": 1, "outcome": "produces_not_in_diff", "duration_seconds": 36.995, "cost_usd": 0.1896408, "input_tokens": 12, "output_tokens": 3449, "cache_read_input_tokens": 217814, "cache_creation_input_tokens": 27891, "model": "sonnet", "effort": "medium", "failure_class": "produces_not_in_diff", "failure_signature": "test_ids_migrate_all.py", "failure_excerpt": "declared produces path(s) not in this WU's squash diff: tests/test_ids_migrate_all.py\n\nTwo escape hatches: `produces_unchanged:` \u2014 the deliverable already holds at HEAD; `produces_amended:` \u2014 the plan named a path this solution did not need.\n\n\n...\n tests/test_ids_migrate_all.py\n    justification: <the command you ran and its output showing the deliverable already holds>\nproduces_amended:\n  - path: tests/test_ids_migrate_all.py\n    reason: <why this WU no longer needs this produces: path>\n```", "files_touched": [".specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/WU-02-structural-means-a-real-folder.md", ".specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/events.jsonl", "specfuse/loop/ids.py", "tests/test_migrate_all_repo_stays_valid.py"], "agent_status": null, "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": [], "summary": "declared produces path(s) not in this WU's squash diff: tests/test_ids_migrate_all.py", "tree_retained": true}}
+{"timestamp": "2026-10-29T15:14:29.537134+00:00", "correlation_id": "FEAT-LOOP-2026-0248/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.30.0", "payload": {"attempt": 2, "outcome": "passed", "duration_seconds": 36.169, "cost_usd": 0.1461498, "input_tokens": 10, "output_tokens": 1442, "cache_read_input_tokens": 174189, "cache_creation_input_tokens": 24218, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/WU-02-structural-means-a-real-folder.md", ".specfuse/features/FEAT-LOOP-2026-0248-rekey-all-safe/events.jsonl", "specfuse/loop/ids.py", "tests/test_ids_migrate_all.py", "tests/test_migrate_all_repo_stays_valid.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
+{"timestamp": "2026-10-29T15:14:29.537320+00:00", "correlation_id": "FEAT-LOOP-2026-0248/T02", "event_type": "task_completed", "source": "driver", "source_version": "0.30.0", "payload": {"attempts": 2, "attempts_usage": [{"attempt": 1, "duration_seconds": 36.995, "cost_usd": 0.1896408, "input_tokens": 12, "output_tokens": 3449, "cache_read_input_tokens": 217814, "cache_creation_input_tokens": 27891}, {"attempt": 2, "duration_seconds": 36.169, "cost_usd": 0.1461498, "input_tokens": 10, "output_tokens": 1442, "cache_read_input_tokens": 174189, "cache_creation_input_tokens": 24218}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.335791, "cumulative_cost_usd": 0.335791, "attempts_lifetime": 2, "planned_cost_usd": 2.5}}
+{"timestamp": "2026-10-29T15:14:29.544253+00:00", "correlation_id": "FEAT-LOOP-2026-0248", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.30.0", "payload": {"gate": 1, "wu_id": "FEAT-LOOP-2026-0248/T02", "driver_paths": ["specfuse/loop/ids.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "e97183eb79f76aedcc0d02efb81434e915caf4e6", "next_pin_tree": "82b7c815bc427d7db4625320118345dc08a60a1f"}}
diff --git a/specfuse/loop/ids.py b/specfuse/loop/ids.py
index fa3bfa9..a88d827 100644
--- a/specfuse/loop/ids.py
+++ b/specfuse/loop/ids.py
@@ -13,12 +13,14 @@ Standalone like `layout.py`: must not import the driver.
 
     python3 -m specfuse.loop.ids [--repo DIR] next [--year YYYY]
     python3 -m specfuse.loop.ids [--repo DIR] migrate --planned-only [--apply]
-    python3 -m specfuse.loop.ids [--repo DIR] migrate --all [--apply] [--include-prose]
+    python3 -m specfuse.loop.ids [--repo DIR] migrate --all [--apply]
+        [--include-prose [PATH ...]] [--exclude-id ID ...]
 """
 
 from __future__ import annotations
 
 import argparse
+import fnmatch
 import datetime
 import re
 import subprocess
@@ -279,7 +281,7 @@ def _tracked_text_files(root: Path):
             continue
 
 
-def _own_unkeyed_ids(root: Path, key: str):
+def _own_unkeyed_ids(root: Path, key: str, exclude=()):
     """(renames, skipped): unkeyed IDs with a feature folder or a roadmap row."""
     found = {}
     features = root / ".specfuse" / "features"
@@ -299,7 +301,9 @@ def _own_unkeyed_ids(root: Path, key: str):
         if parsed.key:
             continue
         new = str(FeatureId(key, parsed.year, parsed.ordinal))
-        if new in existing:
+        if fid in exclude:
+            skipped.append((fid, "excluded by operator"))
+        elif new in existing:
             skipped.append((fid, "keyed ID already exists"))
         else:
             renames.append((fid, new))
@@ -422,16 +426,29 @@ def _rewrite_file(rel, text, renames, include_prose, plan, folders=()):
     return "".join(out)
 
 
-def plan_migrate_all(root, key: str, include_prose: bool = False) -> AllPlan:
+def _prose_in(rel: str, include_prose) -> bool:
+    """True when prose in *rel* is rewritten: all files (True) or matching paths/globs."""
+    if isinstance(include_prose, (list, tuple)):
+        return any(
+            fnmatch.fnmatchcase(rel, pat) or rel.startswith(pat.rstrip("/") + "/")
+            for pat in include_prose
+        )
+    return bool(include_prose)
+
+
+def plan_migrate_all(root, key: str, include_prose=False, exclude=()) -> AllPlan:
+    """*include_prose*: False (none), True (all files) or a list of paths/globs."""
     root = Path(root)
-    renames, skipped = _own_unkeyed_ids(root, key)
+    renames, skipped = _own_unkeyed_ids(root, key, set(exclude))
     plan = AllPlan(renames, skipped, [], {}, {}, [], [])
     if not renames:
         return plan
     features = root / ".specfuse" / "features"
     folders = sorted(p.name for p in features.iterdir() if p.is_dir()) if features.is_dir() else []
     for rel, text in _tracked_text_files(root):
-        new_text = _rewrite_file(rel, text, renames, include_prose, plan, folders)
+        new_text = _rewrite_file(
+            rel, text, renames, _prose_in(rel, include_prose), plan, folders
+        )
         if new_text != text:
             plan.files[rel] = new_text
     if features.is_dir():
@@ -523,7 +540,9 @@ def _append_aliases(root: Path, renames) -> None:
         path.write_text(existing + add, encoding="utf-8")
 
 
-def migrate_all(repo_root, apply: bool = False, include_prose: bool = False, out=None) -> int:
+def migrate_all(
+    repo_root, apply: bool = False, include_prose=False, out=None, exclude=()
+) -> int:
     from specfuse.loop import layout
 
     out = out or sys.stdout
@@ -548,7 +567,7 @@ def migrate_all(repo_root, apply: bool = False, include_prose: bool = False, out
             )
             return 2
     try:
-        plan = plan_migrate_all(root, key, include_prose)
+        plan = plan_migrate_all(root, key, include_prose, exclude)
         print(f"{'apply' if apply else 'dry run'}: key {key}", file=out)
         for old, new in plan.renames:
             print(f"  rekey  {old} -> {new}", file=out)
@@ -567,6 +586,13 @@ def migrate_all(repo_root, apply: bool = False, include_prose: bool = False, out
                 f"{'left unchanged' if apply else 'rewritten only with --include-prose'})",
                 file=out,
             )
+        if plan.ambiguous and not apply:
+            by_dir = {}
+            for rel, _no, _old in plan.ambiguous:
+                top = rel.split("/", 1)[0] if "/" in rel else "."
+                by_dir[top] = by_dir.get(top, 0) + 1
+            summary = ", ".join(f"{d}: {n}" for d, n in sorted(by_dir.items()))
+            print(f"  prose mentions remaining by top-level directory: {summary}", file=out)
         if not plan.renames:
             print("nothing to do", file=out)
             return 0
@@ -619,17 +645,30 @@ def main(argv=None) -> int:
     which.add_argument("--all", action="store_true", help="re-key every feature of this repository")
     mig.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
     mig.add_argument(
-        "--include-prose", action="store_true",
-        help="with --all --apply, also rewrite ambiguous prose mentions",
+        "--include-prose", nargs="*", default=None, metavar="PATH",
+        help="with --all, also rewrite prose mentions: in all files when bare, "
+        "else only in files matching the given paths or globs",
+    )
+    mig.add_argument(
+        "--exclude-id", action="append", default=[], metavar="ID",
+        help="with --all, leave this old ID untouched everywhere (repeatable)",
     )
     args = parser.parse_args(argv)
     if args.command == "next":
         print(next_id(args.repo, args.year))
     elif args.command == "migrate":
         if args.all:
-            return migrate_all(args.repo, apply=args.apply, include_prose=args.include_prose)
-        if args.include_prose:
+            for value in args.exclude_id:
+                if not FEATURE_ID_RE.match(value):
+                    parser.error(f"--exclude-id: {value!r} is not a feature ID")
+            prose = False if args.include_prose is None else (args.include_prose or True)
+            return migrate_all(
+                args.repo, apply=args.apply, include_prose=prose, exclude=args.exclude_id
+            )
+        if args.include_prose is not None:
             parser.error("--include-prose requires --all")
+        if args.exclude_id:
+            parser.error("--exclude-id requires --all")
         return migrate(args.repo, apply=args.apply)
     return 0
 
diff --git a/tests/test_migrate_all_repo_stays_valid.py b/tests/test_migrate_all_repo_stays_valid.py
index 914d8b3..d129186 100644
--- a/tests/test_migrate_all_repo_stays_valid.py
+++ b/tests/test_migrate_all_repo_stays_valid.py
@@ -110,10 +110,62 @@ class Clause3RewriteClassification(unittest.TestCase):
             self.assertIn('".specfuse/features/FEAT-ACME-2026-0005-real"', text)
 
 
-@unittest.skip("T03 owns prose scoping")
 class Clause4ProseScoping(unittest.TestCase):
-    def test_pending(self):
-        pass
+    def _fixture(self, tmp):
+        root = _make(tmp)
+        for d in ("docs", "tests"):
+            (root / d).mkdir()
+            (root / d / "note.md").write_text(f"{d} cites FEAT-2026-0042 here.\n")
+        _git(root, "add", "-A")
+        _git(root, "commit", "-q", "-m", "prose")
+        return root
+
+    def test_include_prose_path_scopes_rewrite(self):
+        with tempfile.TemporaryDirectory() as tmp:
+            root = self._fixture(tmp)
+            code, out, err = _run(root, "--apply", "--include-prose", "docs")
+            self.assertEqual(code, 0, out + err)
+            self.assertIn("FEAT-ACME-2026-0042", (root / "docs" / "note.md").read_text())
+            self.assertIn("FEAT-2026-0042 here", (root / "tests" / "note.md").read_text())
+
+    def test_bare_include_prose_rewrites_both(self):
+        with tempfile.TemporaryDirectory() as tmp:
+            root = self._fixture(tmp)
+            code, out, err = _run(root, "--apply", "--include-prose")
+            self.assertEqual(code, 0, out + err)
+            for d in ("docs", "tests"):
+                self.assertIn("FEAT-ACME-2026-0042", (root / d / "note.md").read_text())
+
+    def test_dry_run_sizes_remaining_prose_by_directory(self):
+        with tempfile.TemporaryDirectory() as tmp:
+            root = self._fixture(tmp)
+            code, out, err = _run(root, "--include-prose", "docs")
+            self.assertEqual(code, 0, out + err)
+            self.assertIn("tests: 1", out)
+            self.assertNotIn("docs: 1", out)
+
+    def test_exclude_id_leaves_everything_untouched(self):
+        with tempfile.TemporaryDirectory() as tmp:
+            root = self._fixture(tmp)
+            code, out, err = _run(
+                root, "--apply", "--include-prose", "--exclude-id", "FEAT-2026-0042"
+            )
+            self.assertEqual(code, 0, out + err)
+            self.assertIn("excluded by operator", out)
+            spec = root / ".specfuse"
+            self.assertTrue((spec / "features" / "FEAT-2026-0042-live").is_dir())
+            self.assertIn("| FEAT-2026-0042 |", (spec / "roadmap.md").read_text())
+            self.assertIn("FEAT-2026-0042 here", (root / "docs" / "note.md").read_text())
+            aliases = (spec / "id-aliases.yml").read_text()
+            self.assertNotIn("FEAT-2026-0042", aliases)
+            self.assertIn("FEAT-2026-0071", aliases)
+
+    def test_invalid_exclude_id_exits_nonzero(self):
+        with tempfile.TemporaryDirectory() as tmp:
+            root = self._fixture(tmp)
+            with self.assertRaises(SystemExit) as cm:
+                _run(root, "--exclude-id", "nope")
+            self.assertNotEqual(cm.exception.code, 0)
 
 
 @unittest.skip("T04 owns --rehearse")

```
