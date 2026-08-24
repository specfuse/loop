#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Refuse a change that edits an already-published CHANGELOG section (#2727).

Thin git plumbing over `changelog.released_section_drift`, which owns the
rule and is unit-tested without git. This resolves the base revision's
CHANGELOG.md and reports what the comparison finds.

Why this is a diff-time check and not a parse-time one: the drift produces a
perfectly valid Keep-a-Changelog document. Five well-formed entries in the
wrong section parse exactly as cleanly as five in the right one, so no
amount of validating a single file can see it. The error only exists as a
difference between two revisions.

    python3 scripts/check_changelog_append_only.py origin/main

Exits 0 when clean or when the base cannot be resolved (see below), 1 on
findings, 2 on usage error.

**An unresolvable base is not a failure.** A shallow clone, a first commit,
or a base ref that was never fetched all mean "could not look" -- and a
checker that fails closed on those blocks every PR in a fresh clone while
reporting a problem it never actually found. It says so on stderr and exits
0. Conflating "could not look" with "found a problem" is the shape recorded
as `LEARNINGS [FEAT-2026-0072/G1-CLOSE]`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from specfuse.loop.changelog import released_section_drift  # noqa: E402

_CHANGELOG = "CHANGELOG.md"


def base_changelog(ref: str, root: Path | None = None) -> str | None:
    """Return `ref`'s CHANGELOG.md, or None when it cannot be read."""
    root = root or _REPO_ROOT
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{_CHANGELOG}"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(
            "usage: python3 scripts/check_changelog_append_only.py <base-ref>",
            file=sys.stderr,
        )
        return 2

    ref = args[0]
    base = base_changelog(ref)
    if base is None:
        print(
            f"note: could not read {_CHANGELOG} at {ref!r} — skipping the "
            f"append-only check. This is not a finding; fetch the base ref "
            f"(actions/checkout with fetch-depth: 0) to enable it.",
            file=sys.stderr,
        )
        return 0

    head = (_REPO_ROOT / _CHANGELOG).read_text(encoding="utf-8")
    findings = released_section_drift(base, head)
    if not findings:
        print(f"changelog: no published section was edited (base {ref})")
        return 0

    print(
        f"error: {_CHANGELOG} edits an already-published release section.\n"
        f"New entries belong under [Unreleased]; a dated section records "
        f"what a tag actually contains.\n",
        file=sys.stderr,
    )
    for finding in findings:
        print(f"  - {finding}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
