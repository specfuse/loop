# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Adapter protocols the provider-specific gate-2 adapters implement.

Neither protocol names a provider (FEAT-2026-0040/T01 criterion 3): each
declares only that it hands back ``FailureArtifact``s, the neutral model in
``artifact.py``. Provider-specific adapters live in gate 2 and implement
these shapes.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Protocol

from specfuse.monitor.artifact import FailureArtifact


class TelemetryAdapter(Protocol):
    """Produces failure artifacts by querying a telemetry backend."""

    def fetch_failures(self) -> Iterable[FailureArtifact]:
        ...


class BrokerAdapter(Protocol):
    """Produces failure artifacts by inspecting a message-broker's state."""

    def fetch_failures(self) -> Iterable[FailureArtifact]:
        ...


def resolve_telemetry(component: str, environment: Mapping[str, object]) -> object:
    """Resolve the telemetry binding a component's failure artifacts use.

    This is the seam from the recorded PLAN.md decision against #262:
    ``environments.<name>.telemetry`` is a single binding per environment
    today, so every component in an environment resolves to the same sink —
    correct for the motivating project, wrong in general. The signature
    takes ``component`` even though this, the only implementation today,
    reads only the environment's binding, so a future per-component
    resolver adds a resolver rather than reshaping every adapter that calls
    this function.
    """
    return environment["telemetry"]
