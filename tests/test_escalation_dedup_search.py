# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`emit_escalation`'s dedup search must use a term GitHub can match (#2548).

`_find_existing_issue` passed the whole correlation marker --
`<!-- specfuse:escalation id=... -->` -- as the `--search` term. GitHub's
issue-search tokenizer never matches that raw HTML comment, so the query
returned zero rows on a queue that demonstrably held five copies, the
find-then-create seam fell through to `gh issue create`, and the
`needs-human` queue grew by one issue per run: 10 open issues for 2 real
escalations, burying the genuine ones.

The marker is not the problem and neither is the exact-body check -- that
check is what stops a nested ID (`feature-FEAT-2026-0058-g1`) being taken
for its parent (`feature-FEAT-2026-0058`), since a token search returns
both. Only the search *term* was wrong. These tests pin both halves: a
tokenizable term goes out, and the exact-marker filter still decides.

Existing coverage stubbed the runner to return a match regardless of what
was searched for and never asserted the argv, so zero recall against the
real API was invisible to the suite. The argv assertion below is the guard
that was missing.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.loop.escalation import (
    NEEDS_HUMAN_LABEL,
    _correlation_marker,
    _find_existing_issue,
)


class _StubRunner:
    """Records every call and replays a scripted sequence of results."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(args)
        return self._results.pop(0)


def _search_result(issues):
    return SimpleNamespace(returncode=0, stdout=json.dumps(issues), stderr="")


def _search_term(argv):
    return argv[argv.index("--search") + 1]


class TestDedupSearchTermIsMatchable(unittest.TestCase):
    def test_the_search_term_does_not_carry_the_raw_html_comment(self):
        # The regression itself: an HTML comment is not a searchable token,
        # so sending one guarantees zero rows and a duplicate issue.
        runner = _StubRunner([_search_result([])])

        _find_existing_issue(runner, "acme-widget/repo", "feature-FEAT-2026-0081")

        term = _search_term(runner.calls[0])
        self.assertNotIn("<!--", term)
        self.assertNotIn("-->", term)
        self.assertNotIn("specfuse:escalation", term)

    def test_the_search_term_carries_the_correlation_id(self):
        runner = _StubRunner([_search_result([])])

        _find_existing_issue(runner, "acme-widget/repo", "feature-FEAT-2026-0081")

        self.assertIn("feature-FEAT-2026-0081", _search_term(runner.calls[0]))

    def test_the_query_still_scopes_to_open_needs_human_issues(self):
        runner = _StubRunner([_search_result([])])

        _find_existing_issue(runner, "acme-widget/repo", "feature-FEAT-2026-0081")

        argv = runner.calls[0]
        self.assertIn(NEEDS_HUMAN_LABEL, argv)
        self.assertIn("--state", argv)
        self.assertEqual(argv[argv.index("--state") + 1], "open")


class TestTheExactMarkerFilterStillDecides(unittest.TestCase):
    def test_an_issue_carrying_the_marker_is_returned(self):
        cid = "feature-FEAT-2026-0081"
        runner = _StubRunner([
            _search_result([{"number": 2381, "body": f"{_correlation_marker(cid)}\n\nbody"}])
        ])

        self.assertEqual(
            _find_existing_issue(runner, "acme-widget/repo", cid), "2381")

    def test_a_nested_id_is_not_mistaken_for_its_parent(self):
        # A token search for the parent returns the `-g1` child too; only the
        # exact-marker body check keeps them apart. Without it, broadening the
        # search term would trade duplicate issues for wrong-issue reuse.
        parent = "feature-FEAT-2026-0058"
        child_body = f"{_correlation_marker(parent + '-g1')}\n\nbody"
        runner = _StubRunner([_search_result([{"number": 2541, "body": child_body}])])

        self.assertIsNone(_find_existing_issue(runner, "acme-widget/repo", parent))

    def test_a_search_hit_with_no_marker_at_all_is_ignored(self):
        runner = _StubRunner([
            _search_result([{"number": 99, "body": "mentions feature-FEAT-2026-0081 in prose"}])
        ])

        self.assertIsNone(
            _find_existing_issue(runner, "acme-widget/repo", "feature-FEAT-2026-0081"))


if __name__ == "__main__":
    unittest.main()
