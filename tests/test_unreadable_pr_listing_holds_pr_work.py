# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""An unreadable PR listing holds back PR-opening work under a cap (#3412).

`max_open_prs` read a failed PR listing as zero open PRs, so with a readable
issue listing and an unreadable PR listing the run dispatched with the cap
silently off -- the guard an operator set to bound unattended PR creation.
#3411 made that visible; the decision on #3412 is to enforce the cap the way
reaching it already does: the PR-opening kinds wait, everything else runs, and
a refresh that reads the listing releases them.

No cap declared, nothing changes: there is no ceiling to enforce.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from tests.test_max_open_prs import _POLICY, _KindProvider, _run

_FAIL = SimpleNamespace(returncode=1, stdout="", stderr="gh: HTTP 502")

_POLICY_NO_CAP = _POLICY.replace("  max_open_prs: {cap}\n", "")


class _Runner:
    """`gh pr list` fails for the first *pr_failures* calls, then reads empty."""

    def __init__(self, pr_failures):
        self.pr_failures = pr_failures

    def __call__(self, argv, check=False):
        argv = list(argv)
        if argv[:3] == ["gh", "pr", "list"]:
            if self.pr_failures > 0:
                self.pr_failures -= 1
                return _FAIL
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")
        if argv[:3] == ["gh", "issue", "list"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps([]), stderr="")
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")


class TestUnreadablePrListingUnderACap(unittest.TestCase):
    def test_pr_opening_kinds_wait_and_the_run_says_why(self):
        bugs = _KindProvider("bug", "bug-7")
        autofix = _KindProvider("finding-autofix", "autofix-3")
        reports = []

        _run(_Runner(pr_failures=99), (bugs, autofix), _POLICY.format(cap="5"), reports)

        self.assertEqual(bugs.executed, [])
        self.assertEqual(autofix.executed, [])
        self.assertTrue(
            any("max_open_prs" in line and "could not be read" in line
                and "not starting" in line for line in reports),
            f"the hold must be reported, got {reports!r}",
        )

    def test_work_that_opens_no_pr_still_runs(self):
        triage = _KindProvider("triage", "triage-7")
        reports = []

        _run(_Runner(pr_failures=99), (triage,), _POLICY.format(cap="5"), reports)

        self.assertEqual(triage.executed, ["triage-7"])

    def test_a_listing_read_later_in_the_run_releases_the_hold(self):
        # Opening read fails; the refresh after the triage item reads it.
        triage = _KindProvider("triage", "triage-7")
        bugs = _KindProvider("bug", "bug-7")
        reports = []

        _run(_Runner(pr_failures=1), (bugs, triage), _POLICY.format(cap="5"), reports)

        self.assertEqual(triage.executed, ["triage-7"])
        self.assertEqual(bugs.executed, ["bug-7"])

    def test_without_a_cap_nothing_is_held(self):
        bugs = _KindProvider("bug", "bug-7")
        reports = []

        _run(_Runner(pr_failures=99), (bugs,), _POLICY_NO_CAP, reports)

        self.assertEqual(bugs.executed, ["bug-7"])


if __name__ == "__main__":
    unittest.main()
