#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0070/T04: lint_plan's close-WU verdict-exempt set must include the
dispatch-transient statuses (in_progress, in_review) the driver itself writes
mid-session, without weakening the check for settled states.

Verifies:
  1. close WU status=in_progress, no verdict -> zero errors (dispatch-transient).
  2. close WU status=in_review, no verdict -> zero errors (dispatch-transient).
  3. close WU status=ready, no verdict -> still errors (settled state; the
     verdict requirement is not dropped, only narrowed away from dispatch
     states already covered by assert_verdict_well_formed).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint
from tests.test_verdict_coupling import _make_single_gate_feature

lint_plan = load_lint()


class TestDispatchStatesAreExempt(unittest.TestCase):

    def test_in_progress_close_wu_without_verdict_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat = _make_single_gate_feature(
                Path(tmpdir),
                close_wu_id="FEAT-2026-9998/G1-CLOSE",
                close_wu_type="close",
                close_status="in_progress",
                close_verdict=None,
            )
            errs = lint_plan.lint(feat)
            verdict_errs = [e for e in errs if "verdict" in e and "close-type" in e]
            self.assertFalse(
                verdict_errs,
                f"in_progress close WU (driver-dispatched, verdict not yet "
                f"written) must not trigger the verdict check; errs={errs}",
            )

    def test_in_review_close_wu_without_verdict_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat = _make_single_gate_feature(
                Path(tmpdir),
                close_wu_id="FEAT-2026-9998/G1-CLOSE",
                close_wu_type="close",
                close_status="in_review",
                close_verdict=None,
            )
            errs = lint_plan.lint(feat)
            verdict_errs = [e for e in errs if "verdict" in e and "close-type" in e]
            self.assertFalse(
                verdict_errs,
                f"in_review close WU (gate set running, verdict not yet "
                f"written) must not trigger the verdict check; errs={errs}",
            )


class TestSettledStateStillRequiresVerdict(unittest.TestCase):
    """The exempt set narrows plan-lint's overlap with
    assert_verdict_well_formed; it must not make the verdict optional for a
    close WU that has settled into a state requiring one.
    """

    def test_ready_close_wu_without_verdict_still_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat = _make_single_gate_feature(
                Path(tmpdir),
                close_wu_id="FEAT-2026-9998/G1-CLOSE",
                close_wu_type="close",
                close_status="ready",
                close_verdict=None,
            )
            errs = lint_plan.lint(feat)
            verdict_errs = [e for e in errs if "verdict" in e and "close-type" in e]
            self.assertTrue(
                verdict_errs,
                f"ready close WU missing verdict must still error — the "
                f"dispatch-transient exemption is narrow, not a blanket "
                f"opt-out; errs={errs}",
            )


if __name__ == "__main__":
    unittest.main()
