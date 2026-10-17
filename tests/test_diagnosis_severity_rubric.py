# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0205/T02: one severity rubric shared by the headless prompt and
`/diagnose-issue`."""

from __future__ import annotations

import unittest

from tests._loop_loader import REPO_ROOT

from specfuse.agent.diagnose_invoke import build_invocation
from specfuse.loop.agent_policy import SEVERITY_VALUES
from specfuse.monitor.diagnosis import SEVERITY_RUBRIC

_SKILLS = (
    REPO_ROOT / ".specfuse" / "skills" / "diagnose-issue" / "SKILL.md",
    REPO_ROOT / "plugins" / "specfuse" / "skills" / "diagnose-issue" / "SKILL.md",
)


class TestRubric(unittest.TestCase):
    def test_one_line_per_value(self):
        values = [line.split(":", 1)[0] for line in SEVERITY_RUBRIC]
        self.assertEqual(len(values), len(set(values)))
        self.assertEqual(set(values), set(SEVERITY_VALUES))

    def test_prompt_carries_the_rubric(self):
        _, prompt = build_invocation(1, "t", "b", "o/r")
        for line in SEVERITY_RUBRIC:
            self.assertIn(line, prompt)
        self.assertIn("severity (optional)", prompt)

    def test_skill_copies_name_rubric_and_match(self):
        texts = [p.read_bytes() for p in _SKILLS]
        self.assertEqual(texts[0], texts[1])
        self.assertIn(b"SEVERITY_RUBRIC", texts[0])


if __name__ == "__main__":
    unittest.main()
