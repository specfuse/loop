# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.loop.triage (FEAT-2026-0045/T01)."""

from __future__ import annotations

import itertools
import json
import unittest
from types import SimpleNamespace

from specfuse.loop.labels import LABEL_REGISTRY
from specfuse.loop.triage import (
    CATEGORIES,
    CONFIDENCES,
    label_for,
    list_untriaged,
    parse_marker,
    render_marker,
    route_for,
)
from specfuse.monitor.issues import _marker as _finding_marker

_REPO = "acme-widget/example"


class _StubRunner:
    """Records every call and replays a scripted sequence of results."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(args)
        return self._results.pop(0)


def _list_result(issues_json):
    return SimpleNamespace(returncode=0, stdout=json.dumps(issues_json), stderr="")


class TestUntriagedScan(unittest.TestCase):
    def test_untriaged_excludes_marked_issue(self):
        marked_body = render_marker("bug", "high") + "\n\nSomething broke."
        runner = _StubRunner([
            _list_result([
                {"number": 1, "title": "marked", "body": marked_body, "labels": []},
                {"number": 2, "title": "unmarked", "body": "No marker here.", "labels": []},
            ])
        ])

        untriaged = list_untriaged(runner, _REPO, limit=50)

        numbers = {row["number"] for row in untriaged}
        self.assertEqual(numbers, {2})

    def test_finding_marker_issue_is_returned_and_flagged(self):
        finding_body = _finding_marker("fp-1") + "\n\nA harvester finding."
        runner = _StubRunner([
            _list_result([
                {"number": 3, "title": "finding", "body": finding_body, "labels": []},
            ])
        ])

        untriaged = list_untriaged(runner, _REPO, limit=50)

        self.assertEqual(len(untriaged), 1)
        self.assertEqual(untriaged[0]["number"], 3)
        self.assertTrue(untriaged[0]["already_structured"])

    def test_plain_issue_is_returned_and_not_flagged(self):
        runner = _StubRunner([
            _list_result([
                {"number": 4, "title": "plain", "body": "just an issue", "labels": []},
            ])
        ])

        untriaged = list_untriaged(runner, _REPO, limit=50)

        self.assertFalse(untriaged[0]["already_structured"])

    def test_no_gh_call_when_stub_never_touched(self):
        runner = _StubRunner([_list_result([])])
        list_untriaged(runner, _REPO, limit=50)
        self.assertEqual(len(runner.calls), 1)
        self.assertIn("gh", runner.calls[0])

    def test_nonzero_returncode_yields_empty_list(self):
        runner = _StubRunner([SimpleNamespace(returncode=1, stdout="", stderr="boom")])
        self.assertEqual(list_untriaged(runner, _REPO, limit=50), [])

    def test_unparseable_stdout_yields_empty_list(self):
        runner = _StubRunner([SimpleNamespace(returncode=0, stdout="not json", stderr="")])
        self.assertEqual(list_untriaged(runner, _REPO, limit=50), [])


class TestRouteFor(unittest.TestCase):
    def test_total_over_categories(self):
        for category in CATEGORIES:
            route = route_for(category)
            self.assertIsInstance(route, str)
            self.assertTrue(route)

    def test_raises_on_non_member(self):
        with self.assertRaises(ValueError):
            route_for("not-a-category")


class TestMarkerRoundTrip(unittest.TestCase):
    def test_round_trips_every_pair(self):
        for category, confidence in itertools.product(CATEGORIES, CONFIDENCES):
            body = render_marker(category, confidence)
            self.assertEqual(parse_marker(body), (category, confidence))

    def test_parse_returns_none_when_absent(self):
        self.assertIsNone(parse_marker("no marker in here"))


class TestLabelProjection(unittest.TestCase):
    def test_every_category_label_is_registered(self):
        registered = {entry.name for entry in LABEL_REGISTRY}
        for category in CATEGORIES:
            self.assertIn(label_for(category), registered)

    def test_raises_on_non_member(self):
        with self.assertRaises(ValueError):
            label_for("not-a-category")


if __name__ == "__main__":
    unittest.main()
