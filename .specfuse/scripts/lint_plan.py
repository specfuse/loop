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

# Strict mini-YAML reader and loop constants (alongside this script).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _miniyaml  # noqa: E402
from loop import VERDICT_VALUES  # noqa: E402

FM = re.compile(r"^---\s*$")
REQUIRED_FEATURE_KEYS = {"feature_id", "title", "branch", "roadmap_goal", "status"}
VALID_TYPES = {"implementation", "retrospective", "lessons", "docs", "plan-next", "close",
               "close-intermediate"}
VALID_STATUS = {"draft", "pending", "ready", "in_progress", "in_review", "done",
                "blocked_human", "abandoned"}
CLOSING_SEQUENCE = ["retrospective", "lessons", "docs", "plan-next"]
# New compact closing shapes (FEAT-2026-0015):
#   non-terminal gate: close-intermediate → plan-next
#   terminal gate:     close  (any feature size)
# Legacy 4-WU CLOSING_SEQUENCE still accepted on any gate but emits a WARN.
NEW_INTERMEDIATE_SEQUENCE = ["close-intermediate", "plan-next"]
# All WU types that count as closing work.
_CLOSING_TYPES = frozenset(CLOSING_SEQUENCE) | {"close", "close-intermediate"}
# Correlation-ID pattern — canonical, mirroring `.specfuse/rules/correlation-ids.md`.
# Two namespaces:
#   Component-local: FEAT-YYYY-NNNN, optional /(T<NN>[H[N*]] | G<n>-<CLOSE>).
#   Orchestrated:    INIT-YYYY-NNNN/F<NN>, optional /(T<NN>[H[N*]] | G<n>-<CLOSE>).
# A bare INIT-YYYY-NNNN (no /FNN segment) is NOT a loop feature ID.
MODEL_ALIASES = frozenset({"sonnet", "opus", "haiku"})
VALID_EFFORT = frozenset({"low", "medium", "high", "xhigh", "max"})
FULL_MODEL_ID_RE = re.compile(r"^claude-\w[\w.-]*$")

CORRELATION_ID_RE = re.compile(
    r"^(FEAT-\d{4}-\d{4}(/(T\d{2}(H\d*)?|G\d+-(RETRO|LESSONS|DOCS|PLAN|CLOSE-INTERMEDIATE|CLOSE)))?|"
    r"INIT-\d{4}-\d{4}/F\d{2}(/(T\d{2}(H\d*)?|G\d+-(RETRO|LESSONS|DOCS|PLAN|CLOSE-INTERMEDIATE|CLOSE)))?)$"
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
    # Last non-empty gate is the terminal gate; `close` is only valid there.
    terminal_gate_gnum = next(
        (g.get("gate", "?") for g in reversed(gates) if g.get("work_units")), None
    )
    # Track closing shape per gate for cross-gate mixed-shape detection.
    _gate_closing_shapes: dict = {}  # gnum -> "NEW" | "LEGACY" | "INVALID"

    for g in gates:
        gnum = g.get("gate", "?")
        is_terminal = (gnum == terminal_gate_gnum)
        units = g.get("work_units") or []

        # GATE.md cost_budget_usd: optional, must be numeric when present.
        # Validated independently of work-unit presence so a drafted-but-empty
        # gate can still declare a budget for its eventual WUs.
        gate_file_rel = g.get("file")
        if gate_file_rel:
            gate_path = feature_dir / gate_file_rel
            if gate_path.exists():
                gfm, _ = read_frontmatter(gate_path)
                if "cost_budget_usd" in gfm:
                    val = gfm["cost_budget_usd"]
                    if isinstance(val, bool) or not isinstance(val, (int, float)):
                        errs.append(
                            f"{gate_file_rel}: cost_budget_usd must be numeric "
                            f"(int or float), got {val!r}"
                        )

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
            if "model" in wfm:
                _model = wfm["model"]
                if not _model:
                    errs.append(
                        f"{wfile}: model present but has no value — must be a family alias "
                        f"({sorted(MODEL_ALIASES)}) or a full model ID (claude-*)"
                    )
                elif _model not in MODEL_ALIASES and not FULL_MODEL_ID_RE.match(_model):
                    errs.append(
                        f"{wfile}: invalid model '{_model}' — must be a family alias "
                        f"({sorted(MODEL_ALIASES)}) or a full model ID (claude-*)"
                    )
            # model absent: valid — load_wu applies MODEL_BY_TYPE[type] at dispatch time
            if wfm.get("status") not in VALID_STATUS:
                errs.append(f"{wfile}: invalid status '{wfm.get('status')}'")
            _effort = wfm.get("effort")
            if _effort is not None and _effort not in VALID_EFFORT:
                errs.append(
                    f"{wfile}: invalid effort '{_effort}' — must be one of "
                    f"{sorted(VALID_EFFORT)}"
                )
            types_in_order.append(wfm.get("type"))

            # Dispatchable WUs must have the five mandatory prompt sections.
            if wfm.get("status") in SECTION_CHECK_STATUSES:
                for sec in REQUIRED_SECTIONS:
                    if not re.search(rf"(?mi)^(?:#+\s*|\**){re.escape(sec)}", wbody):
                        errs.append(f"{wfile}: {wfm.get('status')} WU missing "
                                    f"section '{sec}'")

            # Verdict frontmatter validation.
            wu_verdict = wfm.get("verdict")
            wu_status = wfm.get("status")
            wu_type_val = wfm.get("type")
            if wu_type_val in {"close", "close-intermediate"}:
                # draft/pending: verdict written at execution time, not before dispatch.
                # done/abandoned/blocked_human: legacy fixtures without verdict are valid.
                if wu_status not in {"draft", "pending", "done", "abandoned", "blocked_human"}:
                    if wu_verdict is None or wu_verdict not in VERDICT_VALUES:
                        errs.append(
                            f"ERROR: {wfile}: close-type WU missing or invalid 'verdict' "
                            f"frontmatter (must be one of: "
                            f"met, met_locally, partially_met, not_met)."
                        )
            else:
                if wu_verdict is not None:
                    errs.append(
                        f"ERROR: {wfile}: 'verdict' frontmatter is only meaningful for "
                        f"closing types (close, close-intermediate); remove it from "
                        f"this {wu_type_val!r} WU."
                    )

        # Closing shape check.
        closing_found = [t for t in types_in_order if t in _CLOSING_TYPES]
        if closing_found == ["close"]:
            if is_terminal:
                _gate_closing_shapes[gnum] = "NEW"
            else:
                errs.append(
                    f"gate {gnum}: `close` WU is only valid on a terminal gate; "
                    f"non-terminal gates must use {NEW_INTERMEDIATE_SEQUENCE} "
                    f"(new) or {CLOSING_SEQUENCE} (legacy)"
                )
                _gate_closing_shapes[gnum] = "INVALID"
        elif closing_found == NEW_INTERMEDIATE_SEQUENCE:
            if not is_terminal:
                _gate_closing_shapes[gnum] = "NEW"
            else:
                errs.append(
                    f"gate {gnum}: `close-intermediate → plan-next` is for "
                    f"non-terminal gates; terminal gate must use a single `close` WU "
                    f"(new) or {CLOSING_SEQUENCE} (legacy)"
                )
                _gate_closing_shapes[gnum] = "INVALID"
        elif closing_found == CLOSING_SEQUENCE:
            gate_file_for_warn = gate_file_rel or f"GATE-{gnum:02d}.md"
            print(
                f"WARN: {feature_dir}/{gate_file_for_warn} uses legacy 4-WU closing "
                f"sequence; new contract is 2-WU (close-intermediate + plan-next) for "
                f"intermediate or 1-WU (close) for terminal. See FEAT-2026-0015."
            )
            _gate_closing_shapes[gnum] = "LEGACY"
        elif "close-intermediate" in closing_found:
            errs.append(
                f"gate {gnum}: close-intermediate must be immediately followed by "
                f"plan-next; found closing sequence {closing_found}"
            )
            _gate_closing_shapes[gnum] = "INVALID"
        else:
            errs.append(
                f"gate {gnum}: closing sequence must be {CLOSING_SEQUENCE} (legacy), "
                f"{NEW_INTERMEDIATE_SEQUENCE} (non-terminal new), or a single `close` "
                f"WU (terminal new); found {closing_found}"
            )
            _gate_closing_shapes[gnum] = "INVALID"

    # Cross-gate mixed-shape check. Two directions of mix:
    #
    # - FORWARD MIGRATION (legacy on earlier gates + NEW on terminal):
    #   ALLOWED with WARN. This is the documented dogfood-inversion pattern
    #   FEAT-2026-0015 uses on itself (gate 1 closed under the legacy 4-WU
    #   sequence; gate 2 ships + dogfoods the NEW close contract). Operators
    #   migrating an in-flight feature mid-stream land here naturally.
    #
    # - BACKWARD DRIFT (NEW on earlier gates + legacy on terminal): ERROR.
    #   The new contract is the canonical target; sliding back to legacy on
    #   the terminal gate after using NEW earlier is methodology drift the
    #   author owes a deliberate explanation for. Don't soft-fail it.
    new_gnums = sorted(n for n, s in _gate_closing_shapes.items() if s == "NEW")
    legacy_gnums = sorted(n for n, s in _gate_closing_shapes.items() if s == "LEGACY")
    if new_gnums and legacy_gnums:
        terminal_gnum = max(new_gnums + legacy_gnums)
        if terminal_gnum in new_gnums:
            # Forward migration: legacy earlier, NEW terminal.
            print(
                f"WARN: {feature_dir}: forward-mixed closing-shape contracts — "
                f"gate(s) {legacy_gnums} use LEGACY 4-WU, terminal gate "
                f"{terminal_gnum} uses NEW. This is allowed as a dogfood / "
                f"migration pattern (see FEAT-2026-0015 LEARNINGS). Future "
                f"features should consistently use NEW from the start."
            )
        else:
            errs.append(
                f"ERROR: {feature_dir}: backward-mixed closing-shape contracts — "
                f"gate(s) {new_gnums} use NEW but terminal gate {terminal_gnum} "
                f"uses LEGACY. The new contract is canonical; reverting to "
                f"legacy on the terminal gate is methodology drift. Pick NEW "
                f"on the terminal gate, or use LEGACY consistently."
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
