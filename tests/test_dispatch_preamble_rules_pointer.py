# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The dispatch preamble points at the injected binding block instead of
telling every session to read `.specfuse/rules/` in full (#3422).

Measured 2026-09-26: the "read in full" sentence cost every dispatched session
ten files and 11,573 words of tool reads on top of the 2,461 words CLAUDE.md
already injects, and those tokens rode along in every later turn's cache read.
"""
import unittest

from tests._loop_loader import load_loop

loop = load_loop()


class PreamblePointsAtTheBindingBlock(unittest.TestCase):
    def test_no_session_is_told_to_read_the_rules_in_full(self):
        self.assertNotIn("in full", loop.PROMPT_PREAMBLE)

    def test_preamble_names_the_injected_binding_block(self):
        self.assertIn(".claude/CLAUDE.md", loop.PROMPT_PREAMBLE)
        self.assertIn("only when your unit body names it", loop.PROMPT_PREAMBLE)

    def test_the_other_obligations_survive(self):
        for phrase in ("Do NOT run any git command", "narrow", "RESULT block",
                       ".specfuse/rules/result-contract.md"):
            self.assertIn(phrase, loop.PROMPT_PREAMBLE)


if __name__ == "__main__":
    unittest.main()
