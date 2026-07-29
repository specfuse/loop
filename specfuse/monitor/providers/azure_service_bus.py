# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Service Bus broker adapters (FEAT-2026-0040/T05, /T08).

Two adapters, both read-only:

- `ServiceBusDlqAdapter` (T05) peeks — never receives, completes, abandons,
  dead-letters, defers, or renews a lock on — a subscription's dead-letter
  queue and returns one redacted `FailureArtifact` per dead-lettered
  message. Quarantine harvesting (the mode that moves messages) is
  FEAT-2026-0038's; this module only reads.
- `QueueStalledAdapter` (T08) reads a subscription's queue depth and the
  age of its oldest active message — a broker coordinate, not a telemetry
  one — and yields one `FailureArtifact` per target whose backlog has sat
  longer than its declared `stall_after` threshold.

Both transports are injected at construction, so every test in this module
runs against a stub with no Azure SDK on the path. `build_azure_transport`
and `build_azure_queue_stalled_transport` are the only functions that touch
the real SDK, and each imports it lazily inside its function body so
importing this module never requires `azure-servicebus` to be installed
(the package has zero runtime dependencies).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Iterator, List, Mapping, Optional, Protocol, Sequence

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


_STALL_AFTER_RE = re.compile(r"^(\d+)([smhd])$")
_STALL_AFTER_MULTIPLIERS: Mapping[str, int] = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}


def parse_stall_after_seconds(value: str) -> int:
    """Parse a `stall_after` value (`<integer><unit>`, unit in s/m/h/d) into
    seconds.

    Refuses rather than guesses (the WU's sub-decision 1): anything outside
    the grammar — no unit, an unsupported unit, whitespace, a negative sign
    — raises `ValueError` naming the offending value. No coercion, no
    "assume minutes", no silent zero.
    """
    match = _STALL_AFTER_RE.match(value)
    if not match:
        raise ValueError(
            f"invalid stall_after value {value!r} — expected "
            f"<integer><unit> with unit in s/m/h/d, e.g. '15m'"
        )
    magnitude, unit = match.groups()
    return int(magnitude) * _STALL_AFTER_MULTIPLIERS[unit]


@dataclass(frozen=True)
class SkippedTarget:
    """A `queue-stalled` target the adapter did not evaluate, and why."""

    subscription: str
    function: str
    reason: str


class QueueStalledTransport(Protocol):
    """The metadata-read operations this adapter needs from a transport.

    Both are management/metadata reads over a subscription's active queue —
    neither peeks, receives, nor otherwise touches a message body.
    """

    def get_active_message_count(self, *, subscription: str) -> int:
        ...

    def get_oldest_message_enqueued_time(
        self, *, subscription: str
    ) -> Optional[datetime]:
        ...


class QueueStalledAdapter:
    """`BrokerAdapter` for Service Bus: flags a subscription whose oldest
    active message has been sitting longer than its declared `stall_after`
    threshold. Queue depth rides along as evidence in `observed_text`; the
    stall decision itself is made on the age alone (the WU's binding
    invariant — a deep-but-draining queue is not stalled).
    """

    def __init__(
        self,
        *,
        component: str,
        transport: QueueStalledTransport,
        targets: Sequence[Mapping[str, str]],
        reference: datetime,
    ) -> None:
        self._component = component
        self._transport = transport
        self._targets = targets
        self._reference = reference
        self.skipped_targets: List[SkippedTarget] = []

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        for target in self._targets:
            subscription = target["subscription"]
            function = target["function"]
            stall_after_raw = target.get("stall_after")
            if not stall_after_raw:
                self.skipped_targets.append(
                    SkippedTarget(
                        subscription=subscription,
                        function=function,
                        reason="no stall_after configured",
                    )
                )
                continue

            stall_after_seconds = parse_stall_after_seconds(stall_after_raw)
            active_count = self._transport.get_active_message_count(
                subscription=subscription
            )
            oldest_enqueued = self._transport.get_oldest_message_enqueued_time(
                subscription=subscription
            )
            if oldest_enqueued is None:
                continue
            age_seconds = (self._reference - oldest_enqueued).total_seconds()
            if age_seconds < stall_after_seconds:
                continue
            yield self._build_artifact(
                subscription, function, active_count, age_seconds, stall_after_raw
            )

    def _build_artifact(
        self,
        subscription: str,
        function: str,
        active_count: int,
        age_seconds: float,
        stall_after_raw: str,
    ) -> FailureArtifact:
        observed_text = (
            f"subscription={subscription}, "
            f"queue depth (active message count)={active_count}, "
            f"oldest message age={int(age_seconds)}s, "
            f"stall_after={stall_after_raw}"
        )
        artifact = FailureArtifact.from_target(
            component=self._component,
            check_type="queue-stalled",
            target={"subscription": subscription, "function": function},
            failure_class="QueueStalled",
            failure_signature=f"QueueStalled:{subscription}",
            observed_text=observed_text,
        )
        return redact_artifact(artifact)


def build_azure_queue_stalled_transport(
    *, fully_qualified_namespace: str, topic_name: str, credential: object
) -> QueueStalledTransport:
    """Build a `QueueStalledTransport` backed by the real Azure Service Bus
    SDK's management client.

    Imported lazily so `azure-servicebus` is never required to import this
    module — only to call this factory.
    """
    from azure.servicebus.management import ServiceBusAdministrationClient

    class _AzureQueueStalledTransport:
        def get_active_message_count(self, *, subscription: str) -> int:
            client = ServiceBusAdministrationClient(
                fully_qualified_namespace=fully_qualified_namespace,
                credential=credential,
            )
            with client:
                runtime_properties = client.get_subscription_runtime_properties(
                    topic_name, subscription
                )
                return runtime_properties.active_message_count

        def get_oldest_message_enqueued_time(
            self, *, subscription: str
        ) -> Optional[datetime]:
            client = ServiceBusAdministrationClient(
                fully_qualified_namespace=fully_qualified_namespace,
                credential=credential,
            )
            with client:
                runtime_properties = client.get_subscription_runtime_properties(
                    topic_name, subscription
                )
                return getattr(
                    runtime_properties, "oldest_message_enqueued_time_utc", None
                )

    return _AzureQueueStalledTransport()


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
