#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.agent_policy."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from specfuse.loop.agent_policy import (
    AUTOMERGE_VALUES,
    GATE_REVIEW_VALUES,
    SEVERITY_VALUES,
    main,
    validate_agent_policy,
)

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / ".specfuse" / "agent-policy.yml.example"

VALID_CONFIG = """\
version: 1
queue:
  - FEAT-2026-0048
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
  webhook: ""
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
"""


def _write(text: str) -> str:
    fd = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    fd.write(text)
    fd.close()
    return fd.name


class TestValidateAgentPolicy(unittest.TestCase):
    def test_shipped_example_validates_clean(self):
        findings = validate_agent_policy(str(EXAMPLE_PATH))
        self.assertEqual(findings, [])

    def test_valid_config_validates_clean(self):
        path = _write(VALID_CONFIG)
        self.assertEqual(validate_agent_policy(path), [])

    def test_missing_file_is_error(self):
        findings = validate_agent_policy("/nonexistent/agent-policy.yml")
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0].startswith("ERROR: "))

    def test_all_findings_have_severity_prefix(self):
        broken = VALID_CONFIG.replace("version: 1", "version: 2") + "extra_key: 1\n"
        findings = validate_agent_policy(_write(broken))
        self.assertTrue(findings)
        for finding in findings:
            self.assertTrue(
                finding.startswith("ERROR: ") or finding.startswith("WARN: "),
                finding,
            )

    def test_empty_queue_produces_zero_findings(self):
        config = VALID_CONFIG.replace("queue:\n  - FEAT-2026-0048\n", "queue: []\n")
        self.assertEqual(validate_agent_policy(_write(config)), [])

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

    _CONFIGS_MISSING_KEY = {
        "version": VALID_CONFIG.replace("version: 1\n", ""),
        "queue": VALID_CONFIG.replace("queue:\n  - FEAT-2026-0048\n", ""),
        "rules": VALID_CONFIG.replace(_RULES_BLOCK, ""),
        "budgets": "".join(
            line + "\n" for line in VALID_CONFIG.splitlines()
            if line not in (
                "budgets:", "  max_tokens_per_run: 2000000",
                "  max_open_prs: 3", "  max_items_per_day: 10",
            )
        ),
        "escalation": "".join(
            line + "\n" for line in VALID_CONFIG.splitlines()
            if line not in (
                "escalation:", '  webhook: ""', '  assignee: ""',
                '  quiet_hours: ""', "  sla_hours: 24",
            )
        ),
    }

    def test_missing_required_top_level_key(self):
        for key, config in self._CONFIGS_MISSING_KEY.items():
            with self.subTest(key=key):
                findings = validate_agent_policy(_write(config))
                matching = [
                    f for f in findings
                    if f == f"ERROR: missing top-level '{key}' key"
                ]
                self.assertEqual(len(matching), 1, findings)

    def test_unknown_top_level_key(self):
        config = VALID_CONFIG + "bogus_key: 1\n"
        findings = validate_agent_policy(_write(config))
        self.assertIn("ERROR: unknown top-level key 'bogus_key'", findings)

    def test_version_not_one(self):
        config = VALID_CONFIG.replace("version: 1", "version: 2")
        findings = validate_agent_policy(_write(config))
        self.assertTrue(any("version" in f and f.startswith("ERROR: ") for f in findings))

    def test_queue_entry_bad_shape(self):
        config = VALID_CONFIG.replace(
            "queue:\n  - FEAT-2026-0048\n", "queue:\n  - not-a-feat-id\n"
        )
        findings = validate_agent_policy(_write(config))
        self.assertTrue(any("not-a-feat-id" in f for f in findings))

    def test_queue_duplicate_entry(self):
        config = VALID_CONFIG.replace(
            "queue:\n  - FEAT-2026-0048\n",
            "queue:\n  - FEAT-2026-0048\n  - FEAT-2026-0048\n",
        )
        findings = validate_agent_policy(_write(config))
        self.assertTrue(
            any("duplicate" in f and "FEAT-2026-0048" in f for f in findings)
        )

    def test_severity_enum_rejects_bad_value(self):
        config = VALID_CONFIG.replace("min_severity: low", "min_severity: extreme")
        findings = validate_agent_policy(_write(config))
        self.assertTrue(
            any(f.startswith("ERROR: ") and "min_severity" in f for f in findings)
        )
        self.assertEqual(SEVERITY_VALUES, frozenset({"low", "medium", "high", "critical"}))

    def test_automerge_enum_rejects_bad_value(self):
        config = VALID_CONFIG.replace('automerge: "off"', 'automerge: maybe')
        findings = validate_agent_policy(_write(config))
        self.assertTrue(
            any(f.startswith("ERROR: ") and "automerge" in f for f in findings)
        )
        self.assertEqual(AUTOMERGE_VALUES, frozenset({"off", "on"}))

    def test_gate_review_enum_rejects_bad_value(self):
        config = VALID_CONFIG.replace("gate_review: human", "gate_review: sometimes")
        findings = validate_agent_policy(_write(config))
        self.assertTrue(
            any(f.startswith("ERROR: ") and "gate_review" in f for f in findings)
        )
        self.assertEqual(GATE_REVIEW_VALUES, frozenset({"human", "auto"}))

    def test_wip_limit_zero_is_error(self):
        config = VALID_CONFIG.replace("wip_limit: 1", "wip_limit: 0")
        findings = validate_agent_policy(_write(config))
        self.assertTrue(any("wip_limit" in f and f.startswith("ERROR: ") for f in findings))

    def test_wip_limit_wrong_type_is_error(self):
        config = VALID_CONFIG.replace("wip_limit: 1", 'wip_limit: "one"')
        findings = validate_agent_policy(_write(config))
        self.assertTrue(any("wip_limit" in f and f.startswith("ERROR: ") for f in findings))

    def test_max_open_prs_negative_is_error(self):
        config = VALID_CONFIG.replace("max_open_prs: 3", "max_open_prs: -1")
        findings = validate_agent_policy(_write(config))
        self.assertTrue(
            any("max_open_prs" in f and f.startswith("ERROR: ") for f in findings)
        )

    def test_sla_hours_zero_is_error(self):
        config = VALID_CONFIG.replace("sla_hours: 24", "sla_hours: 0")
        findings = validate_agent_policy(_write(config))
        self.assertTrue(any("sla_hours" in f and f.startswith("ERROR: ") for f in findings))

    def test_preempt_non_bool_is_error(self):
        config = VALID_CONFIG.replace("preempt: true", 'preempt: "yes"')
        findings = validate_agent_policy(_write(config))
        self.assertTrue(any("preempt" in f and f.startswith("ERROR: ") for f in findings))

    def test_feature_overrides_valid(self):
        config = VALID_CONFIG.replace(
            "wip_limit: 1\n",
            "wip_limit: 1\n    overrides:\n      FEAT-2026-0048: auto\n",
        )
        self.assertEqual(validate_agent_policy(_write(config)), [])

    def test_feature_overrides_bad_key(self):
        config = VALID_CONFIG.replace(
            "wip_limit: 1\n",
            "wip_limit: 1\n    overrides:\n      not-a-feat-id: auto\n",
        )
        findings = validate_agent_policy(_write(config))
        self.assertTrue(any("not-a-feat-id" in f for f in findings))

    def test_feature_overrides_bad_value(self):
        config = VALID_CONFIG.replace(
            "wip_limit: 1\n",
            "wip_limit: 1\n    overrides:\n      FEAT-2026-0048: sometimes\n",
        )
        findings = validate_agent_policy(_write(config))
        self.assertTrue(any("overrides" in f and "sometimes" in f for f in findings))

    def test_main_prints_findings_and_returns_nonzero_on_error(self):
        config = VALID_CONFIG.replace("version: 1", "version: 2")
        path = _write(config)
        buf = io.StringIO()
        with redirect_stdout(buf), mock.patch("sys.argv", ["prog", path]):
            code = main()
        self.assertEqual(code, 1)
        self.assertIn("ERROR: ", buf.getvalue())

    def test_main_returns_zero_on_clean_file(self):
        path = _write(VALID_CONFIG)
        buf = io.StringIO()
        with redirect_stdout(buf), mock.patch("sys.argv", ["prog", path]):
            code = main()
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
