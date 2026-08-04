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
