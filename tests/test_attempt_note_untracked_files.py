#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""An attempt note records files the attempt CREATED, not only ones it changed (#3249).

`capture_working_tree_diff` folds `git diff <head_before>` into a failing
attempt's evidence note before the per-attempt `git reset --hard` discards the
work. `git diff` only sees tracked content, so a file that did not exist at
`head_before` has nothing to diff against and never reaches the note.

That is not a theoretical gap. FEAT-2026-0100/T03 spun twice on 2026-09-06
against six failures in `tests/test_verify_empty_gate_set.py`; the note carried
diffs for the WU file, `events.jsonl` and `loop.py`, and the one file that
explained the failure — the new test module, patching `loop.verify` without
restoring it — was absent. The operator had to guess, which is what
`/gate-status` ended up doing.

Same lesson `verify_files_changed` already learned for its own purpose (#3119):
`git diff` is not a complete account of what an attempt did.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout


class TestAttemptNoteRecordsUntrackedFiles(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _git("init", "-q", cwd=self.repo)
        _git("config", "user.email", "t@example.com", cwd=self.repo)
        _git("config", "user.name", "t", cwd=self.repo)
        (self.repo / "tracked.py").write_text("original\n")
        (self.repo / ".gitignore").write_text("work/\n")
        _git("add", "-A", cwd=self.repo)
        _git("commit", "-qm", "base", cwd=self.repo)
        self.head_before = _git("rev-parse", "HEAD", cwd=self.repo).strip()
        self._cwd = os.getcwd()
        os.chdir(self.repo)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_a_created_file_reaches_the_note(self):
        # The FEAT-2026-0100/T03 shape: the attempt edits one tracked file and
        # creates the test module that actually breaks the suite.
        (self.repo / "tracked.py").write_text("edited\n")
        (self.repo / "new_test.py").write_text("SENTINEL_CREATED_CONTENT = 1\n")

        out = loop.capture_working_tree_diff(self.head_before)

        self.assertIn("tracked.py", out, "the tracked diff must still be there")
        self.assertIn(
            "new_test.py", out,
            "a file the attempt CREATED is exactly what the note was missing "
            "when FEAT-2026-0100/T03 spun twice (#3249)")
        self.assertIn(
            "SENTINEL_CREATED_CONTENT", out,
            "naming the file is not enough — the note has to carry what the "
            "file says, or it still cannot be diagnosed from the artifacts")

    def test_gitignored_paths_stay_out(self):
        # work/ holds the notes themselves; folding them into a note would
        # nest each attempt's evidence inside the next one's.
        (self.repo / "work").mkdir()
        (self.repo / "work" / "attempt-1.md").write_text("SHOULD_NOT_APPEAR\n")
        (self.repo / "new_test.py").write_text("kept\n")

        out = loop.capture_working_tree_diff(self.head_before)

        self.assertNotIn("SHOULD_NOT_APPEAR", out)
        self.assertIn("new_test.py", out)

    def test_a_clean_tree_still_returns_empty(self):
        self.assertEqual("", loop.capture_working_tree_diff(self.head_before))

    def test_the_cap_still_bounds_the_note(self):
        (self.repo / "big_new.py").write_text("x" * 50_000)
        out = loop.capture_working_tree_diff(self.head_before, max_chars=2_000)
        self.assertLess(
            len(out), 4_000,
            "an untracked file must not escape the cap that keeps a committed "
            "note from bloating")

    def test_a_large_tracked_diff_does_not_squeeze_out_the_created_file(self):
        """The regression that would reintroduce the bug at a different size.

        Truncating a concatenation would let a big tracked diff consume the
        whole budget, and the created file — the thing this fix exists to
        surface — would vanish again on exactly the large attempts where
        diagnosis matters most.
        """
        (self.repo / "tracked.py").write_text("y" * 40_000)
        (self.repo / "new_test.py").write_text("SENTINEL_CREATED_CONTENT = 1\n")

        out = loop.capture_working_tree_diff(self.head_before, max_chars=4_000)

        self.assertIn("SENTINEL_CREATED_CONTENT", out)

    def test_a_binary_file_is_named_but_not_inlined(self):
        (self.repo / "blob.bin").write_bytes(b"\x00\x01\x02BINARY\x00")
        out = loop.capture_working_tree_diff(self.head_before)
        self.assertIn("blob.bin", out)
        self.assertNotIn("BINARY", out)


if __name__ == "__main__":
    unittest.main()
