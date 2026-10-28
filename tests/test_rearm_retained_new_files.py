#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A re-armed unit keeps the new files its retained attempt created (#3538).

After a bookkeeping-guard refusal the driver uncommits the squash and keeps
the tree (`retain_tree_after_refusal`, FEAT-2026-0103), so the attempt's new
files are untracked again. The untracked snapshot a later dispatch takes
(`untracked_paths`, #150) then classified them as operator WIP — on a re-arm,
which starts a new snapshot, `squash_commit` unstaged them and every new
`produces:` file failed `produces_not_in_diff`. Undeclared new files were
silently left out of the commit.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _git(*args):
    subprocess.run(["git", *args], check=True, capture_output=True)


class RetainedNewFilesSurviveRearm(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        _git("init", "-q")
        _git("config", "user.email", "t@example.com")
        _git("config", "user.name", "t")
        Path("tracked.txt").write_text("v1\n")
        _git("add", ".")
        _git("commit", "-q", "-m", "base")
        Path("operator-notes.md").write_text("mine\n")
        self.events = Path("events.jsonl")
        self.wu = loop.WorkUnit(
            wu_id="X/T1", file=Path("WU-1.md"), depends_on=[],
            type="implementation", model="m", status="pending", attempts=0,
            title="t", body="", produces=["src/new_module.py"],
        )

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _refused_attempt(self):
        """Cycle 1: an attempt creates files, squashes, and is refused."""
        head_before = loop.git("rev-parse", "HEAD")
        untracked_before = loop.untracked_paths()
        Path("src").mkdir()
        Path("src/new_module.py").write_text("x = 1\n")
        Path("src/helper.py").write_text("y = 2\n")
        Path("tracked.txt").write_text("v2\n")
        self.assertIsNotNone(
            loop.squash_commit(self.wu, head_before, untracked_before))
        _note, retained = loop._resolve_guard_refusal_tree(
            {}, head_before, self.events, untracked_before, "refused")
        self.assertTrue(retained)
        return head_before

    def test_rearm_snapshot_does_not_claim_retained_files(self):
        self._refused_attempt()
        snapshot = loop.untracked_paths()
        self.assertNotIn("src/new_module.py", snapshot)
        self.assertNotIn("src/helper.py", snapshot)
        self.assertIn("operator-notes.md", snapshot)

    def test_rearm_squash_commits_retained_files_not_operator_wip(self):
        self._refused_attempt()
        # Cycle 2 (re-arm): a fresh dispatch takes a fresh snapshot.
        head_before = loop.git("rev-parse", "HEAD")
        untracked_before = loop.untracked_paths()
        sha = loop.squash_commit(self.wu, head_before, untracked_before)
        self.assertIsNotNone(sha)
        committed = set(loop.git(
            "show", "--name-only", "--pretty=format:", sha).split())
        self.assertEqual(
            committed, {"src/new_module.py", "src/helper.py", "tracked.txt"})

    def test_bookkeeping_commit_after_refusal_carries_only_its_paths(self):
        self._refused_attempt()
        Path("WU-1.md").write_text("status: blocked_human\n")
        sha = loop.commit_bookkeeping([Path("WU-1.md")], "chore: blocked")
        committed = set(loop.git(
            "show", "--name-only", "--pretty=format:", sha).split())
        self.assertEqual(committed, {"WU-1.md"})
        self.assertTrue(Path("src/new_module.py").exists())
        self.assertNotIn("src/new_module.py", loop.untracked_paths())

    def test_tree_and_operator_wip_are_kept(self):
        self._refused_attempt()
        self.assertEqual(Path("src/helper.py").read_text(), "y = 2\n")
        self.assertEqual(Path("tracked.txt").read_text(), "v2\n")
        self.assertIn("operator-notes.md", loop.untracked_paths())

    def test_retained_diff_note_still_shows_created_files(self):
        head_before = loop.git("rev-parse", "HEAD")
        untracked_before = loop.untracked_paths()
        Path("created.py").write_text("z = 3\n")
        loop.squash_commit(self.wu, head_before, untracked_before)
        note, _retained = loop._resolve_guard_refusal_tree(
            {}, head_before, self.events, untracked_before, "refused")
        self.assertIn("created.py", note)
        self.assertIn("z = 3", note)


if __name__ == "__main__":
    unittest.main()
