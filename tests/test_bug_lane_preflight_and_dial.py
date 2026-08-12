# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Two corrections to what the bug lane reports and when it pays for CI.

1. `automerge: off` is not a guardrail decline. Every guardrail passing while
   the dial is off produced `declined ... reason=eligible` -- reported live on
   issue #296 as "declined by the merge guardrails -- `eligible`".

2. The guardrails decidable from the PR's shape are evaluated BEFORE the
   up-to-ten-minute CI wait. A PR touching a judge path cannot merge whatever
   CI says, so waiting for CI first buys nothing; two of eight items in the
   first unattended run paid that wait to be declined `judge_path_touched`.
"""

from __future__ import annotations

import json
import sys
import unittest
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop.bug_lane import (
    REASON_DIFF_TOO_LARGE,
    REASON_ELIGIBLE,
    REASON_JUDGE_PATH_TOUCHED,
    REASON_NO_TEST_EVIDENCE,
    evaluate_pr_shape_guardrails,
    judge_paths_touched,
)
from specfuse.loop.bug_lane_run import (
    OUTCOME_AUTOMERGE_OFF,
    OUTCOME_DECLINED,
    run_bug_lane,
)

_REPO = "acme-widget/example"
_ISSUE = 240
_PROVENANCE = {"kind": "triaged_issue", "ref": "240"}


class _LaneRunner:
    """Enough `gh` to drive `run_bug_lane`, counting `gh pr checks` reads."""

    def __init__(self, files):
        self.calls: list[list] = []
        self._files = files

    def __call__(self, argv, check: bool = False):
        self.calls.append(list(argv))
        if argv[:2] == ["claude", "-p"]:
            return SimpleNamespace(returncode=0, stdout="completed", stderr="")
        if argv[:3] == ["gh", "pr", "list"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps([{"number": 900, "body": f"closes #{_ISSUE}"}]),
                stderr="",
            )
        if argv[:3] == ["gh", "pr", "view"]:
            return SimpleNamespace(
                returncode=0, stdout=json.dumps({"files": self._files}), stderr=""
            )
        if argv[:3] == ["gh", "pr", "checks"]:
            return SimpleNamespace(
                returncode=0, stdout=json.dumps([{"bucket": "pass"}]), stderr=""
            )
        if argv[:3] == ["gh", "issue", "view"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {"body": "<!-- specfuse:triage category=bug confidence=high -->"}
                ),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    def matching(self, prefix):
        return [c for c in self.calls if c[: len(prefix)] == prefix]


def _files(*paths, additions=2):
    return [{"path": p, "additions": additions, "deletions": 0} for p in paths]


class TestShapeGuardrailsRunBeforeCI(unittest.TestCase):
    def test_judge_path_declines_without_reading_ci_at_all(self):
        runner = _LaneRunner(_files("specfuse/loop/loop.py", "tests/test_loop.py"))

        result = run_bug_lane(runner, _REPO, _ISSUE, ci_deadline_seconds=0)

        self.assertEqual(result.outcome, OUTCOME_DECLINED)
        self.assertEqual(result.reason, REASON_JUDGE_PATH_TOUCHED)
        self.assertEqual(runner.matching(["gh", "pr", "checks"]), [])

    def test_a_clean_pr_still_reads_ci(self):
        runner = _LaneRunner(_files("specfuse/monitor/thing.py", "tests/test_thing.py"))

        run_bug_lane(runner, _REPO, _ISSUE, ci_deadline_seconds=0)

        self.assertEqual(len(runner.matching(["gh", "pr", "checks"])), 1)

    def test_declining_reason_still_reaches_the_pr_as_a_label(self):
        runner = _LaneRunner(_files("specfuse/loop/loop.py", "tests/test_loop.py"))

        run_bug_lane(runner, _REPO, _ISSUE, ci_deadline_seconds=0)

        edits = runner.matching(["gh", "pr", "edit"])
        self.assertEqual(len(edits), 1)
        self.assertIn("bug-lane:judge-path-touched", edits[0])


class TestDeclineCarriesItsMeasurement(unittest.TestCase):
    def test_judge_path_evidence_names_the_path(self):
        runner = _LaneRunner(_files("specfuse/loop/loop.py", "tests/test_loop.py"))

        result = run_bug_lane(runner, _REPO, _ISSUE, ci_deadline_seconds=0)

        self.assertTrue(result.evidence)
        self.assertIn("specfuse/loop/loop.py", " ".join(result.evidence))

    def test_diff_too_large_evidence_names_both_numbers(self):
        runner = _LaneRunner(
            _files("specfuse/monitor/a.py", "tests/test_a.py", additions=500)
        )

        result = run_bug_lane(runner, _REPO, _ISSUE, ci_deadline_seconds=0)

        self.assertEqual(result.reason, REASON_DIFF_TOO_LARGE)
        joined = " ".join(result.evidence)
        self.assertIn("1000", joined)  # two files x 500 additions
        self.assertIn("150", joined)  # the default cap


class TestAutomergeOffIsNotADecline(unittest.TestCase):
    def test_eligible_with_dial_off_reports_automerge_off(self):
        runner = _LaneRunner(_files("specfuse/monitor/a.py", "tests/test_a.py"))

        result = run_bug_lane(runner, _REPO, _ISSUE, ci_deadline_seconds=0)

        self.assertEqual(result.outcome, OUTCOME_AUTOMERGE_OFF)
        self.assertEqual(result.reason, REASON_ELIGIBLE)
        self.assertEqual(runner.matching(["gh", "pr", "merge"]), [])

    def test_automerge_off_writes_no_decline_label(self):
        runner = _LaneRunner(_files("specfuse/monitor/a.py", "tests/test_a.py"))

        run_bug_lane(runner, _REPO, _ISSUE, ci_deadline_seconds=0)

        self.assertEqual(runner.matching(["gh", "pr", "edit"]), [])


class TestShapePredicateInIsolation(unittest.TestCase):
    def _shape(self, changed, diff_lines=10, max_diff_lines=150):
        return evaluate_pr_shape_guardrails(
            changed_files=changed,
            diff_lines=diff_lines,
            max_diff_lines=max_diff_lines,
            provenance=_PROVENANCE,
        )

    def test_clean_pr_passes(self):
        decision = self._shape(["specfuse/monitor/a.py", "tests/test_a.py"])
        self.assertTrue(decision.eligible)

    def test_missing_test_evidence_declines(self):
        decision = self._shape(["specfuse/monitor/a.py"])
        self.assertEqual(decision.reason, REASON_NO_TEST_EVIDENCE)

    def test_oversize_diff_declines(self):
        decision = self._shape(["tests/test_a.py"], diff_lines=999)
        self.assertEqual(decision.reason, REASON_DIFF_TOO_LARGE)

    def test_judge_path_declines(self):
        decision = self._shape(["pyproject.toml", "tests/test_a.py"])
        self.assertEqual(decision.reason, REASON_JUDGE_PATH_TOUCHED)


class TestJudgePathsTouched(unittest.TestCase):
    def test_names_every_matching_path_once(self):
        hits = judge_paths_touched(
            ["specfuse/loop/a.py", "specfuse/loop/b.py", "tests/test_a.py"]
        )
        self.assertEqual(hits, ["specfuse/loop/a.py", "specfuse/loop/b.py"])

    def test_exact_file_entries_match_only_exactly(self):
        self.assertEqual(judge_paths_touched(["pyproject.toml"]), ["pyproject.toml"])
        self.assertEqual(judge_paths_touched(["sub/pyproject.toml"]), [])

    def test_no_judge_path_returns_empty(self):
        self.assertEqual(judge_paths_touched(["tests/test_a.py"]), [])


if __name__ == "__main__":
    unittest.main()
