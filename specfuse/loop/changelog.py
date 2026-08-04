#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Keep-a-Changelog-shaped parser for CHANGELOG.md.

FEAT-2026-0064/T01. One parser, three consumers: this WU ships it, T02's two
collection points (`close-discipline.md`'s §3 enumeration and `fix-bug`'s PR
body) append entries through it, and T03 stamps a release heading through it.
A regex-only validator would leave each of those reimplementing the parse and
drifting; this module owns the structure once.

Four entry classes — `added` / `changed` / `fixed` / `breaking` — `breaking`
is its own class, not a flag on the others, because "will this break me" must
be answerable by reading one heading. Every entry carries a `FEAT-YYYY-NNNN`
or `#<issue-number>` trace; an entry without one is a finding, not silently
dropped, because it would otherwise be the only record of what happened with
no way back to the retrospective or issue that explains it.

Never raises on malformed input. A parser that crashes on a truncated file or
a stray bullet cannot distinguish "found a problem" from "could not look" —
`LEARNINGS [FEAT-2026-0072/G1-CLOSE]`. Every malformed shape this module
knows about becomes an entry in `ParseResult.findings`; `parse_changelog`
returns a normal `ParseResult` in every case, never an exception.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ENTRY_CLASSES = ("added", "changed", "fixed", "breaking")

_UNRELEASED_HEADING_RE = re.compile(r"^##\s+\[Unreleased\]\s*$")
_RELEASED_HEADING_RE = re.compile(r"^##\s+\[(?P<version>[^\]]+)\]\s*-\s*(?P<date>\S+)\s*$")
_ANY_H2_RE = re.compile(r"^##\s+")
_CLASS_HEADING_RE = re.compile(r"^###\s+(?P<name>\S.*?)\s*$")
_ENTRY_RE = re.compile(r"^-\s+(?P<summary>.+?)\s+\((?P<trace>[^()]+)\)\s*$")
_TRACE_RE = re.compile(r"^(FEAT-\d{4}-\d{4}(?:/[A-Za-z0-9-]+)?|#\d+)$")


@dataclass
class ChangelogEntry:
    entry_class: str
    summary: str
    trace: str
    line: int


@dataclass
class ChangelogSection:
    kind: str  # "unreleased" | "released"
    version: str | None
    date: str | None
    heading_line: int
    entries: list[ChangelogEntry] = field(default_factory=list)

    @property
    def is_unreleased(self) -> bool:
        return self.kind == "unreleased"


@dataclass
class ParseResult:
    sections: list[ChangelogSection] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    def unreleased(self) -> ChangelogSection | None:
        for section in self.sections:
            if section.is_unreleased:
                return section
        return None


def parse_changelog(text: str) -> ParseResult:
    """Parse Keep-a-Changelog-shaped text into sections/entries + findings.

    Never raises: every malformed shape below is recorded as a finding and
    parsing continues over the rest of the document.
    """
    sections: list[ChangelogSection] = []
    findings: list[str] = []
    current_section: ChangelogSection | None = None
    current_class: str | None = None

    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\n")

        if _UNRELEASED_HEADING_RE.match(line):
            current_section = ChangelogSection(
                kind="unreleased", version=None, date=None, heading_line=i,
            )
            sections.append(current_section)
            current_class = None
            continue

        m = _RELEASED_HEADING_RE.match(line)
        if m:
            current_section = ChangelogSection(
                kind="released",
                version=m.group("version"),
                date=m.group("date"),
                heading_line=i,
            )
            sections.append(current_section)
            current_class = None
            continue

        if _ANY_H2_RE.match(line):
            findings.append(f"line {i}: unrecognised release heading {line!r}")
            current_section = None
            current_class = None
            continue

        cm = _CLASS_HEADING_RE.match(line)
        if cm:
            if current_section is None:
                findings.append(
                    f"line {i}: entry class heading {line!r} appears outside "
                    "any release section"
                )
                current_class = None
                continue
            name = cm.group("name").strip().lower()
            if name not in ENTRY_CLASSES:
                findings.append(
                    f"line {i}: unrecognised entry class {cm.group('name')!r} "
                    f"— must be one of {', '.join(ENTRY_CLASSES)}"
                )
                current_class = None
                continue
            current_class = name
            continue

        if line.startswith("- "):
            if current_section is None:
                findings.append(
                    f"line {i}: entry {line!r} appears under no section heading"
                )
                continue
            if current_class is None:
                findings.append(
                    f"line {i}: entry {line!r} appears under no entry-class heading"
                )
                continue
            em = _ENTRY_RE.match(line)
            trace = em.group("trace").strip() if em else ""
            if not em or not _TRACE_RE.match(trace):
                findings.append(
                    f"line {i}: entry {line!r} carries no FEAT-YYYY-NNNN or "
                    "issue-number trace"
                )
                continue
            current_section.entries.append(
                ChangelogEntry(
                    entry_class=current_class,
                    summary=em.group("summary").strip(),
                    trace=trace,
                    line=i,
                )
            )
            continue

    for section in sections:
        if not section.entries:
            findings.append(f"line {section.heading_line}: section has no entries")

    return ParseResult(sections=sections, findings=findings)


# --- FEAT-2026-0064/T03: release stamping and the append primitive ---
#
# T01 owns the schema above; nothing here changes it. `stamp_release` and
# `append_entry` are the two writers T03 adds — `bump_version.py` calls the
# former, and it is the thing that makes a released section immutable: once a
# section is no longer `Unreleased`, `append_entry` refuses to target it.

_VERSION_FIELD_SEP = "+umbrella."


def _compose_version_field(version: str, umbrella_version: str) -> str:
    """Pack the umbrella version into the release heading's version field.

    `_RELEASED_HEADING_RE` (T01's, unmodified) requires the date to be the
    last token on the heading line, so there is no room to append the
    umbrella version after it. The version field itself is `[^\\]]+` —
    anything but `]` — so the umbrella version is packed inside it using a
    semver-build-metadata-shaped separator, keeping the heading a single
    schema-legal `## [version] - date` line.
    """
    return f"{version}{_VERSION_FIELD_SEP}{umbrella_version}"


def split_version_field(version_field: str) -> tuple[str, str | None]:
    """Split a released heading's version field into (version, umbrella_version).

    Returns `(version_field, None)` unchanged if it carries no umbrella
    suffix (e.g. a pre-T03 release heading).
    """
    if _VERSION_FIELD_SEP in version_field:
        version, _, umbrella = version_field.partition(_VERSION_FIELD_SEP)
        return version, umbrella
    return version_field, None


def stamp_release(text: str, *, version: str, date: str, umbrella_version: str) -> str:
    """Stamp `Unreleased` as a released section and open a fresh one above it.

    `umbrella_version` is a required keyword argument, not merely a
    recommended one: a call that omits it raises `ValueError` before any
    text is touched, because a driver version with no umbrella version is
    half a release (`pipx upgrade specfuse` resolves through the umbrella
    package).

    Refuses (does not silently re-stamp) if `version` already names a
    released section in `text` — a release script that double-stamps
    corrupts the document it exists to protect, so a second stamp of the
    same version is an error, not a no-op.
    """
    if not umbrella_version:
        raise ValueError(
            "umbrella_version is required to stamp a release — a driver "
            "version alone documents half a release"
        )

    result = parse_changelog(text)
    for section in result.sections:
        if section.is_unreleased:
            continue
        existing_version, _ = split_version_field(section.version or "")
        if existing_version == version:
            raise ValueError(
                f"version {version!r} is already stamped in the changelog — "
                "refusing to double-stamp a released section"
            )

    unreleased = result.unreleased()
    if unreleased is None:
        raise ValueError("no [Unreleased] section found to stamp")

    lines = text.splitlines()
    heading_idx = unreleased.heading_line - 1  # heading_line is 1-based
    version_field = _compose_version_field(version, umbrella_version)
    lines[heading_idx] = f"## [{version_field}] - {date}"
    lines[heading_idx:heading_idx] = ["## [Unreleased]", ""]

    newline = "\n" if text.endswith("\n") else ""
    return "\n".join(lines) + newline


def append_entry(
    text: str,
    *,
    entry_class: str,
    summary: str,
    trace: str,
    section: str = "Unreleased",
) -> str:
    """Append one entry under `Unreleased`'s `entry_class` subheading.

    `section` names the target release section by its heading label.
    **Only `"Unreleased"` is writable** — any other value is refused,
    including the label of a section that was just stamped, because a
    released section is immutable once stamped. If a later append could
    land inside a shipped section, the document would become a moving
    record of the past.
    """
    if section != "Unreleased":
        raise ValueError(
            f"cannot append to {section!r} — 'Unreleased' is the only "
            "writable section; released sections are immutable once stamped"
        )
    if entry_class not in ENTRY_CLASSES:
        raise ValueError(
            f"unrecognised entry class {entry_class!r} — must be one of "
            f"{', '.join(ENTRY_CLASSES)}"
        )

    result = parse_changelog(text)
    unreleased = result.unreleased()
    if unreleased is None:
        raise ValueError("no [Unreleased] section found to append to")

    lines = text.splitlines()
    start = unreleased.heading_line  # 0-based index of the line after heading
    end = len(lines)
    for i in range(start, len(lines)):
        if _UNRELEASED_HEADING_RE.match(lines[i]) or _RELEASED_HEADING_RE.match(lines[i]):
            end = i
            break

    class_heading = f"### {entry_class.capitalize()}"
    bullet = f"- {summary} ({trace})"

    class_idx = None
    class_end = end
    for i in range(start, end):
        cm = _CLASS_HEADING_RE.match(lines[i])
        if cm and cm.group("name").strip().lower() == entry_class:
            class_idx = i
            class_end = end
            for j in range(i + 1, end):
                if _CLASS_HEADING_RE.match(lines[j]):
                    class_end = j
                    break
            break

    if class_idx is not None:
        insert_at = class_end
        while insert_at > class_idx + 1 and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        lines[insert_at:insert_at] = [bullet]
    else:
        insert_at = end
        while insert_at > start and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        lines[insert_at:insert_at] = ["", class_heading, "", bullet]

    newline = "\n" if text.endswith("\n") else ""
    return "\n".join(lines) + newline
