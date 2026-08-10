# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Drift guard: SKILL.md's documented vocabulary matches triage.py's constants
(FEAT-2026-0045/T03).

Prose and constants are two statements of one contract, and prose drifts. This
test asserts SKILL.md names every category in `CATEGORIES`, every route in
the route map, and no category outside `CATEGORIES` -- imported from the
module, never hardcoded here. It is NOT proof that an agent following the
prose triages an unseen issue correctly; see SKILL.md's Version section.
"""

from __future__ import annotations

import pathlib
import re
import unittest

from specfuse.loop.triage import CATEGORIES, route_for

REPO_ROOT = pathlib.Path(__file__).parent.parent
SKILL_MD = REPO_ROOT / "plugins" / "specfuse" / "skills" / "triage-issues" / "SKILL.md"

# Matches a two-column markdown table row: | category | route |
_TABLE_ROW_RE = re.compile(r"^\|\s*`?(?P<category>[a-z_]+)`?\s*\|\s*`?(?P<route>[a-z_-]+)`?\s*\|\s*$", re.MULTILINE)


class TestSkillVocabularyMatchesModule(unittest.TestCase):
    def test_skill_vocabulary_matches_module(self):
        self.assertTrue(
            SKILL_MD.is_file(),
            f"SKILL.md missing: {SKILL_MD}",
        )
        text = SKILL_MD.read_text()

        for category in CATEGORIES:
            self.assertIn(
                category,
                text,
                f"SKILL.md does not mention category {category!r}",
            )

        for category in CATEGORIES:
            route = route_for(category)
            self.assertIn(
                route,
                text,
                f"SKILL.md does not mention route {route!r} (for category {category!r})",
            )

        rows = {
            m.group("category"): m.group("route")
            for m in _TABLE_ROW_RE.finditer(text)
            if m.group("category") != "category"
        }
        table_categories = set(rows) - {"category"}
        self.assertTrue(table_categories, "SKILL.md has no category/route table")
        self.assertEqual(
            table_categories,
            set(CATEGORIES),
            "SKILL.md's category table names a category outside CATEGORIES, "
            "or is missing one",
        )
        for category in CATEGORIES:
            self.assertEqual(
                rows[category],
                route_for(category),
                f"SKILL.md's table routes {category!r} to {rows[category]!r}, "
                f"module says {route_for(category)!r}",
            )


if __name__ == "__main__":
    unittest.main()
