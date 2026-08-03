# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for GitHub-held autofix rate-limit state (FEAT-2026-0042/T02)."""

from __future__ import annotations

import json
import subprocess
import unittest

from specfuse.monitor.autofix_state import (
    AUTOFIX_FAILED_LABEL,
    DAILY_CAP,
    ROLLING_WINDOW_SECONDS,
    GitHubAutofixState,
    daily_cap_reached,
    has_prior_attempt,
    record_attempt,
)
from specfuse.monitor.issues import FINDING_LABEL, _marker

_REPO = "acme-widget/example"
_FINGERPRINT = "fp-1234"
_NOW = 1_700_000_000.0


class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _StubGitHub:
    """A tiny in-memory stand-in for `gh issue list`/`gh issue edit`.

    Every call it services goes through `__call__`, matching the
    `runner(args, check=...)` seam every autofix_state.py function takes --
    the same discipline `issues.py` uses, so a call that bypassed the seam
    (a raw `subprocess.run`) would escape this stub entirely rather than
    silently pass, per `[FEAT-2026-0031/G1-CLOSE]`.
    """

    def __init__(self):
        self._issues = {}
        self.calls = []

    def add_finding(self, number, fingerprint, body_extra=""):
        self._issues[number] = _marker(fingerprint) + "\n" + body_extra

    def __call__(self, args, check=True):
        self.calls.append(args)
        if args[:3] == ["gh", "issue", "list"]:
            rows = [{"number": n, "body": b} for n, b in self._issues.items()]
            return _Result(stdout=json.dumps(rows))
        if args[:3] == ["gh", "issue", "edit"]:
            number = int(args[3])
            body_index = args.index("--body") + 1
            self._issues[number] = args[body_index]
            return _Result()
        raise AssertionError(f"unexpected call: {args}")


class _RaisingGitHub:
    def __call__(self, args, check=True):
        raise RuntimeError("network unreachable")


class TestAutofixState(unittest.TestCase):
    def test_attempt_record_is_idempotent(self):
        gh = _StubGitHub()
        gh.add_finding(1, _FINGERPRINT)

        record_attempt(gh, _REPO, _FINGERPRINT, now=_NOW)
        record_attempt(gh, _REPO, _FINGERPRINT, now=_NOW + 10)

        body = gh._issues[1]
        self.assertEqual(
            body.count(f"specfuse:autofix-attempt fingerprint={_FINGERPRINT} "), 1
        )
        edit_calls = [c for c in gh.calls if c[:3] == ["gh", "issue", "edit"]]
        self.assertEqual(len(edit_calls), 1)
        self.assertTrue(has_prior_attempt(gh, _REPO, _FINGERPRINT))

    def test_has_prior_attempt_false_before_any_record(self):
        gh = _StubGitHub()
        gh.add_finding(1, _FINGERPRINT)
        self.assertFalse(has_prior_attempt(gh, _REPO, _FINGERPRINT))

    def test_has_prior_attempt_rechecks_client_side_not_just_listed(self):
        gh = _StubGitHub()
        # A decoy finding issue for a different, prefix-colliding fingerprint.
        gh.add_finding(1, _FINGERPRINT + "-other")
        # No issue exists for the exact fingerprint we ask about.
        self.assertFalse(has_prior_attempt(gh, _REPO, _FINGERPRINT))

    def test_daily_cap_counts_attempt_just_inside_window(self):
        gh = _StubGitHub()
        gh.add_finding(1, _FINGERPRINT)
        record_attempt(gh, _REPO, _FINGERPRINT, now=_NOW - (ROLLING_WINDOW_SECONDS - 1))

        self.assertTrue(daily_cap_reached(gh, _REPO, now=_NOW, cap=1))

    def test_daily_cap_does_not_count_attempt_just_outside_window(self):
        gh = _StubGitHub()
        gh.add_finding(1, _FINGERPRINT)
        record_attempt(gh, _REPO, _FINGERPRINT, now=_NOW - (ROLLING_WINDOW_SECONDS + 1))

        self.assertFalse(daily_cap_reached(gh, _REPO, now=_NOW, cap=1))

    def test_daily_cap_ignores_finding_issues_with_no_attempt_marker(self):
        gh = _StubGitHub()
        gh.add_finding(1, _FINGERPRINT)  # finding exists, no attempt yet
        self.assertFalse(daily_cap_reached(gh, _REPO, now=_NOW, cap=1))

    def test_daily_cap_treats_nonzero_returncode_as_no_rows(self):
        class _FailingList:
            def __call__(self, args, check=True):
                return _Result(returncode=1, stdout="")

        self.assertFalse(daily_cap_reached(_FailingList(), _REPO, now=_NOW, cap=1))

    def test_daily_cap_treats_unparseable_json_as_no_rows(self):
        class _GarbledList:
            def __call__(self, args, check=True):
                return _Result(returncode=0, stdout="not json")

        self.assertFalse(daily_cap_reached(_GarbledList(), _REPO, now=_NOW, cap=1))

    def test_daily_cap_default_constant_is_a_reasonable_positive_int(self):
        self.assertIsInstance(DAILY_CAP, int)
        self.assertGreater(DAILY_CAP, 0)

    def test_record_attempt_raises_lookup_error_without_a_finding_issue(self):
        gh = _StubGitHub()
        with self.assertRaises(LookupError):
            record_attempt(gh, _REPO, _FINGERPRINT, now=_NOW)

    def test_has_prior_attempt_fails_closed_when_runner_raises(self):
        self.assertTrue(has_prior_attempt(_RaisingGitHub(), _REPO, _FINGERPRINT))

    def test_daily_cap_reached_fails_closed_when_runner_raises(self):
        self.assertTrue(daily_cap_reached(_RaisingGitHub(), _REPO, now=_NOW))

    def test_github_autofix_state_adapts_to_rate_limit_state_reader_protocol(self):
        gh = _StubGitHub()
        gh.add_finding(1, _FINGERPRINT)
        record_attempt(gh, _REPO, _FINGERPRINT, now=_NOW)

        reader = GitHubAutofixState(runner=gh, repo=_REPO, now=_NOW, cap=1)
        self.assertTrue(reader.has_prior_attempt(_FINGERPRINT))
        self.assertTrue(reader.daily_cap_reached())

        other_reader = GitHubAutofixState(runner=gh, repo=_REPO, now=_NOW, cap=1)
        self.assertFalse(other_reader.has_prior_attempt("fp-not-seen"))

    def test_autofix_failed_label_is_registered(self):
        from specfuse.loop.labels import LABEL_REGISTRY

        matches = [spec for spec in LABEL_REGISTRY if spec.name == AUTOFIX_FAILED_LABEL]
        self.assertEqual(len(matches), 1)
        spec = matches[0]
        self.assertTrue(spec.name)
        self.assertTrue(spec.colour)
        self.assertTrue(spec.description)

    def test_label_registry_covers_consumers_suite_passes(self):
        result = subprocess.run(
            ["python3", "-m", "pytest", "-q", "tests/test_label_registry_covers_consumers.py"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_finding_label_constant_used_for_daily_cap_scoping(self):
        # Documents the scoping this module relies on rather than asserting
        # a private implementation detail.
        self.assertEqual(FINDING_LABEL, "monitoring-finding")

    def test_no_raw_external_calls_in_module(self):
        result = subprocess.run(
            [
                "grep",
                "-n",
                r"subprocess\.\|requests\.\|urllib\|os\.system",
                "specfuse/monitor/autofix_state.py",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1, msg=f"unexpected match: {result.stdout!r}")
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
