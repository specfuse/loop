#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for rendering the drafting interview as a question issue
(FEAT-2026-0050/T02)."""

from __future__ import annotations

import unittest

from specfuse.agent.drafting_questions import Question, render_question_issue
from specfuse.loop import escalation

_QUESTIONS = [
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
]


class RenderQuestionIssueTests(unittest.TestCase):
    def test_each_question_carries_its_own_marker(self):
        body, _labels = render_question_issue("FEAT-2026-9999/T01", _QUESTIONS)
        for question in _QUESTIONS:
            marker = f"<!-- specfuse:question id={question.id} -->"
            self.assertIn(marker, body)
        markers = {f"<!-- specfuse:question id={q.id} -->" for q in _QUESTIONS}
        self.assertEqual(len(markers), len(_QUESTIONS))

    def test_body_is_produced_by_render_escalation_body(self):
        body, _labels = render_question_issue("FEAT-2026-9999/T01", _QUESTIONS)
        for heading in escalation._PART_HEADINGS:
            self.assertIn(heading, body)

    def test_hand_rolled_body_fails_the_same_check(self):
        hand_rolled = "Just answer these questions:\n1. roadmap-goal\n2. scope-boundary\n"
        missing = [
            heading
            for heading in escalation._PART_HEADINGS
            if heading not in hand_rolled
        ]
        self.assertTrue(missing)

    def test_labels_are_needs_human_and_drafting_needed_only(self):
        _body, labels = render_question_issue("FEAT-2026-9999/T01", _QUESTIONS)
        self.assertEqual(labels, frozenset({escalation.NEEDS_HUMAN_LABEL, "drafting-needed"}))
        for label in labels:
            if label != escalation.NEEDS_HUMAN_LABEL:
                self.assertIn(label, escalation.CATEGORY_LABELS)

    def test_elicitation_questions_render_open_with_no_options(self):
        body, _labels = render_question_issue("FEAT-2026-9999/T01", _QUESTIONS)
        self.assertNotIn("roadmap-goal:", body.split("## Options")[1].split("## A recommendation")[0])

    def test_decision_questions_render_options_with_recommendation_named(self):
        body, _labels = render_question_issue("FEAT-2026-9999/T01", _QUESTIONS)
        options_part = body.split("## Options")[1].split("## A recommendation")[0]
        self.assertIn("autonomy-level: auto", options_part)
        self.assertIn("autonomy-level: review", options_part)
        self.assertIn("autonomy-level: supervised", options_part)
        self.assertIn("gate-shape: single gate", options_part)
        self.assertIn("gate-shape: multi-gate", options_part)

        recommendation_part = body.split("## A recommendation")[1]
        self.assertIn("autonomy-level: review", recommendation_part)
        self.assertIn("gate-shape: single gate", recommendation_part)

    def test_renders_no_gh_command(self):
        import inspect

        source = inspect.getsource(render_question_issue)
        self.assertNotIn("gh", source.split('"""')[-1])
        self.assertNotIn("subprocess", source)
        body, labels = render_question_issue("FEAT-2026-9999/T01", _QUESTIONS)
        self.assertIsInstance(body, str)
        self.assertIsInstance(labels, frozenset)

    def test_requires_at_least_one_question(self):
        with self.assertRaises(ValueError):
            render_question_issue("FEAT-2026-9999/T01", [])


if __name__ == "__main__":
    unittest.main()
