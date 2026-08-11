# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.loop.triage.apply_triage (FEAT-2026-0045/T02)."""

from __future__ import annotations

import unittest

from specfuse.loop.triage import CATEGORIES, apply_triage, label_for, parse_marker, route_for

_REPO = "acme-widget/example"


class _StubRunner:
    """Records every call; raises on calls matching a scripted predicate."""

    def __init__(self, raise_on=None):
        self.calls = []
        self._raise_on = raise_on

    def __call__(self, args, check=True):
        self.calls.append(args)
        if self._raise_on is not None and self._raise_on(args):
            raise RuntimeError("gh call failed")
        return None


class TestAutoDial(unittest.TestCase):
    def test_auto_dial_skips_low_confidence(self):
        runner = _StubRunner()
        decisions = [{"number": 1, "body": "Something broke.", "category": "bug", "confidence": "low"}]

        results = apply_triage(runner, _REPO, decisions, auto=True)

        self.assertEqual(results[0]["category"], "question")
        self.assertEqual(results[0]["route"], "needs-human")
        self.assertTrue(results[0]["marker_written"])

    def test_auto_false_applies_decision_as_given(self):
        runner = _StubRunner()
        decisions = [{"number": 1, "body": "Something broke.", "category": "bug", "confidence": "low"}]

        results = apply_triage(runner, _REPO, decisions, auto=False)

        self.assertEqual(results[0]["category"], "bug")


class TestWriteOrder(unittest.TestCase):
    def test_marker_precedes_label_for_same_issue(self):
        runner = _StubRunner()
        decisions = [{"number": 7, "body": "Body text.", "category": "feature", "confidence": "high"}]

        apply_triage(runner, _REPO, decisions)

        body_call_index = next(i for i, c in enumerate(runner.calls) if "--body" in c)
        label_call_index = next(i for i, c in enumerate(runner.calls) if "--add-label" in c)
        self.assertLess(body_call_index, label_call_index)


class TestLabelFailureTolerated(unittest.TestCase):
    def test_label_failure_recorded_not_raised(self):
        runner = _StubRunner(raise_on=lambda args: "--add-label" in args)
        decisions = [{"number": 9, "body": "Body text.", "category": "wontfix", "confidence": "high"}]

        results = apply_triage(runner, _REPO, decisions)

        self.assertTrue(results[0]["marker_written"])
        self.assertFalse(results[0]["label_written"])


class TestMarkedButUnlabelledIsRepaired(unittest.TestCase):
    """Issue #1163: a marker-written/label-failed issue must become
    labelled once the label exists, not stay permanently skipped."""

    def test_marked_issue_missing_label_retries_label_only(self):
        runner = _StubRunner()
        marked_body = "Body text.\n\n<!-- specfuse:triage category=bug confidence=high -->"
        decisions = [{
            "number": 796,
            "body": marked_body,
            "category": "bug",
            "confidence": "high",
            "labels": [{"name": "bug"}],
        }]

        results = apply_triage(runner, _REPO, decisions)

        self.assertTrue(results[0]["skipped"])
        self.assertTrue(results[0]["label_written"])
        self.assertTrue(any("--add-label" in c for c in runner.calls))
        self.assertFalse(any("--body" in c for c in runner.calls))

    def test_marked_issue_with_label_already_present_does_nothing(self):
        runner = _StubRunner()
        marked_body = "Body text.\n\n<!-- specfuse:triage category=bug confidence=high -->"
        decisions = [{
            "number": 248,
            "body": marked_body,
            "category": "bug",
            "confidence": "high",
            "labels": [{"name": "triage:bug"}],
        }]

        results = apply_triage(runner, _REPO, decisions)

        self.assertTrue(results[0]["skipped"])
        self.assertFalse(runner.calls)


class TestIdempotency(unittest.TestCase):
    def test_second_call_over_marked_issue_performs_no_write(self):
        runner = _StubRunner()
        decisions = [{"number": 3, "body": "Body text.", "category": "duplicate", "confidence": "high"}]

        apply_triage(runner, _REPO, decisions)
        self.assertEqual(len(runner.calls), 2)

        marked_body = next(c[c.index("--body") + 1] for c in runner.calls if "--body" in c)
        self.assertIsNotNone(parse_marker(marked_body))

        runner2 = _StubRunner()
        decisions2 = [{
            "number": 3,
            "body": marked_body,
            "category": "duplicate",
            "confidence": "high",
            "labels": [{"name": label_for("duplicate")}],
        }]
        apply_triage(runner2, _REPO, decisions2)
        self.assertEqual(len(runner2.calls), 0)


class TestInvalidCategory(unittest.TestCase):
    def test_unknown_category_raises_before_write(self):
        runner = _StubRunner()
        decisions = [{"number": 5, "body": "Body text.", "category": "not-a-category", "confidence": "high"}]

        with self.assertRaises(ValueError):
            apply_triage(runner, _REPO, decisions)

        self.assertEqual(len(runner.calls), 0)


class TestRouteAndLabelStayConsistent(unittest.TestCase):
    def test_every_category_still_routes_and_labels(self):
        for category in CATEGORIES:
            self.assertTrue(route_for(category))
            self.assertTrue(label_for(category))


if __name__ == "__main__":
    unittest.main()
