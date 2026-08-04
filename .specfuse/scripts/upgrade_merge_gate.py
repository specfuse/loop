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

import re
import subprocess
import sys
from pathlib import Path

_DETAIL_TAIL_CHARS = 500

# Feature folders are `FEAT-YYYY-NNNN-<slug>`; anything else under
# .specfuse/features/ is incidental and not evidence about conformance (#309).
_FEATURE_DIR_RE = re.compile(r"^FEAT-\d{4}-\d{4}-")


def decide(ci_all_green: bool, feature_reports: list[dict]) -> tuple[str, str]:
    """Return (verdict, reason). verdict is 'merge' or 'halt'.

    Fails safe: an empty `feature_reports` halts rather than merging, since
    absence of evidence is not evidence of conformance.
    """
    if not feature_reports:
        return ("halt", "no feature folders were checked")
    unrunnable = [r for r in feature_reports if r.get("linter_unrunnable")]
    if unrunnable:
        # Not a conformance verdict: the gate never got to ask the question.
        # Reported before the CI check so the reason names the real blocker.
        return ("halt", unrunnable[0].get("detail") or "could not run the linter")
    if not ci_all_green:
        return ("halt", "CI not green")
    failing = [r["feature"] for r in feature_reports if not r.get("ok")]
    if failing:
        return ("halt", f"conformance failed for: {', '.join(failing)}")
    return ("merge", "")


def _lint_command(repo_root: Path) -> tuple[list[str], bool]:
    """Return (argv_prefix, used_shim) for linting a feature folder.

    Two eras of target repo (#309):

    - **pre-package**: the target ships `.specfuse/scripts/lint_plan.py`, and
      that shim is the linter it was scaffolded against. Keep using it, so an
      upgrade does not silently switch a repo to a different linter than the
      one its features were written for.
    - **package-era**: scripts come from the installed `specfuse-loop`, and no
      shim exists in the target. Invoke the module instead.

    Hardcoding the shim path made every folder in a package-era target report
    a FAIL whose `detail` was Python's own "can't open file" message, so
    `decide` returned a **false halt** on a fully conformant repo.
    """
    shim = repo_root / ".specfuse" / "scripts" / "lint_plan.py"
    if shim.is_file():
        return [sys.executable, str(shim)], True
    return [sys.executable, "-m", "specfuse.loop.lint_plan"], False


def _is_feature_dir(path: Path) -> bool:
    """Feature folders are `FEAT-YYYY-NNNN-<slug>`.

    `.specfuse/features/` also picks up incidental directories -- a `.claude`
    dir was linted in the field, reported as a failing "feature", and named in
    the halt reason. A folder that is not a feature is not evidence about
    conformance either way, so it is skipped rather than passed or failed.
    """
    return bool(_FEATURE_DIR_RE.match(path.name))


def _linter_unrunnable(argv_prefix: list[str]) -> str:
    """Return why the linter cannot run at all, or "" when it can.

    Distinguishes "this repo is non-conformant" from "I could not check it"
    (#309). Without this, an interpreter that cannot reach `specfuse.loop`
    makes every feature fail with the same error and `decide` names each
    conformant feature in the halt reason -- exactly how the original bug
    read in the field, just with a different underlying cause.
    """
    try:
        probe = subprocess.run(
            [*argv_prefix, "--help"],
            capture_output=True, text=True, check=False,
        )
    except OSError as exc:
        return f"could not run the plan linter ({argv_prefix[0]}): {exc}"
    if probe.returncode != 0 and "ModuleNotFoundError" in (
        probe.stdout + probe.stderr
    ):
        return (
            "could not run the plan linter: specfuse.loop is not importable "
            f"by {argv_prefix[0]}. Install specfuse-loop into that "
            "interpreter, or run this gate with the one that has it."
        )
    return ""


def collect_reports(repo_root, python: "str | None" = None) -> list[dict]:
    """Run the plan lint once per feature folder under repo_root; report results.

    `python` overrides the interpreter used for the lint subprocess; it exists
    so tests can exercise the unrunnable-linter path without breaking the
    running interpreter.
    """
    repo_root = Path(repo_root)
    features_dir = repo_root / ".specfuse" / "features"

    reports = []
    if not features_dir.is_dir():
        return reports

    argv_prefix, used_shim = _lint_command(repo_root)
    if python:
        argv_prefix = [python, *argv_prefix[1:]]

    unrunnable = _linter_unrunnable(argv_prefix)
    if unrunnable:
        # One report about the gate, not N reports blaming the features.
        return [{"feature": "<lint>", "ok": False, "detail": unrunnable,
                 "used_shim": used_shim, "linter_unrunnable": True}]

    for feature_dir in sorted(
        p for p in features_dir.iterdir() if p.is_dir() and _is_feature_dir(p)
    ):
        result = subprocess.run(
            [*argv_prefix, str(feature_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        ok = result.returncode == 0
        detail = ""
        if not ok:
            output = (result.stdout + result.stderr).strip()
            detail = output[-_DETAIL_TAIL_CHARS:]
        reports.append({
            "feature": feature_dir.name,
            "ok": ok,
            "detail": detail,
            "used_shim": used_shim,
        })

    return reports
