#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Issue #1844 — headless `/fix-bug` did not re-apply Step 2's feature

indicators to the diff it actually produced. On #1041 the triage-time
issue text looked bug-shaped, but the fix that got written minted a new
frontmatter field — a named Step 2 indicator ("frontmatter-field
addition") — and the run still reported `completed` instead of
`refused`, because Step 2 only ever ran once, before the fix existed.

This asserts SKILL.md now has a diff self-check step, run after gates
pass and before commit, that re-applies Step 2's indicators to the diff
itself and — in headless mode — resolves any indicator firing there to
`refused`, not `completed`.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import unittest


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "plugins" / "specfuse" / "skills" / "fix-bug" / "SKILL.md"
VENDORED = REPO_ROOT / ".specfuse" / "skills" / "fix-bug" / "SKILL.md"

DIFF_SELF_CHECK_HEADING = "Diff self-check"


class TestFixBugDiffSelfCheck(unittest.TestCase):

    def setUp(self):
        self.text = CANONICAL.read_text(encoding="utf-8")
        self.flat_text = _collapse_whitespace(self.text)

    def test_diff_self_check_step_exists_between_gates_and_commit(self):
        self.assertIn(
            DIFF_SELF_CHECK_HEADING, self.text,
            "SKILL.md does not document a diff self-check step")
        gates_idx = self.text.index("### 6. Run gates")
        commit_idx = self.text.index("### 7. Commit + push + PR")
        self_check_idx = self.text.index(DIFF_SELF_CHECK_HEADING)
        self.assertTrue(
            gates_idx < self_check_idx < commit_idx,
            "diff self-check must run after gates pass and before commit "
            "— otherwise a bad diff could already be pushed/PR'd before "
            "the check fires")

    def test_diff_self_check_reapplies_step_2_indicators_to_the_diff(self):
        self.assertIn(
            "Step 2", self.text[self.text.index(DIFF_SELF_CHECK_HEADING):
                                 self.text.index("### 7. Commit + push + PR")],
            "diff self-check must explicitly re-apply Step 2's indicators, "
            "not invent a parallel checklist")
        self.assertIn(
            "frontmatter", self.flat_text.lower(),
            "diff self-check must call out the frontmatter-field-addition "
            "indicator as mechanically detectable in a diff")

    def test_diff_self_check_blocks_commit_when_indicator_fires(self):
        self.assertIn(
            "Do not commit", self.text,
            "diff self-check must explicitly stop before commit/push/PR "
            "when a Step 2 indicator fires against the diff")

    def test_headless_mapping_includes_diff_self_check_row(self):
        self.assertIn(
            "Diff self-check", self.flat_text,
        )
        table_start = self.text.index("| Interactive halt (Method step) |")
        table_text = self.text[table_start:table_start + 3000]
        self.assertIn(
            "Diff self-check", table_text,
            "the headless halt-to-outcome mapping table must include a row "
            "for the diff self-check step")
        self.assertIn(
            "`refused`",
            table_text[table_text.index("Diff self-check"):
                       table_text.index("Diff self-check") + 400],
            "the diff self-check row must map to `refused`, not "
            "`could_not_proceed` or `completed` — a fired indicator here "
            "is the same refusal criterion as Step 2, discovered late")

    def test_completed_outcome_requires_a_clean_diff_self_check(self):
        headless_idx = self.text.index("## Headless mode")
        completed_block = self.text[headless_idx:headless_idx + 2000]
        self.assertIn(
            "diff self-check", completed_block.lower(),
            "the `completed` outcome definition must require the diff "
            "self-check found no indicator, not just that gates passed")

    def test_canonical_and_vendored_skill_are_byte_identical(self):
        result = subprocess.run(
            ["diff", str(CANONICAL), str(VENDORED)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            f"plugins/specfuse/skills/fix-bug/SKILL.md and "
            f".specfuse/skills/fix-bug/SKILL.md have drifted — diff output: "
            f"{result.stdout!r}")
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
