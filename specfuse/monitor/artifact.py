# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The neutral failure artifact the harvester's core reasons about.

No provider type is reachable from this module (FEAT-2026-0040/T01 criterion
3) and no firing-time computation lives here (criterion 9) — both are gate
2's concern, once real adapters exist to need them.

0069 separated two axes: ``component`` is the unit of deployment and
attribution, ``targets`` is the unit of failure-artifact enumeration. A
``FailureArtifact`` therefore carries both — the component it belongs to,
and, when it came from a target, that target's coordinates — so T02 can
fingerprint on the coordinates the binding constraint requires.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional

# Which coordinate keys a target-derived artifact carries, per check type.
# Mirrors the shape of the monitoring schema's own per-check-type target
# requirements without importing from lint_monitoring.py — that module is
# gate 2's, and this WU only reads its shape (see the WU's "do not touch").
_TARGET_COORDINATE_FIELDS: Mapping[str, tuple[str, ...]] = {
    "dlq": ("subscription", "function"),
    "heartbeat": ("name",),
    "queue-stalled": ("subscription", "function"),
}

# Check types that must never carry target coordinates — 0069 rejected
# `targets` on these, so `fingerprint_by` stays their single enumeration key.
_TARGETLESS_CHECK_TYPES = frozenset({"error-logs", "http-5xx", "invariant"})


@dataclass(frozen=True)
class FailureArtifact:
    """A single observed failure, stripped of any provider-specific shape.

    ``target_coordinates`` is populated only for artifacts derived from a
    monitoring target (``dlq``, ``heartbeat``, ``queue-stalled``, ...); it is
    ``None`` for check types that enumerate on something other than a
    target, such as ``invariant``.
    """

    component: str
    check_type: str
    failure_class: str
    failure_signature: str
    observed_text: str
    target_coordinates: Optional[Mapping[str, str]] = None

    @classmethod
    def from_target(
        cls,
        *,
        component: str,
        check_type: str,
        target: Mapping[str, str],
        failure_class: str,
        failure_signature: str,
        observed_text: str,
    ) -> "FailureArtifact":
        """Build an artifact from a monitoring target, extracting only the
        coordinate keys that check type is defined to carry."""
        if check_type in _TARGETLESS_CHECK_TYPES:
            raise ValueError(
                f"check type {check_type!r} does not carry target coordinates"
            )
        fields = _TARGET_COORDINATE_FIELDS.get(check_type, ())
        coordinates = MappingProxyType(
            {field: target[field] for field in fields if field in target}
        )
        return cls(
            component=component,
            check_type=check_type,
            failure_class=failure_class,
            failure_signature=failure_signature,
            observed_text=observed_text,
            target_coordinates=coordinates or None,
        )
