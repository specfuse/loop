# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3565: one missing subscription must not fail the whole `dlq` or
`queue-stalled` check. The missing target is skipped and reported; the other
targets are still read. Any other transport error still fails the check."""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from specfuse.monitor.providers.azure_service_bus import (
    QueueStalledAdapter,
    ServiceBusDlqAdapter,
)

_NOW = datetime(2026, 11, 3, 12, 0, 0, tzinfo=timezone.utc)


# Stand-ins named like the Azure SDK classes the real transports raise, so the
# test needs no Azure SDK installed.
class MessagingEntityNotFoundError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


class ServiceRequestError(Exception):
    pass


@dataclass(frozen=True)
class _Message:
    message_id: str
    dead_letter_reason: str = "MaxDeliveryCountExceeded"
    dead_letter_error_description: str = "System.TimeoutException: timed out"


class _DlqTransport:
    def __init__(self, missing, error=MessagingEntityNotFoundError):
        self._missing = missing
        self._error = error

    def peek_dead_letter_messages(self, *, subscription, max_message_count):
        if subscription == self._missing:
            raise self._error(f"The messaging entity '{subscription}' could not be found.")
        return [_Message(message_id=f"{subscription}-1")]


class _StalledTransport:
    def __init__(self, missing, error=ResourceNotFoundError):
        self._missing = missing
        self._error = error

    def _check(self, subscription):
        if subscription == self._missing:
            raise self._error("Operation returned an invalid status 'Not Found'")

    def get_active_message_count(self, *, subscription):
        self._check(subscription)
        return 3

    def get_oldest_message_enqueued_time(self, *, subscription):
        self._check(subscription)
        return _NOW - timedelta(hours=2)


_TARGETS = [
    {"subscription": "first-sub", "function": "First", "stall_after": "10m"},
    {"subscription": "retired-sub", "function": "Retired", "stall_after": "10m"},
    {"subscription": "last-sub", "function": "Last", "stall_after": "10m"},
]


class DlqMissingSubscriptionTests(unittest.TestCase):
    def _adapter(self, transport):
        return ServiceBusDlqAdapter(component="svc", transport=transport, targets=_TARGETS)

    def test_missing_subscription_is_skipped_and_others_still_read(self):
        adapter = self._adapter(_DlqTransport("retired-sub"))
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(
            [a.message_id for a in artifacts], ["first-sub-1", "last-sub-1"]
        )
        self.assertEqual(len(adapter.skipped_targets), 1)
        skipped = adapter.skipped_targets[0]
        self.assertEqual(
            (skipped.subscription, skipped.function), ("retired-sub", "Retired")
        )
        self.assertIn("not found", skipped.reason)

    def test_other_transport_errors_still_fail_the_check(self):
        adapter = self._adapter(_DlqTransport("retired-sub", error=ServiceRequestError))
        with self.assertRaises(ServiceRequestError):
            list(adapter.fetch_failures())


class QueueStalledMissingSubscriptionTests(unittest.TestCase):
    def _adapter(self, transport):
        return QueueStalledAdapter(
            component="svc", transport=transport, targets=_TARGETS, reference=_NOW
        )

    def test_missing_subscription_is_skipped_and_others_still_read(self):
        adapter = self._adapter(_StalledTransport("retired-sub"))
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 2)
        self.assertEqual(
            [s.subscription for s in adapter.skipped_targets], ["retired-sub"]
        )
        self.assertIn("not found", adapter.skipped_targets[0].reason)

    def test_other_transport_errors_still_fail_the_check(self):
        adapter = self._adapter(_StalledTransport("retired-sub", error=ServiceRequestError))
        with self.assertRaises(ServiceRequestError):
            list(adapter.fetch_failures())


if __name__ == "__main__":
    unittest.main()
