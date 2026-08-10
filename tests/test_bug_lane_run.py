# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for `specfuse.loop.bug_lane_run` (FEAT-2026-0048/T04)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from specfuse.loop.bug_lane import (
    DECLINE_LABELS,
    REASON_CI_NOT_GREEN,
    REASON_DAILY_CAP_REACHED,
    REASON_DIFF_TOO_LARGE,
    REASON_ELIGIBLE,
    REASON_JUDGE_PATH_TOUCHED,
    REASON_NO_TEST_EVIDENCE,
    REASON_UNTRACEABLE,
)
from specfuse.loop.bug_lane_run import (
    CORRELATION_ID,
    OUTCOME_COULD_NOT_PROCEED,
    OUTCOME_DECLINED,
    OUTCOME_MERGED,
    OUTCOME_REFUSED,
    pr_ci_conclusion,
    run_bug_lane,
)

_REPO = "acme-widget/example"
_ISSUE_NUMBER = 7
_PR_NUMBER = 21
_SOURCE_PATH = Path(__file__).resolve().parent.parent / "specfuse" / "loop" / "bug_lane_run.py"
_SOURCE_TEXT = _SOURCE_PATH.read_text(encoding="utf-8")

def _policy_yaml(automerge: str) -> str:
    return f"""
version: 1
queue: []
rules:
  bugs:
    preempt: false
    min_severity: low
    automerge: "{automerge}"
  features:
    gate_review: human
    wip_limit: 1
  triage:
    auto: false
budgets:
  max_tokens_per_run: 1
  max_open_prs: 1
  max_items_per_day: 1
escalation:
  webhook_env: x
  assignee: x
  quiet_hours: x
  sla_hours: 1
"""


_AGENT_POLICY_ON = _policy_yaml("on")
_AGENT_POLICY_OFF = _policy_yaml("off")


class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _StubRunner:
    """Fake `gh`/`claude` runner. Tracks every call so tests can assert
    which commands reached it and in what order."""

    def __init__(
        self,
        *,
        fix_bug_stdout="completed",
        pr_body=None,
        pr_files=None,
        issue_body=None,
        checks=None,
        checks_returncode=0,
        merged_prs=None,
        existing_escalation_issue=None,
        override=None,
    ):
        self.calls: list[list[str]] = []
        self._override = override
        self._fix_bug_stdout = fix_bug_stdout
        self._pr_body = pr_body if pr_body is not None else f"Fixes it.\n\ncloses #{_ISSUE_NUMBER}\n"
        self._pr_files = pr_files if pr_files is not None else [
            {"path": "tests/test_thing.py", "additions": 10, "deletions": 0},
            {"path": "specfuse/monitor/thing.py", "additions": 5, "deletions": 2},
        ]
        self._issue_body = (
            issue_body if issue_body is not None
            else "<!-- specfuse:triage category=bug confidence=high -->\nRepro steps."
        )
        self._checks = checks if checks is not None else [{"conclusion": "success"}]
        self._checks_returncode = checks_returncode
        self._merged_prs = merged_prs if merged_prs is not None else []
        self._existing_escalation_issue = existing_escalation_issue

    def __call__(self, args, check=True):
        self.calls.append(list(args))

        if self._override is not None:
            overridden = self._override(args)
            if overridden is not None:
                return overridden

        if args[:3] == ["gh", "issue", "view"]:
            return _Result(stdout=json.dumps({"body": self._issue_body}))
        if args[:3] == ["gh", "issue", "list"]:
            # escalation.py's find-existing-issue probe
            if self._existing_escalation_issue is not None:
                return _Result(stdout=json.dumps(
                    [{"number": self._existing_escalation_issue, "body": f"<!-- specfuse:escalation id={CORRELATION_ID} -->"}]
                ))
            return _Result(stdout="[]")
        if args[:3] == ["gh", "issue", "create"]:
            return _Result(stdout="https://example.invalid/issues/999")
        if args[:3] == ["gh", "pr", "list"]:
            return _Result(stdout=json.dumps([{"number": _PR_NUMBER, "body": self._pr_body}]))
        if args[:3] == ["gh", "pr", "view"]:
            return _Result(stdout=json.dumps({"files": self._pr_files}))
        if args[:3] == ["gh", "pr", "checks"]:
            return _Result(returncode=self._checks_returncode, stdout=json.dumps(self._checks))
        if args[:3] == ["gh", "pr", "merge"]:
            return _Result(stdout="")
        if args[:3] == ["gh", "pr", "edit"]:
            return _Result(stdout="")
        if args[:2] == ["claude", "-p"]:
            return _Result(stdout=self._fix_bug_stdout)
        raise AssertionError(f"unexpected call: {args}")

    def calls_matching(self, prefix):
        return [c for c in self.calls if c[: len(prefix)] == prefix]


class TestRunBugLane(unittest.TestCase):
    # -- Criterion 3: dial off never merges ---------------------------------

    def test_dial_off_never_merges(self):
        runner = _StubRunner()
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_OFF))

        self.assertEqual(result.outcome, OUTCOME_DECLINED)
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])

    def test_dial_off_all_guardrails_satisfied_still_no_merge(self):
        runner = _StubRunner()
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_OFF))

        self.assertEqual(result.reason, REASON_ELIGIBLE)
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])

    # -- Criterion 4: guardrails cannot be bypassed by the dial --------------

    def test_dial_on_no_test_evidence_never_merges(self):
        runner = _StubRunner(pr_files=[{"path": "specfuse/loop/thing.py", "additions": 5, "deletions": 0}])
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        self.assertEqual(result.reason, REASON_NO_TEST_EVIDENCE)
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])

    def test_dial_on_ci_not_green_never_merges(self):
        runner = _StubRunner(checks=[{"conclusion": "failure"}])
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        self.assertEqual(result.reason, REASON_CI_NOT_GREEN)
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])

    def test_dial_on_diff_too_large_never_merges(self):
        big_files = [{"path": "tests/test_thing.py", "additions": 1000, "deletions": 0}]
        runner = _StubRunner(pr_files=big_files)
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        self.assertEqual(result.reason, REASON_DIFF_TOO_LARGE)
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])

    def test_dial_on_judge_path_touched_never_merges(self):
        runner = _StubRunner(pr_files=[
            {"path": "tests/test_thing.py", "additions": 10, "deletions": 0},
            {"path": ".specfuse/verification.yml", "additions": 1, "deletions": 0},
        ])
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        self.assertEqual(result.reason, REASON_JUDGE_PATH_TOUCHED)
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])

    def test_dial_on_untraceable_provenance_never_merges(self):
        # PR is found (its body still cites the issue) but the issue itself
        # carries no `bug`-category triage marker -- untraceable.
        runner = _StubRunner(issue_body="No triage marker on this issue.")
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        self.assertEqual(result.reason, REASON_UNTRACEABLE)
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])

    def test_pr_ci_conclusion_mixed_conclusions_is_non_success(self):
        runner = _StubRunner(checks=[{"conclusion": "success"}, {"conclusion": "failure"}])
        conclusion = pr_ci_conclusion(runner, _REPO, _PR_NUMBER)
        self.assertNotEqual(conclusion, "success")

    def test_pr_ci_conclusion_row_missing_conclusion_key(self):
        runner = _StubRunner(checks=[{"name": "build"}])
        conclusion = pr_ci_conclusion(runner, _REPO, _PR_NUMBER)
        self.assertNotEqual(conclusion, "success")

    def test_pr_ci_conclusion_empty_rows(self):
        runner = _StubRunner(checks=[])
        conclusion = pr_ci_conclusion(runner, _REPO, _PR_NUMBER)
        self.assertNotEqual(conclusion, "success")

    def test_find_pr_for_issue_command_failure_declines(self):
        def override(args):
            if args[:3] == ["gh", "pr", "list"]:
                return _Result(returncode=1, stdout="")
            return None

        runner = _StubRunner(override=override)
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))
        self.assertEqual(result.outcome, OUTCOME_DECLINED)
        self.assertIsNone(result.pr_number)

    def test_find_pr_for_issue_malformed_json_declines(self):
        def override(args):
            if args[:3] == ["gh", "pr", "list"]:
                return _Result(stdout="not json")
            return None

        runner = _StubRunner(override=override)
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))
        self.assertEqual(result.outcome, OUTCOME_DECLINED)
        self.assertIsNone(result.pr_number)

    def test_pr_view_malformed_json_treated_as_no_changes(self):
        def override(args):
            if args[:3] == ["gh", "pr", "view"]:
                return _Result(stdout="not json")
            return None

        runner = _StubRunner(override=override)
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))
        # No changed files at all -> fails the test-evidence guardrail.
        self.assertEqual(result.reason, REASON_NO_TEST_EVIDENCE)

    def test_issue_view_command_failure_is_untraceable(self):
        def override(args):
            if args[:3] == ["gh", "issue", "view"]:
                return _Result(returncode=1, stdout="")
            return None

        runner = _StubRunner(override=override)
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))
        self.assertEqual(result.reason, REASON_UNTRACEABLE)

    def test_dial_on_daily_cap_reached_never_merges(self):
        from specfuse.loop.bug_lane_state import render_merge_marker

        merged = [
            {"number": n, "body": render_merge_marker(1_700_000_000.0)}
            for n in range(3)
        ]

        # DEFAULT_MAX_MERGES_PER_DAY is 3; wire the pr-list stub to also
        # answer the merge-cap reader's `gh pr list --state merged` query.
        def override(args):
            if args[:3] == ["gh", "pr", "list"] and "merged" in args:
                return _Result(stdout=json.dumps(merged))
            return None

        runner = _StubRunner(override=override)
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON), now=1_700_000_010.0)

        self.assertEqual(result.reason, REASON_DAILY_CAP_REACHED)
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])

    # -- Criterion 5: exactly one merge call site -----------------------------

    def test_exactly_one_merge_call_site_gated_by_dial_and_eligible(self):
        merge_lines = [
            line for line in _SOURCE_TEXT.splitlines()
            if '"pr", "merge"' in line or "'pr', 'merge'" in line
        ]
        self.assertEqual(len(merge_lines), 1)

        gate_pattern = re.compile(r"^\s*if dial and decision\.eligible:\s*$", re.MULTILINE)
        self.assertEqual(len(gate_pattern.findall(_SOURCE_TEXT)), 1)

    # -- Criterion 6: pr_ci_conclusion never raises, non-success on bad input -

    def test_pr_ci_conclusion_missing(self):
        runner = _StubRunner(checks=[], checks_returncode=1)
        conclusion = pr_ci_conclusion(runner, _REPO, _PR_NUMBER)
        self.assertNotEqual(conclusion, "success")

    def test_pr_ci_conclusion_malformed(self):
        class _MalformedRunner(_StubRunner):
            def __call__(self, args, check=True):
                if args[:3] == ["gh", "pr", "checks"]:
                    return _Result(stdout="not json")
                return super().__call__(args, check=check)

        conclusion = pr_ci_conclusion(_MalformedRunner(), _REPO, _PR_NUMBER)
        self.assertNotEqual(conclusion, "success")

    def test_pr_ci_conclusion_command_fails(self):
        class _RaisingRunner:
            def __call__(self, args, check=True):
                raise RuntimeError("network unreachable")

        conclusion = pr_ci_conclusion(_RaisingRunner(), _REPO, _PR_NUMBER)
        self.assertNotEqual(conclusion, "success")

    def test_pr_ci_conclusion_success(self):
        runner = _StubRunner(checks=[{"conclusion": "success"}, {"conclusion": "success"}])
        self.assertEqual(pr_ci_conclusion(runner, _REPO, _PR_NUMBER), "success")

    # -- Criterion 7: declining path labels + leaves PR open -----------------

    def test_declining_path_labels_reason_and_never_closes_or_reinvokes(self):
        runner = _StubRunner(checks=[{"conclusion": "failure"}])
        run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        label_calls = runner.calls_matching(["gh", "pr", "edit"])
        self.assertEqual(len(label_calls), 1)
        # The PUBLIC label name, not the raw reason constant (#1420). Asserting
        # the constant here is what let the defect ship: the lane labelled with
        # a name provision_labels never creates, so this call failed against a
        # real repository while the stubbed test stayed green.
        self.assertIn(DECLINE_LABELS[REASON_CI_NOT_GREEN], label_calls[0])
        self.assertNotIn(REASON_CI_NOT_GREEN, label_calls[0])

        close_calls = [c for c in runner.calls if "close" in c]
        self.assertEqual(close_calls, [])

        fix_bug_calls = runner.calls_matching(["claude", "-p"])
        self.assertEqual(len(fix_bug_calls), 1)

    # -- Criterion 8/9: refused / could_not_proceed escalate at both dials ---

    def test_refused_escalates_at_dial_on(self):
        runner = _StubRunner(fix_bug_stdout="refused")
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        self.assertEqual(result.outcome, OUTCOME_REFUSED)
        create_calls = runner.calls_matching(["gh", "issue", "create"])
        self.assertEqual(len(create_calls), 1)
        self.assertIn(CORRELATION_ID, " ".join(create_calls[0]))

    def test_refused_escalates_at_dial_off(self):
        runner = _StubRunner(fix_bug_stdout="refused")
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_OFF))

        self.assertEqual(result.outcome, OUTCOME_REFUSED)
        create_calls = runner.calls_matching(["gh", "issue", "create"])
        self.assertEqual(len(create_calls), 1)

    def test_could_not_proceed_escalates_at_both_dials(self):
        for policy in (_AGENT_POLICY_ON, _AGENT_POLICY_OFF):
            runner = _StubRunner(fix_bug_stdout="could_not_proceed")
            result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(policy))

            self.assertEqual(result.outcome, OUTCOME_COULD_NOT_PROCEED)
            self.assertEqual(len(runner.calls_matching(["gh", "issue", "create"])), 1)

    def test_escalation_idempotent_across_repeated_runs(self):
        runner = _StubRunner(fix_bug_stdout="refused", existing_escalation_issue=123)
        run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        create_calls = runner.calls_matching(["gh", "issue", "create"])
        self.assertEqual(create_calls, [])

    def test_refused_never_merges_or_finds_pr(self):
        runner = _StubRunner(fix_bug_stdout="refused")
        run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        self.assertEqual(runner.calls_matching(["gh", "pr", "list"]), [])
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])

    # -- Criterion 10: record_merge called exactly once, only on merge -------

    def test_successful_merge_records_exactly_once(self):
        runner = _StubRunner()
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON), now=1.0)

        self.assertEqual(result.outcome, OUTCOME_MERGED)
        merge_calls = runner.calls_matching(["gh", "pr", "merge"])
        self.assertEqual(len(merge_calls), 1)
        view_calls_for_record = [
            c for c in runner.calls_matching(["gh", "pr", "view"])
        ]
        # record_merge does its own `gh pr view` + `gh pr edit` to write the
        # marker -- assert exactly one `gh pr edit` happened after the merge
        # (the marker write), and it is not a label-add call.
        edit_calls = runner.calls_matching(["gh", "pr", "edit"])
        self.assertEqual(len(edit_calls), 1)
        self.assertIn("--body", edit_calls[0])
        self.assertNotIn("--add-label", edit_calls[0])
        self.assertTrue(view_calls_for_record)

    def test_record_merge_not_called_on_declining_path(self):
        runner = _StubRunner(checks=[{"conclusion": "failure"}])
        run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        edit_calls = runner.calls_matching(["gh", "pr", "edit"])
        for call in edit_calls:
            self.assertNotIn("--body", call)

    def test_record_merge_not_called_when_dial_off(self):
        runner = _StubRunner()
        run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_OFF))

        edit_calls = runner.calls_matching(["gh", "pr", "edit"])
        for call in edit_calls:
            self.assertNotIn("--body", call)

    # -- Criterion 11: full happy path + declining paths through fake runner -

    def test_happy_path_merges_with_injected_runner_no_network(self):
        runner = _StubRunner()
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON), now=5.0)

        self.assertEqual(result.outcome, OUTCOME_MERGED)
        self.assertEqual(result.pr_number, _PR_NUMBER)
        self.assertTrue(runner.calls_matching(["claude", "-p"]))
        self.assertTrue(runner.calls_matching(["gh", "pr", "merge"]))

    def test_no_pr_found_declines_without_error(self):
        def override(args):
            if args[:3] == ["gh", "pr", "list"]:
                return _Result(stdout="[]")
            return None

        runner = _StubRunner(override=override)
        result = run_bug_lane(runner, _REPO, _ISSUE_NUMBER, policy_path=_dump(_AGENT_POLICY_ON))

        self.assertEqual(result.outcome, OUTCOME_DECLINED)
        self.assertIsNone(result.pr_number)
        self.assertEqual(runner.calls_matching(["gh", "pr", "merge"]), [])


def _dump(policy_yaml: str) -> str:
    """Write *policy_yaml* to a scratch file and return its path."""
    import tempfile

    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    handle.write(policy_yaml)
    handle.close()
    return handle.name


if __name__ == "__main__":
    unittest.main()
