#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Project layout resolver — FEAT-2026-0224 (project-configurable layout).

Reads an optional `.specfuse/layout.yml` and answers `layout get <key>` for
`decisions.style`, `decisions.location`, `decisions.link` and `ids.key`.

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
import posixpath
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from specfuse.loop import _miniyaml
from specfuse.loop.ids import KEY_PATTERN, KEY_RE

LAYOUT_RELPATH = Path(".specfuse") / "layout.yml"

DEFAULT_STYLE = "adr"
_STYLE_DEFAULTS = {
    "adr": ("docs/adr", "{path}"),
    "entries": ("docs/decisions", "{location}/decisions.md#{id}"),
}
_FALLBACK_DEFAULTS = _STYLE_DEFAULTS["adr"]

KEYS = ("decisions.style", "decisions.location", "decisions.link", "ids.key")

VALID_STYLES = ("adr", "entries")
LINK_PLACEHOLDERS = ("location", "path", "id", "domain")
KNOWN_TOP_LEVEL = ("decisions", "ids")
_PLACEHOLDER_RE = re.compile(r"\{([^{}]*)\}")
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True)
class Decisions:
    style: str
    location: str
    link: str


@dataclass(frozen=True)
class Ids:
    key: Optional[str] = None


@dataclass(frozen=True)
class Layout:
    decisions: Decisions
    ids: Ids = Ids()


def _normalise(location: str) -> str:
    return location.rstrip("/") or location


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
        location=default_location if location is None else _normalise(str(location)),
        link=default_link if link is None else str(link),
    )


def _read(path: Path):
    """Parsed layout file, or None when absent or unparseable (validate reports)."""
    if not path.is_file():
        return None
    try:
        return _miniyaml.parse(path.read_text(encoding="utf-8"))
    except _miniyaml.MiniYAMLError:
        return None


def load(repo_root) -> Layout:
    path = Path(repo_root) / LAYOUT_RELPATH
    data = _read(path)
    block = data.get("decisions") if isinstance(data, dict) else None
    ids_block = data.get("ids") if isinstance(data, dict) else None
    key = ids_block.get("key") if isinstance(ids_block, dict) else None
    return Layout(
        decisions=_resolve_decisions(block if isinstance(block, dict) else None),
        ids=Ids(key=None if key is None else str(key)),
    )


def _line_of(text: str, key: str) -> int:
    for number, line in enumerate(text.splitlines(), start=1):
        if re.match(r"\s*" + re.escape(key) + r"\s*:", line):
            return number
    return 1


def validate(repo_root) -> list:
    """Findings for a malformed layout file; `[]` when absent or valid.

    `Finding` and the severities come from `lint_roadmap`; imported lazily so
    `lint_roadmap` can import this module without a cycle.
    """
    from specfuse.loop.lint_roadmap import SEVERITY_ERROR, SEVERITY_WARN, Finding

    root = Path(repo_root)
    path = root / LAYOUT_RELPATH
    if not path.is_file():
        return []
    rel = LAYOUT_RELPATH.as_posix()
    text = path.read_text(encoding="utf-8")
    findings = []

    def add(severity, key, message):
        findings.append(Finding(severity, rel, _line_of(text, key), message))

    try:
        data = _miniyaml.parse(text)
    except _miniyaml.MiniYAMLError as exc:
        add(SEVERITY_ERROR, "decisions", f"layout.yml could not be parsed: {exc}")
        return findings
    if not isinstance(data, dict):
        if data is not None:
            add(SEVERITY_ERROR, "decisions", "layout.yml must be a mapping")
        return findings

    for key in data:
        if key == "paths":
            add(
                SEVERITY_WARN,
                key,
                "`paths:` is not supported yet; the authoring follow-up to "
                "FEAT-2026-0224 adds it",
            )
        elif key not in KNOWN_TOP_LEVEL:
            add(SEVERITY_WARN, key, f"unknown top-level key {key!r} in layout.yml")

    ids_block = data.get("ids")
    if isinstance(ids_block, dict) and ids_block.get("key") is not None:
        key = str(ids_block["key"])
        if not KEY_RE.match(key):
            add(
                SEVERITY_ERROR,
                "key",
                f"ids.key {key!r} is invalid; must match {KEY_PATTERN} "
                "(2-6 characters, upper-case letters and digits, starting with a letter)",
            )

    block = data.get("decisions")
    if not isinstance(block, dict):
        return findings

    style = block.get("style")
    if style is not None and str(style) not in VALID_STYLES:
        add(
            SEVERITY_ERROR,
            "style",
            f"decisions.style {str(style)!r} is invalid; must be one of "
            f"{VALID_STYLES[0]!r} or {VALID_STYLES[1]!r}",
        )

    location = block.get("location")
    if location is not None:
        loc = str(location)
        if loc.startswith("/"):
            add(SEVERITY_ERROR, "location", f"decisions.location {loc!r} must not be absolute")
        if _DRIVE_RE.match(loc):
            add(
                SEVERITY_ERROR,
                "location",
                f"decisions.location {loc!r} must not start with a Windows drive",
            )
        if "\\" in loc:
            add(
                SEVERITY_ERROR,
                "location",
                f"decisions.location {loc!r} must not contain a backslash; use '/'",
            )
        if ".." in re.split(r"[\\/]", loc):
            add(
                SEVERITY_ERROR,
                "location",
                f"decisions.location {loc!r} must not contain a '..' segment",
            )
        if not findings_for_location(findings):
            try:
                resolved = (root / loc).resolve()
                inside = resolved.is_relative_to(root.resolve())
            except (OSError, RuntimeError, ValueError):
                inside = True
            if not inside:
                add(
                    SEVERITY_ERROR,
                    "location",
                    f"decisions.location {loc!r} resolves outside the repo root",
                )

    link = block.get("link")
    if link is not None:
        for name in _PLACEHOLDER_RE.findall(str(link)):
            if name not in LINK_PLACEHOLDERS:
                add(
                    SEVERITY_ERROR,
                    "link",
                    f"decisions.link placeholder '{{{name}}}' is not allowed; "
                    "use {location}, {path}, {id} or {domain}",
                )
    return findings


def findings_for_location(findings) -> list:
    return [f for f in findings if "decisions.location" in f.message]


def get(layout: Layout, key: str) -> str:
    if key not in KEYS:
        raise KeyError(key)
    if key == "ids.key":
        return layout.ids.key or ""
    return getattr(layout.decisions, key.split(".", 1)[1])


def split_link(href: str):
    """(path, fragment | None, is_url) — the one parser of a decision href."""
    if re.match(r"^https?://", href):
        return href, None, True
    path, sep, fragment = href.partition("#")
    return path, (fragment if sep else None), False


def render_link(layout: Layout, *, target: str, label: str, from_dir: str, domain=None) -> str:
    """`[label](href)` for a decision; a repo-relative href is made relative to `from_dir`."""
    supplied = {"location": layout.decisions.location}
    supplied["path" if layout.decisions.style == "adr" else "id"] = target
    if domain is not None:
        supplied["domain"] = domain

    def fill(match):
        name = match.group(1)
        if name not in supplied:
            raise ValueError(f"link template needs {{{name}}} but the call does not supply it")
        return supplied[name]

    href = _PLACEHOLDER_RE.sub(fill, layout.decisions.link)
    path, fragment, is_url = split_link(href)
    if not is_url and path:
        path = posixpath.relpath(path, posixpath.normpath(from_dir or "."))
        href = path if fragment is None else f"{path}#{fragment}"
    return f"[{label}]({href})"


_REGION_RE = re.compile(
    r"<!-- layout:decisions-example -->\n(.*?)<!-- /layout:decisions-example -->\n", re.DOTALL
)


def _entries_example(layout: Layout) -> str:
    link = render_link(
        layout, target="D-0007", label="D-0007: event-schema versioning", from_dir=".specfuse"
    )
    return (
        f"**Blocked by.** {link} — awaiting approval; "
        "[FEAT-2026-0011](#feat-2026-0011) — scoring data must land first.\n\n"
        "Each blocker is a Markdown link: a decision entry points at its heading anchor "
        "in the decisions file (kept under\n"
        f"`{layout.decisions.location}/` per `layout.yml`, so from `.specfuse/roadmap.md` the link is\n"
        "relative to `.specfuse/`); a feature dependency points at the blocking\n"
        "feature's roadmap anchor (`#feat-yyyy-nnnn`). When every blocker clears, a human\n"
        "flips `blocked` → `active` (or `planned`) and removes the `**Blocked by.**` block.\n"
    )


def render_roadmap_template(text: str, layout: Layout) -> str:
    """Roadmap template with its decisions-example region rendered for `layout`.

    The region markers never reach the output; with the default style the
    region body is kept verbatim, so a no-layout seed is byte-identical to
    the marker-free template.
    """
    if layout.decisions.style == "entries":
        return _REGION_RE.sub(lambda m: _entries_example(layout), text)
    return _REGION_RE.sub(lambda m: m.group(1), text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="specfuse.loop.layout", description="Resolve the project's layout.yml."
    )
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    getp = sub.add_parser("get", help="print the resolved value of one key")
    getp.add_argument("key")
    sub.add_parser("check", help="report malformed layout; exit 1 on any error")
    linkp = sub.add_parser("link", help="print the rendered decision link")
    linkp.add_argument("--target", required=True)
    linkp.add_argument("--label", required=True)
    linkp.add_argument("--from", dest="from_dir", default=".specfuse")
    linkp.add_argument("--domain", default=None)
    args = parser.parse_args(argv)

    if args.command == "check":
        from specfuse.loop.lint_roadmap import SEVERITY_ERROR

        findings = validate(args.repo)
        for f in findings:
            print(f"{f.severity.upper()} {f.file}:{f.line}: {f.message}")
        return 1 if any(f.severity == SEVERITY_ERROR for f in findings) else 0

    layout = load(args.repo)
    if args.command == "link":
        try:
            print(
                render_link(
                    layout,
                    target=args.target,
                    label=args.label,
                    from_dir=args.from_dir,
                    domain=args.domain,
                )
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        return 0
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
