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
    python3 -m specfuse.loop.ids [--repo DIR] migrate --all [--apply] [--include-prose]
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
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


# --- migrate --all (FEAT-2026-0247/T08) -------------------------------------

ALIASES_FILE = "id-aliases.yml"
_ALL_BOUNDARY = r"(?!\w)(?!-\d)"  # whole ID; `-slug` (folder name) still matches


@dataclass
class AllPlan:
    renames: list  # [(old_id, new_id)]
    skipped: list  # [(id, reason)]
    moves: list  # [(old_folder_name, new_folder_name)]
    files: dict  # {relpath: new_text}
    counts: dict  # {relpath: {old_id: n}}
    changelog_skipped: list  # ["## [0.30.0] ..." headings left alone]
    ambiguous: list  # [(relpath, line_no, old_id)] prose mentions


def _tracked_text_files(root: Path):
    r = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=False
    )
    for rel in r.stdout.decode("utf-8", "replace").split("\0"):
        path = root / rel
        if not rel or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        try:
            yield rel, data.decode("utf-8")
        except UnicodeDecodeError:
            continue


def _own_unkeyed_ids(root: Path, key: str):
    """(renames, skipped): unkeyed IDs with a feature folder or a roadmap row."""
    found = {}
    features = root / ".specfuse" / "features"
    if features.is_dir():
        for folder in sorted(features.iterdir()):
            parsed = parse(folder.name) if folder.is_dir() else None
            if parsed is not None:
                found[str(parsed) if not parsed.key else folder.name] = parsed
    for fid, _ in _roadmap_rows(root):
        parsed = parse(fid)
        if parsed is not None:
            found[fid] = parsed
    existing = {str(p) for p in found.values() if p.key}
    renames, skipped = [], []
    for fid in sorted(found):
        parsed = found[fid]
        if parsed.key:
            continue
        new = str(FeatureId(key, parsed.year, parsed.ordinal))
        if new in existing:
            skipped.append((fid, "keyed ID already exists"))
        else:
            renames.append((fid, new))
    return renames, skipped


def _frontmatter_end(lines) -> int:
    """Index of the closing `---` of a leading frontmatter block, else -1."""
    if not lines or lines[0].strip() != "---":
        return -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i
    return -1


def _task_graph_lines(lines) -> set:
    """Line indexes inside the PLAN.md yaml block with a top-level `gates:` key."""
    found, start = set(), None
    for i, line in enumerate(lines):
        if start is None:
            if re.match(r"^```ya?ml\s*$", line):
                start = i
        elif line.startswith("```"):
            body = lines[start + 1 : i]
            if any(ln.startswith("gates:") for ln in body):
                found.update(range(start + 1, i))
            start = None
    return found


def _unreleased_span(lines):
    """(start, end) line indexes of CHANGELOG's Unreleased section; None if absent."""
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+\[?Unreleased", line, re.IGNORECASE):
            start = i
        elif start is not None and re.match(r"^##\s", line):
            return start, i
    return (start, len(lines)) if start is not None else None


def _rewrite_line(line, old, new, structural, anchors, events, prose, where):
    """Rewrite `old` -> `new` in one line; ambiguous prose matches are recorded."""
    rel, no, plan = where

    def replace(repl, is_structural):
        def sub(m):
            if is_structural(m.string, m.start()) or prose:
                plan.counts.setdefault(rel, {}).setdefault(old, 0)
                plan.counts[rel][old] += 1
                return repl
            plan.ambiguous.append((rel, no, old))
            return m.group(0)

        return sub

    def upper(text, start):
        if structural or text[:start].endswith("features/"):
            return True
        return events and bool(re.search(r'"correlation_id"\s*:\s*"$', text[:start]))

    def lower(text, start):  # anchors and `#feat-` refs
        return anchors and (text[:start].endswith("#") or text[:start].endswith('id="'))

    tail = _ALL_BOUNDARY
    line = re.sub(r"(?<!\w)" + re.escape(old) + tail, replace(new, upper), line)
    return re.sub(
        r"(?<!\w)" + re.escape(old.lower()) + tail, replace(new.lower(), lower), line
    )


def _rewrite_file(rel, text, renames, include_prose, plan):
    """Rewrite one file; structural matches always, prose only with include_prose."""
    name = Path(rel).name
    is_md = name.endswith(".md")
    is_roadmap = rel in (f".specfuse/{n}" for n in ROADMAP_FILES)
    is_events = name == "events.jsonl"
    in_features = rel.startswith(".specfuse/features/")
    is_changelog = rel == "CHANGELOG.md"
    lines = text.splitlines(keepends=True)
    bare = [ln.rstrip("\r\n") for ln in lines]
    fm_end = _frontmatter_end(bare) if is_md and in_features else -1
    graph = _task_graph_lines(bare) if name == "PLAN.md" and in_features else set()
    span = _unreleased_span(bare) if is_changelog else None
    if is_changelog and span is None:
        span = (len(lines), len(lines))
    pairs = [(o, n) for o, n in renames]
    out, fenced = [], False
    for no, line in enumerate(lines):
        if is_changelog and not (span[0] <= no < span[1]):
            if re.match(r"^##\s", line):
                plan.changelog_skipped.append(line.strip())
            out.append(line)
            continue
        if _FENCE_RE.match(line):
            fenced = not fenced
        row = bool(is_roadmap and _ROW_ID_RE.match(line))
        heading = bool(is_roadmap and re.match(r"^#{1,6}\s", line))
        frontmatter = no <= fm_end or no in graph
        for old, new in pairs:
            line = _rewrite_line(
                line, old, new,
                structural=row or heading or frontmatter,
                anchors=is_roadmap or frontmatter,
                events=is_events,
                prose=include_prose and not fenced,
                where=(rel, no + 1, plan),
            )
        out.append(line)
    return "".join(out)


def plan_migrate_all(root, key: str, include_prose: bool = False) -> AllPlan:
    root = Path(root)
    renames, skipped = _own_unkeyed_ids(root, key)
    plan = AllPlan(renames, skipped, [], {}, {}, [], [])
    if not renames:
        return plan
    for rel, text in _tracked_text_files(root):
        new_text = _rewrite_file(rel, text, renames, include_prose, plan)
        if new_text != text:
            plan.files[rel] = new_text
    features = root / ".specfuse" / "features"
    if features.is_dir():
        for old, new in renames:
            for folder in sorted(features.glob(f"{old}-*")):
                plan.moves.append((folder.name, new + folder.name[len(old):]))
    plan.ambiguous = sorted(set(plan.ambiguous))
    plan.changelog_skipped = list(dict.fromkeys(plan.changelog_skipped))
    return plan


def _dirty(root: Path) -> bool:
    r = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    return bool(r.stdout.strip())


def _append_aliases(root: Path, renames) -> None:
    path = root / ".specfuse" / ALIASES_FILE
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    have = {ln.split(":")[0].strip() for ln in existing.splitlines() if ":" in ln}
    add = "".join(f"{o}: {n}\n" for o, n in renames if o not in have)
    if add:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        path.write_text(existing + add, encoding="utf-8")


def migrate_all(repo_root, apply: bool = False, include_prose: bool = False, out=None) -> int:
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
    lock = None
    if apply:
        from specfuse.loop import _filelock

        try:
            lock = _filelock.acquire_tree_lock(root / ".specfuse")
        except BlockingIOError:
            print(
                "ids migrate: a loop driver holds .specfuse/.loop.lock; stop it first",
                file=sys.stderr,
            )
            return 2
    try:
        plan = plan_migrate_all(root, key, include_prose)
        print(f"{'apply' if apply else 'dry run'}: key {key}", file=out)
        for old, new in plan.renames:
            print(f"  rekey  {old} -> {new}", file=out)
        for fid, reason in plan.skipped:
            print(f"  skip   {fid}: {reason}", file=out)
        for old, new in plan.moves:
            print(f"  move   .specfuse/features/{old} -> .specfuse/features/{new}", file=out)
        for rel in sorted(plan.counts):
            for old, n in sorted(plan.counts[rel].items()):
                print(f"  edit   {rel}: {n} x {old}", file=out)
        for heading in plan.changelog_skipped:
            print(f"  skip   CHANGELOG.md: released section `{heading}` (append-only)", file=out)
        for rel, no, old in plan.ambiguous:
            print(
                f"  prose  {rel}:{no}: {old} (may cite another repository; "
                f"{'left unchanged' if apply else 'rewritten only with --include-prose'})",
                file=out,
            )
        if not plan.renames:
            print("nothing to do", file=out)
            return 0
        if not apply:
            print("nothing written; re-run with --apply", file=out)
            return 0
        if _dirty(root):
            print(
                "ids migrate: working tree has uncommitted changes; commit or stash first",
                file=sys.stderr,
            )
            return 2
        for rel, text in plan.files.items():
            (root / rel).write_text(text, encoding="utf-8")
        for old, new in plan.moves:
            subprocess.run(
                ["git", "mv", f".specfuse/features/{old}", f".specfuse/features/{new}"],
                cwd=root, check=True, capture_output=True,
            )
        _append_aliases(root, plan.renames)
        print(f"re-keyed {len(plan.renames)} feature(s); alias map .specfuse/{ALIASES_FILE}", file=out)
        return 0
    finally:
        if lock is not None:
            lock.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="specfuse.loop.ids", description="Allocate and parse feature IDs."
    )
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    nextp = sub.add_parser("next", help="print the next free feature ID")
    nextp.add_argument("--year", type=int, default=None)
    mig = sub.add_parser("migrate", help="re-key folderless planned roadmap rows")
    which = mig.add_mutually_exclusive_group(required=True)
    which.add_argument("--planned-only", action="store_true")
    which.add_argument("--all", action="store_true", help="re-key every feature of this repository")
    mig.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    mig.add_argument(
        "--include-prose", action="store_true",
        help="with --all --apply, also rewrite ambiguous prose mentions",
    )
    args = parser.parse_args(argv)
    if args.command == "next":
        print(next_id(args.repo, args.year))
    elif args.command == "migrate":
        if args.all:
            return migrate_all(args.repo, apply=args.apply, include_prose=args.include_prose)
        if args.include_prose:
            parser.error("--include-prose requires --all")
        return migrate(args.repo, apply=args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
