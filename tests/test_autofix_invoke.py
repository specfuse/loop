# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the headless `fix-bug` invoker (FEAT-2026-0042/T04)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from specfuse.monitor.autofix_invoke import (
    OUTCOMES,
    build_invocation,
    classify_outcome,
)

_SKILL_PATH = Path(__file__).resolve().parents[1] / "plugins" / "specfuse" / "skills" / "fix-bug" / "SKILL.md"
_SUBJECT_PATH = Path(__file__).resolve().parents[1] / "specfuse" / "monitor" / "autofix_invoke.py"


def _outcomes_from_skill():
    text = _SKILL_PATH.read_text(encoding="utf-8")
    match = re.search(r"## Headless mode(.*?)\n## ", text, re.DOTALL)
    section = match.group(1)
    bullets = re.findall(r"\*\*`([a-z_]+)`\*\*", section)
    # Every distinct bolded-code bullet in the section, with no cap. The cap
    # used to be a literal 3 — it encoded the very count this guard exists to
    # verify, so adding `needs_decision` (#3390) made the guard report the
    # skill as missing `completed` rather than reporting the real difference.
    seen = []
    for name in bullets:
        if name not in seen:
            seen.append(name)
    return tuple(seen)


class TestAutofixInvoke(unittest.TestCase):
    def test_outcomes_matches_skill_headless_section(self):
        # Compared as sets: which outcomes exist is the invariant, the order
        # they are presented in is a prose choice. Pinning the order made the
        # guard fail on an edit that changed nothing about the contract.
        self.assertEqual(
            set(OUTCOMES), set(_outcomes_from_skill()),
            "the skill's headless section and OUTCOMES must name the same set "
            "— a session can only report an outcome the skill told it about, "
            "and the lane can only classify one OUTCOMES contains",
        )

    def test_subject_runs_nothing_itself(self):
        text = _SUBJECT_PATH.read_text(encoding="utf-8")
        hits = re.findall(r"subprocess|requests|urllib|os\.system|^import |^from ", text, re.MULTILINE)
        self.assertEqual(hits, [])

    def test_build_invocation_names_issue_headless_and_safety_floor(self):
        argv, prompt = build_invocation(
            issue_number=42, repo="acme-widget/example", working_dir="/tmp/scratch"
        )
        self.assertIn("42", prompt)
        self.assertIn("headless", prompt)
        self.assertIn("merge a pull request", prompt)
        self.assertIn("auto-merge", prompt)
        self.assertIn("protected branch", prompt)
        self.assertEqual(argv[0], "claude")
        self.assertIn("-p", argv)

    def test_unclassifiable_result_is_could_not_proceed(self):
        self.assertEqual(classify_outcome(""), "could_not_proceed")
        self.assertEqual(classify_outcome("   \n  "), "could_not_proceed")
        self.assertEqual(classify_outcome("the run finished without incident"), "could_not_proceed")
        self.assertEqual(
            classify_outcome("status: completed\nactually wait, refused"), "could_not_proceed"
        )
        for text in [
            "",
            "no outcome word here",
            "completed and also refused",
        ]:
            self.assertNotEqual(classify_outcome(text), "completed")

    def test_classify_outcome_refused(self):
        outcome = classify_outcome("status: refused -- this is a feature, not a bug")
        self.assertEqual(outcome, "refused")
        for other in OUTCOMES:
            if other != "refused":
                self.assertNotEqual(outcome, other)

    def test_classify_outcome_could_not_proceed(self):
        outcome = classify_outcome("status: could_not_proceed -- gh auth status failed")
        self.assertEqual(outcome, "could_not_proceed")
        for other in OUTCOMES:
            if other != "could_not_proceed":
                self.assertNotEqual(outcome, other)

    def test_classify_outcome_completed(self):
        outcome = classify_outcome("status: completed -- PR opened")
        self.assertEqual(outcome, "completed")
        for other in OUTCOMES:
            if other != "completed":
                self.assertNotEqual(outcome, other)


if __name__ == "__main__":
    unittest.main()
