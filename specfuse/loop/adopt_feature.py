#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Adopt a picked specfuse:feature issue into a dispatchable loop-feature folder."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from . import gh_features as _gh_features


def _encode_id(feature_id: str) -> str:
    """Map INIT-YYYY-NNNN/FNN -> INIT-YYYY-NNNN-FNN; FEAT-YYYY-NNNN unchanged."""
    return feature_id.replace("/", "-")


def _make_slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _plan_md(candidate: dict, encoded_id: str, slug: str) -> str:
    fid = candidate["feature_id"]
    title = candidate["title"]
    branch = f"feat/{encoded_id}-{slug}"
    autonomy = candidate.get("autonomy") or "review"
    source_url = candidate.get("url", "")
    initiative = candidate.get("initiative")

    fm_lines = [
        "---",
        f"feature_id: {fid}",
        f"title: {title}",
        f"slug: {slug}",
        f"branch: {branch}",
        f"roadmap_goal: {title}",
        f"autonomy_default: {autonomy}",
        "status: planned",
        f"source_issue_url: {source_url}",
    ]
    if initiative is not None:
        fm_lines.append(f"initiative: {initiative}")
    fm_lines.append("---")

    wu01_file = f"WU-01-{slug}.md"
    graph = f"""\
```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: {fid}/T01
        file: {wu01_file}
        depends_on: []
      - id: {fid}/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on: [{fid}/T01]
      - id: {fid}/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on: [{fid}/G1-RETRO]
      - id: {fid}/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on: [{fid}/G1-LESSONS]
      - id: {fid}/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on: [{fid}/G1-DOCS]
  - gate: 2
    file: GATE-02.md
    work_units: []
  - gate: 3
    file: GATE-03.md
    work_units: []
```"""

    body = (
        f"\n# Plan: {title}\n\n"
        f"Adopted from GitHub issue: {source_url}\n\n"
        "This file owns the **shape** of the feature: gate order, work units, "
        "dependency edges.\n"
        "WU files own their own status; GATE files own gate status.\n\n"
        "## Task graph\n\n"
        f"{graph}\n"
    )

    return "\n".join(fm_lines) + "\n" + body


def _wu01_md(candidate: dict) -> str:
    fid = candidate["feature_id"]
    title = candidate["title"]
    task_type = candidate.get("task_type") or "implementation"
    body_text = candidate.get("body", "")

    fm = (
        "---\n"
        f"id: {fid}/T01\n"
        f"type: {task_type}\n"
        "model: claude-sonnet-4-6\n"
        "status: draft\n"
        "attempts: 0\n"
        "---"
    )

    return f"{fm}\n\n# {title}\n\n**Objective.** TODO\n\n{body_text}\n"


def _closing_wu(
    feature_id: str, wu_id: str, wu_type: str, model: str, title: str
) -> str:
    fm = (
        "---\n"
        f"id: {feature_id}/{wu_id}\n"
        f"type: {wu_type}\n"
        f"model: {model}\n"
        "status: draft\n"
        "attempts: 0\n"
        "---"
    )

    body = (
        f"\n# {title}\n\n"
        f"**Context.** This is the `{wu_id}` unit for feature `{feature_id}`.\n"
        "Read the feature's `events.jsonl` and the commits on the feature branch.\n\n"
        "**Acceptance criteria.** The artifact for this unit exists and is substantive.\n\n"
        "**Do not touch.** Source code not owned by this unit, generated directories, "
        "secrets, `.git/`. The driver owns all git — edit files only.\n\n"
        "**Verification.** The `doc` gates in `.specfuse/verification.yml` "
        "(the artifact exists and something changed).\n\n"
        "**Escalation triggers.** If the event log is too sparse to complete this unit "
        "honestly, say so in the artifact rather than inventing content.\n"
    )

    return fm + body


def _gate_md(gate_num: int, title_line: str, body_text: str) -> str:
    return (
        f"---\ngate: {gate_num}\nstatus: open\n---\n\n"
        f"# Gate {gate_num} — {title_line}\n\n"
        "## Definition of done\n\n"
        f"{body_text}\n\n"
        "## Reflection notes\n\n"
        "<written by the human at review time>\n"
    )


def adopt_feature(candidate: dict, root: Path) -> Path:
    """Scaffold a loop-feature folder from a picked specfuse:feature candidate.

    Returns the created folder path.
    Raises FileExistsError if the folder already exists.
    """
    fid = candidate["feature_id"]
    encoded_id = _encode_id(fid)
    slug = _make_slug(candidate["title"])
    folder = root / f"{encoded_id}-{slug}"

    if folder.exists():
        raise FileExistsError(f"folder already exists: {folder}")

    folder.mkdir(parents=True)

    (folder / "PLAN.md").write_text(_plan_md(candidate, encoded_id, slug))
    (folder / "GATE-01.md").write_text(
        _gate_md(1, candidate["title"], f"Gate 1 implementation complete: {candidate['title']}")
    )
    (folder / "GATE-02.md").write_text(
        _gate_md(2, "Next gate", "Drafted by gate 1's plan-next.")
    )
    (folder / f"WU-01-{slug}.md").write_text(_wu01_md(candidate))
    (folder / "WU-90-gate-1-retrospective.md").write_text(
        _closing_wu(fid, "G1-RETRO", "retrospective", "claude-sonnet-4-6", "Gate 1 retrospective")
    )
    (folder / "WU-91-gate-1-lessons.md").write_text(
        _closing_wu(fid, "G1-LESSONS", "lessons", "claude-sonnet-4-6", "Gate 1 lessons")
    )
    (folder / "WU-92-gate-1-docs.md").write_text(
        _closing_wu(fid, "G1-DOCS", "docs", "claude-sonnet-4-6", "Gate 1 documentation update")
    )
    (folder / "WU-93-gate-1-plan-next.md").write_text(
        _closing_wu(fid, "G1-PLAN", "plan-next", "claude-opus-4-7", "Gate 1 plan next gate")
    )

    return folder


def main(_runner=None, _root=None) -> None:
    """CLI: adopt_feature.py <repo> <issue-number>"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Adopt a specfuse:feature GitHub issue into a loop-feature folder."
    )
    parser.add_argument("repo", help="GitHub repo (owner/repo)")
    parser.add_argument("issue_number", type=int, help="Issue number to adopt")
    parsed = parser.parse_args()

    root = _root if _root is not None else Path(".specfuse/features")
    candidates = _gh_features.list_features(parsed.repo, runner=_runner)
    matched = [c for c in candidates if c["number"] == parsed.issue_number]
    if not matched:
        print(
            f"no specfuse:feature issue with number {parsed.issue_number} in {parsed.repo}",
            file=sys.stderr,
        )
        sys.exit(1)

    folder = adopt_feature(matched[0], root=root)
    print(folder)


if __name__ == "__main__":
    main()
