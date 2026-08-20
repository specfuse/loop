#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the drafting interview's D1 answer gate
(FEAT-2026-0050/T03)."""

from __future__ import annotations

import unittest
from pathlib import Path

from specfuse.agent.drafting_answers import (
    MAX_ROUNDS,
    OUTCOME_DRAFT_READY,
    OUTCOME_FALLBACK,
    evaluate_answer_gate,
    fallback_escalation,
    next_round_questions,
    parse_reply_answers,
    reask_allowed,
)
from specfuse.agent.drafting_questions import Question
from specfuse.agent.providers.feature import FeatureProvider
from specfuse.agent.run import STATUS_ESCALATED
from specfuse.agent.state import AgentSnapshot

_QUESTIONS = (
    Question(
        id="roadmap-goal",
        kind="elicitation",
        text="In one sentence, what user-observable outcome should this feature produce?",
    ),
    Question(
        id="scope-boundary",
        kind="elicitation",
        text="What is explicitly OUT of scope for this feature?",
    ),
    Question(
        id="surfaces-touched",
        kind="elicitation",
        text="Which surfaces does this feature touch?",
    ),
    Question(
        id="autonomy-level",
        kind="decision",
        text="What autonomy level should this feature default to?",
        options=("auto", "review", "supervised"),
        recommendation="review",
    ),
    Question(
        id="gate-shape",
        kind="decision",
        text="Should this feature draft as a single gate or multiple gates?",
        options=("single gate", "multi-gate"),
        recommendation="single gate",
    ),
)

_FEATURE_ID = "FEAT-2026-9999"


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


class UnansweredElicitationForcesFallbackTests(unittest.TestCase):
    def test_unanswered_elicitation_forces_fallback(self):
        answers = {
            # scope-boundary and surfaces-touched left unanswered.
            "roadmap-goal": "Operators answer async, drafting proceeds later.",
            "autonomy-level": "auto",
            "gate-shape": "single gate",
        }
        result = evaluate_answer_gate(_FEATURE_ID, _QUESTIONS, answers)
        self.assertEqual(result.outcome, OUTCOME_FALLBACK)
        self.assertEqual(result.answers, {})
        self.assertIsNotNone(result.escalation)
        self.assertEqual(result.escalation.category, "drafting-needed")


class UnansweredDecisionDefaultsTests(unittest.TestCase):
    def test_unanswered_decision_yields_recommendation_and_assumption(self):
        answers = {
            "roadmap-goal": "Operators answer async, drafting proceeds later.",
            "scope-boundary": "No change to the write path.",
            "surfaces-touched": "specfuse/agent/drafting_answers.py",
            # autonomy-level and gate-shape left unanswered.
        }
        result = evaluate_answer_gate(_FEATURE_ID, _QUESTIONS, answers)
        self.assertEqual(result.outcome, OUTCOME_DRAFT_READY)
        self.assertEqual(result.answers["autonomy-level"], "review")
        self.assertEqual(result.answers["gate-shape"], "single gate")
        self.assertTrue(result.assumptions)
        assumed_ids = {a.question_id for a in result.assumptions}
        self.assertEqual(assumed_ids, {"autonomy-level", "gate-shape"})
        for assumption in result.assumptions:
            if assumption.question_id == "autonomy-level":
                self.assertEqual(assumption.assumed_value, "review")
            if assumption.question_id == "gate-shape":
                self.assertEqual(assumption.assumed_value, "single gate")

    def test_no_assumptions_when_every_decision_answered(self):
        answers = {
            "roadmap-goal": "Operators answer async, drafting proceeds later.",
            "scope-boundary": "No change to the write path.",
            "surfaces-touched": "specfuse/agent/drafting_answers.py",
            "autonomy-level": "supervised",
            "gate-shape": "multi-gate",
        }
        result = evaluate_answer_gate(_FEATURE_ID, _QUESTIONS, answers)
        self.assertEqual(result.outcome, OUTCOME_DRAFT_READY)
        self.assertEqual(result.assumptions, ())
        self.assertEqual(result.answers["autonomy-level"], "supervised")
        self.assertEqual(result.answers["gate-shape"], "multi-gate")


class BindByQuestionIdNotPositionTests(unittest.TestCase):
    def test_skipped_question_stays_unanswered_not_shifted(self):
        question_ids = [q.id for q in _QUESTIONS]
        reply = (
            "roadmap-goal: Operators answer async, drafting proceeds later.\n"
            "surfaces-touched: specfuse/agent/drafting_answers.py\n"
        )
        answers = parse_reply_answers(reply, question_ids)
        self.assertIn("roadmap-goal", answers)
        self.assertIn("surfaces-touched", answers)
        self.assertNotIn("scope-boundary", answers)
        self.assertEqual(
            answers["roadmap-goal"],
            "Operators answer async, drafting proceeds later.",
        )

    def test_out_of_order_reply_binds_correctly(self):
        question_ids = [q.id for q in _QUESTIONS]
        reply = (
            "gate-shape: multi-gate\n"
            "roadmap-goal: Operators answer async, drafting proceeds later.\n"
        )
        answers = parse_reply_answers(reply, question_ids)
        self.assertEqual(answers["gate-shape"], "multi-gate")
        self.assertEqual(
            answers["roadmap-goal"],
            "Operators answer async, drafting proceeds later.",
        )
        self.assertNotIn("scope-boundary", answers)

    def test_unknown_id_lines_are_ignored(self):
        answers = parse_reply_answers("not-a-question: whatever\n", ["roadmap-goal"])
        self.assertEqual(answers, {})


class RoundTwoReasksOnlyUnansweredElicitationTests(unittest.TestCase):
    def test_second_round_question_set_excludes_decisions_and_answered(self):
        round_one_answers = {
            "roadmap-goal": "Operators answer async, drafting proceeds later.",
            "autonomy-level": "auto",
        }
        reask = next_round_questions(_QUESTIONS, round_one_answers)
        reask_ids = {q.id for q in reask}

        self.assertEqual(reask_ids, {"scope-boundary", "surfaces-touched"})
        for question in reask:
            self.assertEqual(question.kind, "elicitation")
        self.assertNotIn("autonomy-level", reask_ids)
        self.assertNotIn("gate-shape", reask_ids)
        self.assertNotIn("roadmap-goal", reask_ids)

    def test_nothing_to_reask_when_all_elicitation_answered(self):
        answers = {
            "roadmap-goal": "x",
            "scope-boundary": "x",
            "surfaces-touched": "x",
        }
        self.assertEqual(next_round_questions(_QUESTIONS, answers), ())


class HardCapOfTwoRoundsTests(unittest.TestCase):
    def test_third_round_never_allowed(self):
        self.assertTrue(reask_allowed(1))
        self.assertFalse(reask_allowed(2))
        self.assertFalse(reask_allowed(3))

    def test_cap_reached_with_elicitation_unanswered_falls_back(self):
        # Round two's re-ask still left scope-boundary unanswered; no third
        # round is posted, so this is the final answer set.
        final_answers = {
            "roadmap-goal": "Operators answer async, drafting proceeds later.",
            "surfaces-touched": "specfuse/agent/drafting_answers.py",
            "autonomy-level": "auto",
            "gate-shape": "single gate",
        }
        self.assertFalse(reask_allowed(MAX_ROUNDS))
        result = evaluate_answer_gate(_FEATURE_ID, _QUESTIONS, final_answers)
        self.assertEqual(result.outcome, OUTCOME_FALLBACK)
        self.assertEqual(result.answers, {})


class FallbackMatchesFeatureProviderTests(unittest.TestCase):
    def test_fallback_escalation_matches_needs_drafting_branch(self):
        provider = FeatureProvider(repo="o/r", features_root=Path("/nonexistent-features-root"))
        items = provider.advertise(_snapshot(("FEAT-MISSING",)))
        self.assertEqual(len(items), 1)
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.escalation.category, "drafting-needed")

        gate_escalation = fallback_escalation("FEAT-MISSING")
        self.assertEqual(gate_escalation, outcome.escalation)


if __name__ == "__main__":
    unittest.main()
