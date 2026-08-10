# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0044/T04: structural oracle for the /groom-backlog skill.
# [FEAT-2026-0003/G2-LESSONS] — a prose artifact (SKILL.md) passes automated
# code gates trivially; this test is the falsifiable check that its required
# sections and load-bearing literals actually exist.

import pathlib
import unittest

import yaml

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "groom-backlog" / "SKILL.md"
_VENDORED = _REPO_ROOT / ".specfuse" / "skills" / "groom-backlog" / "SKILL.md"


def _frontmatter_and_body(text: str):
    assert text.startswith("---\n"), "SKILL.md must open with YAML frontmatter"
    _, _, rest = text.partition("---\n")
    fm_text, _, body = rest.partition("\n---\n")
    return yaml.safe_load(fm_text), body


class TestGroomBacklogSkill(unittest.TestCase):
    def test_skill_file_exists(self):
        self.assertTrue(_CANONICAL.is_file(), f"missing canonical skill: {_CANONICAL}")

    def test_frontmatter_name_and_trigger_phrases(self):
        text = _CANONICAL.read_text()
        frontmatter, _ = _frontmatter_and_body(text)
        self.assertEqual(frontmatter.get("name"), "groom-backlog")
        description = frontmatter.get("description") or ""
        self.assertIn("/groom-backlog", description)
        self.assertIn("groom the backlog", description)
        self.assertIn("update the queue", description)

    def test_license_header(self):
        text = _CANONICAL.read_text()
        self.assertIn("Copyright 2026 Specfuse Contributors", text)
        self.assertIn("Licensed under the Apache License, Version 2.0. See LICENSE.", text)

    def test_names_real_api_literals(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        for literal in (".specfuse/agent-policy.yml", "load_policy", "validate_agent_policy"):
            self.assertIn(literal, body)

    def test_does_not_section_states_no_auto_and_explicit_accept(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        self.assertIn("What this skill does NOT do", body)
        not_do_section = body.split("What this skill does NOT do", 1)[1]
        not_do_section = not_do_section.split("\n## ", 1)[0]
        self.assertIn("--auto", not_do_section)
        self.assertIn("explicit accept", not_do_section.lower())

    def test_states_only_file_written(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        self.assertIn(".specfuse/agent-policy.yml", body)
        # Some sentence in the body must assert this is the only file written.
        self.assertTrue(
            any(
                "only file" in line.lower() or "writes exactly one file" in line.lower()
                for line in body.splitlines()
            ),
            "expected a statement that .specfuse/agent-policy.yml is the only file written",
        )

    def test_escalation_framing_section(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        self.assertIn("Escalation framing", body)
        self.assertIn("operator-escalation.md", body)

    def test_queue_hygiene_pass_distinguishes_warn_and_error(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        self.assertIn("WARN: ", body)
        self.assertIn("ERROR: ", body)
        # Roughly locate the queue-hygiene discussion and confirm both
        # findings classes are distinguished (removal vs. unresolvable).
        lower = body.lower()
        self.assertIn("proposed for removal", lower)
        self.assertIn("unresolvable", lower)

    def test_empty_queue_is_valid_outcome(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        self.assertIn("empty queue", body.lower())
        self.assertIn("valid", body.lower())

    def test_vendored_copy_exists(self):
        self.assertTrue(_VENDORED.is_file(), f"missing vendored skill: {_VENDORED}")


if __name__ == "__main__":
    unittest.main()
