# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

from __future__ import annotations

import importlib.resources

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
