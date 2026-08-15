# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""An escalation about an issue is recorded ON that issue.

The first unattended run (2026-08-11) filed eight tracking issues for eight
halted items. Each said "issue #N's PR was declined" and left the reader to
correlate it back to issue #N by hand; each was itself triaged `bug` and
became a candidate for the next run; and a halt that recurred filed one more
every time. `annotate_escalation` replaces that for any caller that knows
which issue the halt is about.

Also covers the run-summary line that said "(summary only, no issue filed)"
for four items whose escalation had in fact been filed.
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.run import (
    KIND_BUG,
    STATUS_ESCALATED,
    ActionItem,
    ActionOutcome,
    EscalationPayload,
    _record_escalation,
)
from specfuse.loop.escalation import NEEDS_HUMAN_LABEL, annotate_escalation

_OPTIONS = [("Do it", "pros", "cons"), ("Do not", "pros", "cons")]


def _payload(**overrides) -> EscalationPayload:
    fields = dict(
        done_so_far="ran the lane",
        issue_summary="the fix could not merge",
        decision_needed="merge by hand?",
        why_not_auto="a guardrail declined it",
        options=_OPTIONS,
        recommendation="review it",
        category="blocked-wu",
    )
    fields.update(overrides)
    return EscalationPayload(**fields)


class _Runner:
    """Records argv, and answers `gh issue view` with a configurable issue."""

    def __init__(self, *, body: str = "", comments: tuple = ()):
        self.calls: list[list] = []
        self._body = body
        self._comments = comments

    def __call__(self, argv, check: bool = False):
        self.calls.append(list(argv))
        if argv[:3] == ["gh", "issue", "view"]:
            import json

            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "body": self._body,
                        "comments": [{"body": c} for c in self._comments],
                    }
                ),
                stderr="",
            )
        if argv[:3] == ["gh", "issue", "create"]:
            # What `gh` really prints — the old fake returned "", which made
            # an unparseable id read as a successful filing.
            return SimpleNamespace(
                returncode=0, stdout="https://github.com/o/r/issues/4242\n", stderr=""
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def matching(self, prefix):
        return [c for c in self.calls if c[: len(prefix)] == prefix]


class TestAnnotateEscalation(unittest.TestCase):
    def test_comments_the_six_part_body_on_the_issue(self):
        runner = _Runner()

        returned = annotate_escalation(
            240, "bug-240", category="blocked-wu", repo="o/r",
            done_so_far="a", issue_summary="b", decision_needed="c",
            why_not_auto="d", options=_OPTIONS, recommendation="e",
            runner=runner,
        )

        self.assertEqual(returned, 240)
        comments = runner.matching(["gh", "issue", "comment", "240"])
        self.assertEqual(len(comments), 1)
        body = comments[0][comments[0].index("--body") + 1]
        for part in (
            "What has been done so far",
            "What this issue is about",
            "What decision is needed, and why",
            "Why it did not, or could not, close automatically",
            "Options, each with pros and cons",
            "A recommendation",
            "<!-- specfuse:escalation id=bug-240 -->",
        ):
            self.assertIn(part, body)

    def test_files_no_new_issue(self):
        runner = _Runner()

        annotate_escalation(
            240, "bug-240", category="blocked-wu", repo="o/r",
            done_so_far="a", issue_summary="b", decision_needed="c",
            why_not_auto="d", options=_OPTIONS, recommendation="e",
            runner=runner,
        )

        self.assertEqual(runner.matching(["gh", "issue", "create"]), [])

    def test_labels_and_assigns_the_issue(self):
        runner = _Runner()

        annotate_escalation(
            240, "bug-240", category="blocked-wu", repo="o/r",
            done_so_far="a", issue_summary="b", decision_needed="c",
            why_not_auto="d", options=_OPTIONS, recommendation="e",
            assignee="operator", runner=runner,
        )

        edits = runner.matching(["gh", "issue", "edit", "240"])
        self.assertEqual(len(edits), 1)
        self.assertIn(NEEDS_HUMAN_LABEL, edits[0])
        self.assertIn("blocked-wu", edits[0])
        self.assertIn("--add-assignee", edits[0])
        self.assertIn("operator", edits[0])

    def test_empty_assignee_omits_the_flag(self):
        runner = _Runner()

        annotate_escalation(
            240, "bug-240", category="blocked-wu", repo="o/r",
            done_so_far="a", issue_summary="b", decision_needed="c",
            why_not_auto="d", options=_OPTIONS, recommendation="e",
            assignee="  ", runner=runner,
        )

        edits = runner.matching(["gh", "issue", "edit", "240"])
        self.assertNotIn("--add-assignee", edits[0])

    def test_second_call_posts_no_duplicate_comment_but_repairs_labels(self):
        runner = _Runner(comments=("<!-- specfuse:escalation id=bug-240 -->\nolder",))

        annotate_escalation(
            240, "bug-240", category="blocked-wu", repo="o/r",
            done_so_far="a", issue_summary="b", decision_needed="c",
            why_not_auto="d", options=_OPTIONS, recommendation="e",
            runner=runner,
        )

        self.assertEqual(runner.matching(["gh", "issue", "comment"]), [])
        # The label write is still re-asserted, so a first call whose label
        # failed is repaired rather than left half-applied.
        self.assertEqual(len(runner.matching(["gh", "issue", "edit", "240"])), 1)

    def test_a_failing_label_write_does_not_lose_the_comment(self):
        class Failing(_Runner):
            def __call__(self, argv, check: bool = False):
                if argv[:3] == ["gh", "issue", "edit"]:
                    self.calls.append(list(argv))
                    raise RuntimeError("label does not exist")
                return super().__call__(argv, check=check)

        runner = Failing()

        returned = annotate_escalation(
            240, "bug-240", category="blocked-wu", repo="o/r",
            done_so_far="a", issue_summary="b", decision_needed="c",
            why_not_auto="d", options=_OPTIONS, recommendation="e",
            runner=runner,
        )

        self.assertEqual(returned, 240)
        self.assertEqual(len(runner.matching(["gh", "issue", "comment", "240"])), 1)


class TestRecordEscalationRouting(unittest.TestCase):
    def _record(self, payload, runner):
        item = ActionItem(item_id="bug-240", kind=KIND_BUG)
        outcome = ActionOutcome(
            status=STATUS_ESCALATED, detail="judge_path_touched", escalation=payload
        )
        return _record_escalation(
            item, outcome, repo="o/r", runner=runner, policy_path=None
        )

    def test_payload_with_target_issue_annotates_and_says_so(self):
        runner = _Runner()

        reason = self._record(_payload(target_issue=240), runner)

        self.assertEqual(len(runner.matching(["gh", "issue", "comment", "240"])), 1)
        self.assertEqual(runner.matching(["gh", "issue", "create"]), [])
        self.assertIn("recorded on issue #240", reason)
        self.assertIn("judge_path_touched", reason)

    def test_payload_without_target_issue_still_files_a_tracking_issue(self):
        runner = _Runner()

        reason = self._record(_payload(), runner)

        self.assertEqual(len(runner.matching(["gh", "issue", "create"])), 1)
        self.assertIn("filed as issue", reason)

    def test_no_payload_says_nothing_was_recorded_rather_than_no_issue_filed(self):
        """The old wording claimed no issue was filed when one had been.

        `bugs.py` returned `escalation=None` for the two outcomes the lane
        filed for itself, and the loop printed "(summary only, no issue
        filed)" -- so four items of the first live run reported no trace
        while issues #1873, #1878, #1879 and #1880 existed. Nothing sets
        `escalation=None` for a filed escalation any more, and the wording no
        longer asserts anything about issues.
        """
        item = ActionItem(item_id="bug-240", kind=KIND_BUG)
        outcome = ActionOutcome(
            status=STATUS_ESCALATED, detail="something", escalation=None
        )

        reason = _record_escalation(
            item, outcome, repo="o/r", runner=_Runner(), policy_path=None
        )

        self.assertNotIn("no issue filed", reason)
        self.assertIn("not recorded on GitHub", reason)


if __name__ == "__main__":
    unittest.main()
