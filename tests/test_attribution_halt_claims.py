#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The attribution halt stops claiming nothing was dispatched (#3330 defect 2).

`format_preexisting_gate_failure` was written for a gate-entry probe
(FEAT-2026-0051/T03), where "zero work units were dispatched" was simply true.
FEAT-2026-0109/T01 then removed the gate-entry probe. Attribution is now the
only path that renders this message, and on that path a unit *was* dispatched:
its attempt failed, the driver reset the tree and re-ran the checks to ask
whether the failure predated the attempt.

So every fresh-gate claim in the message is false exactly when it is shown,
unless the gate already has `done` units (the `resumed` branch, #360, which
only fires once something landed).

The cost is not cosmetic. In the reported incident the checks failed on
**gitignored output the failed attempt itself produced** -- `git reset --hard`
restores tracked files and leaves ignored ones behind. The message told the
operator no unit had run and offered a tracked-file diff as proof the failure
predated the feature, so they went looking at the integration branch. It took
a bisect across three commits to find the real cause, because the proof reads
as conclusive and a tracked diff structurally cannot see an untracked input.

These tests pin the honest claims. They do not fix defect 1 -- the probe still
runs against whatever ignored state the attempt left -- which needs a design
decision (clean worktree, declared wipe set, or reproduce-at-head_before) and
stays open on #3330.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

loop = load_loop()

FAILING = [{
    "gate": "tests",
    "failure_class": "test_failure",
    "failure_signature": "everyModuleIsReachableFromABarrel",
}]

WU = "FEAT-2026-0173/T01"


def _attributed(**kw) -> str:
    return loop.format_preexisting_gate_failure(
        1, FAILING, {}, attributed_to=WU, **kw
    )


class AttributedHaltDoesNotClaimNothingRan(unittest.TestCase):

    def test_it_does_not_say_zero_units_were_dispatched(self):
        msg = _attributed()

        self.assertNotIn("Zero work units were dispatched", msg)
        self.assertNotIn("before any work unit was dispatched", msg)

    def test_it_does_not_say_the_feature_touched_no_file(self):
        msg = _attributed()

        self.assertNotIn("before this feature touched any file", msg)

    def test_it_names_the_unit_whose_failure_triggered_the_probe(self):
        msg = _attributed()

        self.assertIn(WU, msg)

    def test_it_says_the_probe_ran_after_that_attempt_was_reset(self):
        msg = _attributed().lower()

        self.assertIn("reset", msg)


class TheProofNamesWhatItCannotSee(unittest.TestCase):
    """#3371's narrow ask: a tracked diff cannot rule out untracked state, so
    the message must not state the conclusion more strongly than it supports."""

    def test_untracked_and_ignored_paths_are_named_as_outside_the_comparison(self):
        msg = _attributed().lower()

        self.assertIn("ignored", msg)
        self.assertTrue(
            "untracked" in msg or "outside" in msg,
            "the message must say the comparison does not cover untracked "
            "state, or a reader takes a tracked diff as conclusive (#3371)",
        )

    def test_it_does_not_call_the_tracked_diff_proof_the_failure_predates(self):
        msg = _attributed()

        self.assertNotIn(
            "so the failure predates this feature", msg,
            "a tracked-file diff is consistent with both 'pre-existing' and "
            "'left behind by this run's own failed attempt' (#3371)",
        )

    def test_reset_hard_leaving_ignored_files_is_spelled_out(self):
        msg = _attributed().lower()

        self.assertIn("reset --hard", msg)

    def test_the_operator_is_pointed_at_leftover_state_first(self):
        msg = _attributed()
        steps = msg[msg.index("What to do next:"):]
        first = steps.split("\n")[1].lower()

        self.assertTrue(
            "ignored" in first or "untracked" in first or "leftover" in first,
            "the cheapest check must come first: the reported incident cost a "
            "three-commit bisect because step 1 sent the operator to the "
            f"integration branch. Got: {first!r}",
        )


class TheUnattributedPathsAreUnchanged(unittest.TestCase):
    """Attribution framing must not leak into the two paths that earned their
    claims: a resumed gate, and a caller that names no attributing unit."""

    def test_a_resumed_gate_still_warns_that_its_own_work_may_be_at_fault(self):
        msg = loop.format_preexisting_gate_failure(
            1, FAILING, {}, done_unit_ids=["FEAT-2026-0173/T01"],
        )

        self.assertIn("ALREADY LANDED WORK", msg)
        self.assertNotIn("Zero work units were dispatched", msg)

    def test_no_attribution_keeps_the_original_wording(self):
        msg = loop.format_preexisting_gate_failure(1, FAILING, {})

        self.assertIn("Zero work units were dispatched", msg)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
