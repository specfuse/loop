# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A closed issue does not keep the lane's escalation labels (#3523).

The bug lane escalated clabonte/generator#2856 with `refused` and labelled it
`needs-human` + `blocked-wu`. A hand-written PR then fixed and closed it, and
the closed issue kept both labels until someone removed them by hand -- so it
looked parked to anyone filtering by label, and had it been reopened the bug
lane would have skipped it (`needs-human` is human-owned there).

Each run now clears those labels from closed issues that carry the lane's own
escalation marker. A label the lane did not write (`status:open`) and an issue
with no lane marker (labelled by hand) are left alone.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.run import run_agent
from specfuse.loop.escalation import clear_closed_escalation_labels

_MARKER = "<!-- specfuse:escalation id=bug-2856 -->"


def _closed_issue(number, *, labels, body="", comments=()):
    return {
        "number": number,
        "body": body,
        "labels": [{"name": name} for name in labels],
        "comments": [{"body": text} for text in comments],
    }


class _Runner:
    def __init__(self, closed, *, fail_closed_list=False):
        self.closed = closed
        self.fail_closed_list = fail_closed_list
        self.calls = []

    def __call__(self, argv, check=False):
        argv = list(argv)
        self.calls.append(argv)
        if argv[:3] == ["gh", "issue", "list"] and "closed" in argv:
            if self.fail_closed_list:
                return SimpleNamespace(returncode=1, stdout="", stderr="rate limited")
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.closed), stderr="")
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    def removed(self, number):
        removed = []
        for call in self.calls:
            if call[:4] == ["gh", "issue", "edit", str(number)]:
                removed += [call[i + 1] for i, a in enumerate(call) if a == "--remove-label"]
        return removed


class ClearClosedEscalationLabels(unittest.TestCase):
    def test_lane_labels_are_removed_from_a_closed_escalated_issue(self):
        runner = _Runner([_closed_issue(
            2856, labels=("needs-human", "blocked-wu", "status:open", "bug"),
            comments=("unrelated", f"{_MARKER}\n\n## What has been done so far"),
        )])

        cleared = clear_closed_escalation_labels(runner, "o/r")

        self.assertEqual(cleared, [2856])
        self.assertEqual(sorted(runner.removed(2856)), ["blocked-wu", "needs-human"])

    def test_marker_in_the_body_counts_too(self):
        runner = _Runner([_closed_issue(
            9, labels=("needs-human", "gate-review"), body=f"{_MARKER}\n\nbody")])

        self.assertEqual(clear_closed_escalation_labels(runner, "o/r"), [9])
        self.assertEqual(sorted(runner.removed(9)), ["gate-review", "needs-human"])

    def test_issue_labelled_by_hand_is_left_alone(self):
        runner = _Runner([_closed_issue(
            12, labels=("needs-human", "blocked-wu"), comments=("please look",))])

        self.assertEqual(clear_closed_escalation_labels(runner, "o/r"), [])
        self.assertEqual(runner.removed(12), [])

    def test_unreadable_listing_clears_nothing_and_does_not_raise(self):
        runner = _Runner([], fail_closed_list=True)

        self.assertEqual(clear_closed_escalation_labels(runner, "o/r"), [])

    def test_runner_that_raises_clears_nothing(self):
        def runner(argv, check=False):
            raise OSError("gh not installed")

        self.assertEqual(clear_closed_escalation_labels(runner, "o/r"), [])

    def test_malformed_listing_clears_nothing(self):
        for stdout in ("not json", json.dumps({"number": 1}), json.dumps([{"body": _MARKER}])):
            def answer(argv, check=False, stdout=stdout):
                return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

            self.assertEqual(clear_closed_escalation_labels(answer, "o/r"), [], stdout)

    def test_failed_edit_is_not_reported_as_cleared(self):
        listing = json.dumps([_closed_issue(3, labels=("needs-human",), body=_MARKER)])

        def runner(argv, check=False):
            if argv[:3] == ["gh", "issue", "edit"]:
                return SimpleNamespace(returncode=1, stdout="", stderr="forbidden")
            return SimpleNamespace(returncode=0, stdout=listing, stderr="")

        self.assertEqual(clear_closed_escalation_labels(runner, "o/r"), [])


class RunClearsClosedEscalationLabels(unittest.TestCase):
    def test_a_run_clears_them_and_says_so(self):
        runner = _Runner([_closed_issue(
            2856, labels=("needs-human", "blocked-wu"), comments=(_MARKER,))])
        reports = []
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            (specfuse_dir / "features").mkdir()
            run_agent(
                specfuse_dir=specfuse_dir,
                repo="o/r",
                runner=runner,
                providers=(),
                policy_path=str(specfuse_dir / "agent-policy.yml"),
                features_root=specfuse_dir / "features",
                clock=lambda: 0.0,
                reporter=reports.append,
            )

        self.assertEqual(sorted(runner.removed(2856)), ["blocked-wu", "needs-human"])
        self.assertTrue(any("#2856" in line for line in reports), reports)


if __name__ == "__main__":
    unittest.main()
