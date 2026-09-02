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
    """`terminal_gate_message` must distinguish four states a bare PLAN.md read
    cannot. FEAT-2026-0085 narrowed the verdict to `met` / `not_met`, so the
    deliberate-withholding case this file was written for is now `not_met` and
    the retired values get a migration branch of their own — but the shape #1416
    demands is unchanged: never report correct behaviour as an "Inconsistency",
    and never advise the flip the driver just withheld."""

    def _msg(self, verdict):
        return loop.terminal_gate_message(1, verdict)

    # -- the not_met case: withholding the flips is CORRECT -----------------

    def test_not_met_verdict_is_not_reported_as_an_inconsistency(self):
        self.assertNotIn("Inconsistency", self._msg("not_met"))

    def test_no_withholding_verdict_advises_a_manual_flip(self):
        # The whole defect. Any wording that tells the operator to set PLAN.md
        # `done` here is advice to violate the verdict-coupling contract —
        # equally true for a live `not_met` and for a retired value.
        for verdict in ("not_met", "met_locally", "partially_met"):
            with self.subTest(verdict=verdict):
                message = self._msg(verdict)
                self.assertNotIn("active -> done", message)
                self.assertNotIn("status: done", message)

    def test_withholding_verdict_names_the_verdict_as_the_reason(self):
        for verdict in ("not_met", "met_locally"):
            with self.subTest(verdict=verdict):
                self.assertIn(verdict, self._msg(verdict))

    def test_not_met_points_at_the_tracked_follow_ups(self):
        # The operator's real next step: read the follow-up filed per failed
        # criterion. A `not_met` close is discharged by doing that work, not
        # accepted — /accept-hedged-close has no role here and naming it would
        # re-offer the soft-success route this feature removed.
        message = self._msg("not_met")
        self.assertIn("FOLLOW-UPS.md", message)
        self.assertNotIn("accept-hedged-close", message)

    def test_legacy_verdict_points_at_the_migration_note(self):
        # Readable, not re-checkable. Sending this operator to a follow-up list
        # the close never had would be a dead end.
        for verdict in ("met_locally", "partially_met"):
            with self.subTest(verdict=verdict):
                message = self._msg(verdict)
                self.assertNotIn("Inconsistency", message)
                self.assertIn("docs/methodology.md", message)

    # -- the genuine inconsistency: verdict permits, flips did not fire -----

    def test_met_verdict_without_the_flips_is_still_an_inconsistency(self):
        # This is what the original message was written for, and it must survive:
        # verdict `met` with PLAN.md not `done` is a real defect worth inspecting.
        message = self._msg("met")
        self.assertIn("Inconsistency", message)

    def test_absent_verdict_is_still_an_inconsistency(self):
        # A terminal gate that closed with no verdict at all is not a `not_met`
        # — it is a close that did not do its job, and must not be softened into
        # the reassuring message.
        for verdict in (None, "", "garbage"):
            with self.subTest(verdict=verdict):
                self.assertIn("Inconsistency", self._msg(verdict))

    # -- every branch stays useful -----------------------------------------

    def test_every_branch_names_the_gate_number(self):
        for verdict in ("met", "not_met", "met_locally", None):
            with self.subTest(verdict=verdict):
                self.assertIn("Gate 1", self._msg(verdict))

    def test_reassurance_appears_exactly_for_a_deliberate_withholding(self):
        # There are three outcomes, not two: `not_met` is deliberate, a `met`
        # that did not flip is a defect, and NO usable verdict is also a defect
        # — an absent or unrecognised verdict must not be softened into "this is
        # working as intended", because neither has a follow-up list to read.
        # A retired value is its own case: correct behaviour, but the operator's
        # route is the migration note, so it is not reassured either.
        for verdict in ("met", "met_locally", "partially_met", "not_met",
                        None, "", "garbage"):
            with self.subTest(verdict=verdict):
                reassures = "not a defect" in self._msg(verdict)
                self.assertEqual(verdict == "not_met", reassures)


if __name__ == "__main__":
    unittest.main()
