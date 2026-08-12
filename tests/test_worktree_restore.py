# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A run gives the operator back the branch they started on (#2055).

Dispatched `/fix-bug` sessions create and check out branches, so a run that
began on `main` ends wherever the last session left it. Observed 2026-08-12: a
run started on `main` and ended on
`fix/issue-1859-learnings-curate-vendored-promote`, with nothing in the
summary saying so. An operator who reads `items completed: 0` and starts
working is then committing onto an abandoned feature branch.

The restore lives in `main()`, not `run_agent()`. The conductor's invariant --
no code path in it can commit, branch or merge, enforced by
`tests/test_agent_run.py` asserting its runner only ever issues `gh` -- is a
real safety property. The mutation belongs to the dispatched sessions; what
the *caller* owns is the process boundary.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent import worktree


class _Git:
    """A scripted git: current branch, dirtiness, and checkout success."""

    def __init__(self, *, branch="feat/left-here", dirty=False, checkout_ok=True):
        self.calls: list[list] = []
        self.branch = branch
        self._dirty = dirty
        self._checkout_ok = checkout_ok

    def __call__(self, argv, check: bool = False):
        self.calls.append(list(argv))
        if argv[:3] == ["git", "branch", "--show-current"]:
            return SimpleNamespace(returncode=0, stdout=self.branch + "\n", stderr="")
        if argv[:3] == ["git", "status", "--porcelain"]:
            return SimpleNamespace(
                returncode=0, stdout="M file.py\n" if self._dirty else "", stderr=""
            )
        if argv[:2] == ["git", "checkout"]:
            if self._checkout_ok:
                self.branch = argv[2]
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="cannot switch")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    @property
    def checked_out(self) -> bool:
        return any(c[:2] == ["git", "checkout"] for c in self.calls)


class TestRestore(unittest.TestCase):
    def test_a_moved_tree_is_put_back(self):
        git = _Git(branch="feat/left-here")
        said = []

        ok = worktree.restore_branch("main", runner=git, report=said.append)

        self.assertTrue(ok)
        self.assertEqual(git.branch, "main")
        self.assertTrue(any("restored to 'main'" in m for m in said), said)

    def test_the_report_names_where_the_run_left_it(self):
        """"Restored" alone hides that anything happened."""
        git = _Git(branch="fix/issue-1859-something")
        said = []

        worktree.restore_branch("main", runner=git, report=said.append)

        self.assertTrue(any("fix/issue-1859-something" in m for m in said), said)

    def test_an_unmoved_tree_is_not_checked_out(self):
        git = _Git(branch="main")

        ok = worktree.restore_branch("main", runner=git)

        self.assertTrue(ok)
        self.assertFalse(git.checked_out)


class TestRestoreRefusesRatherThanRisksWork(unittest.TestCase):
    def test_a_dirty_tree_is_not_forced(self):
        """A checkout here could discard a dispatched session's work.

        Losing work is strictly worse than being on the wrong branch, so the
        refusal is the correct outcome — but it must be loud.
        """
        git = _Git(branch="feat/left-here", dirty=True)
        said = []

        ok = worktree.restore_branch("main", runner=git, report=said.append)

        self.assertFalse(ok)
        self.assertFalse(git.checked_out)
        self.assertTrue(any("NOT restored" in m for m in said), said)
        self.assertTrue(any("uncommitted" in m for m in said), said)

    def test_an_unreadable_status_is_not_forced_either(self):
        def unreadable(argv, check=False):
            if argv[:3] == ["git", "branch", "--show-current"]:
                return SimpleNamespace(returncode=0, stdout="feat/x\n", stderr="")
            return SimpleNamespace(returncode=128, stdout="", stderr="not a repo")

        said = []
        ok = worktree.restore_branch("main", runner=unreadable, report=said.append)

        self.assertFalse(ok)
        self.assertTrue(any("could not read" in m for m in said), said)

    def test_a_failed_checkout_is_reported(self):
        git = _Git(branch="feat/left-here", checkout_ok=False)
        said = []

        ok = worktree.restore_branch("main", runner=git, report=said.append)

        self.assertFalse(ok)
        self.assertTrue(any("could not restore" in m for m in said), said)

    def test_a_detached_head_start_restores_nothing(self):
        git = _Git(branch="feat/left-here")

        ok = worktree.restore_branch(None, runner=git)

        self.assertTrue(ok)
        self.assertFalse(git.checked_out)

    def test_a_raising_git_never_propagates(self):
        def broken(argv, check=False):
            raise OSError("git missing")

        self.assertIsNone(worktree.current_branch(broken))
        self.assertIsNone(worktree.is_dirty(broken))
        self.assertFalse(worktree.restore_branch("main", runner=broken))


class TestAgainstRealGit(unittest.TestCase):
    """Fixtures can encode the author's misunderstanding; git cannot."""

    def test_restore_round_trip_in_a_real_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(root), *args],
                    capture_output=True, text=True, check=False,
                )

            git("init", "-q", "-b", "main")
            git("config", "user.email", "t@example.com")
            git("config", "user.name", "T")
            git("config", "commit.gpgsign", "false")
            (root / "seed.txt").write_text("seed\n")
            git("add", "-A")
            git("commit", "-qm", "seed")

            def runner(argv, check=False):
                return subprocess.run(
                    ["git", "-C", str(root), *argv[1:]],
                    capture_output=True, text=True, check=False,
                )

            started = worktree.current_branch(runner)
            self.assertEqual(started, "main")

            git("checkout", "-q", "-b", "fix/issue-999-simulated")
            self.assertEqual(worktree.current_branch(runner), "fix/issue-999-simulated")

            said = []
            ok = worktree.restore_branch(started, runner=runner, report=said.append)

            self.assertTrue(ok, said)
            self.assertEqual(worktree.current_branch(runner), "main")


if __name__ == "__main__":
    unittest.main()
