# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3564: a timer host can fire a hair before its scheduled instant. A
heartbeat that lands within the early-firing tolerance of the expected firing
counts as that firing; one further before it is still silent."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from specfuse.monitor.providers.azure_app_insights import HeartbeatAdapter

_ENVIRONMENT = {"telemetry": {"provider": "app-insights"}}
# Most recent expected firing of the 5-minute schedule below is 04:00:00.
_REFERENCE = datetime(2026, 11, 3, 4, 2, 0, tzinfo=timezone.utc)
_TARGETS = [
    {
        "name": "five-minute-sweep",
        "cron": "0 */5 * * * *",
        "dialect": "seconds-first-6",
        "timezone": "Etc/UTC",
    }
]


class _Transport:
    def __init__(self, last_heartbeat):
        self._rows = [
            {
                "name": "five-minute-sweep",
                "last_heartbeat": last_heartbeat,
                "first_heartbeat": "2026-11-01T00:00:00Z",
            }
        ]

    def run_query(self, query):
        return list(self._rows)


def _artifacts(last_heartbeat):
    adapter = HeartbeatAdapter(
        component="acme-functions-host",
        environment=_ENVIRONMENT,
        transport=_Transport(last_heartbeat),
        targets=_TARGETS,
        reference_time=_REFERENCE,
    )
    return list(adapter.fetch_failures())


class HeartbeatEarlyFiringTests(unittest.TestCase):
    def test_heartbeat_a_fraction_of_a_second_early_is_not_silent(self):
        # The reported case: under a millisecond before 04:00:00.
        self.assertEqual(_artifacts("2026-11-03T03:59:59.999238Z"), [])

    def test_heartbeat_just_inside_the_tolerance_is_not_silent(self):
        self.assertEqual(_artifacts("2026-11-03T03:59:55Z"), [])

    def test_heartbeat_from_the_previous_firing_is_still_silent(self):
        artifacts = _artifacts("2026-11-03T03:55:00Z")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].failure_class, "silent-schedule")

    def test_heartbeat_just_outside_the_tolerance_is_still_silent(self):
        self.assertEqual(len(_artifacts("2026-11-03T03:59:54Z")), 1)


if __name__ == "__main__":
    unittest.main()
