# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0041/T02: the `/diagnose-issue` skill exists on all three surfaces
and states its contract correctly.

A skill has three surfaces — canonical (`plugins/specfuse/skills/`), vendored
(`.specfuse/skills/`), and a `.claude/skills/` discovery symlink into the
vendored copy. FEAT-2026-0072 fixed the exact failure of skipping one: four
skills sat invisible to Claude Code for seven weeks. This test asserts all
three exist and stay in sync for `diagnose-issue`, on top of (not instead of)
the repo-wide `tests/test_skill_discovery_links.py` guard.

It also asserts the skill's own contract: it renders through
`specfuse/monitor/diagnosis.py` rather than hand-writing the comment body, and
it states its hard rules (one comment per invocation, never closes the
finding issue, honest low confidence over a guess) and the binding
escalation-framing section every skill in this repo carries.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "plugins" / "specfuse" / "skills" / "diagnose-issue" / "SKILL.md"
VENDORED = REPO_ROOT / ".specfuse" / "skills" / "diagnose-issue" / "SKILL.md"
DISCOVERY_LINK = REPO_ROOT / ".claude" / "skills" / "diagnose-issue"
SPECFUSE_SKILLS = REPO_ROOT / ".specfuse" / "skills"


class TestDiagnoseIssueSkill(unittest.TestCase):

    def test_skill_present_on_all_three_surfaces(self):
        self.assertTrue(
            CANONICAL.is_file(),
            f"canonical skill source missing: {CANONICAL}")
        self.assertTrue(
            VENDORED.is_file(),
            f"vendored skill copy missing: {VENDORED} — run scripts/sync-scaffold.sh")
        self.assertTrue(
            DISCOVERY_LINK.exists(),
            f".claude/skills/ discovery entry missing: {DISCOVERY_LINK}")
        self.assertTrue(
            DISCOVERY_LINK.is_symlink(),
            ".claude/skills/diagnose-issue must be a symlink, not a copy")
        resolved = DISCOVERY_LINK.resolve()
        specfuse_skills_real = SPECFUSE_SKILLS.resolve()
        self.assertTrue(
            resolved.is_relative_to(specfuse_skills_real),
            f".claude/skills/diagnose-issue resolves to {resolved}, "
            f"outside {specfuse_skills_real}")

        canonical_bytes = CANONICAL.read_bytes()
        vendored_bytes = VENDORED.read_bytes()
        self.assertEqual(
            canonical_bytes, vendored_bytes,
            "canonical and vendored SKILL.md copies are not byte-identical "
            "— run scripts/sync-scaffold.sh")

    def test_renders_through_diagnosis_module_not_hand_written(self):
        body = CANONICAL.read_text()
        self.assertIn(
            "diagnosis.py", body,
            "SKILL.md must instruct rendering through specfuse/monitor/diagnosis.py")
        self.assertIn(
            "render(diagnosis)", body,
            "SKILL.md must name the render() call, not just the module")

        # No literal marker template of its own — one contract, one home.
        self.assertNotIn(
            "specfuse:diagnosis", body,
            "SKILL.md must not restate diagnosis.py's marker literal")
        self.assertNotIn(
            "**Root cause:**", body,
            "SKILL.md must not restate diagnosis.py's rendered section headers")
        self.assertNotIn(
            "**Candidate fix:**", body,
            "SKILL.md must not restate diagnosis.py's rendered section headers")

    def test_carries_escalation_framing_section(self):
        body = CANONICAL.read_text()
        self.assertIn(
            "## Escalation framing", body,
            "SKILL.md must carry the escalation-framing section every skill binds to")
        self.assertIn(
            "operator-escalation.md", body,
            "escalation-framing section must reference the binding rule file")

    def test_states_one_comment_per_invocation_rule(self):
        body = CANONICAL.read_text()
        hard_rules = _hard_rules_section(body)
        self.assertIn(
            "one", hard_rules.lower(),
            "Hard rules must state the one-comment-per-invocation rule")
        self.assertIn(
            "comment", hard_rules.lower(),
            "Hard rules must state the one-comment-per-invocation rule")

    def test_states_never_close_the_issue_rule(self):
        body = CANONICAL.read_text()
        hard_rules = _hard_rules_section(body)
        self.assertIn(
            "never closes", hard_rules.lower(),
            "Hard rules must state the never-close-the-issue rule explicitly")

    def test_states_honest_low_confidence_rule(self):
        body = CANONICAL.read_text()
        hard_rules = _hard_rules_section(body)
        self.assertIn(
            "confidence", hard_rules.lower(),
            "Hard rules must state the honest-low-confidence-over-a-guess rule")
        self.assertIn(
            "evidence", hard_rules.lower(),
            "Hard rules must tie the low-confidence rule to evidence not supporting a guess")


def _hard_rules_section(body: str) -> str:
    """Slice out the `## Hard rules` section body, up to the next `## ` heading."""
    start = body.find("## Hard rules")
    assert start != -1, "SKILL.md must have a '## Hard rules' section"
    rest = body[start + len("## Hard rules"):]
    next_heading = rest.find("\n## ")
    return rest if next_heading == -1 else rest[:next_heading]


if __name__ == "__main__":
    unittest.main()
