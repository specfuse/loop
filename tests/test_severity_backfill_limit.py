# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0113/T08H: `--limit` bounds candidates, not the
`gh issue list` listing window, and a zero-candidate run reports why.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.agent.severity_backfill import _print_run_report, run_backfill
from specfuse.loop.triage import list_severity_backfill_candidates, render_marker

_REPO = "acme-widget/example"

_SEVERITY_LABELS = [
    {"name": "severity:low", "description": "Low impact."},
    {"name": "severity:medium", "description": "Medium impact."},
    {"name": "severity:high", "description": "High impact."},
    {"name": "severity:critical", "description": "Critical impact."},
]


def _issue(number: int, *, candidate: bool) -> dict:
    if candidate:
        body = render_marker("bug", "high") + f"\n\nIssue {number} body."
    else:
        body = f"Issue {number} body, no triage marker."
    return {"number": number, "title": f"issue {number}", "body": body, "labels": []}


def _make_listing_runner(issues: list):
    """Records each `gh issue list` argv and answers with the newest-first
    prefix its `--limit` asks for, capped at what `issues` holds -- the same
    "listing has no cursor, later pages re-ask for more" shape `gh` itself
    has."""
    calls: list = []

    def runner(argv, check: bool = False):
        calls.append(list(argv))
        limit = int(argv[argv.index("--limit") + 1])
        return SimpleNamespace(
            returncode=0, stdout=json.dumps(issues[:limit]), stderr=""
        )

    return runner, calls


class LimitBoundsCandidates(unittest.TestCase):
    def test_limit_counts_candidates_not_listed_issues(self):
        issues = [_issue(n, candidate=(n % 10 == 0)) for n in range(1, 51)]
        runner, calls = _make_listing_runner(issues)

        candidates = list_severity_backfill_candidates(runner, _REPO, limit=3)

        self.assertEqual(len(candidates), 3)
        self.assertEqual([c["number"] for c in candidates], [10, 20, 30])
        # Every issue among the first 3 listed carries no marker -- a
        # listing-window reading of `limit` would have returned 0.
        first_three = {i["number"] for i in issues[:3]}
        self.assertFalse(set(c["number"] for c in candidates) & first_three)

    def test_pages_until_limit_found_without_shrinking_the_window(self):
        # 250 open issues; the only candidates sit at newest-order positions
        # 210-214 (5 issues), well past a single 100-issue page.
        issues = [
            _issue(n, candidate=(210 <= n <= 214)) for n in range(1, 251)
        ]
        runner, calls = _make_listing_runner(issues)

        candidates = list_severity_backfill_candidates(runner, _REPO, limit=3)

        self.assertEqual([c["number"] for c in candidates], [210, 211, 212])
        limits_asked = [int(argv[argv.index("--limit") + 1]) for argv in calls]
        # Paged, growing -- never bound to the candidate limit (3).
        self.assertEqual(limits_asked, [100, 200, 300])

    def test_exhaustion_terminates_with_fewer_candidates_than_limit(self):
        issues = [_issue(n, candidate=(n in (3, 7))) for n in range(1, 11)]
        runner, calls = _make_listing_runner(issues)

        candidates = list_severity_backfill_candidates(runner, _REPO, limit=5)

        self.assertEqual([c["number"] for c in candidates], [3, 7])
        # A single page: 10 open issues is fewer than the 100-issue window.
        self.assertEqual(len(calls), 1)


class ZeroCandidateRunReportsWhy(unittest.TestCase):
    def test_a_zero_candidate_run_reports_why(self):
        issues = [_issue(n, candidate=False) for n in range(1, 6)]
        runner, calls = _make_listing_runner(issues)
        real_runner = runner

        def full_runner(argv, check: bool = False):
            if argv[:3] == ["gh", "label", "list"]:
                return SimpleNamespace(
                    returncode=0, stdout=json.dumps(_SEVERITY_LABELS), stderr=""
                )
            return real_runner(argv, check=check)

        report = run_backfill(full_runner, _REPO, limit=5)

        self.assertIsNotNone(report["reason"])
        self.assertIn(_REPO, report["reason"])
        self.assertIn("5", report["reason"])
        self.assertEqual(report["rows"], [])

        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _print_run_report(report)
        self.assertIn(_REPO, buf.getvalue())
        self.assertIn("5", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
