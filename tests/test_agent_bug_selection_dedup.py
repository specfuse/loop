# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The bugs provider does not re-advertise work a human or a PR already owns.

Both exclusions come from one live run (2026-08-11): issue #1183 was refused
on three separate runs and produced three tracking issues, issue #1163 was
re-fixed while its first PR was still open, and the escalations the agent
filed were themselves triaged `bug` -- so the next run's candidate list
contained the agent's own "PR was declined by the merge guardrails" reports.
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.state import AgentSnapshot, IssueSummary, PRSummary


def _runner(argv, check: bool = False):
    return SimpleNamespace(returncode=0, stdout="", stderr="")


def _issue(number: int, *, labels: tuple = ()) -> IssueSummary:
    return IssueSummary(
        number=number,
        title=f"issue {number}",
        labels=labels,
        triage_category="bug",
        triage_confidence="high",
    )


def _snapshot(issues: tuple, prs: tuple = ()) -> AgentSnapshot:
    return AgentSnapshot(
        queue=(),
        triage_auto=False,
        bug_automerge=False,
        bug_lane_limits={},
        issues=issues,
        issues_error=None,
        prs=prs,
        prs_error=None,
        features=(),
    )


class TestHumanOwnedIssuesAreNotAdvertised(unittest.TestCase):
    def test_needs_human_issue_is_skipped(self):
        provider = BugsProvider(repo="o/r", runner=_runner)
        snapshot = _snapshot((_issue(1183, labels=("needs-human", "blocked-wu")),))

        self.assertEqual(provider.advertise(snapshot), [])

    def test_blocked_wu_alone_is_enough_to_skip(self):
        provider = BugsProvider(repo="o/r", runner=_runner)
        snapshot = _snapshot((_issue(1183, labels=("blocked-wu",)),))

        self.assertEqual(provider.advertise(snapshot), [])

    def test_unlabelled_triaged_bug_is_still_advertised(self):
        provider = BugsProvider(repo="o/r", runner=_runner)
        snapshot = _snapshot((_issue(1183, labels=("triage:bug",)),))

        self.assertEqual([i.item_id for i in provider.advertise(snapshot)], ["bug-1183"])


class TestIssueWithOpenPRIsNotReworked(unittest.TestCase):
    def _pr(self, number: int, body: str) -> PRSummary:
        return PRSummary(number=number, title="fix", labels=(), body=body)

    def test_issue_cited_by_an_open_pr_is_skipped(self):
        provider = BugsProvider(repo="o/r", runner=_runner)
        snapshot = _snapshot(
            (_issue(1163),),
            prs=(self._pr(1876, "## Root cause\n...\n\nCloses #1163.\n"),),
        )

        self.assertEqual(provider.advertise(snapshot), [])

    def test_match_is_case_insensitive(self):
        provider = BugsProvider(repo="o/r", runner=_runner)
        snapshot = _snapshot((_issue(1163),), prs=(self._pr(1876, "closes #1163"),))

        self.assertEqual(provider.advertise(snapshot), [])

    def test_a_different_issue_number_does_not_shadow_this_one(self):
        provider = BugsProvider(repo="o/r", runner=_runner)
        snapshot = _snapshot((_issue(116),), prs=(self._pr(1876, "closes #1163"),))

        self.assertEqual([i.item_id for i in provider.advertise(snapshot)], ["bug-116"])

    def test_a_mention_that_is_not_a_closes_line_does_not_skip(self):
        provider = BugsProvider(repo="o/r", runner=_runner)
        snapshot = _snapshot(
            (_issue(1163),), prs=(self._pr(1876, "related to #1163, does not fix it"),)
        )

        self.assertEqual([i.item_id for i in provider.advertise(snapshot)], ["bug-1163"])


class TestSnapshotCarriesPRBodies(unittest.TestCase):
    """The exclusion above is only reachable if the snapshot reads the body."""

    def test_pr_listing_requests_the_body_field(self):
        from specfuse.agent.state import _read_prs

        seen = []

        def recording(argv, check: bool = False):
            seen.append(list(argv))
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")

        _read_prs(recording, "o/r", limit=10)

        self.assertEqual(len(seen), 1)
        fields = seen[0][seen[0].index("--json") + 1]
        self.assertIn("body", fields.split(","))

    def test_pr_body_reaches_the_summary(self):
        from specfuse.agent.state import _read_prs

        def stub(argv, check: bool = False):
            return SimpleNamespace(
                returncode=0,
                stdout='[{"number": 1, "title": "t", "labels": [], "body": "closes #9"}]',
                stderr="",
            )

        prs, error = _read_prs(stub, "o/r", limit=10)

        self.assertIsNone(error)
        self.assertEqual(prs[0].body, "closes #9")


if __name__ == "__main__":
    unittest.main()
