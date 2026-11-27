#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A kept tree whose attempt created a non-ASCII-named file (#3616).

`untracked_paths` read `git ls-files --others` line by line, so with git's
default `core.quotePath=true` a name like `café.md` came back C-quoted
(`"caf\\303\\251.md"`, quotes included). `retain_tree_after_refusal` then
passed that quoted string to `git add -N`, which matched nothing and exited
128, crashing the driver on a guard refusal that kept the tree.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

CAFE = "docs/café.md"


def _git(*args) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True,
                          text=True).stdout


class NonAsciiUntrackedPaths(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        _git("init", "-q")
        _git("config", "user.email", "t@example.com")
        _git("config", "user.name", "t")
        _git("config", "commit.gpgSign", "false")
        Path("tracked.txt").write_text("v1\n")
        _git("add", ".")
        _git("commit", "-q", "-m", "base")

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_untracked_paths_returns_the_real_name(self):
        Path("docs").mkdir()
        Path(CAFE).write_text("x\n")
        self.assertEqual(loop.untracked_paths(), {CAFE})

    def test_kept_tree_marks_a_new_non_ascii_file_intent_to_add(self):
        head_before = loop.git("rev-parse", "HEAD")
        untracked_before = loop.untracked_paths()
        Path("docs").mkdir()
        Path(CAFE).write_text("x\n")
        Path("tracked.txt").write_text("v2\n")

        loop.retain_tree_after_refusal(
            head_before, Path("events.jsonl"), untracked_before)

        self.assertEqual(loop.untracked_paths(), set())
        # Intent-to-add: in the index (ls-files), still uncommitted.
        self.assertIn(CAFE, _git("ls-files", "-z").split("\0"))
        self.assertEqual(loop.git("rev-parse", "HEAD"), head_before)
        self.assertEqual(Path(CAFE).read_text(), "x\n")


if __name__ == "__main__":
    unittest.main()
