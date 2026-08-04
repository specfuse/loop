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

import fnmatch
import re
from pathlib import Path

from . import _miniyaml
from . import _wu_sections
from .closing_requirements import gate_review_filename
from .loop import VERDICT_VALUES

FM = re.compile(r"^---\s*$")
REQUIRED_FEATURE_KEYS = {"feature_id", "title", "branch", "roadmap_goal", "status"}
VALID_TYPES = {"implementation", "retrospective", "lessons", "docs", "plan-next", "close",
               "close-intermediate"}
VALID_STATUS = {"draft", "pending", "ready", "in_progress", "in_review", "done",
                "blocked_human", "abandoned"}
# Feature (PLAN.md) and gate status vocabularies the DRIVER branches on. Kept
# here (duplicated from loop.py's status literals, like VALID_TYPES/VALID_STATUS
# above) so the linter validates the same set the driver acts on — an
# unrecognized status that passes lint and then behaves differently at dispatch
# is the class #183 (deferred) and #185 exist to close. Keep in sync with
# find_feature / the gate-status transitions in loop.py.
VALID_FEATURE_STATUS = {"planned", "active", "blocked", "deferred", "done", "abandoned"}
VALID_GATE_STATUS = {"open", "awaiting_review", "passed"}
# Features whose `status: done` legitimately coexists with a non-`passed`
# gate, keyed by feature directory name. Each entry is checked in
# check_done_feature_gates below for a non-empty reason, and for pointing at
# a directory that still exists (FEAT-2026-0072/T03).
DONE_FEATURE_GATE_EXCLUSIONS = {
    "FEAT-2026-0001-health-endpoint": (
        "bundled worked-example fixture — the self-demonstrating reference "
        "installation a target project copies via init.sh; a template never "
        "executed and never to be, so its gates stay open by design"
    ),
    "FEAT-2026-0036-adopt-ruff-016": (
        "executed directly as a config-only fix after a loop run on a flawed "
        "plan blocked — the close ceremony deliberately never ran, so GATE-01 "
        "stays open rather than asserting a ceremony that did not happen"
    ),
}
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

# Two enforcement surfaces, one contract. This pattern governs PLAN.md graphs
# and WU frontmatter. The event envelope enforces its own, narrower
# `correlation_id` pattern (`data/schemas/event.schema.json`, vendored from the
# methodology core and never edited here); the driver widens it via the
# driver-local registry `data/schemas/driver-event.schema.json`, read by
# `validate_event.load_validator` on a deep copy — the fall-through
# FEAT-2026-0060 established for `event_type` and FEAT-2026-0073 extended to
# correlation IDs.
#
# ADDING A NEW `<NAME>` SEGMENT: update this pattern AND that registry's
# `closing_names`, or IDs the linter accepts will be rejected by envelope
# validation. This note lives here, at the change site, rather than in
# `rules/correlation-ids.md` — that file is vendored from core, so a loop-local
# addition to it is reverted by the next `sync-scaffold.sh` run (#581).
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
def _slice_ac_section(body: str) -> str:
    """Return the text of the Acceptance criteria section only (bold-preamble or ATX)."""
    return _wu_sections.slice_acceptance_criteria(body)


def _slice_section(body: str, section_name: str) -> str:
    """Return content between a named section heading and the next heading."""
    return _wu_sections.slice_wu_section(body, section_name)


# Interpreters / super-generic words that don't distinguish one gate command
# from another — excluded from a command's signature tokens (#176).
_GATE_TOKEN_STOP = {
    "python", "python3", "bash", "sh", "run", "exec", "discover",
    "report", "source", "true", "false",
}
_GATE_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.:+-]{2,}")
# Verification prose that delegates to the whole gate set — treat as
# referencing every gate so a legitimate "all gates pass" phrasing is not
# flagged.
_UMBRELLA_GATES_RE = re.compile(r"(?i)\b(all|every|entire|full|the)\b[^.\n]{0,24}\bgate")


def _must_reference_gate_signatures(feature_dir: Path) -> list[tuple[str, set[str]]]:
    """Return [(gate_name, signature_tokens)] for OPT-IN must-reference gates (#176).

    Reads ``<project>/.specfuse/verification.yml`` (``feature_dir`` is
    ``.../.specfuse/features/<name>``) and includes only `code` gates that set
    ``wu_must_reference: true``. This is deliberately opt-in: warning on every
    declared gate is noise on real multi-gate projects (leak-scan, hygiene
    bats, etc. that an individual WU has no business naming). A project flags
    the gates whose fix is mechanical over a WU's own output — formatters,
    auto-fixable linters — the class #175 shows can burn the whole attempt
    budget when a WU forgets them. Empty list (the check no-ops) when the file
    is absent, unparseable, or no gate opts in. Each gate's token set is the
    distinctive words of its command plus the gate name, lowercased.
    """
    vpath = feature_dir.parent.parent / "verification.yml"
    if not vpath.is_file():
        return []
    try:
        cfg = _miniyaml.parse(vpath.read_text()) or {}
    except _miniyaml.MiniYAMLError:
        return []
    out: list[tuple[str, set[str]]] = []
    for gate in cfg.get("code") or []:
        if not isinstance(gate, dict) or gate.get("wu_must_reference") is not True:
            continue
        name = str(gate.get("name") or "").strip()
        command = str(gate.get("command") or "")
        tokens = {t.lower() for t in _GATE_TOKEN_RE.findall(command)
                  if t.lower() not in _GATE_TOKEN_STOP}
        if name:
            tokens.add(name.lower())
        if tokens:
            out.append((name or command[:40], tokens))
    return out


def _unreferenced_code_gates(
    verification_text: str, signatures: list[tuple[str, set[str]]],
) -> list[str]:
    """Names of code gates whose tokens *verification_text* references none of.

    An umbrella "all gates" phrasing short-circuits to [] (author delegated).
    """
    if _UMBRELLA_GATES_RE.search(verification_text):
        return []
    low = verification_text.lower()
    return [name for name, tokens in signatures
            if not any(tok in low for tok in tokens)]


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
    if j >= len(lines):
        # See loop.read_frontmatter: an opening `---` with no closing one made
        # the scan run off the end and parse the document as frontmatter,
        # reporting the failure against an arbitrary body line (#306).
        raise _miniyaml.MiniYAMLError(
            f"{path}: frontmatter block opened with `---` on line 1 but is "
            f"never closed — add a `---` line to end it. Every line after it "
            f"was read as frontmatter, so no check could evaluate this file."
        )
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


# Ceremony WU types systematically under-estimated in the field: close and
# plan-next WUs ran 2.8-5.2x over on $2-3 estimates across FEAT-2026-0049
# (clabonte/generator), poisoning every calibration built on the plans (#201).
# The floor is a WARN threshold, not a cap — estimates below it are almost
# certainly wishful, not cheap.
# Per-type, because the types do not cost the same: across 158 closing WUs in
# 9 repositories the medians were $3.57 / $2.73 / $2.01 and the p90s $6.10 /
# $5.42 / $4.34. Each floor sits at roughly its own p90. A single flat figure
# either warns on a correctly-drafted close-intermediate or lets a wishful
# plan-next through. Canonical statement: planning-discipline.md §5 — these
# values are bound to it by tests/test_planning_cost_floor.py.
CEREMONY_COST_FLOORS_USD = {
    "plan-next": 6.0,
    "close": 5.0,
    "close-intermediate": 4.5,
}
_CEREMONY_TYPES = frozenset(CEREMONY_COST_FLOORS_USD)


def check_planned_cost(feature_dir: Path, plan_fm: dict, gates: list) -> None:
    """Emit WARN for missing planned_cost_usd on WUs and PLAN.md.

    Sealed WUs (wu status=done AND plan status=done) are skipped silently —
    backfilling cost estimates on history is pointless.  Active or draft WUs
    get the WARN.  Ceremony-type WUs (close/close-intermediate/plan-next)
    with a planned cost below their type's CEREMONY_COST_FLOORS_USD entry get
    (#201).  PLAN.md is compared against the sum of WU planned costs;
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
                # Floor applies to POSITIVE estimates only: the observed
                # failure is a real-but-wishful $2-3 estimate anchoring
                # calibration, not an explicit 0.00 (the scaffold's
                # "unestimated" placeholder, already visible as such).
                wu_type = wfm.get("type")
                floor = CEREMONY_COST_FLOORS_USD.get(wu_type)
                if not is_sealed and floor is not None and 0 < float(planned) < floor:
                    print(
                        f"WARN: {wfile}: planned_cost_usd "
                        f"${float(planned):.2f} is below the "
                        f"${floor:.2f} floor for '{wu_type}' WUs "
                        f"(planning-discipline.md §5). Do not raise a floor to "
                        f"absorb a retry — a closing-WU retry is a defect to "
                        f"diagnose; see close-discipline.md §4."
                    )

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


# Planning-discipline section names (#201, second half). Canonical since the
# FEAT-2026-0049 planning-discipline drop (PR #211): PLAN.md carries the two
# ADR sections; each gate file carries the arming-discipline section. Names
# are shared vocabulary with downstream planning tooling — do not rename here
# without a template/coordination change.
PLAN_DISCIPLINE_SECTIONS = (
    "Existing-mechanism search",
    "Escalation-predicate satisfiability",
)
GATE_ARMING_SECTION = "Arming discipline"



# Closing-WU guards check literal strings in the artifacts a closing WU writes,
# and they check them AFTER the WU has run — so a mismatch costs a full
# re-dispatch, not a re-arm. Measured across 158 closing WUs in 9 repositories:
# 28% of all closing-WU spend went to attempts the driver refused, and guards
# whose literals appeared in no authoring surface accounted for 45% of that.
#
# The guard itself cannot move earlier: it inspects output that does not exist
# until the WU runs. What CAN move earlier is the prediction. If a closing WU's
# body never tells the agent to produce the literal its guard will demand, the
# refusal is foreseeable at arm time, for free.
#
# Verified against the two refusals that motivated this: FEAT-2026-0069's
# G1-CLOSE-INTERMEDIATE (no `## Gate 1` instruction -> $4.45) and G1-PLAN
# (instructed `GATE-01-REVIEW.md`, guard wanted `GATE-02` -> $8.61). Both are
# flagged by this check.
#
# Each entry: WU type -> (regex over the BODY, human label, guard it predicts).
# `{n}` is substituted with the WU's own gate number, `{n1}` with n+1.
# Requirements are the guards' own, documented in close-discipline.md §4.
_GUARD_LITERAL_PREDICTIONS = {
    "close-intermediate": (
        r"`[^`]*#{{1,3}} Gate {n}\b[^`]*`",
        "`## Gate {n}` (the heading assert_retrospective_gate_section requires "
        "in RETROSPECTIVE.md)",
        "assert_retrospective_gate_section",
    ),
    "close": (
        r"`[^`]*## Cost analysis[^`]*`",
        "`## Cost analysis` (the heading assert_cost_analysis_section_when_met "
        "requires in RETROSPECTIVE.md when verdict is `met`)",
        "assert_cost_analysis_section_when_met",
    ),
    "plan-next": (
        r"`[^`]*GATE-{n1:02d}-REVIEW\.md[^`]*`",
        "`GATE-{n1:02d}-REVIEW.md` (assert_gate_review_exists names the review "
        "for the gate being DRAFTED, not the one being closed)",
        "assert_gate_review_exists",
    ),
}

# Matches only inside backticks. The WU's own H1 ("# Gate 1 close-intermediate
# ...") otherwise satisfies a bare substring search, which would bless the exact
# WU that went on to be refused — a false pass is worse than no check.
_GATE_NUM_RE = re.compile(r"/G(\d+)-")


def check_closing_guard_literals(feature_dir: Path, gates: list) -> None:
    """WARN when a closing WU's body omits a literal its guard will demand.

    WARN, never ERROR: 22% of this repo's existing closing WUs would fail it,
    and they are history. An ERROR predicate unsatisfiable on a populated tree
    is the failure `[FEAT-2026-0015/G2-CLOSE]` records. Findings are advisory
    and the exit code is unchanged.
    """
    for gate in gates:
        for entry in gate.get("work_units") or []:
            wfile = feature_dir / str(entry.get("file", ""))
            if not wfile.is_file():
                continue
            try:
                wfm, wbody = read_frontmatter(wfile)
            except Exception:  # noqa: BLE001 - malformed WU is another check's finding
                continue
            spec = _GUARD_LITERAL_PREDICTIONS.get(wfm.get("type"))
            if spec is None:
                continue
            if wfm.get("status") == "done":
                continue  # sealed; backfilling instructions on history is pointless
            gate_m = _GATE_NUM_RE.search(str(wfm.get("id", "")))
            if gate_m is None:
                continue
            n = int(gate_m.group(1))
            pattern, label, guard = spec
            if re.search(pattern.format(n=n, n1=n + 1), wbody):
                continue
            print(
                f"WARN: {wfile}: body does not instruct the agent to produce "
                f"{label.format(n=n, n1=n + 1)}. {guard} checks this AFTER "
                f"dispatch, so the refusal costs a full re-attempt. See "
                f"close-discipline.md §4."
            )


_AUTOCLOSE_DEBT_MARKER_RE = re.compile(r"<!--\s*specfuse:autoclose-debt\s+gate=(\d+)")

_PRODUCES_DISPATCHABLE_STATUSES = {"draft", "pending", "ready"}
_PRODUCES_EXEMPT_PATHS = {"events.jsonl"}


def check_produces_satisfiability(feature_dir: Path, gates: list) -> None:
    """WARN when a dispatchable WU's `produces:` path was already delivered.

    Exact string match only against a `done` WU's `produces:` entries in the
    same feature — a glob is compared literally, not expanded (expansion
    semantics belong to the presence gate, not this lint). Parallel drafts
    sharing a surface are fine (the earlier WU must be `done`), and a WU's own
    file / `events.jsonl` never count as a clash. WARN-only; never appends to
    the errors list. See FEAT-2026-0055/T01, FEAT-2026-0066/T04.
    """
    records = []  # (wid, wfile, status, produces_entries)
    for gate in gates:
        for entry in gate.get("work_units") or []:
            wid, wfile = entry.get("id"), entry.get("file")
            if not wid or not wfile:
                continue
            wpath = feature_dir / wfile
            if not wpath.exists():
                continue
            wfm, _ = read_frontmatter(wpath)
            produces_raw = wfm.get("produces")
            if not produces_raw:
                continue
            raw_entries = produces_raw if isinstance(produces_raw, list) else [produces_raw]
            cleaned = set()
            for p in raw_entries:
                p_s = str(p).strip()
                if not p_s or p_s in _PRODUCES_EXEMPT_PATHS or p_s == wfile:
                    continue
                cleaned.add(p_s)
            if cleaned:
                records.append((wid, wfile, wfm.get("status", ""), cleaned))

    done_paths: dict = {}  # path -> (wid, wfile), first done WU declaring it
    for wid, wfile, status, entries in records:
        if status != "done":
            continue
        for p in entries:
            done_paths.setdefault(p, (wid, wfile))

    for wid, wfile, status, entries in records:
        if status not in _PRODUCES_DISPATCHABLE_STATUSES:
            continue
        for p in entries:
            match = done_paths.get(p)
            if match is None or match[0] == wid:
                continue
            done_wid, done_wfile = match
            print(
                f"WARN: {wfile}: {wid} declares produces path {p!r}, but "
                f"done WU {done_wid} ({done_wfile}) already delivered it. "
                f"Drop the path, or state the incremental edit this WU makes "
                f"to it in the body."
            )


_DNT_CARVEOUT_RE = re.compile(r"(?i)\bexcept\b")
_DNT_ALLOW_ENUM_RE = re.compile(
    r"(?i)\b(?:files?|paths?)(?:\s+that)?\s+change\b|\badds?\b|\bnew\b"
)
_DNT_AMBIGUOUS_PHRASE_RE = re.compile(
    r"(?i)\bexisting\b|\bgenerated (?:by|from)\b|\boutput of\b"
    r"|\bhand-edit\b|\bdirect edit\b"
)
_DNT_CONTAINER_TOKEN_RE = re.compile(r"(?i)\bin\s*`([^`]+)`")
_BACKTICK_TOKEN_RE = re.compile(r"`([^`]+)`")


def _split_dnt_clauses(dnt_text: str) -> list[str]:
    """Split Do-not-touch prose into clauses on ';' and sentence-ending '.'.

    Physical lines are joined first (a wrapped sentence spans them; the
    bold-preamble form's canonical body is prose, not one clause per line),
    and a delimiter inside backticks never splits a clause — a path like
    `SKILL.md` must not fracture on its own period.
    """
    joined = " ".join(
        line.strip().lstrip("-*").strip()
        for line in dnt_text.splitlines()
        if line.strip()
    )
    clauses: list[str] = []
    buf: list[str] = []
    in_backtick = False
    for ch in joined:
        if ch == "`":
            in_backtick = not in_backtick
            buf.append(ch)
            continue
        if not in_backtick and ch in ";.":
            clause = "".join(buf).strip()
            if clause:
                clauses.append(clause)
            buf = []
            continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        clauses.append(tail)
    return clauses


def _extract_do_not_touch_patterns(dnt_text: str) -> tuple[list[str], list[str], set[str]]:
    """Return (prohibit_patterns, ambiguous_patterns, allowed_literals) from a
    Do-not-touch body.

    Only backtick-quoted tokens containing '/', '*', or a file extension count
    as binding path patterns — a plain-prose mention of a path never fires the
    boundary check (no semantic judgment, no false ERROR on illustrative
    prose). Extraction is prohibition-scoped, per clause (split on ';' and
    sentence-ending '.'):

    - A clause carrying an "except" carve-out (the shape FEAT-2026-0066/T04's
      re-armed body used) contributes no patterns at all.
    - A clause carrying an allow-enumeration signal ("These/Paths that
      change:" / "adds" / "new" — the FEAT-2026-0023/T01 shape, where the
      WU's own deliverables are listed, not forbidden) contributes no
      patterns to either bucket. Its backtick tokens are instead recorded as
      `allowed_literals`: exact paths the WU has explicitly declared it is
      creating or changing. A later clause's *pattern* may still coincide
      with one of these paths (e.g. "any other `.github/workflows/*` file"
      after enumerating the one workflow file this WU adds) — the caller
      treats an exact `allowed_literals` hit as never a match, regardless of
      which clause the pattern came from, since the enumeration is a
      definite allow-list for that literal path.
    - A clause carrying a semantic qualifier cannot be resolved without
      knowing something about the WU's own edit that the lint has no way to
      check. Its path-like tokens go in `ambiguous_patterns` — the caller
      downgrades a match to WARN, never ERROR, per this WU's design rule:
      ERROR only on certainty. Two qualifier shapes, both drawn from the
      retrospective's real fixtures:
      - "existing" (FEAT-2026-0070/T08: "every existing `check_*`
        function") — is a given produces path pre-existing or newly
        created by this WU?
      - "generated by/output of/hand-edit/direct edit" (FEAT-2026-0069/T08,
        FEAT-2026-0070/T03: "`.../SKILL.md` as a direct edit — it is an
        output of `scripts/sync-scaffold.sh`") — the prohibition is on
        *manual* editing; a produces declaration doesn't say whether the
        WU reaches the path by hand or by running the generator.
    - A token immediately preceded by "in" (e.g. "`discover_components()`
      and `_STACK_A_PATTERNS` in `tests/test_x.py`" — FEAT-2026-0069/T03)
      names a container, not the prohibition itself: the forbidden things
      are the symbols named before "in", and the file may otherwise be
      touched freely. Also goes to `ambiguous_patterns` — the lint can spot
      the grammatical shape but not verify the symbols went untouched.
    - Everything else is an unqualified prohibition and goes in
      `prohibit_patterns`.
    """
    prohibit: list[str] = []
    ambiguous: list[str] = []
    allowed_literals: set[str] = set()
    for clause in _split_dnt_clauses(dnt_text):
        if _DNT_CARVEOUT_RE.search(clause):
            continue
        if _DNT_ALLOW_ENUM_RE.search(clause):
            for tok in _BACKTICK_TOKEN_RE.findall(clause):
                tok = tok.strip()
                if tok:
                    allowed_literals.add(tok)
            continue
        clause_ambiguous = bool(_DNT_AMBIGUOUS_PHRASE_RE.search(clause))
        container_tokens = {
            m.group(1).strip() for m in _DNT_CONTAINER_TOKEN_RE.finditer(clause)
        }
        for tok in _BACKTICK_TOKEN_RE.findall(clause):
            tok = tok.strip()
            if not tok:
                continue
            if "/" in tok or "*" in tok or re.search(r"\.[A-Za-z0-9]+$", tok.rstrip("/")):
                bucket = (
                    ambiguous if (clause_ambiguous or tok in container_tokens)
                    else prohibit
                )
                bucket.append(tok)
    return prohibit, ambiguous, allowed_literals


def _match_dnt_boundary(
    surface: str,
    prohibit_patterns: list[str],
    ambiguous_patterns: list[str],
    allowed_literals: set[str],
) -> tuple[str, str] | None:
    """Return (severity, pattern) for the first pattern `surface` matches —
    ERROR if prohibited, WARN if only ambiguous. A surface the WU has
    explicitly enumerated as its own new/changed deliverable never matches,
    even against a pattern found in an unrelated clause."""
    if surface in allowed_literals:
        return None
    for pat in prohibit_patterns:
        if fnmatch.fnmatch(surface, pat):
            return ("ERROR", pat)
    for pat in ambiguous_patterns:
        if fnmatch.fnmatch(surface, pat):
            return ("WARN", pat)
    return None


def check_produces_shape(feature_dir: Path, gates: list) -> list[str]:
    """ERROR when a WU's `produces:` entry is a directory rather than a file
    or glob.

    Same family as `check_produces_boundary` below, and the same argument: the
    driver refuses this outright, but only after a full `claude -p` session.
    Since the agent cannot edit its own frontmatter, every retry is
    byte-identical -- a real feature paid $6.42 and 20.6 minutes across three
    of them before `spinning_detected` fired, while `specfuse-lint` reported
    `OK - structurally valid` throughout (#593).

    Every input is static, so this belongs in the pre-dispatch checklist. The
    message is rendered by `loop.produces_shape_error`, the same function the
    driver's guards call, so all three surfaces read identically rather than
    drifting into three descriptions of one rule.

    Applies to every WU with a `produces:` entry regardless of status: a `done`
    WU with a directory entry is a folder authored against the pre-0.9.0
    contract, and reporting it is how a migrating project finds them all at
    once instead of one dispatch at a time.
    """
    from .loop import produces_shape_error

    found: list[str] = []
    for gate in gates:
        for entry in gate.get("work_units") or []:
            wid, wfile = entry.get("id"), entry.get("file")
            if not wid or not wfile:
                continue
            wpath = feature_dir / wfile
            if not wpath.exists():
                continue
            wfm, _ = read_frontmatter(wpath)
            produces_raw = wfm.get("produces")
            if not produces_raw:
                continue
            raw_entries = (
                produces_raw if isinstance(produces_raw, list) else [produces_raw]
            )
            for p in raw_entries:
                p_s = str(p).strip()
                if not p_s:
                    continue
                err = produces_shape_error(p_s)
                if err:
                    found.append(
                        f"ERROR: {wfile}: {wid} {err}. assert_declared_"
                        f"deliverables refuses this after a full dispatch "
                        f"attempt, and a retry cannot help — the agent cannot "
                        f"edit its own frontmatter. See #593."
                    )
    return found


def check_produces_boundary(feature_dir: Path, gates: list) -> list[str]:
    """ERROR when a WU's own `produces:` path (or `produces_driver_helper`
    surface) falls inside its own Do-not-touch section's paths.

    A structural deadlock, not a review nit: the WU cannot both deliver the
    path and honor its own boundary, and `assert_produces_in_diff` only
    catches this AFTER a full dispatch attempt — the cost FEAT-2026-0066/T04
    paid (3 attempts + an operator re-arm) for a conjunction this lint makes
    un-armable up front. See FEAT-2026-0070 (earlier-enforcer-names-the-
    later-one): the ERROR names the post-attempt guard it preempts so the
    author isn't left to rediscover the connection.
    """
    found: list[str] = []
    for gate in gates:
        for entry in gate.get("work_units") or []:
            wid, wfile = entry.get("id"), entry.get("file")
            if not wid or not wfile:
                continue
            wpath = feature_dir / wfile
            if not wpath.exists():
                continue
            wfm, wbody = read_frontmatter(wpath)
            dnt_text = _slice_section(wbody, "Do not touch")
            if not dnt_text.strip():
                continue
            prohibit_patterns, ambiguous_patterns, allowed_literals = (
                _extract_do_not_touch_patterns(dnt_text)
            )
            if not prohibit_patterns and not ambiguous_patterns:
                continue

            produces_raw = wfm.get("produces")
            produces_entries = (
                produces_raw if isinstance(produces_raw, list)
                else [produces_raw] if produces_raw else []
            )
            for p in produces_entries:
                p_s = str(p).strip()
                if not p_s:
                    continue
                hit = _match_dnt_boundary(
                    p_s, prohibit_patterns, ambiguous_patterns, allowed_literals
                )
                if hit is None:
                    continue
                severity, pat = hit
                if severity == "ERROR":
                    found.append(
                        f"ERROR: {wfile}: {wid} declares produces path "
                        f"{p_s!r}, which its own Do-not-touch section "
                        f"forbids via {pat!r}. This is a structural "
                        f"deadlock — assert_produces_in_diff would refuse "
                        f"it after a full dispatch attempt. Drop the path "
                        f"from produces, narrow the Do-not-touch pattern, "
                        f"or add an explicit 'except' carve-out. See "
                        f"FEAT-2026-0066/T04, FEAT-2026-0070."
                    )
                else:
                    print(
                        f"WARN: {wfile}: {wid} declares produces path "
                        f"{p_s!r}, which matches Do-not-touch pattern "
                        f"{pat!r} — the boundary's wording ('existing', "
                        f"'generated by', 'in <file>', or similar) makes "
                        f"this pattern's scope ambiguous without semantic "
                        f"judgment this lint does not have. Confirm by hand "
                        f"before arming, or reword the boundary to name the "
                        f"protected surface unambiguously."
                    )

            pdh_raw = wfm.get("produces_driver_helper")
            if pdh_raw:
                pdh_s = str(pdh_raw).strip()
                surface = pdh_s.split("—")[0].split("--")[0].strip().strip("`\"'")
                if surface:
                    hit = _match_dnt_boundary(
                        surface, prohibit_patterns, ambiguous_patterns, allowed_literals
                    )
                    if hit is not None:
                        severity, pat = hit
                        if severity == "ERROR":
                            found.append(
                                f"ERROR: {wfile}: {wid} declares "
                                f"produces_driver_helper surface {surface!r}, "
                                f"which its own Do-not-touch section forbids "
                                f"via {pat!r}. This is a structural deadlock — "
                                f"assert_produces_in_diff would refuse it "
                                f"after a full dispatch attempt. Drop/narrow "
                                f"the boundary, or add an explicit 'except' "
                                f"carve-out. See FEAT-2026-0066/T04, "
                                f"FEAT-2026-0070."
                            )
                        else:
                            print(
                                f"WARN: {wfile}: {wid} declares "
                                f"produces_driver_helper surface {surface!r}, "
                                f"which matches Do-not-touch pattern {pat!r} "
                                f"— the boundary's wording makes this "
                                f"pattern's scope ambiguous without semantic "
                                f"judgment this lint does not have. Confirm "
                                f"by hand before arming."
                            )
    return found


def check_autoclose_debt_prediction(feature_dir: Path, gates: list) -> None:
    """WARN when a terminal close WU's body never instructs reconciling a
    marked predecessor auto-close debt (`FEAT-2026-0070/T07`'s
    ``assert_autoclose_debt_reconciled``).

    Conditional on feature state, unlike `_GUARD_LITERAL_PREDICTIONS`: it
    fires only when `RETROSPECTIVE.md` already carries T06's
    `<!-- specfuse:autoclose-debt gate=N ... -->` marker for a gate earlier
    than the terminal one. No marker, no WARN — a static per-type row would
    fire on every terminal close in every project, which is the noise this
    check exists to avoid. WARN-only, exit code unchanged, same discipline as
    `check_closing_guard_literals`.
    """
    retro_path = feature_dir / "RETROSPECTIVE.md"
    if not retro_path.exists():
        return
    retro_text = retro_path.read_text()

    terminal_gate_gnum = next(
        (g.get("gate", "?") for g in reversed(gates) if g.get("work_units")), None
    )
    if terminal_gate_gnum is None:
        return

    predecessor_gates = sorted({
        int(m.group(1))
        for m in _AUTOCLOSE_DEBT_MARKER_RE.finditer(retro_text)
        if int(m.group(1)) < terminal_gate_gnum
    })
    if not predecessor_gates:
        return

    terminal_gate = next(g for g in gates if g.get("gate") == terminal_gate_gnum)
    for entry in terminal_gate.get("work_units") or []:
        wfile = feature_dir / str(entry.get("file", ""))
        if not wfile.is_file():
            continue
        try:
            wfm, wbody = read_frontmatter(wfile)
        except Exception:  # noqa: BLE001 - malformed WU is another check's finding
            continue
        if wfm.get("type") != "close":
            continue
        if wfm.get("status") == "done":
            continue  # sealed; backfilling instructions on history is pointless
        unmentioned = [
            g for g in predecessor_gates
            if not re.search(rf"\bgate\s+{g}\b", wbody, re.IGNORECASE)
        ]
        if not unmentioned:
            continue
        print(
            f"WARN: {wfile}: RETROSPECTIVE.md carries an auto-close debt "
            f"marker for gate(s) {', '.join(str(g) for g in unmentioned)}, "
            f"but this terminal close WU's body never instructs the agent to "
            f"reconcile it. assert_autoclose_debt_reconciled checks this "
            f"AFTER dispatch, so the refusal costs a full re-attempt. See "
            f"close-discipline.md §4."
        )


def check_done_feature_gates(feature_dir: Path, plan_fm: dict) -> list[str]:
    """A `status: done` feature must have every gate `status: passed` (#287).

    Catches the drift class where a feature's terminal-flip machinery never
    ran (legacy closing sequence, pre-verdict-contract close WU) and left a
    gate at `open`/`awaiting_review` while PLAN.md already reads `done`.
    Excluded features (DONE_FEATURE_GATE_EXCLUSIONS) are ones where that gap
    is correct, not drift — see the reasons recorded there.

    GATE-NN-REVIEW.md artifacts carry no `status` frontmatter and are not
    gate files, so they're skipped by name.
    """
    if plan_fm.get("status") != "done":
        return []
    if feature_dir.name in DONE_FEATURE_GATE_EXCLUSIONS:
        return []
    errs: list[str] = []
    for gate_path in sorted(feature_dir.glob("GATE-*.md")):
        if gate_path.stem.endswith("-REVIEW"):
            continue
        gfm, _ = read_frontmatter(gate_path)
        gstatus = gfm.get("status")
        if gstatus != "passed":
            errs.append(
                f"{feature_dir.name}: PLAN.md status is 'done' but "
                f"{gate_path.name} is status: {gstatus!r}, not 'passed'"
            )
    return errs


def check_planning_sections(
    feature_dir: Path, plan_fm: dict, plan_body: str, gates: list,
) -> None:
    """WARN when the planning-discipline sections are absent (#201).

    Presence-only: the PLAN template's sections allow an explicit n/a line, so
    content is the arming reviewer's job — this check only catches the section
    never being written at all (pre-0.3.22 drafts, or a plan-next that dropped
    it). Sealed features (plan status done/abandoned) are history and skipped.
    WARN-only, exit code 0, like the rest of the planning-lint family.
    """
    if plan_fm.get("status") in ("done", "abandoned"):
        return
    for section in PLAN_DISCIPLINE_SECTIONS:
        if not _slice_section(plan_body, section).strip():
            print(
                f"WARN: {feature_dir}/PLAN.md: missing '{section}' section "
                f"(planning-discipline; write it or an explicit 'n/a' line). "
                f"See .specfuse/rules/planning-discipline.md."
            )
    for g in gates:
        gate_file = g.get("file")
        if not gate_file:
            continue
        gate_path = feature_dir / gate_file
        if not gate_path.exists():
            continue
        gfm, gbody = read_frontmatter(gate_path)
        if gfm.get("status") == "passed":
            continue
        if not _slice_section(gbody, GATE_ARMING_SECTION).strip():
            print(
                f"WARN: {gate_file}: missing '{GATE_ARMING_SECTION}' section "
                f"(runtime-probe / flag-scope / predicate checks before "
                f"arming). See .specfuse/rules/planning-discipline.md."
            )


def lint(feature_dir: Path) -> list[str]:
    """Lint a feature folder, converting an unparseable file into a finding.

    A malformed WU used to abort the whole run with a traceback, which made
    the folder unevaluable by *every* check rather than one (#306). The lint's
    job is to report what is wrong with a folder; a file it cannot parse is
    the most basic thing that can be wrong with one, so it is a finding like
    any other. Callers still get a non-empty error list and a non-zero exit.
    """
    try:
        return _lint_impl(feature_dir)
    except _miniyaml.MiniYAMLError as exc:
        return [f"ERROR: unparseable frontmatter — {exc}"]


def _lint_impl(feature_dir: Path) -> list[str]:
    errs: list[str] = []
    plan = feature_dir / "PLAN.md"
    if not plan.exists():
        return [f"missing {plan}"]

    fm, body = read_frontmatter(plan)
    missing = REQUIRED_FEATURE_KEYS - set(fm)
    if missing:
        errs.append(f"PLAN.md frontmatter missing keys: {sorted(missing)}")

    # Feature status must be a value the driver recognizes (#185). An
    # unrecognized status passes every other check and then behaves
    # differently at dispatch — the shape #183 (deferred passed lint,
    # dispatched anyway) exposed. Only validate when present; the missing-key
    # check above already covers absence.
    if "status" in fm and fm["status"] not in VALID_FEATURE_STATUS:
        errs.append(
            f"PLAN.md frontmatter status {fm['status']!r} is not a recognized "
            f"feature status {sorted(VALID_FEATURE_STATUS)}"
        )

    # Opt-in must-reference gate signatures, loaded once for the
    # Verification-reference WARN below (#176). Empty unless the project flags
    # gates with `wu_must_reference: true`.
    must_ref_gate_sigs = _must_reference_gate_signatures(feature_dir)

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
                # Gate status must be a value the driver recognizes (#185).
                if "status" in gfm and gfm["status"] not in VALID_GATE_STATUS:
                    errs.append(
                        f"{gate_file_rel}: gate status {gfm['status']!r} is not "
                        f"a recognized gate status {sorted(VALID_GATE_STATUS)}"
                    )
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
                # in_progress/in_review: dispatch-transient states the driver itself
                # writes mid-session (flip to in_progress at dispatch, in_review while
                # the gate set runs) before the agent has written its verdict; the
                # verdict requirement on a *completed* close WU is owned by
                # assert_verdict_well_formed (specfuse/loop/loop.py), which runs at
                # outcome time — not by plan-lint firing on a transient state.
                if wu_status not in {
                    "draft", "pending", "done", "abandoned", "blocked_human",
                    "in_progress", "in_review",
                }:
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

            # Verification ↔ must-reference gate WARN (#176). For gates a
            # project has flagged `wu_must_reference: true` — those whose fix is
            # mechanical over a WU's own output (formatters, auto-fixable
            # linters) — the driver enforces them regardless of what a WU's
            # Verification names. A session not told to run one writes code that
            # fails it and, per #175, can burn the whole attempt budget on the
            # mechanical failure. Flag at lint time, at zero model cost. Opt-in,
            # so no noise on projects that don't flag any gate.
            if wu_type_val == "implementation" and must_ref_gate_sigs:
                verif_text = _slice_section(wbody, "Verification")
                unref = _unreferenced_code_gates(verif_text, must_ref_gate_sigs)
                if unref:
                    print(
                        f"WARN: {wfile}: Verification references none of the "
                        f"must-reference gate(s): {', '.join(unref)}. The driver "
                        f"runs them regardless; name each so the session knows to "
                        f"satisfy it before finishing (#176)."
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
            #
            # "almost always" is the operative word, and #259 found the
            # exception: a genuine root-level deliverable (package.json,
            # pyproject.toml) resolves from the repo root and passes presence in
            # the plain form. Warning there sent authors to './package.json',
            # which `assert_produces_in_diff` then rejected — the two guards
            # were mutually exclusive for a root file. So the warn is suppressed
            # when the bare path IS a real file at the repo root, using the
            # presence gate's own oracle (cwd-relative resolution: the driver
            # runs both from the repo root), and the remediation now names the
            # `git diff --name-only` spelling the diff cross-check consumes
            # rather than an unqualified "repo-root-relative path" an author
            # reasonably reads as "prefix it".
            produces_raw = wfm.get("produces")
            if produces_raw:
                entries = produces_raw if isinstance(produces_raw, list) else [produces_raw]
                for entry in entries:
                    entry_s = str(entry).strip()
                    if not entry_s or "/" in entry_s:
                        continue
                    if Path(entry_s).exists():
                        continue
                    print(
                        f"WARN: {wfile}: produces path {entry_s!r} is a bare "
                        f"filename and no such file exists at the repo root — "
                        f"produces paths are resolved relative to the repo root, "
                        f"and WU deliverables usually live under .specfuse/, "
                        f"modules/, environments/, the feature dir, …. Spell it "
                        f"exactly as `git diff --name-only` reports it (no './' "
                        f"prefix — the diff cross-check rejects that form), or "
                        f"the presence gate will fail every attempt and spin to "
                        f"a block. See #77, #259."
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
    # Planning-discipline section presence (#201): WARN-only.
    check_planning_sections(feature_dir, fm, body, gates)
    check_closing_guard_literals(feature_dir, gates)
    check_autoclose_debt_prediction(feature_dir, gates)
    check_produces_satisfiability(feature_dir, gates)
    errs.extend(check_produces_shape(feature_dir, gates))
    errs.extend(check_produces_boundary(feature_dir, gates))
    errs.extend(check_done_feature_gates(feature_dir, fm))

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

    # open_questions: required explicit list in the GATE-{N+1}-REVIEW.md
    # frontmatter (FEAT-2026-0053/T02). Missing field != empty list — under
    # `auto` (gate 2) a missing field parks the feature, so plan-next must
    # write it explicitly, even as `open_questions: []`. Silent when the
    # review file itself is absent — assert_gate_review_exists already
    # owns that failure; this check must not pile on.
    review_path = feature_dir / gate_review_filename(next_gate_num)
    if review_path.exists():
        review_fm, _ = read_frontmatter(review_path)
        if "open_questions" not in review_fm:
            warns.append(
                f"{review_path.name}: missing 'open_questions:' frontmatter "
                f"field — a required explicit list (empty list means nothing "
                f"requires an answer before execution; a missing field is not "
                f"an empty list and parks the feature under `auto`). See "
                f".specfuse/templates/WU.template.md frontmatter notes."
            )

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
        usage="lint_plan.py <feature_dir> [--just-closed-gate N] [--closing]",
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
    parser.add_argument(
        "--closing",
        action="store_true",
        help=(
            "Lint the feature's in-progress closing WU against the "
            "closing-requirement registry (see closing_requirements.py), "
            "pre-squash. Exits 0/CLOSING-READY or 1 with one line per unmet "
            "requirement. Skips the structural lint entirely."
        ),
    )
    args = parser.parse_args()
    feature_dir = args.feature_dir

    if args.closing:
        from .lint_closing import main_closing
        return main_closing(feature_dir)

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
