#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Merge-safety gate for post-scaffold-upgrade PRs (FEAT-2026-0029/T01).

Decides whether a PR produced by `specfuse upgrade` is safe to auto-merge:
`merge` only when CI is green AND every existing feature folder still passes
`.specfuse/scripts/lint_plan.py`'s structural-conformance check; `halt` (with a
reason) otherwise. `collect_reports` runs that lint per feature folder found
under `<repo_root>/.specfuse/features/`; `decide` turns the results into the
verdict. lint_plan.py is invoked as a subprocess, never imported, so this
module has no coupling to its internals.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_DETAIL_TAIL_CHARS = 500


def decide(ci_all_green: bool, feature_reports: list[dict]) -> tuple[str, str]:
    """Return (verdict, reason). verdict is 'merge' or 'halt'.

    Fails safe: an empty `feature_reports` halts rather than merging, since
    absence of evidence is not evidence of conformance.
    """
    if not feature_reports:
        return ("halt", "no feature folders were checked")
    if not ci_all_green:
        return ("halt", "CI not green")
    failing = [r["feature"] for r in feature_reports if not r.get("ok")]
    if failing:
        return ("halt", f"conformance failed for: {', '.join(failing)}")
    return ("merge", "")


def collect_reports(repo_root) -> list[dict]:
    """Run lint_plan.py once per feature folder under repo_root; report results."""
    repo_root = Path(repo_root)
    lint_script = repo_root / ".specfuse" / "scripts" / "lint_plan.py"
    features_dir = repo_root / ".specfuse" / "features"

    reports = []
    if not features_dir.is_dir():
        return reports

    for feature_dir in sorted(p for p in features_dir.iterdir() if p.is_dir()):
        result = subprocess.run(
            [sys.executable, str(lint_script), str(feature_dir)],
            capture_output=True,
            text=True,
        )
        ok = result.returncode == 0
        detail = ""
        if not ok:
            output = (result.stdout + result.stderr).strip()
            detail = output[-_DETAIL_TAIL_CHARS:]
        reports.append({"feature": feature_dir.name, "ok": ok, "detail": detail})

    return reports
