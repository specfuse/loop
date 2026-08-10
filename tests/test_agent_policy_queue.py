#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for FEAT-2026-0044/T02: load_policy, roadmap_statuses, and the
queue-vs-roadmap WARN/ERROR split in validate_agent_policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop.agent_policy import load_policy, validate_agent_policy
from specfuse.loop.lint_roadmap import roadmap_statuses

REPO_ROOT = Path(__file__).resolve().parents[1]

_RULES_BLOCK = (
    "rules:\n"
    "  bugs:\n"
    "    preempt: true\n"
    "    min_severity: low\n"
    '    automerge: "off"\n'
    "  features:\n"
    "    gate_review: human\n"
    "    wip_limit: 1\n"
    "  triage:\n"
    "    auto: false\n"
)

_TAIL_BLOCK = (
    "budgets:\n"
    "  max_tokens_per_run: 2000000\n"
    "  max_open_prs: 3\n"
    "  max_items_per_day: 10\n"
    "escalation:\n"
    '  webhook: ""\n'
    '  assignee: ""\n'
    '  quiet_hours: ""\n'
    "  sla_hours: 24\n"
)


def _config_with_queue(*feat_ids: str) -> str:
    queue_lines = "".join(f"  - {fid}\n" for fid in feat_ids)
    queue_block = f"queue:\n{queue_lines}" if feat_ids else "queue: []\n"
    return f"version: 1\n{queue_block}{_RULES_BLOCK}{_TAIL_BLOCK}"


def _write(text: str) -> str:
    fd = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    fd.write(text)
    fd.close()
    return fd.name


class TestLoadPolicy(unittest.TestCase):
    def test_load_policy_returns_parsed_mapping(self):
        path = _write(_config_with_queue("FEAT-2026-0048"))
        parsed = load_policy(path)
        self.assertEqual(parsed["version"], 1)
        self.assertEqual(parsed["queue"], ["FEAT-2026-0048"])

    def test_load_policy_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_policy("/nonexistent/agent-policy.yml")

    def test_load_policy_default_path_is_live_repo_file(self):
        parsed = load_policy()
        self.assertIn("queue", parsed)


class TestRoadmapStatuses(unittest.TestCase):
    def test_known_statuses_against_real_roadmap(self):
        statuses = roadmap_statuses(REPO_ROOT)
        self.assertEqual(statuses.get("FEAT-2026-0002"), "done")
        self.assertEqual(statuses.get("FEAT-2026-0011"), "blocked")

    def test_absent_roadmap_returns_empty_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(roadmap_statuses(Path(tmp)), {})


class TestQueueAgainstRoadmap(unittest.TestCase):
    def test_absent_feature_id_is_error(self):
        path = _write(_config_with_queue("FEAT-2026-9999"))
        findings = validate_agent_policy(path)
        matching = [
            f for f in findings
            if f == "ERROR: queue: 'FEAT-2026-9999' has no row in roadmap.md"
        ]
        self.assertEqual(len(matching), 1, findings)

    def test_done_feature_id_is_warn(self):
        path = _write(_config_with_queue("FEAT-2026-0002"))
        findings = validate_agent_policy(path)
        matching = [
            f for f in findings
            if f == "WARN: queue: 'FEAT-2026-0002' is roadmap status 'done'"
        ]
        self.assertEqual(len(matching), 1, findings)
        errors = [f for f in findings if f.startswith("ERROR: ")]
        self.assertEqual(errors, [])

    def test_planned_active_blocked_deferred_produce_no_finding(self):
        # Every ID is looked up from the live roadmap by status rather than
        # hardcoded. Pinning an ID pins its status at authoring time, and the
        # status is exactly what changes: this test asserted FEAT-2026-0048 was
        # `planned` and went red the morning that feature reached `done` — on a
        # correct tree, which is the failure `planning-discipline.md` §2 exists
        # to prevent and which the WARN/ERROR split was designed to avoid.
        statuses = roadmap_statuses(REPO_ROOT)

        checked = 0
        for status in ("planned", "active", "blocked", "deferred"):
            feat_id = next(
                (fid for fid, st in statuses.items() if st == status), None
            )
            if feat_id is None:
                continue  # no feature currently in that state — nothing to assert
            with self.subTest(feat_id=feat_id, status=status):
                path = _write(_config_with_queue(feat_id))
                findings = validate_agent_policy(path)
                self.assertEqual(findings, [], findings)
            checked += 1

        # Guard against the whole loop silently asserting nothing if the roadmap
        # ever holds none of the four non-terminal statuses.
        self.assertGreater(checked, 0, "no non-terminal roadmap status to check")

    def test_skipped_without_roadmap(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_dir = Path(tmp) / ".specfuse"
            policy_dir.mkdir()
            policy_path = policy_dir / "agent-policy.yml"
            policy_path.write_text(
                _config_with_queue("FEAT-2026-0048"), encoding="utf-8"
            )
            import os

            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                findings = validate_agent_policy(str(policy_path))
            finally:
                os.chdir(cwd)
            self.assertEqual(findings, [])


class TestLiveDogfoodFile(unittest.TestCase):
    def test_live_agent_policy_has_zero_errors(self):
        path = REPO_ROOT / ".specfuse" / "agent-policy.yml"
        findings = validate_agent_policy(str(path))
        errors = [f for f in findings if f.startswith("ERROR: ")]
        self.assertEqual(errors, [], findings)


if __name__ == "__main__":
    unittest.main()
