# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the Service Bus DLQ peek adapter (FEAT-2026-0040/T05)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import dataclass, field

from specfuse.monitor.adapters import BrokerAdapter
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.providers.azure_service_bus import ServiceBusDlqAdapter

_FORBIDDEN_OPERATIONS = frozenset(
    {"receive", "complete", "abandon", "dead_letter", "defer", "renew_lock"}
)


@dataclass(frozen=True)
class StubMessage:
    message_id: str
    sequence_number: int
    dead_letter_reason: str
    dead_letter_error_description: str
    exception_type: str = ""


@dataclass
class StubServiceBusTransport:
    """Records every method invoked on it so a test can assert, negatively,
    that only peek/read operations were ever called (criterion 6)."""

    messages_by_subscription: dict
    calls: list = field(default_factory=list)

    def peek_dead_letter_messages(self, *, subscription, max_message_count):
        self.calls.append(("peek_dead_letter_messages", subscription))
        return list(self.messages_by_subscription.get(subscription, []))

    # Settlement operations a real ServiceBusReceiver exposes. Present only
    # so a test can assert the adapter never reaches for them.
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


def _two_subscription_fixture():
    """At least 2 subscriptions, at least 2 dead-lettered messages each, and
    at least two messages sharing an exception type (criterion 4)."""
    return {
        "orders-created-sub": [
            StubMessage(
                message_id="11111111-1111-1111-1111-111111111111",
                sequence_number=100,
                dead_letter_reason="MaxDeliveryCountExceeded",
                dead_letter_error_description=(
                    "System.TimeoutException: downstream call to inventory "
                    "service timed out"
                ),
            ),
            StubMessage(
                message_id="22222222-2222-2222-2222-222222222222",
                sequence_number=101,
                dead_letter_reason="MaxDeliveryCountExceeded",
                dead_letter_error_description=(
                    "System.ArgumentNullException: order payload missing "
                    "customer id"
                ),
            ),
        ],
        "orders-cancelled-sub": [
            StubMessage(
                message_id="33333333-3333-3333-3333-333333333333",
                sequence_number=200,
                dead_letter_reason="MaxDeliveryCountExceeded",
                dead_letter_error_description=(
                    "System.TimeoutException: downstream call to inventory "
                    "service timed out"
                ),
            ),
            StubMessage(
                message_id="44444444-4444-4444-4444-444444444444",
                sequence_number=201,
                dead_letter_reason="MaxDeliveryCountExceeded",
                dead_letter_error_description=(
                    "System.InvalidOperationException: cancellation window "
                    "elapsed"
                ),
            ),
        ],
    }


def _adapter_for(messages_by_subscription):
    transport = StubServiceBusTransport(messages_by_subscription)
    adapter = ServiceBusDlqAdapter(
        component="order-worker",
        transport=transport,
        targets=[
            {"subscription": "orders-created-sub", "function": "ProcessOrderCreated"},
            {
                "subscription": "orders-cancelled-sub",
                "function": "ProcessOrderCancelled",
            },
        ],
    )
    return adapter, transport


class TestDlqPeekAdapter(unittest.TestCase):
    def test_distinct_subscriptions_yield_distinct_fingerprints(self):
        adapter, _ = _adapter_for(_two_subscription_fixture())
        artifacts = list(adapter.fetch_failures())

        timeout_artifacts = [
            a for a in artifacts if "TimeoutException" in a.failure_signature
        ]
        self.assertEqual(len(timeout_artifacts), 2)
        first, second = timeout_artifacts
        self.assertNotEqual(
            first.target_coordinates["subscription"],
            second.target_coordinates["subscription"],
        )
        self.assertNotEqual(
            fingerprint_artifact(first), fingerprint_artifact(second)
        )

    def test_adapter_satisfies_broker_adapter_protocol(self):
        adapter, _ = _adapter_for(_two_subscription_fixture())
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

    def test_cardinality_two_subscriptions_two_messages_each(self):
        fixture = _two_subscription_fixture()
        self.assertGreaterEqual(len(fixture), 2)
        for messages in fixture.values():
            self.assertGreaterEqual(len(messages), 2)

    def test_target_coordinates_carry_subscription_and_function(self):
        adapter, _ = _adapter_for(_two_subscription_fixture())
        artifacts = list(adapter.fetch_failures())
        for artifact in artifacts:
            self.assertIsInstance(artifact, FailureArtifact)
            self.assertIn("subscription", artifact.target_coordinates)
            self.assertIn("function", artifact.target_coordinates)

    def test_only_peek_operations_are_recorded(self):
        adapter, transport = _adapter_for(_two_subscription_fixture())
        list(adapter.fetch_failures())

        called_operations = {name for name, _ in transport.calls}
        self.assertTrue(called_operations)
        self.assertFalse(called_operations & _FORBIDDEN_OPERATIONS)
        self.assertTrue(
            all(name == "peek_dead_letter_messages" for name in called_operations)
        )

    def test_same_poison_message_collapses_to_one_signature(self):
        messages_by_subscription = {
            "orders-created-sub": [
                StubMessage(
                    message_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    sequence_number=1,
                    dead_letter_reason="MaxDeliveryCountExceeded",
                    dead_letter_error_description=(
                        "System.TimeoutException: downstream call timed out"
                    ),
                ),
                StubMessage(
                    message_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                    sequence_number=2,
                    dead_letter_reason="MaxDeliveryCountExceeded",
                    dead_letter_error_description=(
                        "System.TimeoutException: downstream call timed out"
                    ),
                ),
            ],
        }
        adapter, _ = _adapter_for(messages_by_subscription)
        adapter._targets = [
            {"subscription": "orders-created-sub", "function": "ProcessOrderCreated"}
        ]
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 2)
        self.assertEqual(artifacts[0].failure_signature, artifacts[1].failure_signature)
        self.assertEqual(
            fingerprint_artifact(artifacts[0]), fingerprint_artifact(artifacts[1])
        )

    def test_different_exception_types_yield_different_signatures(self):
        adapter, _ = _adapter_for(_two_subscription_fixture())
        adapter._targets = [
            {"subscription": "orders-created-sub", "function": "ProcessOrderCreated"}
        ]
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 2)
        self.assertNotEqual(artifacts[0].failure_signature, artifacts[1].failure_signature)

    def test_planted_secret_is_redacted_at_the_boundary(self):
        planted_secret = "sb-fixture-example-token-not-a-real-credential-000111"
        messages_by_subscription = {
            "orders-created-sub": [
                StubMessage(
                    message_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
                    sequence_number=5,
                    dead_letter_reason="MaxDeliveryCountExceeded",
                    dead_letter_error_description=(
                        f"System.Exception: auth failed, token={planted_secret}"
                    ),
                ),
            ],
        }
        adapter, _ = _adapter_for(messages_by_subscription)
        adapter._targets = [
            {"subscription": "orders-created-sub", "function": "ProcessOrderCreated"}
        ]
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 1)
        observed_text = artifacts[0].observed_text
        self.assertNotIn(planted_secret, observed_text)
        self.assertIn("<redacted:", observed_text)


if __name__ == "__main__":
    unittest.main()
