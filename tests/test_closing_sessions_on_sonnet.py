# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Closing sessions default to sonnet, like the judge that checks them (#3425)."""
import unittest

from tests._loop_loader import load_loop

loop = load_loop()


class ClosingTypesDefaultToSonnet(unittest.TestCase):
    def test_the_three_closing_types_default_to_sonnet_high(self):
        for wu_type in ("close", "close-intermediate", "plan-next"):
            self.assertEqual(loop.MODEL_BY_TYPE[wu_type], "sonnet", wu_type)
            self.assertEqual(loop.EFFORT_BY_TYPE[wu_type], "high", wu_type)

    def test_implementation_default_is_unchanged(self):
        self.assertEqual(loop.MODEL_BY_TYPE["implementation"], "sonnet")
        self.assertEqual(loop.EFFORT_BY_TYPE["implementation"], "medium")

    def test_the_judge_model_is_its_own_constant(self):
        # The judge already ran on sonnet before this change; the close no
        # longer needs a bigger model than the session that checks it.
        self.assertEqual(loop.JUDGE_MODEL, "sonnet")


if __name__ == "__main__":
    unittest.main()
