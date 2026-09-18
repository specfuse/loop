# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the dual-shape triage marker reader (FEAT-2026-0113/T01)."""

from __future__ import annotations

import unittest

from specfuse.loop.triage import parse_marker, parse_marker_fields, render_marker


class DualShapeMarker(unittest.TestCase):
    def test_a_three_field_marker_parses(self):
        body = (
            "<!-- specfuse:triage category=bug confidence=high "
            "severity=critical -->"
        )
        self.assertEqual(parse_marker(body), ("bug", "high"))
        self.assertEqual(
            parse_marker_fields(body),
            {"category": "bug", "confidence": "high", "severity": "critical"},
        )

    def test_two_field_marker_still_parses(self):
        body = "<!-- specfuse:triage category=bug confidence=high -->"
        self.assertEqual(parse_marker(body), ("bug", "high"))
        self.assertEqual(
            parse_marker_fields(body), {"category": "bug", "confidence": "high"}
        )

    def test_no_marker_returns_none(self):
        self.assertIsNone(parse_marker("no marker here"))
        self.assertIsNone(parse_marker_fields("no marker here"))

    def test_render_marker_still_two_field(self):
        self.assertEqual(
            render_marker("bug", "high"),
            "<!-- specfuse:triage category=bug confidence=high -->",
        )


class FailsClosed(unittest.TestCase):
    def test_a_marker_missing_a_required_field_reads_as_absent(self):
        bodies = [
            "<!-- specfuse:triage category=bug -->",
            "<!-- specfuse:triage confidence=high -->",
            "<!-- specfuse:triage category=bug confidence= -->",
            "<!-- specfuse:triage category= confidence=high -->",
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.assertIsNone(parse_marker(body))


if __name__ == "__main__":
    unittest.main()
