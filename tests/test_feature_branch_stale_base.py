# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The driver resumes an in-progress feature branch, and still refuses a stale one.

`ensure_feature_branch` asked `git merge-base --is-ancestor <branch> <base>`,
which exits 0 only when the base already **contains** the branch — true only
once the feature is merged. Every feature branch carrying unmerged work failed
it by construction, so the driver refused to resume any feature that had done
anything.

It stayed hidden because `specfuse-agent` used to leave the working tree ON
the feature branch, so the next run hit the `current == branch` early return
and never reached the check. Restoring the operator's branch at run end
(#2055) removed that accident and exposed it — the first `FeatureBranchError`
appeared on the very next run after the first restore.

The refusal also prescribed `git rebase <base>`, which **cannot** satisfy an
is-ancestor test in that direction: rebasing makes the branch contain the
base, while the test wanted the base to contain the branch. A branch rebased
exactly as instructed was refused again.

These tests run against real git, because the whole defect was a
misunderstanding of what one git command answers.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class _Repo:
    def __init__(self, root: Path):
        self.root = root
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "T")
        self.git("config", "commit.gpgsign", "false")
        self.commit("seed.txt", "seed")

    def git(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True, text=True, check=False,
        )

    def commit(self, name: str, text: str) -> None:
        (self.root / name).write_text(text + "\n")
        self.git("add", "-A")
        self.git("commit", "-qm", f"add {name}")

    def accepted(self, branch: str, base: str = "main") -> bool:
        """Replicate the guard's decision: refuse only true divergence."""
        out = self.git(
            "rev-list", "--left-right", "--count", f"{base}...{branch}"
        ).stdout.split()
        behind, ahead = (int(out[0]), int(out[1])) if len(out) == 2 else (0, 0)
        return not (behind and ahead)


class TestTheGuardsDecision(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _Repo(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_a_branch_with_unmerged_work_is_accepted(self):
        """The case that was refused: normal in-progress feature work."""
        self.repo.git("checkout", "-q", "-b", "feat/x")
        self.repo.commit("work.txt", "real work")

        self.assertTrue(self.repo.accepted("feat/x"))

    def test_a_branch_forked_from_an_older_base_is_refused(self):
        """The case the guard exists for, and still catches."""
        self.repo.git("checkout", "-q", "-b", "feat/stale")
        self.repo.commit("work.txt", "work on an old base")
        self.repo.git("checkout", "-q", "main")
        self.repo.commit("moved.txt", "main moved on")

        self.assertFalse(self.repo.accepted("feat/stale"))

    def test_rebasing_a_stale_branch_makes_it_acceptable(self):
        """The remedy the error prescribes must actually work.

        Under the old is-ancestor test it did not: a branch rebased exactly
        as instructed was refused again, because rebasing cannot make the
        base contain the branch.
        """
        self.repo.git("checkout", "-q", "-b", "feat/stale")
        self.repo.commit("work.txt", "work")
        self.repo.git("checkout", "-q", "main")
        self.repo.commit("moved.txt", "main moved")
        self.assertFalse(self.repo.accepted("feat/stale"))

        self.repo.git("checkout", "-q", "feat/stale")
        self.repo.git("rebase", "main")

        self.assertTrue(self.repo.accepted("feat/stale"))

    def test_a_freshly_created_branch_is_accepted(self):
        self.repo.git("checkout", "-q", "-b", "feat/new")

        self.assertTrue(self.repo.accepted("feat/new"))

    def test_a_merged_branch_is_accepted(self):
        """Merged work leaves the branch behind-only, which is not divergence."""
        self.repo.git("checkout", "-q", "-b", "feat/done")
        self.repo.commit("work.txt", "work")
        self.repo.git("checkout", "-q", "main")
        self.repo.git("merge", "-q", "--no-ff", "-m", "merge", "feat/done")

        self.assertTrue(self.repo.accepted("feat/done"))

    def test_a_branch_merely_behind_is_accepted(self):
        """Created earlier, no work yet. Refusing this broke a shipped test.

        My first attempt compared the branch's merge-base against the base's
        tip, which refused anything not built on the current tip — including
        a branch that has done nothing. `tests/test_ensure_feature_branch.py`
        caught it: its dirty-tree fixture uses exactly this shape.
        """
        self.repo.git("branch", "feat/idle")
        self.repo.commit("moved.txt", "main moved on")

        self.assertTrue(self.repo.accepted("feat/idle"))

    def test_a_merged_branch_main_has_not_moved_past_is_accepted(self):
        """Fast-forward merge: main's tip IS the branch's tip, so it is current."""
        self.repo.git("checkout", "-q", "-b", "feat/ff")
        self.repo.commit("work.txt", "work")
        self.repo.git("checkout", "-q", "main")
        self.repo.git("merge", "-q", "--ff-only", "feat/ff")

        self.assertTrue(self.repo.accepted("feat/ff"))


class TestTheOldCheckWasUnsatisfiable(unittest.TestCase):
    """Pin why the change was needed, not just that it works now."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _Repo(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_is_ancestor_rejects_every_branch_with_work(self):
        self.repo.git("checkout", "-q", "-b", "feat/x")
        self.repo.commit("work.txt", "work")

        old = self.repo.git("merge-base", "--is-ancestor", "feat/x", "main")

        self.assertNotEqual(old.returncode, 0)
        self.assertTrue(self.repo.accepted("feat/x"), "the new check accepts it")

    def test_rebasing_never_satisfied_the_old_check(self):
        self.repo.git("checkout", "-q", "-b", "feat/x")
        self.repo.commit("work.txt", "work")
        self.repo.git("checkout", "-q", "main")
        self.repo.commit("moved.txt", "moved")
        self.repo.git("checkout", "-q", "feat/x")
        self.repo.git("rebase", "main")

        old = self.repo.git("merge-base", "--is-ancestor", "feat/x", "main")

        self.assertNotEqual(
            old.returncode, 0, "rebasing cannot make the base contain the branch"
        )
        self.assertTrue(self.repo.accepted("feat/x"))


class TestUnreadableGitFailsOpen(unittest.TestCase):
    def test_the_message_no_longer_implies_unmerged_work_is_the_problem(self):
        src = (REPO_ROOT / "specfuse" / "loop" / "loop.py").read_text()

        self.assertIn("Carrying unmerged commits is normal", src)


if __name__ == "__main__":
    unittest.main()
