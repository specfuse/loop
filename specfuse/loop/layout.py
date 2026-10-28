#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Project layout resolver — FEAT-2026-0224 (project-configurable layout).

Reads an optional `.specfuse/layout.yml` and answers `layout get <key>` for
`decisions.style`, `decisions.location` and `decisions.link`.

Contract: no file (or no `decisions:` block) means today's behaviour — style
`adr`, location `docs/adr`, link `{path}`. An `entries` style with `location`
or `link` omitted defaults to `docs/decisions` and
`{location}/decisions.md#{id}`.

Walking-skeleton scope (T01): validation (T02) and link rendering (T03) are
not built yet; any string is accepted. Standalone: must not import the driver.

    python3 -m specfuse.loop.layout [--repo DIR] get <key>
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from specfuse.loop import _miniyaml

LAYOUT_RELPATH = Path(".specfuse") / "layout.yml"

DEFAULT_STYLE = "adr"
_STYLE_DEFAULTS = {
    "adr": ("docs/adr", "{path}"),
    "entries": ("docs/decisions", "{location}/decisions.md#{id}"),
}
_FALLBACK_DEFAULTS = _STYLE_DEFAULTS["adr"]

KEYS = ("decisions.style", "decisions.location", "decisions.link")


@dataclass(frozen=True)
class Decisions:
    style: str
    location: str
    link: str


@dataclass(frozen=True)
class Layout:
    decisions: Decisions


def _resolve_decisions(block: Optional[dict]) -> Decisions:
    block = block or {}
    style = block.get("style")
    if style is None:
        style = DEFAULT_STYLE
    style = str(style)
    default_location, default_link = _STYLE_DEFAULTS.get(style, _FALLBACK_DEFAULTS)
    location = block.get("location")
    link = block.get("link")
    return Decisions(
        style=style,
        location=default_location if location is None else str(location),
        link=default_link if link is None else str(link),
    )


def load(repo_root) -> Layout:
    path = Path(repo_root) / LAYOUT_RELPATH
    data = None
    if path.is_file():
        data = _miniyaml.parse(path.read_text(encoding="utf-8"))
    block = data.get("decisions") if isinstance(data, dict) else None
    return Layout(decisions=_resolve_decisions(block if isinstance(block, dict) else None))


def get(layout: Layout, key: str) -> str:
    if key not in KEYS:
        raise KeyError(key)
    return getattr(layout.decisions, key.split(".", 1)[1])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="specfuse.loop.layout", description="Resolve the project's layout.yml."
    )
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    getp = sub.add_parser("get", help="print the resolved value of one key")
    getp.add_argument("key")
    args = parser.parse_args(argv)

    layout = load(args.repo)
    try:
        value = get(layout, args.key)
    except KeyError:
        print(
            f"unknown layout key {args.key!r}; valid keys: {', '.join(KEYS)}",
            file=sys.stderr,
        )
        return 2
    print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
