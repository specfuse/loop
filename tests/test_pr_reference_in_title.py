# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The issue reference counts in a PR title as well as its body (#3366).

`/specfuse:fix-bug`'s `gh pr create` example puts `(closes #<n>)` in the
**title**; its body template opens with `Closes #<n>.` GitHub treats the two
equivalently and closes the issue from either. The lane matched only the body.

Observed: a run fixed clabonte/generator#1916 end to end — real fix, pushed
branch, PR opened with a regression test, reported `completed` — and then
escalated `pr_not_found`, because the reference lived only in the title. The
work was finished, no guardrail ever evaluated it, nothing merged, and the
escalation read as though no fix existed.

The selection side has the same blind spot and a worse consequence:
`_has_open_pr` gates "does this issue already have a fix in review", so a
title-only PR would let the issue be dispatched **again**.
"""

from __future__ import annotations

import unittest

from specfuse.loop.bug_lane_run import pr_closes_issue


class MatchesEitherPlace(unittest.TestCase):

    def test_body_reference_still_matches(self):
        self.assertTrue(pr_closes_issue("Closes #1916.", 1916))

    def test_title_reference_matches(self):
        self.assertTrue(pr_closes_issue(
            "", 1916,
            title="fix(languages): fold framework axis into register() (closes #1916)",
        ))

    def test_neither_place_does_not_match(self):
        self.assertFalse(pr_closes_issue("no reference here", 1916, title="fix: something"))

    def test_case_insensitive_in_the_title_too(self):
        self.assertTrue(pr_closes_issue("", 1916, title="fix: thing (Closes #1916)"))

    def test_word_boundary_is_preserved_in_the_title(self):
        # A bare substring test made `#198` match a PR closing `#1984`; the
        # boundary that fixed it must hold on the new surface too.
        self.assertFalse(pr_closes_issue("", 198, title="fix: thing (closes #1984)"))
        self.assertTrue(pr_closes_issue("", 1984, title="fix: thing (closes #1984)"))

    def test_title_defaults_empty_so_existing_callers_are_unaffected(self):
        self.assertTrue(pr_closes_issue("Closes #7.", 7))
        self.assertFalse(pr_closes_issue("unrelated", 7))


class SelectionSeesTitleOnlyPRs(unittest.TestCase):
    """The blind spot with the worse consequence: a title-only PR must count as
    'already has a fix in review', or the issue is dispatched a second time."""

    def test_has_open_pr_matches_a_title_only_reference(self):
        from specfuse.agent.providers.bugs import _has_open_pr
        from specfuse.agent.state import AgentSnapshot, PRSummary

        snapshot = AgentSnapshot(
            queue=(), triage_auto=False, bug_automerge=False, bug_lane_limits={},
            issues=(), issues_error=None,
            prs=(PRSummary(
                number=1927,
                title="fix(languages): fold framework axis (closes #1916)",
                labels=(),
                body="Root cause. Fix. Tests. Verification.",
            ),),
            prs_error=None, features=(),
        )
        self.assertTrue(_has_open_pr(snapshot, 1916))
        self.assertFalse(_has_open_pr(snapshot, 1915))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
