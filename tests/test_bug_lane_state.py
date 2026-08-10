# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for GitHub-held bug-lane state (FEAT-2026-0048/T03)."""

from __future__ import annotations

import json
import unittest

from specfuse.loop import bug_lane_state
from specfuse.loop.bug_lane import evaluate_merge_guardrails
from specfuse.loop.bug_lane_state import (
    ROLLING_WINDOW_SECONDS,
    GitHubMergeCapState,
    parse_merge_marker,
    record_merge,
    render_merge_marker,
    triaged_bug_intake,
)
from specfuse.loop.triage import render_marker
from specfuse.monitor.autofix_state import AUTOFIX_FAILED_LABEL

_REPO = "acme-widget/example"
_NOW = 1_700_000_000.0


class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _StubGitHub:
    """In-memory stand-in for `gh pr list/view/edit` and `gh issue list`."""

    def __init__(self):
        self._prs = {}
        self._issues = {}
        self.calls = []
        self.opened_local_files = False

    def add_merged_pr(self, number, body=""):
        self._prs[number] = body

    def add_issue(self, number, body="", labels=None):
        self._issues[number] = {"number": number, "body": body, "labels": labels or []}

    def __call__(self, args, check=True):
        self.calls.append(args)
        if args[:3] == ["gh", "pr", "list"]:
            rows = [{"number": n, "body": b} for n, b in self._prs.items()]
            return _Result(stdout=json.dumps(rows))
        if args[:3] == ["gh", "pr", "view"]:
            number = int(args[3])
            return _Result(stdout=json.dumps({"body": self._prs.get(number, "")}))
        if args[:3] == ["gh", "pr", "edit"]:
            number = int(args[3])
            body_index = args.index("--body") + 1
            self._prs[number] = args[body_index]
            return _Result()
        if args[:3] == ["gh", "issue", "list"]:
            rows = list(self._issues.values())
            return _Result(stdout=json.dumps(rows))
        raise AssertionError(f"unexpected call: {args}")


class _RaisingGitHub:
    def __call__(self, args, check=True):
        raise RuntimeError("network unreachable")


class TestGitHubMergeCapState(unittest.TestCase):
    def test_count_is_rederived_from_markers(self):
        gh = _StubGitHub()
        gh.add_merged_pr(1, render_merge_marker(_NOW - 10))
        gh.add_merged_pr(2, render_merge_marker(_NOW - 20))

        state = GitHubMergeCapState(runner=gh, repo=_REPO, now=_NOW)

        self.assertEqual(state.merges_last_24h(), 2)
        self.assertEqual(state.merges_last_24h(), 2)

    def test_marker_outside_window_excluded(self):
        gh = _StubGitHub()
        gh.add_merged_pr(1, render_merge_marker(_NOW - 10))
        gh.add_merged_pr(2, render_merge_marker(_NOW - ROLLING_WINDOW_SECONDS - 1))

        state = GitHubMergeCapState(runner=gh, repo=_REPO, now=_NOW)

        self.assertEqual(state.merges_last_24h(), 1)

    def test_malformed_marker_ignored_not_fatal(self):
        gh = _StubGitHub()
        gh.add_merged_pr(1, "<!-- specfuse:bug-automerge at=not-a-number -->")
        gh.add_merged_pr(2, render_merge_marker(_NOW - 5))
        gh.add_merged_pr(3, "no marker here at all")

        state = GitHubMergeCapState(runner=gh, repo=_REPO, now=_NOW)

        self.assertEqual(state.merges_last_24h(), 1)

    def test_accepted_by_evaluate_merge_guardrails_with_no_adapter(self):
        gh = _StubGitHub()
        state = GitHubMergeCapState(runner=gh, repo=_REPO, now=_NOW)

        decision = evaluate_merge_guardrails(
            changed_files=["tests/test_thing.py"],
            ci_conclusion="success",
            diff_lines=10,
            max_diff_lines=500,
            provenance={"kind": "triaged_issue", "ref": "issue-1"},
            max_merges_per_day=5,
            state_reader=state,
        )

        self.assertTrue(decision.eligible)

    def test_marker_round_trips_through_own_parser(self):
        marker = render_merge_marker(_NOW)
        self.assertEqual(marker, f"<!-- specfuse:bug-automerge at={_NOW} -->")
        self.assertEqual(parse_merge_marker(marker), _NOW)

    def test_read_failure_fails_closed(self):
        gh = _RaisingGitHub()
        state = GitHubMergeCapState(runner=gh, repo=_REPO, now=_NOW)

        self.assertGreaterEqual(state.merges_last_24h(), 5)

    def test_no_local_file_opened_for_cap_state(self):
        gh = _StubGitHub()
        state = GitHubMergeCapState(runner=gh, repo=_REPO, now=_NOW)
        state.merges_last_24h()

        for call in gh.calls:
            self.assertEqual(call[0], "gh")


class TestRecordMerge(unittest.TestCase):
    def test_second_call_does_not_produce_second_marker(self):
        gh = _StubGitHub()
        gh.add_merged_pr(42, "existing pr body")

        record_merge(gh, _REPO, 42, at=_NOW)
        record_merge(gh, _REPO, 42, at=_NOW + 100)

        body = gh._prs[42]
        self.assertEqual(body.count("<!-- specfuse:bug-automerge at="), 1)
        self.assertIn(render_merge_marker(_NOW), body)


class TestTriagedBugIntake(unittest.TestCase):
    def test_classifies_untriaged_non_bug_and_bug_issues(self):
        gh = _StubGitHub()
        gh.add_issue(1, body="no triage marker here")
        gh.add_issue(2, body=render_marker("feature", "high"))
        gh.add_issue(3, body=render_marker("bug", "high"))

        intake = triaged_bug_intake(gh, _REPO)

        numbers = {issue["number"] for issue in intake}
        self.assertEqual(numbers, {3})

    def test_excludes_issue_with_autofix_failed_label(self):
        gh = _StubGitHub()
        gh.add_issue(1, body=render_marker("bug", "high"), labels=[{"name": AUTOFIX_FAILED_LABEL}])
        gh.add_issue(2, body=render_marker("bug", "high"))

        intake = triaged_bug_intake(gh, _REPO)

        numbers = {issue["number"] for issue in intake}
        self.assertEqual(numbers, {2})

    def test_reuses_triage_parser_no_second_regex_over_marker_format(self):
        import inspect

        source = inspect.getsource(bug_lane_state)
        self.assertNotIn("specfuse:triage", source)


if __name__ == "__main__":
    unittest.main()
