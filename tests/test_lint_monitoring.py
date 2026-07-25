#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.lint_monitoring."""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from specfuse.loop.lint_monitoring import main, validate_monitoring

VALID_CONFIG = """\
environments:
  staging:
    telemetry:
      provider: acme-telemetry
    broker:
      provider: acme-broker
      credentials:
        api_key: BROKER_API_KEY
components:
  - name: web
    type: service
    runner: local
    diagnose: manual
    autofix: "off"
    checks:
      - type: heartbeat
      - type: dlq
        harvest_mode: peek
      - type: invariant
        query: "select count(*) from orders"
        fingerprint_by: order_id
"""


def _config_with_components(defect_index: int, defect_field: str) -> str:
    lines = ["environments:", "  staging:", "    telemetry:",
             "      provider: acme-telemetry", "    broker:",
             "      provider: acme-broker", "components:"]
    for i in range(12):
        name = f"svc-{i:02d}"
        lines.append(f"  - name: {name}")
        fields = {
            "type": "service",
            "runner": "local",
            "diagnose": "manual",
            "autofix": '"off"',
        }
        for field, value in fields.items():
            if i == defect_index and field == defect_field:
                continue
            lines.append(f"    {field}: {value}")
        if not (i == defect_index and defect_field == "checks"):
            lines.append("    checks:")
            lines.append("      - type: heartbeat")
    return "\n".join(lines) + "\n"


class LintMonitoringTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = Path(self._tmpdir.name)

    def _write(self, text: str) -> Path:
        p = self.tmp_path / "monitoring.yml"
        p.write_text(text)
        return p

    def test_valid_config_reports_no_findings(self):
        p = self._write(VALID_CONFIG)
        self.assertEqual(validate_monitoring(p), [])

    def test_unknown_check_type_is_rejected(self):
        bad = VALID_CONFIG.replace("type: heartbeat", "type: mystery-check")
        p = self._write(bad)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("mystery-check", findings[0])

    def test_absent_file_returns_no_findings(self):
        missing = self.tmp_path / "does-not-exist.yml"
        self.assertFalse(missing.exists())
        self.assertEqual(validate_monitoring(missing), [])

    def test_absent_file_cli_exits_zero(self):
        missing = self.tmp_path / "does-not-exist.yml"
        result = subprocess.run(
            [sys.executable, "-m", "specfuse.loop.lint_monitoring", str(missing)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_parse_failure_is_distinguishable_from_valid(self):
        p = self._write("environments:\n  staging: 'single-quoted-unsupported'\n")
        findings = validate_monitoring(p)
        self.assertNotEqual(findings, [])

    def test_unknown_runner_dial_value(self):
        bad = VALID_CONFIG.replace("runner: local", "runner: quantum-cloud")
        p = self._write(bad)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("runner", findings[0])
        self.assertIn("quantum-cloud", findings[0])

    def test_unknown_diagnose_dial_value(self):
        bad = VALID_CONFIG.replace("diagnose: manual", "diagnose: telepathic")
        p = self._write(bad)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("diagnose", findings[0])
        self.assertIn("telepathic", findings[0])

    def test_unknown_autofix_dial_value(self):
        bad = VALID_CONFIG.replace('autofix: "off"', "autofix: sometimes")
        p = self._write(bad)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("autofix", findings[0])
        self.assertIn("sometimes", findings[0])

    def test_missing_required_field_names_component_not_just_index(self):
        text = _config_with_components(defect_index=11, defect_field="type")
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("svc-11", findings[0])
        self.assertIn("type", findings[0])

    def test_inline_credential_is_rejected(self):
        bad = VALID_CONFIG.replace(
            "api_key: BROKER_API_KEY",
            'api_key: "Endpoint=sb://fake-namespace.servicebus.windows.net/;'
            'SharedAccessKey=NOTAREALKEY000=="',
        )
        p = self._write(bad)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("api_key", findings[0])

    def test_env_var_name_credential_is_accepted(self):
        p = self._write(VALID_CONFIG)
        self.assertEqual(validate_monitoring(p), [])

    def test_findings_are_deterministically_ordered(self):
        bad = VALID_CONFIG.replace("runner: local", "runner: quantum-cloud")
        p = self._write(bad)
        first = validate_monitoring(p)
        second = validate_monitoring(p)
        self.assertEqual(first, second)

    def test_missing_top_level_keys(self):
        p = self._write("foo: bar\n")
        findings = validate_monitoring(p)
        self.assertTrue(any("environments" in f for f in findings))
        self.assertTrue(any("components" in f for f in findings))

    def test_missing_provider_binding(self):
        text = (
            "environments:\n"
            "  staging:\n"
            "    telemetry:\n"
            "      provider: acme-telemetry\n"
            "components: []\n"
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertTrue(any("broker" in f for f in findings))

    def test_top_level_not_a_mapping(self):
        p = self._write("- 1\n- 2\n")
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("top level", findings[0])

    def test_environments_not_a_mapping(self):
        p = self._write("environments: nope\ncomponents: []\n")
        findings = validate_monitoring(p)
        self.assertTrue(any("'environments' must be a mapping" in f for f in findings))

    def test_environment_body_not_a_mapping(self):
        p = self._write("environments:\n  staging: nope\ncomponents: []\n")
        findings = validate_monitoring(p)
        self.assertTrue(any("environment 'staging': must be a mapping" in f for f in findings))

    def test_provider_binding_not_a_mapping(self):
        text = (
            "environments:\n"
            "  staging:\n"
            "    telemetry: nope\n"
            "    broker:\n"
            "      provider: acme-broker\n"
            "components: []\n"
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertTrue(any("telemetry" in f and "provider" in f for f in findings))

    def test_credential_nested_inside_a_list_is_scanned(self):
        text = (
            "environments:\n"
            "  staging:\n"
            "    telemetry:\n"
            "      provider: acme-telemetry\n"
            "    broker:\n"
            "      provider: acme-broker\n"
            "      extra_configs:\n"
            "        - token: not-an-env-var\n"
            "components: []\n"
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertTrue(any("token" in f for f in findings))

    def test_components_not_a_list(self):
        p = self._write("components: nope\n")
        findings = validate_monitoring(p)
        self.assertTrue(any("'components' must be a list" in f for f in findings))

    def test_component_not_a_mapping(self):
        p = self._write("components:\n  - nope\n")
        findings = validate_monitoring(p)
        self.assertTrue(any("component[0]: must be a mapping" in f for f in findings))

    def test_checks_not_a_list(self):
        text = VALID_CONFIG.replace(
            "    checks:\n"
            "      - type: heartbeat\n"
            "      - type: dlq\n"
            "        harvest_mode: peek\n"
            "      - type: invariant\n"
            "        query: \"select count(*) from orders\"\n"
            "        fingerprint_by: order_id\n",
            "    checks: nope\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertTrue(any("'checks' must be a list" in f for f in findings))

    def test_check_not_a_mapping(self):
        text = VALID_CONFIG.replace(
            "    checks:\n"
            "      - type: heartbeat\n"
            "      - type: dlq\n"
            "        harvest_mode: peek\n"
            "      - type: invariant\n"
            "        query: \"select count(*) from orders\"\n"
            "        fingerprint_by: order_id\n",
            "    checks:\n"
            "      - nope\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertTrue(any("checks[0]: must be a mapping" in f for f in findings))

    def test_dlq_check_missing_harvest_mode(self):
        text = VALID_CONFIG.replace(
            "      - type: dlq\n        harvest_mode: peek\n",
            "      - type: dlq\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertTrue(any("harvest_mode" in f for f in findings))

    def test_invariant_check_missing_fields(self):
        text = VALID_CONFIG.replace(
            "      - type: invariant\n"
            "        query: \"select count(*) from orders\"\n"
            "        fingerprint_by: order_id\n",
            "      - type: invariant\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertTrue(any("'query'" in f for f in findings))
        self.assertTrue(any("'fingerprint_by'" in f for f in findings))

    def test_main_reports_findings_and_returns_one(self):
        p = self._write(VALID_CONFIG.replace("type: heartbeat", "type: mystery-check"))
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["lint_monitoring.py", str(p)]):
            with contextlib.redirect_stdout(out):
                rc = main()
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", out.getvalue())

    def test_main_reports_ok_and_returns_zero(self):
        p = self._write(VALID_CONFIG)
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["lint_monitoring.py", str(p)]):
            with contextlib.redirect_stdout(out):
                rc = main()
        self.assertEqual(rc, 0)
        self.assertIn("OK", out.getvalue())

    def test_default_path_used_when_none_given(self):
        cwd = Path.cwd()
        try:
            import os
            os.chdir(self.tmp_path)
            self.assertEqual(validate_monitoring(), [])
        finally:
            import os
            os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
