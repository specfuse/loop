#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The bug lane can require proof that the new test was red on the base (#3377).

`evaluate_merge_guardrails` had six guardrails -- test evidence, CI green, diff
size, judge paths, provenance, a rolling merge cap -- and every one measures the
**form** of a PR. None measured whether it works: whether the symptom the issue
reports stopped reproducing.

Audited on one consumer repository: seven lane PRs, all seven passing all six
guardrails, four of them incomplete for the issue they claimed to close. Two of
those merged unattended and closed their issues behind a symptom that still
reproduced.

The check added here is the cheap, decidable half of that question. A test that
**passes at the merge base** proves nothing about the fix -- it is asserting
pre-existing behaviour, or testing something adjacent to the defect. Running the
PR's own added test at the base and requiring it to fail is two test runs and no
model judgement.

Its limit is stated honestly rather than papered over: this catches "the test
proves nothing", not "the test proves the wrong thing". A PR whose new test was
red on base for the *wrong reason* still passes it. Closing that gap needs the
issue to carry a machine-readable reproduction, which is a separate and much
bigger ask.

Default off. Turning it on without a way to run the check would decline every
merge on upgrade, which is a silent automerge shutdown rather than a guardrail.
"""

from __future__ import annotations

import unittest

from specfuse.loop.bug_lane import (
    REASON_ELIGIBLE,
    REASON_TEST_NOT_RED_ON_BASE,
    REASON_RED_ON_BASE_UNVERIFIED,
    evaluate_merge_guardrails,
)


class _State:
    def __init__(self, count=0):
        self._count = count

    def merges_last_24h(self):
        return self._count


def _evaluate(**overrides):
    kwargs = dict(
        changed_files=["tests/test_widget.py", "src/widget.py"],
        ci_conclusion="success",
        diff_lines=20,
        max_diff_lines=200,
        provenance={"kind": "triaged_issue", "ref": "issue-123"},
        max_merges_per_day=5,
        state_reader=_State(),
    )
    kwargs.update(overrides)
    return evaluate_merge_guardrails(**kwargs)


class WithoutTheRequirement(unittest.TestCase):
    """Unchanged for every deployment that has not asked for the check."""

    def test_a_clean_pr_is_still_eligible(self):
        self.assertTrue(_evaluate().eligible)

    def test_it_is_eligible_even_with_no_red_on_base_evidence(self):
        self.assertTrue(_evaluate(red_on_base=None).eligible)


class WithTheRequirement(unittest.TestCase):

    def test_a_test_proven_red_on_base_is_eligible(self):
        decision = _evaluate(require_red_on_base=True, red_on_base=True)

        self.assertTrue(decision.eligible)
        self.assertEqual(REASON_ELIGIBLE, decision.reason)

    def test_a_test_that_passed_on_base_declines(self):
        decision = _evaluate(require_red_on_base=True, red_on_base=False)

        self.assertFalse(decision.eligible)
        self.assertEqual(REASON_TEST_NOT_RED_ON_BASE, decision.reason)

    def test_an_unevaluated_check_declines_and_says_so_distinctly(self):
        # "The check said no" and "the check never ran" are different
        # situations with different fixes, and collapsing them is how a
        # guard comes to report clean because it could not look.
        decision = _evaluate(require_red_on_base=True, red_on_base=None)

        self.assertFalse(decision.eligible)
        self.assertEqual(REASON_RED_ON_BASE_UNVERIFIED, decision.reason)

    def test_a_non_boolean_verdict_is_treated_as_unverified(self):
        for value in ("yes", 1, [], {}):
            decision = _evaluate(require_red_on_base=True, red_on_base=value)
            self.assertEqual(REASON_RED_ON_BASE_UNVERIFIED, decision.reason)

    def test_it_does_not_override_an_earlier_decline(self):
        # Precedence matters: a red CI must still read as red CI, not as a
        # missing red-on-base proof.
        decision = _evaluate(
            require_red_on_base=True, red_on_base=None, ci_conclusion="failure")

        self.assertNotEqual(REASON_RED_ON_BASE_UNVERIFIED, decision.reason)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
