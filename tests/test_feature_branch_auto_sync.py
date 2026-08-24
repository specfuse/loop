# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A branch behind its base is brought up to date, not refused.

A feature branch falls behind its base every time anything else merges. That
is the normal life of a feature branch. Refusing it made the driver unable to
advance ANY in-flight feature after any merge to `main` — for an unattended
agent, a deadlock generator rather than a safety property.

Observed across four consecutive runs against FEAT-2026-0080: each fix
exposed the next condition, and the last one recurred the moment `main` moved
again, because merging the previous fix put the branch one commit behind.

The guard's stated purpose (#48) is that a pre-existing branch "is **surfaced**
rather than silently checked out". Surfaced, not refused. The hazard is
silently reusing a branch from a *different lineage*; a branch the driver has
been committing to that is merely behind its base is not that.

So it now does what a human would: bring it up to date, and refuse only when
that cannot be done automatically. `merge`, not `rebase` — the branch may
already be pushed, and rewriting its history would force consumers to recover
from a force-push to fix a condition that is not their fault.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop import loop


@contextmanager
def _chdir(path):
    prior = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prior)


class _Repo:
    def __init__(self, root: Path):
        self.root = root
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "T")
        self.git("config", "commit.gpgsign", "false")
        self.commit("seed.txt", "seed")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True, text=True, check=False,
        )

    def commit(self, name, text):
        (self.root / name).write_text(text + "\n")
        self.git("add", "-A")
        self.git("commit", "-qm", f"write {name}")

    def branch_now(self):
        return self.git("branch", "--show-current").stdout.strip()

    def counts(self, branch, base="main"):
        out = self.git("rev-list", "--left-right", "--count", f"{base}...{branch}").stdout.split()
        return (int(out[0]), int(out[1])) if len(out) == 2 else (0, 0)


class TestBehindBranchIsBroughtUpToDate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _Repo(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def _feature_branch_with_work_then_main_moves(self):
        """The exact shape that blocked FEAT-2026-0080 for four runs."""
        self.repo.git("checkout", "-q", "-b", "feat/x")
        self.repo.commit("work.txt", "real feature work")
        self.repo.git("checkout", "-q", "main")
        self.repo.commit("other.txt", "an unrelated PR merged")

    def test_the_driver_no_longer_refuses(self):
        self._feature_branch_with_work_then_main_moves()
        behind, ahead = self.repo.counts("feat/x")
        self.assertEqual((behind, ahead), (1, 1), "precondition: truly diverged")

        with _chdir(self.repo.root):
            loop.ensure_feature_branch({"branch": "feat/x"})

        self.assertEqual(self.repo.branch_now(), "feat/x")

    def test_the_branch_is_actually_up_to_date_afterwards(self):
        self._feature_branch_with_work_then_main_moves()

        with _chdir(self.repo.root):
            loop.ensure_feature_branch({"branch": "feat/x"})

        behind, _ahead = self.repo.counts("feat/x")
        self.assertEqual(behind, 0, "base's commits must now be on the branch")

    def test_the_feature_work_survives(self):
        """Bringing it up to date must not cost the work it was carrying."""
        self._feature_branch_with_work_then_main_moves()

        with _chdir(self.repo.root):
            loop.ensure_feature_branch({"branch": "feat/x"})

        self.assertEqual((self.repo.root / "work.txt").read_text().strip(), "real feature work")
        self.assertEqual((self.repo.root / "other.txt").read_text().strip(), "an unrelated PR merged")

    def test_history_is_not_rewritten(self):
        """`merge`, not `rebase` — the branch may already be pushed."""
        self._feature_branch_with_work_then_main_moves()
        before = self.repo.git("rev-parse", "feat/x").stdout.strip()

        with _chdir(self.repo.root):
            loop.ensure_feature_branch({"branch": "feat/x"})

        contained = self.repo.git("merge-base", "--is-ancestor", before, "feat/x")
        self.assertEqual(contained.returncode, 0, "the prior tip must still be reachable")

    def test_an_already_current_branch_is_untouched(self):
        self.repo.git("checkout", "-q", "-b", "feat/y")
        self.repo.commit("work.txt", "work")
        tip = self.repo.git("rev-parse", "feat/y").stdout.strip()
        self.repo.git("checkout", "-q", "main")

        with _chdir(self.repo.root):
            loop.ensure_feature_branch({"branch": "feat/y"})

        self.assertEqual(self.repo.git("rev-parse", "feat/y").stdout.strip(), tip)


class TestAConflictIsReportedNotRefused(unittest.TestCase):
    """A conflicting catch-up warns and proceeds; it used to raise (#2556).

    Each guarantee this class asserted when the conflict was fatal is kept
    and re-asserted at the new boundary -- the tree is still left exactly as
    it was, git's own report still reaches the operator, and the condition is
    still named rather than guessed at. Only "the run stops" is gone, because
    under a squash-merge policy the conflict is guaranteed on every run and
    stopping made the driver unusable in such a repository.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _Repo(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def _conflicting(self):
        self.repo.git("checkout", "-q", "-b", "feat/conflict")
        self.repo.commit("shared.txt", "branch version")
        self.repo.git("checkout", "-q", "main")
        self.repo.commit("shared.txt", "main version")

    def _run(self) -> str:
        buf = io.StringIO()
        with _chdir(self.repo.root):
            with contextlib.redirect_stdout(buf):
                loop.ensure_feature_branch({"branch": "feat/conflict"})
        return buf.getvalue()

    def test_it_reports_rather_than_guessing(self):
        """The condition is still named; the driver no longer stops on it."""
        self._conflicting()

        out = self._run()

        self.assertIn("conflicts", out)
        self.assertIn("WARNING", out)

    def test_the_branch_is_left_exactly_as_it_was(self):
        """Unchanged guarantee: no half-merged tree behind, raise or not.

        This one matters MORE now than it did as a refusal -- the run keeps
        going, so a leftover conflicted tree would be swept into the next
        work unit's squash commit.
        """
        self._conflicting()
        tip = self.repo.git("rev-parse", "feat/conflict").stdout.strip()

        self._run()

        self.assertEqual(self.repo.git("rev-parse", "feat/conflict").stdout.strip(), tip)
        self.assertEqual(
            self.repo.git("rev-parse", "-q", "--verify", "MERGE_HEAD").returncode,
            1,
            "no merge may be left in progress",
        )
        self.assertEqual(
            self.repo.git("status", "--porcelain").stdout, "",
            "the tree must be clean for the next squash commit",
        )

    def test_the_message_carries_gits_own_report(self):
        """Unchanged guarantee, now on stdout instead of an exception."""
        self._conflicting()

        out = self._run()

        self.assertIn("shared.txt", out)

    def test_the_driver_ends_on_the_feature_branch_ready_to_work(self):
        """The point of the change: the run continues instead of halting."""
        self._conflicting()

        self._run()

        self.assertEqual(
            self.repo.git("branch", "--show-current").stdout.strip(),
            "feat/conflict",
        )


if __name__ == "__main__":
    unittest.main()
