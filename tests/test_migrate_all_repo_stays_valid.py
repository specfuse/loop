#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Feature oracle for FEAT-LOOP-2026-0248 gate 1 — `ids migrate --all` keeps a repo valid."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import agent_policy, ids
from tests.test_ids_migrate_all import _git, _make, _run

_REAL = Path(__file__).resolve().parent.parent / ".specfuse" / "agent-policy.yml"


def _policy(entry="FEAT-2026-0042"):
    lines = _REAL.read_text().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("queue:"))
    end = next(i for i, ln in enumerate(lines) if i > start and ln.startswith("rules:"))
    return "\n".join(lines[:start] + ["queue:", f"  - {entry}", ""] + lines[end:]) + "\n"


def _commit_policy(root, text=None):
    text = _policy() if text is None else text
    (root / ".specfuse" / "agent-policy.yml").write_text(text)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "policy")


class Clause1PolicyResolvesOldIds(unittest.TestCase):
    def test_queue_with_old_id_validates_after_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            _commit_policy(root)
            code, out, err = _run(root, "--apply")
            self.assertEqual(code, 0, out + err)
            self.assertTrue((root / ".specfuse" / "id-aliases.yml").is_file())
            findings = agent_policy.validate_agent_policy(
                root / ".specfuse" / "agent-policy.yml", repo_root=root
            )
            self.assertEqual([f for f in findings if f.startswith("ERROR")], [])

    def test_unknown_queue_entry_still_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            _commit_policy(root, _policy("FEAT-2026-0999"))
            _run(root, "--apply")
            findings = agent_policy.validate_agent_policy(
                root / ".specfuse" / "agent-policy.yml", repo_root=root
            )
            self.assertTrue(any("has no row in roadmap.md" in f for f in findings), findings)


class Clause2ApplyValidatesResult(unittest.TestCase):
    def test_clean_fixture_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            _commit_policy(root)
            code, out, err = _run(root, "--apply")
            self.assertEqual(code, 0, out + err)
            self.assertIn("validated", out)

    def test_lint_plan_error_exits_nonzero_with_undo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            plan = root / ".specfuse" / "features" / "FEAT-2026-0042-live" / "PLAN.md"
            plan.write_text(plan.read_text().replace("feature_id:", "feature_idx:", 1))
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "break plan")
            code, out, _ = _run(root, "--apply")
            self.assertNotEqual(code, 0)
            self.assertIn("ERROR", out)
            self.assertIn("FEAT-ACME-2026-0042-live", out)
            self.assertIn("git checkout -- . && git clean -fd .specfuse/features", out)


class Clause6ValidatesWithOwnCode(unittest.TestCase):
    """The tree's own `lint_plan` table, not the running process's, judges the result."""

    def _fixture(self, tmp):
        root = _make(tmp)
        shutil.copytree(
            _REAL.parent.parent / "specfuse", root / "specfuse",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        table = root / "specfuse" / "loop" / "lint_plan.py"
        table.write_text(table.read_text().replace(
            "DONE_FEATURE_GATE_EXCLUSIONS = {",
            'DONE_FEATURE_GATE_EXCLUSIONS = {\n    "FEAT-2026-0042-live": "fixture keeps its gate open",',
            1,
        ))
        plan = root / ".specfuse" / "features" / "FEAT-2026-0042-live" / "PLAN.md"
        plan.write_text(plan.read_text().replace("status: active", "status: done", 1))
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "own code table")
        return root

    def test_in_process_linter_would_report_stale_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            _run(root, "--apply")
            stale = ids._validate_tree_here(root)
            self.assertTrue(any("not 'passed'" in e for e in stale), stale)

    def test_apply_validates_with_the_trees_own_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            code, out, err = _run(root, "--apply")
            self.assertEqual(code, 0, out + err)
            self.assertIn("validated", out)

    def test_rehearse_validates_with_the_trees_own_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            code, out, err = _run(root, "--rehearse", "--rehearse-command", "true")
            self.assertEqual(code, 0, out + err)
            self.assertIn("migration validated", out)


class Clause3RewriteClassification(unittest.TestCase):
    def _fixture(self, tmp):
        root = _make(tmp)
        real = root / ".specfuse" / "features" / "FEAT-2026-0005-real"
        real.mkdir()
        (real / "PLAN.md").write_text("placeholder\n")
        (root / "tests").mkdir()
        (root / "tests" / "test_x.py").write_text(
            'FIX = ".specfuse/features/FEAT-2026-0005-fixture"\n'
            'BARE = "FEAT-2026-0005-fixture"\n'
            'D = {"FEAT-2026-0005-real": 1}\n'
            'P = ".specfuse/features/FEAT-2026-0005-real"\n'
        )
        roadmap = root / ".specfuse" / "roadmap.md"
        roadmap.write_text(
            roadmap.read_text().replace(
                "| FEAT-2026-0071 | Other | planned |",
                "| FEAT-2026-0005 | Real | planned |",
            ).replace("FEAT-2026-0071", "FEAT-2026-0005")
        )
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "fixture")
        return root

    def test_only_existing_folder_names_are_structural(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            code, out, err = _run(root, "--apply")
            text = (root / "tests" / "test_x.py").read_text()
            self.assertIn('".specfuse/features/FEAT-2026-0005-fixture"', text)
            self.assertIn('BARE = "FEAT-2026-0005-fixture"', text)
            self.assertIn('{"FEAT-ACME-2026-0005-real": 1}', text)
            self.assertIn('".specfuse/features/FEAT-ACME-2026-0005-real"', text)


class Clause4ProseScoping(unittest.TestCase):
    def _fixture(self, tmp):
        root = _make(tmp)
        for d in ("docs", "tests"):
            (root / d).mkdir()
            (root / d / "n.md").write_text("see FEAT-2026-0042 here\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "prose")
        return root

    def test_path_scopes_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            code, out, err = _run(root, "--apply", "--include-prose", "docs")
            self.assertEqual(code, 0, out + err)
            self.assertIn("FEAT-ACME-2026-0042", (root / "docs" / "n.md").read_text())
            self.assertIn("FEAT-2026-0042", (root / "tests" / "n.md").read_text())
            self.assertNotIn("ACME", (root / "tests" / "n.md").read_text())

    def test_bare_flag_rewrites_all_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            code, out, err = _run(root, "--apply", "--include-prose")
            self.assertEqual(code, 0, out + err)
            for d in ("docs", "tests"):
                self.assertIn("FEAT-ACME-2026-0042", (root / d / "n.md").read_text())

    def test_dry_run_counts_remaining_prose_by_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            code, out, _ = _run(root, "--include-prose", "docs")
            self.assertEqual(code, 0)
            self.assertIn("tests: 1", out)
            self.assertNotIn("docs: 1", out)

    def test_exclude_id_leaves_everything_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            code, out, err = _run(
                root, "--apply", "--include-prose", "--exclude-id", "FEAT-2026-0042"
            )
            self.assertEqual(code, 0, out + err)
            self.assertTrue((root / ".specfuse/features/FEAT-2026-0042-live").is_dir())
            self.assertIn("FEAT-2026-0042", (root / "docs" / "n.md").read_text())
            self.assertNotIn("FEAT-ACME-2026-0042", (root / ".specfuse/roadmap.md").read_text())
            aliases = (root / ".specfuse" / "id-aliases.yml").read_text()
            self.assertNotIn("FEAT-2026-0042", aliases)
            self.assertIn("FEAT-2026-0071", aliases)

    def test_exclude_id_dry_run_lists_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            _, out, _ = _run(root, "--exclude-id", "FEAT-2026-0042")
            self.assertIn("excluded by operator", out)

    def test_invalid_exclude_id_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            code, _, _ = _run(root, "--exclude-id", "nonsense")
            self.assertNotEqual(code, 0)


def _tracked_hash(root):
    import hashlib

    names = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    h = hashlib.sha256()
    for n in sorted(names):
        h.update(n.encode())
        h.update((root / n).read_bytes())
    return h.hexdigest()


def _state(root):
    def git(*a):
        return subprocess.run(
            ["git", *a], cwd=root, capture_output=True, text=True, check=True
        ).stdout

    return git("status", "--porcelain"), _tracked_hash(root), git("worktree", "list")


class Clause5Rehearse(unittest.TestCase):
    PASS = (
        "python3 -c \"import pathlib,sys; "
        "sys.exit(0 if list(pathlib.Path('.specfuse/features').glob('FEAT-ACME-2026-0042-*')) else 1)\""
    )
    FAIL = "python3 -c \"import sys; print('FAIL: test_x (m.C)'); sys.exit(1)\""

    def test_passing_command_exits_zero_and_leaves_real_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            before = _state(root)
            code, out, err = _run(root, "--rehearse", "--rehearse-command", self.PASS)
            self.assertEqual(code, 0, out + err)
            self.assertIn("exit status 0", out)
            self.assertEqual(_state(root), before)
            self.assertEqual(len(before[2].splitlines()), 1)

    def test_failing_command_exits_nonzero_and_reports_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            before = _state(root)
            code, out, err = _run(root, "--rehearse", "--rehearse-command", self.FAIL)
            self.assertNotEqual(code, 0)
            self.assertIn("FAIL: test_x (m.C)", out)
            self.assertEqual(_state(root), before)

    def test_dirty_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            roadmap = root / ".specfuse" / "roadmap.md"
            roadmap.write_text(roadmap.read_text() + "\n")
            code, _, err = _run(root, "--rehearse", "--rehearse-command", self.PASS)
            self.assertEqual(code, 2)
            self.assertIn("uncommitted", err)


if __name__ == "__main__":
    unittest.main()
