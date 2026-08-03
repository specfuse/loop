#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Read-only sweep of `arm_eval.evaluate_arm_predicate` over real feature folders.

Answers "which arm-predicate branches have ever fired on real input, and
which have only ever been exercised in fixtures" for a whole
`.specfuse/features/` tree. This module is a *reader* of the predicate — it
imports `arm_eval` and `plan_baseline` but is never imported by either, and
never imports `loop.py`. A feature folder is evaluable when it carries
`PLAN.baseline.json`; features that predate `write_baseline_if_absent` are
excluded (not failed) and counted as such, per `no_baseline`.

The trap this module exists to not repeat (`LEARNINGS
[FEAT-2026-0072/G1-CLOSE]`): a sweep over many inputs must classify every
non-zero outcome as *this check fired* or *this check never ran*, never
silently shrink the denominator it claims to have covered. Every evaluable
feature lands in exactly one of `evaluated` / `could_not_evaluate`; nothing
is dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .arm_eval import CLASS_NAMES, evaluate_arm_predicate
from .plan_baseline import BASELINE_FILENAME, load_plan_graph

EXCLUDED_REASON_NO_BASELINE = "no_baseline"

_STATUSES = ("clean", "fired", "not_evaluable")


@dataclass(frozen=True)
class ClassObservation:
    """Per-class branch record: counts and first sighting, one entry per status.

    `first_seen` always carries all three status keys — `None` for a status
    never observed — so absence is representable, not inferred from a
    missing key.
    """

    counts: dict
    first_seen: dict


@dataclass(frozen=True)
class SweepReport:
    evaluable_count: int
    excluded_count: int
    excluded: list = field(default_factory=list)
    evaluated: dict = field(default_factory=dict)
    could_not_evaluate: dict = field(default_factory=dict)
    class_observations: dict = field(default_factory=dict)


def sweep_arm_predicate(features_root) -> SweepReport:
    """Walk `features_root`'s feature folders and sweep the arm predicate.

    Returns a `SweepReport`. Every subdirectory of `features_root` that
    carries a `PLAN.md` is either excluded (no `PLAN.baseline.json`) or
    evaluable; every evaluable feature lands in `evaluated` or
    `could_not_evaluate`, never both, never neither.
    """
    features_root = Path(features_root)

    excluded: list = []
    evaluated: dict = {}
    could_not_evaluate: dict = {}
    status_counts = {name: {status: 0 for status in _STATUSES} for name in CLASS_NAMES}
    first_seen: dict = {name: {} for name in CLASS_NAMES}

    feature_dirs = sorted(
        (p for p in features_root.iterdir() if p.is_dir()), key=lambda p: p.name
    )

    for feature_dir in feature_dirs:
        if not (feature_dir / "PLAN.md").exists():
            continue
        if not (feature_dir / BASELINE_FILENAME).exists():
            excluded.append(
                {"feature": feature_dir.name, "reason": EXCLUDED_REASON_NO_BASELINE}
            )
            continue

        try:
            plan = load_plan_graph(feature_dir)
            gate_nums = sorted({g["gate"] for g in plan.get("gates", []) or []})
            feature_id = feature_dir.name
            gates_swept = []
            for gate_num in gate_nums:
                decision = evaluate_arm_predicate(feature_dir, gate_num)
                feature_id = decision.feature_id
                gates_swept.append(gate_num)
                for name in CLASS_NAMES:
                    verdict = decision.classes[name]
                    status_counts[name][verdict.status] += 1
                    if verdict.status not in first_seen[name]:
                        first_seen[name][verdict.status] = (feature_id, gate_num)
            evaluated[feature_id] = gates_swept
        except Exception as exc:  # noqa: BLE001 - a raise must land as a ledger entry
            could_not_evaluate[feature_dir.name] = f"{type(exc).__name__}: {exc}"

    class_observations = {
        name: ClassObservation(
            counts=dict(status_counts[name]),
            first_seen={status: first_seen[name].get(status) for status in _STATUSES},
        )
        for name in CLASS_NAMES
    }

    return SweepReport(
        evaluable_count=len(evaluated) + len(could_not_evaluate),
        excluded_count=len(excluded),
        excluded=excluded,
        evaluated=evaluated,
        could_not_evaluate=could_not_evaluate,
        class_observations=class_observations,
    )
