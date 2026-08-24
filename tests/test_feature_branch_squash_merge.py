# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A squash-merge repository must not deadlock the driver (#2556).

In a repository whose policy is pull-request-per-change squash-merged to
main, a squash commit is **not an ancestor** of the branch it was produced
from. So every feature branch falls behind its base the moment anything
else merges, and `ensure_feature_branch`'s auto-merge replays the squashed
change against the branch's own version of the same files.

When those files overlap, the merge conflicts *by construction* rather than
incidentally, and the driver used to raise `FeatureBranchError` and stop --
so `specfuse run` could not start at all in a repository following one of
the most common merge policies there is.

That refusal contradicted the reasoning already recorded a few lines above
it in `loop.py`, which is why this is a fix and not a preference:

    A feature branch falls behind its base every time anything else merges.
    That is the normal life of a feature branch, not a fault -- and refusing
    it made the driver unable to advance ANY in-flight feature after any
    merge, which for an unattended agent is a deadlock generator rather than
    a safety property.

Real git throughout: the whole defect is about what git does with ancestry
a squash discards, and a mocked subprocess would assert the misunderstanding
rather than the behaviour.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT, load_loop

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

loop = load_loop()


def _git(root: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=False,
    )


@contextlib.contextmanager
def _chdir(target: Path):
    prior = Path.cwd()
    os.chdir(target)
    try:
        yield
    finally:
        os.chdir(prior)


class _SquashMergeRepo:
    """A repo whose merge policy squashes, reproduced exactly.

    `shared.txt` is the overlap that makes the conflict guaranteed: the
    feature branch edits it, and a *different* feature's squash lands a
    different edit to the same file on main.
    """

    def __init__(self, root: Path):
        self.root = root
        _git(root, "init", "-q", "-b", "main")
        _git(root, "config", "user.email", "t@example.com")
        _git(root, "config", "user.name", "T")
        _git(root, "config", "commit.gpgsign", "false")
        self.commit("shared.txt", "base\n")

    def commit(self, name: str, text: str) -> None:
        (self.root / name).write_text(text)
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", f"write {name}")

    def squash_merge_someone_elses_work(self, text: str) -> None:
        """Land a change on main the way a squash-merge policy does.

        Built on a side branch and committed to main as one fresh commit
        with no ancestry link back -- which is the whole point: nothing on
        main is an ancestor of the branch that produced it.
        """
        _git(self.root, "checkout", "-q", "-b", "feat/other")
        self.commit("shared.txt", text)
        _git(self.root, "checkout", "-q", "main")
        _git(self.root, "merge", "-q", "--squash", "feat/other")
        _git(self.root, "commit", "-qm", "squashed: other feature")
        _git(self.root, "branch", "-qD", "feat/other")

    def state(self) -> str:
        return _git(self.root, "status", "--porcelain").stdout


class TestSquashMergeDoesNotDeadlockTheDriver(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _SquashMergeRepo(Path(self._tmp.name))
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _feature_branch_behind_a_conflicting_squash(self) -> None:
        """Set up the exact reported state: a live feature branch, behind."""
        _git(self.root, "checkout", "-q", "-b", "feat/mine")
        self.repo.commit("shared.txt", "my feature's edit\n")
        _git(self.root, "checkout", "-q", "main")
        self.repo.squash_merge_someone_elses_work("a different feature's edit\n")

    def test_driver_proceeds_instead_of_raising(self):
        """The reported bug: a hard stop the operator cannot work around."""
        self._feature_branch_behind_a_conflicting_squash()

        with _chdir(self.root):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                loop.ensure_feature_branch({"branch": "feat/mine", "base": "main"})
            out = buf.getvalue()

        self.assertEqual(
            _git(self.root, "branch", "--show-current").stdout.strip(),
            "feat/mine",
            "the driver must end up on the feature branch, ready to work",
        )
        self.assertIn("could not be brought up to date", out)

    def test_the_conflicted_merge_is_aborted_not_left_in_the_tree(self):
        """Proceeding is only safe if the tree is clean when we do.

        A half-merged tree would be swept into the next work unit's squash
        commit, which is a far worse outcome than the halt this replaces.
        """
        self._feature_branch_behind_a_conflicting_squash()

        with _chdir(self.root):
            with contextlib.redirect_stdout(io.StringIO()):
                loop.ensure_feature_branch({"branch": "feat/mine", "base": "main"})

        self.assertEqual(self.repo.state(), "", "working tree must be clean")
        self.assertFalse(
            (self.root / ".git" / "MERGE_HEAD").exists(),
            "a merge must not still be in progress",
        )

    def test_the_warning_names_the_recovery(self):
        """An operator reading it must know what to do and that work went on."""
        self._feature_branch_behind_a_conflicting_squash()

        with _chdir(self.root):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                loop.ensure_feature_branch({"branch": "feat/mine", "base": "main"})
            out = buf.getvalue()

        self.assertIn("feat/mine", out)
        self.assertIn("main", out)
        self.assertIn("git merge main", out, "the manual recovery must be named")

    def test_a_clean_behind_branch_is_still_merged_up_to_date(self):
        """No regression: the non-conflicting path keeps auto-merging.

        Only the conflicting case changes; a branch that CAN be brought up
        to date still is, which is what #2186 built this path for.
        """
        _git(self.root, "checkout", "-q", "-b", "feat/clean")
        self.repo.commit("mine.txt", "my work\n")
        _git(self.root, "checkout", "-q", "main")
        self.repo.commit("theirs.txt", "unrelated\n")
        main_tip = _git(self.root, "rev-parse", "main").stdout.strip()

        with _chdir(self.root):
            with contextlib.redirect_stdout(io.StringIO()):
                loop.ensure_feature_branch({"branch": "feat/clean", "base": "main"})

        contains = _git(
            self.root, "merge-base", "--is-ancestor", main_tip, "feat/clean"
        ).returncode
        self.assertEqual(contains, 0, "the branch must now contain main's tip")
        self.assertEqual(self.repo.state(), "")

    def test_an_up_to_date_branch_is_untouched(self):
        """No merge attempted when there is nothing to merge."""
        _git(self.root, "checkout", "-q", "-b", "feat/current")
        self.repo.commit("mine.txt", "my work\n")
        tip = _git(self.root, "rev-parse", "feat/current").stdout.strip()
        _git(self.root, "checkout", "-q", "main")

        with _chdir(self.root):
            with contextlib.redirect_stdout(io.StringIO()):
                loop.ensure_feature_branch({"branch": "feat/current", "base": "main"})

        self.assertEqual(
            _git(self.root, "rev-parse", "feat/current").stdout.strip(),
            tip,
            "an up-to-date branch must not gain a merge commit",
        )


if __name__ == "__main__":
    unittest.main()
