# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Redact secret-shaped text out of a `FailureArtifact` before it can leave
the process (FEAT-2026-0040/T03).

The harvester reads dead-lettered message bodies, exception messages, and log
lines straight out of a customer's production environment. Whatever secret
shape was in that text — a connection string, a bearer token, an API key —
rides along unless something strips it before the artifact is serialized,
logged, or filed as a GitHub issue. This module is that boundary.

This is a purpose-built implementation, not a reuse of `redact_leak_findings`
in `loop.py`: that function is marker-gated on the literal string
``"leak-scan"`` (it exists to stop captured pre-commit hook stderr from
re-poisoning the event log) and is a no-op on anything else, including an
exception message. Its repo-internal pattern source lives only under
`.specfuse/scripts/` and is deliberately absent from the packaged
`specfuse/loop/data/` tree (issue #55) — this harvester runs in consumer
repositories where that file does not exist, so importing it would work here
and crash everywhere it ships.

The one thing reused on purpose is the ``<redacted:sha8>`` convention: a
short stable digest of the matched value keeps a deduplicating harvester's
audit signal ("this secret appeared in 40 messages") without the live value
surviving into an issue body.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import replace

from specfuse.monitor.artifact import FailureArtifact

# Secret shapes routinely found in exception messages, dead-letter bodies,
# and log lines: connection strings with embedded credentials, cloud access
# keys, bearer/API tokens, and generic key=value or key: value assignments
# whose key names a credential. Each pattern is anchored tightly enough to
# leave ordinary prose untouched (criterion 7) while still catching the
# secret shapes named in the work unit's Context.
_SECRET_PATTERNS: tuple[re.Pattern, ...] = (
    # scheme://user:password@host connection strings (Postgres, Mongo, AMQP, ...)
    re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s:/@'\"]+:[^\s@'\"]+@[^\s'\"]+"),
    # AWS access key IDs
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # Bearer/authorization tokens
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}=*"),
    # generic key=value / key: "value" assignments naming a credential
    re.compile(
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|token|access[_-]?key)"
        r"\s*[:=]\s*['\"]?([A-Za-z0-9/+_.\-]{6,})['\"]?"
    ),
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


def _redact_text(text: str) -> str:
    """Replace each secret-shaped match in *text* with `<redacted:sha8>`,
    keyed on the matched value so repeats of the same secret redact to the
    same token and distinct secrets redact to distinct tokens."""
    for pattern in _SECRET_PATTERNS:
        def _sub(match: re.Match) -> str:
            matched = match.group(0)
            return f"<redacted:{_digest(matched)}>"

        text = pattern.sub(_sub, text)
    return text


def redact_artifact(artifact: FailureArtifact) -> FailureArtifact:
    """Return a `FailureArtifact` with secret-shaped text redacted.

    `failure_signature` is left untouched on purpose: T02's dedupe fingerprints
    on the signature, and redacting it would make two occurrences of the same
    failure hash to different fingerprints, silently breaking dedupe. The
    signature is expected to hold a stable classification string (e.g.
    ``"orders.created.dlq"``), not raw secret-bearing text — the harvester's
    contract is that free-form text lives in `observed_text`.
    """
    target_coordinates = artifact.target_coordinates
    if target_coordinates is not None:
        target_coordinates = {
            key: _redact_text(value) for key, value in target_coordinates.items()
        }

    return replace(
        artifact,
        component=_redact_text(artifact.component),
        check_type=_redact_text(artifact.check_type),
        failure_class=_redact_text(artifact.failure_class),
        observed_text=_redact_text(artifact.observed_text),
        target_coordinates=target_coordinates,
    )
