# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Service Bus dead-letter-queue peek adapter (FEAT-2026-0040/T05).

Peeks — never receives, completes, abandons, dead-letters, defers, or
renews a lock on — a subscription's dead-letter queue and returns one
redacted `FailureArtifact` per dead-lettered message. Quarantine harvesting
(the mode that moves messages) is FEAT-2026-0038's; this module only reads.

The transport is injected at construction: `ServiceBusDlqAdapter` takes any
object exposing `peek_dead_letter_messages`, so every test in this module
runs against a stub with no Azure SDK on the path. `build_azure_transport`
is the only function that touches the real SDK, and it imports it lazily
inside the function body so importing this module never requires
`azure-servicebus` to be installed (the package has zero runtime
dependencies).
"""

from __future__ import annotations

import re
from typing import Iterable, Iterator, Mapping, Protocol, Sequence

from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.redaction import redact_artifact

_GUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
)
_NUMBER_RE = re.compile(r"\b\d+\b")


def _normalize_message(text: str) -> str:
    """Strip message IDs, timestamps, GUIDs, and sequence numbers so two
    occurrences of the same poison message collapse to one signature."""
    text = _GUID_RE.sub("<guid>", text)
    text = _TIMESTAMP_RE.sub("<timestamp>", text)
    text = _NUMBER_RE.sub("<num>", text)
    return " ".join(text.split())


def _exception_type_and_message(message: object) -> tuple[str, str]:
    """Derive the exception type and a raw description from a dead-lettered
    message. Prefers an explicit `exception_type` attribute (what a stub or
    a richer transport can supply); falls back to splitting the dead-letter
    error description on its first `: `, the common .NET exception-message
    shape (`System.Exception: some message`)."""
    explicit_type = getattr(message, "exception_type", None)
    description = getattr(message, "dead_letter_error_description", None) or ""
    if explicit_type:
        return str(explicit_type), description
    if ": " in description:
        exception_type, _, rest = description.partition(": ")
        return exception_type, rest
    return "UnknownException", description


class DeadLetterMessage(Protocol):
    """The shape a dead-lettered message must supply. Matches the fields a
    real `ServiceBusReceivedMessage` exposes; a stub only needs these."""

    message_id: str
    sequence_number: int
    dead_letter_reason: str
    dead_letter_error_description: str


class ServiceBusDlqTransport(Protocol):
    """The peek-only operation this adapter needs from a transport."""

    def peek_dead_letter_messages(
        self, *, subscription: str, max_message_count: int
    ) -> Iterable[object]:
        ...


class ServiceBusDlqAdapter:
    """`BrokerAdapter` for Service Bus: peeks each target subscription's
    dead-letter queue and yields one redacted `FailureArtifact` per message.
    """

    def __init__(
        self,
        *,
        component: str,
        transport: ServiceBusDlqTransport,
        targets: Sequence[Mapping[str, str]],
        max_message_count: int = 50,
    ) -> None:
        self._component = component
        self._transport = transport
        self._targets = targets
        self._max_message_count = max_message_count

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        for target in self._targets:
            subscription = target["subscription"]
            function = target["function"]
            messages = self._transport.peek_dead_letter_messages(
                subscription=subscription,
                max_message_count=self._max_message_count,
            )
            for message in messages:
                yield self._build_artifact(subscription, function, message)

    def _build_artifact(
        self, subscription: str, function: str, message: object
    ) -> FailureArtifact:
        failure_class = getattr(message, "dead_letter_reason", None) or "Unknown"
        exception_type, raw_message = _exception_type_and_message(message)
        failure_signature = f"{exception_type}:{_normalize_message(raw_message)}"
        observed_text = getattr(message, "dead_letter_error_description", None) or ""

        artifact = FailureArtifact.from_target(
            component=self._component,
            check_type="dlq",
            target={"subscription": subscription, "function": function},
            failure_class=failure_class,
            failure_signature=failure_signature,
            observed_text=observed_text,
        )
        return redact_artifact(artifact)


def build_azure_transport(
    *, fully_qualified_namespace: str, topic_name: str, credential: object
) -> ServiceBusDlqTransport:
    """Build a transport backed by the real Azure Service Bus SDK.

    Imported lazily so `azure-servicebus` is never required to import this
    module — only to call this factory.
    """
    from azure.servicebus import ServiceBusClient, ServiceBusSubQueue

    class _AzureServiceBusTransport:
        def peek_dead_letter_messages(
            self, *, subscription: str, max_message_count: int
        ) -> Iterable[object]:
            client = ServiceBusClient(
                fully_qualified_namespace=fully_qualified_namespace,
                credential=credential,
            )
            with client:
                receiver = client.get_subscription_receiver(
                    topic_name=topic_name,
                    subscription_name=subscription,
                    sub_queue=ServiceBusSubQueue.DEAD_LETTER,
                )
                with receiver:
                    return receiver.peek_messages(
                        max_message_count=max_message_count
                    )

    return _AzureServiceBusTransport()
