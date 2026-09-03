#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`specfuse lint --closing` — the closing contract, checkable in-session.

Reads `specfuse.loop.closing_requirements.CLOSING_REQUIREMENTS` (T01) and
evaluates a feature's currently-in-progress closing WU (`close`,
`close-intermediate`, or `plan-next`) against it, PRE-squash — over the
working tree, not a squash diff — so a session can fix a gap for cents
instead of paying for a post-squash guard refusal and a full re-dispatch.

Read-only: this module never writes to the feature dir, the repo, or git.
Invents no requirement of its own — every literal (heading text, filename
template, verdict set) is read from `closing_requirements.py`, the same
registry the post-squash guards in `loop.py` import from.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import closing_requirements as creq
from . import criteria_state
from .changelog import parse_changelog
from .loop import _gate_number_from_wu_id, summarize_attempt_failure_classes
from .lint_plan import _find_task_graph_block, read_frontmatter

_CLOSING_TYPES = frozenset({"close", "close-intermediate", "plan-next"})
_TERMINAL_WU_STATUSES = frozenset({"done", "abandoned"})


@dataclass
class ClosingContext:
    feature_dir: Path
    repo_root: Path
    plan_fm: dict
    gates: list  # raw graph dicts: {"gate": int, "file": str, "work_units": [...]}
    wu_id: str
    wu_type: str
    gate_num: int | None
    wfm: dict
    wbody: str
    _diff_paths: list[str] | None = field(default=None, repr=False)
    _failures_present: bool | None = field(default=None, repr=False)

    def changed_paths(self) -> list[str]:
        if self._diff_paths is None:
            self._diff_paths = _working_tree_changed_paths(self.repo_root)
        return self._diff_paths

    def failures_present(self) -> bool:
        if self._failures_present is None:
            summary = summarize_attempt_failure_classes(
                self.feature_dir, self.gate_num, exclude_correlation_id=self.wu_id,
            )
            self._failures_present = summary != creq.NO_FAILURES_SENTINEL
        return self._failures_present


def _run_git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True, text=True, check=False,
    )
    return proc.stdout


def _working_tree_changed_paths(repo_root: Path) -> list[str]:
    """Repo-root-relative paths touched in the working tree (staged, unstaged,
    or untracked) — the pre-squash analogue of a closing guard's squash diff.
    """
    out = _run_git(repo_root, "status", "--porcelain")
    paths: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        rest = line[3:] if len(line) > 3 else line.lstrip()
        if " -> " in rest:  # rename
            rest = rest.split(" -> ", 1)[1]
        paths.append(rest.strip())
    return paths


def _git_diff_added_lines(repo_root: Path, rel_path: str) -> bool:
    """True if *rel_path* is untracked-with-content or has an added line in
    the working tree relative to HEAD — the pre-squash analogue of
    `assert_learnings_appended_or_noop`'s squash-diff check.
    """
    status = _run_git(repo_root, "status", "--porcelain", "--", rel_path)
    if status.startswith("??"):
        p = repo_root / rel_path
        return p.exists() and bool(p.read_text().strip())
    diff = _run_git(repo_root, "diff", "HEAD", "--", rel_path)
    return any(
        ln.startswith("+") and not ln.startswith("+++") for ln in diff.splitlines()
    )


# --------------------------------------------------------------------------- #
# Per-requirement checkers — one per `enforced_by` guard name.                #
# Each returns None (not applicable / can't fail here) or (ok, reason).       #
# --------------------------------------------------------------------------- #


def _check_retrospective_exists(req: creq.Requirement, ctx: ClosingContext):
    retro = ctx.feature_dir / creq.RETROSPECTIVE_FILENAME
    if not retro.exists() or not retro.read_text().strip():
        return False, f"{creq.RETROSPECTIVE_FILENAME} absent or empty in feature dir"
    return True, ""


def _check_learnings_appended_or_noop(req: creq.Requirement, ctx: ClosingContext):
    if _git_diff_added_lines(ctx.repo_root, creq.LEARNINGS_PATH):
        return True, ""
    # Under `autonomy_default: auto` the append above is what close-i
    # forbids, so the feature-local staging file carries the same evidence.
    # The mirror has to agree with the driver guard here or lint keeps
    # telling an auto session to write the no-op phrase it just earned the
    # right not to write (#1419).
    staged_rel: str | None = None
    if creq.learnings_staging_is_required(ctx.plan_fm.get("autonomy_default")):
        staged_rel = os.path.relpath(
            ctx.feature_dir / creq.LEARNINGS_PENDING_FILENAME, ctx.repo_root,
        )
        if _git_diff_added_lines(ctx.repo_root, staged_rel):
            return True, ""
    retro = ctx.feature_dir / creq.RETROSPECTIVE_FILENAME
    if retro.exists() and creq.NOTHING_GENERALIZES_PHRASE in retro.read_text().lower():
        return True, ""
    accepted = (
        creq.LEARNINGS_PATH if staged_rel is None
        else f"{creq.LEARNINGS_PATH} or {staged_rel}"
    )
    return False, (
        f"no {accepted} additions in the working tree and no "
        f"'{creq.NOTHING_GENERALIZES_PHRASE}' note in {creq.RETROSPECTIVE_FILENAME}"
    )


def _check_doc_or_roadmap_diff(req: creq.Requirement, ctx: ClosingContext):
    for path in ctx.changed_paths():
        if path == creq.ROADMAP_PATH or path.startswith(creq.DOCS_PREFIX):
            return True, ""
        if path == creq.LEARNINGS_PATH:
            return True, ""
        if path.endswith("/" + creq.RETROSPECTIVE_FILENAME) or path == creq.RETROSPECTIVE_FILENAME:
            return True, ""
    if ctx.wu_type == "close-intermediate":
        if creq.DOCS_PREFIX not in ctx.wbody and "roadmap.md" not in ctx.wbody:
            return True, ""
    return False, (
        f"no {creq.DOCS_PREFIX}, {creq.ROADMAP_PATH}, {creq.LEARNINGS_PATH}, or "
        f"{creq.RETROSPECTIVE_FILENAME} file in the working tree"
    )


def _check_verdict_well_formed(req: creq.Requirement, ctx: ClosingContext):
    verdict = ctx.wfm.get("verdict")
    if verdict is None:
        return False, "verdict frontmatter field is absent"
    legal = req.allowed_values or creq.VERDICT_VALUES
    if verdict in creq.LEGACY_VERDICT_VALUES:
        return False, (
            f"verdict {verdict!r} was retired by FEAT-2026-0085; a close "
            f"records one of {sorted(legal)}. See {creq.VERDICT_MIGRATION_NOTE}"
        )
    if verdict not in legal:
        return False, f"verdict {verdict!r} is not one of {sorted(legal)}"
    return True, ""


def _check_cost_analysis_section_when_met(req: creq.Requirement, ctx: ClosingContext):
    retro = ctx.feature_dir / creq.RETROSPECTIVE_FILENAME
    if retro.exists() and creq.COST_ANALYSIS_HEADING_RE.search(retro.read_text()):
        return True, ""
    return False, (
        f"verdict=met but '## {creq.COST_ANALYSIS_HEADING}' section absent from "
        f"{creq.RETROSPECTIVE_FILENAME}"
    )


def _check_failure_class_breakdown_when_failures_present(
    req: creq.Requirement, ctx: ClosingContext,
):
    retro = ctx.feature_dir / creq.RETROSPECTIVE_FILENAME
    if not retro.exists():
        return True, ""  # assert_retrospective_exists / gate-section check fires first
    if creq.FAILURE_CLASS_HEADING_RE.search(retro.read_text()):
        return True, ""
    gate_label = f"gate {ctx.gate_num}" if ctx.gate_num is not None else "all gates"
    return False, (
        f"non-passing attempt(s) exist for {gate_label} but "
        f"{creq.RETROSPECTIVE_FILENAME} has no "
        f"'{creq.FAILURE_CLASS_HEADING_MARKDOWN}' section"
    )


def _check_retrospective_gate_section(req: creq.Requirement, ctx: ClosingContext):
    if ctx.gate_num is None:
        return False, "cannot parse gate number from wu_id"
    retro = ctx.feature_dir / creq.RETROSPECTIVE_FILENAME
    if not retro.exists():
        return False, f"{creq.RETROSPECTIVE_FILENAME} absent in feature dir"
    if creq.gate_section_heading_re(ctx.gate_num).search(retro.read_text()):
        return True, ""
    return False, (
        f"{creq.RETROSPECTIVE_FILENAME} has no 'Gate {ctx.gate_num}' section"
    )


def _check_gate_review_exists(req: creq.Requirement, ctx: ClosingContext):
    if ctx.gate_num is None:
        return False, "cannot parse gate number from wu_id"
    next_gate = ctx.gate_num + 1
    if not any(g.get("gate") == next_gate for g in ctx.gates):
        return True, ""  # terminal: no next gate to review
    review_name = creq.gate_review_filename(next_gate)
    review = ctx.feature_dir / review_name
    if not review.exists() or not review.read_text().strip():
        return False, f"{review_name} absent or empty"
    return True, ""


def _check_next_gate_drafted_or_terminal(req: creq.Requirement, ctx: ClosingContext):
    if ctx.plan_fm.get("status") == "done":
        return True, ""
    feature_id = ctx.wu_id.rsplit("/", 1)[0]
    roadmap_path = ctx.repo_root / creq.ROADMAP_PATH
    if roadmap_path.exists():
        row_re = re.compile(
            r"^\|\s*" + re.escape(feature_id) + r"\s*\|([^|]*)\|([^|]*)\|",
            re.MULTILINE,
        )
        rm = row_re.search(roadmap_path.read_text())
        if rm and rm.group(2).strip() == "done":
            return True, ""
    if ctx.gate_num is None:
        return False, "cannot parse gate number from wu_id"
    next_gates = [g for g in ctx.gates if g.get("gate") == ctx.gate_num + 1]
    if not next_gates:
        return True, ""
    if next_gates[0].get("work_units"):
        return True, ""
    return False, (
        f"gate {ctx.gate_num + 1} has no drafted work_units in PLAN.md and "
        f"neither PLAN.md nor roadmap marks done"
    )


def _check_changelog_entry_for_contract_changes(req: creq.Requirement, ctx: ClosingContext):
    """Pre-squash analogue of `assert_changelog_entry_for_contract_changes`.

    Scoped to `ctx.feature_dir`'s own RETROSPECTIVE.md and this close's own
    FEAT-ID only — never reads another feature's folder, and only ever
    evaluates the closing WU currently in progress, so an already-`done`
    feature (all fifty-one predate this check) is never re-flagged.
    """
    retro = ctx.feature_dir / creq.RETROSPECTIVE_FILENAME
    if not retro.exists():
        return True, ""  # assert_retrospective_exists already covers this
    section = creq.find_consumer_visible_section(retro.read_text())
    if section is None:
        return True, ""
    if creq.consumer_visible_section_is_na(section):
        return True, ""
    changelog = ctx.repo_root / creq.CHANGELOG_PATH
    if not changelog.exists():
        return False, (
            f"'{creq.CONSUMER_VISIBLE_HEADING}' names a real change but "
            f"{creq.CHANGELOG_PATH} does not exist"
        )
    result = parse_changelog(changelog.read_text())
    unreleased = result.unreleased()
    feature_id = ctx.wu_id.rsplit("/", 1)[0]
    entries = unreleased.entries if unreleased else []
    if creq.changelog_has_entry_for(entries, feature_id):
        return True, ""
    return False, (
        f"'{creq.CONSUMER_VISIBLE_HEADING}' names a real change but "
        f"{creq.CHANGELOG_PATH}'s Unreleased section has no entry tracing to "
        f"{feature_id}"
    )


def _check_followups_recorded(req: creq.Requirement, ctx: ClosingContext):
    if ctx.wfm.get("verdict") != "not_met":
        return None
    path = ctx.feature_dir / creq.FOLLOW_UPS_FILENAME
    if not path.exists():
        return False, f"verdict=not_met but {creq.FOLLOW_UPS_FILENAME} absent from feature dir"
    if not creq.parse_followup_entries(path.read_text()):
        return False, f"verdict=not_met but {creq.FOLLOW_UPS_FILENAME} has no '### ' entry"
    return True, ""


def check_criteria_state_well_formed(req: creq.Requirement, ctx: ClosingContext) -> list[str]:
    """One finding per untrustworthy entry in `GATE-NN-CRITERIA.md`, or none.

    Three shapes make an entry untrustworthy: a `kind:` missing or outside
    `criteria_state.ORACLE_KINDS`; a `state:` missing or outside
    `criteria_state.CRITERION_STATES`; or an entry whose oracle has no
    knowable scope (`kind: broad`) reading `state: pass` with an `attempt:`
    that is not the current attempt — a broad oracle's green can never be
    carried forward from a prior attempt (PLAN.md § *Scope decision*). Each
    is its own finding so one bad entry never masks another, and an entry
    contributes at most one finding — the first problem found. Returns an
    empty list when the artifact does not exist yet; a close that has not
    started recording state is not this requirement's concern.

    A **pristine** entry — `state: unverified`, no `kind:`, no `oracle:`,
    byte for byte what `_precreate_criteria_state_stub` seeds and nothing
    else — is likewise not this requirement's concern: no close has
    annotated it yet, so there is nothing to have gotten wrong. Any
    deviation (a `state` other than `unverified`, or an `oracle` recorded)
    means a close has begun touching the entry, and it re-enters scope.
    """
    if ctx.gate_num is None:
        return []
    path = ctx.feature_dir / criteria_state.criteria_filename(ctx.gate_num)
    if not path.is_file():
        return []
    entries = criteria_state.parse_criteria_state(path.read_text())
    current_attempt = str(ctx.wfm.get("attempts"))
    findings: list[str] = []
    for entry in entries:
        if entry.kind is None and entry.oracle is None and entry.state == "unverified":
            continue
        if entry.kind is None:
            findings.append(f"{entry.criterion_id}: missing kind:")
            continue
        if entry.kind not in criteria_state.ORACLE_KINDS:
            findings.append(
                f"{entry.criterion_id}: kind {entry.kind!r} not one of "
                f"{sorted(criteria_state.ORACLE_KINDS)}"
            )
            continue
        if entry.state not in criteria_state.CRITERION_STATES:
            findings.append(
                f"{entry.criterion_id}: state {entry.state!r} not one of "
                f"{sorted(criteria_state.CRITERION_STATES)}"
            )
            continue
        if entry.kind == "broad" and entry.state == "pass" and entry.attempt != current_attempt:
            findings.append(
                f"{entry.criterion_id}: broad entry reads state: pass but "
                f"attempt {entry.attempt!r} != current attempt {current_attempt!r}"
            )
    return findings


_CHECKS = {
    "assert_retrospective_exists": _check_retrospective_exists,
    "assert_learnings_appended_or_noop": _check_learnings_appended_or_noop,
    "assert_doc_or_roadmap_diff": _check_doc_or_roadmap_diff,
    "assert_verdict_well_formed": _check_verdict_well_formed,
    "assert_cost_analysis_section_when_met": _check_cost_analysis_section_when_met,
    "assert_failure_class_breakdown_when_failures_present":
        _check_failure_class_breakdown_when_failures_present,
    "assert_retrospective_gate_section": _check_retrospective_gate_section,
    "assert_gate_review_exists": _check_gate_review_exists,
    "assert_next_gate_drafted_or_terminal": _check_next_gate_drafted_or_terminal,
    "assert_changelog_entry_for_contract_changes": _check_changelog_entry_for_contract_changes,
    "check_criteria_state_well_formed": check_criteria_state_well_formed,
    "assert_followups_recorded": _check_followups_recorded,
}


def _find_in_progress_closing_wu(feature_dir: Path, gates: list) -> dict | None:
    """First not-yet-terminal closing-type WU across gates, in graph order."""
    for g in gates:
        for ref in g.get("work_units") or []:
            wfile = ref.get("file")
            if not wfile:
                continue
            wpath = feature_dir / wfile
            if not wpath.is_file():
                continue
            wfm, wbody = read_frontmatter(wpath)
            wu_type = wfm.get("type")
            if wu_type not in _CLOSING_TYPES:
                continue
            if wfm.get("status") in _TERMINAL_WU_STATUSES:
                continue
            return {
                "gate": g, "ref": ref, "path": wpath,
                "fm": wfm, "body": wbody, "type": wu_type,
            }
    return None


def _format_finding(req: creq.Requirement, reason: str) -> str:
    return (
        f"{req.id}: {reason} — would fail {req.enforced_by} after squash"
    )


def lint_closing(feature_dir: Path) -> tuple[list[str], list[str]]:
    """Evaluate the feature's in-progress closing WU against the registry.

    Returns (findings, notes): `findings` are pre-squash-checkable unmet
    requirements (non-empty means exit 1); `notes` are advisory post-pass
    requirements that cannot be checked here and never affect the exit code.
    An empty `findings` list with an empty `notes` list can also mean no
    closing WU is currently in progress — see `main()`'s messaging.
    """
    plan_path = feature_dir / "PLAN.md"
    if not plan_path.is_file():
        return ([f"PLAN.md not found in {feature_dir}"], [])

    plan_fm, plan_body = read_frontmatter(plan_path)
    graph = _find_task_graph_block(plan_body)
    if graph is None:
        return ([f"PLAN.md in {feature_dir} has no ```yaml graph block"], [])
    gates = graph.get("gates", [])

    found = _find_in_progress_closing_wu(feature_dir, gates)
    if found is None:
        return ([], [])

    repo_root = feature_dir.parents[2]
    wu_id = found["ref"].get("id", "")
    gate_num = _gate_number_from_wu_id(wu_id)
    if gate_num is None:
        gate_num = found["gate"].get("gate")

    ctx = ClosingContext(
        feature_dir=feature_dir,
        repo_root=repo_root,
        plan_fm=plan_fm,
        gates=gates,
        wu_id=wu_id,
        wu_type=found["type"],
        gate_num=gate_num,
        wfm=found["fm"],
        wbody=found["body"],
    )

    findings: list[str] = []
    notes: list[str] = []

    for req in creq.requirements_for(ctx.wu_type):
        if req.phase == "post-pass":
            notes.append(
                f"NOTE: {req.id} ({req.enforced_by}) is checked post-pass, "
                f"after the gate-boundary state flips — not verifiable here. "
                f"{req.description}."
            )
            continue

        if req.applies_when == "verdict_met":
            if ctx.wfm.get("verdict") != "met":
                continue
        elif req.applies_when == "verdict_not_met":
            if ctx.wfm.get("verdict") != "not_met":
                continue
        elif req.applies_when == "failures_present":
            if not ctx.failures_present():
                continue
        elif req.applies_when == "criteria_artifact_present":
            if ctx.gate_num is None:
                continue
            artifact_path = ctx.feature_dir / criteria_state.criteria_filename(ctx.gate_num)
            if not artifact_path.is_file():
                continue

        checker = _CHECKS.get(req.enforced_by)
        if checker is None:
            # Registry names a guard this lint mode has no checker for — the
            # escalation trigger the WU spec calls out. Surface it loudly
            # rather than silently passing.
            findings.append(
                f"{req.id}: no lint-closing checker registered for "
                f"{req.enforced_by} — registry/lint drift, escalate"
            )
            continue

        result = checker(req, ctx)
        if result is None:
            continue
        if isinstance(result, list):
            for reason in result:
                findings.append(_format_finding(req, reason))
            continue
        ok, reason = result
        if not ok:
            findings.append(_format_finding(req, reason))

    return (findings, notes)


def main_closing(feature_dir: Path) -> int:
    findings, notes = lint_closing(feature_dir)

    plan_path = feature_dir / "PLAN.md"
    no_wu_in_progress = (
        not findings and not notes and plan_path.is_file()
        and _find_in_progress_closing_wu(
            feature_dir,
            (_find_task_graph_block(read_frontmatter(plan_path)[1]) or {}).get("gates", []),
        ) is None
    )

    if findings:
        print(f"FAIL — {len(findings)} unmet closing requirement(s) in {feature_dir}:")
        for f in findings:
            print(f"  - {f}")
    elif no_wu_in_progress:
        print(f"CLOSING-READY — {feature_dir} (no closing WU currently in progress)")
    else:
        print(f"CLOSING-READY — {feature_dir}")

    if notes:
        print()
        for n in notes:
            print(n)

    return 1 if findings else 0
