# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0040/T01: the neutral FailureArtifact model and the
TelemetryAdapter/BrokerAdapter protocol seam."""

from __future__ import annotations

import typing
import unittest
from unittest import mock

from specfuse.monitor import adapters
from specfuse.monitor.artifact import FailureArtifact


class TestArtifactModel(unittest.TestCase):
    def test_artifact_carries_target_coordinates(self):
        artifact = FailureArtifact(
            component="orders-worker",
            check_type="dlq",
            failure_class="dead-letter",
            failure_signature="orders.created.dlq",
            observed_text="message moved to dead-letter queue",
            target_coordinates={
                "subscription": "orders-created-sub",
                "function": "process-order",
            },
        )
        self.assertEqual(
            artifact.target_coordinates["subscription"], "orders-created-sub"
        )
        self.assertEqual(artifact.target_coordinates["function"], "process-order")

    def test_from_target_round_trips_dlq_coordinates(self):
        artifact = FailureArtifact.from_target(
            component="orders-worker",
            check_type="dlq",
            target={"subscription": "orders-created-sub", "function": "process-order"},
            failure_class="dead-letter",
            failure_signature="orders.created.dlq",
            observed_text="message moved to dead-letter queue",
        )
        self.assertEqual(
            dict(artifact.target_coordinates),
            {"subscription": "orders-created-sub", "function": "process-order"},
        )

    def test_from_target_round_trips_heartbeat_coordinates(self):
        artifact = FailureArtifact.from_target(
            component="orders-worker",
            check_type="heartbeat",
            target={"name": "orders-worker-heartbeat"},
            failure_class="missed-heartbeat",
            failure_signature="orders-worker-heartbeat",
            observed_text="no heartbeat observed in window",
        )
        self.assertEqual(
            dict(artifact.target_coordinates), {"name": "orders-worker-heartbeat"}
        )

    def test_invariant_artifact_carries_no_target_coordinates(self):
        artifact = FailureArtifact(
            component="orders-worker",
            check_type="invariant",
            failure_class="invariant-violation",
            failure_signature="orders.pending-count",
            observed_text="pending count exceeded threshold",
        )
        self.assertIsNone(artifact.target_coordinates)

    def test_from_target_rejects_targetless_check_type(self):
        with self.assertRaises(ValueError):
            FailureArtifact.from_target(
                component="orders-worker",
                check_type="invariant",
                target={"name": "irrelevant"},
                failure_class="invariant-violation",
                failure_signature="orders.pending-count",
                observed_text="pending count exceeded threshold",
            )

    def test_adapter_protocols_declare_failure_artifact_return_type(self):
        for adapter_cls in (adapters.TelemetryAdapter, adapters.BrokerAdapter):
            hints = typing.get_type_hints(adapter_cls.fetch_failures)
            self.assertIn("return", hints)
            self.assertIn("FailureArtifact", repr(hints["return"]))

    def test_resolve_telemetry_reads_environment_binding(self):
        environment = {
            "telemetry": {"provider": "acme-telemetry"},
            "broker": {"provider": "acme-broker"},
        }
        self.assertEqual(
            adapters.resolve_telemetry("orders-worker", environment),
            {"provider": "acme-telemetry"},
        )

    def test_resolve_telemetry_receives_component(self):
        original = adapters.resolve_telemetry
        environment = {"telemetry": {"provider": "acme-telemetry"}}
        with mock.patch.object(
            adapters, "resolve_telemetry", side_effect=original
        ) as spy:
            adapters.resolve_telemetry("orders-worker", environment)
        spy.assert_called_once_with("orders-worker", environment)


if __name__ == "__main__":
    unittest.main()
