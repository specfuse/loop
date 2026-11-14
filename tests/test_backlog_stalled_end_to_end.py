# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""End-to-end oracle for the `backlog-stalled` check type (#3576): a config
that lints clean dispatches through `run_cycle` to the App Insights adapter
and files one finding per stalled backlog."""

from __future__ import annotations

import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import specfuse.monitor.cli as cli
from specfuse.loop.lint_monitoring import validate_monitoring

_NOW = datetime(2026, 11, 14, 12, 0, 0, tzinfo=timezone.utc)

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
    "  - name: acme-orders\n"
    "    type: http-service\n"
    "    runner: local\n"
    "    diagnose: manual\n"
    "    autofix: \"off\"\n"
    "    checks:\n"
    "      - type: backlog-stalled\n"
    "        targets:\n"
    "          - name: acme-event-outbox\n"
    "            stall_after: 15m\n"
    "            silent_after: 30m\n"
    "          - name: acme-notification-jobs\n"
    "            stall_after: 1h\n"
)


class _RecordingTransport:
    def __init__(self, rows):
        self._rows = rows
        self.queries: list[str] = []

    def run_query(self, query):
        self.queries.append(query)
        return list(self._rows)


class BacklogStalledEndToEnd(unittest.TestCase):
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

    def test_config_lints_clean(self):
        self.assertEqual(validate_monitoring(self.config_path), [])

    def test_one_stalled_backlog_files_one_finding(self):
        rows = [
            {"name": "acme-event-outbox", "last_snapshot": "2026-11-14T11:59:00Z",
             "oldest_pending_age_seconds": 2400, "pending_count": 57},
            {"name": "acme-notification-jobs", "last_snapshot": "2026-11-14T11:59:00Z",
             "oldest_pending_age_seconds": 30, "pending_count": 2},
        ]
        text, transport = self._cycle(rows)
        lines = [ln for ln in text.splitlines() if "would file:" in ln]
        self.assertEqual(len(lines), 1, text)
        self.assertIn("check_type=backlog-stalled", lines[0])
        self.assertIn("failure_class=stalled-backlog", lines[0])
        self.assertEqual(len(transport.queries), 1)

    def test_healthy_backlogs_file_nothing(self):
        rows = [
            {"name": "acme-event-outbox", "last_snapshot": "2026-11-14T11:59:00Z",
             "oldest_pending_age_seconds": 0, "pending_count": 0},
            {"name": "acme-notification-jobs", "last_snapshot": "2026-11-14T11:59:00Z",
             "oldest_pending_age_seconds": 0},
        ]
        text, _ = self._cycle(rows)
        self.assertNotIn("would file:", text)


if __name__ == "__main__":
    unittest.main()
