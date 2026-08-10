# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0076/T05: structural oracle for /derive-agent-policy's review-mode
# prose. Gate 1's tests/test_derive_agent_policy_skill.py covers the bootstrap
# half only and must stay untouched (criterion 8); this file is the
# falsifiable check that the review half -- reading an existing
# .specfuse/agent-policy.yml against the shipped baseline -- is actually
# described, using the exact literals specfuse/loop/policy_review.py ships.

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-agent-policy" / "SKILL.md"
_CANONICAL_PROMPT = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-agent-policy" / "PROMPT.md"

_REVIEW_HEADING_RE = re.compile(r"^## Review mode.*$", re.MULTILINE)
_NEXT_HEADING_RE = re.compile(r"^## .*$", re.MULTILINE)


def _review_mode_section(body: str) -> str:
    match = _REVIEW_HEADING_RE.search(body)
    assert match is not None, "SKILL.md must have a '## Review mode' section"
    start = match.end()
    next_match = _NEXT_HEADING_RE.search(body, start)
    end = next_match.start() if next_match else len(body)
    return body[start:end]


class TestReviewMode(unittest.TestCase):
    def test_prose_names_review_api_literals(self):
        text = _CANONICAL.read_text()
        for literal in ("review_agent_policy", "specfuse/loop/policy_review.py"):
            self.assertIn(literal, text)

    def test_entry_condition_both_branches_named(self):
        text = _CANONICAL.read_text()
        section = _review_mode_section(text)
        self.assertIn(".specfuse/agent-policy.yml", section)
        lower = section.lower()
        self.assertIn("exists", lower)
        self.assertIn("bootstrap", lower)

    def test_four_in_scope_keys_named(self):
        text = _CANONICAL.read_text()
        section = _review_mode_section(text)
        for literal in (
            "max_tokens_per_run",
            "max_items_per_day",
            "max_open_prs",
            "rules.bugs.test_paths",
        ):
            self.assertIn(literal, section)

    def test_readout_shape_named(self):
        text = _CANONICAL.read_text()
        section = _review_mode_section(text)
        lower = section.lower()
        for literal in ("current", "proposal", "baseline", "provenance"):
            self.assertIn(literal, lower)

    def test_baseline_match_is_hint_not_claim(self):
        text = _CANONICAL.read_text()
        section = _review_mode_section(text)
        lower = section.lower()
        self.assertIn("hint", lower)
        self.assertIn("not a claim", lower)
        self.assertIn("may never have been", lower)
        self.assertIn("reliably", lower)

    def test_measured_vs_converted_distinction(self):
        text = _CANONICAL.read_text()
        section = _review_mode_section(text)
        self.assertIn("measured", section)
        self.assertIn("converted", section)
        self.assertIn("rules.bugs.test_paths", section)

    def test_staged_per_block_accept_names_all_three_blocks(self):
        text = _CANONICAL.read_text()
        section = _review_mode_section(text)
        lower = section.lower()
        self.assertIn("staged", lower)
        for literal in ("`rules`", "`budgets`", "`escalation`"):
            self.assertIn(literal, section)

    def test_prompt_names_review_agent_policy(self):
        text = _CANONICAL_PROMPT.read_text()
        self.assertIn("review_agent_policy", text)


if __name__ == "__main__":
    unittest.main()
