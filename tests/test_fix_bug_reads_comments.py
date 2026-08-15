#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0080/T02 — /fix-bug Step 1 names a command that returns comments.

Step 1 already instructs the session to read "title, labels, body,
comments" but the command one line above it, `gh issue view
<issue-number>`, does not return comment bodies (verified live against
issue #1872 on 2026-08-12: default output ends at the issue body).
`gh issue view <n> --comments` is what surfaces them. This test pins
Step 1's command to the `--comments` form on both skill surfaces, and
that Step 1's prose explains why comments matter to a retry.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "plugins" / "specfuse" / "skills" / "fix-bug" / "SKILL.md"
VENDORED = REPO_ROOT / ".specfuse" / "skills" / "fix-bug" / "SKILL.md"


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _step_1_section(text: str) -> str:
    start = text.index("### 1. Fetch the issue")
    end = text.index("### 2.", start)
    return text[start:end]


class TestFixBugReadsComments(unittest.TestCase):

    def setUp(self):
        self.canonical_text = CANONICAL.read_text(encoding="utf-8")
        self.vendored_text = VENDORED.read_text(encoding="utf-8")

    def test_step_1_command_returns_comments(self):
        for label, text in (
            ("canonical", self.canonical_text),
            ("vendored", self.vendored_text),
        ):
            step_1 = _step_1_section(text)
            self.assertIn(
                "gh issue view <issue-number> --comments", step_1,
                f"{label} SKILL.md Step 1 does not name a command that "
                f"returns comment bodies (missing --comments)")

    def test_step_1_explains_why_comments_matter_to_a_retry(self):
        flat = _collapse_whitespace(self.canonical_text)
        self.assertIn(
            "prior run", flat,
            "Step 1 does not explain that a prior run may have been "
            "answered by an operator")
        self.assertIn(
            "operator", flat,
            "Step 1 does not mention operator guidance as the reason "
            "comments matter")

    def test_canonical_and_vendored_skill_are_byte_identical(self):
        result = subprocess.run(
            ["diff", str(CANONICAL), str(VENDORED)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            f"plugins/specfuse/skills/fix-bug/SKILL.md and "
            f".specfuse/skills/fix-bug/SKILL.md have drifted — diff "
            f"output: {result.stdout!r}")


if __name__ == "__main__":
    unittest.main()
