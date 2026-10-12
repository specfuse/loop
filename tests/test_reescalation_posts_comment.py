# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A re-armed issue that escalates again gets a new comment (#3446).

`annotate_escalation` deduplicated on the item id: any earlier
`<!-- specfuse:escalation id=bug-<n> -->` comment meant "already recorded",
so nothing was posted. On clabonte/generator (2026-10-08) the operator had
re-armed five issues whose Sep-17 escalations were a harness failure
(`Unknown command: /fix-bug`); `/fix-bug` really ran on all five and
escalated with new reasons and PR numbers, and every issue still showed only
the stale Sep-17 comment while the run log said "recorded on issue".

An escalation is an event, not an item. The bug lane never dispatches an
issue that carries `needs-human`, so a marker on an issue *without* that label
means the operator re-armed it and this is a new escalation: post it. A marker
on an issue that still carries `needs-human` is the same standing escalation
-- a retry -- and stays deduplicated.
"""

from __future__ import annotations

import json
import sys
import unittest
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop.escalation import NEEDS_HUMAN_LABEL, annotate_escalation

_OPTIONS = [("Do it", "pros", "cons"), ("Do not", "pros", "cons")]
_STALE = (
    "<!-- specfuse:escalation id=bug-1867 -->\n"
    "could_not_proceed: Unknown command: /fix-bug"
)


class _Runner:
    def __init__(self, *, labels=(), comments=(_STALE,)):
        self.calls: list[list] = []
        self._labels = labels
        self._comments = comments

    def __call__(self, argv, check: bool = False):
        self.calls.append(list(argv))
        if argv[:3] == ["gh", "issue", "view"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({
                    "body": "",
                    "comments": [{"body": c} for c in self._comments],
                    "labels": [{"name": n} for n in self._labels],
                }),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def comments_posted(self):
        return [
            c[c.index("--body") + 1]
            for c in self.calls if c[:3] == ["gh", "issue", "comment"]
        ]


def _escalate(runner):
    return annotate_escalation(
        1867, "bug-1867", category="blocked-wu", repo="o/r",
        done_so_far="ran /fix-bug", issue_summary="feature-scoped",
        decision_needed="promote?", why_not_auto="refused: 4 files",
        options=_OPTIONS, recommendation="promote", runner=runner,
    )


class TestReEscalationAfterReArm(unittest.TestCase):
    def test_re_armed_issue_gets_the_new_escalation(self):
        # Marker from an earlier run, `needs-human` removed by the operator.
        runner = _Runner(labels=("triage:bug",))

        _escalate(runner)

        posted = runner.comments_posted()
        self.assertEqual(len(posted), 1)
        self.assertIn("refused: 4 files", posted[0])

    def test_standing_escalation_is_not_posted_twice(self):
        runner = _Runner(labels=(NEEDS_HUMAN_LABEL, "triage:bug"))

        _escalate(runner)

        self.assertEqual(runner.comments_posted(), [])

    def test_first_escalation_is_posted(self):
        runner = _Runner(comments=())

        _escalate(runner)

        self.assertEqual(len(runner.comments_posted()), 1)


if __name__ == "__main__":
    unittest.main()
