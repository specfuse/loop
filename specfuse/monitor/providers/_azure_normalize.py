#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Message normalization shared by both Azure provider modules.

A failure's signature is its exception type plus its message with every
per-occurrence token replaced, so two occurrences of one failure fingerprint
the same and land on one issue. Anything left in that varies per occurrence
files a new issue per occurrence: #3592 filed 339 issues in one run for a
handful of failures.
"""

from __future__ import annotations

import re

__all__ = ("normalize_message",)

# A .NET stack frame (`at Namespace.Type.Method(`). The Functions host wrapper
# exceptions (`Grpc.Core.RpcException`, `Rpc.RpcException`) embed the inner
# exception's whole stack in their message, so each call path would otherwise
# be its own signature. The top in-app frame is read separately (`Where`).
_STACK_RE = re.compile(r"\s+at [A-Za-z_][\w.`<>+\[\],]*\(.*", re.DOTALL)

# Service Bus per-message tokens. `TrackingId` carries a `_B<n>` partition
# suffix; `SystemTracker` names the entity (`ns:topic:t~<partition>|<sub>`),
# and MessageLockLost on many subscriptions is one failure, not one per
# subscription — the subscription still shows in the issue body.
_AZURE_TOKEN_RE = re.compile(
    r"\b(TrackingId|SystemTracker|Reference|LockToken):\s*[^,\s\"\\]+"
)
# Hex boundaries, not `\b`: `_` is a word character, so `<guid>_B4` never
# matched a `\b`-anchored pattern.
_GUID_RE = re.compile(
    r"(?<![0-9a-fA-F])[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(?![0-9a-fA-F])"
)
_TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
)
# An HTTP `Date:` header value (RFC 1123), as Azure Storage errors echo it.
_HTTP_DATE_RE = re.compile(
    r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), \d{1,2} "
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4} "
    r"\d{2}:\d{2}:\d{2} GMT\b"
)
_NUMBER_RE = re.compile(r"\b\d+\b")


def normalize_message(text: str) -> str:
    """Replace every per-occurrence token in *text* — embedded stack frames,
    Service Bus tracking tokens, GUIDs, timestamps, and bare numbers — so two
    occurrences of one failure collapse to one signature."""
    text = _STACK_RE.sub(" <stack>", text)
    text = _AZURE_TOKEN_RE.sub(lambda m: f"{m.group(1)}:<id>", text)
    text = _GUID_RE.sub("<guid>", text)
    text = _HTTP_DATE_RE.sub("<timestamp>", text)
    text = _TIMESTAMP_RE.sub("<timestamp>", text)
    text = _NUMBER_RE.sub("<num>", text)
    return " ".join(text.split())
