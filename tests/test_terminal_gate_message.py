#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# #1416: after a terminal gate closed with a hedged verdict, the driver reported
# its own correct behaviour as an "Inconsistency" and told the operator to
# hand-flip PLAN.md to `done` — the exact flip the verdict-coupling rule forbids
# and that `fire_terminal_flips` had just deliberately withheld.
#
# An operator who follows that advice marks a feature done with unmet acceptance
# criteria, defeating the guard FEAT-2026-0070 exists to enforce. The advice is
# most convincing precisely when it is most wrong: right after a long close, in a
# message labelled "Inconsistency".
#
# Fired on three consecutive features (FEAT-2026-0044, 0047, 0048) the night of
# 2026-08-09/10.

import unittest

from tests._loop_loader import load_loop

loop = load_loop()


class TestTerminalGateMessage(unittest.TestCase):
    """`terminal_gate_message` must distinguish three states a bare PLAN.md read cannot."""

    def _msg(self, verdict):
        return loop.terminal_gate_message(1, verdict)

    # -- the hedged case: withholding the flips is CORRECT ------------------

    def test_hedged_verdict_is_not_reported_as_an_inconsistency(self):
        for verdict in ("met_locally", "partially_met"):
            with self.subTest(verdict=verdict):
                self.assertNotIn("Inconsistency", self._msg(verdict))

    def test_hedged_verdict_does_not_advise_a_manual_flip(self):
        # The whole defect. Any wording that tells the operator to set PLAN.md
        # `done` here is advice to violate the verdict-coupling contract.
        for verdict in ("met_locally", "partially_met"):
            with self.subTest(verdict=verdict):
                message = self._msg(verdict)
                self.assertNotIn("active -> done", message)
                self.assertNotIn("status: done", message)

    def test_hedged_verdict_names_the_verdict_as_the_reason(self):
        message = self._msg("met_locally")
        self.assertIn("met_locally", message)

    def test_hedged_verdict_points_at_the_follow_up_record_and_acceptance(self):
        # The operator's real next step: read what is unmet, then accept it
        # deliberately through the one skill that records a reason.
        message = self._msg("partially_met")
        self.assertIn("Hedged-verdict follow-up record", message)
        self.assertIn("accept-hedged-close", message)

    # -- the genuine inconsistency: verdict permits, flips did not fire -----

    def test_met_verdict_without_the_flips_is_still_an_inconsistency(self):
        # This is what the original message was written for, and it must survive:
        # verdict `met` with PLAN.md not `done` is a real defect worth inspecting.
        message = self._msg("met")
        self.assertIn("Inconsistency", message)

    def test_absent_verdict_is_still_an_inconsistency(self):
        # A terminal gate that closed with no verdict at all is not a hedge —
        # it is a close that did not do its job, and must not be softened into
        # the reassuring message.
        for verdict in (None, ""):
            with self.subTest(verdict=verdict):
                self.assertIn("Inconsistency", self._msg(verdict))

    # -- every branch stays useful -----------------------------------------

    def test_every_branch_names_the_gate_number(self):
        for verdict in ("met", "met_locally", None):
            with self.subTest(verdict=verdict):
                self.assertIn("Gate 1", self._msg(verdict))

    def test_reassurance_appears_exactly_for_a_recognised_hedge(self):
        # There are three states, not two: a hedge is deliberate, a `met` that
        # did not flip is a defect, and NO usable verdict is also a defect —
        # `not_met` and an absent verdict must not be softened into "this is
        # working as intended", because neither has a follow-up record to accept.
        from specfuse.loop.closing_requirements import HEDGED_VERDICT_VALUES

        for verdict in ("met", "met_locally", "partially_met", "not_met", None, "", "garbage"):
            with self.subTest(verdict=verdict):
                reassures = "not a defect" in self._msg(verdict)
                self.assertEqual(verdict in HEDGED_VERDICT_VALUES, reassures)

    def test_not_met_is_flagged_rather_than_reassured(self):
        # `not_met` says the feature failed its own criteria. It is not a hedge
        # to accept, and /accept-hedged-close explicitly refuses it.
        message = self._msg("not_met")
        self.assertIn("Inconsistency", message)
        self.assertNotIn("accept-hedged-close", message)


if __name__ == "__main__":
    unittest.main()
