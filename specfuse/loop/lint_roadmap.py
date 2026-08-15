#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Roadmap link-integrity lint (FEAT-2026-0034/T01).

`.specfuse/roadmap.md` and `.specfuse/roadmap-archive.md` are one link graph,
not two independent files: a `#feat-…` ref written inside the archive resolves
against the archive's own anchors, while the same ref written
`roadmap.md#feat-…` resolves against the roadmap's — and `/roadmap-archive`
moves detail sections between the two files on every run, so the rot is
bidirectional by construction. This module loads both files together and
checks four invariants:

  1. Every `blocked` row's detail section carries a `**Blocked by.**` block
     with at least one resolvable link (WARN, symmetrically, when that block
     is attached to a non-`blocked` row).
  2. Every `#feat-…` ref resolves against the anchor set of the file it
     names — a bare `#…` against its own file, a `roadmap.md#…` /
     `roadmap-archive.md#…` ref against the named file.
  3. Every `<a id="feat-YYYY-NNNN">` anchor is immediately followed (blank
     lines allowed) by the matching `## FEAT-YYYY-NNNN` heading.
  4. No `feat-…` ID is defined by more than one anchor, whether the
     duplicates land in one file or split across both.

Plus a WARN for a row whose Detail cell is `—` while a detail section for
that ID already exists (a live section nothing points at).

This module intentionally does not import `loop.py`. `auto_archive_feature`
there parses the same anchor/heading pairing and is the *producer* of shapes
3 and 4 above; sharing its parser would let this checker inherit its bugs
instead of catching them. Read as reference, reimplemented independently.

Findings, not exceptions: every check function is defensive about malformed
input (a truncated file, a dangling anchor, a row missing a column) and
`lint_roadmap` wraps the whole pass in a catch-all so a roadmap this checker
cannot make sense of still produces a finding instead of a traceback — a
linter that crashes in a gate cannot tell "found a problem" from "could not
look" (`LEARNINGS [FEAT-2026-0072/G1-CLOSE]`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import re

SEVERITY_ERROR = "error"
SEVERITY_WARN = "warn"

ROADMAP_FILENAME = "roadmap.md"
ARCHIVE_FILENAME = "roadmap-archive.md"

_ANCHOR_RE = re.compile(r'<a\s+id="(feat-\d{4}-\d{4})"\s*>\s*</a>', re.IGNORECASE)
_HEADING_RE = re.compile(r'^##\s+(FEAT-\d{4}-\d{4})\b', re.IGNORECASE)
_ROW_RE = re.compile(r'^\|\s*(FEAT-\d{4}-\d{4})\s*\|')
_LINK_RE = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
_REF_RE = re.compile(r'^(roadmap\.md|roadmap-archive\.md)?#(feat-\d{4}-\d{4})$', re.IGNORECASE)
_BLOCKED_BY_RE = re.compile(r'^\*\*Blocked by\.\*\*\s*(.*)$')
_ORPHAN_DETAIL_CELLS = {"—", "-", ""}
# A detail section's status marker. Trailing prose on the same line is common
# and intentional (`**Status: done.** <close commentary>`), so the pattern
# captures only the word (#465).
_SECTION_STATUS_RE = re.compile(r"^\*\*Status:\s*([a-z_]+)\.?\*\*", re.MULTILINE)


@dataclass(frozen=True)
class Finding:
    severity: str
    file: str
    line: int
    message: str


@dataclass
class _FileDoc:
    filename: str
    path: Path
    lines: list


def lint_roadmap(repo_root: Path) -> list:
    """Load roadmap.md + roadmap-archive.md as one link graph and return findings.

    Never raises: malformed input degrades to findings, per the module docstring.
    """
    try:
        return _lint_roadmap_impl(Path(repo_root))
    except Exception as exc:  # noqa: BLE001 - defensive backstop, a gate script must not crash
        return [Finding(
            SEVERITY_ERROR, ROADMAP_FILENAME, 0,
            f"lint_roadmap could not finish parsing ({exc!r}) — the roadmap or "
            "archive file is malformed beyond what this checker recovers from; "
            "fix the structure by hand and re-run",
        )]


def _lint_roadmap_impl(repo_root: Path) -> list:
    roadmap_path = repo_root / ".specfuse" / "roadmap.md"
    archive_path = repo_root / ".specfuse" / "roadmap-archive.md"

    roadmap_text = _read_text_safely(roadmap_path)
    if roadmap_text is None:
        return [Finding(
            SEVERITY_ERROR, ROADMAP_FILENAME, 0,
            f"{roadmap_path} not found — cannot lint the roadmap link graph",
        )]
    archive_text = _read_text_safely(archive_path)
    if archive_text is None:
        archive_text = ""

    roadmap_doc = _FileDoc(ROADMAP_FILENAME, roadmap_path, roadmap_text.splitlines())
    archive_doc = _FileDoc(ARCHIVE_FILENAME, archive_path, archive_text.splitlines())

    roadmap_anchors = _find_anchors(roadmap_doc.lines)
    archive_anchors = _find_anchors(archive_doc.lines)
    anchor_sets = {
        ROADMAP_FILENAME: {aid for _, aid in roadmap_anchors},
        ARCHIVE_FILENAME: {aid for _, aid in archive_anchors},
    }

    findings = []
    findings += _check_anchor_adjacency(roadmap_doc, roadmap_anchors)
    findings += _check_anchor_adjacency(archive_doc, archive_anchors)
    findings += _check_uniqueness(roadmap_anchors, archive_anchors)
    findings += _check_ref_resolution(roadmap_doc, anchor_sets)
    findings += _check_ref_resolution(archive_doc, anchor_sets)

    rows = _parse_table_rows(roadmap_doc.lines)
    findings += _check_blocked_by(roadmap_doc, archive_doc, rows)
    findings += _check_orphan_sections(roadmap_doc, archive_doc, rows)
    findings += _check_section_status(roadmap_doc, archive_doc, rows)

    return findings


def _read_text_safely(path: Path):
    try:
        return path.read_text()
    except OSError:
        return None


def _find_anchors(lines):
    """Return [(0-based line index, lowercase feat id), ...] in file order."""
    anchors = []
    for i, line in enumerate(lines):
        m = _ANCHOR_RE.search(line)
        if m:
            anchors.append((i, m.group(1).lower()))
    return anchors


def _find_headings(lines):
    """Return [(0-based line index, lowercase feat id), ...] in file order."""
    headings = []
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m:
            headings.append((i, m.group(1).lower()))
    return headings


def _check_anchor_adjacency(doc: _FileDoc, anchors) -> list:
    findings = []
    lines = doc.lines
    for i, aid in anchors:
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j >= len(lines):
            findings.append(Finding(
                SEVERITY_ERROR, doc.filename, i + 1,
                f"anchor '{aid}' has no heading anywhere after it in "
                f"{doc.filename} — add a '## {aid.upper()}' heading immediately "
                "after this anchor",
            ))
            continue
        if _ANCHOR_RE.search(lines[j]):
            findings.append(Finding(
                SEVERITY_ERROR, doc.filename, i + 1,
                f"anchor '{aid}' is immediately followed by another anchor, not "
                f"its heading — insert the '## {aid.upper()}' heading directly "
                "after this anchor",
            ))
            continue
        hm = _HEADING_RE.match(lines[j])
        if not hm:
            findings.append(Finding(
                SEVERITY_ERROR, doc.filename, i + 1,
                f"anchor '{aid}' is not immediately followed by a '## FEAT-…' "
                f"heading — add '## {aid.upper()}' directly after this anchor",
            ))
            continue
        hid = hm.group(1).lower()
        if hid != aid:
            findings.append(Finding(
                SEVERITY_ERROR, doc.filename, i + 1,
                f"anchor '{aid}' is immediately followed by the heading for "
                f"'{hid}', not its own — move this anchor directly above its "
                f"'## {aid.upper()}' heading",
            ))
    return findings


def _check_uniqueness(roadmap_anchors, archive_anchors) -> list:
    occurrences = {}
    for filename, anchors in (
        (ROADMAP_FILENAME, roadmap_anchors), (ARCHIVE_FILENAME, archive_anchors),
    ):
        for i, aid in anchors:
            occurrences.setdefault(aid, []).append((filename, i + 1))

    findings = []
    for aid, occ in occurrences.items():
        if len(occ) <= 1:
            continue
        files_used = {f for f, _ in occ}
        if len(files_used) > 1:
            for filename, line in occ:
                findings.append(Finding(
                    SEVERITY_ERROR, filename, line,
                    f"anchor '{aid}' is defined in both roadmap.md and "
                    "roadmap-archive.md — remove the duplicate and keep the "
                    "definition only in the file the feature currently belongs to",
                ))
        else:
            filename = occ[0][0]
            first_line = occ[0][1]
            for dup_filename, line in occ[1:]:
                findings.append(Finding(
                    SEVERITY_ERROR, dup_filename, line,
                    f"anchor '{aid}' is defined twice in {filename} (first at "
                    f"line {first_line}) — remove the duplicate anchor",
                ))
    return findings


def _check_ref_resolution(doc: _FileDoc, anchor_sets) -> list:
    findings = []
    for i, line in enumerate(doc.lines):
        for href in _LINK_RE.findall(line):
            href = href.strip()
            m = _REF_RE.match(href)
            if not m:
                continue
            prefix, fid = m.group(1), m.group(2).lower()
            if prefix:
                target_filename = (
                    ROADMAP_FILENAME if prefix.lower() == "roadmap.md" else ARCHIVE_FILENAME
                )
            else:
                target_filename = doc.filename

            if fid in anchor_sets.get(target_filename, ()):
                continue

            other_filename = ARCHIVE_FILENAME if target_filename == ROADMAP_FILENAME else ROADMAP_FILENAME
            if fid in anchor_sets.get(other_filename, ()):
                correct_form = f"#{fid}" if other_filename == doc.filename else f"{other_filename}#{fid}"
                message = (
                    f"ref '{href}' in {doc.filename} does not resolve — anchor "
                    f"'{fid}' is defined in {other_filename}, not {target_filename}; "
                    f"rewrite to '{correct_form}'"
                )
            else:
                message = (
                    f"ref '{href}' in {doc.filename} does not resolve — no anchor "
                    f"'{fid}' found in roadmap.md or roadmap-archive.md"
                )
            findings.append(Finding(SEVERITY_ERROR, doc.filename, i + 1, message))
    return findings


def _parse_table_rows(lines) -> list:
    """Parse `| FEAT-... | Title | Status | Folder | Detail |` rows.

    Tolerant of short/malformed rows (a missing column collapses to ""
    rather than raising) — malformed input must produce findings, not a
    traceback.
    """
    rows = []
    for i, line in enumerate(lines):
        m = _ROW_RE.match(line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        feature_id = cells[0] if len(cells) > 0 else m.group(1)
        status = cells[2] if len(cells) > 2 else ""
        detail = cells[4] if len(cells) > 4 else ""
        rows.append({"id": feature_id, "status": status, "detail": detail, "line": i + 1})
    return rows


def roadmap_statuses(repo_root=None) -> dict:
    """Map FEAT-ID -> status string, read from .specfuse/roadmap.md.

    Every feature row — including `done`, `abandoned`, and `deferred` ones —
    lives in roadmap.md; roadmap-archive.md holds only detail sections, never
    rows. Returns {} when roadmap.md is absent, rather than raising, so
    callers (e.g. a policy file present before a roadmap) can skip cleanly.
    """
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    roadmap_path = root / ".specfuse" / ROADMAP_FILENAME
    if not roadmap_path.is_file():
        return {}
    lines = roadmap_path.read_text(encoding="utf-8").splitlines()
    return {row["id"]: row["status"] for row in _parse_table_rows(lines)}


def _detail_sections(lines) -> dict:
    """Map lowercase feat id -> (heading_idx, body_start_idx, body_end_idx).

    A section's body runs from just after its `## FEAT-…` heading up to
    (not including) the next heading or anchor line — whichever comes
    first — mirroring the shape `auto_archive_feature` moves, but computed
    independently rather than shared with it.
    """
    headings = _find_headings(lines)
    anchor_positions = {i for i, _ in _find_anchors(lines)}
    sections = {}
    for idx, fid in headings:
        end = len(lines)
        for j in range(idx + 1, len(lines)):
            if j in anchor_positions or _HEADING_RE.match(lines[j]):
                end = j
                break
        sections[fid] = (idx, idx + 1, end)
    return sections


def _find_blocked_by(section, lines):
    _heading_idx, body_start, body_end = section
    for j in range(body_start, body_end):
        m = _BLOCKED_BY_RE.match(lines[j].strip())
        if m:
            return j, m.group(1)
    return None, None


def _check_blocked_by(roadmap_doc: _FileDoc, archive_doc: _FileDoc, rows) -> list:
    findings = []
    roadmap_sections = _detail_sections(roadmap_doc.lines)
    archive_sections = _detail_sections(archive_doc.lines)

    for row in rows:
        fid = row["id"].lower()
        status = row["status"].strip().lower()

        if fid in roadmap_sections:
            doc, section = roadmap_doc, roadmap_sections[fid]
        elif fid in archive_sections:
            doc, section = archive_doc, archive_sections[fid]
        else:
            doc, section = None, None

        blocked_by_line = blocked_by_text = None
        if section is not None:
            blocked_by_line, blocked_by_text = _find_blocked_by(section, doc.lines)

        if status == "blocked":
            if section is None:
                findings.append(Finding(
                    SEVERITY_ERROR, roadmap_doc.filename, row["line"],
                    f"{row['id']} has status: blocked but no detail section was "
                    "found in roadmap.md or roadmap-archive.md — add one with a "
                    "'**Blocked by.**' block naming the blocker",
                ))
                continue
            if blocked_by_text is None:
                findings.append(Finding(
                    SEVERITY_ERROR, doc.filename, section[0] + 1,
                    f"{row['id']}'s detail section has status: blocked but no "
                    "'**Blocked by.**' block — add one naming at least one blocker",
                ))
                continue
            links = [h.strip() for h in _LINK_RE.findall(blocked_by_text)]
            if not links:
                findings.append(Finding(
                    SEVERITY_ERROR, doc.filename, blocked_by_line + 1,
                    f"{row['id']}'s '**Blocked by.**' block has no links — add at "
                    "least one resolvable blocker link",
                ))
                continue
            for href in links:
                if _REF_RE.match(href):
                    continue  # feat-ref resolution is covered by _check_ref_resolution
                parsed = urlparse(href)
                if parsed.scheme in ("http", "https") and parsed.netloc:
                    continue
                target = (doc.path.parent / href).resolve()
                if not target.exists():
                    findings.append(Finding(
                        SEVERITY_ERROR, doc.filename, blocked_by_line + 1,
                        f"{row['id']}'s Blocked-by link '{href}' does not resolve "
                        "to a file on disk and is not a well-formed URL — fix the "
                        "path",
                    ))
        else:
            if blocked_by_text is not None:
                findings.append(Finding(
                    SEVERITY_WARN, doc.filename, blocked_by_line + 1,
                    f"{row['id']} has a '**Blocked by.**' block but status is "
                    f"'{row['status']}', not blocked — remove the block or set "
                    "status: blocked",
                ))
    return findings


def _check_section_status(roadmap_doc: _FileDoc, archive_doc: _FileDoc, rows) -> list:
    """A detail section's `**Status:**` must agree with its table row (#465).

    The row is authoritative -- `fire_terminal_flips` owns it and deliberately
    does not touch section prose, which is a human record. So a section only
    stays accurate if its feature's close ceremony had a criterion naming it,
    and the closes that lacked one drifted: 21 of 42 archived sections
    disagreed with their rows before #464 repaired them by hand.

    ERROR rather than WARN, unlike the orphan-detail check. An orphan section
    is untidy; a section stating `active` under a row saying `done` means the
    roadmap asserts two different facts about one feature and a reader has no
    way to tell which is authoritative -- the same resolvable-but-wrong shape
    the duplicate-anchor check exists for.

    An ABSENT status line is not a finding. Nine real sections carry none, and
    whether the line is mandatory is a close-discipline.md contract question
    this check must not settle by fiat.
    """
    findings = []
    by_file = (
        (roadmap_doc, _detail_sections(roadmap_doc.lines)),
        (archive_doc, _detail_sections(archive_doc.lines)),
    )
    for row in rows:
        row_status = row["status"].strip().lower()
        if not row_status:
            continue
        fid = row["id"].lower()
        for doc, sections in by_file:
            if fid not in sections:
                continue
            _, body_start, body_end = sections[fid]
            body = "\n".join(doc.lines[body_start:body_end])
            m = _SECTION_STATUS_RE.search(body)
            if m is None:
                continue
            section_status = m.group(1).lower()
            if section_status == row_status:
                continue
            offset = body[:m.start()].count("\n")
            findings.append(Finding(
                SEVERITY_ERROR, doc.filename, body_start + offset + 1,
                f"{row['id']}'s detail section says '**Status: {section_status}.**' "
                f"but its roadmap row says '{row_status}' \u2014 the row is "
                f"authoritative; rewrite the section marker to "
                f"'**Status: {row_status}.**' and keep any prose after it",
            ))
    return findings


def _check_orphan_sections(roadmap_doc: _FileDoc, archive_doc: _FileDoc, rows) -> list:
    findings = []
    roadmap_sections = _detail_sections(roadmap_doc.lines)
    archive_sections = _detail_sections(archive_doc.lines)

    for row in rows:
        if row["detail"].strip() not in _ORPHAN_DETAIL_CELLS:
            continue
        fid = row["id"].lower()
        if fid in roadmap_sections:
            location = roadmap_doc.filename
        elif fid in archive_sections:
            location = archive_doc.filename
        else:
            continue
        findings.append(Finding(
            SEVERITY_WARN, ROADMAP_FILENAME, row["line"],
            f"{row['id']}'s Detail cell is '{row['detail']}' but a detail section "
            f"already exists in {location} — link it, e.g. '[→ detail](#{fid})' "
            f"or '[→ archive](roadmap-archive.md#{fid})'",
        ))
    return findings
