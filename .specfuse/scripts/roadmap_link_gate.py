#!/usr/bin/env python3
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Command-line entry point for `lint_roadmap` (FEAT-2026-0034/T02).

T01's `specfuse.loop.lint_roadmap.lint_roadmap` owns the four link-graph
invariants and returns `Finding` objects; this script owns exit codes and
output shape only — it does not re-implement any check.

Severity decides the exit code. `SEVERITY_ERROR` findings (a dead ref, a
missing anchor, a `blocked` row with no resolvable `**Blocked by.**` link)
fail the gate. `SEVERITY_WARN` findings (a `**Blocked by.**` block on a
non-`blocked` row, an orphan detail section nothing links to) print but do
NOT fail the gate — they flag tidiness, not a broken link graph, and a gate
that goes red for tidiness gets ignored, which is how this rot survived long
enough to need a linter. Every finding, of either severity, is printed with
its file, line, and mechanical fix so the operator never has to re-derive
what the linter already knew.

Exit codes:
    0 — no ERROR finding (WARN findings, if any, are printed but do not fail)
    1 — at least one ERROR finding (all findings printed; errors on stderr)
"""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from specfuse.loop.lint_roadmap import SEVERITY_ERROR, lint_roadmap  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    return roadmap_link_gate_main(REPO_ROOT)


def roadmap_link_gate_main(repo_root: Path) -> int:
    findings = lint_roadmap(repo_root)
    errors = [f for f in findings if f.severity == SEVERITY_ERROR]
    warns = [f for f in findings if f.severity != SEVERITY_ERROR]

    for f in warns:
        sys.stdout.write(f"WARN: {f.file}:{f.line}: {f.message}\n")
    for f in errors:
        sys.stderr.write(f"ERROR: {f.file}:{f.line}: {f.message}\n")

    sys.stdout.write(
        "roadmap link lint: checked roadmap.md + roadmap-archive.md link graph "
        f"— {len(errors)} error(s), {len(warns)} warning(s)\n"
    )

    if errors:
        sys.stderr.write(f"\n{len(errors)} roadmap-link error(s).\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
