"""Blocking check on the `.claude/CLAUDE.md` binding block's word budget
(FEAT-2026-0111/T04). `check_binding_block_budget` is the severity flip:
T01 only measured against `BINDING_BLOCK_WORD_CAP`, this asserts against it,
and against `LEARNINGS_DISTILLED_WORD_CAP` first so a bloated distillate is
named directly rather than folded into the generic total failure.
"""

import tempfile
import unittest
from pathlib import Path

from specfuse.loop.loop import (
    LEARNINGS_DISTILLED_RULE_PATH,
    LEARNINGS_DISTILLED_WORD_CAP,
    REPO_ROOT,
    check_binding_block_budget,
)


class BindingBlockAllocationTests(unittest.TestCase):
    def test_tree_passes_the_blocking_check(self):
        check_binding_block_budget()

    def test_distilled_file_is_under_its_own_sub_budget(self):
        result = check_binding_block_budget()
        self.assertLessEqual(
            result["files"][LEARNINGS_DISTILLED_RULE_PATH],
            LEARNINGS_DISTILLED_WORD_CAP,
        )

    def test_sub_budget_failure_is_named_before_the_total_failure(self):
        oversized = "word " * (LEARNINGS_DISTILLED_WORD_CAP + 1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            distilled = tmp_path / LEARNINGS_DISTILLED_RULE_PATH
            distilled.parent.mkdir(parents=True, exist_ok=True)
            distilled.write_text(oversized, encoding="utf-8")

            claude_md = tmp_path / "CLAUDE.md"
            claude_md.write_text(
                "## Specfuse binding rules (read before any work-unit dispatch)\n"
                f"@{LEARNINGS_DISTILLED_RULE_PATH}\n",
                encoding="utf-8",
            )

            import specfuse.loop.loop as loop_module

            original_root = loop_module.REPO_ROOT
            loop_module.REPO_ROOT = tmp_path
            try:
                with self.assertRaises(AssertionError) as ctx:
                    check_binding_block_budget(claude_md)
            finally:
                loop_module.REPO_ROOT = original_root

        self.assertIn(LEARNINGS_DISTILLED_RULE_PATH, str(ctx.exception))
        self.assertIn("sub-budget", str(ctx.exception))

    def test_repo_root_is_unchanged_by_the_fixture(self):
        self.assertTrue((REPO_ROOT / ".claude" / "CLAUDE.md").is_file())


if __name__ == "__main__":
    unittest.main()
