# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for `run_bug_lane` carrying `pr_number` from `/fix-bug`'s own RESULT
block instead of re-discovering it from a list (FEAT-2026-0108/T05, #3180)."""

from __future__ import annotations

import json
import unittest

from specfuse.loop.bug_lane_run import (
    OUTCOME_DECLINED,
    REASON_PR_NOT_FOUND,
    extract_pr_number,
    run_bug_lane,
)

_REPO = "acme-widget/example"
_ISSUE_NUMBER = 7
_PR_NUMBER = 42


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


def _dump(policy_yaml: str) -> str:
    import tempfile

    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    handle.write(policy_yaml)
    handle.close()
    return handle.name


class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _StubRunner:
    """Fake `gh`/`claude` runner tracking every call, with a scripted
    sequence of `gh pr list` responses so tests can assert retry counts."""

    def __init__(self, *, fix_bug_stdout, pr_list_bodies=()):
        self.calls: list[list[str]] = []
        self._fix_bug_stdout = fix_bug_stdout
        # Each entry is the `body` field of the single row `gh pr list`
        # returns on that call, or `None` for an empty list (not found yet).
        self._pr_list_bodies = list(pr_list_bodies)
        self._pr_files = [
            {"path": "tests/test_thing.py", "additions": 10, "deletions": 0},
        ]
        self._issue_body = (
            "<!-- specfuse:triage category=bug confidence=high -->\nRepro steps."
        )

    def __call__(self, args, check=True):
        self.calls.append(list(args))

        if args[:3] == ["gh", "issue", "view"]:
            return _Result(stdout=json.dumps({"body": self._issue_body}))
        if args[:3] == ["gh", "pr", "list"]:
            body = self._pr_list_bodies.pop(0) if self._pr_list_bodies else None
            if body is None:
                return _Result(stdout="[]")
            return _Result(stdout=json.dumps([{"number": _PR_NUMBER, "body": body}]))
        if args[:3] == ["gh", "pr", "view"]:
            return _Result(stdout=json.dumps({"files": self._pr_files}))
        if args[:3] == ["gh", "pr", "checks"]:
            return _Result(stdout=json.dumps([{"bucket": "pass"}]))
        if args[:3] == ["gh", "pr", "merge"]:
            return _Result(stdout="")
        if args[:3] == ["gh", "pr", "edit"]:
            return _Result(stdout="")
        if args[:2] == ["claude", "-p"]:
            return _Result(stdout=self._fix_bug_stdout)
        raise AssertionError(f"unexpected call: {args}")

    def calls_matching(self, prefix):
        return [c for c in self.calls if c[: len(prefix)] == prefix]


def _open_pr_list_calls(runner):
    return [
        c for c in runner.calls_matching(["gh", "pr", "list"])
        if "open" in c
    ]


_CLOSES_BODY = f"Fixes it.\n\ncloses #{_ISSUE_NUMBER}\n"


class TestExtractPrNumber(unittest.TestCase):
    def test_reads_the_field(self):
        self.assertEqual(extract_pr_number("status: complete\npr_number: 42\n"), 42)

    def test_absent_field_is_none(self):
        self.assertIsNone(extract_pr_number("status: complete\nsummary: did stuff\n"))

    def test_empty_input_is_none(self):
        self.assertIsNone(extract_pr_number(""))

    def test_prose_mention_is_not_the_field(self):
        self.assertIsNone(extract_pr_number("Opened as part of pr_number discussion"))


class TestRunBugLanePrNumberCarried(unittest.TestCase):
    def test_result_block_pr_number_is_used_without_list_lookup(self):
        session_output = (
            "```result\n"
            "status: completed\n"
            f"pr_number: {_PR_NUMBER}\n"
            "```\n"
        )
        runner = _StubRunner(fix_bug_stdout=session_output)

        result = run_bug_lane(
            runner, _REPO, _ISSUE_NUMBER, ci_deadline_seconds=0,
            policy_path=_dump(_AGENT_POLICY_ON),
        )

        self.assertEqual(result.pr_number, _PR_NUMBER)
        self.assertEqual(_open_pr_list_calls(runner), [])

    def test_absent_pr_number_falls_back_to_list_with_one_retry(self):
        runner = _StubRunner(
            fix_bug_stdout="completed",
            pr_list_bodies=[None, _CLOSES_BODY],
        )

        result = run_bug_lane(
            runner, _REPO, _ISSUE_NUMBER, ci_deadline_seconds=0,
            policy_path=_dump(_AGENT_POLICY_ON), pr_lookup_sleep=lambda _seconds: None,
        )

        self.assertEqual(result.pr_number, _PR_NUMBER)
        self.assertEqual(len(_open_pr_list_calls(runner)), 2)

    def test_still_pr_not_found_after_retry(self):
        runner = _StubRunner(
            fix_bug_stdout="completed",
            pr_list_bodies=[None, None],
        )

        result = run_bug_lane(
            runner, _REPO, _ISSUE_NUMBER, ci_deadline_seconds=0,
            policy_path=_dump(_AGENT_POLICY_ON), pr_lookup_sleep=lambda _seconds: None,
        )

        self.assertEqual(result.outcome, OUTCOME_DECLINED)
        self.assertEqual(result.reason, REASON_PR_NOT_FOUND)
        self.assertIsNone(result.pr_number)
        self.assertEqual(len(_open_pr_list_calls(runner)), 2)


if __name__ == "__main__":
    unittest.main()
