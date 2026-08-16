#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.agent.drafting_questions (FEAT-2026-0050/T01)."""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from specfuse.agent import drafting_questions
from specfuse.agent.drafting_questions import (
    Question,
    build_question_set,
    build_question_set_for_feature,
    load_roadmap_entry,
)

_ROADMAP_ENTRY = """\
## FEAT-2026-9999 — Widget catalog sync

**Why.** The widget catalog drifts from `specfuse/agent/widget_sync.py` and
the storefront every time a vendor renames a SKU.

**Goal.** Keep `specfuse/agent/widget_sync.py` and the storefront catalog in
sync on a schedule.

**Benefits.** No more manual reconciliation.

**Status: planned.**
"""

_ROADMAP_TEXT = f"""\
# Roadmap

| Feature ID | Title | Status |

{_ROADMAP_ENTRY}
## FEAT-2026-9998 — Unrelated entry

**Why.** Not this one.

**Status: planned.**
"""

_LEARNINGS_SLICE = "- [pattern] Widget sync failures cluster around SKU renames."


class TestBuildQuestionSet(unittest.TestCase):
    def test_elicitation_questions_carry_no_options(self):
        questions = build_question_set(_ROADMAP_ENTRY, _LEARNINGS_SLICE, ())
        elicitations = [q for q in questions if q.kind == "elicitation"]
        self.assertTrue(elicitations)
        for question in elicitations:
            self.assertEqual(question.options, ())
            self.assertIsNone(question.recommendation)

    def test_every_question_has_kind_id_and_text(self):
        questions = build_question_set(_ROADMAP_ENTRY, _LEARNINGS_SLICE, ())
        self.assertTrue(questions)
        seen_ids = set()
        for question in questions:
            self.assertIn(question.kind, ("elicitation", "decision"))
            self.assertTrue(question.id)
            self.assertNotIn(question.id, seen_ids)
            seen_ids.add(question.id)
            self.assertTrue(question.text)

    def test_decision_questions_carry_options_and_a_recommendation(self):
        questions = build_question_set(_ROADMAP_ENTRY, _LEARNINGS_SLICE, ())
        decisions = [q for q in questions if q.kind == "decision"]
        self.assertTrue(decisions)
        for question in decisions:
            self.assertGreaterEqual(len(question.options), 2)
            self.assertIn(question.recommendation, question.options)

    def test_a_decision_the_builder_cannot_recommend_on_is_rejected(self):
        with self.assertRaises(ValueError):
            Question(
                id="bad-decision",
                kind="decision",
                text="Pick one",
                options=("a", "b"),
                recommendation=None,
            )

    def test_a_decision_recommendation_must_name_one_of_its_own_options(self):
        with self.assertRaises(ValueError):
            Question(
                id="bad-decision",
                kind="decision",
                text="Pick one",
                options=("a", "b"),
                recommendation="c",
            )

    def test_an_elicitation_question_rejects_manufactured_options(self):
        with self.assertRaises(ValueError):
            Question(
                id="bad-elicitation",
                kind="elicitation",
                text="What do you want?",
                options=("a", "b"),
            )

    def test_question_set_mentions_a_surface_named_in_the_roadmap_entry(self):
        questions = build_question_set(_ROADMAP_ENTRY, _LEARNINGS_SLICE, ())
        all_text = " ".join(q.text for q in questions)
        self.assertIn("specfuse/agent/widget_sync.py", all_text)

    def test_module_issues_no_gh_or_git_subprocess(self):
        source = inspect.getsource(drafting_questions)
        self.assertNotIn("import subprocess", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("gh issue", source)
        self.assertNotIn("gh(", source)


class TestLoadRoadmapEntry(unittest.TestCase):
    def test_extracts_only_the_named_entry(self):
        entry = load_roadmap_entry(_ROADMAP_TEXT, "FEAT-2026-9999")
        self.assertIn("Widget catalog sync", entry)
        self.assertNotIn("Unrelated entry", entry)

    def test_missing_feature_id_raises(self):
        with self.assertRaises(ValueError):
            load_roadmap_entry(_ROADMAP_TEXT, "FEAT-2026-0000")


class TestBuildQuestionSetForFeature(unittest.TestCase):
    def test_reads_roadmap_entry_and_builds_from_it(self):
        questions = build_question_set_for_feature(
            "FEAT-2026-9999",
            _ROADMAP_TEXT,
            exemplar_plan_texts=("# exemplar plan\n",),
            learnings_slice=_LEARNINGS_SLICE,
        )
        all_text = " ".join(q.text for q in questions)
        self.assertIn("specfuse/agent/widget_sync.py", all_text)

    def test_reads_learnings_slice_from_a_real_file_when_not_supplied(self):
        with tempfile.TemporaryDirectory() as tmp:
            learnings_path = Path(tmp) / "LEARNINGS.md"
            learnings_path.write_text(
                "<!-- lessons work units append below this line -->\n"
                "- [pattern] Widget sync failures cluster around SKU renames.\n",
                encoding="utf-8",
            )
            questions = build_question_set_for_feature(
                "FEAT-2026-9999",
                _ROADMAP_TEXT,
                learnings_path=learnings_path,
            )
        self.assertTrue(questions)


if __name__ == "__main__":
    unittest.main()
