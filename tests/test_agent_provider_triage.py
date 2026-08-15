# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the triage provider (FEAT-2026-0049/T07).

Covers: selection (one `kind="triage"` item per untriaged, non-`already_structured`
issue), the low-confidence-under-`auto` downgrade to `question` (owned by
`apply_triage`, asserted through the injected runner's `gh issue edit`
call), escalation on an out-of-vocabulary classifier category with no `gh
issue edit` issued, `already_structured` rows never advertised, registration
in `default_providers()`, and no git mutation of the provider's own.
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
from specfuse.agent.run import KIND_TRIAGE, STATUS_COMPLETED, STATUS_ESCALATED, default_providers
from specfuse.agent.state import AgentSnapshot


def _recording_runner(calls: list, stdout: str = ""):
    def runner(argv, check: bool = False):
        calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    return runner


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


def _row(
    number: int,
    title: str = "an issue",
    body: str = "body text",
    already_structured: bool = False,
    needs_repair: bool = False,
    category: str = None,
    confidence: str = "high",
    labels: list = None,
):
    return {
        "number": number,
        "title": title,
        "body": body,
        "labels": labels if labels is not None else [],
        "already_structured": already_structured,
        "needs_repair": needs_repair,
        "category": category,
        "confidence": confidence,
    }


class TestTriageProviderAdvertise(unittest.TestCase):
    def test_advertise_returns_triage_item_for_untriaged_issue(self):
        provider = TriageProvider(repo="o/r", runner=_recording_runner([]))

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(4)],
        ):
            items = provider.advertise(_snapshot())

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].kind, KIND_TRIAGE)
        self.assertEqual(items[0].item_id, "triage-4")

    def test_advertise_skips_already_structured_row(self):
        provider = TriageProvider(repo="o/r", runner=_recording_runner([]))

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(5, already_structured=True)],
        ):
            items = provider.advertise(_snapshot())

        self.assertEqual(items, [])


class TestTriageProvider(unittest.TestCase):
    def test_low_confidence_under_auto_becomes_question(self):
        calls = []

        def runner(argv, check: bool = False):
            calls.append(list(argv))
            if argv[:2] == ["gh", "issue"] and "edit" in argv:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            # the headless classification invocation
            return SimpleNamespace(
                returncode=0,
                stdout="<!-- specfuse:triage category=bug confidence=low -->",
                stderr="",
            )

        provider = TriageProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(6, body="some body")],
        ):
            items = provider.advertise(_snapshot(triage_auto=True))
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)

        edit_calls = [c for c in calls if c[:3] == ["gh", "issue", "edit"] and "--body" in c]
        self.assertEqual(len(edit_calls), 1)
        body_arg = edit_calls[0][edit_calls[0].index("--body") + 1]
        self.assertIn("category=question", body_arg)
        self.assertIn("confidence=low", body_arg)

    def test_out_of_vocabulary_category_escalates_without_edit(self):
        calls = []

        def runner(argv, check: bool = False):
            calls.append(list(argv))
            return SimpleNamespace(
                returncode=0,
                stdout="<!-- specfuse:triage category=not-a-real-category confidence=high -->",
                stderr="",
            )

        provider = TriageProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(7)],
        ):
            items = provider.advertise(_snapshot())
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIn("not-a-real-category", outcome.detail)
        self.assertIsNotNone(outcome.escalation)

        edit_calls = [c for c in calls if c[:3] == ["gh", "issue", "edit"]]
        self.assertEqual(edit_calls, [])

    def test_needs_repair_row_skips_classification_and_repairs_label(self):
        calls = []
        provider = TriageProvider(repo="o/r", runner=_recording_runner(calls))

        marked_body = "<!-- specfuse:triage category=bug confidence=high -->\n\nSomething broke."
        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(9, body=marked_body, needs_repair=True, category="bug")],
        ):
            items = provider.advertise(_snapshot())
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertIn("repaired", outcome.detail)

        # no classification invocation and no marker (--body) rewrite --
        # only the label add.
        self.assertFalse(any("--body" in c for c in calls))
        label_calls = [c for c in calls if c[:3] == ["gh", "issue", "edit"] and "--add-label" in c]
        self.assertEqual(len(label_calls), 1)
        self.assertEqual(label_calls[0][label_calls[0].index("--add-label") + 1], "triage:bug")

    def test_needs_repair_row_escalates_when_label_write_fails(self):
        def runner(argv, check: bool = False):
            if "--add-label" in argv:
                raise RuntimeError("label add failed")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        provider = TriageProvider(repo="o/r", runner=runner)

        marked_body = "<!-- specfuse:triage category=bug confidence=high -->\n\nSomething broke."
        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(10, body=marked_body, needs_repair=True, category="bug")],
        ):
            items = provider.advertise(_snapshot())
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIn("label repair failed", outcome.detail)

    def test_default_providers_registers_triage_provider(self):
        providers = default_providers(repo="o/r")

        self.assertIn("TriageProvider", [type(p).__name__ for p in providers])

    def test_execute_issues_no_git_mutation_of_its_own(self):
        calls = []

        def runner(argv, check: bool = False):
            calls.append(list(argv))
            return SimpleNamespace(
                returncode=0,
                stdout="<!-- specfuse:triage category=bug confidence=high -->",
                stderr="",
            )

        provider = TriageProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(8)],
        ):
            items = provider.advertise(_snapshot())
            provider.execute(items[0])

        self.assertFalse(any(c and c[0] == "git" for c in calls))


if __name__ == "__main__":
    unittest.main()
