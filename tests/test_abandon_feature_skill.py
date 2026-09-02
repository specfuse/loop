#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#3066: /abandon-feature must rewrite the detail-section Status marker.

Sibling of #3053. The skill's write plan stated that the roadmap detail
section's `**Status: <value>.**` marker is prose it does not edit, while
`lint_roadmap.check_section_status_matches_row` ERRORs whenever that marker
disagrees with the row and runs inside the driver's baseline probe and the
real-tree lint test. `/block-feature`, `/pick-feature` (#3053) and
`fire_terminal_flips` all rewrite the marker for exactly that reason.

These tests pin the skill text the way tests/test_pick_feature_skill.py does.
Byte-identity between `plugins/specfuse/skills/` and `.specfuse/skills/` is
asserted generically by tests/test_skills_vendored_in_sync.py, not here.
"""

from __future__ import annotations

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_SKILL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "abandon-feature" / "SKILL.md"


def _skill_text() -> str:
    return _SKILL.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    m = re.search(rf"^#+ .*{re.escape(heading)}.*$", text, re.MULTILINE)
    assert m is not None, f"heading containing {heading!r} not found"
    start = m.end()
    nxt = re.search(r"^#+ ", text[start:], re.MULTILINE)
    return text[start:start + nxt.start()] if nxt else text[start:]


class TestAbandonRewritesTheDetailSectionMarker(unittest.TestCase):
    def test_skill_no_longer_claims_the_marker_is_untouched_prose(self):
        text = _skill_text()
        self.assertNotRegex(
            text, r"(?i)are not edited by this skill",
            "the write plan still says the detail-section marker is not edited",
        )
        self.assertNotRegex(
            text, r"(?i)Do not touch detail sections",
            "the hard rule still forbids touching the detail section",
        )

    def test_write_plan_rewrites_the_marker_to_abandoned(self):
        plan = _section(_skill_text(), "Compute the write plan")
        self.assertIsNotNone(
            re.search(r"\*\*Status: [a-z]+\.\*\*.*?\*\*Status: abandoned\.\*\*", plan, re.S),
            "step 2 must plan rewriting the section's `**Status: <prior>.**` "
            "marker to `**Status: abandoned.**`",
        )
        # An absent marker is not a finding; the skill must say so rather
        # than invent one.
        self.assertRegex(plan, r"(?i)(has|carries) no\s+`\*\*Status:\*\*`\s+line")

    def test_displayed_plan_shows_the_marker_write(self):
        shown = _section(_skill_text(), "Surface the write plan")
        self.assertRegex(shown, r"\*\*Status: [a-z]+\.\*\*\s*->\s*\*\*Status: abandoned\.\*\*")


if __name__ == "__main__":
    unittest.main()
