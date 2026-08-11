# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.agent.queue_read (FEAT-2026-0049/T12).

Covers: the queue-entry-to-disposition classifier and its precedence order,
`select_workable`'s wip_limit-capping and DONE-consumes-no-slot behaviour,
`resolve_wip_limit`/`resolve_gate_review`'s safe-default shape, the
`state.read_feature_summaries` rename-plus-alias, and the module's
no-write/no-gh/no-work-unit-file structural guarantees.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from specfuse.agent import state
from specfuse.agent.queue_read import (
    DISPOSITION_BLOCKED,
    DISPOSITION_DONE,
    DISPOSITION_NEEDS_DRAFTING,
    DISPOSITION_UNREADABLE,
    DISPOSITION_WORKABLE,
    classify_queue_entry,
    resolve_gate_review,
    resolve_wip_limit,
    select_workable,
)
from specfuse.agent.state import FeatureSummary

_RULES_BLOCK = (
    "rules:\n"
    "  bugs:\n"
    "    preempt: true\n"
    "    min_severity: low\n"
    '    automerge: "off"\n'
    "  features:\n"
    "    gate_review: human\n"
    "    wip_limit: 2\n"
    "    overrides:\n"
    "      FEAT-2026-0001: auto\n"
    "  triage:\n"
    "    auto: false\n"
)

_TAIL_BLOCK = (
    "budgets:\n"
    "  max_tokens_per_run: 2000000\n"
    "  max_open_prs: 3\n"
    "  max_items_per_day: 10\n"
    "escalation:\n"
    '  webhook_env: ""\n'
    '  assignee: ""\n'
    '  quiet_hours: ""\n'
    "  sla_hours: 24\n"
)


def _write(text: str) -> str:
    fd = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    fd.write(text)
    fd.close()
    return fd.name


def _feature(feature_id: str, status: str) -> FeatureSummary:
    return FeatureSummary(feature_id=feature_id, status=status, gates=())


class TestQueueWorkability(unittest.TestCase):
    def test_queue_entry_without_a_feature_folder_needs_drafting(self):
        disposition = classify_queue_entry("FEAT-2026-9999", (), {})
        self.assertEqual(disposition, DISPOSITION_NEEDS_DRAFTING)

    def test_unreadable_folder_beats_needs_drafting(self):
        errors = {"FEAT-2026-0001-widget": "ValueError: bad frontmatter"}
        disposition = classify_queue_entry("FEAT-2026-0001", (), errors)
        self.assertEqual(disposition, DISPOSITION_UNREADABLE)

    def test_blocked_and_deferred_statuses(self):
        features = (
            _feature("FEAT-2026-0001", "blocked"),
            _feature("FEAT-2026-0002", "deferred"),
        )
        self.assertEqual(
            classify_queue_entry("FEAT-2026-0001", features, {}), DISPOSITION_BLOCKED
        )
        self.assertEqual(
            classify_queue_entry("FEAT-2026-0002", features, {}), DISPOSITION_BLOCKED
        )

    def test_done_and_abandoned_statuses(self):
        features = (
            _feature("FEAT-2026-0001", "done"),
            _feature("FEAT-2026-0002", "abandoned"),
        )
        self.assertEqual(
            classify_queue_entry("FEAT-2026-0001", features, {}), DISPOSITION_DONE
        )
        self.assertEqual(
            classify_queue_entry("FEAT-2026-0002", features, {}), DISPOSITION_DONE
        )

    def test_active_and_planned_statuses_are_workable(self):
        features = (
            _feature("FEAT-2026-0001", "active"),
            _feature("FEAT-2026-0002", "planned"),
        )
        self.assertEqual(
            classify_queue_entry("FEAT-2026-0001", features, {}), DISPOSITION_WORKABLE
        )
        self.assertEqual(
            classify_queue_entry("FEAT-2026-0002", features, {}), DISPOSITION_WORKABLE
        )

    def test_status_outside_the_vocabulary_is_unreadable(self):
        features = (_feature("FEAT-2026-0001", "mystery"),)
        self.assertEqual(
            classify_queue_entry("FEAT-2026-0001", features, {}), DISPOSITION_UNREADABLE
        )


class TestSelectWorkable(unittest.TestCase):
    def test_done_entry_consumes_no_wip_limit_slot(self):
        features = (
            _feature("done-one", "done"),
            _feature("wk-one", "active"),
            _feature("wk-two", "active"),
        )
        queue = ("done-one", "wk-one", "wk-two")
        workable, needs_attention = select_workable(queue, features, {}, wip_limit=1)
        self.assertEqual(workable, ("wk-one",))
        self.assertEqual(needs_attention, ())

    def test_non_workable_non_done_entries_land_in_needs_attention(self):
        features = (
            _feature("blocked-one", "blocked"),
            _feature("wk-one", "active"),
        )
        queue = ("blocked-one", "wk-one", "missing-one")
        workable, needs_attention = select_workable(queue, features, {}, wip_limit=5)
        self.assertEqual(workable, ("wk-one",))
        self.assertEqual(
            needs_attention,
            (("blocked-one", DISPOSITION_BLOCKED), ("missing-one", DISPOSITION_NEEDS_DRAFTING)),
        )


class TestResolveWipLimit(unittest.TestCase):
    def test_missing_policy_file_defaults_to_one(self):
        self.assertEqual(resolve_wip_limit("/nonexistent/agent-policy.yml"), 1)

    def test_absent_key_defaults_to_one(self):
        path = _write(f"version: 1\nqueue: []\n{_TAIL_BLOCK}")
        try:
            self.assertEqual(resolve_wip_limit(path), 1)
        finally:
            os.unlink(path)

    def test_wrong_typed_value_defaults_to_one(self):
        rules = (
            "rules:\n"
            "  bugs:\n"
            "    preempt: true\n"
            "  features:\n"
            "    gate_review: human\n"
            '    wip_limit: "lots"\n'
        )
        path = _write(f"version: 1\nqueue: []\n{rules}{_TAIL_BLOCK}")
        try:
            self.assertEqual(resolve_wip_limit(path), 1)
        finally:
            os.unlink(path)

    def test_valid_value_is_honoured(self):
        path = _write(f"version: 1\nqueue: []\n{_RULES_BLOCK}{_TAIL_BLOCK}")
        try:
            self.assertEqual(resolve_wip_limit(path), 2)
        finally:
            os.unlink(path)


class TestResolveGateReview(unittest.TestCase):
    def test_missing_policy_file_defaults_to_human(self):
        self.assertEqual(resolve_gate_review("/nonexistent/agent-policy.yml"), "human")

    def test_absent_key_defaults_to_human(self):
        path = _write(f"version: 1\nqueue: []\n{_TAIL_BLOCK}")
        try:
            self.assertEqual(resolve_gate_review(path), "human")
        finally:
            os.unlink(path)

    def test_wrong_typed_value_defaults_to_human(self):
        rules = (
            "rules:\n"
            "  bugs:\n"
            "    preempt: true\n"
            "  features:\n"
            "    gate_review: nonsense\n"
            "    wip_limit: 1\n"
        )
        path = _write(f"version: 1\nqueue: []\n{rules}{_TAIL_BLOCK}")
        try:
            self.assertEqual(resolve_gate_review(path), "human")
        finally:
            os.unlink(path)

    def test_override_wins_over_section_default(self):
        path = _write(f"version: 1\nqueue: []\n{_RULES_BLOCK}{_TAIL_BLOCK}")
        try:
            self.assertEqual(resolve_gate_review(path), "human")
            self.assertEqual(
                resolve_gate_review(path, feature_id="FEAT-2026-0001"), "auto"
            )
        finally:
            os.unlink(path)


class TestStateAlias(unittest.TestCase):
    def test_read_feature_summaries_is_read_features(self):
        self.assertIs(state.read_feature_summaries, state._read_features)


class TestModuleStructure(unittest.TestCase):
    def test_no_write_no_gh_no_work_unit_reads(self):
        captured = []

        def runner(argv, check=False):
            captured.append(argv)
            raise AssertionError("queue_read must not invoke a runner")

        classify_queue_entry("FEAT-2026-0001", (), {})
        select_workable((), (), {}, wip_limit=1)
        self.assertEqual(captured, [])

    def test_source_contains_no_wu_or_read_frontmatter_reference(self):
        source = Path("specfuse/agent/queue_read.py").read_text(encoding="utf-8")
        self.assertNotIn("WU-", source)
        self.assertNotIn("read_frontmatter", source)


if __name__ == "__main__":
    unittest.main()
