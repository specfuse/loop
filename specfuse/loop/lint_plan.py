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

Usage:  specfuse-lint .specfuse/features/FEAT-XXXX-slug
"""

from __future__ import annotations

import re
from pathlib import Path

from . import _miniyaml
from .loop import VERDICT_VALUES

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

# Oracle-env lint (FEAT-2026-0015/T05).
_ORACLE_EXEMPT_TYPES = frozenset({"lessons", "docs", "retrospective"})

# Driver-wiring keyword detector (FEAT-2026-0017/T02).
_DRIVER_WIRING_PATTERNS = [
    re.compile(r"\bloop\.py\b", re.IGNORECASE),
    re.compile(r"\bdriver-side\b", re.IGNORECASE),
    re.compile(r"\bMODEL_BY_TYPE\b", re.IGNORECASE),
    re.compile(r"\bEFFORT_BY_TYPE\b", re.IGNORECASE),
    re.compile(r"\bGATES_FOR_TYPE\b", re.IGNORECASE),
    re.compile(r"\bCLOSING_ASSERTIONS_BY_TYPE\b", re.IGNORECASE),
    re.compile(r"\bPOST_PASS_INVARIANTS_BY_TYPE\b", re.IGNORECASE),
    re.compile(r"\bfire_terminal_flips\b", re.IGNORECASE),
    re.compile(r"\bassert_terminal_flips_fired\b", re.IGNORECASE),
    re.compile(r"\bsquash_commit\b", re.IGNORECASE),
    re.compile(r"\breset_preserving_events\b", re.IGNORECASE),
    re.compile(r"\bcommit_bookkeeping\b", re.IGNORECASE),
]


def detect_driver_wiring(wu_body: str) -> list[str]:
    """Return matched wiring-keyword strings found in wu_body."""
    found = []
    for pat in _DRIVER_WIRING_PATTERNS:
        m = pat.search(wu_body)
        if m:
            found.append(m.group(0))
    return found
ORACLE_VERB_PATTERNS = (
    re.compile(r"\btest\s+loops?\b", re.IGNORECASE),
    re.compile(r"\bloops?\s+of\s+tests?\b", re.IGNORECASE),
    re.compile(r"\baudit\b", re.IGNORECASE),
    re.compile(r"\brecursive\s+run\b", re.IGNORECASE),
    re.compile(r"\brun\s+\d+\s+times\b", re.IGNORECASE),
    re.compile(r"\b\d+\s+consecutive\s+runs?\b", re.IGNORECASE),
    re.compile(r"\bsmoke[-\s]tests?\b", re.IGNORECASE),
    re.compile(r"\boracle\b", re.IGNORECASE),
    re.compile(r"\bintegration\s+tests?\b", re.IGNORECASE),
    re.compile(r"\be2e\b", re.IGNORECASE),
    re.compile(r"for\s+i\s+in\s+\$\(seq\b", re.IGNORECASE),
    re.compile(r"\brepeat\s+\d+\s+times\b", re.IGNORECASE),
)
_AC_START_RE = re.compile(
    r"(?mi)^\*\*Acceptance criteria[^\n*]*\*\*\.?|^#{1,6}\s+Acceptance criteria"
)
_AC_END_RE = re.compile(r"(?m)^(?:\*\*|#{1,6}\s)")


def _slice_ac_section(body: str) -> str:
    """Return the text of the Acceptance criteria section only (bold-preamble or ATX)."""
    m = _AC_START_RE.search(body)
    if not m:
        return ""
    nl = body.find("\n", m.end())
    after = body[nl + 1:] if nl != -1 else ""
    em = _AC_END_RE.search(after)
    return after[:em.start()] if em else after


def _slice_section(body: str, section_name: str) -> str:
    """Return content between a named section heading and the next heading."""
    start_re = re.compile(rf"(?mi)^(?:#+\s*|\**){re.escape(section_name)}")
    m = start_re.search(body)
    if not m:
        return ""
    nl = body.find("\n", m.end())
    after = body[nl + 1:] if nl != -1 else ""
    em = _AC_END_RE.search(after)
    return after[:em.start()] if em else after


def detect_oracle_verbs(ac_section_text: str) -> list[str]:
    """Return matched oracle-verb strings found in the AC section text."""
    found = []
    for pat in ORACLE_VERB_PATTERNS:
        m = pat.search(ac_section_text)
        if m:
            found.append(m.group(0))
    return found


def read_frontmatter(path: Path) -> tuple[dict, str]:
    lines = path.read_text().splitlines()
    if not lines or not FM.match(lines[0]):
        return {}, path.read_text()
    j = 1
    while j < len(lines) and not FM.match(lines[j]):
        j += 1
    return _miniyaml.parse("\n".join(lines[1:j])) or {}, "\n".join(lines[j + 1:])


def _find_task_graph_block(body: str) -> dict | None:
    """Find the YAML block in PLAN.md that contains the task graph (issue #21).

    PLAN.md may include multiple ```yaml fenced blocks (e.g. frontmatter
    schema examples, type catalogs) before the actual task graph. Identify
    the task-graph block by its top-level `gates:` key, scanning every
    yaml block in order and returning the first one whose parsed value
    contains `gates`.

    Returns the parsed dict (with `gates` key) on success, or None when no
    yaml block in the body contains a `gates` key.
    """
    for m in re.finditer(r"```ya?ml\s*\n(.*?)\n```", body, re.DOTALL):
        parsed = _miniyaml.parse(m.group(1)) or {}
        if "gates" in parsed:
            return parsed
    return None


def check_planned_cost(feature_dir: Path, plan_fm: dict, gates: list) -> None:
    """Emit WARN for missing planned_cost_usd on WUs and PLAN.md.

    Sealed WUs (wu status=done AND plan status=done) are skipped silently —
    backfilling cost estimates on history is pointless.  Active or draft WUs
    get the WARN.  PLAN.md is compared against the sum of WU planned costs;
    delta > 10% emits a separate WARN naming the delta.  Never raises or
    appends to an errors list — all findings are WARN-only (exit code 0).
    """
    plan_status = plan_fm.get("status", "")
    wu_sum = 0.0

    for g in gates:
        units = g.get("work_units") or []
        for ref in units:
            wfile = ref.get("file")
            if not wfile:
                continue
            wpath = feature_dir / wfile
            if not wpath.exists():
                continue
            wfm, _ = read_frontmatter(wpath)
            wu_status = wfm.get("status", "")
            planned = wfm.get("planned_cost_usd")

            # Sealed: feature done AND this WU done — nothing useful to backfill.
            is_sealed = (wu_status == "done" and plan_status == "done")
            if not is_sealed and planned is None:
                print(
                    f"WARN: {wfile}: missing 'planned_cost_usd' frontmatter "
                    f"(optional but recommended for cost-variance calibration). "
                    f"See PLAN.md roadmap_goal § Planned-cost capture."
                )
            if planned is not None:
                wu_sum += float(planned)

    wu_sum = round(wu_sum, 2)

    plan_cost = plan_fm.get("planned_cost_usd")
    if plan_cost is None:
        print(
            f"WARN: {feature_dir}/PLAN.md: missing 'planned_cost_usd' frontmatter "
            f"(optional but recommended for cost-variance calibration). "
            f"See PLAN.md roadmap_goal § Planned-cost capture."
        )
    else:
        plan_cost_f = round(float(plan_cost), 2)
        if plan_cost_f > 0 or wu_sum > 0:
            denom = plan_cost_f if plan_cost_f > 0 else wu_sum
            delta_pct = abs(plan_cost_f - wu_sum) / denom * 100
        else:
            delta_pct = 0.0
        if delta_pct > 10:
            print(
                f"WARN: {feature_dir}/PLAN.md: planned_cost_usd "
                f"${plan_cost_f:.2f} differs from sum of WU planned costs "
                f"${wu_sum:.2f} (delta {delta_pct:.0f}%, threshold 10%). "
                f"Review estimates."
            )


def lint(feature_dir: Path) -> list[str]:
    errs: list[str] = []
    plan = feature_dir / "PLAN.md"
    if not plan.exists():
        return [f"missing {plan}"]

    fm, body = read_frontmatter(plan)
    missing = REQUIRED_FEATURE_KEYS - set(fm)
    if missing:
        errs.append(f"PLAN.md frontmatter missing keys: {sorted(missing)}")

    if "base" in fm:
        base_val = fm["base"]
        feature_id_val = fm.get("feature_id", feature_dir.name)
        if not isinstance(base_val, str) or not base_val.strip():
            errs.append(
                f"{feature_id_val}: PLAN.md frontmatter 'base' key is present but "
                f"empty/whitespace-only/non-string: {base_val!r}"
            )

    graph = _find_task_graph_block(body)
    if graph is None:
        return errs + ["PLAN.md has no ```yaml graph block"]
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

            # Oracle-env WARN (FEAT-2026-0015/T05).
            if wu_type_val not in _ORACLE_EXEMPT_TYPES:
                ac_text = _slice_ac_section(wbody)
                oracle_matches = detect_oracle_verbs(ac_text)
                if oracle_matches and "oracle_env" not in wfm:
                    print(
                        f"WARN: {wfile}: AC mentions oracle-like work "
                        f"(matched: {oracle_matches}) but frontmatter has no "
                        f"'oracle_env' field. "
                        f"See LEARNINGS [FEAT-2026-0013/G1-CLOSE]."
                    )

            # Driver-wiring declaration WARN (FEAT-2026-0017/T02).
            if wu_type_val == "implementation":
                wiring_matches = detect_driver_wiring(wbody)
                pdh = wfm.get("produces_driver_helper")
                pdh_empty = not pdh  # None, [], "", or missing all count as empty
                if wiring_matches and pdh_empty:
                    print(
                        f"WARN: {wfile}: implementation WU mentions driver wiring "
                        f"({wiring_matches}) but `produces_driver_helper` frontmatter "
                        f"is empty. Declare the symbol(s) this WU produces in the "
                        f"driver. See authoring-work-units §9 + FEAT-2026-0017."
                    )

            # Deliverable-presence declaration WARN (FEAT-2026-0022/T01).
            # Advisory: an implementation WU should declare the file path(s) it
            # is contracted to yield via `produces:`, which T02's presence gate
            # enforces against disk. Closing types are exempt (gated on
            # implementation above). Non-blocking; never appends to errs.
            if wu_type_val == "implementation":
                produces = wfm.get("produces")
                produces_empty = not produces  # None, [], "", or missing all count
                if produces_empty:
                    print(
                        f"WARN: {wfile}: implementation WU declares no "
                        f"'produces:' deliverable list. See FEAT-2026-0022."
                    )

            # Bare/non-root-relative produces path WARN (#77). Applies to any
            # WU type that declares produces (the incident was a close-adjacent
            # WU). The presence gate (FEAT-2026-0022/T02) resolves each path
            # relative to the repo root; a bare filename (no '/') almost always
            # names a file that actually lives in a subdirectory (.specfuse/,
            # modules/, environments/, the feature dir, …). Resolved from the
            # root it is absent, so the gate fails identically every attempt and
            # spins to a 3-attempt block — ~3 wasted sessions on an authoring
            # typo a static check catches for free.
            produces_raw = wfm.get("produces")
            if produces_raw:
                entries = produces_raw if isinstance(produces_raw, list) else [produces_raw]
                for entry in entries:
                    entry_s = str(entry).strip()
                    if entry_s and "/" not in entry_s:
                        print(
                            f"WARN: {wfile}: produces path {entry_s!r} is a bare "
                            f"filename — produces paths are resolved relative to "
                            f"the repo root, where this almost never exists (WU "
                            f"deliverables live under .specfuse/, modules/, "
                            f"environments/, the feature dir, …). Use a "
                            f"repo-root-relative path or the presence gate will "
                            f"fail every attempt and spin to a block. See #77."
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

    # Planned-cost capture: WARN on missing/divergent planned_cost_usd fields.
    check_planned_cost(feature_dir, fm, gates)

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


def lint_plan_next_draft(feature_dir: Path, just_closed_gate: int) -> list[str]:
    """Warn-only lint over draft WUs produced by the just-completed plan-next.

    Walks gate (just_closed_gate+1) in PLAN.md and applies focused checks to
    each WU with status=='draft'. Returns WARN strings; empty = clean.
    Callers must not raise on non-empty return.
    """
    warns: list[str] = []
    plan = feature_dir / "PLAN.md"
    if not plan.exists():
        return warns

    _, body = read_frontmatter(plan)
    graph = _find_task_graph_block(body)
    if graph is None:
        return warns

    gates = graph.get("gates", [])

    next_gate_num = just_closed_gate + 1
    next_gate = next((g for g in gates if g.get("gate") == next_gate_num), None)
    if next_gate is None:
        return warns  # Terminal gate: no N+1 — clean

    units = next_gate.get("work_units") or []
    for ref in units:
        wfile = ref.get("file")
        if not wfile:
            continue
        wpath = feature_dir / wfile
        if not wpath.exists():
            continue
        wfm, wbody = read_frontmatter(wpath)
        if wfm.get("status") != "draft":
            continue

        wid = ref.get("id", wfile)

        # Correlation-ID format check.
        if not CORRELATION_ID_RE.match(wid):
            warns.append(f"{wfile}: malformed correlation ID '{wid}'")

        # planned_cost_usd: present and parses as a positive float.
        planned = wfm.get("planned_cost_usd")
        if planned is None:
            warns.append(f"{wfile}: missing 'planned_cost_usd' frontmatter")
        else:
            try:
                if float(planned) <= 0:
                    warns.append(
                        f"{wfile}: 'planned_cost_usd' must be a positive float, "
                        f"got {planned!r}"
                    )
            except (TypeError, ValueError):
                warns.append(
                    f"{wfile}: 'planned_cost_usd' is not a valid float: {planned!r}"
                )

        # type must be in VALID_TYPES.
        wu_type = wfm.get("type")
        if wu_type not in VALID_TYPES:
            warns.append(
                f"{wfile}: invalid 'type' {wu_type!r} — must be one of "
                f"{sorted(VALID_TYPES)}"
            )

        # Five mandatory sections: presence + non-empty content.
        for sec in REQUIRED_SECTIONS:
            if not re.search(rf"(?mi)^(?:#+\s*|\**){re.escape(sec)}", wbody):
                warns.append(f"{wfile}: draft WU missing section '{sec}'")
                continue
            if not _slice_section(wbody, sec).strip():
                warns.append(f"{wfile}: section '{sec}' is empty")

        # Implementation + driver-wiring + empty produces_driver_helper → WARN.
        if wu_type == "implementation":
            wiring = detect_driver_wiring(wbody)
            pdh = wfm.get("produces_driver_helper")
            if wiring and not pdh:
                warns.append(
                    f"{wfile}: implementation draft WU mentions driver wiring "
                    f"({wiring}) but 'produces_driver_helper' frontmatter is empty"
                )

    return warns


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Specfuse plan linter.",
        usage="lint_plan.py <feature_dir> [--just-closed-gate N]",
    )
    parser.add_argument("feature_dir", type=Path)
    parser.add_argument(
        "--just-closed-gate",
        type=int,
        dest="just_closed_gate",
        default=None,
        metavar="N",
        help="Also run plan-next-draft lint for gate N+1 draft WUs (warn-only).",
    )
    args = parser.parse_args()
    feature_dir = args.feature_dir
    errs = lint(feature_dir)
    if errs:
        print(f"FAIL — {len(errs)} issue(s) in {feature_dir}:")
        for e in errs:
            print(f"  - {e}")
    else:
        print(f"OK — {feature_dir} is structurally valid.")
    if args.just_closed_gate is not None:
        _draft_warns = lint_plan_next_draft(feature_dir, args.just_closed_gate)
        for _w in _draft_warns:
            print(f"WARN (plan-next-draft lint): {_w}")
        if _draft_warns:
            print(
                f"plan-next-draft lint: {len(_draft_warns)} warning(s) for gate "
                f"{args.just_closed_gate + 1} draft WUs."
            )
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
