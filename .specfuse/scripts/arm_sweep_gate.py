#!/usr/bin/env python3
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Run `arm_sweep.sweep_arm_predicate` over this repo's `.specfuse/features/`
and fail when the sweep itself goes blind (FEAT-2026-0063/T02).

This gate does NOT assert branch coverage. Five of the arm predicate's eight
stop classes — `budget_projection`, `decision_class_paths`, `drift_caps`,
`missing_provenance`, `plan_next_lint` — have never fired on real input as of
authoring (2026-08-03), and no class has ever reported `not_evaluable`.
Asserting that every class has fired, or that `not_evaluable` has been
observed, would be an unsatisfiable acceptance criterion: red today, and
unable to be made green by any work this feature permits, since manufacturing
a fixture to trip a never-fired branch would just be a fixture wearing a
costume (see `PLAN.md` §2 for FEAT-2026-0063). A coverage assertion becomes
satisfiable only once the corpus itself grows a baselined feature whose real
run trips one of those five classes, or hits the predicate's fail-closed
`not_evaluable` path — an event this gate does not manufacture and does not
wait for.

What this gate DOES assert, and why both halves are satisfiable today:

- Every evaluable feature (one that carries `PLAN.baseline.json`) must land
  in `evaluated`, never `could_not_evaluate` — the sweep's own read must not
  silently drop a feature it claims to have covered.
- No `not_evaluable` verdict may appear among evaluable features — among
  features the predicate *could* judge, `not_evaluable` means its
  fail-closed path fired for real, which has never happened and would
  genuinely signal a regression if it started.

The never-fired class list above is printed as output on every run. Printing
it is the deliverable; failing on it is the trap this gate exists to avoid.

Exit codes:
    0 — every evaluable feature was evaluated, and no `not_evaluable` verdict
        appeared among them (including the vacuous case of zero evaluable
        features, reported explicitly rather than passed silently).
    1 — at least one evaluable feature landed in `could_not_evaluate`, or at
        least one `not_evaluable` verdict appeared. Offenders named on
        stderr.
"""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from specfuse.loop.arm_sweep import sweep_arm_predicate  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = REPO_ROOT / ".specfuse" / "features"


def format_table(report) -> str:
    """Render the branch-observation table: per class, which statuses have
    ever been observed and where each was first seen."""
    lines = ["branch-observation table:"]
    for name, obs in report.class_observations.items():
        seen = [status for status in ("clean", "fired", "not_evaluable") if obs.counts.get(status, 0) > 0]
        never = [status for status in ("clean", "fired", "not_evaluable") if obs.counts.get(status, 0) == 0]
        seen_desc = ", ".join(seen) if seen else "(none)"
        never_desc = "; NEVER " + ", NEVER ".join(never) if never else ""
        lines.append(f"  {name:26s} observed=[{seen_desc}]{never_desc}")
    lines.append(
        f"evaluable={report.evaluable_count} "
        f"evaluated={len(report.evaluated)} "
        f"could_not_evaluate={len(report.could_not_evaluate)} "
        f"excluded_no_baseline={report.excluded_count}"
    )
    return "\n".join(lines)


def main() -> int:
    return arm_sweep_gate_main(FEATURES_DIR)


def arm_sweep_gate_main(features_root: Path) -> int:
    report = sweep_arm_predicate(features_root)

    sys.stdout.write(format_table(report) + "\n")

    if report.evaluable_count == 0:
        sys.stdout.write("nothing evaluable: no baselined feature found under the swept root\n")
        return 0

    offenders: list = []

    for feature_name, error in sorted(report.could_not_evaluate.items()):
        offenders.append(f"could_not_evaluate: {feature_name}: {error}")

    for class_name, obs in report.class_observations.items():
        if obs.counts.get("not_evaluable", 0) > 0:
            feature_id, gate_num = obs.first_seen.get("not_evaluable")
            offenders.append(
                f"not_evaluable: class={class_name} feature={feature_id} gate={gate_num}"
            )

    if offenders:
        for msg in offenders:
            sys.stderr.write(msg + "\n")
        sys.stderr.write(f"\n{len(offenders)} arm-sweep offender(s).\n")
        return 1

    sys.stdout.write(
        f"ok: {len(report.evaluated)} evaluable feature(s) swept clean, "
        f"no not_evaluable verdicts\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
