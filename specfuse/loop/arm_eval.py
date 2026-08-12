#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Deterministic gate-arm predicate — pure, side-effect-free module.

Given a feature directory and the gate id that just closed, evaluates whether
the drafted successor gate may be armed automatically, and returns a
structured per-class verdict. Mirrors the shape of `gate_eval.py`'s
`evaluate_auto_close`: pure evaluation over files, a structured decision
object, a formatter for the event trail, no side effects. Arming and closing
are deliberately separate decisions with different inputs — this module does
not fold into `gate_eval.py`, does not import from it, and does not import
from `loop.py` (the dependency points the other way: `loop.py` will call
into this module, T04).

The organizing principle: model-authored signals may only veto; only
mechanical facts and human-authored constants may approve. Of the eight
classes below, "missing_provenance", "open_questions_human_only", and
"plan_next_lint" (FEAT-2026-0053/T07) are veto channels — a clean verdict
there withholds nothing, it just declines to block; every other class both
approves (clean) and blocks (fired) on mechanical grounds alone. `would_arm`
is True only when all eight classes are clean, so the veto classes can only
ever pull the decision from True to False, never the reverse.

Honest v1 limit: a draft that weakens an *existing* test's assertions is
undetectable here. The judge-editing class catches `produces:` paths, not
prose or assertion semantics — it is a path-surface check, nothing more.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

from . import _miniyaml
from .closing_requirements import gate_review_filename
from .cost import wu_lifetime_cost_usd
from .plan_baseline import load_baseline, load_plan_graph

PREDICATE_VERSION = "v1"

BUDGET_PROJECTION_MULTIPLIER = 2.0
DRIFT_CAP_RATIO = 0.5
ADDED_GATE_CAP = 1

# Path-prefix surfaces a drafted WU must not touch (class 2). `pyproject.toml`
# is matched whole-file — this predicate cannot distinguish the coverage/lint
# config sections from the rest of the file without a diff, so any produced
# `pyproject.toml` fires both this class and decision_class_paths below. That
# double-fire is an accepted v1 approximation, not a bug.
#
# These five are surfaces in ANY repository. The `specfuse/loop/` entries below
# exist only in this one — a project vendoring the driver has no such path — so
# they govern the self-hosting case exclusively.
_UNIVERSAL_JUDGE_PATHS = (
    ".specfuse/verification.yml",
    ".specfuse/hooks/",
    ".specfuse/rules/",
    ".github/workflows/",
    "pyproject.toml",
)

# The driver modules a merge, arm, or close decision actually reads (#1938).
#
# This replaces the blanket `specfuse/loop/` prefix. That prefix was correct in
# intent and far too wide in reach: it covered all 44 modules of the package
# plus every shipped document, so in the one repository where it applies —
# this one — **no gate shipping documentation could arm and no bug fix under
# `specfuse/loop/` could auto-merge**, whether or not it went anywhere near a
# decision. FEAT-2026-0053's close recorded the first half as a structural
# limit that made `auto` "currently unreachable for a large class of
# features"; the first unattended agent run hit the second half, declining two
# of eight items `judge_path_touched` for edits to modules that decide nothing.
#
# Membership rule, applied module by module below: a module is a judge if a
# merge/arm/close verdict, or the evidence a verdict reads, can change because
# of an edit to it. Reporting, notification, scaffolding and plumbing are not
# judges — they act on a verdict already reached.
#
# **`NON_JUDGE_MODULES` is the other half of this list and is not optional.**
# An allowlist silently stops protecting the moment someone adds a module and
# forgets it, which is exactly the failure the blanket prefix could not have.
# `tests/test_judge_path_registry.py` enumerates `specfuse/loop/*.py` and fails
# when a module appears in neither tuple, so a new decision module cannot
# escape by omission — it has to be classified, in writing, with a reason.
JUDGE_MODULES = tuple(
    f"specfuse/loop/{name}"
    for name in (
        # The predicates themselves.
        "arm_eval.py",           # this module: the arm verdict
        "arm_sweep.py",          # evaluates the arm predicate over a corpus
        "arm_txn.py",            # performs the arm the verdict authorises
        "gate_eval.py",          # the auto-close verdict
        "bug_lane.py",           # the merge-guardrail verdict
        "bug_lane_run.py",       # holds the single `gh pr merge` call site
        "bug_lane_state.py",     # the rolling merge cap a guardrail reads
        "upgrade_merge_gate.py",  # the scaffold-upgrade merge gate
        # The dials, budgets and command sets a verdict is measured against.
        "agent_policy.py",       # automerge dial, diff/merge caps, test paths
        "cost.py",               # spend, read by budget_projection
        "gate_commands.py",      # resolves which commands a gate must pass
        # What a work unit or a close must satisfy.
        "closing_requirements.py",
        "criteria_state.py",
        "lint_closing.py",
        "lint_plan.py",
        "plan_baseline.py",      # the baseline retroactive_edits compares to
        # The driver: dispatch guards, halt classification, the produces gate,
        # post-pass invariants. The largest judge surface in the package.
        "loop.py",
        "prerun.py",
        "prerun_capture.py",
        # Trail integrity: a verdict is only as good as the events proving it.
        "validate_event.py",
    )
)

# Every other module under `specfuse/loop/`, each with the reason it decides
# nothing. Same shape, and the same obligation, as
# `DEPENDENCY_MANIFEST_NAMED_UNCOVERED` below: a module whose honest answer is
# "it does judge" belongs in `JUDGE_MODULES` instead.
NON_JUDGE_MODULES = {
    "__init__.py": "package marker; no logic",
    "_filelock.py": "advisory lock primitive; grants no verdict",
    "_miniyaml.py": "YAML parsing primitive used by judges and non-judges alike",
    "_wu_sections.py": "work-unit section splitting; a reader, not a verdict",
    "adopt_feature.py": "scaffolds a feature folder from a GitHub issue",
    "changelog.py": "parses and stamps CHANGELOG.md; no gate reads it",
    "driver_edit.py": "applies operator edits to a feature folder",
    "escalation.py": "renders and files needs-human records after a halt",
    "events_stats.py": "aggregates the event trail for reporting",
    "gh_backend.py": "GitHub side effects for a decision already taken",
    "gh_features.py": "reads GitHub feature issues; supplies input, judges none",
    "heartbeat.py": "liveness reporting",
    "labels.py": "label registry and provisioning; a projection of a verdict",
    "learnings_query.py": "reads LEARNINGS.md for planning context",
    "lint_monitoring.py": "lints monitoring.yml, which no arm/close/merge "
        "verdict reads",
    "lint_roadmap.py": "lints roadmap.md, which no arm/close/merge verdict reads",
    "notify.py": "delivery of a message about a decision already made",
    "notify_escalation.py": "as notify.py",
    "notify_sla.py": "as notify.py",
    "policy_proposals.py": "drafts policy changes for a human to accept",
    "policy_review.py": "presents proposals; the human decides",
    "rearm_migration.py": "one-shot migration of re-arm history format",
    "scaffold.py": "writes scaffold files into a target project",
    "triage.py": "classifies inbound issues; sets no gate and merges nothing",
}

# Package data is what a target project receives, so a work unit editing a
# shipped rule, schema, template or workflow is editing the *source of* a judge
# surface in every downstream repository. Those subtrees stay covered.
#
# `data/docs/` is the deliberate exclusion: it is prose for humans, read by no
# predicate. Mirroring every shipped document under `specfuse/loop/data/docs/`
# is what made `judge_editing` fire on any gate that shipped documentation —
# FEAT-2026-0053's own close watched it fire on three documentation work units
# and recorded that narrowing "needs a decision with evidence, not a one-line
# prefix edit". This is that decision: the evidence is that no consumer of
# `data/docs/` exists in any predicate, enforced by the registry test.
JUDGE_DATA_PREFIXES = tuple(
    f"specfuse/loop/data/{name}"
    for name in (
        "rules/",
        "rules-local/",
        "schemas/",
        "templates/",
        "workflows/",
        "verification.yml.example",
    )
)

NON_JUDGE_DATA_ENTRIES = {
    "docs": "documentation for humans; no predicate reads it",
    "CHANGELOG.seed.md": "seed content for a new project's changelog",
    "LEARNINGS.template.md": "seed content for a new project's learnings file",
    "VERSION": "the scaffold version string",
    "gitignore.snippet": "seed content for .gitignore",
    "monitoring-secrets-checklist.md": "operator checklist prose",
    "monitoring.overrides.yml.example": "seeds monitoring config, which no "
        "arm/close/merge verdict reads",
    "monitoring.yml.example": "as monitoring.overrides.yml.example",
    "roadmap.template.md": "seed content for a new project's roadmap",
}

JUDGE_PATHS = _UNIVERSAL_JUDGE_PATHS + JUDGE_MODULES + JUDGE_DATA_PREFIXES

# Dependency-manifest recognition surface (class 3). One stated table:
# `fnmatch` patterns (exact basenames are just patterns with no special
# characters) matched against `Path(p).name`. Same `pyproject.toml` caveat as
# JUDGE_PATHS above.
#
# Covered: manifests decision_class_paths fires on.
DEPENDENCY_MANIFEST_COVERED = (
    "pyproject.toml",
    "package.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "composer.json",
    "requirements*.txt",
    "*.csproj",
)

# Named-uncovered: manifests we know exist and deliberately do not cover yet.
# Each entry carries a reason so "why not just cover it" has a written answer
# on file — an entry whose honest answer is "we should" belongs in the
# covered tuple above instead. A produced path matching one of these reports
# not_evaluable (trigger 1), not clean.
#
# Lockfiles (package-lock.json, poetry.lock, Cargo.lock, go.sum, Gemfile.lock,
# yarn.lock) are dependency changes by any reasonable reading, but were not
# part of FEAT-2026-0061's chartered scope (PLAN.md "Scope boundary"). They
# are named-uncovered here rather than left undiscussed.
DEPENDENCY_MANIFEST_NAMED_UNCOVERED = {
    "mix.exs": "Elixir manifest; Elixir is not yet a Specfuse target ecosystem",
    "pubspec.yaml": "Dart/Flutter manifest; not yet a Specfuse target ecosystem",
    "Podfile": "CocoaPods manifest; not yet a Specfuse target ecosystem",
    "*.gemspec": "Ruby gemspec; Gemfile is covered above, gemspec is not yet",
    "*.cabal": "Haskell manifest; not yet a Specfuse target ecosystem",
    "package-lock.json": "lockfile derived from the covered package.json, "
        "not the dependency declaration itself; out of this feature's scope",
    "poetry.lock": "lockfile derived from the covered pyproject.toml, not "
        "the dependency declaration itself; out of this feature's scope",
    "Cargo.lock": "lockfile derived from the covered Cargo.toml, not the "
        "dependency declaration itself; out of this feature's scope",
    "go.sum": "checksum file derived from the covered go.mod, not the "
        "dependency declaration itself; out of this feature's scope",
    "Gemfile.lock": "lockfile derived from the covered Gemfile, not the "
        "dependency declaration itself; out of this feature's scope",
    "yarn.lock": "lockfile derived from the covered package.json, not the "
        "dependency declaration itself; out of this feature's scope",
}

_FM_DELIM = re.compile(r"^---\s*$")
_TITLE_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)

CLASS_NAMES = (
    "budget_projection",
    "judge_editing",
    "decision_class_paths",
    "retroactive_edits",
    "drift_caps",
    "missing_provenance",
    "open_questions_human_only",
    "plan_next_lint",
)

VETO_CLASSES = frozenset(
    {"missing_provenance", "open_questions_human_only", "plan_next_lint"}
)


@dataclass(frozen=True)
class ClassVerdict:
    status: str   # "fired" | "clean" | "not_evaluable"
    reason: str


@dataclass(frozen=True)
class ArmDecision:
    would_arm: bool
    classes: dict            # class name -> ClassVerdict, one entry per CLASS_NAMES
    feature_id: str
    gate_id: int              # the just-closed gate
    predicate_version: str


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text) from ---\n...\n--- delimited text."""
    lines = text.splitlines()
    if not lines or not _FM_DELIM.match(lines[0]):
        return {}, text
    end = next((i for i, ln in enumerate(lines[1:], 1) if _FM_DELIM.match(ln)), None)
    if end is None:
        return {}, text
    fm = _miniyaml.parse("\n".join(lines[1:end])) or {}
    body = "\n".join(lines[end + 1:])
    return fm, body


def _read_wu(feature_dir: Path, ref: dict) -> "dict | None":
    """Return a normalized WU record, or None when the referenced file is absent."""
    path = feature_dir / ref["file"]
    if not path.exists():
        return None
    fm, body = _parse_frontmatter(path.read_text())
    title_m = _TITLE_RE.search(body)
    goal = title_m.group(1).strip() if title_m else ref["id"]
    return {
        "id": ref["id"],
        "type": fm.get("type", "implementation"),
        "status": fm.get("status", "pending"),
        "cost_usd": wu_lifetime_cost_usd(path, feature_dir / "events.jsonl"),
        "planned_cost_usd": fm.get("planned_cost_usd"),
        "produces": fm.get("produces") or [],
        "produces_driver_helper": fm.get("produces_driver_helper") or [],
        "human_only": bool(fm.get("human_only", False)),
        "provenance": fm.get("provenance"),
        "goal": goal,
    }


def _matches_judge_path(path: str) -> bool:
    return any(path == jp or path.startswith(jp) for jp in JUDGE_PATHS)


def _is_glob_or_directory(path: str) -> bool:
    return any(c in path for c in "*?[") or path.endswith("/")


def _matches_dependency_manifest(path: str) -> "tuple[str, str]":
    """Return (verdict, detail) for `path` against the recognition table.

    verdict is one of "covered" / "undecidable" / "no". detail names the
    matched pattern (covered) or which trigger fired and why (undecidable);
    it is "" for "no".
    """
    if _is_glob_or_directory(path):
        return "undecidable", "trigger 2: glob or directory in produces:"
    basename = path.rsplit("/", 1)[-1]
    for pattern in DEPENDENCY_MANIFEST_COVERED:
        if fnmatch.fnmatch(basename, pattern):
            return "covered", pattern
    for pattern, reason in DEPENDENCY_MANIFEST_NAMED_UNCOVERED.items():
        if fnmatch.fnmatch(basename, pattern):
            return "undecidable", f"trigger 1: named-uncovered {pattern} ({reason})"
    return "no", ""


def evaluate_arm_predicate(feature_dir: Path, just_closed_gate: int) -> ArmDecision:
    """Return an ArmDecision for the gate that just closed in `feature_dir`.

    `just_closed_gate` is the gate number that just passed; the predicate
    evaluates whether gate `just_closed_gate + 1`'s drafted WUs may be armed.
    """
    feature_dir = Path(feature_dir)
    plan_fm, _ = _parse_frontmatter((feature_dir / "PLAN.md").read_text())
    feature_id = plan_fm.get("feature_id", feature_dir.name)

    baseline = load_baseline(feature_dir)
    if baseline is None:
        classes = {name: ClassVerdict("not_evaluable", "no_baseline") for name in CLASS_NAMES}
        return ArmDecision(
            would_arm=False,
            classes=classes,
            feature_id=feature_id,
            gate_id=just_closed_gate,
            predicate_version=PREDICATE_VERSION,
        )

    plan = load_plan_graph(feature_dir)
    gates = plan.get("gates", []) or []

    # Baseline indices
    baseline_wus: dict[str, dict] = {}
    baseline_gate_wu_ids: dict[int, set] = {}
    for g in baseline.get("gates", []) or []:
        ids = set()
        for wu in g.get("work_units", []) or []:
            baseline_wus[wu["id"]] = wu
            ids.add(wu["id"])
        baseline_gate_wu_ids[g["gate"]] = ids
    baseline_gate_nums = set(baseline_gate_wu_ids.keys())
    baseline_total_planned = sum(
        (wu.get("planned_cost_usd") or 0.0) for wu in baseline_wus.values()
    )
    baseline_total_count = len(baseline_wus)

    # Current plan indices
    current_by_gate: dict[int, list] = {}
    current_all: dict[str, dict] = {}
    for g in gates:
        gnum = g.get("gate")
        wus = []
        for ref in g.get("work_units", []) or []:
            wu = _read_wu(feature_dir, ref)
            if wu is None:
                continue
            wus.append(wu)
            current_all[wu["id"]] = wu
        current_by_gate[gnum] = wus

    added_ids = set(current_all) - set(baseline_wus)

    classes: dict[str, ClassVerdict] = {}

    # --- Class 1: budget projection ---
    lifetime_spend = sum(wu["cost_usd"] for wu in current_all.values())
    planned_remaining = sum(
        (wu["planned_cost_usd"] or 0.0)
        for wu in current_all.values()
        if wu["status"] != "done"
    )
    projection = lifetime_spend + planned_remaining
    ceiling = BUDGET_PROJECTION_MULTIPLIER * baseline_total_planned
    if projection > ceiling:
        classes["budget_projection"] = ClassVerdict(
            "fired",
            f"projected spend ${projection:.2f} (spend ${lifetime_spend:.2f} + "
            f"remaining ${planned_remaining:.2f}) exceeds "
            f"{BUDGET_PROJECTION_MULTIPLIER:.1f}x baseline planned total "
            f"${baseline_total_planned:.2f} (cap ${ceiling:.2f})",
        )
    else:
        classes["budget_projection"] = ClassVerdict(
            "clean",
            f"projected spend ${projection:.2f} within "
            f"{BUDGET_PROJECTION_MULTIPLIER:.1f}x baseline planned total "
            f"${baseline_total_planned:.2f} (cap ${ceiling:.2f})",
        )

    next_gate_num = just_closed_gate + 1
    drafted = current_by_gate.get(next_gate_num, [])

    # --- Class 2: judge-editing ---
    judge_hits: list[str] = []
    for wu in drafted:
        for p in wu["produces"]:
            if _matches_judge_path(p):
                judge_hits.append(f"{wu['id']} produces {p}")
        if wu["produces_driver_helper"]:
            judge_hits.append(
                f"{wu['id']} declares produces_driver_helper "
                f"{wu['produces_driver_helper']!r}"
            )
    if judge_hits:
        classes["judge_editing"] = ClassVerdict("fired", "; ".join(judge_hits))
    else:
        classes["judge_editing"] = ClassVerdict(
            "clean", "no drafted WU touches judge-path surfaces"
        )

    # --- Class 3: decision-class paths ---
    # Precedence: any covered hit fires, even if a sibling produced path in
    # the same WU is undecidable — a definite dependency hit is never masked
    # by an undecidable sibling. Only when nothing is covered does an
    # undecidable path report not_evaluable instead of clean.
    dep_covered_hits: list[str] = []
    dep_undecidable_hits: list[str] = []
    for wu in drafted:
        for p in wu["produces"]:
            verdict, detail = _matches_dependency_manifest(p)
            if verdict == "covered":
                dep_covered_hits.append(f"{wu['id']} produces {p} (matches {detail})")
            elif verdict == "undecidable":
                dep_undecidable_hits.append(f"{wu['id']} produces {p}: {detail}")
    if dep_covered_hits:
        classes["decision_class_paths"] = ClassVerdict(
            "fired", "; ".join(dep_covered_hits)
        )
    elif dep_undecidable_hits:
        classes["decision_class_paths"] = ClassVerdict(
            "not_evaluable", "; ".join(dep_undecidable_hits)
        )
    else:
        classes["decision_class_paths"] = ClassVerdict(
            "clean",
            "no drafted WU touches a recognised dependency manifest "
            f"({', '.join(DEPENDENCY_MANIFEST_COVERED)})",
        )

    # --- Class 4: retroactive edits (baseline WUs of already-passed gates) ---
    retro_hits: list[str] = []
    for gnum, ids in baseline_gate_wu_ids.items():
        gate_entry = next((g for g in gates if g.get("gate") == gnum), None)
        gate_file = gate_entry.get("file") if gate_entry else f"GATE-{gnum:02d}.md"
        gate_path = feature_dir / gate_file
        if not gate_path.exists():
            continue
        gate_fm, _ = _parse_frontmatter(gate_path.read_text())
        if gate_fm.get("status") != "passed":
            continue
        for wu_id in sorted(ids):
            baseline_wu = baseline_wus[wu_id]
            current_wu = current_all.get(wu_id)
            if current_wu is None:
                retro_hits.append(f"{wu_id} left the graph")
                continue
            if current_wu["type"] != baseline_wu.get("type"):
                retro_hits.append(
                    f"{wu_id} type changed {baseline_wu.get('type')!r} -> "
                    f"{current_wu['type']!r}"
                )
            if current_wu["goal"] != baseline_wu.get("goal"):
                retro_hits.append(
                    f"{wu_id} goal changed {baseline_wu.get('goal')!r} -> "
                    f"{current_wu['goal']!r}"
                )
    if retro_hits:
        classes["retroactive_edits"] = ClassVerdict("fired", "; ".join(retro_hits))
    else:
        classes["retroactive_edits"] = ClassVerdict(
            "clean", "no passed-gate baseline WU altered or removed"
        )

    # --- Class 5: drift caps ---
    added_count = len(added_ids)
    added_sum = sum((current_all[i]["planned_cost_usd"] or 0.0) for i in added_ids)
    current_gate_nums = {g.get("gate") for g in gates}
    added_gate_nums = current_gate_nums - baseline_gate_nums
    count_ceiling = DRIFT_CAP_RATIO * baseline_total_count
    sum_ceiling = DRIFT_CAP_RATIO * baseline_total_planned
    drift_hits: list[str] = []
    if added_count > count_ceiling:
        drift_hits.append(
            f"added WU count {added_count} exceeds {DRIFT_CAP_RATIO:.1f}x baseline "
            f"count {baseline_total_count} (cap {count_ceiling:.1f})"
        )
    if added_sum > sum_ceiling:
        drift_hits.append(
            f"added planned cost ${added_sum:.2f} exceeds {DRIFT_CAP_RATIO:.1f}x "
            f"baseline planned total ${baseline_total_planned:.2f} "
            f"(cap ${sum_ceiling:.2f})"
        )
    if len(added_gate_nums) > ADDED_GATE_CAP:
        drift_hits.append(
            f"added gate count {len(added_gate_nums)} exceeds cap {ADDED_GATE_CAP}: "
            f"{sorted(added_gate_nums)}"
        )
    if drift_hits:
        classes["drift_caps"] = ClassVerdict("fired", "; ".join(drift_hits))
    else:
        classes["drift_caps"] = ClassVerdict(
            "clean", "added WUs and gates within drift caps"
        )

    # --- Class 6: missing provenance (veto channel) ---
    missing_prov = sorted(
        wu_id for wu_id in added_ids if not current_all[wu_id]["provenance"]
    )
    if missing_prov:
        classes["missing_provenance"] = ClassVerdict(
            "fired", f"added WU(s) missing provenance: {', '.join(missing_prov)}"
        )
    else:
        classes["missing_provenance"] = ClassVerdict(
            "clean",
            "every added WU carries a provenance field" if added_ids else "no added WUs",
        )

    # --- Class 7: open questions / human-only (veto channel) ---
    reasons7: list[str] = []
    if next_gate_num in current_by_gate:
        review_path = feature_dir / gate_review_filename(next_gate_num)
        if not review_path.exists():
            reasons7.append(f"{review_path.name} missing")
        else:
            review_fm, _ = _parse_frontmatter(review_path.read_text())
            if "open_questions" not in review_fm:
                reasons7.append(f"{review_path.name} missing open_questions field")
            else:
                oq = review_fm.get("open_questions") or []
                if oq:
                    reasons7.append(f"{review_path.name} open_questions non-empty: {oq!r}")
        human_only_hits = [wu["id"] for wu in drafted if wu["human_only"]]
        if human_only_hits:
            reasons7.append(f"human_only flagged: {', '.join(human_only_hits)}")
        clean_reason = "open_questions present and empty, no human_only flags"
    else:
        clean_reason = "terminal gate: no drafted successor"
    if reasons7:
        classes["open_questions_human_only"] = ClassVerdict("fired", "; ".join(reasons7))
    else:
        classes["open_questions_human_only"] = ClassVerdict("clean", clean_reason)

    # --- Class 8: plan-next contract lint (veto channel, FEAT-2026-0053/T07) ---
    # lint_plan_next_draft is WARN-only for its own CLI caller; here a
    # non-empty finding list vetoes the arm. A parse failure inside the lint
    # (malformed frontmatter) must degrade to a fired verdict, not crash the
    # gate close — same precedent as build_arm_predicate_event's outer catch.
    try:
        from .lint_plan import lint_plan_next_draft  # deferred: lint_plan imports loop.py

        lint_warns = lint_plan_next_draft(feature_dir, just_closed_gate)
    except Exception as exc:  # noqa: BLE001 - a raise is not a verdict
        classes["plan_next_lint"] = ClassVerdict(
            "fired",
            f"plan-next lint raised {type(exc).__name__}: {exc}",
        )
    else:
        if lint_warns:
            classes["plan_next_lint"] = ClassVerdict("fired", "; ".join(lint_warns))
        else:
            classes["plan_next_lint"] = ClassVerdict("clean", "plan-next lint: no findings")

    # not_evaluable is fail-closed, same as fired — a class with no basis to
    # evaluate must not let arming proceed on its say-so.
    would_arm = all(classes[name].status == "clean" for name in CLASS_NAMES)

    return ArmDecision(
        would_arm=would_arm,
        classes=classes,
        feature_id=feature_id,
        gate_id=just_closed_gate,
        predicate_version=PREDICATE_VERSION,
    )


def _format_decision(decision: ArmDecision) -> str:
    """Render an ArmDecision to the canonical event-trail block shape."""
    lines: list[str] = [
        f"  arm_predicate  gate={decision.gate_id}  would_arm={decision.would_arm}"
    ]
    for name in CLASS_NAMES:
        v = decision.classes.get(name)
        if v is None:
            continue
        lines.append(f"    {name}: {v.status} — {v.reason}")
    return "\n".join(lines)
