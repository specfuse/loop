# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the `backlog-stalled` App Insights adapter (#3576).

The component reports its own data-store backlog as `BacklogSnapshot` custom
events; the adapter reads the latest snapshot per backlog name and files:

- a `stalled-backlog` finding when that snapshot's oldest pending item is
  older than the target's `stall_after`;
- a `silent-backlog` finding when the target sets `silent_after` and no
  snapshot for that backlog arrived within it (the reporter died).

`pendingCount` is reported in the finding, never compared against anything.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import datetime, timezone

from specfuse.monitor.adapters import TelemetryAdapter
from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.providers.azure_app_insights import BacklogStalledAdapter

_ENVIRONMENT = {"telemetry": {"provider": "azure_app_insights"}}
_NOW = datetime(2026, 11, 14, 12, 0, 0, tzinfo=timezone.utc)


@dataclass
class StubTransport:
    rows: list
    queries: list = field(default_factory=list)

    def run_query(self, query):
        self.queries.append(query)
        return list(self.rows)


def _row(name="acme-event-outbox", at="2026-11-14T11:58:00Z", age=60, count=3):
    row = {"name": name, "last_snapshot": at, "oldest_pending_age_seconds": age}
    if count is not None:
        row["pending_count"] = count
    return row


def _adapter(rows, targets=None):
    transport = StubTransport(rows=rows)
    adapter = BacklogStalledAdapter(
        component="acme-orders",
        environment=_ENVIRONMENT,
        transport=transport,
        targets=targets
        if targets is not None
        else [{"name": "acme-event-outbox", "stall_after": "15m", "silent_after": "30m"}],
        reference_time=_NOW,
    )
    return adapter, transport


def _artifacts(rows, targets=None):
    adapter, transport = _adapter(rows, targets)
    return list(adapter.fetch_failures()), transport


class TestBacklogStalledAdapter(unittest.TestCase):
    def test_satisfies_the_telemetry_protocol(self):
        adapter, _ = _adapter([])
        self.assertTrue(callable(getattr(adapter, "fetch_failures", None)))
        self.assertTrue(hasattr(TelemetryAdapter, "fetch_failures"))

    def test_moving_backlog_is_quiet(self):
        artifacts, _ = _artifacts([_row(age=14 * 60)])
        self.assertEqual(artifacts, [])

    def test_age_at_threshold_is_quiet(self):
        artifacts, _ = _artifacts([_row(age=15 * 60)])
        self.assertEqual(artifacts, [])

    def test_oldest_item_older_than_stall_after_files_a_stalled_finding(self):
        artifacts, _ = _artifacts([_row(age=42 * 60, count=118)])
        self.assertEqual(len(artifacts), 1)
        artifact = artifacts[0]
        self.assertEqual(artifact.check_type, "backlog-stalled")
        self.assertEqual(artifact.component, "acme-orders")
        self.assertEqual(artifact.failure_class, "stalled-backlog")
        self.assertEqual(artifact.failure_signature, "acme-event-outbox")
        self.assertEqual(dict(artifact.target_coordinates), {"name": "acme-event-outbox"})
        self.assertIn("acme-event-outbox", artifact.observed_text)
        self.assertIn("42m", artifact.observed_text)
        body = artifact.observed_text + " ".join((artifact.context or {}).values())
        self.assertIn("118", body)

    def test_pending_count_is_never_a_threshold(self):
        artifacts, _ = _artifacts([_row(age=0, count=10_000_000)])
        self.assertEqual(artifacts, [])

    def test_missing_pending_count_still_files(self):
        artifacts, _ = _artifacts([_row(age=3600, count=None)])
        self.assertEqual(len(artifacts), 1)

    def test_stall_lasting_many_harvests_keeps_one_fingerprint(self):
        first, _ = _artifacts([_row(age=20 * 60, count=5)])
        later, _ = _artifacts([_row(at="2026-11-14T11:59:00Z", age=7 * 3600, count=900)])
        self.assertEqual(fingerprint_artifact(first[0]), fingerprint_artifact(later[0]))

    def test_distinct_backlogs_have_distinct_fingerprints(self):
        targets = [
            {"name": "acme-event-outbox", "stall_after": "15m"},
            {"name": "acme-notification-jobs", "stall_after": "15m"},
        ]
        artifacts, _ = _artifacts(
            [_row(age=3600), _row(name="acme-notification-jobs", age=3600)], targets
        )
        self.assertEqual(len(artifacts), 2)
        self.assertNotEqual(
            fingerprint_artifact(artifacts[0]), fingerprint_artifact(artifacts[1])
        )

    def test_unconfigured_backlog_is_ignored(self):
        targets = [{"name": "acme-event-outbox", "stall_after": "15m"}]
        artifacts, _ = _artifacts([_row(name="acme-other-table", age=99999)], targets)
        self.assertEqual(artifacts, [])

    def test_silent_reporter_files_a_silent_finding(self):
        artifacts, _ = _artifacts([_row(at="2026-11-14T11:00:00Z", age=0)])
        self.assertEqual(len(artifacts), 1)
        artifact = artifacts[0]
        self.assertEqual(artifact.failure_class, "silent-backlog")
        self.assertEqual(artifact.failure_signature, "acme-event-outbox")
        self.assertIn("2026-11-14T11:00:00Z", artifact.observed_text)

    def test_silent_and_stalled_are_distinct_findings(self):
        artifacts, _ = _artifacts([_row(at="2026-11-14T10:00:00Z", age=3 * 3600)])
        classes = sorted(a.failure_class for a in artifacts)
        self.assertEqual(classes, ["silent-backlog", "stalled-backlog"])
        self.assertNotEqual(
            fingerprint_artifact(artifacts[0]), fingerprint_artifact(artifacts[1])
        )

    def test_stale_snapshot_without_silent_after_is_quiet(self):
        targets = [{"name": "acme-event-outbox", "stall_after": "15m"}]
        artifacts, _ = _artifacts([_row(at="2026-11-01T00:00:00Z", age=0)], targets)
        self.assertEqual(artifacts, [])

    def test_backlog_never_reported_is_silent_when_component_reports_others(self):
        targets = [
            {"name": "acme-event-outbox", "stall_after": "15m", "silent_after": "30m"},
            {"name": "acme-notification-jobs", "stall_after": "15m"},
        ]
        artifacts, _ = _artifacts([_row(name="acme-notification-jobs", age=0)], targets)
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].failure_class, "silent-backlog")
        self.assertIn("never", artifacts[0].observed_text)

    def test_component_with_no_snapshot_at_all_is_pending(self):
        # "Never deployed" and "reporter dead" are indistinguishable when the
        # component has emitted nothing: no finding, as for heartbeat.
        artifacts, _ = _artifacts([])
        self.assertEqual(artifacts, [])

    def test_one_query_built_from_configuration_only(self):
        rows = [_row(name="acme-event-outbox", age=3600, count=424242)]
        _, transport = _artifacts(rows)
        self.assertEqual(len(transport.queries), 1)
        query = transport.queries[0]
        self.assertIn("AppRoleName == 'acme-orders'", query)
        self.assertIn("Name == 'BacklogSnapshot'", query)
        self.assertNotIn("424242", query)
        self.assertNotIn("ingestion_time()", query)


if __name__ == "__main__":
    unittest.main()
