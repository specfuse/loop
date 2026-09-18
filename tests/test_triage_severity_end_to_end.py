# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Gate 2's `feature_oracle` (FEAT-2026-0113/T06): a full `TriageProvider`
run records severity end to end, on both repository shapes, and never
disturbs a repository's own severity labels.

Each test injects one runner covering every `gh`/`claude` call a run makes --
`gh label list`, the headless classification invocation, `gh issue edit
--body`/`--add-label`, and (empty-namespace branch only) `gh label create`.
"""

from __future__ import annotations

import json
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


def _snapshot(triage_auto: bool = False) -> AgentSnapshot:
    return AgentSnapshot(
        queue=(),
        triage_auto=triage_auto,
        bug_automerge=False,
        bug_lane_limits={},
        issues=(),
        issues_error=None,
        prs=(),
        prs_error=None,
        features=(),
    )


def _row(number: int, title: str = "an issue", body: str = "body text") -> dict:
    return {
        "number": number,
        "title": title,
        "body": body,
        "labels": [],
        "already_structured": False,
        "needs_repair": False,
        "category": None,
        "confidence": "high",
    }


_OWN_LABELS_JSON = json.dumps(
    [
        {"name": "severity:low", "color": "c2e0c6", "description": "Cosmetic or trivial."},
        {"name": "severity:medium", "color": "fbca04", "description": "Degrades a feature."},
        {"name": "severity:high", "color": "d93f0b", "description": "Broken, no workaround."},
        {"name": "severity:critical", "color": "b60205", "description": "Data loss or outage."},
    ]
)


def _make_runner(*, label_list_result, classify_stdout: str):
    """One runner covering every call `TriageProvider.execute` can issue.

    *label_list_result* is either a `(returncode, stdout)` pair for `gh
    label list`, or `None` to make it fail (returncode 1, empty stdout) --
    the degradation path.
    """
    calls: list = []

    def runner(argv, check: bool = False):
        calls.append(list(argv))
        if argv[:3] == ["gh", "label", "list"]:
            if label_list_result is None:
                return SimpleNamespace(returncode=1, stdout="", stderr="gh: not found")
            returncode, stdout = label_list_result
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")
        if argv[:3] == ["gh", "label", "create"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[:3] == ["gh", "issue", "edit"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv and argv[0] == "claude":
            return SimpleNamespace(returncode=0, stdout=classify_stdout, stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner, calls


def _body_edit_calls(calls: list) -> list:
    return [c for c in calls if c[:3] == ["gh", "issue", "edit"] and "--body" in c]


def _label_add_calls(calls: list) -> list:
    return [c for c in calls if c[:3] == ["gh", "issue", "edit"] and "--add-label" in c]


def _label_create_calls(calls: list) -> list:
    return [c for c in calls if c[:3] == ["gh", "label", "create"]]


class SeverityEndToEnd(unittest.TestCase):
    def test_severity_recorded_when_labels_are_defined(self):
        runner, calls = _make_runner(
            label_list_result=(0, _OWN_LABELS_JSON),
            classify_stdout=(
                "<!-- specfuse:triage category=bug confidence=high severity=high -->"
            ),
        )
        provider = TriageProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(101)],
        ):
            items = provider.advertise(_snapshot())
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)

        body_calls = _body_edit_calls(calls)
        label_calls = _label_add_calls(calls)
        self.assertEqual(len(body_calls), 1)
        self.assertIn("severity=high", body_calls[0][body_calls[0].index("--body") + 1])
        self.assertEqual(len(label_calls), 1)
        self.assertIn("severity:high", label_calls[0][label_calls[0].index("--add-label") + 1])

        body_index = calls.index(body_calls[0])
        label_index = calls.index(label_calls[0])
        self.assertLess(body_index, label_index)

    def test_repository_with_its_own_labels_is_not_interfered_with(self):
        runner, calls = _make_runner(
            label_list_result=(0, _OWN_LABELS_JSON),
            classify_stdout=(
                "<!-- specfuse:triage category=bug confidence=high severity=high -->"
            ),
        )
        provider = TriageProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(102)],
        ):
            items = provider.advertise(_snapshot())
            provider.execute(items[0])

        self.assertEqual(_label_create_calls(calls), [])
        for call in calls:
            self.assertNotIn("--description", call)

    def test_severity_recorded_when_repository_defines_none(self):
        runner, calls = _make_runner(
            label_list_result=(0, "[]"),
            classify_stdout=(
                "<!-- specfuse:triage category=bug confidence=high severity=high -->"
            ),
        )
        provider = TriageProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(103)],
        ):
            items = provider.advertise(_snapshot())
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)

        create_calls = _label_create_calls(calls)
        self.assertEqual(len(create_calls), 4)
        for call in create_calls:
            self.assertIn("--force", call)

        body_calls = _body_edit_calls(calls)
        label_calls = _label_add_calls(calls)
        self.assertEqual(len(body_calls), 1)
        self.assertIn("severity=high", body_calls[0][body_calls[0].index("--body") + 1])
        self.assertEqual(len(label_calls), 1)
        self.assertIn("severity:high", label_calls[0][label_calls[0].index("--add-label") + 1])

        last_create_index = max(calls.index(c) for c in create_calls)
        first_label_add_index = min(calls.index(c) for c in label_calls)
        self.assertLess(last_create_index, first_label_add_index)

    def test_listing_and_provisioning_happen_once_per_run(self):
        runner, calls = _make_runner(
            label_list_result=(0, "[]"),
            classify_stdout=(
                "<!-- specfuse:triage category=bug confidence=high severity=high -->"
            ),
        )
        provider = TriageProvider(repo="o/r", runner=runner)

        rows = [_row(201), _row(202), _row(203)]
        with patch("specfuse.agent.providers.triage.list_untriaged", return_value=rows):
            items = provider.advertise(_snapshot())
            for item in items:
                provider.execute(item)

        list_calls = [c for c in calls if c[:3] == ["gh", "label", "list"]]
        self.assertEqual(len(list_calls), 1)

        create_calls = _label_create_calls(calls)
        created_names = [c[3] for c in create_calls]
        self.assertEqual(len(created_names), len(set(created_names)))

    def test_failing_label_listing_degrades_to_todays_write_sequence(self):
        runner, calls = _make_runner(
            label_list_result=None,
            classify_stdout="<!-- specfuse:triage category=bug confidence=high -->",
        )
        provider = TriageProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(301)],
        ):
            items = provider.advertise(_snapshot())
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertEqual(_label_create_calls(calls), [])

        body_calls = _body_edit_calls(calls)
        label_calls = _label_add_calls(calls)
        self.assertEqual(len(body_calls), 1)
        self.assertNotIn("severity=", body_calls[0][body_calls[0].index("--body") + 1])
        self.assertEqual(len(label_calls), 1)
        add_arg = label_calls[0][label_calls[0].index("--add-label") + 1]
        self.assertNotIn("severity:", add_arg)


if __name__ == "__main__":
    unittest.main()
