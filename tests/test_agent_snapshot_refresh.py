# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Work one provider creates must be visible to the next, in the same run (#3338).

`run_agent` gathered `AgentSnapshot` once, before the dispatch loop, and handed
that same value to every provider on every pass. `BugsProvider.advertise` reads
`snapshot.issues` and only advertises an issue whose body already carried a
`bug` triage marker at snapshot time; `TriageProvider.execute` writes that
marker mid-run. So a run on 2026-09-17 triaged 72 issues -- 55 of them to `bug`
-- and dispatched the bug lane against none of them.

The tests here drive a real `run_agent` against a runner whose `gh issue list`
output changes when the triage double executes, with providers that read the
snapshot exactly as the real ones do. The first is the reported defect; the
rest pin the guard rails the refresh needs so a transient listing failure
cannot blank a lane mid-run.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.run import (
    ActionItem,
    ActionOutcome,
    STATUS_COMPLETED,
    _format_summary,
    run_agent,
)


class _FakeClock:
    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class _IssueListRunner:
    """A `gh` runner whose open-issue listing is mutable mid-run.

    Only `gh issue list` and `gh pr list` are answered; every other argv gets
    an empty-JSON success, which is all the snapshot reads.
    """

    def __init__(self, issues):
        self.issues = list(issues)
        self.fail_issue_list = False
        self.issue_list_calls = 0

    def __call__(self, argv, check=False):
        argv = list(argv)
        if argv[:3] == ["gh", "issue", "list"]:
            self.issue_list_calls += 1
            if self.fail_issue_list:
                return SimpleNamespace(returncode=1, stdout="", stderr="gh: rate limited")
            import json as _json

            return SimpleNamespace(returncode=0, stdout=_json.dumps(self.issues), stderr="")
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    def mark_bug(self, number):
        for issue in self.issues:
            if issue["number"] == number:
                issue["body"] = "<!-- specfuse:triage category=bug confidence=high -->"


class _TriageDouble:
    """Advertises from the live listing, as `TriageProvider` does, and writes
    the marker on execute."""

    def __init__(self, runner):
        self._runner = runner
        self.executed = []

    def advertise(self, snapshot):
        return tuple(
            ActionItem(item_id=f"triage-{issue.number}", kind="triage",
                       summary=issue.title, queue_key=None)
            for issue in snapshot.issues
            if issue.triage_category is None
        )

    def execute(self, item):
        number = int(item.item_id.split("-")[-1])
        self.executed.append(number)
        self._runner.mark_bug(number)
        return ActionOutcome(status=STATUS_COMPLETED, detail=f"issue #{number} triaged as bug")

    def reconcile(self, item, outcome):
        return None


class _BugsDouble:
    """Advertises exactly what `BugsProvider.advertise` advertises: issues whose
    snapshot body already carries a `bug` marker."""

    def __init__(self):
        self.executed = []

    def advertise(self, snapshot):
        return tuple(
            ActionItem(item_id=f"bug-{issue.number}", kind="bug",
                       summary=issue.title, queue_key=None)
            for issue in snapshot.issues
            if issue.triage_category == "bug"
        )

    def execute(self, item):
        self.executed.append(int(item.item_id.split("-")[-1]))
        return ActionOutcome(status=STATUS_COMPLETED, detail="fixed")

    def reconcile(self, item, outcome):
        return None


def _run(runner, providers, *, reports=None, max_items=None):
    with tempfile.TemporaryDirectory() as tmp:
        specfuse_dir = Path(tmp) / ".specfuse"
        specfuse_dir.mkdir()
        features_root = specfuse_dir / "features"
        features_root.mkdir()
        return run_agent(
            specfuse_dir=specfuse_dir,
            repo="acme/widget",
            runner=runner,
            providers=providers,
            policy_path=str(specfuse_dir / "agent-policy.yml"),
            features_root=features_root,
            clock=_FakeClock(),
            max_items=max_items,
            reporter=(reports.append if reports is not None else None),
        )


class TriagedInThisRunReachesTheBugLane(unittest.TestCase):

    def test_an_issue_triaged_mid_run_is_dispatched_in_the_same_run(self):
        runner = _IssueListRunner([
            {"number": 11, "title": "crash on save", "labels": [], "body": "no marker"},
        ])
        triage, bugs = _TriageDouble(runner), _BugsDouble()

        summary = _run(runner, (bugs, triage))

        self.assertEqual(triage.executed, [11])
        self.assertEqual(
            bugs.executed, [11],
            "the issue triaged as `bug` by an earlier item in this same run "
            "must be visible to the bug lane before the run drains",
        )
        self.assertEqual(summary.items_completed, 2)


class RefreshIsGuarded(unittest.TestCase):

    def test_a_failed_listing_keeps_the_previous_issues_rather_than_blanking(self):
        runner = _IssueListRunner([
            {"number": 11, "title": "crash on save", "labels": [],
             "body": "<!-- specfuse:triage category=bug confidence=high -->"},
            {"number": 12, "title": "typo", "labels": [],
             "body": "<!-- specfuse:triage category=bug confidence=high -->"},
        ])
        bugs = _BugsDouble()

        class _FailAfterFirst:
            def __init__(self, runner):
                self._runner = runner
                self._seen = 0

            def advertise(self, snapshot):
                return ()

            def execute(self, item):  # pragma: no cover - never selected
                raise AssertionError

            def reconcile(self, item, outcome):  # pragma: no cover
                raise AssertionError

        reports = []
        # The listing starts failing once the first bug item has run; the
        # second must still be dispatched from the issues already in hand.
        original_execute = bugs.execute

        def execute(item):
            outcome = original_execute(item)
            runner.fail_issue_list = True
            return outcome

        bugs.execute = execute

        summary = _run(runner, (bugs, _FailAfterFirst(runner)), reports=reports)

        self.assertEqual(
            sorted(bugs.executed), [11, 12],
            "a listing failure mid-run must not blank the lane's remaining work",
        )
        self.assertEqual(summary.items_completed, 2)
        self.assertTrue(
            any("refresh" in line and "gh: rate limited" in line for line in reports),
            f"the failed refresh must be reported, got {reports!r}",
        )

    def test_refresh_does_not_resurrect_an_already_handled_item(self):
        runner = _IssueListRunner([
            {"number": 11, "title": "crash on save", "labels": [],
             "body": "<!-- specfuse:triage category=bug confidence=high -->"},
        ])
        bugs = _BugsDouble()

        summary = _run(runner, (bugs,), max_items=5)

        self.assertEqual(bugs.executed, [11])
        self.assertEqual(summary.items_attempted, 1)


class AnUndispatchedTriageIsReported(unittest.TestCase):
    """The issue's minimum ask: a triage-only run must not read as a bug lane
    that declined everything."""

    def test_a_bug_triaged_but_never_dispatched_is_named_in_the_summary(self):
        runner = _IssueListRunner([
            {"number": 11, "title": "crash on save", "labels": [], "body": "no marker"},
        ])
        triage, bugs = _TriageDouble(runner), _BugsDouble()
        reports = []

        # One item only, so the marker is written and the run stops before the
        # bug lane ever gets a pass.
        summary = _run(runner, (bugs, triage), reports=reports, max_items=1)

        self.assertEqual(triage.executed, [11])
        self.assertEqual(bugs.executed, [])
        self.assertEqual(summary.newly_triaged_bugs_undispatched, (11,))
        self.assertIn("re-run to fix them: #11", _format_summary(summary))
        self.assertTrue(
            any("re-run to fix them" in line for line in reports),
            f"the run must say so as it finishes, got {reports!r}",
        )

    def test_a_dispatched_bug_is_not_reported_as_outstanding(self):
        runner = _IssueListRunner([
            {"number": 11, "title": "crash on save", "labels": [], "body": "no marker"},
        ])
        triage, bugs = _TriageDouble(runner), _BugsDouble()

        summary = _run(runner, (bugs, triage))

        self.assertEqual(summary.newly_triaged_bugs_undispatched, ())
        self.assertNotIn("re-run to fix them", _format_summary(summary))

    def test_a_bug_marked_before_the_run_is_never_counted_as_newly_triaged(self):
        runner = _IssueListRunner([
            {"number": 11, "title": "crash on save", "labels": [],
             "body": "<!-- specfuse:triage category=bug confidence=high -->"},
        ])
        bugs = _BugsDouble()

        summary = _run(runner, (bugs,), max_items=0)

        self.assertEqual(bugs.executed, [])
        self.assertEqual(summary.newly_triaged_bugs_undispatched, ())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
