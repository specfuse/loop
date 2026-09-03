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

Usage:  specfuse lint .specfuse/features/FEAT-XXXX-slug
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from . import _miniyaml
from . import _wu_sections
from .closing_requirements import (
    LEARNINGS_PATH,
    LEARNINGS_PENDING_FILENAME,
    gate_review_filename,
    learnings_staging_is_required,
)
from .criteria_state import CRITERIA_FILENAME_RE
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
# and WU frontmatter. The event envelope enforces its own `correlation_id`
# pattern (`data/schemas/event.schema.json`, vendored from the methodology core
# and never edited here); since #1433 that envelope carries all three documented
# work-unit shapes, so the two surfaces agree on their own. The driver-local
# registry `data/schemas/driver-event.schema.json` — read by
# `validate_event.load_validator` on a deep copy, the fall-through
# FEAT-2026-0060 established for `event_type` and FEAT-2026-0073 extended to
# correlation IDs — is now an inert safety net against an older schema root.
#
# ADDING A NEW `<NAME>` SEGMENT: it belongs in core's envelope. Update this
# pattern AND that registry's `closing_names` in the same change, then get core
# to adopt it — until it does, only the registry's widening makes envelope
# validation accept what the linter already does. This note lives here, at the change site, rather than in
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


# §1-§3 obligations from close-discipline.md, matched on the phrasing an author
# actually writes. Imprecise by nature — the same heuristic shape the oracle_env
# WARN already uses, on the same reasoning: a false positive costs one flag, a
# false negative costs an unverified feature (#293).
LOAD_BEARING_CLOSE_PATTERNS = (
    re.compile(r"\bre-?run\s+fresh\b", re.IGNORECASE),
    re.compile(r"\bre-?verif(?:y|ied|ication)\b", re.IGNORECASE),
    re.compile(r"\bre-?observe\b", re.IGNORECASE),
    re.compile(r"\bfresh\b[^.\n]{0,40}\b(?:run|output|dir|directory|clone)\b",
               re.IGNORECASE),
    re.compile(r"\bnever\s+a?\s*producing\b", re.IGNORECASE),
    re.compile(r"\bself-?report\b", re.IGNORECASE),
    re.compile(r"\bexit\s+codes?\s+read\b", re.IGNORECASE),
    re.compile(r"\bhedged\b", re.IGNORECASE),
    re.compile(r"\bconsumer-?visible\b", re.IGNORECASE),
    re.compile(r"\bcontract\s+change", re.IGNORECASE),
    re.compile(r"\boracles?\s+re-?run\b", re.IGNORECASE),
)

# Durable surfaces a close may be the SOLE writer of. Naming one of these is a
# load-bearing signal by construction rather than by wording — the gap the
# phrase match above cannot close, reported on #293 after FEAT-2026-0063 lost a
# roadmap-reconciliation criterion that contained no verification verb at all.
#
# `LEARNINGS.md` is deliberately NOT in this list, despite being a durable
# surface a skipped close genuinely corrupts (FEAT-2026-0031 lost every entry
# that way). Measured on this repo: 68 of 71 close WUs mention it and 3 declare
# it in `produces:`. A signal present in ~96% of the population separates
# nothing — including it fired this warning on 29 of 55 features, which is the
# shape that trains an operator to ignore it (the #771 lesson). The lesson-loss
# risk is real and stays owned by close-discipline's own guards; this lint
# targets the criteria a phrase match and a *selective* surface test can
# actually discriminate.
_DURABLE_SURFACE_RE = re.compile(
    r"(?:^|[\s`(\[])"
    r"(?:\.specfuse/)?"
    r"(?:roadmap(?:-archive)?\.md"
    r"|CHANGELOG\.md"
    r"|docs/[\w./-]+"
    r"|\.specfuse/rules/[\w./-]+)",
    re.IGNORECASE,
)


def detect_load_bearing_close(ac_section_text: str, feature_dir_name: str) -> bool:
    """Return True iff a close WU's acceptance criteria make it load-bearing (#293).

    Two independent signals, either sufficient:

    1. **Verification phrasing** — a §1-§3 obligation from
       `close-discipline.md`: a fresh oracle re-run, a hedged-verdict record, a
       consumer-visible contract enumeration.
    2. **Surface scope** — the criteria name a durable surface *outside the
       feature's own folder*. Such a close is the only thing that reconciles
       that surface with what the gate produced, so skipping it silently
       corrupts a project surface. This signal is mechanical, which is the
       point: it catches criteria that carry no verification wording.

    `feature_dir_name` scopes signal 2. A close naming files inside its own
    folder — `RETROSPECTIVE.md`, its own `PLAN.md` — is not reaching outside it,
    and treating that as load-bearing would fire on every close in existence and
    turn the warning into noise.
    """
    if not ac_section_text or not ac_section_text.strip():
        return False

    for pat in LOAD_BEARING_CLOSE_PATTERNS:
        if pat.search(ac_section_text):
            return True

    # Signal 2. Drop any mention of the feature's own folder first, so a close
    # citing its own PLAN.md does not read as an outside-surface write.
    scoped = ac_section_text
    if feature_dir_name:
        scoped = re.sub(
            r"\.specfuse/features/" + re.escape(feature_dir_name) + r"[\w./-]*",
            " ", scoped)
    return bool(_DURABLE_SURFACE_RE.search(scoped))


def detect_oracle_verbs(ac_section_text: str) -> list[str]:
    """Return matched oracle-verb strings found in the AC section text."""
    found = []
    for pat in ORACLE_VERB_PATTERNS:
        m = pat.search(ac_section_text)
        if m:
            found.append(m.group(0))
    return found


# Unobservable-AC lint (FEAT-2026-0084/T03). 72 of 101 hedged features across
# 12 repos hedged on criteria of the shape "applied in prod", "consumer repo
# green", "operator confirms" — bullets the loop has no oracle for and so can
# only ever pass on trust at close time. Catch it at arm time instead, on the
# same WARN-then-ERROR escalation shape the oracle_env heuristic above uses.
_UNOBSERVABLE_PHRASES = [
    "in prod", "in production", "applied", "apply to", "live cluster",
    "operator confirms", "operator replies", "human confirms", "real device",
    "store console", "consumer repo", "post-merge", "after merge",
]
_UNOBSERVABLE_PHRASE_RE = re.compile(
    r"(?i)\b(?:" + "|".join(re.escape(p) for p in _UNOBSERVABLE_PHRASES) + r")\b"
)
_AC_BULLET_RE = re.compile(r"^\s*[-*]\s+(.*\S)\s*$")
_BACKTICK_RE = re.compile(r"`[^`]+`")
# Escape hatch: an oracle_env the loop can actually run in. Anything else
# (github_actions_ci, a bespoke label, ...) is treated as an explicit
# declaration that this criterion is observed elsewhere, not by this loop.
_OBSERVABLE_ORACLE_ENVS = frozenset({"macos_local", "linux_docker"})


def detect_unobservable_ac_bullets(ac_section_text: str) -> list[str]:
    """Return AC bullets matching an unobservable phrase with no backticked check."""
    hits = []
    for line in ac_section_text.splitlines():
        m = _AC_BULLET_RE.match(line)
        if not m:
            continue
        bullet = m.group(1)
        if _BACKTICK_RE.search(bullet):
            continue
        if _UNOBSERVABLE_PHRASE_RE.search(bullet):
            hits.append(bullet)
    return hits


def lint_ac_observable(feature_dir: Path) -> list[str]:
    """Flag AC bullets the loop cannot observe (FEAT-2026-0084/T03).

    ERROR when the owning WU is pending/ready (about to be dispatched), WARN
    (printed, not returned) when draft, skipped when done or any other
    status. Escape hatches: `human_only: true`, or `oracle_env` set to
    anything other than macos_local/linux_docker.
    """
    errs: list[str] = []
    for wfile in sorted(feature_dir.glob("WU-*.md")):
        try:
            wfm, wbody = read_frontmatter(wfile)
        except _miniyaml.MiniYAMLError:
            continue
        status = wfm.get("status")
        if status not in ("draft", "pending", "ready"):
            continue
        if wfm.get("human_only") in (True, "true", "True"):
            continue
        oracle_env = wfm.get("oracle_env")
        if oracle_env and oracle_env not in _OBSERVABLE_ORACLE_ENVS:
            continue
        bullets = detect_unobservable_ac_bullets(_slice_ac_section(wbody))
        if not bullets:
            continue
        if status in ("pending", "ready"):
            for bullet in bullets:
                errs.append(
                    f"ERROR: {wfile}: acceptance criterion the loop cannot "
                    f"observe: {bullet!r}"
                )
        else:  # draft
            for bullet in bullets:
                print(
                    f"WARN: {wfile}: acceptance criterion the loop cannot "
                    f"observe: {bullet!r} — see .specfuse/rules/close-discipline.md "
                    f"and rewrite it now, or declare an escape hatch "
                    f"(human_only: true / oracle_env)."
                )
    return errs


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


#: `LEARNINGS_PATH` named as a lessons destination. Anchored on the filename
#: rather than the full path so `LEARNINGS.md` and `.specfuse/LEARNINGS.md`
#: both match, and bounded on the left so `LEARNINGS-archive.md` — a different
#: surface entirely — does not. `LEARNINGS-pending.md` cannot match this
#: pattern either: the segment after `LEARNINGS` is `-pending`, not `.md`.
_LEARNINGS_DESTINATION_RE = re.compile(r"(?<![\w-])LEARNINGS\.md")


def check_convergent_wu_wiring(
    feature_dir: Path, plan_fm: dict, gates: list
) -> list:
    """ERROR when a unit declares `iterate_on_failure` it cannot act on (#2652).

    `iterate_on_failure` (#2650) keeps a failed attempt's working tree when
    the validator's findings improved. That only helps if the next attempt
    can *see* what the validator currently reports, which is what an
    `oracles` set delivers pre-dispatch — the set runs on every attempt and
    its output is injected into the session prompt. Declared without one, a
    unit iterates **blind**: it keeps its tree and learns nothing new about
    it, which is strictly worse than the discard it opted out of, because it
    also compounds.

    Also refuses `max_attempts: 1` alongside it: one attempt has no second
    pass to continue into, so the flag is a no-op its author plainly did not
    intend.

    **ERROR, not WARN**, on `check_closing_guard_literals`' own rule — the
    signal is structural (frontmatter fields, not a prose match), and an
    ERROR must be satisfiable on a populated tree
    (`[FEAT-2026-0015/G2-CLOSE]`). Measured 2026-08-22: zero existing work
    units in this repository declare `iterate_on_failure`, so the live tree
    is clean by construction. `done` units are skipped as sealed history, the
    same exemption every sibling check applies.

    This is #2652's answer made concrete: the loop **hosts** convergent
    authoring rather than forbidding it, and refuses only the configuration
    that cannot work. Forbidding the work outright would not stop it
    happening — it would only lose the loop's record of how it was done.
    """
    errs: list = []
    for gate in gates:
        for entry in gate.get("work_units") or []:
            wfile = feature_dir / str(entry.get("file", ""))
            if not wfile.is_file():
                continue
            try:
                wfm, _ = read_frontmatter(wfile)
            except Exception:  # noqa: BLE001 - malformed WU is another check's finding
                continue
            if not wfm.get("iterate_on_failure"):
                continue
            if wfm.get("status") == "done":
                continue  # sealed; arming rules do not apply retroactively
            if not wfm.get("oracles"):
                errs.append(
                    f"ERROR: {wfile}: declares `iterate_on_failure` but no "
                    f"`oracles` set. A retained tree is only useful if the "
                    f"next attempt can see what the validator now reports; "
                    f"without an oracles set the unit iterates blind and "
                    f"compounds. Name the validator's verification.yml set "
                    f"in `oracles`, or drop `iterate_on_failure`."
                )
            if wfm.get("max_attempts") == 1:
                errs.append(
                    f"ERROR: {wfile}: declares `iterate_on_failure` with "
                    f"`max_attempts: 1`. One attempt has no second pass to "
                    f"continue into, so the flag does nothing. Raise the "
                    f"ceiling, or drop `iterate_on_failure`."
                )
    return errs


def check_closing_learnings_destination(
    feature_dir: Path, plan_fm: dict, gates: list
) -> None:
    """WARN when an `auto` feature's closing WU names the one lessons
    destination `close-i` forbids (#2173).

    Under `autonomy_default: auto`, `assert_learnings_staged_under_auto`
    forbids a closing WU from appending to `LEARNINGS_PATH`; lessons stage to
    `LEARNINGS_PENDING_FILENAME` instead. A WU whose body names only the
    forbidden path is *describing* a write the guard will refuse, so a session
    following its own acceptance criteria literally is left with a forbidden
    door and a false one -- the shape #2173 was filed on.

    **This is not what caused that issue's headline $40.27.** The author
    retracted that diagnosis with reflog evidence: every refused attempt had in
    fact staged correctly, and the spin was the stale-build hazard (#1040,
    fixed dispatcher-side in #2186). What survives the retraction is the
    narrower defect checked here -- a work unit that describes a forbidden
    destination is wrong whether or not a session has yet been misled by it.

    WARN, never ERROR, for the reason `check_closing_guard_literals` gives:
    measured on this repo, 9 of 14 historical `auto` closing WUs would fail it.
    All 14 are `done` and skipped as sealed history, so the live tree is clean
    -- but a prose match on a body is not a strong enough signal to fail a
    build over, and a body may name the path descriptively without instructing
    a write.
    """
    if not learnings_staging_is_required(plan_fm.get("autonomy_default")):
        return
    for gate in gates:
        for entry in gate.get("work_units") or []:
            wfile = feature_dir / str(entry.get("file", ""))
            if not wfile.is_file():
                continue
            try:
                wfm, wbody = read_frontmatter(wfile)
            except Exception:  # noqa: BLE001 - malformed WU is another check's finding
                continue
            if wfm.get("type") not in ("close", "close-intermediate"):
                continue
            if wfm.get("status") == "done":
                continue  # sealed; backfilling instructions on history is pointless
            if LEARNINGS_PENDING_FILENAME in wbody:
                continue  # names the routing, not just the forbidden half
            if not _LEARNINGS_DESTINATION_RE.search(wbody):
                continue
            print(
                f"WARN: {wfile}: body names {LEARNINGS_PATH} as a lessons "
                f"destination, but this feature is autonomy_default=auto, where "
                f"assert_learnings_staged_under_auto forbids that write — "
                f"lessons stage to {LEARNINGS_PENDING_FILENAME}. A session "
                f"following this criterion literally is refused after dispatch. "
                f"See close-discipline.md §4."
            )


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


# Ceremony-proportionality threshold (docs/methodology.md §6): one fact, one
# home. Referenced, not redefined, in the draft-feature skill.
GATE_PROPORTIONALITY_THRESHOLD = 8
GATE_PROPORTIONALITY_SUBSTANTIVE_TYPES = frozenset(
    {"implementation", "qa_authoring", "qa_execution", "qa_curation"}
)


def lint_gate_proportionality(feature_dir: Path, gates: list) -> None:
    """WARN when a small feature is split across more than one gate.

    A feature whose planned substantive WU count (types implementation,
    qa_authoring, qa_execution, qa_curation) is at most
    GATE_PROPORTIONALITY_THRESHOLD should draft as a single gate
    (docs/methodology.md §6 "Ceremony proportionality"). WARN-only; never
    appends to the errors list — an existing feature drafted before this rule
    should not suddenly fail lint.
    """
    substantive_count = 0
    gates_with_units = 0
    for gate in gates:
        units = gate.get("work_units") or []
        if not units:
            continue
        gates_with_units += 1
        for entry in units:
            wfile = entry.get("file")
            if not wfile:
                continue
            wpath = feature_dir / wfile
            if not wpath.exists():
                continue
            wfm, _ = read_frontmatter(wpath)
            if wfm.get("type") in GATE_PROPORTIONALITY_SUBSTANTIVE_TYPES:
                substantive_count += 1

    if (
        gates_with_units > 1
        and substantive_count <= GATE_PROPORTIONALITY_THRESHOLD
    ):
        print(
            f"WARN: {feature_dir}: planned substantive WU count "
            f"({substantive_count}) is at most the ceremony-proportionality "
            f"threshold ({GATE_PROPORTIONALITY_THRESHOLD}) but the plan "
            f"spans {gates_with_units} gates. See docs/methodology.md §6 "
            f"\"Ceremony proportionality\" — a feature this small should "
            f"draft as a single gate with a single terminal `close` WU."
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
    of them before `spinning_detected` fired, while `specfuse lint` reported
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


#: A decision citation, by this repo's own convention (`D1`, `D2`, ...) —
#: see `specfuse/loop/decisions_format.py` and FEAT-2026-0058/WU-01. The
#: format module itself allows any non-space heading token as an ID; this
#: pattern is the narrower shape every real registry in this tree uses, and
#: is what lets a *dangling* citation (an ID that looks cited but is not
#: registered) be told apart from ordinary prose.
_DECISION_CITATION_RE = re.compile(r"\bD\d+\b")

_WORD_RE = re.compile(r"[a-z0-9]+")

#: Below this many words a statement's own phrasing is too generic to
#: fingerprint reliably — flagging it would just be matching common English.
_RESTATEMENT_MIN_WORDS = 8
#: Sequence-similarity floor for "same clause, one word changed" (the
#: FEAT-2026-0066 dropped-row shape) without also catching a merely related
#: sentence that happens to share vocabulary.
_RESTATEMENT_RATIO = 0.82


def _normalize_words(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _restates(statement: str, body_words: list[str]) -> "tuple[int, int] | None":
    """The `(start, end)` word span restating *statement*, or None.

    Fuzzy on purpose: exact-substring matching would miss a restatement with
    "one clause altered" (FEAT-2026-0066's dropped-row shape). Slides windows
    of roughly the statement's own length across the body and scores each
    with `difflib.SequenceMatcher` over word tokens; any window at or above
    `_RESTATEMENT_RATIO` is a restatement.

    Returns the span rather than a bool so the caller can ask whether the
    decision's ID is cited *near this passage* (FEAT-2026-0058 hedged
    follow-up 1). A whole-file exemption made the check inert: any occurrence
    of the bare token `D3` anywhere in a document exempted every restatement
    of D3 elsewhere in it.
    """
    import difflib

    stmt_words = _normalize_words(statement)
    if len(stmt_words) < _RESTATEMENT_MIN_WORDS or len(body_words) < len(stmt_words):
        return None
    window = len(stmt_words)
    lo = max(_RESTATEMENT_MIN_WORDS, int(window * 0.7))
    hi = min(len(body_words), int(window * 1.3) + 1)
    step = max(1, window // 4)
    for start in range(0, len(body_words) - lo + 1, step):
        for size in range(lo, hi + 1, max(1, (hi - lo) // 2 or 1)):
            end = start + size
            if end > len(body_words):
                break
            chunk = body_words[start:end]
            ratio = difflib.SequenceMatcher(a=stmt_words, b=chunk, autojunk=False).ratio()
            if ratio >= _RESTATEMENT_RATIO:
                return (start, end)
    return None


#: How many words either side of a restating passage still count as "cited
#: alongside it". Wide enough for a lead-in (`Per D2: <statement>`), a trailing
#: parenthetical (`<statement> (D2)`), or a citation in the same sentence;
#: far too narrow for a mention in an unrelated section of the same file.
_CITATION_PROXIMITY_WORDS = 25


def _cited_near(
    decision_id: str, body_words: list[str], span: "tuple[int, int]"
) -> bool:
    """True when *decision_id* is cited within the proximity window of *span*.

    This is what "quoting a decision while citing it" actually looks like:
    the ID sits next to the quotation, not a thousand words away in a
    different section (FEAT-2026-0058 hedged follow-up 1).
    """
    start, end = span
    lo = max(0, start - _CITATION_PROXIMITY_WORDS)
    hi = min(len(body_words), end + _CITATION_PROXIMITY_WORDS)
    target = decision_id.lower()
    return any(word == target for word in body_words[lo:hi])


def check_decision_citations(feature_dir: Path, plan_fm: dict, gates: list) -> list[str]:
    """ERROR when an artifact cites a decision ID absent from `DECISIONS.md`,
    or reproduces a decision's statement text instead of citing its ID
    (FEAT-2026-0058/T02).

    Opt-in per feature (rule 5): a feature with no `DECISIONS.md` is not
    scanned at all — 60 of 66 folders have none, and the registry is a
    convention a feature adopts, not one imposed on every folder. `done` and
    `abandoned` features are exempt as sealed history, the same exemption
    `check_closing_guard_literals` already applies.

    Non-restatement's exemption is scoped to the quotation, not to the file
    (FEAT-2026-0058 hedged follow-up 1): a near-verbatim quotation is
    legitimate when the decision's ID is cited within
    `_CITATION_PROXIMITY_WORDS` of the restating passage, which is what
    quoting-while-citing looks like. The exemption was previously per whole
    artifact, which made the check inert — `_DECISION_CITATION_RE` is
    `\\bD\\d+\\b`, so the bare token `D3` occurring anywhere in a document
    exempted every restatement of D3 elsewhere in it. Measured on this
    feature's own artifacts it was live on 3 of 24 (artifact, decision)
    pairs.

    A feature's own `PLAN.md` is **not** specially exempt. Where a decision is
    originally taken, `DECISIONS.md` holds the statement and `PLAN.md` cites
    it — that is `PLAN.md` D1's rule ("if artifacts may only cite, there is
    no second copy to drift"), and exempting the one file most likely to hold
    a second copy would have hollowed it out.
    """
    if plan_fm.get("status") in ("done", "abandoned"):
        return []

    decisions_path = feature_dir / "DECISIONS.md"
    if not decisions_path.is_file():
        return []  # opt-in; no registry, nothing to hold this feature to

    from . import decisions_format

    parsed = decisions_format.parse_decisions(decisions_path.read_text())
    # Refused entries keep their IDs known to the citation check
    # (FEAT-2026-0058 hedged follow-up 3). A parse failure excludes an entry
    # from `.entries`, and reference integrity used to read that as "the ID
    # does not exist" — so one unsigned override reported as seven ERRORs,
    # six of them telling the operator to add a decision that is already in
    # the registry. `DecisionParseError` carries `decision_id`, so a
    # present-but-unparseable ID is recoverable. The override finding names
    # the real fault on its own; a dangling-citation error alongside it only
    # obscures which finding to act on.
    valid_ids = {e.decision_id for e in parsed.entries} | {
        e.decision_id for e in parsed.errors
    }
    statements = {
        e.decision_id: e.statement for e in parsed.entries if e.statement
    }

    artifact_paths: list[Path] = []
    plan_path = feature_dir / "PLAN.md"
    if plan_path.is_file():
        artifact_paths.append(plan_path)
    for gate in gates:
        gfile = gate.get("file")
        if gfile and (feature_dir / gfile).is_file():
            artifact_paths.append(feature_dir / gfile)
        for entry in gate.get("work_units") or []:
            wfile = entry.get("file")
            if wfile and (feature_dir / wfile).is_file():
                artifact_paths.append(feature_dir / wfile)

    errs: list[str] = []
    for path in artifact_paths:
        try:
            _, body = read_frontmatter(path)
        except Exception:  # noqa: BLE001 - malformed file is another check's finding
            continue

        cited_ids = set(_DECISION_CITATION_RE.findall(body))

        for cid in sorted(cited_ids):
            if cid not in valid_ids:
                errs.append(
                    f"ERROR: {path}: cites decision {cid!r}, which is not in "
                    f"{decisions_path.name}. Add the decision to the "
                    f"registry, or fix the citation if it names the wrong ID."
                )

        body_words = _normalize_words(body)
        for did, statement in statements.items():
            span = _restates(statement, body_words)
            if span is None:
                continue
            if _cited_near(did, body_words, span):
                continue  # quoted with its ID alongside — legitimate quotation
            errs.append(
                f"ERROR: {path}: reproduces decision {did}'s statement "
                f"text instead of citing `{did}`. {decisions_path.name} "
                f"is the one place the statement lives — cite the ID "
                f"rather than restating it."
            )

    return errs


#: Values `signed_off_by` is rejected for even though they are non-empty —
#: a placeholder standing in for a name rather than one (FEAT-2026-0058/T03,
#: criterion 3). Checks only that *someone* is named, never what they wrote.
_PLACEHOLDER_SIGNOFF_RE = re.compile(
    r"^(tbd|todo|n/?a|unknown|someone|xxx+|\?+|fixme|pending|tba)$",
    re.IGNORECASE,
)


def check_decision_override_signoff(feature_dir: Path, plan_fm: dict) -> list[str]:
    """ERROR when an override reaches `ratified` (or sits at
    `overridden-pending-signoff`) without a named human on record
    (FEAT-2026-0058/T03).

    `decisions_format.parse_decisions` already refuses to parse an entry
    whose override provenance is incomplete — it lands in `ParseResult.errors`
    instead of `.entries`. Left there, an unsigned override is silently
    invisible to lint rather than blocking arming. This check surfaces those
    refusals as ERROR findings (criteria 1 and 2). It also catches what the
    parser cannot: every override field present but `signed_off_by` holding a
    placeholder rather than a name (criterion 3) — checking only that
    *someone* is named, never what they wrote, per
    `.specfuse/rules/operator-escalation.md`'s rule against authoring the
    human's justification for them.

    Sealed features (done/abandoned) are exempt, matching
    `check_decision_citations`. A feature with no `DECISIONS.md`, or a
    decision that was never overridden, produces no findings (criterion 4).
    """
    if plan_fm.get("status") in ("done", "abandoned"):
        return []

    decisions_path = feature_dir / "DECISIONS.md"
    if not decisions_path.is_file():
        return []  # opt-in; no registry, nothing to hold this feature to

    from . import decisions_format

    parsed = decisions_format.parse_decisions(decisions_path.read_text())

    errs: list[str] = []
    for err in parsed.errors:
        if "override provenance incomplete" in err.reason:
            errs.append(
                f"ERROR: {decisions_path}: {err.decision_id} is "
                f"{err.reason} — an override cannot arm unsigned. Name who "
                f"signed off and when."
            )

    for entry in parsed.entries:
        if not (
            entry.status == "overridden-pending-signoff" or entry.was_overridden()
        ):
            continue
        signed_off_by = (entry.signed_off_by or "").strip()
        if _PLACEHOLDER_SIGNOFF_RE.match(signed_off_by):
            errs.append(
                f"ERROR: {decisions_path}: {entry.decision_id}'s "
                f"signed_off_by field is a placeholder ({signed_off_by!r}), "
                f"not a named human. Name who signed off on the override."
            )

    return errs


def check_done_feature_gates(feature_dir: Path, plan_fm: dict) -> list[str]:
    """A `status: done` feature must have every gate `status: passed` (#287).

    Catches the drift class where a feature's terminal-flip machinery never
    ran (legacy closing sequence, pre-verdict-contract close WU) and left a
    gate at `open`/`awaiting_review` while PLAN.md already reads `done`.
    Excluded features (DONE_FEATURE_GATE_EXCLUSIONS) are ones where that gap
    is correct, not drift — see the reasons recorded there.

    GATE-NN-REVIEW.md artifacts carry no `status` frontmatter and are not
    gate files, so they're skipped by name. GATE-NN-CRITERIA.md (FEAT-2026-0056)
    is skipped for the same reason and matched through `CRITERIA_FILENAME_RE`
    rather than a fresh literal — that pattern is the artifact basename's one
    home, and this is its fifth reader.
    """
    if plan_fm.get("status") != "done":
        return []
    if feature_dir.name in DONE_FEATURE_GATE_EXCLUSIONS:
        return []
    errs: list[str] = []
    for gate_path in sorted(feature_dir.glob("GATE-*.md")):
        if gate_path.stem.endswith("-REVIEW"):
            continue
        if CRITERIA_FILENAME_RE.fullmatch(gate_path.name):
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
                            f"{', '.join(sorted(VERDICT_VALUES))})."
                        )
            else:
                if wu_verdict is not None:
                    errs.append(
                        f"ERROR: {wfile}: 'verdict' frontmatter is only meaningful for "
                        f"closing types (close, close-intermediate); remove it from "
                        f"this {wu_type_val!r} WU."
                    )

            # Load-bearing close WARN (#293). A close carrying a §1-§3
            # obligation, or one that is the sole writer of a surface outside
            # its own folder, must set `auto_close_disabled: true` or
            # `evaluate_auto_close` can skip it at attempts: 0 — silently, with
            # every acceptance criterion in its body left unfulfilled.
            #
            # The selection effect is why this warns rather than informs: a gate
            # only auto-closes when it is on-plan and under budget, so these
            # criteria are dropped precisely on the features that behaved well
            # and therefore attract the least scrutiny.
            # Scoped to a close that can still be dispatched. On a `done` or
            # `abandoned` WU the flag is unactionable — the close already ran or
            # already didn't, and setting it now changes nothing. Measured: all
            # 22 features this fired on before the filter were `done`, so the
            # unfiltered rule was pure noise on exactly the runs that lint for
            # other reasons (feature-conversion, upgrade health reports).
            if (wu_type_val in {"close", "close-intermediate"}
                    and wu_status not in {"done", "abandoned"}):
                ac_text = _slice_ac_section(wbody)
                flag = wfm.get("auto_close_disabled")
                flag_set = flag in (True, "true", "True")
                if not flag_set and detect_load_bearing_close(
                        ac_text, feature_dir.name):
                    print(
                        f"WARN: {wfile}: close WU's acceptance criteria are "
                        f"load-bearing (a close-discipline §1-§3 obligation, or "
                        f"a write to a surface outside this feature's folder) "
                        f"but frontmatter lacks 'auto_close_disabled: true' — "
                        f"evaluate_auto_close may skip this WU at attempts: 0 "
                        f"and every criterion in its body would go unfulfilled. "
                        f"See .specfuse/rules/close-discipline.md and #293."
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
    check_closing_learnings_destination(feature_dir, fm, gates)
    # Returns rather than prints: an ERROR that does not reach `errs`
    # never fails the lint, which is the defect shape LEARNINGS records
    # as detecting-a-condition-is-not-handling-it.
    errs.extend(check_convergent_wu_wiring(feature_dir, fm, gates))
    check_produces_satisfiability(feature_dir, gates)
    lint_gate_proportionality(feature_dir, gates)
    errs.extend(check_produces_shape(feature_dir, gates))
    errs.extend(check_produces_boundary(feature_dir, gates))
    errs.extend(check_done_feature_gates(feature_dir, fm))
    errs.extend(check_decision_citations(feature_dir, fm, gates))
    errs.extend(check_decision_override_signoff(feature_dir, fm))
    errs.extend(lint_ac_observable(feature_dir))

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

    from specfuse.loop.build_provenance import warn_if_out_of_tree
    warn_if_out_of_tree()
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
