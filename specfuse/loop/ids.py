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
    python3 -m specfuse.loop.ids [--repo DIR] migrate --all [--apply] [--include-prose [PATH ...]]
        [--exclude-id ID ...]
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
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


def _exists(repo_root: Path, feature_id: str) -> bool:
    """A folder under features/ or a row in either roadmap file."""
    return _has_folder(repo_root, feature_id) or any(
        fid == feature_id for fid, _ in _roadmap_rows(repo_root)
    )


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
            old_l = anchor(old)
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
                        r"\g<1>" + anchor(new) + r"\g<2>",
                    ),
                    (r"(#)" + re.escape(old_l) + _ID_BOUNDARY, r"\g<1>" + anchor(new)),
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


def _rewrite_line(line, old, new, structural, anchors, events, prose, where, folders=()):
    """Rewrite `old` -> `new` in one line; ambiguous prose matches are recorded.

    An exact existing folder name (`folders`) is structural wherever it appears,
    with or without a leading `features/`; any other `<old>-<slug>` is prose.
    """
    rel, no, plan = where

    def replace(repl, is_structural):
        def sub(m):
            if is_structural(m.string, m.start(), m.end()) or prose:
                plan.counts.setdefault(rel, {}).setdefault(old, 0)
                plan.counts[rel][old] += 1
                return repl
            plan.ambiguous.append((rel, no, old))
            return m.group(0)

        return sub

    def upper(text, start, end):
        if structural:
            return True
        rest = text[start:]
        for name in folders:
            if rest.startswith(name) and not re.match(r"[\w-]", rest[len(name):][:1]):
                return True
        return events and bool(re.search(r'"correlation_id"\s*:\s*"$', text[:start]))

    def lower(text, start, end):  # anchors and `#feat-` refs
        return anchors and (text[:start].endswith("#") or text[:start].endswith('id="'))

    tail = _ALL_BOUNDARY
    line = re.sub(r"(?<!\w)" + re.escape(old) + tail, replace(new, upper), line)
    return re.sub(
        r"(?<!\w)" + re.escape(anchor(old)) + tail, replace(anchor(new), lower), line
    )


def _rewrite_file(rel, text, renames, include_prose, plan, folders=()):
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
                folders=[f for f in folders if f.startswith(old + "-")],
            )
        out.append(line)
    return "".join(out)


def _prose_scope(include_prose):
    """Predicate rel -> bool: True/False for all/none, a list of paths or globs to scope."""
    if include_prose is True or not include_prose:
        return lambda rel: bool(include_prose)
    patterns = [p.strip("/") if not any(c in p for c in "*?[") else p for p in include_prose]
    return lambda rel: any(
        fnmatch.fnmatchcase(rel, p) or rel.startswith(p.rstrip("/") + "/") for p in patterns
    )


def plan_migrate_all(
    root, key: str, include_prose=False, exclude_ids=()
) -> AllPlan:
    root = Path(root)
    renames, skipped = _own_unkeyed_ids(root, key)
    excluded = set(exclude_ids)
    if excluded:
        skipped = skipped + [
            (old, "excluded by operator") for old, _ in renames if old in excluded
        ]
        renames = [(o, n) for o, n in renames if o not in excluded]
    in_scope = _prose_scope(include_prose)
    plan = AllPlan(renames, skipped, [], {}, {}, [], [])
    if not renames:
        return plan
    features = root / ".specfuse" / "features"
    folders = sorted(p.name for p in features.iterdir() if p.is_dir()) if features.is_dir() else []
    for rel, text in _tracked_text_files(root):
        new_text = _rewrite_file(rel, text, renames, in_scope(rel), plan, folders)
        if new_text != text:
            plan.files[rel] = new_text
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


def read_aliases(repo_root) -> dict:
    """`{old_id: new_id}` from `.specfuse/id-aliases.yml`; `{}` when absent."""
    path = Path(repo_root) / ".specfuse" / ALIASES_FILE
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0]
        old, sep, new = line.partition(":")
        if sep and old.strip() and new.strip():
            out[old.strip()] = new.strip().strip("'\"")
    return out


def resolve(repo_root, feature_id, err=None) -> str:
    """The ID itself when it has a folder or roadmap row, else its alias target (one hop).

    No alias map, no alias entry, or an alias whose target has neither a
    folder nor a roadmap row all return *feature_id* unchanged; the last case is reported on *err*
    (default stderr) rather than followed into an error.
    """
    if not isinstance(feature_id, str) or _exists(Path(repo_root), feature_id):
        return feature_id
    target = read_aliases(repo_root).get(feature_id)
    if target is None:
        return feature_id
    if not _exists(Path(repo_root), target):
        print(
            f"WARNING: {ALIASES_FILE} maps {feature_id} to {target}, "
            f"which has no feature folder or roadmap row",
            file=err or sys.stderr,
        )
        return feature_id
    return target


def _validate_tree_here(root: Path) -> list:
    """ERROR lines from lint_plan, lint_roadmap and agent-policy validation, in-process."""
    from specfuse.loop import agent_policy, lint_plan, lint_roadmap

    errors = []
    features = root / ".specfuse" / "features"
    if features.is_dir():
        # Only `<ID>-<slug>` folders are features; harness dot-dirs and notes are not (#3554).
        for folder in sorted(
            p for p in features.iterdir() if p.is_dir() and parse(p.name) is not None
        ):
            errors.extend(
                f"ERROR: {folder.name}: {e}"
                for e in lint_plan.lint(folder)
                if not e.startswith("WARN")
            )
    for f in lint_roadmap.lint_roadmap(root):
        if f.severity == lint_roadmap.SEVERITY_ERROR:
            errors.append(f"ERROR: {f.file}:{f.line}: {f.message}")
    policy = root / ".specfuse" / "agent-policy.yml"
    if policy.is_file():
        errors.extend(
            e for e in agent_policy.validate_agent_policy(policy, repo_root=root)
            if e.startswith("ERROR")
        )
    return errors


def _validate_tree(root: Path) -> list:
    """ERROR lines judged by *root*'s own linters, run in a fresh interpreter.

    The renamed tree may carry code tables keyed by feature folder names; modules
    already imported here belong to another checkout and would judge it by the
    old names.
    """
    import os

    root = Path(root).resolve()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    r = subprocess.run(
        [sys.executable, "-m", "specfuse.loop.ids", "--repo", str(root), "validate"],
        cwd=root, env=env, capture_output=True, text=True, check=False,
    )
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith("ERROR")]
    if r.returncode != 0 and not lines:
        tail = (r.stderr.strip().splitlines() or ["no output"])[-1]
        lines = [f"ERROR: validation process exited {r.returncode}: {tail}"]
    return lines


def _append_aliases(root: Path, renames) -> None:
    path = root / ".specfuse" / ALIASES_FILE
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    have = {ln.split(":")[0].strip() for ln in existing.splitlines() if ":" in ln}
    add = "".join(f"{o}: {n}\n" for o, n in renames if o not in have)
    if add:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        path.write_text(existing + add, encoding="utf-8")


def migrate_all(
    repo_root, apply: bool = False, include_prose=False, out=None, exclude_ids=()
) -> int:
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
        plan = plan_migrate_all(root, key, include_prose, exclude_ids)
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
        if plan.ambiguous:
            tops = {}
            for rel, _, _ in plan.ambiguous:
                top = rel.split("/", 1)[0] if "/" in rel else "."
                tops[top] = tops.get(top, 0) + 1
            summary = ", ".join(f"{t}: {n}" for t, n in sorted(tops.items()))
            print(f"  prose mentions remaining by top-level directory: {summary}", file=out)
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
        errors = _validate_tree(root)
        for e in errors:
            print(e, file=out)
        if errors:
            print(
                f"ids migrate: {len(errors)} error(s) after rename; the tree is under git, "
                "`git checkout -- . && git clean -fd .specfuse/features` undoes the rename",
                file=out,
            )
            return 1
        print("validated: lint_plan, lint_roadmap, agent-policy clean", file=out)
        return 0
    finally:
        if lock is not None:
            lock.close()


def _failing_lines(output: str) -> list:
    """unittest `FAIL:`/`ERROR:` and pytest `FAILED` lines, else the last 20 lines."""
    lines = output.splitlines()
    found = [
        ln for ln in lines
        if ln.startswith(("FAIL:", "ERROR:", "FAILED "))
    ]
    return found or lines[-20:]


def _snapshot_working_tree(root: Path, wt: Path, out) -> tuple:
    """Copy *root*'s uncommitted state into worktree *wt* and commit it there; (modified, untracked)."""
    import shutil

    def git(*a, cwd=root, **kw):
        return subprocess.run(["git", *a], cwd=cwd, capture_output=True, check=False, **kw)

    diff = git("diff", "HEAD", "--binary")
    if diff.returncode != 0:
        raise RuntimeError(f"git diff HEAD failed: {diff.stderr.decode(errors='replace').strip()}")
    names = git("diff", "HEAD", "--name-only", "-z").stdout.decode().split("\0")
    names = [n for n in names if n]
    if diff.stdout:
        ap = git("apply", "--binary", "--whitespace=nowarn", "-", cwd=wt, input=diff.stdout)
        if ap.returncode != 0:
            print("rehearse: git apply failed; copying modified files instead", file=out)
            subprocess.run(["git", "checkout", "-q", "--", "."], cwd=wt, capture_output=True, check=False)
            for n in names:
                src = root / n
                if not src.exists() and not src.is_symlink():
                    raise RuntimeError(
                        f"cannot represent deleted tracked file {n!r} without git apply"
                    )
                dst = wt / n
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists() or dst.is_symlink():
                    dst.unlink()
                shutil.copy2(src, dst, follow_symlinks=False)
    others = git("ls-files", "--others", "--exclude-standard", "-z")
    untracked = [n for n in others.stdout.decode().split("\0") if n]
    for n in untracked:
        src = root / n
        dst = wt / n
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst, follow_symlinks=False)
    if names or untracked:
        for cmd in (
            ["add", "-A"],
            ["-c", "user.name=rehearsal", "-c", "user.email=rehearsal@localhost",
             "commit", "-q", "--no-verify", "-m", "rehearsal snapshot"],
        ):
            r = git(*cmd, cwd=wt)
            if r.returncode != 0:
                raise RuntimeError(f"git {cmd[-1]} failed in rehearsal: {r.stderr.decode(errors='replace').strip()}")
    return len(names), len(untracked)


def rehearse(repo_root, run_migration, command=None, out=None) -> int:
    """Run *run_migration(worktree_root)* on a throwaway snapshot of the working tree, then a test command.

    The snapshot is HEAD plus the real tree's uncommitted and untracked changes, committed on a
    detached HEAD inside the worktree only. Never writes to the real tree; the worktree is
    always removed.
    """
    import os
    import shutil
    import tempfile

    out = out or sys.stdout
    root = Path(repo_root).resolve()
    if command is None:
        from specfuse.loop import gate_commands

        gates = dict(gate_commands.iter_code_gates(root / ".specfuse" / "verification.yml"))
        command = gates.get("tests")
        if not command:
            print(
                "ids migrate: no `tests` gate in .specfuse/verification.yml; "
                "pass --rehearse-command",
                file=sys.stderr,
            )
            return 2
    tmp = Path(tempfile.mkdtemp(prefix="ids-rehearse-"))
    wt = tmp / "tree"
    added = False
    try:
        r = subprocess.run(
            ["git", "worktree", "add", "--detach", str(wt), "HEAD"],
            cwd=root, capture_output=True, text=True, check=False,
        )
        if r.returncode != 0:
            print(f"ids migrate: git worktree add failed: {r.stderr.strip()}", file=sys.stderr)
            return 2
        added = True
        try:
            modified, untracked = _snapshot_working_tree(root, wt, out)
        except RuntimeError as exc:
            print(f"ids migrate: {exc}", file=sys.stderr)
            return 2
        state = (
            "HEAD alone" if not (modified or untracked)
            else f"HEAD plus {modified} modified and {untracked} untracked file(s)"
        )
        print(f"rehearse: migrating a throwaway copy of {state} at {wt}", file=out)
        code = run_migration(wt)
        print(f"rehearse: migration {'validated' if code == 0 else f'failed (exit {code})'}", file=out)
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(wt)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
        )
        print(f"rehearse: running `{command}`", file=out)
        t = subprocess.run(  # nosec B602 - command is operator-declared config
            command, shell=True, cwd=wt, env=env,
            capture_output=True, text=True, check=False,
        )
        print(f"rehearse: command exit status {t.returncode}", file=out)
        if t.returncode != 0:
            for ln in _failing_lines(t.stdout + "\n" + t.stderr):
                print(f"  {ln}", file=out)
        ok = code == 0 and t.returncode == 0
        print(f"rehearse: {'passed' if ok else 'FAILED'}; real tree untouched", file=out)
        return 0 if ok else 1
    finally:
        if added:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt)],
                cwd=root, capture_output=True, check=False,
            )
            subprocess.run(["git", "worktree", "prune"], cwd=root, capture_output=True, check=False)
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="specfuse.loop.ids", description="Allocate and parse feature IDs."
    )
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    nextp = sub.add_parser("next", help="print the next free feature ID")
    nextp.add_argument("--year", type=int, default=None)
    sub.add_parser("validate", help="lint the tree with its own linters; print ERROR lines")
    mig = sub.add_parser("migrate", help="re-key folderless planned roadmap rows")
    which = mig.add_mutually_exclusive_group(required=True)
    which.add_argument("--planned-only", action="store_true")
    which.add_argument("--all", action="store_true", help="re-key every feature of this repository")
    mig.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    mig.add_argument(
        "--include-prose", nargs="*", default=None, metavar="PATH",
        help="with --all, also rewrite ambiguous prose mentions: in all files when bare, "
        "else only in the given repo-relative paths or globs",
    )
    mig.add_argument(
        "--exclude-id", action="append", default=[], metavar="ID",
        help="with --all, leave this old ID untouched everywhere (repeatable)",
    )
    mig.add_argument(
        "--rehearse", action="store_true",
        help="apply the rename on a throwaway snapshot of the working tree and run the tests gate there",
    )
    mig.add_argument(
        "--rehearse-command", default=None, metavar="CMD",
        help="with --rehearse, run CMD instead of the tests gate command",
    )
    args = parser.parse_args(argv)
    if args.command == "next":
        print(next_id(args.repo, args.year))
    elif args.command == "validate":
        errors = _validate_tree_here(Path(args.repo))
        for e in errors:
            print(e)
        return 1 if errors else 0
    elif args.command == "migrate":
        prose = args.include_prose
        if prose is not None and not prose:
            prose = True
        if args.rehearse_command is not None and not args.rehearse:
            parser.error("--rehearse-command requires --rehearse")
        if args.all:
            for value in args.exclude_id:
                if not FEATURE_ID_RE.match(value):
                    print(f"ids migrate: invalid --exclude-id value: {value!r}", file=sys.stderr)
                    return 2
            if args.rehearse:
                return rehearse(
                    args.repo,
                    lambda wt: migrate_all(
                        wt, apply=True, include_prose=prose or False,
                        exclude_ids=args.exclude_id,
                    ),
                    args.rehearse_command,
                )
            return migrate_all(
                args.repo, apply=args.apply, include_prose=prose or False,
                exclude_ids=args.exclude_id,
            )
        if prose is not None:
            parser.error("--include-prose requires --all")
        if args.exclude_id:
            parser.error("--exclude-id requires --all")
        if args.rehearse:
            return rehearse(
                args.repo, lambda wt: migrate(wt, apply=True), args.rehearse_command
            )
        return migrate(args.repo, apply=args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
