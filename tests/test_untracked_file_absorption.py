#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression tests for issue #150 — squash_commit must not absorb untracked
operator files that pre-date the work unit's dispatch.

Repro: `squash_commit` staged the whole tree with `git add -A`, while the
dirty-tree guard (`ensure_feature_branch` via `_tracked_dirty_paths`)
deliberately ignores untracked files on the premise — stated in that helper's
docstring — that they "carry harmlessly". They do not: `git add -A` commits
them. Any untracked file present when a run starts (another harness's config,
scratch notes, a local script) was silently committed onto the feature branch,
attributed to whichever WU committed first.

Observed: FEAT-2026-0031/T01 absorbed `.codex/config.toml` and `AGENTS.md`
into commit fffadb0.

The fix keeps `add -A` (agent-created files must still be committed) but
unstages any untracked path that was already present at dispatch time — the
distinction that matters is "did this run create the file", not "is it tracked".
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import types
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


class TestUntrackedFileAbsorption(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)],
                       check=True)
        _git(root, "config", "commit.gpgSign", "false")
        _git(root, "config", "user.email", "test@example.com")
        _git(root, "config", "user.name", "Test")
        (root / "a.py").write_text("a\n")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        self.head = _git(root, "rev-parse", "HEAD")
        os.chdir(root)
        self.root = root
        self.wu = types.SimpleNamespace(title="Test WU", wu_id="FEAT-TEST/T01")

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _committed_paths(self) -> set[str]:
        out = _git(self.root, "show", "--name-only", "--format=", "HEAD")
        return {p for p in out.splitlines() if p.strip()}

    def _untracked(self) -> set[str]:
        out = _git(self.root, "ls-files", "--others", "--exclude-standard")
        return {p for p in out.splitlines() if p.strip()}

    # -- the bug ---------------------------------------------------------- #

    def test_preexisting_untracked_file_is_not_absorbed(self):
        """Operator WIP present before dispatch must not enter the WU commit."""
        (self.root / "AGENTS.md").write_text("operator WIP\n")
        untracked_before = loop.untracked_paths()
        self.assertIn("AGENTS.md", untracked_before)

        # The agent does its actual work.
        (self.root / "feature.py").write_text("real work\n")

        sha = loop.squash_commit(self.wu, self.head,
                                 untracked_before=untracked_before)
        self.assertIsNotNone(sha)
        committed = self._committed_paths()
        self.assertIn("feature.py", committed)
        self.assertNotIn("AGENTS.md", committed)

    def test_preexisting_untracked_file_survives_on_disk_and_stays_untracked(self):
        """The operator's file is left alone, not deleted and not staged."""
        (self.root / "AGENTS.md").write_text("operator WIP\n")
        untracked_before = loop.untracked_paths()
        (self.root / "feature.py").write_text("real work\n")

        loop.squash_commit(self.wu, self.head, untracked_before=untracked_before)

        self.assertTrue((self.root / "AGENTS.md").exists())
        self.assertEqual((self.root / "AGENTS.md").read_text(), "operator WIP\n")
        self.assertIn("AGENTS.md", self._untracked())

    def test_preexisting_untracked_directory_is_not_absorbed(self):
        """The .codex/ case — an untracked directory, not just a file."""
        (self.root / ".codex").mkdir()
        (self.root / ".codex" / "config.toml").write_text("cfg\n")
        untracked_before = loop.untracked_paths()
        self.assertIn(".codex/config.toml", untracked_before)

        (self.root / "feature.py").write_text("real work\n")
        loop.squash_commit(self.wu, self.head, untracked_before=untracked_before)

        self.assertNotIn(".codex/config.toml", self._committed_paths())
        self.assertTrue((self.root / ".codex" / "config.toml").exists())

    def test_returns_none_when_only_preexisting_untracked_present(self):
        """A WU that changed nothing of its own must not manufacture a commit
        out of the operator's WIP."""
        (self.root / "AGENTS.md").write_text("operator WIP\n")
        untracked_before = loop.untracked_paths()

        sha = loop.squash_commit(self.wu, self.head,
                                 untracked_before=untracked_before)

        self.assertIsNone(sha)
        self.assertEqual(_git(self.root, "rev-parse", "HEAD"), self.head)
        self.assertIn("AGENTS.md", self._untracked())

    # -- no regression ---------------------------------------------------- #

    def test_agent_created_untracked_file_is_still_committed(self):
        """Files the run itself creates must still be absorbed — that is the
        whole point of `add -A`. Only pre-existing untracked paths are exempt."""
        untracked_before = loop.untracked_paths()   # empty
        (self.root / "new_module.py").write_text("agent wrote this\n")

        sha = loop.squash_commit(self.wu, self.head,
                                 untracked_before=untracked_before)

        self.assertIsNotNone(sha)
        self.assertIn("new_module.py", self._committed_paths())

    def test_tracked_modification_is_still_committed(self):
        """Tracked edits are unaffected by the untracked exemption."""
        (self.root / "a.py").write_text("modified\n")
        untracked_before = loop.untracked_paths()

        sha = loop.squash_commit(self.wu, self.head,
                                 untracked_before=untracked_before)

        self.assertIsNotNone(sha)
        self.assertIn("a.py", self._committed_paths())

    def test_default_arg_preserves_legacy_add_all_behavior(self):
        """Called without the snapshot, behavior is unchanged — callers that
        do not pass it keep absorbing everything (back-compat for any
        non-run() caller)."""
        (self.root / "stray.txt").write_text("stray\n")

        sha = loop.squash_commit(self.wu, self.head)

        self.assertIsNotNone(sha)
        self.assertIn("stray.txt", self._committed_paths())

    def test_untracked_file_deleted_during_dispatch_does_not_break_reset(self):
        """A snapshot path the agent legitimately removed must not make the
        unstage step fail — `git reset -- <missing path>` is a real case."""
        (self.root / "scratch.txt").write_text("scratch\n")
        untracked_before = loop.untracked_paths()
        (self.root / "scratch.txt").unlink()
        (self.root / "feature.py").write_text("real work\n")

        sha = loop.squash_commit(self.wu, self.head,
                                 untracked_before=untracked_before)

        self.assertIsNotNone(sha)
        self.assertIn("feature.py", self._committed_paths())


class TestUntrackedPathsHelper(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)],
                       check=True)
        _git(root, "config", "user.email", "test@example.com")
        _git(root, "config", "user.name", "Test")
        (root / "a.py").write_text("a\n")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        os.chdir(root)
        self.root = root

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_reports_untracked_only(self):
        (self.root / "untracked.txt").write_text("u\n")
        (self.root / "a.py").write_text("modified\n")   # tracked, dirty
        self.assertEqual(loop.untracked_paths(), {"untracked.txt"})

    def test_respects_gitignore(self):
        (self.root / ".gitignore").write_text("ignored.txt\n")
        (self.root / "ignored.txt").write_text("i\n")
        paths = loop.untracked_paths()
        self.assertNotIn("ignored.txt", paths)
        self.assertIn(".gitignore", paths)

    def test_empty_when_clean(self):
        self.assertEqual(loop.untracked_paths(), set())


if __name__ == "__main__":
    unittest.main()
