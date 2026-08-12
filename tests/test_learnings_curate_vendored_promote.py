# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Issue #1859: /learnings-curate's promote step could propose an apply-in-place
# write onto a core-vendored rules file (.specfuse/.vendored.json), which
# scripts/sync-scaffold.sh refuses to keep — discovered only after LEARNINGS.md
# and LEARNINGS-archive.md had already been mutated. The skill must read
# .vendored.json in §1, classify each rules/*.md as core-vendored or
# locally-owned, and route core-vendored promotes to a flag-only path that
# leaves LEARNINGS.md untouched and points at the upstream repo instead.

import pathlib
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "learnings-curate" / "SKILL.md"


def _skill_text() -> str:
    return _CANONICAL.read_text(encoding="utf-8")


def _section(body: str, heading: str) -> str:
    start = body.find(heading)
    assert start != -1, f"SKILL.md must have a '{heading}' section"
    rest = body[start + len(heading):]
    next_heading = rest.find("\n## ")
    return rest if next_heading == -1 else rest[:next_heading]


class TestLoadReadsVendoredManifest(unittest.TestCase):
    def test_section1_reads_vendored_json(self):
        load_section = _section(_skill_text(), "## §1 Load")
        self.assertIn(
            ".vendored.json", load_section,
            "§1 Load must read .specfuse/.vendored.json to classify rules files")


class TestPromoteRespectsVendoredSplit(unittest.TestCase):
    def test_promote_section_mentions_vendored_check(self):
        body = _skill_text()
        promote_section = _section(body, "**Promote.**") if "**Promote.**" in body else ""
        self.assertNotEqual(promote_section, "", "SKILL.md must have a '**Promote.**' block in §4")

    def test_promote_never_applies_in_place_to_vendored_file(self):
        body = _skill_text()
        idx = body.find("**Promote.**")
        self.assertNotEqual(idx, -1, "SKILL.md must have a '**Promote.**' block")
        next_heading = body.find("\n### ", idx)
        promote_block = body[idx:next_heading] if next_heading != -1 else body[idx:]
        lowered = promote_block.lower()
        self.assertIn("core-vendored", lowered)
        self.assertIn("flag-only", lowered)
        self.assertIn("specfuse/specfuse", lowered)
        self.assertIn(
            "leave", lowered,
            "vendored-file promotes must leave LEARNINGS.md untouched, not just flag")

    def test_hard_rule_5_names_the_vendored_split(self):
        body = _skill_text()
        hard_rules_start = body.find("## Hard rules")
        self.assertNotEqual(hard_rules_start, -1)
        rule5_start = body.find("5. **Scope boundary", hard_rules_start)
        self.assertNotEqual(rule5_start, -1, "Hard rule 5 (Scope boundary) not found")
        next_rule = body.find("\n6.", rule5_start)
        rule5 = body[rule5_start:next_rule] if next_rule != -1 else body[rule5_start:]
        self.assertIn(
            "core-vendored", rule5.lower(),
            "Hard rule 5 must name the core-vendored / locally-owned split, "
            "not blanket-glob rules/*.md")


if __name__ == "__main__":
    unittest.main()
