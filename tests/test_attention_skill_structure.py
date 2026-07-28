# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0046/T03: structural oracle for the /attention skill.
# [FEAT-2026-0003/G2-LESSONS] — a prose artifact (SKILL.md) passes automated
# code gates trivially; this test is the falsifiable check that its required
# sections actually exist.

import pathlib
import unittest

import yaml

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "attention" / "SKILL.md"
_VENDORED = _REPO_ROOT / ".specfuse" / "skills" / "attention" / "SKILL.md"


def _frontmatter_and_body(text: str):
    assert text.startswith("---\n"), "SKILL.md must open with YAML frontmatter"
    _, _, rest = text.partition("---\n")
    fm_text, _, body = rest.partition("\n---\n")
    return yaml.safe_load(fm_text), body


class TestAttentionSkillStructure(unittest.TestCase):
    def test_required_sections_present(self):
        self.assertTrue(_CANONICAL.is_file(), f"missing canonical skill: {_CANONICAL}")
        text = _CANONICAL.read_text()
        frontmatter, body = _frontmatter_and_body(text)

        # Criterion 2: frontmatter name + non-empty description.
        self.assertEqual(frontmatter.get("name"), "attention")
        self.assertTrue(frontmatter.get("description"))

        # Criteria 3-4: required headings.
        self.assertIn("## Hard rules", body)
        self.assertIn("## Method", body)

        # Criterion 5: read-only hard rule, literal word.
        self.assertIn("read-only", body.lower())

        # Criterion 6: all four swept state classes, literal strings.
        for literal in ("blocked_human", "awaiting_review", "blocked", "stale"):
            self.assertIn(literal, body)

        # Criterion 7: names gate-status as the delegated per-feature diagnosis.
        self.assertIn("gate-status", body)

        # Criterion 8: names needs-human as the issue label it queries.
        self.assertIn("needs-human", body)

        # Criterion 9: priority ordering heading, listing classes in presented order.
        self.assertIn("## Priority order", body)
        priority_section = body.split("## Priority order", 1)[1]
        priority_section = priority_section.split("\n## ", 1)[0]
        positions = []
        cursor = 0
        for literal in ("blocked_human", "awaiting_review", "blocked", "stale"):
            pos = priority_section.find(literal, cursor)
            self.assertNotEqual(pos, -1, f"{literal!r} not found in order in Priority order section")
            positions.append(pos)
            cursor = pos + len(literal)
        self.assertEqual(positions, sorted(positions))

        # Criterion 10: graceful gh degradation, local sweep still runs.
        self.assertIn("gh", body)
        self.assertIn("degrad", body.lower())

    def test_vendored_copy_exists(self):
        self.assertTrue(_VENDORED.is_file(), f"missing vendored skill: {_VENDORED}")


if __name__ == "__main__":
    unittest.main()
