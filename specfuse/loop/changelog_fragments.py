#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Changelog fragments — FEAT-LOOP-2026-0249.

One writer for changelog entries. `add` routes by `changelog.mode` in
`.specfuse/layout.yml`: `fragments` writes `changelog.d/<trace>-<slug>.md`
(so concurrent PRs never touch the same file), `single` (the default) appends
to `CHANGELOG.md` through `changelog.append_entry`.

    python3 -m specfuse.loop.changelog_fragments add --class C --trace T --summary S [--repo DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from specfuse.loop import layout
from specfuse.loop.changelog import _TRACE_RE, ENTRY_CLASSES, ChangelogEntry, append_entry

FRAGMENT_DIR = "changelog.d"
CHANGELOG_FILE = "CHANGELOG.md"
_SLUG_MAX = 40


def normalize_trace(trace: str) -> str:
    """`#3563` -> `3563`, `FEAT-X/T01` -> `FEAT-X-T01`."""
    return trace.lstrip("#").replace("/", "-")


def slugify(summary: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", summary.lower()).strip("-")[:_SLUG_MAX].strip("-")
    return slug or "entry"


def _validate(entry_class: str, trace: str, summary: str) -> None:
    if entry_class not in ENTRY_CLASSES:
        raise ValueError(
            f"unrecognised entry class {entry_class!r} — must be one of "
            f"{', '.join(ENTRY_CLASSES)}"
        )
    if not _TRACE_RE.match(trace):
        raise ValueError(f"trace {trace!r} is not a FEAT-YYYY-NNNN or #<issue-number> trace")
    if not summary.strip():
        raise ValueError("summary must not be empty")
    if "\n" in summary or "\r" in summary:
        raise ValueError("summary must be a single line")


def read_fragment(path) -> ChangelogEntry | None:
    """The entry one fragment file carries, or None when it is not a valid fragment.

    Frontmatter is read line by line, not through `_miniyaml`: `trace: #101`
    is a comment to a YAML reader. Never raises on a malformed file.
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        key, sep, value = line.partition(":")
        if not sep:
            return None
        fields[key.strip()] = value.strip()
    entry_class, trace = fields.get("class", ""), fields.get("trace", "")
    body = [ln.strip() for ln in lines[end + 1:] if ln.strip()]
    if entry_class not in ENTRY_CLASSES or not _TRACE_RE.match(trace) or len(body) != 1:
        return None
    return ChangelogEntry(entry_class=entry_class, summary=body[0], trace=trace, line=end + 2)


def fragment_entries(repo_root) -> list:
    """Every valid fragment's entry under `changelog.d/`; malformed files are skipped."""
    directory = Path(repo_root) / FRAGMENT_DIR
    if not directory.is_dir():
        return []
    found = (read_fragment(p) for p in sorted(directory.glob("*.md")))
    return [entry for entry in found if entry is not None]


def add(repo_root, *, entry_class: str, trace: str, summary: str) -> Path:
    """Write one entry in the project's mode; return the file written."""
    _validate(entry_class, trace, summary)
    summary = summary.strip()
    root = Path(repo_root)
    if layout.load(root).changelog.mode == "fragments":
        target = root / FRAGMENT_DIR / f"{normalize_trace(trace)}-{slugify(summary)}.md"
        if target.exists():
            raise ValueError(f"{target.relative_to(root).as_posix()} already exists")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            f"---\nclass: {entry_class}\ntrace: {trace}\n---\n{summary}\n", encoding="utf-8"
        )
        return target
    path = root / CHANGELOG_FILE
    if not path.is_file():
        raise ValueError(f"{CHANGELOG_FILE} not found in {root}")
    text = path.read_text(encoding="utf-8")
    path.write_text(
        append_entry(text, entry_class=entry_class, summary=summary, trace=trace),
        encoding="utf-8",
    )
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="specfuse.loop.changelog_fragments", description="Write changelog entries."
    )
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    addp = sub.add_parser("add", help="write one changelog entry in the project's mode")
    addp.add_argument("--class", dest="entry_class", required=True)
    addp.add_argument("--trace", required=True)
    addp.add_argument("--summary", required=True)
    args = parser.parse_args(argv)

    try:
        target = add(
            args.repo,
            entry_class=args.entry_class,
            trace=args.trace,
            summary=args.summary,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
