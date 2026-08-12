# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A stop that already committed work must say so.

`refused` / `could_not_proceed` describes the step the session reached. It
says nothing about what the session finished before reaching it, and the two
are not distinguishable from the outcome constant alone.

Observed live on issue #1859: the session wrote a skill fix, a new test file
and a CHANGELOG entry, committed all of it as "Closes #1859", then stopped --
almost certainly at the push or the PR open. The escalation recorded on the
issue read "stopped without opening a mergeable PR" and offered three
options: fix by hand, promote to a feature, close the issue. None of them was
"push the branch that already exists". Twenty minutes of green, tested work
was invisible until someone went looking by hand, and a fresh clone would
have lost it silently.
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.run import KIND_BUG, STATUS_ESCALATED, ActionItem
from specfuse.loop.bug_lane_run import (
    OUTCOME_COULD_NOT_PROCEED,
    OUTCOME_REFUSED,
    BugLaneResult,
    unpushed_work_for_issue,
)

_BRANCH = "fix/issue-1859-learnings-curate-vendored-promote"


class _Git:
    """`git branch --list` / `git log` over a fake local repository."""

    def __init__(self, branches=(), unpushed=None):
        self.calls: list[list] = []
        self._branches = branches
        self._unpushed = unpushed or {}

    def __call__(self, argv, check: bool = False):
        self.calls.append(list(argv))
        if argv[:3] == ["git", "branch", "--list"]:
            return SimpleNamespace(
                returncode=0, stdout="\n".join(self._branches), stderr=""
            )
        if argv[:2] == ["git", "log"]:
            shas = self._unpushed.get(argv[2], [])
            return SimpleNamespace(returncode=0, stdout="\n".join(shas), stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")


class TestDetectingUnpushedWork(unittest.TestCase):
    def test_a_branch_with_unpushed_commits_is_found(self):
        runner = _Git(branches=[_BRANCH], unpushed={_BRANCH: ["a" * 40, "b" * 40]})

        self.assertEqual(unpushed_work_for_issue(runner, 1859), (_BRANCH, 2))

    def test_a_branch_whose_commits_are_all_pushed_is_not_reported(self):
        """Pushed work is discoverable; only the invisible kind matters here."""
        runner = _Git(branches=[_BRANCH], unpushed={_BRANCH: []})

        self.assertIsNone(unpushed_work_for_issue(runner, 1859))

    def test_no_branch_at_all_reports_nothing(self):
        self.assertIsNone(unpushed_work_for_issue(_Git(branches=[]), 1859))

    def test_only_this_issue_s_branch_is_considered(self):
        runner = _Git(branches=[_BRANCH], unpushed={_BRANCH: ["a" * 40]})

        unpushed_work_for_issue(runner, 1859)

        glob = runner.calls[0][3]
        self.assertIn("1859", glob)

    def test_the_probe_is_read_only(self):
        runner = _Git(branches=[_BRANCH], unpushed={_BRANCH: ["a" * 40]})

        unpushed_work_for_issue(runner, 1859)

        for call in runner.calls:
            with self.subTest(call=call):
                self.assertIn(call[1], ("branch", "log"))
                self.assertNotIn("--delete", call)
                self.assertNotIn("-d", call)

    def test_a_failing_git_never_breaks_the_lane(self):
        def broken(argv, check: bool = False):
            raise OSError("git is not on PATH")

        self.assertIsNone(unpushed_work_for_issue(broken, 1859))

    def test_a_nonzero_git_reports_nothing_rather_than_guessing(self):
        def failing(argv, check: bool = False):
            return SimpleNamespace(returncode=128, stdout="", stderr="not a repo")

        self.assertIsNone(unpushed_work_for_issue(failing, 1859))


class TestTheEscalationNamesTheBranch(unittest.TestCase):
    def _escalate(self, outcome, unpushed):
        provider = BugsProvider(repo="o/r", runner=lambda *a, **k: None)
        item = ActionItem(item_id="bug-1859", kind=KIND_BUG)
        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(
                outcome=outcome, reason=None, pr_number=None, unpushed_work=unpushed
            ),
        ):
            return provider.execute(item)

    def test_the_branch_and_commit_count_are_in_the_body(self):
        outcome = self._escalate(OUTCOME_COULD_NOT_PROCEED, (_BRANCH, 2))

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        body = " ".join(
            [
                outcome.escalation.done_so_far,
                outcome.escalation.issue_summary,
                outcome.escalation.recommendation,
            ]
        )
        self.assertIn(_BRANCH, body)
        self.assertIn("2 commits", body)

    def test_pushing_the_branch_is_offered_as_an_option(self):
        """The option that was missing when this cost twenty minutes."""
        outcome = self._escalate(OUTCOME_REFUSED, (_BRANCH, 1))

        labels = " ".join(label for label, _pros, _cons in outcome.escalation.options)
        self.assertIn("push", labels.lower())
        self.assertIn(_BRANCH, labels)

    def test_a_single_commit_is_not_described_as_commits(self):
        outcome = self._escalate(OUTCOME_REFUSED, (_BRANCH, 1))

        self.assertIn("1 commit ", outcome.escalation.done_so_far + " ")
        self.assertNotIn("1 commits", outcome.escalation.done_so_far)

    def test_the_run_summary_detail_mentions_the_branch(self):
        """The operator scanning the terminal should not need the issue."""
        outcome = self._escalate(OUTCOME_COULD_NOT_PROCEED, (_BRANCH, 3))

        self.assertIn(_BRANCH, outcome.detail)
        self.assertIn("unpushed", outcome.detail)

    def test_a_genuinely_empty_stop_keeps_the_original_wording(self):
        """Not every stop leaves work; that payload was right for those."""
        outcome = self._escalate(OUTCOME_REFUSED, None)

        self.assertIn("without opening a mergeable PR", outcome.escalation.done_so_far)
        labels = " ".join(label for label, _p, _c in outcome.escalation.options)
        self.assertNotIn("push", labels.lower())

    def test_the_escalation_still_lands_on_the_bug_s_own_issue(self):
        outcome = self._escalate(OUTCOME_COULD_NOT_PROCEED, (_BRANCH, 2))

        self.assertEqual(outcome.escalation.target_issue, 1859)


if __name__ == "__main__":
    unittest.main()
