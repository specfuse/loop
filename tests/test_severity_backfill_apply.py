# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0113/T09's backfill write path: marker amended
before the label is projected, and a decision already carrying a severity
produces no writes at all.
"""

from __future__ import annotations

import unittest

from specfuse.agent.severity_backfill import apply_severity_backfill
from specfuse.loop.triage import render_marker

_REPO = "acme-widget/example"


class _StubRunner:
    def __init__(self, outcomes=None):
        self._outcomes = dict(outcomes or {})
        self.calls = []

    def __call__(self, argv, check=True):
        self.calls.append(list(argv))
        for marker, exc in self._outcomes.items():
            if marker in argv:
                raise exc
        return None


class BackfillApply(unittest.TestCase):
    def test_marker_is_amended_before_the_label_is_added(self):
        body = render_marker("bug", "high") + "\n\nSomething broke."
        runner = _StubRunner()
        decisions = [{"number": 501, "body": body, "severity": "high"}]

        results = apply_severity_backfill(runner, _REPO, decisions)

        body_calls = [c for c in runner.calls if "--body" in c]
        label_calls = [c for c in runner.calls if "--add-label" in c]
        self.assertEqual(len(body_calls), 1)
        self.assertEqual(len(label_calls), 1)
        self.assertLess(
            runner.calls.index(body_calls[0]), runner.calls.index(label_calls[0])
        )

        self.assertEqual(
            body_calls[0],
            ["gh", "issue", "edit", "501", "--repo", _REPO, "--body", body_calls[0][-1]],
        )
        self.assertEqual(
            label_calls[0],
            ["gh", "issue", "edit", "501", "--repo", _REPO, "--add-label", "severity:high"],
        )

        amended_body = body_calls[0][-1]
        self.assertIn("category=bug", amended_body)
        self.assertIn("confidence=high", amended_body)
        self.assertIn("severity=high", amended_body)

        self.assertEqual(results[0]["number"], 501)
        self.assertFalse(results[0]["skipped"])
        self.assertTrue(results[0]["marker_written"])
        self.assertTrue(results[0]["label_written"])

    def test_an_issue_already_carrying_a_severity_is_never_written(self):
        body = render_marker("bug", "high", "high") + "\n\nAlready done."
        runner = _StubRunner()
        decisions = [{"number": 502, "body": body, "severity": "high"}]

        results = apply_severity_backfill(runner, _REPO, decisions)

        self.assertEqual(runner.calls, [])
        self.assertEqual(results[0]["number"], 502)
        self.assertTrue(results[0]["skipped"])
        self.assertFalse(results[0]["marker_written"])
        self.assertFalse(results[0]["label_written"])

    def test_a_failed_label_write_is_recorded_and_never_raised_marker_stays(self):
        body = render_marker("bug", "high") + "\n\nSomething broke."
        runner = _StubRunner(outcomes={"--add-label": RuntimeError("label api down")})
        decisions = [{"number": 503, "body": body, "severity": "high"}]

        results = apply_severity_backfill(runner, _REPO, decisions)

        body_calls = [c for c in runner.calls if "--body" in c]
        label_calls = [c for c in runner.calls if "--add-label" in c]
        self.assertEqual(len(body_calls), 1)
        self.assertEqual(len(label_calls), 1)

        self.assertTrue(results[0]["marker_written"])
        self.assertFalse(results[0]["label_written"])
        self.assertIn("label_error", results[0])

    def test_a_failed_marker_write_leaves_the_label_unwritten(self):
        body = render_marker("bug", "high") + "\n\nSomething broke."
        runner = _StubRunner(outcomes={"--body": RuntimeError("body edit failed")})
        decisions = [{"number": 504, "body": body, "severity": "high"}]

        results = apply_severity_backfill(runner, _REPO, decisions)

        body_calls = [c for c in runner.calls if "--body" in c]
        label_calls = [c for c in runner.calls if "--add-label" in c]
        self.assertEqual(len(body_calls), 1)
        self.assertEqual(len(label_calls), 0)

        self.assertFalse(results[0]["marker_written"])
        self.assertIn("marker_error", results[0])
        self.assertFalse(results[0]["label_written"])


if __name__ == "__main__":
    unittest.main()
