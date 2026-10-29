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
    python3 -m specfuse.loop.ids [--repo DIR] migrate --planned-only [--apply]
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


_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_CODE_SPAN_RE = re.compile(r"(`[^`]*`)")
_ID_BOUNDARY = r"(?![\w-])"


@dataclass
class MigrationPlan:
    candidates: list  # [(old_id, new_id)]
    skipped: list  # [(id, reason)]
    unplaced: list  # [(file, line_no, old_id)] refs left alone (code spans/blocks)


def _status_column(lines) -> int:
    for line in lines:
        if line.lstrip().startswith("|") and "status" in line.lower() and "id" in line.lower():
            cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
            if "status" in cells:
                return cells.index("status")
    return 2


def _roadmap_rows(repo_root: Path):
    """Yield (id_text, status) for every roadmap table row, both files."""
    for name in ROADMAP_FILES:
        path = repo_root / ".specfuse" / name
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        col = _status_column(lines)
        for line in lines:
            m = _ROW_ID_RE.match(line)
            if not m:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            status = cells[col].strip("*_` ").lower() if len(cells) > col else ""
            yield m.group(1), status


def _has_folder(repo_root: Path, feature_id: str) -> bool:
    features = repo_root / ".specfuse" / "features"
    return features.is_dir() and any(features.glob(f"{feature_id}-*"))


def plan_migration(repo_root, key: str) -> MigrationPlan:
    root = Path(repo_root)
    rows = list(_roadmap_rows(root))
    present = {fid for fid, _ in rows}
    candidates, skipped, seen = [], [], set()
    for fid, status in rows:
        if fid in seen:
            continue
        seen.add(fid)
        parsed = parse(fid)
        if parsed is None:
            continue
        if parsed.key:
            skipped.append((fid, "already keyed"))
        elif status != "planned":
            skipped.append((fid, f"status is {status or 'unknown'}, not planned"))
        elif _has_folder(root, fid):
            skipped.append((fid, "has a feature folder"))
        elif str(FeatureId(key, parsed.year, parsed.ordinal)) in present:
            skipped.append((fid, "keyed ID already in the roadmap"))
        else:
            candidates.append((fid, str(FeatureId(key, parsed.year, parsed.ordinal))))
    plan = MigrationPlan(candidates, skipped, [])
    for name in ROADMAP_FILES:
        path = root / ".specfuse" / name
        if path.is_file():
            _, unplaced = _rewrite(path.read_text(encoding="utf-8"), candidates, name)
            plan.unplaced.extend(unplaced)
    return plan


def _rewrite(text: str, candidates, filename: str):
    """Re-key table row IDs, headings, anchors and `#feat-` refs; returns (text, unplaced)."""
    unplaced = []
    out = []
    in_fence = False
    for no, line in enumerate(text.splitlines(keepends=True), 1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        for old, new in candidates:
            old_l = old.lower()
            if in_fence:
                if old in line or old_l in line:
                    unplaced.append((filename, no, old))
                continue
            parts = _CODE_SPAN_RE.split(line)
            for i, part in enumerate(parts):
                if i % 2:  # inline code span: report, leave alone
                    if old in part or old_l in part:
                        unplaced.append((filename, no, old))
                    continue
                subs = (
                    (r"^(\|\s*)" + re.escape(old) + r"(\s*\|)", r"\g<1>" + new + r"\g<2>"),
                    (r"^(##\s+)" + re.escape(old) + _ID_BOUNDARY, r"\g<1>" + new),
                    (
                        r'(<a\s+id=")' + re.escape(old_l) + r'(")',
                        r"\g<1>" + new.lower() + r"\g<2>",
                    ),
                    (r"(#)" + re.escape(old_l) + _ID_BOUNDARY, r"\g<1>" + new.lower()),
                )
                for pattern, repl in subs:
                    part = re.sub(pattern, repl, part)
                parts[i] = part
            line = "".join(parts)
        out.append(line)
    return "".join(out), unplaced


def migrate(repo_root, apply: bool = False, out=None) -> int:
    from specfuse.loop import layout

    out = out or sys.stdout
    root = Path(repo_root)
    key = layout.load(root).ids.key
    if not key:
        print(
            "ids migrate: no project key set; configure `ids.key` in .specfuse/layout.yml first",
            file=sys.stderr,
        )
        return 2
    plan = plan_migration(root, key)
    print(f"{'apply' if apply else 'dry run'}: key {key}", file=out)
    for old, new in plan.candidates:
        print(f"  rekey  {old} -> {new}", file=out)
    for fid, reason in plan.skipped:
        print(f"  skip   {fid}: {reason}", file=out)
    for filename, no, old in plan.unplaced:
        print(f"  unplaced ref to {old} at {filename}:{no} (code span/block, left unchanged)", file=out)
    if not plan.candidates:
        print("no candidates", file=out)
    elif apply:
        for name in ROADMAP_FILES:
            path = root / ".specfuse" / name
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                new_text, _ = _rewrite(text, plan.candidates, name)
                if new_text != text:
                    path.write_text(new_text, encoding="utf-8")
        print(f"rewrote {len(plan.candidates)} row(s)", file=out)
    else:
        print("nothing written; re-run with --apply", file=out)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="specfuse.loop.ids", description="Allocate and parse feature IDs."
    )
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    nextp = sub.add_parser("next", help="print the next free feature ID")
    nextp.add_argument("--year", type=int, default=None)
    mig = sub.add_parser("migrate", help="re-key folderless planned roadmap rows")
    mig.add_argument("--planned-only", action="store_true", required=True)
    mig.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    args = parser.parse_args(argv)
    if args.command == "next":
        print(next_id(args.repo, args.year))
    elif args.command == "migrate":
        return migrate(args.repo, apply=args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
