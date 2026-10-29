#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Feature-ID grammar and allocation — FEAT-2026-0247 (project-keyed feature IDs).

One module owns the feature-ID grammar so no site carries its own literal. A
feature ID is `FEAT-YYYY-NNNN` (legacy) or `FEAT-<KEY>-YYYY-NNNN` where
`<KEY>` is the project key configured as `ids.key` in `.specfuse/layout.yml`.

Standalone like `layout.py`: must not import the driver.

    python3 -m specfuse.loop.ids [--repo DIR] next [--year YYYY]
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

KEY_PATTERN = r"[A-Z][A-Z0-9]{1,5}"
KEY_RE = re.compile(r"^" + KEY_PATTERN + r"$")

# Un-anchored source string other regexes embed; the key group is non-capturing.
FEATURE_ID_PATTERN = r"FEAT-(?:" + KEY_PATTERN + r"-)?\d{4}-\d{4}"
FEATURE_ID_RE = re.compile(r"^" + FEATURE_ID_PATTERN + r"$")

_PARSE_RE = re.compile(r"^FEAT-(?:(" + KEY_PATTERN + r")-)?(\d{4})-(\d{4})(?:-.+)?$")
_ROW_ID_RE = re.compile(r"^\|\s*(" + FEATURE_ID_PATTERN + r")\s*\|")
_PLAN_ID_RE = re.compile(r"^feature_id:\s*[\"']?(" + FEATURE_ID_PATTERN + r")", re.MULTILINE)

ROADMAP_FILES = ("roadmap.md", "roadmap-archive.md")


@dataclass(frozen=True)
class FeatureId:
    key: Optional[str]
    year: int
    ordinal: int

    def __str__(self) -> str:
        prefix = f"FEAT-{self.key}-" if self.key else "FEAT-"
        return f"{prefix}{self.year:04d}-{self.ordinal:04d}"


def parse(text) -> Optional[FeatureId]:
    """FeatureId from an ID or a folder name (`<ID>-<slug>`); None otherwise."""
    m = _PARSE_RE.match(text or "")
    if not m:
        return None
    return FeatureId(m.group(1), int(m.group(2)), int(m.group(3)))


def anchor(feature_id) -> str:
    """Roadmap anchor for an ID: its lower-cased form."""
    return str(feature_id).lower()


def sort_key(feature_id):
    """Order by year, then ordinal, then key (legacy before keyed on a tie)."""
    parsed = feature_id if isinstance(feature_id, FeatureId) else parse(feature_id)
    if parsed is None:
        return (0, 0, "")
    return (parsed.year, parsed.ordinal, parsed.key or "")


def _existing_ids(repo_root: Path):
    specfuse = repo_root / ".specfuse"
    for name in ROADMAP_FILES:
        path = specfuse / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _ROW_ID_RE.match(line)
            if m:
                yield parse(m.group(1))
    features = specfuse / "features"
    if features.is_dir():
        for plan in features.glob("*/PLAN.md"):
            m = _PLAN_ID_RE.search(plan.read_text(encoding="utf-8", errors="replace"))
            if m:
                yield parse(m.group(1))


def next_id(repo_root, year: Optional[int] = None) -> str:
    """Next free ID for `year`: max ordinal across both forms, plus one."""
    from specfuse.loop import layout

    root = Path(repo_root)
    year = datetime.date.today().year if year is None else year
    highest = max(
        (f.ordinal for f in _existing_ids(root) if f is not None and f.year == year),
        default=0,
    )
    return str(FeatureId(layout.load(root).ids.key, year, highest + 1))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="specfuse.loop.ids", description="Allocate and parse feature IDs."
    )
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    nextp = sub.add_parser("next", help="print the next free feature ID")
    nextp.add_argument("--year", type=int, default=None)
    args = parser.parse_args(argv)
    if args.command == "next":
        print(next_id(args.repo, args.year))
    return 0


if __name__ == "__main__":
    sys.exit(main())
