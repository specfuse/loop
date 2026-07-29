# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the Service Bus queue-stalled adapter (FEAT-2026-0040/T08)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from specfuse.monitor.adapters import BrokerAdapter
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.providers.azure_service_bus import (
    QueueStalledAdapter,
    parse_stall_after_seconds,
)

_FORBIDDEN_OPERATIONS = frozenset(
    {
        "receive",
        "complete",
        "abandon",
        "dead_letter",
        "defer",
        "renew_lock",
        "peek",
    }
)

_NOW = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)


@dataclass
class StubQueueStalledTransport:
    """Records every method invoked so a test can assert, negatively, that
    only metadata-read operations were ever called (criterion 9)."""

    active_counts: dict
    oldest_enqueued_times: dict
    calls: list = field(default_factory=list)

    def get_active_message_count(self, *, subscription):
        self.calls.append(("get_active_message_count", subscription))
        return self.active_counts.get(subscription, 0)

    def get_oldest_message_enqueued_time(self, *, subscription):
        self.calls.append(("get_oldest_message_enqueued_time", subscription))
        return self.oldest_enqueued_times.get(subscription)

    # Operations a real Service Bus receiver/management client exposes.
    # Present only so a test can assert the adapter never reaches for them.
    def receive(self, *args, **kwargs):
        self.calls.append(("receive", None))
        raise AssertionError("adapter must never call receive()")

    def complete(self, *args, **kwargs):
        self.calls.append(("complete", None))
        raise AssertionError("adapter must never call complete()")

    def abandon(self, *args, **kwargs):
        self.calls.append(("abandon", None))
        raise AssertionError("adapter must never call abandon()")

    def dead_letter(self, *args, **kwargs):
        self.calls.append(("dead_letter", None))
        raise AssertionError("adapter must never call dead_letter()")

    def defer(self, *args, **kwargs):
        self.calls.append(("defer", None))
        raise AssertionError("adapter must never call defer()")

    def renew_lock(self, *args, **kwargs):
        self.calls.append(("renew_lock", None))
        raise AssertionError("adapter must never call renew_lock()")

    def peek(self, *args, **kwargs):
        self.calls.append(("peek", None))
        raise AssertionError("adapter must never call peek()")


def _two_subscription_targets():
    """At least 2 subscriptions, at least one stalled and one not
    (criterion 5)."""
    return [
        {
            "subscription": "orders-created-sub",
            "function": "ProcessOrderCreated",
            "stall_after": "15m",
        },
        {
            "subscription": "orders-cancelled-sub",
            "function": "ProcessOrderCancelled",
            "stall_after": "15m",
        },
    ]


def _adapter_for(targets, active_counts, oldest_enqueued_times, reference=_NOW):
    transport = StubQueueStalledTransport(active_counts, oldest_enqueued_times)
    adapter = QueueStalledAdapter(
        component="order-worker",
        transport=transport,
        targets=targets,
        reference=reference,
    )
    return adapter, transport


class TestQueueStalledAdapter(unittest.TestCase):
    def test_distinct_subscriptions_yield_distinct_fingerprints(self):
        targets = _two_subscription_targets()
        active_counts = {"orders-created-sub": 40, "orders-cancelled-sub": 12}
        oldest_enqueued_times = {
            "orders-created-sub": _NOW - timedelta(minutes=30),
            "orders-cancelled-sub": _NOW - timedelta(minutes=45),
        }
        adapter, _ = _adapter_for(targets, active_counts, oldest_enqueued_times)
        artifacts = list(adapter.fetch_failures())

        self.assertEqual(len(artifacts), 2)
        first, second = artifacts
        self.assertNotEqual(
            first.target_coordinates["subscription"],
            second.target_coordinates["subscription"],
        )
        self.assertNotEqual(
            fingerprint_artifact(first), fingerprint_artifact(second)
        )

    def test_adapter_satisfies_broker_adapter_protocol(self):
        adapter, _ = _adapter_for(_two_subscription_targets(), {}, {})
        self.assertTrue(hasattr(adapter, "fetch_failures"))
        self.assertTrue(callable(adapter.fetch_failures))
        fetch_signature = BrokerAdapter.fetch_failures
        self.assertTrue(callable(fetch_signature))

    def test_azure_sdk_is_not_importable_at_module_scope(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import specfuse.monitor.providers.azure_service_bus",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_transport_asked_for_both_depth_and_age(self):
        targets = [
            {
                "subscription": "orders-created-sub",
                "function": "ProcessOrderCreated",
                "stall_after": "15m",
            }
        ]
        active_counts = {"orders-created-sub": 40}
        oldest_enqueued_times = {
            "orders-created-sub": _NOW - timedelta(minutes=30)
        }
        adapter, transport = _adapter_for(
            targets, active_counts, oldest_enqueued_times
        )
        artifacts = list(adapter.fetch_failures())

        called_operations = {name for name, _ in transport.calls}
        self.assertIn("get_active_message_count", called_operations)
        self.assertIn("get_oldest_message_enqueued_time", called_operations)

        self.assertEqual(len(artifacts), 1)
        observed_text = artifacts[0].observed_text
        self.assertIn("40", observed_text)
        self.assertIn("1800", observed_text)  # 30 minutes, in seconds

    def test_oldest_message_older_than_threshold_yields_artifact(self):
        targets = [
            {
                "subscription": "orders-created-sub",
                "function": "ProcessOrderCreated",
                "stall_after": "15m",
            }
        ]
        active_counts = {"orders-created-sub": 5}
        oldest_enqueued_times = {
            "orders-created-sub": _NOW - timedelta(minutes=30)
        }
        adapter, _ = _adapter_for(targets, active_counts, oldest_enqueued_times)
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 1)

    def test_deep_but_draining_queue_yields_no_artifact(self):
        """A large depth with a young oldest message is not stalled — the
        age is the decision, the depth is only evidence (criterion 4)."""
        targets = [
            {
                "subscription": "orders-created-sub",
                "function": "ProcessOrderCreated",
                "stall_after": "15m",
            }
        ]
        active_counts = {"orders-created-sub": 5000}
        oldest_enqueued_times = {
            "orders-created-sub": _NOW - timedelta(minutes=1)
        }
        adapter, _ = _adapter_for(targets, active_counts, oldest_enqueued_times)
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(artifacts, [])

    def test_target_coordinates_carry_subscription_and_function(self):
        targets = _two_subscription_targets()
        active_counts = {"orders-created-sub": 40, "orders-cancelled-sub": 12}
        oldest_enqueued_times = {
            "orders-created-sub": _NOW - timedelta(minutes=30),
            "orders-cancelled-sub": _NOW - timedelta(minutes=45),
        }
        adapter, _ = _adapter_for(targets, active_counts, oldest_enqueued_times)
        artifacts = list(adapter.fetch_failures())
        for artifact in artifacts:
            self.assertIsInstance(artifact, FailureArtifact)
            self.assertIn("subscription", artifact.target_coordinates)
            self.assertIn("function", artifact.target_coordinates)

    def test_only_metadata_read_operations_are_recorded(self):
        targets = _two_subscription_targets()
        active_counts = {"orders-created-sub": 40, "orders-cancelled-sub": 12}
        oldest_enqueued_times = {
            "orders-created-sub": _NOW - timedelta(minutes=30),
            "orders-cancelled-sub": _NOW - timedelta(minutes=45),
        }
        adapter, transport = _adapter_for(
            targets, active_counts, oldest_enqueued_times
        )
        list(adapter.fetch_failures())

        called_operations = {name for name, _ in transport.calls}
        self.assertTrue(called_operations)
        self.assertFalse(called_operations & _FORBIDDEN_OPERATIONS)
        self.assertTrue(
            called_operations.issubset(
                {"get_active_message_count", "get_oldest_message_enqueued_time"}
            )
        )

    def test_stall_after_grammar_parses_expected_units(self):
        self.assertEqual(parse_stall_after_seconds("30s"), 30)
        self.assertEqual(parse_stall_after_seconds("15m"), 15 * 60)
        self.assertEqual(parse_stall_after_seconds("2h"), 2 * 3600)
        self.assertEqual(parse_stall_after_seconds("1d"), 86400)

    def test_stall_after_grammar_rejects_malformed_values(self):
        for bad_value in ("15", "15 minutes", "m15", "", "-5m"):
            with self.subTest(bad_value=bad_value):
                with self.assertRaises(ValueError) as ctx:
                    parse_stall_after_seconds(bad_value)
                self.assertIn(bad_value, str(ctx.exception))

    def test_target_with_no_stall_after_is_skipped_and_recorded(self):
        targets = [
            {
                "subscription": "orders-created-sub",
                "function": "ProcessOrderCreated",
                # no stall_after
            },
            {
                "subscription": "orders-cancelled-sub",
                "function": "ProcessOrderCancelled",
                "stall_after": "15m",
            },
        ]
        active_counts = {"orders-cancelled-sub": 12}
        oldest_enqueued_times = {
            "orders-cancelled-sub": _NOW - timedelta(minutes=45)
        }
        adapter, _ = _adapter_for(targets, active_counts, oldest_enqueued_times)
        artifacts = list(adapter.fetch_failures())

        self.assertEqual(len(artifacts), 1)
        self.assertEqual(
            artifacts[0].target_coordinates["subscription"],
            "orders-cancelled-sub",
        )

        self.assertEqual(len(adapter.skipped_targets), 1)
        skipped = adapter.skipped_targets[0]
        self.assertEqual(skipped.subscription, "orders-created-sub")
        self.assertEqual(skipped.function, "ProcessOrderCreated")
        self.assertTrue(skipped.reason)

    def test_reference_instant_pins_stalled_vs_not_stalled(self):
        targets = [
            {
                "subscription": "orders-created-sub",
                "function": "ProcessOrderCreated",
                "stall_after": "15m",
            }
        ]
        active_counts = {"orders-created-sub": 40}
        oldest_message_time = _NOW - timedelta(minutes=30)
        oldest_enqueued_times = {"orders-created-sub": oldest_message_time}

        not_stalled_reference = oldest_message_time + timedelta(minutes=5)
        adapter, _ = _adapter_for(
            targets,
            active_counts,
            oldest_enqueued_times,
            reference=not_stalled_reference,
        )
        self.assertEqual(list(adapter.fetch_failures()), [])

        stalled_reference = oldest_message_time + timedelta(minutes=20)
        adapter, _ = _adapter_for(
            targets, active_counts, oldest_enqueued_times, reference=stalled_reference
        )
        self.assertEqual(len(list(adapter.fetch_failures())), 1)

    def test_no_wall_clock_read_in_queue_stalled_code_path(self):
        result = subprocess.run(
            [
                "grep",
                "-rn",
                "datetime.now\\|time.time",
                "specfuse/monitor/providers/azure_service_bus.py",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.stdout.strip(), "")

    def test_planted_secret_is_redacted_at_the_boundary(self):
        planted_secret = "sb-fixture-example-not-a-real-credential-000222"
        subscription = f"orders-created-sub-token={planted_secret}"
        targets = [
            {
                "subscription": subscription,
                "function": "ProcessOrderCreated",
                "stall_after": "15m",
            }
        ]
        active_counts = {subscription: 40}
        oldest_enqueued_times = {subscription: _NOW - timedelta(minutes=30)}
        adapter, _ = _adapter_for(targets, active_counts, oldest_enqueued_times)
        artifacts = list(adapter.fetch_failures())

        self.assertEqual(len(artifacts), 1)
        observed_text = artifacts[0].observed_text
        self.assertNotIn(planted_secret, observed_text)
        self.assertIn("<redacted:", observed_text)


if __name__ == "__main__":
    unittest.main()
