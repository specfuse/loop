# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Stable fingerprinting over a FailureArtifact's identity.

FEAT-2026-0040/T02: the fingerprint incorporates the target coordinates a
target-derived artifact carries (`dlq`'s `subscription`+`function`,
`heartbeat`'s `name`) so distinct targets on one component never collapse
into one dedupe key. An `invariant` artifact carries no target coordinates
(T01 guarantees this) and falls back to its `failure_signature` alone, which
is where the check's `fingerprint_by` value lives for that check type.

Python's built-in string hashing is salted per process and would not survive
a restart, so it is not used here. `hashlib.sha256` over a canonically
ordered JSON payload is stable across processes and insensitive to mapping
iteration order.
"""

from __future__ import annotations

import hashlib
import json

from specfuse.monitor.artifact import FailureArtifact


def fingerprint_artifact(artifact: FailureArtifact) -> str:
    """Return a stable digest identifying this artifact's dedupe identity."""
    payload = {
        "component": artifact.component,
        "check_type": artifact.check_type,
        "failure_class": artifact.failure_class,
        "failure_signature": artifact.failure_signature,
    }
    if artifact.target_coordinates:
        payload["target_coordinates"] = dict(artifact.target_coordinates)
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
