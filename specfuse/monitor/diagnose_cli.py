# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The headless diagnosis entry point (FEAT-2026-0041/T03).

A second caller of `specfuse.monitor.diagnosis.render`, so a finding can be
diagnosed without an interactive session. This module produces a comment
body; it does not post one, and shells out to nothing and reaches no
network of its own — posting is the caller's job, same as it is the
interactive skill's job.

Rendering is delegated to `diagnosis.py` exclusively: this module holds no
literal marker string or section-heading template of its own. Any drift
between the headless body and the interactive skill's body would mean two
entry points disagree on format, which is the exact failure this module
exists to avoid.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from specfuse.monitor.diagnosis import Diagnosis, FIX_SCOPES, render

_REQUIRED_FIELDS = ("root_cause", "evidence", "candidate_fix", "confidence", "fix_scope")


class AnalysisParseError(ValueError):
    """Raised when an analysis-step result cannot be turned into a `Diagnosis`.

    Covers both "not JSON at all" and "JSON, but missing or malformed
    fields" — including an absent or out-of-vocabulary `fix_scope`, which is
    rejected here rather than defaulted. A defaulted `fix_scope` would
    silently route real work past FEAT-2026-0042's gate.
    """


def parse_analysis(raw: str) -> Diagnosis:
    """Parse an analysis-step result (JSON text) into a `Diagnosis`.

    Raises `AnalysisParseError` — never returns a `Diagnosis` with an empty
    or defaulted field — on invalid JSON, a non-object payload, a missing
    required field, or a `fix_scope` outside `FIX_SCOPES`.
    """
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AnalysisParseError(f"analysis result is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise AnalysisParseError(
            f"analysis result must be a JSON object, got {type(data).__name__}"
        )

    missing = [field for field in _REQUIRED_FIELDS if field not in data]
    if missing:
        raise AnalysisParseError(
            f"analysis result missing required field(s): {missing!r}"
        )

    fix_scope = data["fix_scope"]
    if fix_scope not in FIX_SCOPES:
        raise AnalysisParseError(
            f"fix_scope must be one of {FIX_SCOPES!r}, got {fix_scope!r}"
        )

    try:
        confidence = float(data["confidence"])
    except (TypeError, ValueError) as exc:
        raise AnalysisParseError(
            f"confidence is not a number: {data['confidence']!r}"
        ) from exc

    try:
        return Diagnosis(
            root_cause=str(data["root_cause"]),
            evidence=str(data["evidence"]),
            candidate_fix=str(data["candidate_fix"]),
            confidence=confidence,
            fix_scope=fix_scope,
        )
    except ValueError as exc:
        raise AnalysisParseError(str(exc)) from exc


def render_headless(raw: str) -> str:
    """Parse `raw` analysis JSON and render it via `diagnosis.render`."""
    return render(parse_analysis(raw))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Render a diagnosis comment body from an analysis-step JSON "
            "result. Prints the rendered body to stdout; does not post it."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to a JSON file holding the analysis result. Reads stdin if omitted.",
    )
    args = parser.parse_args(argv)

    raw = sys.stdin.read() if args.input is None else _read_file(args.input)

    try:
        body = render_headless(raw)
    except AnalysisParseError as exc:
        print(f"diagnose_cli: {exc}", file=sys.stderr)
        return 1

    print(body)
    return 0


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


if __name__ == "__main__":
    sys.exit(main())
