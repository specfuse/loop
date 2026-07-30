#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Write-once snapshot of a feature's as-activated PLAN graph.

Drift detection needs a stable reference to the plan as it looked when the
driver first dispatched it. Git archaeology was rejected at drafting — the
driver stays dumb and reads files, not history. `PLAN.baseline.json` is the
explicit artifact: written once by `write_baseline_if_absent`, never rewritten.
A baseline that can be refreshed is a drift detector that can be gamed by
drifting, so this module has no "refresh" or "overwrite" entry point at all.

Per gate the snapshot captures the gate number and, per work unit, the `id`,
`type`, a `goal` line (the WU file's `# ` title when present, else the id),
and `planned_cost_usd`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import _miniyaml

BASELINE_FILENAME = "PLAN.baseline.json"

_FM = re.compile(r"^---\s*$")
_TITLE = re.compile(r"^#\s+(.*)$", re.MULTILINE)
_GRAPH_BLOCK = re.compile(r"```ya?ml\s*\n(.*?)\n```", re.DOTALL)


def _read_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text) for a WU/PLAN file.

    Mirrors the split-then-`_miniyaml.parse` shape the driver uses elsewhere,
    kept local so this module has no import-time coupling to loop.py.
    """
    lines = path.read_text().splitlines()
    if not lines or not _FM.match(lines[0]):
        return {}, path.read_text()
    j = 1
    while j < len(lines) and not _FM.match(lines[j]):
        j += 1
    fm = _miniyaml.parse("\n".join(lines[1:j])) or {}
    body = "\n".join(lines[j + 1:])
    return fm, body


def load_plan_graph(feature_dir: Path) -> dict:
    """Parse `<feature_dir>/PLAN.md`'s fenced ```yaml graph block."""
    _, body = _read_frontmatter(Path(feature_dir) / "PLAN.md")
    m = _GRAPH_BLOCK.search(body)
    if not m:
        raise ValueError(f"{feature_dir}/PLAN.md has no ```yaml graph block.")
    return _miniyaml.parse(m.group(1)) or {}


def _wu_snapshot(feature_dir: Path, ref: dict) -> dict:
    wu_path = Path(feature_dir) / ref["file"]
    fm, body = _read_frontmatter(wu_path)
    title_m = _TITLE.search(body)
    goal = title_m.group(1).strip() if title_m else ref["id"]
    return {
        "id": ref["id"],
        "type": fm.get("type", "implementation"),
        "goal": goal,
        "planned_cost_usd": fm.get("planned_cost_usd"),
    }


def _snapshot(feature_dir: Path, plan: dict) -> dict:
    gates_out: list[dict[str, Any]] = []
    for gate in plan.get("gates", []) or []:
        wus_out = [_wu_snapshot(feature_dir, ref) for ref in gate.get("work_units", []) or []]
        gates_out.append({"gate": gate["gate"], "work_units": wus_out})
    return {"gates": gates_out}


def write_baseline_if_absent(feature_dir: Path, plan: dict) -> None:
    """Write `PLAN.baseline.json` if it does not already exist. No-op otherwise.

    `plan` is the parsed graph dict (as returned by `load_plan_graph` — the
    same shape `{"gates": [{"gate": N, "work_units": [{"id", "file", ...}]}]}`
    the driver already parses out of PLAN.md's fenced yaml block).
    """
    baseline_path = Path(feature_dir) / BASELINE_FILENAME
    if baseline_path.exists():
        return
    snapshot = _snapshot(feature_dir, plan)
    baseline_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")


def load_baseline(feature_dir: Path) -> dict | None:
    """Return the parsed baseline snapshot, or None when the file is absent."""
    baseline_path = Path(feature_dir) / BASELINE_FILENAME
    if not baseline_path.exists():
        return None
    return json.loads(baseline_path.read_text())
