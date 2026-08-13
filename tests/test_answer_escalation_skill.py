#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0080/T01 — the `/answer-escalation` skill exists and is complete.

`AnsweredEscalationProvider` (`specfuse/agent/providers/answers.py`) records an
operator's numbered reply but explicitly does not carry it out, leaving
`NEEDS_HUMAN_LABEL` in place. `BugsProvider.advertise` skips any issue carrying
`needs-human` or `blocked-wu`. This test asserts the human-invoked skill that
closes that gap exists in both the canonical and vendored trees, is
byte-identical between them, documents all four dispositions, routes every
`escalation.CATEGORY_LABELS` category to an owning skill, and states the
write-order, headless-refusal, and skip-writes-nothing rules PLAN.md decided.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import unittest

from specfuse.loop.escalation import CATEGORY_LABELS


def _collapse_whitespace(text: str) -> str:
    """Markdown hard-wraps mid-sentence; compare on normalized whitespace so
    an anchor phrase that happens to straddle a line break still matches."""
    return re.sub(r"\s+", " ", text)


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "plugins" / "specfuse" / "skills" / "answer-escalation" / "SKILL.md"
VENDORED = REPO_ROOT / ".specfuse" / "skills" / "answer-escalation" / "SKILL.md"

REQUIRED_DISPOSITIONS = ("hand off", "answer", "close", "skip")

GUIDANCE_MARKER = "<!-- specfuse:operator-guidance id="


class TestAnswerEscalationSkill(unittest.TestCase):

    def test_skill_file_exists_in_both_trees(self):
        self.assertTrue(
            CANONICAL.exists(),
            f"canonical skill file missing: {CANONICAL}")
        self.assertTrue(
            VENDORED.exists(),
            f"vendored skill file missing: {VENDORED}")

    def test_frontmatter_names_the_skill_and_trigger_phrases(self):
        text = CANONICAL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"), "SKILL.md must open with YAML frontmatter")
        self.assertIn("name: answer-escalation", text)
        frontmatter_end = text.index("\n---", 4)
        frontmatter = text[:frontmatter_end]
        self.assertIn("description:", frontmatter)

    def test_human_invoked_only_and_headless_reason_stated(self):
        text = CANONICAL.read_text(encoding="utf-8").lower()
        self.assertIn("human-invoked only", text)
        self.assertIn("never run headless", text)
        self.assertIn("no channel to supply", text)

    def test_all_four_dispositions_documented_as_own_step(self):
        text = CANONICAL.read_text(encoding="utf-8")
        for disposition in REQUIRED_DISPOSITIONS:
            heading = f"Disposition: {disposition}"
            self.assertIn(
                heading, text,
                f"SKILL.md does not document {disposition!r} as its own step")

    def test_routing_table_covers_every_category_label_exactly(self):
        text = CANONICAL.read_text(encoding="utf-8")
        table_start = text.index("| Category | Owning skill |")
        table_end = text.index("\n\n", table_start)
        table = text[table_start:table_end]
        found_categories = set()
        for category in CATEGORY_LABELS:
            self.assertIn(
                f"`{category}`", table,
                f"routing table is missing category {category!r}")
            found_categories.add(category)
        # Every backtick-quoted token in the table's first column must be a
        # known category -- catches a stale/renamed entry the CATEGORY_LABELS
        # loop above wouldn't.
        for line in table.splitlines():
            if not line.startswith("| `"):
                continue
            token = line.split("`")[1]
            self.assertIn(
                token, CATEGORY_LABELS,
                f"routing table names {token!r}, which is not in "
                f"escalation.CATEGORY_LABELS {sorted(CATEGORY_LABELS)}")
        self.assertEqual(found_categories, set(CATEGORY_LABELS))

    def test_guidance_marker_documented(self):
        text = CANONICAL.read_text(encoding="utf-8")
        self.assertIn(GUIDANCE_MARKER, text)

    def test_write_order_documented_with_reason(self):
        text = CANONICAL.read_text(encoding="utf-8")
        flat_text = _collapse_whitespace(text).lower()
        self.assertIn("guidance comment first", flat_text)
        self.assertIn("label release second", flat_text)
        self.assertIn("comment is the authoritative record", flat_text)

    def test_skip_writes_nothing_documented(self):
        text = CANONICAL.read_text(encoding="utf-8")
        skip_idx = text.index("Disposition: skip")
        next_heading = text.index("\n#### ", skip_idx + 1) if "\n#### " in text[skip_idx + 1:] else len(text)
        skip_section = text[skip_idx:next_heading if next_heading != len(text) else None]
        if next_heading == len(text):
            skip_section = text[skip_idx:skip_idx + 2000]
        flat_skip_section = _collapse_whitespace(skip_section)
        self.assertIn("Writes nothing at all", flat_skip_section)
        self.assertIn("no guidance comment, no label edit, no issue state change", flat_skip_section)

    def test_triggers_no_fix_and_no_retry(self):
        text = CANONICAL.read_text(encoding="utf-8")
        flat_text = _collapse_whitespace(text)
        self.assertIn("Triggers no fix and no retry", flat_text)
        self.assertIn("/fix-bug", flat_text)
        self.assertIn("never opens a pr", flat_text.lower())
        self.assertIn("never merges", flat_text.lower())

    def test_gh_unavailable_degradation_documented(self):
        text = CANONICAL.read_text(encoding="utf-8")
        flat_text = _collapse_whitespace(text)
        self.assertIn("gh auth status", flat_text)
        self.assertIn("report that plainly and stop", flat_text.lower())

    def test_canonical_and_vendored_skill_are_byte_identical(self):
        result = subprocess.run(
            ["diff", str(CANONICAL), str(VENDORED)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            f"plugins/specfuse/skills/answer-escalation/SKILL.md and "
            f".specfuse/skills/answer-escalation/SKILL.md have drifted — "
            f"diff output: {result.stdout!r}")
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
