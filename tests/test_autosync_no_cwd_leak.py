#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""auto_sync must never commit into a repository it was not pointed at (#290).

`auto_sync(repo)` operates on *repo*, but the persistence step it ends with —
``_persist_scaffold_sync`` — was wired to the **current working directory**:
``_scaffold_managed_dirty()`` shells out to ``git status`` in cwd, and
``commit_bookkeeping`` commits in cwd. Neither takes a target.

When those two agree, nothing is wrong. When they diverge, auto_sync commits
somebody else's repository. That is not hypothetical — it is how
``tests/test_autosync.py`` produced three real commits in this repo's history
(``chore(loop): sync scaffold to 0.2.0``, the version those tests patch
``scaffold_version`` to return). Each swept a deliberate release-time edit to
``.specfuse/VERSION`` into an auto-generated commit, and each had to be undone
by hand.

Reproduced before the fix: with ``.specfuse/VERSION`` dirty in the real repo,
``python3 -m unittest tests.test_autosync`` created a commit there.

The guard is that auto_sync persists only when its target *is* the cwd
repository. The tests below use two temp repositories so the assertion can be
made without involving the real one.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from tests._loop_loader import load_loop

loop = load_loop()


@contextmanager
def _chdir(target: Path):
    previous = os.getcwd()
    os.chdir(target)
    try:
        yield
    finally:
        os.chdir(previous)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _make_repo(root: Path) -> None:
    """A git repo with one tracked, committed scaffold file."""
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    specfuse = root / ".specfuse"
    specfuse.mkdir()
    (specfuse / "VERSION").write_text("0.3.0\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "scaffold")


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD")


class TestAutoSyncDoesNotCommitIntoCwd(unittest.TestCase):
    """auto_sync pointed at one repo must not commit into another."""

    def test_autosync_on_foreign_target_does_not_commit_into_cwd(self):
        """The #290 regression: cwd is repo B, auto_sync targets repo A, and
        B has a dirty scaffold file. B must be untouched."""
        with tempfile.TemporaryDirectory() as da, tempfile.TemporaryDirectory() as db:
            target, cwd_repo = Path(da), Path(db)
            _make_repo(target)
            _make_repo(cwd_repo)
            # Non-default branch: on the default branch _persist_scaffold_sync
            # deliberately leaves changes uncommitted, so the leak cannot fire
            # there. Every real occurrence was on a feature/release branch.
            _git(cwd_repo, "checkout", "-q", "-b", "chore/release-x")

            # cwd repo has a deliberate, uncommitted scaffold edit — the
            # release-time shape that was being swept up.
            (cwd_repo / ".specfuse" / "VERSION").write_text(
                "9.9.9\n", encoding="utf-8")
            before = _head(cwd_repo)

            with _chdir(cwd_repo):
                with patch("specfuse.loop.loop._scaffold.scaffold_version",
                           return_value="0.4.0"):
                    loop.auto_sync(target)

            self.assertEqual(
                _head(cwd_repo), before,
                "auto_sync pointed at a different repository must not create a "
                "commit in the current working directory's repository (#290)")

    def test_foreign_target_leaves_the_cwd_edit_uncommitted(self):
        """The edit must survive as a working-tree change, not be absorbed."""
        with tempfile.TemporaryDirectory() as da, tempfile.TemporaryDirectory() as db:
            target, cwd_repo = Path(da), Path(db)
            _make_repo(target)
            _make_repo(cwd_repo)
            _git(cwd_repo, "checkout", "-q", "-b", "chore/release-x")
            (cwd_repo / ".specfuse" / "VERSION").write_text(
                "9.9.9\n", encoding="utf-8")

            with _chdir(cwd_repo):
                with patch("specfuse.loop.loop._scaffold.scaffold_version",
                           return_value="0.4.0"):
                    loop.auto_sync(target)

            self.assertEqual(
                (cwd_repo / ".specfuse" / "VERSION").read_text().strip(), "9.9.9",
                "the operator's edit must be left exactly as found")
            self.assertIn(
                ".specfuse/VERSION",
                _git(cwd_repo, "status", "--porcelain"),
                "the edit must remain uncommitted in the working tree")


class TestAutoSyncStillPersistsOnItsOwnRepo(unittest.TestCase):
    """The guard must not disable the legitimate case it protects."""

    def test_autosync_on_cwd_repo_still_commits(self):
        """When target IS the cwd repo — the real driver's shape — the scaffold
        sync still persists. A guard that also broke this would be a
        regression, not a fix."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _make_repo(root)
            _git(root, "checkout", "-q", "-b", "feat/x")
            before = _head(root)

            with _chdir(root):
                with patch("specfuse.loop.loop._scaffold.scaffold_version",
                           return_value="0.4.0"):
                    loop.auto_sync(root)

            self.assertNotEqual(
                _head(root), before,
                "auto_sync on its own repo must still persist the scaffold sync")


if __name__ == "__main__":
    unittest.main()
