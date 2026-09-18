# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0113/T10's backfill run shape: the rubric read once
per run, each selected candidate classified through the same
`triage_invoke.classify_severity` a fresh triage uses, and nothing written
unless the caller passes `apply=True`.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.agent.severity_backfill import run_backfill
from specfuse.loop.triage import render_marker

_REPO = "acme-widget/example"

_SEVERITY_LABELS = [
    {"name": "severity:low", "description": "Low impact."},
    {"name": "severity:medium", "description": "Medium impact."},
    {"name": "severity:high", "description": "High impact."},
    {"name": "severity:critical", "description": "Critical impact."},
]

_OWN_SCHEME_LABELS = [
    {"name": "severity:p0", "description": "Drop everything."},
    {"name": "severity:p1", "description": "Next up."},
]


def _candidate(number: int) -> dict:
    body = render_marker("bug", "high") + f"\n\nIssue {number} body."
    return {"number": number, "title": f"issue {number}", "body": body, "labels": []}


def _claude_envelope(text: str) -> str:
    return json.dumps({"result": text, "total_cost_usd": 0.0, "usage": {}})


def _make_runner(*, candidates, label_rows, claude_answers):
    """`claude_answers` maps issue number -> the classification session's
    raw text. `label_rows` is what `gh label list` returns."""
    calls: list = []

    def runner(argv, check: bool = False):
        calls.append(list(argv))
        if argv[:3] == ["gh", "label", "list"]:
            return SimpleNamespace(
                returncode=0, stdout=json.dumps(label_rows), stderr=""
            )
        if argv[:3] == ["gh", "issue", "list"]:
            return SimpleNamespace(
                returncode=0, stdout=json.dumps(candidates), stderr=""
            )
        if argv[0] == "claude":
            # The prompt is the final positional argument; the issue number
            # is embedded in it (`triage_invoke.build_invocation`).
            prompt = argv[-1]
            for number, text in claude_answers.items():
                if f"Issue number: {number}" in prompt:
                    return SimpleNamespace(
                        returncode=0, stdout=_claude_envelope(text), stderr=""
                    )
            return SimpleNamespace(returncode=0, stdout=_claude_envelope(""), stderr="")
        if argv[:3] == ["gh", "issue", "edit"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner, calls


def _label_list_calls(calls: list) -> list:
    return [c for c in calls if c[:3] == ["gh", "label", "list"]]


def _issue_list_calls(calls: list) -> list:
    return [c for c in calls if c[:3] == ["gh", "issue", "list"]]


def _claude_calls(calls: list) -> list:
    return [c for c in calls if c and c[0] == "claude"]


def _issue_edit_calls(calls: list) -> list:
    return [c for c in calls if c[:3] == ["gh", "issue", "edit"]]


def _marker(number: int, category: str, confidence: str, severity: str = None) -> str:
    if severity is None:
        return f"<!-- specfuse:triage category={category} confidence={confidence} -->"
    return (
        f"<!-- specfuse:triage category={category} confidence={confidence} "
        f"severity={severity} -->"
    )


class BackfillRun(unittest.TestCase):
    def test_rubric_is_read_once_and_each_candidate_is_classified(self):
        self.test_listing_and_provisioning_happen_once_per_run()

    def test_listing_and_provisioning_happen_once_per_run(self):
        candidates = [_candidate(1), _candidate(2), _candidate(3)]
        claude_answers = {
            1: _marker(1, "bug", "high", "high"),
            2: _marker(2, "bug", "high", "medium"),
            3: _marker(3, "bug", "high", "low"),
        }
        runner, calls = _make_runner(
            candidates=candidates,
            label_rows=_SEVERITY_LABELS,
            claude_answers=claude_answers,
        )

        report = run_backfill(runner, _REPO, apply=True)

        self.assertEqual(1, len(_label_list_calls(calls)))
        self.assertEqual(3, len(_claude_calls(calls)))

        edit_calls = _issue_edit_calls(calls)
        body_calls = [c for c in edit_calls if "--body" in c]
        label_calls = [c for c in edit_calls if "--add-label" in c]
        self.assertEqual(3, len(body_calls))
        self.assertEqual(3, len(label_calls))

        self.assertEqual(3, len(report["rows"]))
        self.assertTrue(all(row["classified"] for row in report["rows"]))

    def test_a_low_confidence_or_out_of_rubric_answer_writes_nothing(self):
        candidates = [_candidate(1), _candidate(2), _candidate(3)]
        claude_answers = {
            1: _marker(1, "bug", "high", "not-a-severity"),  # outside rubric
            2: _marker(2, "bug", "low", "high"),  # confidence not high
            3: "no marker here at all",  # unparseable
        }
        runner, calls = _make_runner(
            candidates=candidates,
            label_rows=_SEVERITY_LABELS,
            claude_answers=claude_answers,
        )

        report = run_backfill(runner, _REPO, apply=True)

        self.assertEqual(0, len(_issue_edit_calls(calls)))
        self.assertEqual(3, len(report["rows"]))
        self.assertTrue(all(not row["classified"] for row in report["rows"]))
        self.assertTrue(all(row["severity"] is None for row in report["rows"]))

    def test_an_empty_rubric_makes_the_run_a_no_op_on_failed_listing(self):
        candidates = [_candidate(1)]
        runner, calls = _make_runner(
            candidates=candidates,
            label_rows=[],
            claude_answers={},
        )

        def failing_runner(argv, check=False):
            if argv[:3] == ["gh", "label", "list"]:
                return SimpleNamespace(returncode=1, stdout="", stderr="rate limited")
            return runner(argv, check=check)

        report = run_backfill(failing_runner, _REPO, apply=True)

        self.assertEqual({}, report["rubric"])
        self.assertEqual([], report["candidates"])
        self.assertEqual([], report["rows"])
        self.assertIsNotNone(report["reason"])

    def test_an_empty_rubric_makes_the_run_a_no_op_on_out_of_vocabulary_scheme(self):
        candidates = [_candidate(1)]
        runner, calls = _make_runner(
            candidates=candidates,
            label_rows=_OWN_SCHEME_LABELS,
            claude_answers={},
        )

        report = run_backfill(runner, _REPO, apply=True)

        self.assertEqual({}, report["rubric"])
        self.assertEqual([], report["rows"])
        self.assertIsNotNone(report["reason"])
        self.assertEqual(0, len(_claude_calls(calls)))
        self.assertEqual(0, len(_issue_edit_calls(calls)))

    def test_without_apply_nothing_is_written(self):
        candidates = [_candidate(1), _candidate(2), _candidate(3)]
        claude_answers = {
            1: _marker(1, "bug", "high", "high"),
            2: _marker(2, "bug", "high", "medium"),
            3: _marker(3, "bug", "high", "low"),
        }
        runner, calls = _make_runner(
            candidates=candidates,
            label_rows=_SEVERITY_LABELS,
            claude_answers=claude_answers,
        )

        report = run_backfill(runner, _REPO, apply=False)

        self.assertEqual(0, len(_issue_edit_calls(calls)))
        self.assertEqual(3, len(report["rows"]))
        self.assertTrue(all(row["classified"] for row in report["rows"]))

    def test_backfill_creates_no_labels_against_a_repository_with_its_own_scheme(self):
        candidates = [_candidate(1)]
        claude_answers = {1: _marker(1, "bug", "high", "p0")}
        # p0/p1 fall outside agent_policy.SEVERITY_VALUES, so the rubric is
        # empty and the run is a no-op -- no claude invocation, and
        # certainly no label creation.
        runner, calls = _make_runner(
            candidates=candidates,
            label_rows=_OWN_SCHEME_LABELS,
            claude_answers=claude_answers,
        )

        run_backfill(runner, _REPO, apply=True)

        label_create_calls = [
            c for c in calls if c[:3] == ["gh", "label", "create"]
        ]
        self.assertEqual([], label_create_calls)


if __name__ == "__main__":
    unittest.main()
