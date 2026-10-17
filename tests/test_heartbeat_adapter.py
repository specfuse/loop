# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the heartbeat adapter (FEAT-2026-0040/T07).

Fixture note: every ``targets`` dict literal below carries a ``cron`` key
paired with a conforming ``dialect`` — the tree-wide sweep in
``test_monitoring_cron_dialect.py`` walks every Python dict literal in the
tracked tree for exactly this shape, so a silent-schedule fixture here that
disagreed on dialect/arity would fail that sweep, not just this file.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import datetime, timezone

from specfuse.monitor.adapters import TelemetryAdapter
from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.providers.azure_app_insights import HeartbeatAdapter

_ENVIRONMENT = {"telemetry": {"provider": "app-insights"}}
# 10:15, not on the hour, so hourly-cache-warm's most recent expected firing
# (10:00:00) is unambiguously before the reference rather than coinciding
# with it.
_REFERENCE = datetime(2026, 7, 28, 10, 15, 0, tzinfo=timezone.utc)


@dataclass
class StubTransport:
    """Returns a canned row set regardless of the query text, and records
    every query it was asked to run."""

    rows: list
    queries: list = field(default_factory=list)

    def run_query(self, query):
        self.queries.append(query)
        return list(self.rows)


def _two_target_fixture():
    """At least 2 heartbeat targets on one component with different
    dialects (criterion 8): one reported in within its window, one has
    not."""
    return [
        {
            "name": "nightly-reconciliation",
            "cron": "0 2 * * *",
            "dialect": "standard-5",
            "timezone": "Etc/UTC",
        },
        {
            "name": "hourly-cache-warm",
            "cron": "0 0 * * * *",
            "dialect": "seconds-first-6",
            "timezone": "Etc/UTC",
        },
    ]


class TestHeartbeatAdapter(unittest.TestCase):
    def test_only_silent_schedule_yields_an_artifact(self):
        # nightly-reconciliation last reported two days before its most
        # recent expected 02:00 fire (silent); hourly-cache-warm reported in
        # exactly at its most recent expected 10:00:00 fire (not silent).
        rows = [
            {"name": "nightly-reconciliation", "last_heartbeat": "2026-07-26T02:00:00Z"},
            {"name": "hourly-cache-warm", "last_heartbeat": "2026-07-28T10:00:00Z"},
        ]
        adapter = HeartbeatAdapter(
            component="acme-functions-host",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows=rows),
            targets=_two_target_fixture(),
            reference_time=_REFERENCE,
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(
            artifacts[0].target_coordinates["name"], "nightly-reconciliation"
        )

    def test_no_artifact_when_last_heartbeat_at_or_after_expected_firing(self):
        # Both targets reported in at/after their most recent expected
        # firing — the false-positive direction (criterion 9).
        rows = [
            {"name": "nightly-reconciliation", "last_heartbeat": "2026-07-28T02:00:00Z"},
            {"name": "hourly-cache-warm", "last_heartbeat": "2026-07-28T10:00:00Z"},
        ]
        adapter = HeartbeatAdapter(
            component="acme-functions-host",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows=rows),
            targets=_two_target_fixture(),
            reference_time=_REFERENCE,
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(artifacts, [])

    def test_distinct_silent_targets_on_one_component_yield_distinct_fingerprints(self):
        # Both targets now silent (the component emitted, but neither of
        # these schedules did since before their expected firings).
        rows = [{"name": "other-schedule", "last_heartbeat": "2026-07-01T00:00:00Z"}]
        adapter = HeartbeatAdapter(
            component="acme-functions-host",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows=rows),
            targets=_two_target_fixture(),
            reference_time=_REFERENCE,
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 2)
        digests = {fingerprint_artifact(a) for a in artifacts}
        self.assertEqual(len(digests), 2)

    def test_adapter_satisfies_telemetry_adapter_protocol(self):
        adapter = HeartbeatAdapter(
            component="c",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows=[]),
            targets=[],
            reference_time=_REFERENCE,
        )
        self.assertTrue(hasattr(adapter, "fetch_failures"))
        self.assertTrue(callable(adapter.fetch_failures))
        self.assertTrue(callable(TelemetryAdapter.fetch_failures))
        self.assertEqual(list(adapter.fetch_failures()), [])

    def test_resolve_telemetry_is_called_with_the_component(self):
        from unittest import mock

        from specfuse.monitor.providers import azure_app_insights as aai

        with mock.patch.object(
            aai, "resolve_telemetry", wraps=aai.resolve_telemetry
        ) as spy:
            HeartbeatAdapter(
                component="acme-functions-host",
                environment=_ENVIRONMENT,
                transport=StubTransport(rows=[]),
                targets=[],
                reference_time=_REFERENCE,
            )
            spy.assert_called_once_with("acme-functions-host", _ENVIRONMENT)

    def test_row_with_no_last_heartbeat_value_is_treated_as_silent(self):
        rows = [
            {"name": "nightly-reconciliation", "last_heartbeat": None},
            {"name": "other-schedule", "last_heartbeat": "2026-07-01T00:00:00Z"},
        ]
        adapter = HeartbeatAdapter(
            component="acme-functions-host",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows=rows),
            targets=[_two_target_fixture()[0]],
            reference_time=_REFERENCE,
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 1)

    def test_cron_less_target_is_skipped_without_error(self):
        targets = [{"name": "no-schedule-declared"}]
        adapter = HeartbeatAdapter(
            component="c",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows=[]),
            targets=targets,
            reference_time=_REFERENCE,
        )
        self.assertEqual(list(adapter.fetch_failures()), [])

    def test_planted_secret_is_redacted_at_the_boundary(self):
        planted_secret = "hb-fixture-example-token-not-a-real-credential-000111"
        targets = [
            {
                "name": f"schedule-token={planted_secret}",
                "cron": "0 2 * * *",
                "dialect": "standard-5",
                "timezone": "Etc/UTC",
            }
        ]
        adapter = HeartbeatAdapter(
            component="c",
            environment=_ENVIRONMENT,
            transport=StubTransport(
                rows=[{"name": "other", "last_heartbeat": "2026-07-01T00:00:00Z"}]
            ),
            targets=targets,
            reference_time=_REFERENCE,
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 1)
        observed_text = artifacts[0].observed_text
        self.assertNotIn(planted_secret, observed_text)
        self.assertIn("<redacted:", observed_text)


class TestHeartbeatGrace(unittest.TestCase):
    _WEEKLY = {
        "name": "weekly-job",
        "cron": "0 8 * * 1",
        "dialect": "standard-5",
        "timezone": "Etc/UTC",
    }

    def _run(self, rows, reference):
        transport = StubTransport(rows=rows)
        adapter = HeartbeatAdapter(
            component="acme-functions-host",
            environment=_ENVIRONMENT,
            transport=transport,
            targets=[self._WEEKLY],
            reference_time=reference,
        )
        return list(adapter.fetch_failures()), transport

    def test_firing_before_first_heartbeat_is_not_evaluated(self):
        rows = [{
            "name": "other-schedule",
            "last_heartbeat": "2026-10-16T09:00:00Z",
            "first_heartbeat": "2026-10-14T13:50:00Z",
        }]
        artifacts, transport = self._run(
            rows, datetime(2026, 10, 17, 1, 0, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(artifacts, [])
        self.assertEqual(len(transport.queries), 1)

    def test_missed_firing_after_emission_still_fires(self):
        target = dict(self._WEEKLY, cron="0 8 * * *")
        rows = [{
            "name": "weekly-job",
            "last_heartbeat": "2026-10-14T08:00:00Z",
            "first_heartbeat": "2026-10-14T08:00:00Z",
        }]
        adapter = HeartbeatAdapter(
            component="acme-functions-host",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows=rows),
            targets=[target],
            reference_time=datetime(2026, 10, 15, 9, 0, 0, tzinfo=timezone.utc),
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].failure_class, "silent-schedule")
        self.assertIn("2026-10-15T08:00:00", artifacts[0].observed_text)
        self.assertIn("last observed heartbeat 2026-10-14T08:00:00", artifacts[0].observed_text)

    def test_component_without_any_heartbeat_files_nothing(self):
        artifacts, transport = self._run(
            [], datetime(2026, 10, 17, 1, 0, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(artifacts, [])
        self.assertEqual(len(transport.queries), 1)


if __name__ == "__main__":
    unittest.main()
