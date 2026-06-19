#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Deterministic gate-close predicate — pure, side-effect-free module.

Given a feature directory and a gate id, evaluates the v1 predicate and
returns an AutoCloseDecision. No imports from loop.py. No subprocess calls.
No file writes. Pure read + compute.

Coverage pragmas removed in T02 (tests/test_gate_eval.py) — T01 had added
them temporarily so the overall coverage threshold was unaffected before
tests landed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from . import _miniyaml

PREDICATE_VERSION = "v1"
PER_WU_COST_RATIO_CEILING = 1.5
PER_WU_HARD_OVERRUN_RATIO = 2.0
PLAN_NEXT_COST_RATIO_CEILING = 1.5

_FM_DELIM = re.compile(r"^---\s*$")
_YAML_BLOCK_RE = re.compile(r"```ya?ml\s*\n(.*?)\n```", re.DOTALL)
_CLOSING_TYPES = frozenset({"close", "close-intermediate"})
_NON_SUBSTANTIVE_TYPES = frozenset({"close", "close-intermediate", "plan-next"})


@dataclass(frozen=True)
class AutoCloseDecision:
    auto: bool                  # True iff predicate fires
    reasons: list[str]          # one entry per failing criterion (empty if auto=True)
    metrics: dict               # raw numbers for human inspection
    gate_id: int
    feature_id: str
    predicate_version: str      # "v1" — bumped when constants change


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


def _read_plan_metrics(feature_dir: Path) -> dict:
    """Return frontmatter + parsed task-graph gates from PLAN.md."""
    text = (feature_dir / "PLAN.md").read_text()
    fm, body = _parse_frontmatter(text)
    gates: list[dict] = []
    m = _YAML_BLOCK_RE.search(body)
    if m:
        graph = _miniyaml.parse(m.group(1)) or {}
        gates = graph.get("gates", []) or []
    return {"frontmatter": fm, "gates": gates}


def _read_wu_metrics(wu_path: Path) -> dict:
    """Return WU frontmatter as dict, with defaults for missing fields."""
    fm, _ = _parse_frontmatter(wu_path.read_text())
    return {
        "id": fm.get("id", ""),
        "type": fm.get("type", "implementation"),
        "status": fm.get("status", "pending"),
        "attempts": fm.get("attempts", 0),
        "cost_usd": fm.get("cost_usd", 0.0),
        "planned_cost_usd": fm.get("planned_cost_usd"),   # None when absent
        "auto_close": fm.get("auto_close"),
        "rearm_count": fm.get("rearm_count", 0),          # FEAT-2026-0016; 0 when absent
    }


def _read_events(events_path: Path, wu_ids: list[str]) -> list[dict]:
    """Return events whose correlation_id is in wu_ids. Returns [] if file missing."""
    if not events_path.exists():
        return []
    id_set = set(wu_ids)
    out: list[dict] = []
    with events_path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                ev = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if ev.get("correlation_id") in id_set:
                out.append(ev)
    return out


def _apply_predicate(
    plan_metrics: dict,
    wu_metrics_list: list[dict],
    events: list[dict],
    gate_budget: float | None,
) -> tuple[list[str], dict]:
    """Apply all v1 predicate checks. Collects ALL failure reasons; no short-circuit.

    Returns (reasons, metrics_dict).
    """
    reasons: list[str] = []
    warnings: list[str] = []

    # Index events by WU ID for O(1) lookup
    events_by_wu: dict[str, list[dict]] = {}
    for ev in events:
        cid = ev.get("correlation_id", "")
        events_by_wu.setdefault(cid, []).append(ev)

    # Metrics accumulators
    per_wu_cost: dict[str, float] = {}
    per_wu_planned: dict[str, float | None] = {}
    gate_total_cost = 0.0
    plan_next_cost: float | None = None
    plan_next_planned: float | None = None
    blocked_human_events: list[str] = []
    replan_events: list[str] = []
    final_outcomes: dict[str, str] = {}

    # First pass: compute per-WU metrics and determine final outcomes
    for wm in wu_metrics_list:
        wu_id = wm["id"]
        cost = wm["cost_usd"]
        planned = wm["planned_cost_usd"]
        wu_type = wm["type"]

        per_wu_cost[wu_id] = cost
        per_wu_planned[wu_id] = planned
        gate_total_cost += cost

        if wu_type == "plan-next":
            plan_next_cost = cost
            plan_next_planned = planned

        # Determine final outcome from event sequence
        wu_evs = events_by_wu.get(wu_id, [])
        last_terminal = None
        for ev in wu_evs:
            if ev.get("event_type") in ("task_completed", "human_escalation", "blocked_human"):
                last_terminal = ev
        if last_terminal is None:
            final_outcomes[wu_id] = "no_events"
        elif last_terminal.get("event_type") == "task_completed":
            final_outcomes[wu_id] = "passed"
        else:
            final_outcomes[wu_id] = "escalated"

    # --- Check 1: No blocked_human / human_escalation events ---
    seen_blocked: set[str] = set()
    for ev in events:
        if ev.get("event_type") in ("human_escalation", "blocked_human"):
            wu_id = ev.get("correlation_id", "unknown")
            if wu_id in seen_blocked:
                continue
            seen_blocked.add(wu_id)
            blocked_human_events.append(wu_id)
            sub_id = wu_id.split("/")[-1] if "/" in wu_id else wu_id
            ts = ev.get("timestamp", "")[:10]
            reasons.append(f"blocked_human_in_chain: {sub_id} escalated {ts}")

    # FEAT-2026-0016 re-arm history: rearm_count > 0 signals a prior blocked cycle
    for wm in wu_metrics_list:
        rearm = wm.get("rearm_count", 0)
        if rearm and rearm > 0:
            wu_id = wm["id"]
            if wu_id not in seen_blocked:
                seen_blocked.add(wu_id)
                blocked_human_events.append(wu_id)
                sub_id = wu_id.split("/")[-1] if "/" in wu_id else wu_id
                reasons.append(
                    f"blocked_human_in_chain: {sub_id} (rearm_count={rearm})"
                )

    # --- Check 2: No replan events ---
    seen_replan: set[str] = set()
    for ev in events:
        if ev.get("event_type") == "replan":
            wu_id = ev.get("correlation_id", "unknown")
            if wu_id in seen_replan:
                continue
            seen_replan.add(wu_id)
            replan_events.append(wu_id)
            sub_id = wu_id.split("/")[-1] if "/" in wu_id else wu_id
            reasons.append(f"replan_event: {sub_id}")

    # --- Checks 3 & 4: Per-WU cost ratios (skip close/close-intermediate and plan-next) ---
    for wm in wu_metrics_list:
        wu_type = wm["type"]
        if wu_type in _CLOSING_TYPES or wu_type == "plan-next":
            continue
        wu_id = wm["id"]
        sub_id = wu_id.split("/")[-1] if "/" in wu_id else wu_id
        cost = wm["cost_usd"]
        planned = wm["planned_cost_usd"]

        if planned is None:
            warnings.append(f"planned_cost_missing: {sub_id}")
            continue

        ratio = (cost / planned) if planned > 0 else (float("inf") if cost > 0 else 0.0)

        if ratio > PER_WU_COST_RATIO_CEILING:
            reasons.append(
                f"per_wu_cost_overrun: {sub_id} actual=${cost:.2f} "
                f"planned=${planned:.2f} ratio={ratio:.2f}x"
            )

        if ratio > PER_WU_HARD_OVERRUN_RATIO:
            reasons.append(
                f"per_wu_hard_overrun: {sub_id} actual=${cost:.2f} "
                f"planned=${planned:.2f} ratio={ratio:.2f}x"
            )

    # --- Check 5: Plan-next ≤ 1.5× planned ---
    for wm in wu_metrics_list:
        if wm["type"] != "plan-next":
            continue
        wu_id = wm["id"]
        sub_id = wu_id.split("/")[-1] if "/" in wu_id else wu_id
        cost = wm["cost_usd"]
        planned = wm["planned_cost_usd"]

        if planned is None:
            warnings.append(f"planned_cost_missing: {sub_id}")
            continue

        ratio = (cost / planned) if planned > 0 else (float("inf") if cost > 0 else 0.0)

        if ratio > PLAN_NEXT_COST_RATIO_CEILING:
            reasons.append(
                f"plan_next_overrun: {sub_id} actual=${cost:.2f} "
                f"planned=${planned:.2f} ratio={ratio:.2f}x"
            )

    # --- Check 6: Gate total ≤ cost_budget_usd (skip when budget absent) ---
    if gate_budget is not None:
        if gate_total_cost > gate_budget:
            reasons.append(
                f"gate_budget_exceeded: total=${gate_total_cost:.2f} "
                f"budget=${gate_budget:.2f}"
            )

    # --- Check 7: Every substantive WU's final outcome must be passed ---
    for wm in wu_metrics_list:
        if wm["type"] in _NON_SUBSTANTIVE_TYPES:
            continue
        wu_id = wm["id"]
        sub_id = wu_id.split("/")[-1] if "/" in wu_id else wu_id
        outcome = final_outcomes.get(wu_id, "no_events")
        if outcome != "passed":
            reasons.append(f"final_attempt_not_passed: {sub_id} (outcome={outcome})")

    metrics: dict = {
        "per_wu_cost": per_wu_cost,
        "per_wu_planned": per_wu_planned,
        "gate_total_cost": gate_total_cost,
        "gate_budget": gate_budget,
        "plan_next_cost": plan_next_cost,
        "plan_next_planned": plan_next_planned,
        "blocked_human_events": blocked_human_events,
        "replan_events": replan_events,
        "final_outcomes": final_outcomes,
        "warnings": warnings,
    }
    return reasons, metrics


def evaluate_auto_close(feature_dir: Path, gate_id: int) -> AutoCloseDecision:
    """Return AutoCloseDecision for gate_id in the given feature directory."""
    plan = _read_plan_metrics(feature_dir)
    fm = plan["frontmatter"]
    feature_id = fm.get("feature_id", feature_dir.name)

    # Operator manual override — honored before reading any WU evidence
    if fm.get("auto_close_disabled") is True:
        return AutoCloseDecision(
            auto=False,
            reasons=["auto_close_disabled_per_plan"],
            metrics={"warnings": []},
            gate_id=gate_id,
            feature_id=feature_id,
            predicate_version=PREDICATE_VERSION,
        )

    # Locate target gate in task graph
    gates = plan["gates"]
    target_gate = next((g for g in gates if g.get("gate") == gate_id), None)
    if target_gate is None:
        return AutoCloseDecision(
            auto=False,
            reasons=[f"gate_not_found: gate {gate_id} absent in PLAN.md graph"],
            metrics={"warnings": []},
            gate_id=gate_id,
            feature_id=feature_id,
            predicate_version=PREDICATE_VERSION,
        )

    # Load GATE-NN.md frontmatter for optional budget (check 6)
    gate_budget: float | None = None
    gate_file_name = target_gate.get("file", f"GATE-{gate_id:02d}.md")
    gate_path = feature_dir / gate_file_name
    if gate_path.exists():
        gate_fm, _ = _parse_frontmatter(gate_path.read_text())
        gate_budget = gate_fm.get("cost_budget_usd")

    # Resolve WU list from task graph
    wu_refs = target_gate.get("work_units", []) or []
    wu_ids = [ref["id"] for ref in wu_refs if ref.get("id")]

    # Load events — graceful degrade if file missing
    events_path = feature_dir / "events.jsonl"
    pre_warnings: list[str] = []
    if not events_path.exists():
        pre_warnings.append("events_jsonl_missing")
    events = _read_events(events_path, wu_ids)

    # Load WU metrics; missing files are hard failures (refuse partial evaluation)
    wu_metrics_list: list[dict] = []
    missing_reasons: list[str] = []
    for ref in wu_refs:
        wu_id = ref.get("id", "unknown")
        wu_file = ref.get("file", "")
        wu_path = feature_dir / wu_file
        sub_id = wu_id.split("/")[-1] if "/" in wu_id else wu_id
        if not wu_path.exists():
            missing_reasons.append(f"wu_file_missing: {sub_id}")
        else:
            wu_metrics_list.append(_read_wu_metrics(wu_path))

    if missing_reasons:
        return AutoCloseDecision(
            auto=False,
            reasons=missing_reasons,
            metrics={
                "per_wu_cost": {},
                "per_wu_planned": {},
                "gate_total_cost": 0.0,
                "gate_budget": gate_budget,
                "plan_next_cost": None,
                "plan_next_planned": None,
                "blocked_human_events": [],
                "replan_events": [],
                "final_outcomes": {},
                "warnings": pre_warnings,
            },
            gate_id=gate_id,
            feature_id=feature_id,
            predicate_version=PREDICATE_VERSION,
        )

    reasons, metrics = _apply_predicate(plan, wu_metrics_list, events, gate_budget)
    metrics["warnings"] = pre_warnings + metrics.get("warnings", [])

    return AutoCloseDecision(
        auto=len(reasons) == 0,
        reasons=reasons,
        metrics=metrics,
        gate_id=gate_id,
        feature_id=feature_id,
        predicate_version=PREDICATE_VERSION,
    )


# ---------------------------------------------------------------------------
# CLI helpers (T03)
# ---------------------------------------------------------------------------


def _resolve_feature_dir(feature_id: str, repo_root: Path) -> "Path | None":
    """Resolve a feature ID (full, partial numeric, or slug) to a feature directory.

    Returns None on no match; raises ValueError on ambiguous partial match.
    """
    features_dir = repo_root / ".specfuse" / "features"
    if not features_dir.is_dir():
        return None

    candidates = sorted(d for d in features_dir.iterdir() if d.is_dir())

    # Priority 1: exact directory name
    exact = [d for d in candidates if d.name == feature_id]
    if len(exact) == 1:
        return exact[0]

    # Priority 2: name starts with "<feature_id>-" (full FEAT-YYYY-NNNN prefix)
    prefix = [d for d in candidates if d.name.startswith(feature_id + "-")]
    if len(prefix) == 1:
        return prefix[0]
    if len(prefix) > 1:
        raise ValueError(f"ambiguous: {[d.name for d in prefix]}")

    # Priority 3: partial numeric (0017) or slug suffix match
    partial: list[Path] = []
    for d in candidates:
        name = d.name
        parts = name.split("-")
        # FEAT-YYYY-NNNN-slug → parts[2] is the NNNN part
        if len(parts) >= 4:
            nnnn = parts[2]
            slug = "-".join(parts[3:])
            if nnnn == feature_id or slug == feature_id:
                partial.append(d)
        elif feature_id in name:
            partial.append(d)

    if len(partial) == 0:
        return None
    if len(partial) == 1:
        return partial[0]
    raise ValueError(f"ambiguous: {[d.name for d in partial]}")


def _format_decision(decision: AutoCloseDecision) -> str:
    """Render an AutoCloseDecision to the canonical block shape."""
    lines: list[str] = []
    gate_str = f"G{decision.gate_id:02d}"
    lines.append(f"  {gate_str}  auto={decision.auto}")
    if decision.reasons:
        lines.append("    reasons:")
        for r in decision.reasons:
            lines.append(f"      - {r}")
    lines.append("    metrics:")
    total = decision.metrics.get("gate_total_cost", 0.0)
    budget = decision.metrics.get("gate_budget")
    lines.append(f"      gate_total_cost: ${total:.2f}")
    budget_str = f"${budget:.2f}" if budget is not None else "<unset>"
    lines.append(f"      gate_budget: {budget_str}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gate_eval.py",
        description=f"Specfuse gate-close predicate CLI (predicate={PREDICATE_VERSION})",
    )
    subparsers = parser.add_subparsers(dest="command")

    bt = subparsers.add_parser(
        "backtest",
        help="Evaluate the auto-close predicate against a feature directory",
    )
    bt.add_argument("feature_id", help="Feature ID (full FEAT-YYYY-NNNN, partial 0017, or slug)")
    bt.add_argument(
        "--gate",
        type=int,
        metavar="N",
        default=None,
        help="Restrict evaluation to gate N",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # backtest subcommand
    repo_root = Path(__file__).resolve().parent.parent.parent

    try:
        feature_dir = _resolve_feature_dir(args.feature_id, repo_root)
    except ValueError as exc:
        print(f"ambiguous feature ID: {exc}")
        sys.exit(0)

    if feature_dir is None:
        print(f"no feature matches: {args.feature_id}")
        sys.exit(0)

    plan = _read_plan_metrics(feature_dir)
    fm = plan["frontmatter"]
    feature_id = fm.get("feature_id", feature_dir.name)
    gates = plan["gates"]

    gate_ids = [g["gate"] for g in gates if isinstance(g.get("gate"), int)]
    if args.gate is not None:
        gate_ids = [gid for gid in gate_ids if gid == args.gate]

    print(f"{feature_id}  predicate={PREDICATE_VERSION}")
    for gate_id in gate_ids:
        decision = evaluate_auto_close(feature_dir, gate_id)
        print(_format_decision(decision))


if __name__ == "__main__":
    main()
