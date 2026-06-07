#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""
Specfuse plan linter.

Validates a feature folder's structural integrity:
  - PLAN.md has the required feature frontmatter and a parseable graph,
  - every WU referenced in the graph has a file that exists with valid frontmatter,
  - every dependency edge points at a WU that exists in the graph,
  - every gate carries the mandatory closing sequence in order
    (retrospective -> lessons -> docs -> plan-next),
  - any WU in `draft` (i.e. just produced by plan-next) has the five mandatory
    prompt sections, so it is actually dispatchable.

Two jobs:
  1. plan-next's verification gate calls this (a malformed next-gate draft fails
     HERE, where you are already reviewing — far cheaper than failing mid-dispatch
     three gates later).
  2. a human integrity check you can run any time.

Exit 0 = clean, 1 = problems (printed).

Usage:  python .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-XXXX-slug
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Strict mini-YAML reader (alongside this script) — keeps the linter zero-install.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _miniyaml  # noqa: E402

FM = re.compile(r"^---\s*$")
REQUIRED_FEATURE_KEYS = {"feature_id", "title", "branch", "roadmap_goal", "status"}
VALID_TYPES = {"implementation", "retrospective", "lessons", "docs", "plan-next", "close"}
VALID_STATUS = {"draft", "pending", "ready", "in_progress", "in_review", "done",
                "blocked_human", "abandoned"}
CLOSING_SEQUENCE = ["retrospective", "lessons", "docs", "plan-next"]
# All WU types that count as closing work — the four-WU sequence members
# plus the single-session `close` alternative (single-gate features only).
_CLOSING_TYPES = frozenset(CLOSING_SEQUENCE) | {"close"}
# Correlation-ID pattern — canonical, mirroring `.specfuse/rules/correlation-ids.md`.
# Two namespaces:
#   Component-local: FEAT-YYYY-NNNN, optional /(T<NN>[H[N*]] | G<n>-<CLOSE>).
#   Orchestrated:    INIT-YYYY-NNNN/F<NN>, optional /(T<NN>[H[N*]] | G<n>-<CLOSE>).
# A bare INIT-YYYY-NNNN (no /FNN segment) is NOT a loop feature ID.
MODEL_ALIASES = frozenset({"sonnet", "opus", "haiku"})
FULL_MODEL_ID_RE = re.compile(r"^claude-\w[\w.-]*$")

CORRELATION_ID_RE = re.compile(
    r"^(FEAT-\d{4}-\d{4}(/(T\d{2}(H\d*)?|G\d+-(RETRO|LESSONS|DOCS|PLAN|CLOSE)))?|"
    r"INIT-\d{4}-\d{4}/F\d{2}(/(T\d{2}(H\d*)?|G\d+-(RETRO|LESSONS|DOCS|PLAN|CLOSE)))?)$"
)
# The five mandatory sections (architecture §8). 'Objective' is recommended in the
# template but not hard-required here.
REQUIRED_SECTIONS = ["Context", "Acceptance criteria", "Do not touch",
                     "Verification", "Escalation triggers"]
SECTION_CHECK_STATUSES = {"draft", "pending", "ready"}


def read_frontmatter(path: Path) -> tuple[dict, str]:
    lines = path.read_text().splitlines()
    if not lines or not FM.match(lines[0]):
        return {}, path.read_text()
    j = 1
    while j < len(lines) and not FM.match(lines[j]):
        j += 1
    return _miniyaml.parse("\n".join(lines[1:j])) or {}, "\n".join(lines[j + 1:])


def lint(feature_dir: Path) -> list[str]:
    errs: list[str] = []
    plan = feature_dir / "PLAN.md"
    if not plan.exists():
        return [f"missing {plan}"]

    fm, body = read_frontmatter(plan)
    missing = REQUIRED_FEATURE_KEYS - set(fm)
    if missing:
        errs.append(f"PLAN.md frontmatter missing keys: {sorted(missing)}")

    m = re.search(r"```ya?ml\s*\n(.*?)\n```", body, re.DOTALL)
    if not m:
        return errs + ["PLAN.md has no ```yaml graph block"]
    graph = _miniyaml.parse(m.group(1)) or {}
    gates = graph.get("gates", [])
    all_ids = {wu["id"] for g in gates for wu in (g.get("work_units") or [])}
    nonempty_gates_count = sum(1 for g in gates if g.get("work_units"))

    for g in gates:
        gnum = g.get("gate", "?")
        units = g.get("work_units") or []
        # An un-drafted future gate (empty) is fine — it just hasn't been planned yet.
        if not units:
            continue

        # WU files + frontmatter + dependency edges.
        types_in_order: list[str] = []
        for ref in units:
            wid, wfile = ref.get("id"), ref.get("file")
            if not wid or not wfile:
                errs.append(f"gate {gnum}: work unit missing id/file: {ref}")
                continue
            if not CORRELATION_ID_RE.match(wid):
                errs.append(f"gate {gnum}: malformed correlation id '{wid}' — "
                            f"must match {CORRELATION_ID_RE.pattern}")
            for dep in ref.get("depends_on") or []:
                if dep not in all_ids:
                    errs.append(f"gate {gnum}: {wid} depends on unknown WU '{dep}'")
            wpath = feature_dir / wfile
            if not wpath.exists():
                errs.append(f"gate {gnum}: {wid} -> file not found: {wfile}")
                continue
            wfm, wbody = read_frontmatter(wpath)
            fm_id = wfm.get("id")
            if fm_id != wid:
                errs.append(f"{wfile}: frontmatter id '{fm_id}' != graph id '{wid}'")
            # Only flag the frontmatter id separately when it disagrees with the graph
            # id (otherwise the graph-id check above already covers it).
            if fm_id and fm_id != wid and not CORRELATION_ID_RE.match(fm_id):
                errs.append(f"{wfile}: malformed frontmatter id '{fm_id}' — "
                            f"must match {CORRELATION_ID_RE.pattern}")
            if wfm.get("type") not in VALID_TYPES:
                errs.append(f"{wfile}: invalid type '{wfm.get('type')}'")
            _model = wfm.get("model", "")
            if not _model:
                errs.append(f"{wfile}: missing model")
            elif _model not in MODEL_ALIASES and not FULL_MODEL_ID_RE.match(_model):
                errs.append(
                    f"{wfile}: invalid model '{_model}' — must be a family alias "
                    f"({sorted(MODEL_ALIASES)}) or a full model ID (claude-*)"
                )
            if wfm.get("status") not in VALID_STATUS:
                errs.append(f"{wfile}: invalid status '{wfm.get('status')}'")
            types_in_order.append(wfm.get("type"))

            # Dispatchable WUs must have the five mandatory prompt sections.
            if wfm.get("status") in SECTION_CHECK_STATUSES:
                for sec in REQUIRED_SECTIONS:
                    if not re.search(rf"(?mi)^(?:#+\s*|\**){re.escape(sec)}", wbody):
                        errs.append(f"{wfile}: {wfm.get('status')} WU missing "
                                    f"section '{sec}'")

        # Closing: either the four-WU sequence or a single `close` WU (single-gate only).
        closing_found = [t for t in types_in_order if t in _CLOSING_TYPES]
        if closing_found == ["close"]:
            if nonempty_gates_count != 1:
                errs.append(
                    f"gate {gnum}: `close` WU is only valid in single-gate features "
                    f"({nonempty_gates_count} non-empty gates found); "
                    f"multi-gate features must use {CLOSING_SEQUENCE}"
                )
        elif closing_found != CLOSING_SEQUENCE:
            errs.append(
                f"gate {gnum}: closing sequence must be exactly "
                f"{CLOSING_SEQUENCE} in order (or a single `close` WU for "
                f"single-gate features); found {closing_found}"
            )

    return errs


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit("usage: lint_plan.py <feature_dir>")
    feature_dir = Path(sys.argv[1])
    errs = lint(feature_dir)
    if errs:
        print(f"FAIL — {len(errs)} issue(s) in {feature_dir}:")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"OK — {feature_dir} is structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
