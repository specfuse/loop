# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for severity on the triage write path (FEAT-2026-0113/T04).

Marker first, label second -- see `triage.py`'s module docstring and
`PLAN.md`'s "Record precedence" section, which this unit extends from
category to severity without changing the shape.
"""

from __future__ import annotations

import unittest

from specfuse.loop.triage import apply_triage, render_marker, severity_label_for

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


class SeverityWrite(unittest.TestCase):
    def test_marker_is_written_before_label(self):
        runner = _StubRunner()
        decisions = [{
            "number": 42,
            "body": "Body text.",
            "category": "bug",
            "confidence": "high",
            "severity": "high",
        }]

        apply_triage(runner, _REPO, decisions)

        body_call_index = next(i for i, c in enumerate(runner.calls) if "--body" in c)
        label_call_index = next(i for i, c in enumerate(runner.calls) if "--add-label" in c)
        self.assertLess(body_call_index, label_call_index)

        body_arg = runner.calls[body_call_index][runner.calls[body_call_index].index("--body") + 1]
        self.assertIn("severity=high", body_arg)

        label_arg = runner.calls[label_call_index][runner.calls[label_call_index].index("--add-label") + 1]
        self.assertIn(severity_label_for("high"), label_arg.split(","))


class RenderMarkerShape(unittest.TestCase):
    def test_two_field_form_is_byte_identical(self):
        self.assertEqual(
            render_marker("bug", "high"),
            "<!-- specfuse:triage category=bug confidence=high -->",
        )

    def test_severity_appended_as_third_field(self):
        self.assertEqual(
            render_marker("bug", "high", "critical"),
            "<!-- specfuse:triage category=bug confidence=high severity=critical -->",
        )


class NoSeverityKeyIsUnaffected(unittest.TestCase):
    def test_argv_sequence_matches_pre_existing_expectation(self):
        runner = _StubRunner()
        decisions = [{"number": 7, "body": "Body text.", "category": "feature", "confidence": "high"}]

        apply_triage(runner, _REPO, decisions)

        self.assertEqual(
            runner.calls,
            [
                ["gh", "issue", "edit", "7", "--repo", _REPO, "--body",
                 "Body text.\n\n<!-- specfuse:triage category=feature confidence=high -->"],
                ["gh", "issue", "edit", "7", "--repo", _REPO, "--add-label", "triage:feature"],
            ],
        )


class SeverityLabelFailureTolerated(unittest.TestCase):
    def test_failed_severity_label_write_recorded_not_raised(self):
        runner = _StubRunner(raise_on=lambda args: "--add-label" in args)
        decisions = [{
            "number": 9,
            "body": "Body text.",
            "category": "wontfix",
            "confidence": "high",
            "severity": "medium",
        }]

        results = apply_triage(runner, _REPO, decisions)

        self.assertTrue(results[0]["marker_written"])
        self.assertFalse(results[0]["label_written"])
        self.assertIn("label_error", results[0])
        self.assertTrue(any("--body" in c and "severity=medium" in c[c.index("--body") + 1] for c in runner.calls))


class SeverityRepairIsIdempotent(unittest.TestCase):
    def test_marked_issue_missing_severity_label_gets_it_added(self):
        runner = _StubRunner()
        marked_body = "Body text.\n\n<!-- specfuse:triage category=bug confidence=high severity=high -->"
        decisions = [{
            "number": 796,
            "body": marked_body,
            "category": "bug",
            "confidence": "high",
            "labels": [{"name": "triage:bug"}],
        }]

        results = apply_triage(runner, _REPO, decisions)

        self.assertTrue(results[0]["skipped"])
        self.assertTrue(results[0]["label_written"])
        self.assertFalse(any("--body" in c for c in runner.calls))
        add_label_call = next(c for c in runner.calls if "--add-label" in c)
        added = add_label_call[add_label_call.index("--add-label") + 1].split(",")
        self.assertIn(severity_label_for("high"), added)

    def test_marked_issue_with_severity_label_already_present_does_nothing(self):
        runner = _StubRunner()
        marked_body = "Body text.\n\n<!-- specfuse:triage category=bug confidence=high severity=high -->"
        decisions = [{
            "number": 248,
            "body": marked_body,
            "category": "bug",
            "confidence": "high",
            "labels": [{"name": "triage:bug"}, {"name": severity_label_for("high")}],
        }]

        results = apply_triage(runner, _REPO, decisions)

        self.assertTrue(results[0]["skipped"])
        self.assertFalse(runner.calls)


if __name__ == "__main__":
    unittest.main()
