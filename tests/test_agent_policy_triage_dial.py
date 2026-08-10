#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.agent_policy.resolve_triage_auto (FEAT-2026-0044/T03)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop.agent_policy import resolve_triage_auto

VALID_CONFIG_TRUE = """\
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
    auto: true
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

CONFIG_NO_TRIAGE_KEY = """\
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

CONFIG_STRING_TRUE = """\
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
    auto: "true"
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


class TestResolveTriageAuto(unittest.TestCase):
    def test_absent_policy_file_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "agent-policy.yml"
            self.assertFalse(missing.exists())
            self.assertFalse(resolve_triage_auto(missing))

    def test_missing_triage_key_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(CONFIG_NO_TRIAGE_KEY)
            self.assertFalse(resolve_triage_auto(p))

    def test_string_true_does_not_enable_dial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(CONFIG_STRING_TRUE)
            self.assertFalse(resolve_triage_auto(p))

    def test_boolean_true_enables_dial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "agent-policy.yml"
            p.write_text(VALID_CONFIG_TRUE)
            self.assertTrue(resolve_triage_auto(p))


if __name__ == "__main__":
    unittest.main()
