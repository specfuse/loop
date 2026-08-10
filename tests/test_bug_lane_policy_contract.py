#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the FEAT-2026-0048/T01 policy-schema contract and the bug-lane
dials it adds: resolve_bug_automerge and bug_lane_limits.

The first class asserts every row of PLAN.md's assumed-surfaces table holds
against the shipped specfuse/loop/agent_policy.py — this is the WU's primary
job, not incidental coverage.
"""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import agent_policy
from specfuse.loop.agent_policy import (
    bug_lane_limits,
    load_policy,
    resolve_bug_automerge,
    validate_agent_policy,
)

EXAMPLE_POLICY_PATH = Path(".specfuse/agent-policy.yml.example")
LIVE_POLICY_PATH = Path(".specfuse/agent-policy.yml")

VALID_CONFIG_AUTOMERGE_ON = """\
version: 1
queue: []
rules:
  bugs:
    preempt: true
    min_severity: low
    automerge: "on"
  features:
    gate_review: human
    wip_limit: 1
budgets:
  max_tokens_per_run: 2000000
  max_open_prs: 3
  max_items_per_day: 10
escalation:
  webhook_env: ""
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
"""

VALID_CONFIG_AUTOMERGE_OFF = VALID_CONFIG_AUTOMERGE_ON.replace(
    'automerge: "on"', 'automerge: "off"'
)

CONFIG_AUTOMERGE_BOOL_TRUE = """\
version: 1
queue: []
rules:
  bugs:
    preempt: true
    min_severity: low
    automerge: true
  features:
    gate_review: human
    wip_limit: 1
budgets:
  max_tokens_per_run: 2000000
  max_open_prs: 3
  max_items_per_day: 10
escalation:
  webhook_env: ""
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
"""

CONFIG_NO_BUGS_KEY = """\
version: 1
queue: []
rules:
  features:
    gate_review: human
    wip_limit: 1
budgets:
  max_tokens_per_run: 2000000
  max_open_prs: 3
  max_items_per_day: 10
escalation:
  webhook_env: ""
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
"""


def _config_with_limits(max_diff_lines=None, max_merges_per_day=None) -> str:
    extra = ""
    if max_diff_lines is not None:
        extra += f"    max_diff_lines: {max_diff_lines!r}\n"
    if max_merges_per_day is not None:
        extra += f"    max_merges_per_day: {max_merges_per_day!r}\n"
    return f"""\
version: 1
queue: []
rules:
  bugs:
    preempt: true
    min_severity: low
    automerge: "off"
{extra}  features:
    gate_review: human
    wip_limit: 1
budgets:
  max_tokens_per_run: 2000000
  max_open_prs: 3
  max_items_per_day: 10
escalation:
  webhook_env: ""
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
"""


class TestAssumedSurfaces(unittest.TestCase):
    """PLAN.md's § 'The dependency that makes T01 exist' table, verbatim."""

    def test_module_exists(self) -> None:
        self.assertTrue(
            Path(agent_policy.__file__).is_file(),
            "specfuse/loop/agent_policy.py must exist",
        )

    def test_load_policy_signature(self) -> None:
        sig = inspect.signature(load_policy)
        params = list(sig.parameters.values())
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0].name, "path")
        self.assertIsNone(params[0].default)

    def test_load_policy_returns_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(VALID_CONFIG_AUTOMERGE_OFF)
            self.assertIsInstance(load_policy(p), dict)

    def test_validate_agent_policy_signature(self) -> None:
        sig = inspect.signature(validate_agent_policy)
        params = list(sig.parameters.values())
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0].name, "path")
        self.assertIsNone(params[0].default)

    def test_validate_agent_policy_findings_are_prefixed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(CONFIG_NO_BUGS_KEY)
            findings = validate_agent_policy(p)
            self.assertTrue(findings)
            for finding in findings:
                self.assertTrue(
                    finding.startswith("ERROR: ") or finding.startswith("WARN: "),
                    finding,
                )

    def test_example_policy_declares_bugs_automerge(self) -> None:
        text = EXAMPLE_POLICY_PATH.read_text()
        self.assertIn("automerge:", text)

    def test_example_policy_declares_bugs_min_severity(self) -> None:
        text = EXAMPLE_POLICY_PATH.read_text()
        self.assertIn("min_severity:", text)

    def test_example_policy_declares_bugs_preempt(self) -> None:
        text = EXAMPLE_POLICY_PATH.read_text()
        self.assertIn("preempt:", text)

    def test_example_policy_bugs_block_parses_documented_shape(self) -> None:
        policy = load_policy(EXAMPLE_POLICY_PATH)
        bugs = policy["rules"]["bugs"]
        self.assertIn(bugs["automerge"], agent_policy.AUTOMERGE_VALUES)
        self.assertIn(bugs["min_severity"], agent_policy.SEVERITY_VALUES)
        self.assertIsInstance(bugs["preempt"], bool)


class TestPolicyContract(unittest.TestCase):
    def test_resolve_bug_automerge_defaults_off(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "agent-policy.yml"
            self.assertFalse(missing.exists())
            self.assertFalse(resolve_bug_automerge(missing))

    def test_missing_bugs_key_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(CONFIG_NO_BUGS_KEY)
            self.assertFalse(resolve_bug_automerge(p))

    def test_boolean_true_does_not_enable_dial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(CONFIG_AUTOMERGE_BOOL_TRUE)
            self.assertFalse(resolve_bug_automerge(p))

    def test_string_on_enables_dial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(VALID_CONFIG_AUTOMERGE_ON)
            self.assertTrue(resolve_bug_automerge(p))

    def test_string_off_does_not_enable_dial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(VALID_CONFIG_AUTOMERGE_OFF)
            self.assertFalse(resolve_bug_automerge(p))


class TestBugLaneLimits(unittest.TestCase):
    def test_defaults_when_file_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "agent-policy.yml"
            self.assertEqual(
                bug_lane_limits(missing),
                {"max_diff_lines": 150, "max_merges_per_day": 3,
                 "test_paths": ["tests/"]},
            )

    def test_defaults_when_keys_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(VALID_CONFIG_AUTOMERGE_OFF)
            self.assertEqual(
                bug_lane_limits(p),
                {"max_diff_lines": 150, "max_merges_per_day": 3,
                 "test_paths": ["tests/"]},
            )

    def test_explicit_values_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(_config_with_limits(max_diff_lines=75, max_merges_per_day=5))
            self.assertEqual(
                bug_lane_limits(p),
                {"max_diff_lines": 75, "max_merges_per_day": 5,
                 "test_paths": ["tests/"]},
            )


class TestBugLaneLimitsValidation(unittest.TestCase):
    def test_zero_max_diff_lines_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(_config_with_limits(max_diff_lines=0))
            findings = validate_agent_policy(p)
            self.assertTrue(
                any(
                    "max_diff_lines" in f and f.startswith("ERROR: ")
                    for f in findings
                ),
                findings,
            )

    def test_negative_max_merges_per_day_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(_config_with_limits(max_merges_per_day=-1))
            findings = validate_agent_policy(p)
            self.assertTrue(
                any(
                    "max_merges_per_day" in f and f.startswith("ERROR: ")
                    for f in findings
                ),
                findings,
            )

    def test_string_max_diff_lines_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            text = _config_with_limits().replace(
                'automerge: "off"\n',
                'automerge: "off"\n    max_diff_lines: "big"\n',
            )
            p.write_text(text)
            findings = validate_agent_policy(p)
            self.assertTrue(
                any(
                    "max_diff_lines" in f and f.startswith("ERROR: ")
                    for f in findings
                ),
                findings,
            )


class TestExamplePolicyClean(unittest.TestCase):
    def test_example_policy_has_no_findings(self) -> None:
        self.assertEqual(validate_agent_policy(EXAMPLE_POLICY_PATH), [])


class TestLivePolicyAutomergeOff(unittest.TestCase):
    def test_live_policy_automerge_stays_off(self) -> None:
        self.assertFalse(resolve_bug_automerge(LIVE_POLICY_PATH))


if __name__ == "__main__":
    unittest.main()
