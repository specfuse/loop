# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0076/T02: structural oracle for the /derive-agent-policy skill.
# [FEAT-2026-0003/G2-LESSONS] — a prose artifact (SKILL.md) passes automated
# code gates trivially; this test is the falsifiable check that its required
# sections and load-bearing literals actually exist.

import pathlib
import unittest

import yaml

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-agent-policy" / "SKILL.md"
_VENDORED = _REPO_ROOT / ".specfuse" / "skills" / "derive-agent-policy" / "SKILL.md"
_CANONICAL_PROMPT = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-agent-policy" / "PROMPT.md"
_VENDORED_PROMPT = _REPO_ROOT / ".specfuse" / "skills" / "derive-agent-policy" / "PROMPT.md"


def _frontmatter_and_body(text: str):
    assert text.startswith("---\n"), "SKILL.md must open with YAML frontmatter"
    _, _, rest = text.partition("---\n")
    fm_text, _, body = rest.partition("\n---\n")
    return yaml.safe_load(fm_text), body


class TestDeriveAgentPolicySkill(unittest.TestCase):
    def test_skill_file_exists(self):
        self.assertTrue(_CANONICAL.is_file(), f"missing canonical skill: {_CANONICAL}")

    def test_frontmatter_name_and_trigger_phrases(self):
        text = _CANONICAL.read_text()
        frontmatter, _ = _frontmatter_and_body(text)
        self.assertEqual(frontmatter.get("name"), "derive-agent-policy")
        description = frontmatter.get("description") or ""
        self.assertIn("/derive-agent-policy", description)
        self.assertIn("derive the agent policy", description.lower())

    def test_license_header(self):
        text = _CANONICAL.read_text()
        self.assertIn("Copyright 2026 Specfuse Contributors", text)
        self.assertIn("Licensed under the Apache License, Version 2.0. See LICENSE.", text)

    def test_prompt_file_exists(self):
        self.assertTrue(_CANONICAL_PROMPT.is_file(), f"missing canonical prompt: {_CANONICAL_PROMPT}")

    def test_names_real_api_literals(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        for literal in (
            "propose_policy_defaults",
            "validate_agent_policy",
            ".specfuse/agent-policy.yml",
        ):
            self.assertIn(literal, body)

    def test_names_proposed_values_as_evidence_backed(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        for literal in (
            "max_tokens_per_run",
            "max_items_per_day",
            "max_open_prs",
            "test_paths",
        ):
            self.assertIn(literal, body)
        lower = body.lower()
        self.assertIn("proposed", lower)
        self.assertIn("evidence", lower)

    def test_no_proposal_states_shipped_default_as_default(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        lower = body.lower()
        self.assertIn("shipped default", lower)
        self.assertIn("as a default", lower)

    def test_webhook_requires_env_var_name_not_url(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        self.assertIn("webhook_env", body)
        lower = body.lower()
        self.assertIn("environment-variable name", lower)
        self.assertIn("never a url", lower)
        self.assertIn("^[a-za-z_][a-za-z0-9_]*$", lower)

    def test_webhook_unset_silent_noop_documented(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        lower = body.lower()
        self.assertIn("resolve_webhook_url", body)
        self.assertIn("silently", lower)

    def test_staged_per_block_accept_and_draft_never_write(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        lower = body.lower()
        self.assertIn("staged", lower)
        self.assertIn("per-block accept", lower)
        self.assertIn("draft", lower)
        self.assertIn("never", lower)

    def test_escalation_framing_section(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        self.assertIn("Escalation framing", body)
        self.assertIn("operator-escalation.md", body)

    def test_does_not_section(self):
        text = _CANONICAL.read_text()
        _, body = _frontmatter_and_body(text)
        self.assertIn("What this skill does NOT do", body)

    def test_vendored_copy_exists(self):
        self.assertTrue(_VENDORED.is_file(), f"missing vendored skill: {_VENDORED}")
        self.assertTrue(_VENDORED_PROMPT.is_file(), f"missing vendored prompt: {_VENDORED_PROMPT}")


if __name__ == "__main__":
    unittest.main()
