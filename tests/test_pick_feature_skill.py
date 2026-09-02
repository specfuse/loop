#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#3053: /pick-feature must write all three status surfaces.

A feature's status lives in three places: the roadmap row's status column,
`PLAN.md` frontmatter, and the detail section's own `**Status: <value>.**`
marker. `lint_roadmap.check_section_status_matches_row` (ERROR) holds the
marker to the row, `fire_terminal_flips` rewrites it at archive time, and
`/block-feature` rewrites it when it blocks. `/pick-feature` wrote only the
first two, so the very first `specfuse run` after a pick halted gate 1 on a
red baseline: the lint gate, the real-tree lint test, and coverage (because
the suite failed) all reported the one stale sentence.

These tests pin the skill text the way the sibling skill tests do: the step
that executes the pick must name the marker as a write, and every place the
skill counts its writes must agree on three. Byte-identity between
`plugins/specfuse/skills/` and `.specfuse/skills/` is asserted generically by
tests/test_skills_vendored_in_sync.py, not here.
"""

from __future__ import annotations

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_SKILL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "pick-feature" / "SKILL.md"


def _skill_text() -> str:
    return _SKILL.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Body of the markdown section whose heading line contains *heading*."""
    m = re.search(rf"^#+ .*{re.escape(heading)}.*$", text, re.MULTILINE)
    assert m is not None, f"heading containing {heading!r} not found"
    start = m.end()
    nxt = re.search(r"^#+ ", text[start:], re.MULTILINE)
    return text[start:start + nxt.start()] if nxt else text[start:]


class TestPickWritesTheDetailSectionMarker(unittest.TestCase):
    def test_step_6_names_the_detail_section_status_marker_as_a_write(self):
        step6 = _section(_skill_text(), "On explicit pick, flip status")
        self.assertIsNotNone(
            re.search(r"\*\*Status: planned\.\*\*.*?\*\*Status: active\.\*\*", step6, re.S),
            "step 6 must instruct rewriting the detail section's "
            "`**Status: planned.**` marker to `**Status: active.**`",
        )

    def test_step_6_scopes_the_marker_write_to_the_chosen_feature_section(self):
        step6 = _section(_skill_text(), "On explicit pick, flip status")
        self.assertRegex(step6, r"(?i)detail[\s-]+section")
        # The marker is optional in a section (nine real sections carry none);
        # the skill must say what to do when it is absent rather than invent it.
        self.assertRegex(step6, r"(?i)(has|carries) no `\*\*Status:\*\*` line")

    def test_hard_rule_and_not_do_list_count_three_writes(self):
        text = _skill_text()
        self.assertNotIn(
            "Two writes per accepted pick", text,
            "the hard rule still counts two writes; the detail marker is the third",
        )
        self.assertNotIn(
            "Two writes per pick", text,
            "the 'does NOT do' list still counts two writes",
        )
        self.assertRegex(text, r"(?i)three writes per (accepted )?pick")


if __name__ == "__main__":
    unittest.main()
