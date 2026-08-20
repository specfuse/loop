#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Round-trip test: the rendered question issue's reply instructions must
produce a reply `drafting_answers.parse_reply_answers` actually binds
(FEAT-2026-0050/T04).

`GATE-02-REVIEW.md` § Runtime probe measured the gap this closes: the
rendered body's closing section asks for a bare number, while
`parse_reply_answers` only binds `"{question_id}: <answer>"` lines. Numbers
cannot carry the interview at all -- elicitation questions contribute no
options, so no number exists for them.
"""

from __future__ import annotations

import unittest

from specfuse.agent.drafting_answers import evaluate_answer_gate, parse_reply_answers
from specfuse.agent.drafting_questions import (
    ANSWER_TEMPLATE_END,
    ANSWER_TEMPLATE_START,
    Question,
    render_question_issue,
)
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


def _extract_template_block(body: str) -> str:
    start = body.index(ANSWER_TEMPLATE_START) + len(ANSWER_TEMPLATE_START)
    end = body.index(ANSWER_TEMPLATE_END)
    return body[start:end]


class ReplyTemplateRoundTripTests(unittest.TestCase):
    def test_template_block_parses_back_to_every_question(self):
        body, _labels = render_question_issue("FEAT-2026-9999/T04", _QUESTIONS)
        block = _extract_template_block(body)

        filled_lines = []
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("```") or not stripped:
                continue
            qid, _sep, _rest = stripped.partition(":")
            filled_lines.append(f"{qid}: answer for {qid}")
        reply_text = "\n".join(filled_lines)

        question_ids = [q.id for q in _QUESTIONS]
        answers = parse_reply_answers(reply_text, question_ids)

        for question in _QUESTIONS:
            self.assertIn(question.id, answers)
            self.assertEqual(answers[question.id], f"answer for {question.id}")

    def test_template_names_every_question_including_elicitation(self):
        body, _labels = render_question_issue("FEAT-2026-9999/T04", _QUESTIONS)
        block = _extract_template_block(body)
        for question in _QUESTIONS:
            self.assertIn(f"{question.id}:", block)

    def test_body_still_conforms_to_escalation_shape(self):
        body, _labels = render_question_issue("FEAT-2026-9999/T04", _QUESTIONS)
        self.assertEqual(escalation.validate_escalation_body(body), [])
        self.assertIn("## Reply with a number", body)
        self.assertIn("1.", body.split("## Reply with a number")[1])

    def test_bare_number_reply_still_binds_nothing_and_falls_back(self):
        question_ids = [q.id for q in _QUESTIONS]
        answers = parse_reply_answers("4", question_ids)
        self.assertEqual(answers, {})

        result = evaluate_answer_gate("FEAT-2026-9999", _QUESTIONS, answers)
        self.assertEqual(result.outcome, "fallback")


if __name__ == "__main__":
    unittest.main()
