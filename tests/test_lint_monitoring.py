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
        # The fixture is assembled from fragments rather than written as one
        # literal, and the host is a reserved-for-testing domain. Both are
        # deliberate: a contiguous `Endpoint=sb://...;SharedAccessKey=...`
        # string matches gitleaks' Azure connection-string rule on some
        # versions (CI installs whatever apt ships; developers install
        # whatever brew ships), so the repo's own secret scanner flagged this
        # line and failed `leak-scan` in CI while passing locally. Splitting it
        # keeps the value connection-string-*shaped* for the validator — which
        # is the point of the negative case — without carrying a signature that
        # a secret scanner is right to match. See #250.
        secret_shaped = (
            "Endpoint=sb://example.invalid/;" + "SharedAccess" + "Key=NOT-A-REAL-KEY"
        )
        bad = VALID_CONFIG.replace(
            "api_key: BROKER_API_KEY",
            f'api_key: "{secret_shaped}"',
        )
        p = self._write(bad)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("api_key", findings[0])

    def test_env_var_name_credential_is_accepted(self):
        p = self._write(VALID_CONFIG)
        self.assertEqual(validate_monitoring(p), [])

    def test_hierarchical_env_var_name_is_accepted(self):
        """`Section__Key` is the canonical .NET/Spring spelling — see #246.

        Case is preserved and the separator is a double underscore. This is an
        environment-variable NAME, not a value, so the credential check must
        accept it. `UPPER_SNAKE_CASE` is a convention, not a rule; POSIX
        permits lowercase and nothing forbids mixed case.
        """
        for name in (
            "ApplicationInsights__ConnectionString",
            "AzureServiceBus__ConnectionString",
        ):
            with self.subTest(name=name):
                text = VALID_CONFIG.replace("api_key: BROKER_API_KEY",
                                            f"api_key: {name}")
                p = self._write(text)
                self.assertEqual(validate_monitoring(p), [])

    def test_lowercase_env_var_name_is_accepted(self):
        text = VALID_CONFIG.replace("api_key: BROKER_API_KEY",
                                    "api_key: broker_api_key")
        p = self._write(text)
        self.assertEqual(validate_monitoring(p), [])

    def test_credential_finding_names_the_accepted_forms(self):
        """The finding must say what to write, not merely that this is wrong.

        Per #246: the operator's next move after a rejection was a guess,
        because the message named no accepted form.
        """
        bad = VALID_CONFIG.replace("api_key: BROKER_API_KEY",
                                   'api_key: "some value with spaces"')
        p = self._write(bad)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("ACME_API_KEY", findings[0])
        self.assertIn("Section__Key", findings[0])

    def test_value_shaped_credentials_are_still_rejected(self):
        """Widening for `Section__Key` must not admit value-shaped strings.

        Each marker below (whitespace, `=`, `;`, `://`, quotes, commas) is a
        thing a variable NAME cannot contain and an inline literal commonly
        does.
        """
        for value in (
            "has whitespace",
            "KEY=VALUE",
            "a;b",
            "scheme://host/path",
            "trailing-hyphen-not-allowed",
            "dots.are.not.allowed",
            "comma,separated",
        ):
            with self.subTest(value=value):
                bad = VALID_CONFIG.replace("api_key: BROKER_API_KEY",
                                           f'api_key: "{value}"')
                p = self._write(bad)
                findings = validate_monitoring(p)
                self.assertEqual(len(findings), 1, f"{value!r} was accepted")
                self.assertIn("api_key", findings[0])

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


class TestCheckTargets(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = Path(self._tmpdir.name)

    def _write(self, text: str) -> Path:
        p = self.tmp_path / "monitoring.yml"
        p.write_text(text)
        return p

    def test_dlq_target_missing_function_is_rejected(self):
        text = VALID_CONFIG.replace(
            "      - type: dlq\n        harvest_mode: peek\n",
            "      - type: dlq\n"
            "        harvest_mode: peek\n"
            "        targets:\n"
            "          - subscription: orders-sub\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("function", findings[0])

    def test_dlq_target_missing_subscription_is_rejected(self):
        text = VALID_CONFIG.replace(
            "      - type: dlq\n        harvest_mode: peek\n",
            "      - type: dlq\n"
            "        harvest_mode: peek\n"
            "        targets:\n"
            "          - function: ProcessOrder\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("subscription", findings[0])

    def test_dlq_target_with_both_coordinates_validates_clean(self):
        text = VALID_CONFIG.replace(
            "      - type: dlq\n        harvest_mode: peek\n",
            "      - type: dlq\n"
            "        harvest_mode: peek\n"
            "        targets:\n"
            "          - subscription: orders-sub\n"
            "            function: ProcessOrder\n",
        )
        p = self._write(text)
        self.assertEqual(validate_monitoring(p), [])

    def test_heartbeat_target_missing_name_is_rejected(self):
        text = VALID_CONFIG.replace(
            "      - type: heartbeat\n",
            "      - type: heartbeat\n"
            "        targets:\n"
            "          - cron: \"0 * * * *\"\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("name", findings[0])

    def test_heartbeat_target_cron_and_timezone_contents_are_opaque(self):
        text = VALID_CONFIG.replace(
            "      - type: heartbeat\n",
            "      - type: heartbeat\n"
            "        targets:\n"
            "          - name: nightly-sync\n"
            "            cron: \"this is not a cron expression at all\"\n"
            "            timezone: Not/A_Real_Zone\n",
        )
        p = self._write(text)
        self.assertEqual(validate_monitoring(p), [])

    def test_error_logs_check_with_targets_is_rejected(self):
        text = VALID_CONFIG.replace(
            "    checks:\n      - type: heartbeat\n",
            "    checks:\n"
            "      - type: error-logs\n"
            "        targets:\n"
            "          - name: whatever\n"
            "      - type: heartbeat\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("error-logs", findings[0])

    def test_http_5xx_check_with_targets_is_rejected(self):
        text = VALID_CONFIG.replace(
            "    checks:\n      - type: heartbeat\n",
            "    checks:\n"
            "      - type: http-5xx\n"
            "        targets:\n"
            "          - name: whatever\n"
            "      - type: heartbeat\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("http-5xx", findings[0])

    def test_targetless_dlq_check_still_validates_clean(self):
        """T03 flips this; T01 must not — see PLAN.md escalation-predicate section."""
        p = self._write(VALID_CONFIG)
        self.assertEqual(validate_monitoring(p), [])

    def test_targets_not_a_list_is_rejected(self):
        text = VALID_CONFIG.replace(
            "      - type: heartbeat\n",
            "      - type: heartbeat\n        targets: nope\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("targets", findings[0])

    def test_empty_targets_list_is_rejected(self):
        text = VALID_CONFIG.replace(
            "      - type: heartbeat\n",
            "      - type: heartbeat\n        targets: []\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("empty", findings[0])

    def test_target_not_a_mapping_names_check_and_target_index(self):
        text = VALID_CONFIG.replace(
            "      - type: heartbeat\n",
            "      - type: heartbeat\n        targets:\n          - nope\n",
        )
        p = self._write(text)
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("checks[0]", findings[0])
        self.assertIn("targets[0]", findings[0])

    def test_findings_are_deterministically_ordered(self):
        text = VALID_CONFIG.replace(
            "      - type: dlq\n        harvest_mode: peek\n",
            "      - type: dlq\n"
            "        harvest_mode: peek\n"
            "        targets:\n"
            "          - subscription: orders-sub\n",
        )
        p = self._write(text)
        first = validate_monitoring(p)
        second = validate_monitoring(p)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
