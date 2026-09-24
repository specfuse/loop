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


class AliasedSchemeWritesTheRepositorysOwnLabel(unittest.TestCase):
    """End to end for #3353: a repository whose severity labels are its own
    words gets those words written back, not the vocabulary spelling.

    The unit tests for `severity_label_projection` prove the mapping; this
    proves the wiring, which is where the defect actually lived -- the
    projection existed nowhere and `apply_severity_backfill` wrote
    `severity_label_for(value)` unconditionally.
    """

    ALIASED_LABELS = [
        {"name": "severity:major", "description": "Wrong behavior."},
        {"name": "severity:minor", "description": "Cosmetic."},
    ]

    def test_the_label_written_is_the_repositorys_word(self):
        candidates = [_candidate(1)]
        runner, calls = _make_runner(
            candidates=candidates,
            label_rows=self.ALIASED_LABELS,
            claude_answers={1: _marker(1, "bug", "high", "high")},
        )

        report = run_backfill(runner, _REPO, apply=True)

        self.assertEqual({"high", "low"}, set(report["rubric"]))

        label_calls = [c for c in _issue_edit_calls(calls) if "--add-label" in c]
        self.assertEqual(1, len(label_calls))
        written = label_calls[0][label_calls[0].index("--add-label") + 1]
        self.assertEqual("severity:major", written)

    def test_the_marker_still_records_the_vocabulary_value(self):
        candidates = [_candidate(1)]
        runner, calls = _make_runner(
            candidates=candidates,
            label_rows=self.ALIASED_LABELS,
            claude_answers={1: _marker(1, "bug", "high", "high")},
        )

        run_backfill(runner, _REPO, apply=True)

        body_calls = [c for c in _issue_edit_calls(calls) if "--body" in c]
        self.assertEqual(1, len(body_calls))
        body = body_calls[0][body_calls[0].index("--body") + 1]
        self.assertIn("severity=high", body)

    def test_the_listing_is_still_read_exactly_once(self):
        candidates = [_candidate(1)]
        runner, calls = _make_runner(
            candidates=candidates,
            label_rows=self.ALIASED_LABELS,
            claude_answers={1: _marker(1, "bug", "high", "high")},
        )

        run_backfill(runner, _REPO, apply=True)

        self.assertEqual(1, len(_label_list_calls(calls)))


class HumanAppliedSeverityIsReconciledNotReDecided(unittest.TestCase):
    """End to end for #3360: the live collision the close named.

    `#1902`, `#1895` and `#1893` carry `severity:minor` / `severity:major`
    applied by a person, with no `severity=` in their markers. The selection
    predicate reads the marker, so they are candidates. They were masked only
    because that repository's scheme yielded a one-entry rubric -- and #3355
    removed the mask, so a run today would classify them and write a second
    severity label beside the human's.
    """

    ALIASED_LABELS = [
        {"name": "severity:critical", "description": "Drop everything."},
        {"name": "severity:major", "description": "Wrong behavior."},
        {"name": "severity:minor", "description": "Cosmetic."},
    ]

    def _labelled_candidate(self, number: int, *label_names) -> dict:
        issue = _candidate(number)
        issue["labels"] = [{"name": n} for n in label_names]
        return issue

    def test_no_classification_session_is_spent_on_a_labelled_issue(self):
        runner, calls = _make_runner(
            candidates=[self._labelled_candidate(1902, "severity:minor")],
            label_rows=self.ALIASED_LABELS,
            claude_answers={1902: _marker(1902, "bug", "high", "critical")},
        )

        run_backfill(runner, _REPO, apply=True)

        self.assertEqual(
            [], _claude_calls(calls),
            "the label already states the severity — classifying it spends "
            "money to produce an opinion that must then be discarded",
        )

    def test_the_marker_records_the_humans_severity(self):
        runner, calls = _make_runner(
            candidates=[self._labelled_candidate(1902, "severity:minor")],
            label_rows=self.ALIASED_LABELS,
            claude_answers={1902: _marker(1902, "bug", "high", "critical")},
        )

        report = run_backfill(runner, _REPO, apply=True)

        body_calls = [c for c in _issue_edit_calls(calls) if "--body" in c]
        self.assertEqual(1, len(body_calls))
        body = body_calls[0][body_calls[0].index("--body") + 1]
        self.assertIn("severity=low", body)
        self.assertNotIn("severity=critical", body)
        self.assertEqual("label", report["rows"][0]["severity_source"])

    def test_no_second_label_is_written_beside_the_humans(self):
        runner, calls = _make_runner(
            candidates=[self._labelled_candidate(1902, "severity:minor")],
            label_rows=self.ALIASED_LABELS,
            claude_answers={1902: _marker(1902, "bug", "high", "critical")},
        )

        run_backfill(runner, _REPO, apply=True)

        self.assertEqual(
            [], [c for c in _issue_edit_calls(calls) if "--add-label" in c],
            "the label is the source of this severity and is already on the "
            "issue; writing one can only duplicate or contradict it",
        )

    def test_contradictory_labels_leave_the_issue_alone(self):
        runner, calls = _make_runner(
            candidates=[self._labelled_candidate(
                7, "severity:minor", "severity:critical")],
            label_rows=self.ALIASED_LABELS,
            claude_answers={7: _marker(7, "bug", "high", "critical")},
        )

        report = run_backfill(runner, _REPO, apply=True)

        self.assertEqual([], _issue_edit_calls(calls))
        self.assertEqual([], _claude_calls(calls))
        self.assertFalse(report["rows"][0]["classified"])
        self.assertIn("more than one", report["rows"][0]["skipped_reason"])

    def test_an_unlabelled_issue_is_still_classified(self):
        # The reconciliation path must not swallow the feature's actual job.
        runner, calls = _make_runner(
            candidates=[_candidate(42)],
            label_rows=self.ALIASED_LABELS,
            claude_answers={42: _marker(42, "bug", "high", "critical")},
        )

        report = run_backfill(runner, _REPO, apply=True)

        self.assertEqual(1, len(_claude_calls(calls)))
        self.assertEqual("classifier", report["rows"][0]["severity_source"])
        self.assertEqual("critical", report["rows"][0]["severity"])


if __name__ == "__main__":
    unittest.main()
