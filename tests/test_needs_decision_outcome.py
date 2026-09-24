#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`/fix-bug` can say the direction is a decision, not just the size (#3390).

The skill had one way to decline -- `refused` -- keyed on **size and risk**:
the work is too large, promote it to a feature. It had no outcome for a
different situation: the fix is small, but *which* fix is correct is a decision
the issue does not make. A headless session cannot ask, so it picked.

Measured cost: a lane PR made a generated service block on a soft-delete
archive, reversing a decision a feature gate had explicitly recorded, and would
have made any aggregate with a child permanently un-archivable. It passed all
six merge guardrails and reached `eligible`. The session was not incompetent --
it spent 17.7 minutes and produced a coherent change with a passing test. It was
asked to decide something the issue left open, with no way to say so.

`needs_decision` is that way. It is distinct from `refused` because the remedies
differ: `refused` sends the operator to `/draft-feature` to plan bigger work,
while this one asks them a question whose answer is usually one line. Routing it
through `refused` would hand them the wrong instruction.

The asymmetry is what makes the direction safe: over-use costs throughput and
produces an escalation a human reads; under-use merges a wrong fix and closes
the issue behind it.
"""

from __future__ import annotations

import unittest

from specfuse.loop import bug_lane_run
from specfuse.monitor.autofix_invoke import (
    OUTCOMES,
    classify_outcome,
    outcome_was_named,
)


class TheOutcomeSet(unittest.TestCase):

    def test_needs_decision_is_a_member(self):
        self.assertIn("needs_decision", OUTCOMES)

    def test_the_three_original_outcomes_survive(self):
        for outcome in ("refused", "could_not_proceed", "completed"):
            self.assertIn(outcome, OUTCOMES)

    def test_no_outcome_is_a_substring_of_another(self):
        # classify_outcome matches by substring and requires exactly one hit,
        # so an outcome containing another would make every session naming the
        # longer one classify as unreadable.
        for outer in OUTCOMES:
            for inner in OUTCOMES:
                if outer is inner:
                    continue
                self.assertNotIn(
                    inner, outer,
                    f"{inner!r} inside {outer!r} breaks classify_outcome",
                )


class Classification(unittest.TestCase):

    def test_a_session_naming_it_is_classified_as_such(self):
        text = "## Headless outcome\n\nneeds_decision\n\nTwo fixes are defensible."

        self.assertEqual("needs_decision", classify_outcome(text))
        self.assertTrue(outcome_was_named(text))

    def test_naming_it_alongside_another_still_fails_closed(self):
        text = "needs_decision ... completed"

        self.assertEqual("could_not_proceed", classify_outcome(text))
        self.assertFalse(outcome_was_named(text))

    def test_an_unclassifiable_result_is_still_never_completed(self):
        self.assertEqual("could_not_proceed", classify_outcome(""))
        self.assertEqual("could_not_proceed", classify_outcome("no outcome here"))


class TheLaneEscalatesIt(unittest.TestCase):

    def test_it_escalates_rather_than_evaluating_guardrails(self):
        # A needs_decision session opened no PR, so there is nothing to
        # evaluate. Treating it as anything but escalating would send the lane
        # looking for a PR that does not exist (#3180's pr_not_found shape).
        self.assertIn("needs_decision", bug_lane_run._ESCALATING_OUTCOMES)

    def test_completed_is_not_escalating(self):
        self.assertNotIn("completed", bug_lane_run._ESCALATING_OUTCOMES)


class TheSkillDocumentsIt(unittest.TestCase):

    def _skill(self) -> str:
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        return (root / "plugins/specfuse/skills/fix-bug/SKILL.md").read_text(
            encoding="utf-8")

    def test_the_closed_set_no_longer_says_three(self):
        body = self._skill()

        self.assertIn("needs_decision", body)
        self.assertNotIn("no fourth outcome exists", body)

    def test_the_skill_says_what_distinguishes_it_from_refused(self):
        body = self._skill().lower()

        self.assertIn("who they affect", body)

    def test_the_mirrored_scaffold_copy_agrees(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        self.assertEqual(
            (root / "plugins/specfuse/skills/fix-bug/SKILL.md").read_text(
                encoding="utf-8"),
            (root / ".specfuse/skills/fix-bug/SKILL.md").read_text(
                encoding="utf-8"),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
