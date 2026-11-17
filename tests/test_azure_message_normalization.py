# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3592: per-message Azure tokens must not survive message normalization.

One `specfuse monitor run` filed 339 issues for what was a handful of failures:
the Service Bus `TrackingId` GUID carries a `_B<n>` partition suffix, so the
`\\b`-anchored GUID pattern never matched it; the `SystemTracker` subscription,
an HTTP `Date:` header, and stack traces embedded by the Functions host wrapper
exceptions varied per occurrence too. Each case below pairs two occurrences of
one failure that must share a signature, and every pair of distinct failures
must still stay apart.

Both Azure providers normalize the same way, so each case runs through the
error-logs adapter (App Insights) and the dlq adapter (Service Bus).
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.providers.azure_app_insights import ErrorLogsAdapter
from specfuse.monitor.providers.azure_service_bus import ServiceBusDlqAdapter

_LOCK_LOST = (
    "The lock supplied is invalid. Either the lock expired, or the message has "
    "already been removed from the queue. For more information please see "
    "https://aka.ms/ServiceBusExceptions . Reference:{ref}, TrackingId:{track}, "
    "SystemTracker:sbns-acme-prd:topic:sbt-acme~{part}|{sub}, Timestamp:{ts} "
    "(MessageLockLost). For troubleshooting information, see "
    "https://aka.ms/azsdk/net/servicebus/exceptions/troubleshoot."
)

LOCK_LOST_A = _LOCK_LOST.format(
    ref="1b9d4c1e-7a3f-4e0b-9c55-2f6a8d7e1a10",
    track="4311145c-fcf8-4a21-9bdb-95c15255c504_B4",
    part="16383",
    sub="on-order-created",
    ts="2026-11-16T10:00:00",
)
LOCK_LOST_B = _LOCK_LOST.format(
    ref="9e2a7b30-55c1-4d8e-8f0a-6b1c3d2e4f50",
    track="68128c21-0bb5-44ea-8e81-77822ab6f35b_B11",
    part="12287",
    sub="on-invoice-paid-sync-ledger",
    ts="2026-11-16T11:42:17",
)

_RPC = (
    'Status(StatusCode="Unknown", Detail="Azure.Messaging.ServiceBus.'
    "ServiceBusException: The lock supplied is invalid. (MessageLockLost)\n"
    "   at Azure.Messaging.ServiceBus.Amqp.AmqpReceiver.{receiver}(Guid lockToken, "
    "TimeSpan timeout)\n"
    "   at Acme.Functions.{function}.Run(ServiceBusReceivedMessage message) in "
    '/src/Acme.Functions/{function}.cs:line {line}")'
)
RPC_A = _RPC.format(receiver="CompleteInternalAsync", function="Orders.OrderCreatedTrigger", line=42)
RPC_B = _RPC.format(receiver="AbandonInternalAsync", function="Billing.InvoicePaidTrigger", line=117)

_LEASE = (
    "The lease ID specified did not match the lease ID for the blob. "
    "RequestId:{req} Time:{time} Status: 412 (The lease ID specified did not match "
    "the lease ID for the blob.) ErrorCode: LeaseIdMismatchWithLeaseOperation "
    "Headers: Date: {date} Server: Windows-Azure-Blob/1.0"
)
LEASE_A = _LEASE.format(
    req="0f8e7d6c-5b4a-4392-8170-6f5e4d3c2b1a",
    time="2026-11-14T08:01:02.1234567Z",
    date="Fri, 14 Nov 2026 08:01:02 GMT",
)
LEASE_B = _LEASE.format(
    req="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
    time="2026-11-15T19:30:45.7654321Z",
    date="Sat, 15 Nov 2026 19:30:45 GMT",
)

# Same failure in each pair; different failures across pairs.
SAME_FAILURE_PAIRS = {
    "service-bus-lock-lost": (LOCK_LOST_A, LOCK_LOST_B),
    "functions-host-wrapper-with-stack": (RPC_A, RPC_B),
    "blob-lease-with-http-date": (LEASE_A, LEASE_B),
}


class _Transport:
    def __init__(self, messages):
        self._messages = messages

    def run_query(self, query):
        return [
            {"type": "Acme.FailureException", "outerMessage": m, "operation_Id": f"op{i}"}
            for i, m in enumerate(self._messages)
        ]


@dataclass(frozen=True)
class _DeadLetter:
    message_id: str
    dead_letter_reason: str
    dead_letter_error_description: str
    exception_type: str = "Acme.FailureException"


class _DlqTransport:
    def __init__(self, messages):
        self._messages = messages

    def peek_dead_letter_messages(self, *, subscription, max_message_count):
        return [
            _DeadLetter(f"m{i}", "MaxDeliveryCountExceeded", m)
            for i, m in enumerate(self._messages)
        ]


def _error_logs_fingerprints(messages):
    adapter = ErrorLogsAdapter(
        component="acme-worker",
        environment={"telemetry": {"provider": "app-insights"}},
        transport=_Transport(messages),
    )
    return [fingerprint_artifact(a) for a in adapter.fetch_failures()]


def _dlq_fingerprints(messages):
    adapter = ServiceBusDlqAdapter(
        component="acme-worker",
        transport=_DlqTransport(messages),
        targets=[{"subscription": "acme-sub", "function": "AcmeFunction"}],
    )
    return [fingerprint_artifact(a) for a in adapter.fetch_failures()]


_PROVIDERS = {"error-logs": _error_logs_fingerprints, "dlq": _dlq_fingerprints}


class SameFailureCollapsesTests(unittest.TestCase):
    def test_two_occurrences_of_one_failure_share_a_fingerprint(self):
        for provider, fingerprints in _PROVIDERS.items():
            for case, pair in SAME_FAILURE_PAIRS.items():
                with self.subTest(provider=provider, case=case):
                    first, second = fingerprints(list(pair))
                    self.assertEqual(first, second)


class DistinctFailuresStayApartTests(unittest.TestCase):
    def test_different_failures_keep_different_fingerprints(self):
        messages = [pair[0] for pair in SAME_FAILURE_PAIRS.values()] + [
            "Connection to the database failed at the gateway.",
            "Connection to the cache failed at the gateway.",
        ]
        for provider, fingerprints in _PROVIDERS.items():
            with self.subTest(provider=provider):
                prints = fingerprints(messages)
                self.assertEqual(len(set(prints)), len(messages))


class GuidBoundaryTests(unittest.TestCase):
    def test_guid_is_normalized_whatever_follows_it(self):
        guid_a = "4311145c-fcf8-4a21-9bdb-95c15255c504"
        guid_b = "68128c21-0bb5-44ea-8e81-77822ab6f35b"
        for suffix in ("_B4", ")", ".", ""):
            for provider, fingerprints in _PROVIDERS.items():
                with self.subTest(provider=provider, suffix=suffix):
                    first, second = fingerprints(
                        [f"Entity id={guid_a}{suffix} failed", f"Entity id={guid_b}{suffix} failed"]
                    )
                    self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
