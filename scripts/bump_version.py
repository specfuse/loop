#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Bump every package-version source in lockstep (specfuse-loop).

The package version lives in FOUR places that must always agree, or a release
half-bumps and the tag/version-agreement check (or `pip install`) breaks:

  1. pyproject.toml          [project] version  — the PyPI package version
  2. specfuse/loop/loop.py   DRIVER_VERSION      — stamped into events
  3. .specfuse/VERSION       canonical scaffold version (self-provision source)
  4. specfuse/loop/data/VERSION  the synced pip-shipped scaffold seed (== #3)

This sets all four. It does NOT touch `MIN_SCAFFOLD_VERSION` (the
oldest-driveable-scaffold floor) — bump that by hand, only on a scaffold-format
break. `tests/test_version_consistency.py` enforces the four stay equal, so a
forgotten source fails CI at PR time, not at release tag time.

Usage:
    python3 scripts/bump_version.py 0.3.1
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-.][0-9A-Za-z.]+)?$")


def set_version(root: Path, version: str) -> list[str]:
    """Set the package version across all four sources under *root*.

    Returns the list of repo-relative paths actually changed. Raises
    ValueError if a source file is missing its expected version marker.
    """
    changed: list[str] = []

    pyproject = root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    new, n = re.subn(
        r'(?m)^(version\s*=\s*)"[^"]+"', rf'\g<1>"{version}"', text, count=1
    )
    if n != 1:
        raise ValueError(f"{pyproject}: no `version = \"...\"` line found")
    if new != text:
        pyproject.write_text(new, encoding="utf-8")
        changed.append("pyproject.toml")

    loop_py = root / "specfuse" / "loop" / "loop.py"
    text = loop_py.read_text(encoding="utf-8")
    new, n = re.subn(
        r'(?m)^(DRIVER_VERSION\s*=\s*)"[^"]+"', rf'\g<1>"{version}"', text, count=1
    )
    if n != 1:
        raise ValueError(f"{loop_py}: no `DRIVER_VERSION = \"...\"` line found")
    if new != text:
        loop_py.write_text(new, encoding="utf-8")
        changed.append("specfuse/loop/loop.py")

    for rel in (".specfuse/VERSION", "specfuse/loop/data/VERSION"):
        vf = root / rel
        if vf.read_text(encoding="utf-8").strip() != version:
            vf.write_text(version + "\n", encoding="utf-8")
            changed.append(rel)

    return changed


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or not _SEMVER.match(args[0]):
        print("usage: python3 scripts/bump_version.py <X.Y.Z>", file=sys.stderr)
        return 2
    version = args[0]
    root = Path(__file__).resolve().parent.parent
    changed = set_version(root, version)
    if changed:
        print(f"bumped to {version}:")
        for p in changed:
            print(f"  {p}")
    else:
        print(f"already at {version} — nothing to change")
    print(
        "\nNote: MIN_SCAFFOLD_VERSION is intentionally untouched. "
        "Bump it by hand only on a scaffold-format break."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
