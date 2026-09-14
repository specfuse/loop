"""Lint tracer bullet for the `.claude/CLAUDE.md` binding block's word budget
(FEAT-2026-0111/T01). Measures; does not yet fail the build over the cap —
the block is over budget on HEAD today and T04 lands the trim.
"""

import unittest

from specfuse.loop.loop import (
    REPO_ROOT,
    BINDING_BLOCK_WORD_CAP,
    binding_block_word_count,
)


class BindingBlockWordCountTests(unittest.TestCase):
    def test_reads_actual_at_references_not_a_hardcoded_list(self):
        result = binding_block_word_count()
        self.assertIn("result-contract.md", "".join(result["files"]))
        self.assertGreaterEqual(len(result["files"]), 4)

    def test_total_is_sum_of_per_file_counts(self):
        result = binding_block_word_count()
        self.assertEqual(result["total"], sum(result["files"].values()))

    def test_cap_is_exposed_on_the_result(self):
        result = binding_block_word_count()
        self.assertEqual(result["cap"], BINDING_BLOCK_WORD_CAP)
        self.assertEqual(BINDING_BLOCK_WORD_CAP, 2500)

    def test_every_referenced_file_resolves_under_repo_root(self):
        result = binding_block_word_count()
        for relpath, count in result["files"].items():
            target = REPO_ROOT / relpath
            self.assertTrue(target.is_file(), f"{relpath} does not resolve to a file")
            self.assertGreater(count, 0, f"{relpath} counted zero words")

    def test_rules_local_distilled_file_is_wired_and_counted(self):
        result = binding_block_word_count()
        self.assertIn(".specfuse/rules-local/learnings-distilled.md", result["files"])


if __name__ == "__main__":
    unittest.main()
