# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""End-to-end oracle for the `http-status-regression` check type
(FEAT-2026-0203 gate 1, T01 walking skeleton)."""

from __future__ import annotations

import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import specfuse.monitor.cli as cli
from specfuse.loop.lint_monitoring import validate_monitoring
from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.providers.azure_app_insights import HttpStatusRegressionAdapter

_NOW = datetime(2026, 10, 14, 10, 0, 0, tzinfo=timezone.utc)

_CONFIG_YAML = (
    "environments:\n"
    "  production:\n"
    "    telemetry:\n"
    "      provider: azure_app_insights\n"
    "      credentials:\n"
    "        api_key: ACME_API_KEY\n"
    "    broker:\n"
    "      provider: azure_service_bus\n"
    "      credentials:\n"
    "        connection_string: ACME_CONN\n"
    "components:\n"
    "  - name: order-api\n"
    "    type: http-service\n"
    "    runner: local\n"
    "    diagnose: manual\n"
    "    autofix: \"off\"\n"
    "    checks:\n"
    "      - type: http-status-regression\n"
    "        deploy_signal:\n"
    "          kind: app-version\n"
    "        window_after_deploy: 1h\n"
    "        codes:\n"
    "          - 401\n"
)


def _row(version="2026.10.1", code="401", before=1, after=40):
    return {
        "version": version,
        "code": code,
        "first_seen": "2026-10-14T07:00:00Z",
        "before": before,
        "after": after,
        "before_total": 100,
        "after_total": 100,
    }


class _RecordingTransport:
    def __init__(self, rows):
        self._rows = rows
        self.queries: list[str] = []

    def run_query(self, query):
        self.queries.append(query)
        return list(self._rows)


class HttpStatusRegressionEndToEnd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.config_path = self.tmp / "monitoring.yml"
        self.config_path.write_text(_CONFIG_YAML, encoding="utf-8")

    def _cycle(self, rows):
        transport = _RecordingTransport(rows)
        out = io.StringIO()
        config = cli.load_monitoring_config(self.config_path)
        cli.run_cycle(
            config,
            dry_run=True,
            transport_resolver=lambda module, check_type, binding: transport,
            now=_NOW,
            watermark_dir=self.tmp,
            out=out,
        )
        return out.getvalue(), transport

    def _artifacts(self, rows):
        transport = _RecordingTransport(rows)
        adapter = HttpStatusRegressionAdapter(
            component="order-api",
            environment={"telemetry": {"provider": "azure_app_insights"}},
            transport=transport,
            deploy_signal="deployment-marker",
            window_after_deploy="1h",
            codes=["401"],
        )
        return list(adapter.fetch_failures()), transport

    def test_one_deployment_files_one_finding_per_code(self):
        self.assertEqual(validate_monitoring(self.config_path), [])
        text, _ = self._cycle([_row()])
        lines = [ln for ln in text.splitlines() if "would file:" in ln]
        self.assertEqual(len(lines), 1, text)
        self.assertIn("check_type=http-status-regression", lines[0])
        self.assertIn("401", lines[0])

    def test_same_rows_same_fingerprint(self):
        first, _ = self._artifacts([_row()])
        second, _ = self._artifacts([_row()])
        other, _ = self._artifacts([_row(version="2026.10.2")])
        self.assertEqual(len(first), 1)
        self.assertEqual(fingerprint_artifact(first[0]), fingerprint_artifact(second[0]))
        self.assertNotEqual(fingerprint_artifact(first[0]), fingerprint_artifact(other[0]))

    def test_adapter_issues_one_query(self):
        rows = [_row(version="9.8.7-sentinel", code="401")]
        artifacts, transport = self._artifacts(rows)
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(len(transport.queries), 1)
        for value in ("9.8.7-sentinel",):
            self.assertNotIn(value, transport.queries[0])


if __name__ == "__main__":
    unittest.main()
