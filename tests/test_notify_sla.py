#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.notify_sla."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from specfuse.loop.escalation import NEEDS_HUMAN_LABEL
from specfuse.loop.notify_sla import PARKED_LABEL, sla_sweep

_POLICY = """\
version: 1
queue: []
rules:
  bugs:
    preempt: true
    min_severity: low
    automerge: "off"
  features:
    gate_review: human
    wip_limit: 1
  triage:
    auto: false
budgets:
  max_tokens_per_run: 2000000
  max_open_prs: 3
  max_items_per_day: 10
escalation:
  webhook_env: {webhook_env}
  provider: {provider}
  assignee: ""
  quiet_hours: ""
  sla_hours: {sla_hours}
"""


def _write_policy(webhook_env: str = '""', provider: str = "none", sla_hours: int = 24) -> str:
    text = _POLICY.format(webhook_env=webhook_env, provider=provider, sla_hours=sla_hours)
    fd = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, encoding="utf-8")
    fd.write(text)
    fd.close()
    return fd.name


class _Result:
    def __init__(self, returncode: int, stdout: str):
        self.returncode = returncode
        self.stdout = stdout


class FakeGitHub:
    """Stateful fake `gh` runner: mutates its own issue store on write."""

    def __init__(self, issues: dict):
        self.issues = issues
        self.calls: list = []

    def runner(self, args: list, check: bool = True):
        self.calls.append(list(args))

        if args[:3] == ["gh", "issue", "list"]:
            rows = []
            for number, data in self.issues.items():
                rows.append(
                    {
                        "number": int(number),
                        "createdAt": data["createdAt"],
                        "comments": [{"body": b} for b in data["comments"]],
                    }
                )
            return _Result(0, json.dumps(rows))

        if args[:3] == ["gh", "issue", "comment"]:
            number = args[3]
            body = args[args.index("--body") + 1]
            self.issues[number]["comments"].append(body)
            return _Result(0, "")

        if args[:3] == ["gh", "issue", "edit"]:
            number = args[3]
            if "--add-label" in args:
                label = args[args.index("--add-label") + 1]
                self.issues[number].setdefault("labels", []).append(label)
            return _Result(0, "")

        raise AssertionError(f"unexpected gh call: {args}")


_NOW = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)


def _created_at(hours_ago: float) -> str:
    return (_NOW - timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


class TestSlaSweep(unittest.TestCase):
    def test_repings_once_then_parks(self):
        policy_path = _write_policy(webhook_env="SPECFUSE_SLA_TEST_URL", provider="discord", sla_hours=24)
        posts = []

        def poster(url, payload):
            posts.append((url, payload))
            return 200

        gh = FakeGitHub({"7": {"createdAt": _created_at(30), "comments": []}})

        with mock.patch.dict("os.environ", {"SPECFUSE_SLA_TEST_URL": "https://example.invalid/hook"}):
            first = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)
            self.assertEqual(first, [{"number": "7", "action": "repinged"}])
            self.assertEqual(len(posts), 1)
            comment_calls = [c for c in gh.calls if c[:3] == ["gh", "issue", "comment"]]
            self.assertEqual(len(comment_calls), 1)
            self.assertEqual(len(gh.issues["7"]["comments"]), 1)
            self.assertTrue(gh.issues["7"]["comments"][0].startswith("<!-- specfuse:sla-repinged at="))

            second = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)
            self.assertEqual(second, [{"number": "7", "action": "parked"}])
            self.assertEqual(len(posts), 1)  # no second post
            self.assertIn(PARKED_LABEL, gh.issues["7"].get("labels", []))

    def test_issue_younger_than_sla_is_untouched(self):
        policy_path = _write_policy(sla_hours=24)
        gh = FakeGitHub({"1": {"createdAt": _created_at(5), "comments": []}})

        result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path)

        self.assertEqual(result, [])
        self.assertEqual(gh.issues["1"]["comments"], [])
        self.assertNotIn("labels", gh.issues["1"])

    def test_boundary_at_exactly_the_window_is_untouched(self):
        policy_path = _write_policy(sla_hours=24)
        gh = FakeGitHub({"2": {"createdAt": _created_at(24), "comments": []}})

        result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path)

        self.assertEqual(result, [])
        self.assertEqual(gh.issues["2"]["comments"], [])

    def test_boundary_just_past_the_window_acts(self):
        policy_path = _write_policy(sla_hours=24)
        gh = FakeGitHub({"3": {"createdAt": _created_at(24.001), "comments": []}})

        result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path)

        self.assertEqual(result, [{"number": "3", "action": "repinged"}])

    def test_no_marker_repings_exactly_once(self):
        policy_path = _write_policy(webhook_env="SPECFUSE_SLA_TEST_URL2", provider="slack", sla_hours=24)
        posts = []

        def poster(url, payload):
            posts.append((url, payload))
            return 200

        gh = FakeGitHub({"4": {"createdAt": _created_at(48), "comments": []}})

        with mock.patch.dict("os.environ", {"SPECFUSE_SLA_TEST_URL2": "https://example.invalid/hook"}):
            result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)

        self.assertEqual(result, [{"number": "4", "action": "repinged"}])
        self.assertEqual(len(posts), 1)
        self.assertEqual(len(gh.issues["4"]["comments"]), 1)

    def test_already_marked_parks_with_no_second_post(self):
        policy_path = _write_policy(webhook_env="SPECFUSE_SLA_TEST_URL3", provider="slack", sla_hours=24)
        posts = []

        def poster(url, payload):
            posts.append((url, payload))
            return 200

        marker = "<!-- specfuse:sla-repinged at=1780000000.0 -->"
        gh = FakeGitHub({"5": {"createdAt": _created_at(48), "comments": [marker]}})

        with mock.patch.dict("os.environ", {"SPECFUSE_SLA_TEST_URL3": "https://example.invalid/hook"}):
            result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)

        self.assertEqual(result, [{"number": "5", "action": "parked"}])
        self.assertEqual(len(posts), 0)
        self.assertIn(PARKED_LABEL, gh.issues["5"].get("labels", []))
        comment_calls = [c for c in gh.calls if c[:3] == ["gh", "issue", "comment"]]
        self.assertEqual(len(comment_calls), 0)

    def test_two_successive_sweeps_are_stable(self):
        policy_path = _write_policy(webhook_env="SPECFUSE_SLA_TEST_URL4", provider="slack", sla_hours=24)
        posts = []

        def poster(url, payload):
            posts.append((url, payload))
            return 200

        gh = FakeGitHub({"6": {"createdAt": _created_at(48), "comments": []}})

        with mock.patch.dict("os.environ", {"SPECFUSE_SLA_TEST_URL4": "https://example.invalid/hook"}):
            first = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)
            second = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)
            third = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)

        self.assertEqual(first, [{"number": "6", "action": "repinged"}])
        self.assertEqual(second, [{"number": "6", "action": "parked"}])
        self.assertEqual(third, [{"number": "6", "action": "parked"}])
        self.assertEqual(len(posts), 1)

    def test_parked_issue_never_closed(self):
        policy_path = _write_policy(sla_hours=24)
        marker = "<!-- specfuse:sla-repinged at=1780000000.0 -->"
        gh = FakeGitHub({"9": {"createdAt": _created_at(48), "comments": [marker]}})

        sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path)

        close_calls = [c for c in gh.calls if "close" in c]
        self.assertEqual(close_calls, [])

    def test_malformed_marker_ignored_not_fatal(self):
        policy_path = _write_policy(webhook_env="SPECFUSE_SLA_TEST_URL5", provider="slack", sla_hours=24)
        posts = []

        def poster(url, payload):
            posts.append((url, payload))
            return 200

        garbage = "<!-- specfuse:sla-repinged at=not-a-number -->"
        gh = FakeGitHub({"10": {"createdAt": _created_at(48), "comments": [garbage]}})

        with mock.patch.dict("os.environ", {"SPECFUSE_SLA_TEST_URL5": "https://example.invalid/hook"}):
            result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)

            # No valid marker found -> treated as not-yet-repinged, repinged exactly once.
            self.assertEqual(result, [{"number": "10", "action": "repinged"}])
            self.assertEqual(len(posts), 1)
            self.assertEqual(len(gh.issues["10"]["comments"]), 2)

            # A second sweep now finds the valid marker added above -> parks, no extra post.
            second = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)
            self.assertEqual(second, [{"number": "10", "action": "parked"}])
            self.assertEqual(len(posts), 1)

    def test_no_webhook_configured_still_parks_no_poster_call(self):
        policy_path = _write_policy(webhook_env='""', provider="none", sla_hours=24)
        calls = []

        def poster(url, payload):
            calls.append((url, payload))
            return 200

        marker = "<!-- specfuse:sla-repinged at=1780000000.0 -->"
        gh = FakeGitHub({"11": {"createdAt": _created_at(48), "comments": [marker]}})

        result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path, poster=poster)

        self.assertEqual(result, [{"number": "11", "action": "parked"}])
        self.assertEqual(calls, [])
        self.assertIn(PARKED_LABEL, gh.issues["11"].get("labels", []))

    def test_all_paths_use_injected_runner_no_network(self):
        policy_path = _write_policy(sla_hours=24)
        gh = FakeGitHub(
            {
                "20": {"createdAt": _created_at(1), "comments": []},  # untouched
                "21": {"createdAt": _created_at(48), "comments": []},  # repinged
                "22": {
                    "createdAt": _created_at(48),
                    "comments": ["<!-- specfuse:sla-repinged at=1780000000.0 -->"],
                },  # parked
            }
        )

        result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path)

        self.assertEqual(len(result), 2)
        self.assertTrue(any(c[:3] == ["gh", "issue", "list"] for c in gh.calls))
        self.assertTrue(any(c[:3] == ["gh", "issue", "comment"] for c in gh.calls))
        self.assertTrue(any(c[:3] == ["gh", "issue", "edit"] for c in gh.calls))

    def test_needs_human_label_imported_not_retyped(self):
        from specfuse.loop import escalation

        self.assertIs(NEEDS_HUMAN_LABEL, escalation.NEEDS_HUMAN_LABEL)

    def test_missing_policy_file_falls_back_to_default_sla(self):
        gh = FakeGitHub({"30": {"createdAt": _created_at(25), "comments": []}})

        result = sla_sweep(
            gh.runner, "acme/widget", now=_NOW, policy_path="/nonexistent/agent-policy.yml"
        )

        self.assertEqual(result, [{"number": "30", "action": "repinged"}])

    def test_policy_without_escalation_section_falls_back_to_default_sla(self):
        fd = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, encoding="utf-8")
        fd.write("version: 1\nqueue: []\n")
        fd.close()
        gh = FakeGitHub({"31": {"createdAt": _created_at(25), "comments": []}})

        result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=fd.name)

        self.assertEqual(result, [{"number": "31", "action": "repinged"}])

    def test_invalid_sla_hours_falls_back_to_default(self):
        policy_path = _write_policy(sla_hours=0)
        gh = FakeGitHub({"32": {"createdAt": _created_at(25), "comments": []}})

        result = sla_sweep(gh.runner, "acme/widget", now=_NOW, policy_path=policy_path)

        self.assertEqual(result, [{"number": "32", "action": "repinged"}])

    def test_list_command_failure_yields_no_records(self):
        policy_path = _write_policy(sla_hours=24)

        def failing_runner(args, check=True):
            return _Result(1, "")

        result = sla_sweep(failing_runner, "acme/widget", now=_NOW, policy_path=policy_path)

        self.assertEqual(result, [])

    def test_list_command_unparseable_json_yields_no_records(self):
        policy_path = _write_policy(sla_hours=24)

        def garbage_runner(args, check=True):
            return _Result(0, "not json")

        result = sla_sweep(garbage_runner, "acme/widget", now=_NOW, policy_path=policy_path)

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
