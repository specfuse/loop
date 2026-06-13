#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0015/T02H — CORRELATION_ID_RE must accept CLOSE-INTERMEDIATE suffix.

Four targeted regex tests; no fixture mutation required.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_lint

lint_plan = load_lint()


class TestCloseIntermediateIdAdmitted(unittest.TestCase):

    def test_correlation_id_re_accepts_g1_close_intermediate(self):
        self.assertIsNotNone(
            lint_plan.CORRELATION_ID_RE.match("FEAT-2026-0042/G1-CLOSE-INTERMEDIATE"))

    def test_correlation_id_re_accepts_g1_close_after_extension(self):
        # Regression: existing CLOSE suffix must still match.
        self.assertIsNotNone(
            lint_plan.CORRELATION_ID_RE.match("FEAT-2026-0042/G1-CLOSE"))

    def test_correlation_id_re_accepts_init_g1_close_intermediate(self):
        self.assertIsNotNone(
            lint_plan.CORRELATION_ID_RE.match("example-feature/G1-CLOSE-INTERMEDIATE"))

    def test_correlation_id_re_rejects_unknown_suffix(self):
        # Alternation must not open a gap — CLOSE-FOO is not a valid suffix.
        self.assertIsNone(
            lint_plan.CORRELATION_ID_RE.match("FEAT-2026-0042/G1-CLOSE-FOO"))


if __name__ == "__main__":
    unittest.main()
