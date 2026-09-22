# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The authoring rule teaches the reword the lint asks for (#3357).

`lint_plan` WARNs when a work unit declares a `produces:` path that also matches
one of its own Do-not-touch patterns, and since #3357 that warning names the
fix: reword the boundary to name the *surfaces* it protects rather than the file
this unit also produces.

The shape that trips it is not an edge case. A hygiene unit exists to make a
bounded fix inside a file a previous unit built, so it has to declare that file
in `produces:` *and* protect almost all of it — and §7 of the authoring skill,
which is where an author is told how to write a hygiene unit, said to name the
broken file in `produces:` without saying anything about how to word the
boundary. The author met the warning with no guidance in the rule that
generated the shape.

Worse than unhelpful: FEAT-2026-0113's `T08H` wrote "every other function in
`specfuse/loop/triage.py`", which read literally forbids editing the one
function that unit existed to fix. It passed only because the acceptance
criteria named the target unambiguously, so the boundary and the criteria
contradicted each other and only the criteria were load-bearing.

This guards the pairing rather than the prose: whatever wording either side
uses, the authoring rule must teach surface-naming, so the lint's recommended
fix and the rule that produces the shape cannot drift apart again.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "plugins/specfuse/skills/authoring-work-units/SKILL.md"
MIRROR = REPO_ROOT / ".specfuse/skills/authoring-work-units/SKILL.md"
LINT = REPO_ROOT / "specfuse/loop/lint_plan.py"


def _section_7(text: str) -> str:
    """§7, the hygiene-work-unit section, up to the next top-level heading."""
    match = re.search(r"^## 7\. .*?$(.*?)(?=^## \d+\. )", text, re.S | re.M)
    assert match, "authoring skill has no '## 7.' section"
    return match.group(1)


class HygieneBoundaryGuidance(unittest.TestCase):

    def test_the_lint_still_recommends_naming_surfaces(self):
        # If this fails the lint changed its advice, and the rule below is
        # now teaching the wrong reword rather than merely a stale one.
        self.assertIn("surfaces it protects", LINT.read_text(encoding="utf-8"))

    def test_section_7_tells_the_author_how_to_word_the_boundary(self):
        body = _section_7(SKILL.read_text(encoding="utf-8"))

        self.assertIn(
            "surface", body.lower(),
            "§7 tells an author to put the broken file in `produces:`, which is "
            "exactly the shape that trips the Do-not-touch collision warning. "
            "It must also tell them to word the boundary by naming the "
            "surfaces it protects, or the rule generates a warning it gives no "
            "way to answer (#3357).",
        )

    def test_section_7_warns_against_the_whole_file_wording(self):
        body = _section_7(SKILL.read_text(encoding="utf-8")).lower()

        self.assertTrue(
            "every other function in" in body or "whole file" in body,
            "§7 must show the wording that actually went wrong — a boundary "
            "phrased over a whole file contradicts the criteria of a unit that "
            "exists to edit one function in it (FEAT-2026-0113/T08H).",
        )

    def test_the_mirrored_copy_agrees(self):
        # plugins/ is canonical; .specfuse/ is the synced scaffold copy.
        self.assertEqual(
            SKILL.read_text(encoding="utf-8"),
            MIRROR.read_text(encoding="utf-8"),
            "plugins/ and .specfuse/ copies of the authoring skill diverged — "
            "run scripts/sync-scaffold.sh",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
