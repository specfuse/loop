#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0050/T05 — draft-feature's answers-supplied mode is documented
and additive.

`draft-feature` (plugins/specfuse/skills/draft-feature/SKILL.md) is titled
"interactive" and its Method walks a guided one-question-at-a-time interview.
This test asserts the skill now also documents an **Answers-supplied mode**
in which the interview's answers arrive as supplied text instead of a live
conversation, restates the skill's write rule as "never writes without
answers", states the never-prompts/never-waits rule, states that an
unanswered elicitation question means the skill does not write at all, states
that a defaulted decision is written into the drafted PLAN.md as an explicit
assumption, and states that the drafted folder lands `status: planned` and
unarmed. It also asserts the interactive Method above the new section is
untouched (only additive content was introduced, byte-compared against
`git show HEAD:`) and that both skill surfaces stay byte-identical.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import unittest


def _collapse_whitespace(text: str) -> str:
    """Markdown hard-wraps mid-sentence; compare on normalized whitespace so
    an anchor phrase that happens to straddle a line break still matches."""
    return re.sub(r"\s+", " ", text)


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CANONICAL = (
    REPO_ROOT / "plugins" / "specfuse" / "skills" / "draft-feature" / "SKILL.md"
)
VENDORED = REPO_ROOT / ".specfuse" / "skills" / "draft-feature" / "SKILL.md"

ANSWERS_MODE_HEADING = "## Answers-supplied mode"

# Headings and hard rules present in HEAD's SKILL.md before this WU — every
# one must still be present verbatim after the change (additive-only).
HEAD_ANCHORS = (
    "## Hard rules",
    "## When to invoke",
    "## Method (strict order",
    "### 1. Read the grounding context",
    "### 2. Reconnaissance",
    "### 3. Interview",
    "### 4. Propose the gate skeleton",
    "### 5. Propose gate 1's WUs",
    "### 6. Write only on accept",
    "## What this skill does NOT do",
    "## Escalation framing",
    "## Version",
    "Trace every proposal to evidence.",
    "Infer first, ask last.",
    "Don't restate the binding rules.",
    "Detail only gate 1.",
    "Does not flip status to `active`.",
    "Does not detail gates 2..N.",
    "Does not invent acceptance criteria.",
    "Does not run git.",
)


def _git_show_head(path: pathlib.Path) -> str:
    rel = path.relative_to(REPO_ROOT)
    out = subprocess.run(
        ["git", "show", f"HEAD:{rel.as_posix()}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    return out.stdout


class AnswersSuppliedModeTests(unittest.TestCase):

    def setUp(self):
        self.text = CANONICAL.read_text(encoding="utf-8")
        self.head_text = _git_show_head(CANONICAL)
        self.flat_text = _collapse_whitespace(self.text)

    def test_mode_section_states_the_answers_rule(self):
        self.assertIn(
            ANSWERS_MODE_HEADING, self.text,
            "SKILL.md does not document an Answers-supplied mode section")

        self.assertIn(
            "never writes without answers", self.flat_text,
            "SKILL.md does not restate the write rule as 'never writes "
            "without answers'")
        self.assertIn(
            "whatever channel", self.flat_text,
            "SKILL.md does not state the write rule holds regardless of "
            "which channel the answers arrived through")

        self.assertIn(
            "never prompts and never waits", self.flat_text,
            "SKILL.md does not state the never-prompts/never-waits rule "
            "for this mode")

        self.assertIn(
            "unanswered elicitation question", self.flat_text,
            "SKILL.md does not state what happens on an unanswered "
            "elicitation question")
        self.assertIn(
            "does not write at all", self.flat_text,
            "SKILL.md does not state that an unanswered elicitation "
            "question means the skill does not write at all")

        self.assertIn(
            "defaulted decision", self.flat_text,
            "SKILL.md does not address a defaulted decision")
        self.assertIn(
            "explicit assumption", self.flat_text,
            "SKILL.md does not state a defaulted decision is written into "
            "the drafted PLAN.md as an explicit assumption")

        self.assertIn(
            "`status: planned` and unarmed", self.flat_text,
            "SKILL.md does not state the drafted folder lands "
            "status: planned and unarmed in this mode")

    def test_answers_mode_is_additive_and_does_not_interleave(self):
        self.assertEqual(
            self.text.count(f"\n{ANSWERS_MODE_HEADING}"), 1,
            f"{ANSWERS_MODE_HEADING!r} must appear exactly once — a second "
            f"block means the mode is described in two places")

        for anchor in HEAD_ANCHORS:
            self.assertIn(
                anchor, self.head_text,
                f"test fixture drifted from HEAD: anchor {anchor!r} no "
                f"longer present in the pre-WU skill body")
            self.assertIn(
                anchor, self.text,
                f"heading or hard rule {anchor!r} was removed or reworded "
                f"— every existing heading/hard rule must survive unchanged")

        interactive_method_start = self.text.index("## Method (strict order")
        answers_mode_start = self.text.index(ANSWERS_MODE_HEADING)
        does_not_start = self.text.index("## What this skill does NOT do")
        self.assertLess(
            interactive_method_start, answers_mode_start,
            "Answers-supplied mode section appears before the interactive "
            "Method — it must be appended, not spliced in")
        self.assertLess(
            answers_mode_start, does_not_start,
            "Answers-supplied mode section must sit before "
            "'What this skill does NOT do', not after it")

    def test_canonical_and_vendored_skill_are_byte_identical(self):
        result = subprocess.run(
            ["diff", str(CANONICAL), str(VENDORED)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            f"plugins/specfuse/skills/draft-feature/SKILL.md and "
            f".specfuse/skills/draft-feature/SKILL.md have drifted — diff "
            f"output: {result.stdout!r}")
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
