# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The lane finds a PR it opened one second ago.

`_find_pr_for_issue` used `gh pr list --search "closes #N in:body"`. That
hits GitHub's **search index**, which lags object creation by seconds to
minutes -- and the function is called immediately after `/fix-bug` opens the
PR it is looking for.

Observed live on 2026-08-12: issue #1984's fix ran for 17 minutes, opened PR
#2016 with a correct `Closes #1984` body, and the lane reported
`pr_not_found`. The identical search returned that PR minutes later. Cost:
17 minutes of correct work reported as a failure, and a PR left un-evaluated
by every guardrail -- no CI read, no label, no merge decision.

Listing without `--search` reads the repository's pull requests directly
rather than an index built from them, so the just-opened PR is visible. The
same run also exposed the second defect these tests pin: the client-side
match was a bare `f"#{n}"` substring test, so `#198` matched a PR closing
`#1984`. The search query had been masking it.
"""

from __future__ import annotations

import json
import sys
import unittest
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop.bug_lane_run import _find_pr_for_issue, pr_closes_issue

_REPO = "acme-widget/example"


class _Lister:
    """`gh pr list` whose rows are visible only when NOT filtered by search.

    Models the real failure: the search index has not caught up, so a
    `--search` query returns nothing while a plain listing returns the PR.
    """

    def __init__(self, rows, *, search_is_stale: bool = True):
        self.calls: list[list] = []
        self._rows = rows
        self._search_is_stale = search_is_stale

    def __call__(self, argv, check: bool = False):
        self.calls.append(list(argv))
        if argv[:3] != ["gh", "pr", "list"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if "--search" in argv and self._search_is_stale:
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")
        return SimpleNamespace(returncode=0, stdout=json.dumps(self._rows), stderr="")

    @property
    def used_search(self) -> bool:
        return any("--search" in call for call in self.calls)


class TestFindsAJustOpenedPR(unittest.TestCase):
    def test_a_pr_missing_from_the_search_index_is_still_found(self):
        runner = _Lister([{"number": 2016, "body": "## Root cause\n\nCloses #1984"}])

        found = _find_pr_for_issue(runner, _REPO, 1984)

        self.assertEqual(found, 2016)

    def test_the_search_index_is_not_consulted_at_all(self):
        """Not 'search, then fall back' — the index is off the path entirely.

        A fallback would still pay the lag on the first call and would still
        be non-deterministic about which answer wins.
        """
        runner = _Lister([{"number": 2016, "body": "Closes #1984"}])

        _find_pr_for_issue(runner, _REPO, 1984)

        self.assertFalse(runner.used_search, runner.calls)

    def test_the_listing_is_bounded_and_says_so(self):
        runner = _Lister([{"number": 1, "body": "Closes #5"}])

        _find_pr_for_issue(runner, _REPO, 5)

        call = runner.calls[0]
        self.assertIn("--limit", call)
        self.assertTrue(int(call[call.index("--limit") + 1]) >= 100)

    def test_no_matching_pr_still_reports_not_found(self):
        runner = _Lister([{"number": 3, "body": "Closes #999"}])

        self.assertIsNone(_find_pr_for_issue(runner, _REPO, 1984))

    def test_an_unreadable_listing_reports_not_found(self):
        def broken(argv, check: bool = False):
            return SimpleNamespace(returncode=1, stdout="", stderr="boom")

        self.assertIsNone(_find_pr_for_issue(broken, _REPO, 1984))

    def test_unparseable_output_reports_not_found(self):
        def garbage(argv, check: bool = False):
            return SimpleNamespace(returncode=0, stdout="not json", stderr="")

        self.assertIsNone(_find_pr_for_issue(garbage, _REPO, 1984))


class TestTheLinkageMatchIsExact(unittest.TestCase):
    def test_a_shorter_issue_number_does_not_match_a_longer_one(self):
        """`#198` must not match a PR closing `#1984`.

        The old client-side test was `f"#{n}" in body`, so it did. The search
        query masked it: the index only returned plausible candidates, so the
        loose check was never handed a near-miss. Removing the search removes
        the mask, which is why this is pinned here rather than assumed.
        """
        self.assertFalse(pr_closes_issue("Closes #1984", 198))
        self.assertTrue(pr_closes_issue("Closes #1984", 1984))

    def test_a_longer_issue_number_does_not_match_a_shorter_one(self):
        self.assertFalse(pr_closes_issue("Closes #198", 1984))

    def test_a_mention_that_is_not_a_closes_line_does_not_match(self):
        self.assertFalse(pr_closes_issue("related to #1984, does not fix it", 1984))
        self.assertFalse(pr_closes_issue("see #1984", 1984))

    def test_case_and_surrounding_prose_do_not_matter(self):
        for body in ("closes #77", "Closes #77", "CLOSES #77", "...text\n\nCloses #77.\n"):
            with self.subTest(body=body):
                self.assertTrue(pr_closes_issue(body, 77))

    def test_an_empty_or_absent_body_is_not_a_match(self):
        self.assertFalse(pr_closes_issue("", 77))
        self.assertFalse(pr_closes_issue(None, 77))

    def test_selection_and_the_lane_share_one_predicate(self):
        """Two copies of "does this PR close this issue" is how they drift."""
        from specfuse.agent.providers import bugs

        self.assertIs(bugs.pr_closes_issue, pr_closes_issue)


if __name__ == "__main__":
    unittest.main()
