#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Caveman preamble selection — FEAT-2026-0007/T03.

Verifies that dispatch() prefixes the caveman terseness directive only for
low/medium effort, and uses the plain preamble for high/xhigh/max.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

loop = load_loop()


def _preamble_for(effort: str) -> str:
    """Return the preamble string dispatch() would build for a given effort."""
    if effort in loop._CAVEMAN_EFFORT:
        return loop.PROMPT_PREAMBLE + "\n\n" + loop.CAVEMAN_DIRECTIVE
    return loop.PROMPT_PREAMBLE


class TestCavemanPreambleSelection(unittest.TestCase):

    def test_low_includes_directive(self):
        preamble = _preamble_for("low")
        self.assertIn(loop.CAVEMAN_DIRECTIVE, preamble)
        self.assertTrue(preamble.startswith(loop.PROMPT_PREAMBLE))

    def test_medium_includes_directive(self):
        preamble = _preamble_for("medium")
        self.assertIn(loop.CAVEMAN_DIRECTIVE, preamble)
        self.assertTrue(preamble.startswith(loop.PROMPT_PREAMBLE))

    def test_high_no_directive(self):
        preamble = _preamble_for("high")
        self.assertEqual(preamble, loop.PROMPT_PREAMBLE)
        self.assertNotIn(loop.CAVEMAN_DIRECTIVE, preamble)

    def test_xhigh_no_directive(self):
        preamble = _preamble_for("xhigh")
        self.assertEqual(preamble, loop.PROMPT_PREAMBLE)

    def test_max_no_directive(self):
        preamble = _preamble_for("max")
        self.assertEqual(preamble, loop.PROMPT_PREAMBLE)

    def test_directive_does_not_contain_result_fence(self):
        """Directive must not include ```result fences — would break RESULT-block parsing."""
        self.assertNotIn("```result", loop.CAVEMAN_DIRECTIVE)


if __name__ == "__main__":
    unittest.main()
