# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

from __future__ import annotations

import importlib.resources
from pathlib import Path

try:
    from importlib.resources.abc import Traversable  # Python 3.11+
except ImportError:
    from importlib.abc import Traversable  # Python 3.10

_DATA: Traversable = importlib.resources.files("specfuse.loop").joinpath("data")


def _walk(node: Traversable, prefix: str) -> list[tuple[str, bytes]]:
    results: list[tuple[str, bytes]] = []
    for child in node.iterdir():
        rel = f"{prefix}/{child.name}" if prefix else child.name
        if child.is_dir():
            results.extend(_walk(child, rel))
        else:
            results.append((rel, child.read_bytes()))
    return results


def iter_scaffold_files() -> list[tuple[str, bytes]]:
    """Return every seed file as (relpath, content) pairs."""
    return _walk(_DATA, "")


def scaffold_version() -> str:
    """Return the packaged VERSION string."""
    return _DATA.joinpath("VERSION").read_text(encoding="utf-8").strip()


def read_scaffold(relpath: str) -> bytes:
    """Return content of one seed file by relpath (e.g. 'templates/PLAN.template.md')."""
    node: Traversable = _DATA
    for part in relpath.split("/"):
        node = node.joinpath(part)
    return node.read_bytes()


class ScaffoldExistsError(Exception):
    """Raised by init_specfuse when .specfuse/ already exists in the target."""


# Seed relpaths that map to a different target name inside .specfuse/
_SEED_RENAME: dict[str, str] = {
    "roadmap.template.md": "roadmap.md",
    "LEARNINGS.template.md": "LEARNINGS.md",
    "verification.yml.example": "verification.yml",
}

# Seed files handled by other work units (T05); skip during init
_SKIP_SEEDS: frozenset[str] = frozenset({"gitignore.snippet"})


def init_specfuse(
    target: str | Path, *, ci_check: str | None = None
) -> list[str]:
    """Write a fresh .specfuse/ tree in *target* from the packaged seed.

    Returns the sorted list of relpaths written (relative to .specfuse/).
    Raises ScaffoldExistsError if .specfuse/ already exists; nothing is written.
    ci_check is accepted for API compatibility but wiring is deferred to T06.
    """
    target_path = Path(target)
    specfuse_dir = target_path / ".specfuse"

    if specfuse_dir.exists():
        raise ScaffoldExistsError(
            f"{specfuse_dir} already exists; run `specfuse upgrade` to update."
        )

    written: list[str] = []

    for relpath, content in iter_scaffold_files():
        if relpath in _SKIP_SEEDS:
            continue
        dest_rel = _SEED_RENAME.get(relpath, relpath)
        dest = specfuse_dir / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        written.append(dest_rel)

    features_keep = specfuse_dir / "features" / ".gitkeep"
    features_keep.parent.mkdir(parents=True, exist_ok=True)
    features_keep.write_bytes(b"")
    written.append("features/.gitkeep")

    return sorted(written)
