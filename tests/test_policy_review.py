#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.policy_review (FEAT-2026-0076/T04).

`review_agent_policy` compares an existing `.specfuse/agent-policy.yml`
against the *shipped baseline* -- `agent_policy.DEFAULT_*` where a constant
exists, `.specfuse/agent-policy.yml.example`'s literal value where one does
not -- for the four in-scope keys, and records which source answered each
key. The comparison is a hint, not a claim: a `matches_baseline` entry must
carry a caveat saying so, in the returned data, not only in prose. See
GATE-02-REVIEW.md "The provenance question".
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from specfuse.loop.agent_policy import DEFAULT_TEST_PATHS
from specfuse.loop.policy_review import review_agent_policy

_IN_SCOPE_KEYS = (
    "budgets.max_tokens_per_run",
    "budgets.max_items_per_day",
    "budgets.max_open_prs",
    "rules.bugs.test_paths",
)

_EXAMPLE_TEXT = textwrap.dedent("""\
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
      silence_hours: 24
    """)


def _write_example(root: Path, text: str = _EXAMPLE_TEXT) -> None:
    (root / ".specfuse").mkdir(parents=True, exist_ok=True)
    (root / ".specfuse" / "agent-policy.yml.example").write_text(text)


def _write_policy(root: Path, text: str) -> None:
    (root / ".specfuse").mkdir(parents=True, exist_ok=True)
    (root / ".specfuse" / "agent-policy.yml").write_text(text)


def _write_events(root: Path) -> None:
    import json

    d = root / ".specfuse" / "features" / "FEAT-2026-0001-x"
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps({
            "timestamp": 1.0,
            "correlation_id": "FEAT-2026-0001/T01",
            "event_type": "attempt_outcome",
            "payload": {"outcome": "passed", "cost_usd": 2.0, "attempt": 1},
        }),
        json.dumps({
            "timestamp": 2.0,
            "correlation_id": "FEAT-2026-0001/T02",
            "event_type": "attempt_outcome",
            "payload": {"outcome": "passed", "cost_usd": 3.0, "attempt": 1},
        }),
    ]
    (d / "events.jsonl").write_text("\n".join(lines) + "\n")


_POLICY_AT_BASELINE = textwrap.dedent("""\
    version: 1
    queue:
      - FEAT-2026-0001
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
      silence_hours: 24
    """)

_POLICY_DIFFERS = textwrap.dedent("""\
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
      max_tokens_per_run: 900000
      max_open_prs: 3
      max_items_per_day: 10
    escalation:
      webhook_env: ""
      provider: none
      assignee: ""
      quiet_hours: ""
      sla_hours: 24
      silence_hours: 24
    """)

_POLICY_MISSING_TEST_PATHS = _POLICY_AT_BASELINE  # rules.bugs.test_paths absent


class TestReviewAgentPolicy(unittest.TestCase):
    def test_baseline_match_is_classified_and_caveated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root)
            _write_policy(root, _POLICY_AT_BASELINE)

            result = review_agent_policy(root)

            entry = result["budgets.max_tokens_per_run"]
            self.assertEqual(entry["classification"], "matches_baseline")
            self.assertIsInstance(entry["caveat"], str)
            self.assertIn("indistinguishable", entry["caveat"])

    def test_differs_from_baseline_has_no_caveat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root)
            _write_policy(root, _POLICY_DIFFERS)

            result = review_agent_policy(root)

            entry = result["budgets.max_tokens_per_run"]
            self.assertEqual(entry["classification"], "differs_from_baseline")
            self.assertIsNone(entry["caveat"])

    def test_returns_all_four_in_scope_keys_with_baseline_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root)
            _write_policy(root, _POLICY_AT_BASELINE)

            result = review_agent_policy(root)

            self.assertEqual(set(result), set(_IN_SCOPE_KEYS))
            for key in _IN_SCOPE_KEYS:
                entry = result[key]
                self.assertIn("current", entry)
                self.assertIn("proposal", entry)
                self.assertIn("baseline", entry)
                self.assertIn("classification", entry)
                self.assertTrue(entry["baseline"]["available"])
                self.assertIn("source", entry["baseline"])

            self.assertEqual(
                result["rules.bugs.test_paths"]["baseline"]["source"],
                "agent_policy.DEFAULT_TEST_PATHS",
            )
            for key in (
                "budgets.max_tokens_per_run",
                "budgets.max_items_per_day",
                "budgets.max_open_prs",
            ):
                self.assertEqual(
                    result[key]["baseline"]["source"], "agent-policy.yml.example"
                )

    def test_test_paths_baseline_matches_default_constant(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root)
            _write_policy(root, _POLICY_MISSING_TEST_PATHS)

            result = review_agent_policy(root)

            self.assertEqual(
                result["rules.bugs.test_paths"]["baseline"]["value"],
                list(DEFAULT_TEST_PATHS),
            )

    def test_proposal_kind_measured_vs_converted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root)
            _write_policy(root, _POLICY_AT_BASELINE)
            (root / "tests").mkdir()
            (root / ".specfuse").mkdir(exist_ok=True)
            (root / ".specfuse" / "verification.yml").write_text(
                'code:\n  - name: tests\n    command: "python3 -m unittest discover -s tests"\n'
            )
            _write_events(root)

            def _ok_runner(args, check=True):
                from types import SimpleNamespace
                return SimpleNamespace(returncode=0, stdout="[]", stderr="")

            result = review_agent_policy(root, runner=_ok_runner)

            test_paths_entry = result["rules.bugs.test_paths"]
            self.assertTrue(test_paths_entry["proposal"]["available"])
            self.assertEqual(test_paths_entry["proposal"]["kind"], "measured")

            tokens_entry = result["budgets.max_tokens_per_run"]
            self.assertEqual(tokens_entry["proposal"]["kind"], "converted")
            self.assertIn("assumed", tokens_entry["proposal"]["evidence"])

            items_entry = result["budgets.max_items_per_day"]
            self.assertEqual(items_entry["proposal"]["kind"], "converted")

            open_prs_entry = result["budgets.max_open_prs"]
            self.assertEqual(open_prs_entry["proposal"]["kind"], "converted")

    def test_three_absences_are_distinguishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Absence 1: key absent from an otherwise-present policy file.
            root_key_absent = Path(tmp) / "key-absent"
            _write_example(root_key_absent)
            _write_policy(root_key_absent, _POLICY_MISSING_TEST_PATHS)
            r1 = review_agent_policy(root_key_absent)
            self.assertEqual(
                r1["rules.bugs.test_paths"]["classification"], "absent_from_file"
            )

            # Absence 2: key present, but propose_policy_defaults has no
            # proposal for it (no history, no gh runner, no test tree).
            root_no_proposal = Path(tmp) / "no-proposal"
            _write_example(root_no_proposal)
            _write_policy(root_no_proposal, _POLICY_AT_BASELINE)
            r2 = review_agent_policy(root_no_proposal, runner=None)
            self.assertFalse(r2["budgets.max_open_prs"]["proposal"]["available"])
            self.assertNotEqual(
                r2["budgets.max_open_prs"]["classification"], "baseline_unavailable"
            )

            # Absence 3: baseline itself unreadable (no example file at all).
            root_no_baseline = Path(tmp) / "no-baseline"
            (root_no_baseline / ".specfuse").mkdir(parents=True)
            _write_policy(root_no_baseline, _POLICY_AT_BASELINE)
            r3 = review_agent_policy(root_no_baseline)
            self.assertEqual(
                r3["budgets.max_open_prs"]["classification"], "baseline_unavailable"
            )

            # All three are pairwise distinct observable shapes.
            self.assertNotEqual(
                r1["rules.bugs.test_paths"]["classification"],
                r3["budgets.max_open_prs"]["classification"],
            )

    def test_missing_example_file_marks_budgets_baseline_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specfuse").mkdir(parents=True)
            _write_policy(root, _POLICY_AT_BASELINE)
            # No .specfuse/agent-policy.yml.example written at all.

            result = review_agent_policy(root)

            for key in (
                "budgets.max_tokens_per_run",
                "budgets.max_items_per_day",
                "budgets.max_open_prs",
            ):
                self.assertEqual(result[key]["classification"], "baseline_unavailable")
                self.assertFalse(result[key]["baseline"]["available"])
            # rules.bugs.test_paths's baseline is the DEFAULT_TEST_PATHS
            # constant, unaffected by the example file's absence.
            self.assertNotEqual(
                result["rules.bugs.test_paths"]["classification"], "baseline_unavailable"
            )

    def test_unparseable_example_file_marks_budgets_baseline_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root, text="budgets:\n  max_tokens_per_run: [unterminated\n")
            _write_policy(root, _POLICY_AT_BASELINE)

            result = review_agent_policy(root)

            self.assertEqual(
                result["budgets.max_tokens_per_run"]["classification"],
                "baseline_unavailable",
            )

    def test_queue_never_appears_in_returned_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root)
            policy_with_queue = _POLICY_AT_BASELINE  # already carries a populated queue:
            _write_policy(root, policy_with_queue)

            result = review_agent_policy(root)

            self.assertNotIn("queue", result)
            rendered = repr(result)
            self.assertNotIn("FEAT-2026-0001", rendered)

    def test_result_is_per_key_readout_not_a_whole_file_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root)
            _write_policy(root, _POLICY_AT_BASELINE)

            result = review_agent_policy(root)

            self.assertEqual(set(result), set(_IN_SCOPE_KEYS))
            for entry in result.values():
                self.assertIsInstance(entry, dict)
                self.assertNotIn("version", entry)
                self.assertNotIn("escalation", entry)
                self.assertNotIn("rules", entry)

    def test_no_network_call_of_its_own(self):
        def _raising_runner(args, check=True):
            raise OSError("gh: command not found")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root)
            _write_policy(root, _POLICY_AT_BASELINE)

            result = review_agent_policy(root, runner=_raising_runner)

            self.assertEqual(set(result), set(_IN_SCOPE_KEYS))
            self.assertFalse(result["budgets.max_open_prs"]["proposal"]["available"])

    def test_absent_policy_file_classifies_all_keys_absent_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_example(root)
            # No .specfuse/agent-policy.yml written at all.

            result = review_agent_policy(root)

            for key in _IN_SCOPE_KEYS:
                self.assertEqual(result[key]["classification"], "absent_from_file")
                self.assertFalse(result[key]["current"]["present"])


if __name__ == "__main__":
    unittest.main()
