#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.agent.drafting_invoke (FEAT-2026-0050/T06)."""

from __future__ import annotations

import inspect
import unittest

from specfuse.agent import drafting_invoke
from specfuse.agent.drafting_answers import (
    OUTCOME_DRAFT_READY,
    OUTCOME_FALLBACK,
    Assumption,
    AnswerGateResult,
    fallback_escalation,
)
from specfuse.agent.drafting_invoke import (
    DraftingInvokeError,
    build_invocation,
    read_result,
)

_FEATURE_ID = "FEAT-2026-9999"

_DRAFT_READY_RESULT = AnswerGateResult(
    outcome=OUTCOME_DRAFT_READY,
    answers={
        "roadmap-goal": "Keep the widget catalog in sync.",
        "autonomy-level": "review",
    },
    assumptions=(Assumption(question_id="autonomy-level", assumed_value="review"),),
)

_FALLBACK_RESULT = AnswerGateResult(
    outcome=OUTCOME_FALLBACK,
    escalation=fallback_escalation(_FEATURE_ID),
)


class RefusesFallbackTests(unittest.TestCase):
    def test_build_invocation_refuses_a_fallback_result(self):
        with self.assertRaises(DraftingInvokeError):
            build_invocation(_FEATURE_ID, _FALLBACK_RESULT)


class BuildInvocationTests(unittest.TestCase):
    def test_returns_argv_and_prompt_tuple(self):
        result = build_invocation(_FEATURE_ID, _DRAFT_READY_RESULT)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        argv, prompt = result
        self.assertIsInstance(argv, list)
        self.assertIsInstance(prompt, str)
        self.assertEqual(argv[0], "claude")
        self.assertIn("-p", argv)

    def test_prompt_names_every_question_id_and_effective_answer(self):
        _, prompt = build_invocation(_FEATURE_ID, _DRAFT_READY_RESULT)
        for question_id, answer in _DRAFT_READY_RESULT.answers.items():
            self.assertIn(question_id, prompt)
            self.assertIn(answer, prompt)

    def test_prompt_names_every_assumption_verbatim(self):
        _, prompt = build_invocation(_FEATURE_ID, _DRAFT_READY_RESULT)
        for assumption in _DRAFT_READY_RESULT.assumptions:
            self.assertIn(assumption.question_id, prompt)
            self.assertIn(assumption.assumed_value, prompt)

    def test_module_runs_no_subprocess(self):
        source = inspect.getsource(drafting_invoke)
        self.assertNotIn("import subprocess", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("gh issue", source)
        self.assertNotIn("gh(", source)
        self.assertNotIn("Popen", source)
        self.assertNotIn("run_module", source)


class ReadResultTests(unittest.TestCase):
    def test_complete_status_returns_parsed_result(self):
        text = (
            "Drafted the feature.\n\n"
            "```result\n"
            "status: complete\n"
            "summary: Drafted FEAT-2026-9999's gate skeleton.\n"
            "```\n"
        )
        parsed = read_result(text)
        self.assertEqual(parsed.get("status"), "complete")

    def test_blocked_status_raises(self):
        text = (
            "```result\n"
            "status: blocked\n"
            "blocked_reason: spec ambiguity\n"
            "```\n"
        )
        with self.assertRaises(DraftingInvokeError):
            read_result(text)

    def test_missing_result_block_raises(self):
        with self.assertRaises(DraftingInvokeError):
            read_result("the session finished without incident")

    def test_empty_result_raises(self):
        with self.assertRaises(DraftingInvokeError):
            read_result("")


if __name__ == "__main__":
    unittest.main()
