# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for `specfuse.monitor.autofix_run` (FEAT-2026-0042/T05)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from unittest.mock import Mock

from specfuse.monitor.autofix import DECLINE, FIRE, ROUTE_TO_HUMAN
from specfuse.monitor.autofix_run import run_autofix
from specfuse.monitor.autofix_state import AUTOFIX_FAILED_LABEL
from specfuse.monitor.diagnosis import Diagnosis, render

_SOURCE_PATH = Path(__file__).resolve().parent.parent / "specfuse" / "monitor" / "autofix_run.py"
_SOURCE_TEXT = _SOURCE_PATH.read_text(encoding="utf-8")

_REPO = "acme/widget"
_ISSUE_NUMBER = 42
_FINGERPRINT = "abc123fingerprint"
_COMPONENT = "web"


def _finding_body(fingerprint: str = _FINGERPRINT) -> str:
    return f"<!-- specfuse:finding fingerprint={fingerprint} -->\nSomething broke."


def _diagnosis_comment(*, confidence: float = 1.0, fix_scope: str = "small") -> dict:
    body = render(
        Diagnosis(
            root_cause="root",
            evidence="evidence",
            candidate_fix="candidate",
            confidence=confidence,
            fix_scope=fix_scope,
        )
    )
    return {"body": body}


def _monitoring_config(dial: str) -> dict:
    return {"components": [{"name": _COMPONENT, "autofix": dial}]}


class _FakeResult:
    def __init__(self, returncode: int, stdout: str) -> None:
        self.returncode = returncode
        self.stdout = stdout


class FakeRunner:
    """Records every call; answers `gh` reads/writes and the fired-session
    launch from canned data. `order` is a shared list callers can also
    append `invoker:*` markers to, so tests can assert call ordering across
    both the runner and the invoker."""

    def __init__(self, *, comments, attempted_rows=None, order=None) -> None:
        self.calls: list[list[str]] = []
        self.order = order if order is not None else []
        self._comments = comments
        self._attempted_rows = attempted_rows if attempted_rows is not None else [
            {"number": _ISSUE_NUMBER, "body": _finding_body()}
        ]

    def __call__(self, argv, check=False):
        self.calls.append(list(argv))
        if argv[:3] == ["gh", "issue", "view"]:
            return _FakeResult(
                0, json.dumps({"body": _finding_body(), "comments": self._comments})
            )
        if argv[:3] == ["gh", "issue", "list"]:
            return _FakeResult(0, json.dumps(self._attempted_rows))
        if argv[:3] == ["gh", "issue", "edit"] and "--body" in argv:
            self.order.append("runner:record_attempt")
            row = self._attempted_rows[0]
            row["body"] = row["body"] + "\n\n<!-- specfuse:autofix-attempt fingerprint={} at=1.0 -->\n".format(
                _FINGERPRINT
            )
            return _FakeResult(0, "")
        if argv[:3] == ["gh", "issue", "edit"] and "--add-label" in argv:
            self.order.append("runner:apply_label")
            return _FakeResult(0, "")
        self.order.append("runner:invoke_session")
        return _FakeResult(0, "completed")


def _make_invoker(*, outcome="completed", order=None):
    order = order if order is not None else []
    invoker = Mock(spec=["build_invocation", "classify_outcome"])

    def build_invocation(issue_number, repo, working_dir):
        order.append("invoker:build_invocation")
        return (["claude", "-p", "--model", "sonnet"], "PROMPT")

    def classify_outcome(result_text):
        order.append("invoker:classify_outcome")
        return outcome

    invoker.build_invocation.side_effect = build_invocation
    invoker.classify_outcome.side_effect = classify_outcome
    return invoker


class TestAutofixRun(unittest.TestCase):
    def test_dial_off_never_invokes_the_fixer(self):
        runner = FakeRunner(comments=[_diagnosis_comment(confidence=1.0, fix_scope="small")])
        invoker = _make_invoker()

        result = run_autofix(
            runner=runner,
            invoker=invoker,
            repo=_REPO,
            finding_issue_number=_ISSUE_NUMBER,
            monitoring_config=_monitoring_config("off"),
            component=_COMPONENT,
        )

        self.assertEqual(result.decision, DECLINE)
        self.assertIsNone(result.outcome)
        invoker.build_invocation.assert_not_called()
        invoker.classify_outcome.assert_not_called()
        writing_calls = [
            call for call in runner.calls
            if call[:3] == ["gh", "issue", "edit"]
        ]
        self.assertEqual(writing_calls, [])

    def test_fire_records_attempt_before_invoking(self):
        order: list[str] = []
        runner = FakeRunner(
            comments=[_diagnosis_comment(confidence=1.0, fix_scope="small")], order=order
        )
        invoker = _make_invoker(outcome="completed", order=order)

        result = run_autofix(
            runner=runner,
            invoker=invoker,
            repo=_REPO,
            finding_issue_number=_ISSUE_NUMBER,
            monitoring_config=_monitoring_config("on"),
            component=_COMPONENT,
        )

        self.assertEqual(result.decision, FIRE)
        self.assertEqual(result.outcome, "completed")
        record_index = order.index("runner:record_attempt")
        build_index = order.index("invoker:build_invocation")
        self.assertLess(record_index, build_index)

    def test_no_diagnosis_comment_declines_as_unreadable(self):
        runner = FakeRunner(comments=[])
        invoker = _make_invoker()

        result = run_autofix(
            runner=runner,
            invoker=invoker,
            repo=_REPO,
            finding_issue_number=_ISSUE_NUMBER,
            monitoring_config=_monitoring_config("on"),
            component=_COMPONENT,
        )

        self.assertEqual(result.decision, DECLINE)
        invoker.build_invocation.assert_not_called()

    def test_unreadable_finding_issue_declines(self):
        calls: list[list[str]] = []

        def flaky_runner(argv, check=False):
            calls.append(list(argv))
            if argv[:3] == ["gh", "issue", "view"]:
                return _FakeResult(1, "")
            return _FakeResult(0, "[]")

        result = run_autofix(
            runner=flaky_runner,
            invoker=_make_invoker(),
            repo=_REPO,
            finding_issue_number=_ISSUE_NUMBER,
            monitoring_config=_monitoring_config("on"),
            component=_COMPONENT,
        )

        self.assertEqual(result.decision, DECLINE)

    def test_malformed_components_config_declines(self):
        runner = FakeRunner(comments=[_diagnosis_comment()])
        result = run_autofix(
            runner=runner,
            invoker=_make_invoker(),
            repo=_REPO,
            finding_issue_number=_ISSUE_NUMBER,
            monitoring_config={"components": "not-a-list"},
            component=_COMPONENT,
        )
        self.assertEqual(result.decision, DECLINE)

    def test_route_to_human_calls_neither_invoker_nor_record_attempt(self):
        runner = FakeRunner(comments=[_diagnosis_comment(confidence=1.0, fix_scope="large")])
        invoker = _make_invoker()

        result = run_autofix(
            runner=runner,
            invoker=invoker,
            repo=_REPO,
            finding_issue_number=_ISSUE_NUMBER,
            monitoring_config=_monitoring_config("on"),
            component=_COMPONENT,
        )

        self.assertEqual(result.decision, ROUTE_TO_HUMAN)
        self.assertIsNone(result.outcome)
        invoker.build_invocation.assert_not_called()
        invoker.classify_outcome.assert_not_called()
        writing_calls = [
            call for call in runner.calls
            if call[:3] == ["gh", "issue", "edit"] and "--body" in call
        ]
        self.assertEqual(writing_calls, [])

    def test_completed_outcome_applies_no_failure_label(self):
        runner = FakeRunner(comments=[_diagnosis_comment(confidence=1.0, fix_scope="small")])
        invoker = _make_invoker(outcome="completed")

        result = run_autofix(
            runner=runner,
            invoker=invoker,
            repo=_REPO,
            finding_issue_number=_ISSUE_NUMBER,
            monitoring_config=_monitoring_config("on"),
            component=_COMPONENT,
        )

        self.assertEqual(result.outcome, "completed")
        label_calls = [
            call for call in runner.calls
            if call[:3] == ["gh", "issue", "edit"] and "--add-label" in call
        ]
        self.assertEqual(label_calls, [])

    def test_refused_outcome_applies_failure_label(self):
        runner = FakeRunner(comments=[_diagnosis_comment(confidence=1.0, fix_scope="small")])
        invoker = _make_invoker(outcome="refused")

        result = run_autofix(
            runner=runner,
            invoker=invoker,
            repo=_REPO,
            finding_issue_number=_ISSUE_NUMBER,
            monitoring_config=_monitoring_config("on"),
            component=_COMPONENT,
        )

        self.assertEqual(result.outcome, "refused")
        label_calls = [
            call for call in runner.calls
            if call[:3] == ["gh", "issue", "edit"] and "--add-label" in call
        ]
        self.assertEqual(len(label_calls), 1)
        self.assertIn(AUTOFIX_FAILED_LABEL, label_calls[0])

    def test_could_not_proceed_outcome_applies_failure_label(self):
        runner = FakeRunner(comments=[_diagnosis_comment(confidence=1.0, fix_scope="small")])
        invoker = _make_invoker(outcome="could_not_proceed")

        result = run_autofix(
            runner=runner,
            invoker=invoker,
            repo=_REPO,
            finding_issue_number=_ISSUE_NUMBER,
            monitoring_config=_monitoring_config("on"),
            component=_COMPONENT,
        )

        self.assertEqual(result.outcome, "could_not_proceed")
        label_calls = [
            call for call in runner.calls
            if call[:3] == ["gh", "issue", "edit"] and "--add-label" in call
        ]
        self.assertEqual(len(label_calls), 1)
        self.assertIn(AUTOFIX_FAILED_LABEL, label_calls[0])

    def test_failure_label_constant_never_spelled_as_a_literal(self):
        self.assertNotIn("auto-fix-attempted-failed", _SOURCE_TEXT)

    def test_no_merge_or_push_calls(self):
        pattern = re.compile(r"pr merge|--auto|--admin|push")
        self.assertIsNone(pattern.search(_SOURCE_TEXT))

    def test_shells_out_to_nothing_directly(self):
        pattern = re.compile(r"subprocess|requests|urllib|os\.system")
        self.assertIsNone(pattern.search(_SOURCE_TEXT))


if __name__ == "__main__":
    unittest.main()
