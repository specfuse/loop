# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3480: the App Insights `error-logs` and `http-5xx` checks must read only
the harvest window `run_cycle` computes — from the environment's watermark,
or `now - lookback` without one — not the workspace's whole retention.

The window is bounded on `ingestion_time()`, not `TimeGenerated`: a row
stamped just before the previous run but ingested after it is still picked
up by the next run instead of being skipped forever. `heartbeat` and
`http-status-regression` are deliberately not bounded by it: one needs the
last heartbeat however old, the other compares windows around a deployment.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import specfuse.monitor.cli as cli

_NOW = datetime(2026, 10, 16, 10, 0, 0, 123456, tzinfo=timezone.utc)
_ENVIRONMENT = {
    "telemetry": {"provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}},
}


def _config(checks):
    return {
        "environments": {"production": _ENVIRONMENT},
        "components": [{
            "name": "web-api",
            "type": "api",
            "runner": "local",
            "diagnose": "manual",
            "autofix": "off",
            "checks": checks,
        }],
    }


class _Recorder:
    def __init__(self):
        self.queries: dict[str, str] = {}

    def resolver(self, module, check_type, binding):
        recorder = self

        class _Transport:
            def run_query(self, query):
                recorder.queries[check_type] = query
                return []

        return _Transport()


_BOUNDED = [{"type": "error-logs"}, {"type": "http-5xx"}]


class TestTelemetryQueriesAreBoundedToTheHarvestWindow(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.watermark_dir = Path(self._tmpdir.name)

    def _run(self, checks):
        recorder = _Recorder()
        cli.run_cycle(
            _config(checks),
            dry_run=True,
            transport_resolver=recorder.resolver,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=io.StringIO(),
        )
        return recorder.queries

    def _window(self, since):
        return (
            f"| where ingestion_time() >= datetime({since}) "
            f"and ingestion_time() < datetime(2026-10-16T10:00:00.123456Z)"
        )

    def test_no_watermark_bounds_to_the_lookback(self):
        queries = self._run(_BOUNDED)
        since = "2026-10-15T10:00:00.123456Z"  # _NOW - DEFAULT_LOOKBACK (24h)
        for check_type in ("error-logs", "http-5xx"):
            with self.subTest(check_type=check_type):
                self.assertIn(self._window(since), queries[check_type])

    def test_watermark_bounds_to_the_previous_run(self):
        previous = _NOW - timedelta(minutes=15)
        cli._write_watermark(self.watermark_dir / "production.json", now=previous)
        queries = self._run(_BOUNDED)
        for check_type in ("error-logs", "http-5xx"):
            with self.subTest(check_type=check_type):
                self.assertIn(self._window("2026-10-16T09:45:00.123456Z"), queries[check_type])

    def test_window_filter_follows_the_table_scope(self):
        # Bounded before projection, so the predicate reads the source table.
        query = self._run([{"type": "error-logs"}])["error-logs"]
        self.assertLess(query.index("ingestion_time()"), query.index("| project"))

    def test_heartbeat_and_status_regression_are_not_window_bounded(self):
        queries = self._run([
            {"type": "heartbeat", "targets": [
                {"name": "nightly", "cron": "0 2 * * *", "dialect": "standard-5", "timezone": "Etc/UTC"},
            ]},
            {"type": "http-status-regression", "deploy_signal": {"kind": "app-version"},
             "window_after_deploy": "1h"},
        ])
        for check_type in ("heartbeat", "http-status-regression"):
            with self.subTest(check_type=check_type):
                self.assertNotIn("ingestion_time()", queries[check_type])


class TestBoundedQueriesMatchWorkspaceSchema(unittest.TestCase):
    def test_bounded_queries_use_only_workspace_names(self):
        from specfuse.monitor.providers import azure_app_insights as aai
        from tests.test_app_insights_query_schema_check import schema_violations

        since, until = _NOW - timedelta(hours=1), _NOW
        for build in (aai._error_logs_query, aai._http_5xx_query):
            with self.subTest(build=build.__name__):
                query = build("backend-api", since, until)
                self.assertEqual(schema_violations(query), [], query)


if __name__ == "__main__":
    unittest.main()
