#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the driver-edit detection predicate (FEAT-2026-0075/T01).

`diff_edits_driver` and `driver_paths_in` are pure predicates over a list of
changed paths; `changed_paths_for_commit` is the one impure function in the
module, exercised here against a real temporary git repository.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.driver_edit import (
    DRIVER_MODULE_PREFIXES,
    changed_paths_for_commit,
    diff_edits_driver,
    driver_paths_in,
)


class TestLoopPyEditIsDetected(unittest.TestCase):
    def test_loop_py_edit_is_detected(self):
        self.assertTrue(diff_edits_driver(["specfuse/loop/loop.py"]))


class TestDiffEditsDriver(unittest.TestCase):
    def test_driver_module_prefixes_contains_loop_dir(self):
        self.assertIn("specfuse/loop/", DRIVER_MODULE_PREFIXES)

    def test_loop_py(self):
        self.assertTrue(diff_edits_driver(["specfuse/loop/loop.py"]))

    def test_arm_eval_py(self):
        self.assertTrue(diff_edits_driver(["specfuse/loop/arm_eval.py"]))

    def test_test_loop_py_is_not_driver(self):
        self.assertFalse(diff_edits_driver(["tests/test_loop.py"]))

    def test_plan_md_is_not_driver(self):
        self.assertFalse(
            diff_edits_driver([".specfuse/features/X/PLAN.md"])
        )

    def test_docs_is_not_driver(self):
        self.assertFalse(diff_edits_driver(["docs/methodology.md"]))

    def test_empty_iterable(self):
        self.assertFalse(diff_edits_driver([]))

    def test_mixed_paths_true_if_any_match(self):
        self.assertTrue(
            diff_edits_driver(["docs/methodology.md", "specfuse/loop/loop.py"])
        )


class TestDriverPathsIn(unittest.TestCase):
    def test_returns_only_matches_in_input_order(self):
        paths = [
            "docs/methodology.md",
            "specfuse/loop/loop.py",
            "tests/test_loop.py",
            "specfuse/loop/arm_eval.py",
        ]
        self.assertEqual(
            driver_paths_in(paths),
            ["specfuse/loop/loop.py", "specfuse/loop/arm_eval.py"],
        )

    def test_empty_when_no_matches(self):
        self.assertEqual(driver_paths_in(["docs/methodology.md"]), [])

    def test_empty_iterable(self):
        self.assertEqual(driver_paths_in([]), [])


class TestPurity(unittest.TestCase):
    def test_no_filesystem_or_subprocess_calls_in_predicate_sources(self):
        import inspect

        from specfuse.loop import driver_edit

        for fn in (driver_edit.diff_edits_driver, driver_edit.driver_paths_in):
            src = inspect.getsource(fn)
            body = src.split("\n", 1)[1] if "\n" in src else src
            self.assertNotRegex(
                body,
                r"open\(|Path\(|subprocess|os\.",
                f"{fn.__name__} should be pure",
            )


class TestChangedPathsForCommit(unittest.TestCase):
    def test_two_file_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            subprocess.run(
                ["git", "init"], cwd=repo_root, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "commit.gpgsign", "false"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            (repo_root / "a.txt").write_text("a\n")
            (repo_root / "b.txt").write_text("b\n")
            subprocess.run(
                ["git", "add", "a.txt", "b.txt"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "add a and b"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            paths = changed_paths_for_commit(sha, repo_root)

            self.assertEqual(sorted(paths), ["a.txt", "b.txt"])


if __name__ == "__main__":
    unittest.main()
