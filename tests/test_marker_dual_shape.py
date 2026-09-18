# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the dual-shape triage marker reader (FEAT-2026-0113/T01)."""

from __future__ import annotations

import ast
import itertools
import pathlib
import re
import unittest

from specfuse.loop.triage import (
    CATEGORIES,
    CONFIDENCES,
    parse_marker,
    parse_marker_fields,
    render_marker,
)

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_TESTS_DIR = _REPO_ROOT / "tests"
_CHANGELOG_PATH = _REPO_ROOT / "CHANGELOG.md"
_THIS_FILE = pathlib.Path(__file__).resolve()

_MARKER_SCAN_RE = re.compile(r"<!-- specfuse:triage [^>]*-->")


def _string_literals(path: pathlib.Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value


def _shipped_markers_from_tests():
    """Every well-formed `specfuse:triage` marker literal in `tests/`.

    Skips this file itself -- its own malformed fixtures are deliberately
    unparseable and belong to `FailsClosed`, not the shipped-shape corpus.
    Python concatenates adjacent string literals at parse time, so scanning
    `ast.Constant` values (rather than raw source text) sees a marker split
    across lines as the single string it renders to.
    """
    markers = set()
    for path in sorted(_TESTS_DIR.glob("*.py")):
        if path.resolve() == _THIS_FILE:
            continue
        for literal in _string_literals(path):
            for found in _MARKER_SCAN_RE.findall(literal):
                if parse_marker(found) is not None:
                    markers.add(found)
    return markers


def _changelog_marker_template():
    text = _CHANGELOG_PATH.read_text(encoding="utf-8")
    match = re.search(r"`(<!-- specfuse:triage[^`]*-->)`", text)
    if match is None:
        raise AssertionError(
            "CHANGELOG.md no longer documents the specfuse:triage marker "
            "contract at the format this corpus expects"
        )
    return match.group(1)


def _shipped_markers_from_changelog():
    template = _changelog_marker_template()
    return {
        template.format(category=category, confidence=confidence)
        for category, confidence in itertools.product(CATEGORIES, CONFIDENCES)
    }


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

    def test_an_unterminated_comment_reads_as_absent(self):
        bodies = [
            "<!-- specfuse:triage category=bug confidence=high",
            "<!-- specfuse:triage category=bug confidence=high --",
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.assertIsNone(parse_marker(body))
                self.assertIsNone(parse_marker_fields(body))


class MarkerCorpus(unittest.TestCase):
    """FEAT-2026-0113/T02: the reader tolerates every marker shape shipped,
    not just the ones this suite imagined."""

    def test_every_shipped_marker_shape_parses(self):
        corpus = {}
        for category, confidence in itertools.product(CATEGORIES, CONFIDENCES):
            corpus[render_marker(category, confidence)] = (category, confidence)
        for marker in _shipped_markers_from_tests():
            corpus[marker] = parse_marker(marker)
        for marker in _shipped_markers_from_changelog():
            corpus[marker] = parse_marker(marker)

        self.assertTrue(corpus, "corpus assembly found no marker literals")
        for marker, expected in corpus.items():
            with self.subTest(marker=marker):
                self.assertEqual(parse_marker(marker), expected)

    def test_marker_in_a_realistic_issue_body_parses(self):
        body = (
            "Thanks for filing this!\n\n"
            "<!-- some-other-tool:note reviewed=true -->\n\n"
            "We looked into it and it does look like a bug.\n\n"
            "<!-- specfuse:triage category=bug confidence=high -->\n\n"
            "Routing to the fix-bug lane.\n"
        )
        self.assertEqual(parse_marker(body), ("bug", "high"))

    def test_an_unrelated_html_comment_alone_is_never_a_marker(self):
        body = (
            "Some prose.\n\n"
            "<!-- some-other-tool:note reviewed=true -->\n\n"
            "More prose.\n"
        )
        self.assertIsNone(parse_marker(body))

    def test_three_field_shape_round_trips_through_the_two_field_contract(self):
        for category, confidence in itertools.product(CATEGORIES, CONFIDENCES):
            body = (
                f"<!-- specfuse:triage category={category} "
                f"confidence={confidence} severity=critical -->"
            )
            self.assertEqual(
                parse_marker_fields(body),
                {
                    "category": category,
                    "confidence": confidence,
                    "severity": "critical",
                },
            )
            self.assertEqual(parse_marker(body), (category, confidence))


class RoundTrip(unittest.TestCase):
    def test_render_then_parse_is_identity_for_every_pair(self):
        for category, confidence in itertools.product(CATEGORIES, CONFIDENCES):
            with self.subTest(category=category, confidence=confidence):
                self.assertEqual(
                    parse_marker(render_marker(category, confidence)),
                    (category, confidence),
                )


if __name__ == "__main__":
    unittest.main()
