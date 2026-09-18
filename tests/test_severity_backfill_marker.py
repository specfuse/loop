# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0113/T08's backfill selection and marker amendment."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.loop.escalation import CATEGORY_LABELS
from specfuse.loop.triage import (
    amend_marker_severity,
    list_severity_backfill_candidates,
    parse_marker_fields,
    render_marker,
)
from specfuse.monitor.issues import _marker as _finding_marker

_REPO = "acme-widget/example"


class _StubRunner:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(args)
        return self._results.pop(0)


def _list_result(issues_json):
    return SimpleNamespace(returncode=0, stdout=json.dumps(issues_json), stderr="")


class BackfillSelection(unittest.TestCase):
    def test_marked_issue_without_severity_is_a_candidate(self):
        candidate_body = render_marker("bug", "high") + "\n\nSomething broke."
        already_severity_body = render_marker("bug", "high", "high") + "\n\nAlready done."
        runner = _StubRunner([
            _list_result([
                {"number": 1, "title": "candidate", "body": candidate_body, "labels": []},
                {"number": 2, "title": "has severity", "body": already_severity_body, "labels": []},
            ])
        ])

        result = list_severity_backfill_candidates(runner, _REPO, limit=10)

        numbers = [row["number"] for row in result]
        self.assertIn(1, numbers)
        self.assertNotIn(2, numbers)

    def test_excludes_harvester_finding_issue(self):
        body = render_marker("bug", "high") + "\n\n" + _finding_marker("fingerprint-1")
        runner = _StubRunner([
            _list_result([{"number": 3, "title": "finding", "body": body, "labels": []}])
        ])

        result = list_severity_backfill_candidates(runner, _REPO, limit=10)

        self.assertEqual([], result)

    def test_excludes_agent_escalation_issue(self):
        escalation_label = next(iter(CATEGORY_LABELS))
        body = render_marker("bug", "high") + "\n\nEscalated."
        runner = _StubRunner([
            _list_result([
                {
                    "number": 4,
                    "title": "escalated",
                    "body": body,
                    "labels": [{"name": escalation_label}],
                }
            ])
        ])

        result = list_severity_backfill_candidates(runner, _REPO, limit=10)

        self.assertEqual([], result)

    def test_excludes_marker_naming_unknown_category(self):
        body = "<!-- specfuse:triage category=not-a-category confidence=high -->\n\nBody."
        runner = _StubRunner([
            _list_result([{"number": 5, "title": "unknown category", "body": body, "labels": []}])
        ])

        result = list_severity_backfill_candidates(runner, _REPO, limit=10)

        self.assertEqual([], result)

    def test_excludes_issue_with_no_marker(self):
        runner = _StubRunner([
            _list_result([{"number": 6, "title": "no marker", "body": "Plain body.", "labels": []}])
        ])

        result = list_severity_backfill_candidates(runner, _REPO, limit=10)

        self.assertEqual([], result)

    def test_limit_bounds_the_result_not_the_listing(self):
        # `limit` bounds how many candidates come back, not the `gh issue
        # list` window -- [FEAT-2026-0113/T08H/limit-bounds-candidates].
        body = render_marker("bug", "high") + "\n\nSomething broke."
        runner = _StubRunner([
            _list_result([{"number": i, "title": "candidate", "body": body, "labels": []} for i in range(5)])
        ])

        result = list_severity_backfill_candidates(runner, _REPO, limit=2)

        self.assertEqual(len(result), 2)
        self.assertIn("--limit", runner.calls[0])
        limit_index = runner.calls[0].index("--limit")
        self.assertNotEqual(runner.calls[0][limit_index + 1], "2")

    def test_issues_a_single_listing_call(self):
        body = render_marker("bug", "high") + "\n\nSomething broke."
        runner = _StubRunner([
            _list_result([{"number": 1, "title": "candidate", "body": body, "labels": []}])
        ])

        list_severity_backfill_candidates(runner, _REPO, limit=10)

        self.assertEqual(1, len(runner.calls))
        self.assertIn("issue", runner.calls[0])
        self.assertIn("list", runner.calls[0])


class AmendMarkerSeverity(unittest.TestCase):
    def test_replaces_marker_in_place_keeping_category_and_confidence(self):
        body = render_marker("bug", "low") + "\n\nSomething broke."

        result = amend_marker_severity(body, "high")

        fields = parse_marker_fields(result)
        self.assertEqual("bug", fields["category"])
        self.assertEqual("low", fields["confidence"])
        self.assertEqual("high", fields["severity"])
        self.assertEqual(1, result.count("specfuse:triage"))
        self.assertIn("Something broke.", result)

    def test_renders_through_render_marker(self):
        body = render_marker("feature", "high") + "\n\nBody."

        result = amend_marker_severity(body, "low")

        self.assertEqual(
            render_marker("feature", "high", "low") + "\n\nBody.",
            result,
        )

    def test_returns_body_unchanged_when_no_marker(self):
        body = "No marker here."

        self.assertEqual(body, amend_marker_severity(body, "high"))

    def test_returns_body_unchanged_when_severity_already_present(self):
        body = render_marker("bug", "high", "high") + "\n\nBody."

        self.assertEqual(body, amend_marker_severity(body, "low"))


if __name__ == "__main__":
    unittest.main()
