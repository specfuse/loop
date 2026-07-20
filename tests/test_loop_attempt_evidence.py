#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Unit tests for #168 — persist rejected-attempt evidence before git reset.

Two helpers keep a blocked WU diagnosable:

- `capture_working_tree_diff(head_before)` folds the rejected diff into a
  failing attempt's note BEFORE the per-attempt `git reset` discards it.
- `persist_attempt_notes(work_dir, wu_id, notes)` writes the buffered
  evidence to `work/<wu>/attempt-N.md`. It is now called on BOTH escalation
  paths (early spinning_signature_repeat and exhausted-attempts); previously
  only the latter wrote notes, so a signature-repeat block lost all evidence.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


@contextmanager
def _git_repo_no_sign():
    """Minimal git repo with signing disabled (operator config-independent)."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        run = lambda *a: subprocess.run(  # noqa: E731
            ["git", "-C", str(root), *a], check=True, capture_output=True,
        )
        run("init", "-q", "-b", "main")
        run("config", "commit.gpgSign", "false")
        run("config", "gc.auto", "0")
        run("config", "user.email", "test@example.com")
        run("config", "user.name", "Test")
        (root / "README.md").write_text("# fixture\n")
        run("add", ".")
        run("commit", "-q", "-m", "init")
        run("rev-parse", "HEAD")
        prev_cwd = os.getcwd()
        try:
            os.chdir(root)
            yield root
        finally:
            os.chdir(prev_cwd)


class TestCaptureWorkingTreeDiff(unittest.TestCase):

    def test_captures_tracked_modification(self):
        with _git_repo_no_sign() as root:
            head = loop.git("rev-parse", "HEAD")
            (root / "README.md").write_text("# fixture\nnew line\n")
            diff = loop.capture_working_tree_diff(head)
            self.assertIn("new line", diff)
            self.assertIn("README.md", diff)

    def test_empty_on_clean_tree(self):
        with _git_repo_no_sign():
            head = loop.git("rev-parse", "HEAD")
            self.assertEqual(loop.capture_working_tree_diff(head), "")

    def test_truncates_large_diff(self):
        with _git_repo_no_sign() as root:
            head = loop.git("rev-parse", "HEAD")
            (root / "big.txt").write_text("x\n" * 100000)
            subprocess.run(["git", "-C", str(root), "add", "big.txt"],
                           check=True, capture_output=True)
            diff = loop.capture_working_tree_diff(head, max_chars=2000)
            self.assertLessEqual(len(diff), 2000 + 64)
            self.assertIn("truncated", diff)

    def test_empty_on_bad_ref(self):
        with _git_repo_no_sign():
            # A non-existent ref makes git diff exit non-zero → "" (best-effort).
            self.assertEqual(
                loop.capture_working_tree_diff("deadbeefdeadbeef"), "")


class TestPersistAttemptNotes(unittest.TestCase):

    def test_writes_one_file_per_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            notes = [(1, "first failure"), (2, "second failure")]
            paths = loop.persist_attempt_notes(work, "FEAT-2026-0016/T03", notes)
            self.assertEqual(len(paths), 2)
            self.assertTrue((work / "FEAT-2026-0016_T03" / "attempt-1.md").exists())
            self.assertEqual(
                (work / "FEAT-2026-0016_T03" / "attempt-2.md").read_text(),
                "second failure")

    def test_wu_id_slashes_flattened(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            paths = loop.persist_attempt_notes(work, "A/B/C", [(1, "x")])
            self.assertIn("A_B_C", str(paths[0]))

    def test_empty_notes_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            paths = loop.persist_attempt_notes(work, "X/T01", [])
            self.assertEqual(paths, [])
            self.assertFalse(work.exists())


if __name__ == "__main__":
    unittest.main()
