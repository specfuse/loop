#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.heartbeat."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from specfuse.loop.heartbeat import last_run_at, silence_check

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
  webhook_env: ""
  provider: none
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
  silence_hours: {silence_hours}
"""


def _write_policy(silence_hours: int = 24) -> str:
    fd = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, encoding="utf-8")
    fd.write(_POLICY.format(silence_hours=silence_hours))
    fd.close()
    return fd.name


def _write_events(repo_root: str, feature: str, lines: list) -> None:
    feature_dir = os.path.join(repo_root, ".specfuse", "features", feature)
    os.makedirs(feature_dir, exist_ok=True)
    path = os.path.join(feature_dir, "events.jsonl")
    with open(path, "w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line + "\n")


def _event(timestamp: str) -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "correlation_id": "FEAT-2026-0047/T04",
            "event_type": "task_started",
            "source": "driver",
            "source_version": "0.2.0",
            "payload": {},
        }
    )


class TestLastRunAt(unittest.TestCase):
    def test_no_events_returns_none(self):
        with tempfile.TemporaryDirectory() as repo_root:
            self.assertIsNone(last_run_at(repo_root=repo_root))

    def test_newest_across_multiple_features(self):
        with tempfile.TemporaryDirectory() as repo_root:
            _write_events(repo_root, "FEAT-2026-0001", [_event("2026-08-01T00:00:00+00:00")])
            _write_events(repo_root, "FEAT-2026-0002", [_event("2026-08-05T12:00:00+00:00")])
            newest = last_run_at(repo_root=repo_root)
            expected = datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc).timestamp()
            self.assertEqual(newest, expected)

    def test_malformed_line_is_skipped(self):
        with tempfile.TemporaryDirectory() as repo_root:
            _write_events(
                repo_root,
                "FEAT-2026-0001",
                ["not json at all", _event("2026-08-05T12:00:00+00:00")],
            )
            newest = last_run_at(repo_root=repo_root)
            expected = datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc).timestamp()
            self.assertEqual(newest, expected)

    def test_does_not_write_any_events_file(self):
        with tempfile.TemporaryDirectory() as repo_root:
            _write_events(repo_root, "FEAT-2026-0001", [_event("2026-08-05T12:00:00+00:00")])
            path = os.path.join(
                repo_root, ".specfuse", "features", "FEAT-2026-0001", "events.jsonl"
            )
            before = os.path.getmtime(path)
            last_run_at(repo_root=repo_root)
            after = os.path.getmtime(path)
            self.assertEqual(before, after)


class TestSilenceCheck(unittest.TestCase):
    def test_stale_when_no_events_within_window(self):
        policy_path = _write_policy(silence_hours=24)
        with tempfile.TemporaryDirectory() as repo_root:
            old = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
            _write_events(repo_root, "FEAT-2026-0001", [_event(old.isoformat())])
            now = (old + timedelta(hours=48)).timestamp()
            verdict = silence_check(now=now, repo_root=repo_root, policy_path=policy_path)
            self.assertTrue(verdict["stale"])
            self.assertFalse(verdict["no_events"])
            self.assertAlmostEqual(verdict["hours_since"], 48.0, places=3)

    def test_not_stale_with_recent_event(self):
        policy_path = _write_policy(silence_hours=24)
        with tempfile.TemporaryDirectory() as repo_root:
            recent = datetime(2026, 8, 10, 0, 0, 0, tzinfo=timezone.utc)
            _write_events(repo_root, "FEAT-2026-0001", [_event(recent.isoformat())])
            now = (recent + timedelta(hours=1)).timestamp()
            verdict = silence_check(now=now, repo_root=repo_root, policy_path=policy_path)
            self.assertFalse(verdict["stale"])
            self.assertFalse(verdict["no_events"])

    def test_boundary_exactly_at_window_is_not_stale(self):
        policy_path = _write_policy(silence_hours=24)
        with tempfile.TemporaryDirectory() as repo_root:
            event_time = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
            _write_events(repo_root, "FEAT-2026-0001", [_event(event_time.isoformat())])
            now = (event_time + timedelta(hours=24)).timestamp()
            verdict = silence_check(now=now, repo_root=repo_root, policy_path=policy_path)
            self.assertFalse(verdict["stale"])

    def test_no_events_at_all_is_a_distinct_verdict(self):
        policy_path = _write_policy(silence_hours=24)
        with tempfile.TemporaryDirectory() as repo_root:
            now = datetime(2026, 8, 10, 0, 0, 0, tzinfo=timezone.utc).timestamp()
            verdict = silence_check(now=now, repo_root=repo_root, policy_path=policy_path)
            self.assertTrue(verdict["no_events"])
            self.assertFalse(verdict["stale"])
            self.assertIsNone(verdict["last_run_at"])
            self.assertIsNone(verdict["hours_since"])

    def test_malformed_line_among_valid_does_not_look_silent(self):
        policy_path = _write_policy(silence_hours=24)
        with tempfile.TemporaryDirectory() as repo_root:
            recent = datetime(2026, 8, 10, 0, 0, 0, tzinfo=timezone.utc)
            _write_events(
                repo_root,
                "FEAT-2026-0001",
                ["{garbage", _event(recent.isoformat())],
            )
            now = (recent + timedelta(hours=1)).timestamp()
            verdict = silence_check(now=now, repo_root=repo_root, policy_path=policy_path)
            self.assertFalse(verdict["stale"])
            self.assertFalse(verdict["no_events"])

    def test_no_poster_call_from_within_silence_check(self):
        policy_path = _write_policy(silence_hours=24)
        with tempfile.TemporaryDirectory() as repo_root:
            recent = datetime(2026, 8, 10, 0, 0, 0, tzinfo=timezone.utc)
            _write_events(repo_root, "FEAT-2026-0001", [_event(recent.isoformat())])
            now = (recent + timedelta(hours=1)).timestamp()
            with mock.patch("specfuse.loop.notify.post_notification") as poster:
                silence_check(now=now, repo_root=repo_root, policy_path=policy_path)
                poster.assert_not_called()


if __name__ == "__main__":
    unittest.main()
