# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`provision_labels` works with the runner its callers actually inject (#2081).

`labels._default_runner(args, cwd=None, check=True)` is the **only** runner in
this codebase that takes `cwd`. Every other one -- `agent.run`, `escalation`,
`gh_backend` -- is `(argv, check)`. So `provision_labels` passing `cwd=` meant
any injected runner raised `TypeError` on its very first `gh` call, which the
function then caught into `ProvisionReport.reason` and reported as `skipped`.

`bug_lane_run.add_guardrail_label` has injected the lane's runner since #1785
added on-demand provisioning, so that path **never once created a label**: the
seven `bug-lane:*` entries were registered by FEAT-2026-0048 and no repository
had any of them, while every label `scaffold.py` provisions -- it passes no
runner, so it gets the compatible default -- existed.

The failure was invisible three times over: swallowed into a report nobody
read, flattened to a bare `False` by `add_guardrail_label`, and returned as
`BugLaneResult.label_written=False` that no consumer surfaced.
"""

from __future__ import annotations

import sys
import unittest

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.bugs import _declined_payload
from specfuse.loop.labels import LABEL_REGISTRY, provision_labels


class _LaneRunner:
    """The `(argv, check)` contract every non-labels module implements.

    Deliberately does NOT accept `cwd` — that is the bug being pinned.
    """

    def __init__(self, existing=()):
        self.calls: list[list] = []
        self._existing = existing

    def __call__(self, argv, check: bool = False):
        self.calls.append(list(argv))

        class _Result:
            returncode = 0
            stdout = (
                "[" + ",".join(f'{{"name":"{n}"}}' for n in self._existing) + "]"
                if "list" in argv
                else ""
            )
            stderr = ""

        _Result.stdout = _Result.stdout if "list" in argv else ""
        return _Result()


class TestProvisioningWithAnInjectedRunner(unittest.TestCase):
    def test_it_does_not_skip(self):
        report = provision_labels(".", runner=_LaneRunner(), repo="o/r")

        self.assertFalse(report.skipped, report.reason)
        self.assertFalse(report.reason, report.reason)

    def test_it_creates_the_missing_labels(self):
        report = provision_labels(".", runner=_LaneRunner(), repo="o/r")

        self.assertEqual(len(report.created), len(LABEL_REGISTRY))

    def test_cwd_is_never_passed_when_a_repo_is_given(self):
        """The whole defect in one assertion."""
        runner = _LaneRunner()

        provision_labels(".", runner=runner, repo="o/r")

        for call in runner.calls:
            with self.subTest(call=call):
                self.assertIn("--repo", call)
                self.assertIn("o/r", call)

    def test_the_bug_lane_labels_are_in_the_registry_at_all(self):
        """They always were — provisioning could just never reach them."""
        names = {spec.name for spec in LABEL_REGISTRY}
        for reason in ("diff-too-large", "judge-path-touched", "ci-not-green"):
            self.assertIn(f"bug-lane:{reason}", names)

    def test_an_already_present_label_is_not_recreated(self):
        runner = _LaneRunner(existing=[spec.name for spec in LABEL_REGISTRY])

        report = provision_labels(".", runner=runner, repo="o/r")

        self.assertEqual(report.created, [])
        self.assertEqual(len(report.already_present), len(LABEL_REGISTRY))

    def test_the_cwd_path_still_works_for_callers_that_use_it(self):
        """`scaffold.py` passes no repo and relies on cwd. Do not break it."""
        seen = {}

        def cwd_runner(argv, cwd=None, check=False):
            seen["cwd"] = cwd

            class _R:
                returncode = 0
                stdout = "[]"
                stderr = ""

            return _R()

        report = provision_labels("/some/target", runner=cwd_runner)

        self.assertFalse(report.skipped, report.reason)
        self.assertEqual(seen["cwd"], "/some/target")


class TestAFailedLabelIsReportedNotSwallowed(unittest.TestCase):
    def test_the_escalation_says_the_label_did_not_land(self):
        payload = _declined_payload(1844, 2080, "diff_too_large", (), label_written=False)

        self.assertIn("could NOT be written", payload.issue_summary)
        self.assertIn("gh pr list --label", payload.issue_summary)

    def test_a_successful_label_adds_no_noise(self):
        payload = _declined_payload(1844, 2080, "diff_too_large", (), label_written=True)

        self.assertNotIn("could NOT", payload.issue_summary)

    def test_the_verdict_is_still_the_record(self):
        """#1785's rule: losing the projection must not lose the item."""
        payload = _declined_payload(1844, 2080, "diff_too_large", (), label_written=False)

        self.assertIn("diff_too_large", payload.issue_summary)
        self.assertEqual(payload.target_issue, 1844)


if __name__ == "__main__":
    unittest.main()
