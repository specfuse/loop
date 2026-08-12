# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A stopped session's own reason survives into the escalation.

`classify_outcome` reduces an entire headless session to one of four words
and discards everything else -- including why it stopped. `/fix-bug`'s
contract is explicit that there is something to keep: *"The recorded reason
names which criterion fired."*

Observed 2026-08-12: a run refused #2075, #2053 and #757 in a row, producing
three **byte-identical** escalations whose entire content was "`/fix-bug`
reported `refused`". Nothing distinguished a correct refusal on architectural
work (#757, driver-editing, genuinely feature-scoped) from a questionable one
on a small skill-prose fix (#2053, `/fix-bug`'s own missing `closes #` line),
and the operator could not tell which without redoing the analysis by hand.
"""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.run import KIND_BUG, ActionItem
from specfuse.loop.bug_lane_run import (
    OUTCOME_COULD_NOT_PROCEED,
    OUTCOME_REFUSED,
    BugLaneResult,
)
from specfuse.monitor.autofix_invoke import extract_stop_rationale


class TestExtractingTheRationale(unittest.TestCase):
    def test_a_blocked_reason_field_is_preferred(self):
        out = (
            "some session chatter\n"
            "status: blocked\n"
            "blocked_reason: Step 2 feature indicator fired — adds a new "
            "frontmatter field\n"
        )

        self.assertEqual(
            extract_stop_rationale(out),
            "Step 2 feature indicator fired — adds a new frontmatter field",
        )

    def test_a_wrapped_blocked_reason_is_joined(self):
        out = (
            "blocked_reason: the repro cannot be reduced to a falsifiable\n"
            "  failing test without deciding the intended contract first\n"
            "\nnext section\n"
        )

        rationale = extract_stop_rationale(out)

        self.assertIn("falsifiable", rationale)
        self.assertIn("intended contract", rationale)
        self.assertNotIn("next section", rationale)

    def test_without_a_field_the_tail_is_used(self):
        """A session's closing explanation lands at the end of its output."""
        out = "step 1\nstep 2\nrefused\nThis is feature-scoped: it changes the driver contract."

        rationale = extract_stop_rationale(out)

        self.assertIn("feature-scoped", rationale)

    def test_empty_output_yields_an_empty_rationale(self):
        """Honest emptiness beats an invented reason."""
        self.assertEqual(extract_stop_rationale(""), "")
        self.assertEqual(extract_stop_rationale("   \n\n"), "")

    def test_the_rationale_is_bounded(self):
        out = "blocked_reason: " + ("x" * 5000)

        self.assertLessEqual(len(extract_stop_rationale(out)), 700)


class TestTheEscalationCarriesIt(unittest.TestCase):
    def _execute(self, outcome, rationale, unpushed=None):
        provider = BugsProvider(repo="o/r", runner=lambda *a, **k: None)
        item = ActionItem(item_id="bug-2053", kind=KIND_BUG)
        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(
                outcome=outcome,
                reason=None,
                pr_number=None,
                stop_rationale=rationale,
                unpushed_work=unpushed,
            ),
        ):
            return provider.execute(item)

    def test_a_refusal_quotes_the_session(self):
        outcome = self._execute(
            OUTCOME_REFUSED, "Step 2 feature indicator fired — adds a frontmatter field"
        )

        self.assertIn("Step 2 feature indicator", outcome.escalation.done_so_far)
        self.assertIn(">", outcome.escalation.done_so_far)

    def test_could_not_proceed_carries_it_too(self):
        outcome = self._execute(
            OUTCOME_COULD_NOT_PROCEED, "no clear repro in the issue body"
        )

        self.assertIn("no clear repro", outcome.escalation.done_so_far)

    def test_the_abandoned_work_payload_carries_it_as_well(self):
        """Both stop payloads, not just the empty-handed one."""
        outcome = self._execute(
            OUTCOME_COULD_NOT_PROCEED,
            "gh auth status failed at the push step",
            unpushed=("fix/issue-2053-x", 2),
        )

        self.assertIn("gh auth status failed", outcome.escalation.done_so_far)
        self.assertIn("fix/issue-2053-x", outcome.escalation.done_so_far)

    def test_a_missing_rationale_is_called_out_not_hidden(self):
        """Silence from the session is itself a reportable fact.

        The contract says a reason is recorded, so its absence means either
        the session broke its contract or the capture did — and either is
        worth the operator seeing rather than a body that reads as complete.
        """
        outcome = self._execute(OUTCOME_REFUSED, "")

        self.assertIn("recorded no reason", outcome.escalation.done_so_far)
        self.assertIn("contract", outcome.escalation.done_so_far)

    def test_two_different_refusals_no_longer_read_identically(self):
        """The whole point: three refusals in one run were indistinguishable."""
        a = self._execute(OUTCOME_REFUSED, "architectural: same-process dispatch")
        b = self._execute(OUTCOME_REFUSED, "scope creep found mid-flow")

        self.assertNotEqual(
            a.escalation.done_so_far, b.escalation.done_so_far
        )


if __name__ == "__main__":
    unittest.main()
