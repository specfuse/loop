# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Triage never adds a second, contradicting `severity:*` label (#3521).

clabonte/generator#2532 carried a maintainer's `severity:low`; a triage pass
added `severity:high` beside it, and the bug lane dispatched on whichever label
`read_severity_label` happened to read first. Per #3360 the person's label is
the source: when an issue already carries any `severity:*` label, triage writes
its own verdict to the marker only, leaves the labels alone, and reports the
disagreement.
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.triage import TriageProvider
from specfuse.agent.run import STATUS_COMPLETED
from specfuse.agent.state import AgentSnapshot
from specfuse.loop.triage import apply_triage

_REPO = "acme-widget/example"


class _StubRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def added_labels(self):
        added = []
        for call in self.calls:
            if "--add-label" in call:
                added.extend(call[call.index("--add-label") + 1].split(","))
        return added


def _labels(*names):
    return [{"name": name} for name in names]


class FreshTriageLeavesAHumanSeverityLabelAlone(unittest.TestCase):
    def test_contradicting_severity_label_is_not_added(self):
        runner = _StubRunner()
        rows = apply_triage(runner, _REPO, [{
            "number": 2532, "body": "Body.", "category": "bug",
            "confidence": "high", "severity": "high",
            "labels": _labels("severity:low"),
        }])

        self.assertNotIn("severity:high", runner.added_labels())
        self.assertIn("triage:bug", runner.added_labels())
        self.assertEqual(rows[0]["severity_conflict"], ["severity:low"])

    def test_out_of_vocabulary_human_label_also_wins(self):
        runner = _StubRunner()
        rows = apply_triage(runner, _REPO, [{
            "number": 2833, "body": "Body.", "category": "bug",
            "confidence": "high", "severity": "high",
            "labels": _labels("severity:major"),
        }])

        self.assertNotIn("severity:high", runner.added_labels())
        self.assertEqual(rows[0]["severity_conflict"], ["severity:major"])

    def test_agreeing_label_is_not_a_conflict(self):
        runner = _StubRunner()
        rows = apply_triage(runner, _REPO, [{
            "number": 5, "body": "Body.", "category": "bug",
            "confidence": "high", "severity": "high",
            "labels": _labels("severity:high"),
        }])

        self.assertNotIn("severity_conflict", rows[0])

    def test_no_severity_label_still_gets_triage_verdict(self):
        runner = _StubRunner()
        rows = apply_triage(runner, _REPO, [{
            "number": 6, "body": "Body.", "category": "bug",
            "confidence": "high", "severity": "high",
            "labels": _labels("triage:bug"),
        }])

        self.assertIn("severity:high", runner.added_labels())
        self.assertNotIn("severity_conflict", rows[0])


class MarkedIssueRepairLeavesAHumanSeverityLabelAlone(unittest.TestCase):
    def test_marker_severity_does_not_add_a_second_label(self):
        runner = _StubRunner()
        body = ("Body.\n\n<!-- specfuse:triage category=bug confidence=high "
                "severity=high -->")
        rows = apply_triage(runner, _REPO, [{
            "number": 2532, "body": body, "category": "bug",
            "labels": _labels("severity:low"),
        }])

        self.assertNotIn("severity:high", runner.added_labels())
        self.assertIn("triage:bug", runner.added_labels())
        self.assertEqual(rows[0]["severity_conflict"], ["severity:low"])


def _snapshot():
    return AgentSnapshot(
        queue=(), triage_auto=False, bug_automerge=False, bug_lane_limits={},
        issues=(), issues_error=None, prs=(), prs_error=None, features=(),
    )


class ProviderPassesLabelsAndReportsTheConflict(unittest.TestCase):
    def test_provider_reports_conflict_and_writes_no_second_label(self):
        calls = []

        def runner(argv, check=False):
            calls.append(list(argv))
            if argv[:3] == ["gh", "issue", "edit"]:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(
                returncode=0,
                stdout=("<!-- specfuse:triage category=bug confidence=high "
                        "severity=high -->"),
                stderr="",
            )

        provider = TriageProvider(repo="o/r", runner=runner)
        row = {
            "number": 2532, "title": "t", "body": "Body.",
            "labels": _labels("severity:low"),
            "already_structured": False, "needs_repair": False,
            "category": None, "confidence": "high",
        }
        with patch("specfuse.agent.providers.triage.list_untriaged",
                   return_value=[row]), \
             patch.object(TriageProvider, "_rubric_for_run",
                          return_value={"high": "h", "low": "l"}), \
             patch.object(TriageProvider, "_projection_for_run",
                          return_value={}):
            items = provider.advertise(_snapshot())
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        added = []
        for call in calls:
            if "--add-label" in call:
                added.extend(call[call.index("--add-label") + 1].split(","))
        self.assertFalse(
            [label for label in added if label.startswith("severity:")],
            f"no severity label may be added beside severity:low, got {added!r}",
        )
        self.assertIn("severity:low", outcome.detail)


if __name__ == "__main__":
    unittest.main()
