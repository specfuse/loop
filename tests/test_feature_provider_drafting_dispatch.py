# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FeatureProvider's `needs_drafting` dispatch branch
(FEAT-2026-0050/T07).

Covers: a `draft_ready` answer-gate result dispatches the headless drafting
session through the provider's injected `runner` instead of escalating; a
`fallback` result still escalates with `drafting_answers.fallback_escalation`,
field-for-field, unchanged from before this unit.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.agent.drafting_answers import (
    OUTCOME_DRAFT_READY,
    OUTCOME_FALLBACK,
    AnswerGateResult,
    fallback_escalation,
)
from specfuse.agent.providers.feature import FeatureProvider
from specfuse.agent.run import STATUS_ESCALATED
from specfuse.agent.state import AgentSnapshot

_FEATURE_ID = "FEAT-MISSING"

_DRAFT_READY_RESULT = AnswerGateResult(
    outcome=OUTCOME_DRAFT_READY,
    answers={"roadmap-goal": "Keep the widget catalog in sync."},
)


class _StubResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _RecordingRunner:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def __call__(self, argv, check=False):
        self.calls.append(argv)
        return self._result


def _snapshot(queue: tuple) -> AgentSnapshot:
    return AgentSnapshot(
        queue=queue,
        triage_auto=False,
        bug_automerge=False,
        bug_lane_limits={},
        issues=(),
        issues_error=None,
        prs=(),
        prs_error=None,
        features=(),
    )


class _BaseCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)


class DraftReadyDispatchesTests(_BaseCase):
    def test_draft_ready_invokes_drafting_not_escalation(self):
        runner = _RecordingRunner(_StubResult(0))
        provider = FeatureProvider(
            repo="o/r",
            runner=runner,
            features_root=self.root,
            answer_gate=lambda feature_id: _DRAFT_READY_RESULT,
        )
        items = provider.advertise(_snapshot((_FEATURE_ID,)))
        self.assertEqual(len(items), 1)

        outcome = provider.execute(items[0])

        self.assertNotEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(len(runner.calls), 1)
        self.assertIn("claude", runner.calls[0])


class FallbackDispatchesTests(_BaseCase):
    def test_fallback_still_escalates_matching_fallback_escalation(self):
        runner = _RecordingRunner(_StubResult(0))
        provider = FeatureProvider(
            repo="o/r",
            runner=runner,
            features_root=self.root,
            answer_gate=lambda feature_id: AnswerGateResult(
                outcome=OUTCOME_FALLBACK,
                escalation=fallback_escalation(feature_id),
            ),
        )
        items = provider.advertise(_snapshot((_FEATURE_ID,)))
        self.assertEqual(len(items), 1)

        outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.escalation, fallback_escalation(_FEATURE_ID))
        self.assertEqual(runner.calls, [])

    def test_default_answer_gate_falls_back_with_no_injection(self):
        runner = _RecordingRunner(_StubResult(0))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot((_FEATURE_ID,)))

        outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.escalation, fallback_escalation(_FEATURE_ID))
        self.assertEqual(runner.calls, [])


if __name__ == "__main__":
    unittest.main()
