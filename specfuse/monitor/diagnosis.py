# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The diagnosis comment contract (FEAT-2026-0041/T01): one `Diagnosis`
model, one renderer, one parser, one marker.

Mirrors `issues.py`'s embedded-marker shape rather than inventing a second
convention: a single `<!-- specfuse:diagnosis ... -->` marker carries every
structured field, and the marker in the body — re-checked client-side on
parse — is the sole authority. Render is the only place prose fields cross
the redaction boundary (`specfuse.monitor.redaction.redact_text`, promoted
from module-private by this work unit); by the time a body exists, its
prose is already safe to post.

`confidence` is a bounded float in `[0.0, 1.0]` rather than a closed
vocabulary: FEAT-2026-0042 gates on a threshold ("route to autofix above
X"), and a threshold comparison is direct against a numeric scale but
requires an arbitrary total order imposed on a word list. `fix_scope` is
the closed vocabulary — `small` / `large` / `external` — since it names a
routing category, not a threshold.

This module does not call `gh`, does not post anything, and makes no
subprocess or network call. It formats and parses; the skill posts.
"""

from __future__ import annotations

from dataclasses import dataclass

from specfuse.monitor.redaction import redact_text

FIX_SCOPES = ("small", "large", "external")

_MARKER_PREFIX = "<!-- specfuse:diagnosis "
_MARKER_SUFFIX = " -->"


class DiagnosisParseError(ValueError):
    """Raised by `parse` when a marker is present but malformed.

    A missing marker is a different, non-exceptional negative — `parse`
    returns `None` for that case, since "no diagnosis here" is an expected
    outcome for any comment body a caller might hand it. A *present but
    malformed* marker is a distinct failure: something produced or edited a
    marker this parser cannot trust, and that is worth naming loudly rather
    than silently treated as absence.
    """


@dataclass(frozen=True)
class Diagnosis:
    """A structured root-cause diagnosis of one harvester finding.

    `confidence` is a float in `[0.0, 1.0]`; `fix_scope` is one of
    `FIX_SCOPES` and nothing else. Both are validated at construction so an
    illegal value is rejected before it can reach render or a downstream
    parser.
    """

    root_cause: str
    evidence: str
    candidate_fix: str
    confidence: float
    fix_scope: str

    def __post_init__(self) -> None:
        if self.fix_scope not in FIX_SCOPES:
            raise ValueError(
                f"fix_scope must be one of {FIX_SCOPES!r}, got {self.fix_scope!r}"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be within [0.0, 1.0], got {self.confidence!r}"
            )


def _marker(diagnosis: Diagnosis) -> str:
    return (
        f"{_MARKER_PREFIX}"
        f"confidence={diagnosis.confidence} fix_scope={diagnosis.fix_scope}"
        f"{_MARKER_SUFFIX}"
    )


def render(diagnosis: Diagnosis) -> str:
    """Render `diagnosis` as a human-readable comment body carrying the
    embedded marker. Prose fields are redacted here, at the boundary,
    before anything can leave the process."""
    lines = [
        _marker(diagnosis),
        "",
        "**Root cause:**",
        redact_text(diagnosis.root_cause),
        "",
        "**Evidence:**",
        redact_text(diagnosis.evidence),
        "",
        "**Candidate fix:**",
        redact_text(diagnosis.candidate_fix),
        "",
        f"**Confidence:** {diagnosis.confidence}",
        f"**Fix scope:** {diagnosis.fix_scope}",
    ]
    return "\n".join(lines)


def parse(body: str) -> Diagnosis | None:
    """Recover a `Diagnosis` from a rendered comment body.

    Returns `None` when no marker is present. Raises `DiagnosisParseError`
    when a marker is present but its fields cannot be recovered — a
    malformed marker is not the same negative as no marker at all.
    """
    marker_start = body.find(_MARKER_PREFIX)
    if marker_start == -1:
        return None
    marker_end = body.find(_MARKER_SUFFIX, marker_start)
    if marker_end == -1:
        raise DiagnosisParseError("diagnosis marker has no closing '-->'")

    fragment = body[marker_start + len(_MARKER_PREFIX) : marker_end]
    fields: dict[str, str] = {}
    for token in fragment.split():
        if "=" not in token:
            raise DiagnosisParseError(f"malformed marker token: {token!r}")
        key, _, value = token.partition("=")
        fields[key] = value

    if "confidence" not in fields or "fix_scope" not in fields:
        raise DiagnosisParseError(
            f"diagnosis marker missing required field(s); got {fields!r}"
        )

    try:
        confidence = float(fields["confidence"])
    except ValueError as exc:
        raise DiagnosisParseError(
            f"confidence is not a float: {fields['confidence']!r}"
        ) from exc
    fix_scope = fields["fix_scope"]

    sections = _parse_sections(body[marker_end + len(_MARKER_SUFFIX) :])

    try:
        return Diagnosis(
            root_cause=sections["Root cause"],
            evidence=sections["Evidence"],
            candidate_fix=sections["Candidate fix"],
            confidence=confidence,
            fix_scope=fix_scope,
        )
    except KeyError as exc:
        raise DiagnosisParseError(f"diagnosis body missing section: {exc}") from exc
    except ValueError as exc:
        raise DiagnosisParseError(str(exc)) from exc


_SECTION_HEADERS = ("Root cause", "Evidence", "Candidate fix")


def _parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        matched_header = None
        for header in _SECTION_HEADERS:
            if stripped == f"**{header}:**":
                matched_header = header
                break
        if matched_header is not None:
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = matched_header
            buffer = []
            continue
        if stripped.startswith("**Confidence:**") or stripped.startswith("**Fix scope:**"):
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
                current = None
            continue
        if current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = "\n".join(buffer).strip()
    return sections
