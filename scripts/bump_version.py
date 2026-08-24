#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Bump every package-version source in lockstep and stamp CHANGELOG.md
(specfuse-loop). FEAT-2026-0064/T03 wires the changelog step in; the four
version sources were the whole story before that.

The package version lives in FOUR places that must always agree, or a release
half-bumps and the tag/version-agreement check (or `pip install`) breaks:

  1. pyproject.toml          [project] version  — the PyPI package version
  2. specfuse/loop/loop.py   DRIVER_VERSION      — stamped into events
  3. .specfuse/VERSION       canonical scaffold version (self-provision source)
  4. specfuse/loop/data/VERSION  the synced pip-shipped scaffold seed (== #3)

That list — and the `v*` git-tag convention — are THIS repository's values,
read from `.specfuse/release.yml` with these same values as the fallback
default (see `load_release_config`); a target project installing the
scaffold supplies its own file to set different ones.

`set_version` alone sets the four sources; it does NOT touch
`MIN_SCAFFOLD_VERSION` (the oldest-driveable-scaffold floor) — bump that by
hand, only on a scaffold-format break. `tests/test_version_consistency.py`
enforces the four stay equal, so a forgotten source fails CI at PR time, not
at release tag time.

`release` is the atomic entry point `main()` drives: it sets the four
sources AND stamps CHANGELOG.md's `Unreleased` section in one call, so a
version set in four files and absent from the changelog cannot happen.

The umbrella version in the heading is **resolved from PyPI, not asserted**
(#2757). It used to be a required hand-passed argument, justified by "a driver
version nobody can install is not a release" — true before umbrella 0.11.0,
when the umbrella floor was the upgrade lever. Since components became hard
dependencies, `pipx upgrade specfuse` re-resolves on its own and the driver
reaches users whether or not the umbrella moves; the coordinate became a
record of what was current, and a record nobody checked. It drifted:
`0.13.0+umbrella.0.13.0` and `0.14.0+umbrella.0.14.0` both name umbrella
versions that were never published, because the old check tested the argument
for non-emptiness and nothing else. `--umbrella-version` is now optional — it
pins, and is validated against the index; omitted, the latest release is used.

Usage:
    python3 scripts/bump_version.py 0.3.1
    python3 scripts/bump_version.py 0.3.1 --umbrella-version 1.4.0
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path
from typing import Callable

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from specfuse.loop import _miniyaml  # noqa: E402
from specfuse.loop import changelog as _changelog  # noqa: E402

_SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-.][0-9A-Za-z.]+)?$")

_DEFAULT_TAG_PREFIX = "v"
_DEFAULT_VERSION_SOURCES = [
    {"path": "pyproject.toml", "kind": "pyproject_version"},
    {"path": "specfuse/loop/loop.py", "kind": "driver_version_constant"},
    {"path": ".specfuse/VERSION", "kind": "plain_version_file"},
    {"path": "specfuse/loop/data/VERSION", "kind": "plain_version_file"},
]


#: Where the umbrella's released versions are read from (#2757). The JSON API
#: rather than the simple index: it is one request and already parsed, and the
#: simple index's minutes-long lag behind it is a hazard only for *resolving a
#: just-published* version, which is never what this does.
UMBRELLA_PACKAGE = "specfuse"
_UMBRELLA_JSON_URL = f"https://pypi.org/pypi/{UMBRELLA_PACKAGE}/json"

#: Seconds. A release must not hang on a slow index; an unreachable one is a
#: reported condition, not a wait.
_UMBRELLA_FETCH_TIMEOUT = 10


class UmbrellaUnreachable(Exception):
    """The index could not be consulted. Distinct from "the version is not
    there" -- one means we could not look, the other means we looked and it
    is absent, and conflating them is how a check reports a wrong answer
    instead of no answer (`LEARNINGS [FEAT-2026-0072/G1-CLOSE]`)."""


def fetch_umbrella_versions(url: str = _UMBRELLA_JSON_URL) -> tuple:
    """Return every released umbrella version, newest last.

    Raises `UmbrellaUnreachable` on any network or parse failure -- never
    returns an empty tuple to mean "could not look", because the caller
    treats emptiness as "no such release" and would reject a perfectly
    valid version on a transient outage.
    """
    try:
        with urllib.request.urlopen(url, timeout=_UMBRELLA_FETCH_TIMEOUT) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise UmbrellaUnreachable(str(exc)) from exc

    releases = payload.get("releases")
    if not isinstance(releases, dict) or not releases:
        raise UmbrellaUnreachable(f"{url}: no releases in payload")

    def key(v: str):
        try:
            return tuple(int(p) for p in v.split("."))
        except ValueError:
            return (0,)

    return tuple(sorted((v for v in releases if _SEMVER.match(v)), key=key))


def resolve_umbrella_version(
    requested: str | None,
    *,
    fetch: Callable = fetch_umbrella_versions,
) -> tuple:
    """Resolve the umbrella coordinate for the changelog heading (#2757).

    Returns `(version, verified)`. `verified` is False only when the index
    could not be consulted and the caller supplied a value to fall back on.

    The heading pairs driver and umbrella (`X.Y.Z+umbrella.A.B.C`), and for
    ten releases the pair was real. It stopped being real at 0.13.0 and
    nothing noticed, because `--umbrella-version` was checked for
    non-emptiness and never against anything that exists. Two headings now
    name an umbrella version that was never published.

    So: resolve from the index by default, and validate an explicitly passed
    one. The old required-argument rationale ("a driver version nobody can
    install is not a release") described the pre-0.11.0 world where the
    umbrella floor gated reach; since components became hard dependencies,
    `pipx upgrade specfuse` re-resolves on its own and the driver reaches
    users whether or not the umbrella moves.

    An unreachable index does NOT block a release. It downgrades to the
    passed-in value, flagged unverified, because refusing to cut a release
    over a documentation field would be a worse failure than the one this
    fixes. With no value to fall back on there is nothing to write, and that
    does raise.
    """
    try:
        released = fetch()
    except UmbrellaUnreachable:
        if requested:
            return (requested, False)
        raise

    if requested is None:
        return (released[-1], True)

    if requested not in released:
        raise ValueError(
            f"umbrella version {requested!r} has never been released — "
            f"the changelog heading would name a version nobody can install. "
            f"Released: {', '.join(released[-5:])}. "
            f"Omit --umbrella-version to use the latest ({released[-1]})."
        )
    return (requested, True)


@dataclass
class ReleaseConfig:
    tag_prefix: str = _DEFAULT_TAG_PREFIX
    version_sources: list[dict] = field(
        default_factory=lambda: [dict(s) for s in _DEFAULT_VERSION_SOURCES]
    )


def load_release_config(root: Path) -> ReleaseConfig:
    """Read `.specfuse/release.yml`; fall back to this repo's defaults.

    A target project overrides `tag_prefix` and/or `version_sources` by
    shipping its own `.specfuse/release.yml` — both are configuration, not
    hardcoded to this repository's `v*` tag convention or four-file layout.
    """
    config_path = root / ".specfuse" / "release.yml"
    if not config_path.exists():
        return ReleaseConfig()
    data = _miniyaml.parse(config_path.read_text(encoding="utf-8")) or {}
    tag_prefix = data.get("tag_prefix", _DEFAULT_TAG_PREFIX)
    version_sources = data.get("version_sources")
    if version_sources is None:
        version_sources = [dict(s) for s in _DEFAULT_VERSION_SOURCES]
    return ReleaseConfig(tag_prefix=tag_prefix, version_sources=version_sources)


def set_version(
    root: Path, version: str, config: ReleaseConfig | None = None
) -> list[str]:
    """Set the package version across the configured sources under *root*.

    Returns the list of repo-relative paths actually changed. Raises
    ValueError if a source file is missing its expected version marker, or
    if a source names an unrecognised `kind`.
    """
    if config is None:
        config = ReleaseConfig()
    changed: list[str] = []

    for source in config.version_sources:
        rel = source["path"]
        kind = source["kind"]
        path = root / rel

        if kind == "pyproject_version":
            text = path.read_text(encoding="utf-8")
            new, n = re.subn(
                r'(?m)^(version\s*=\s*)"[^"]+"', rf'\g<1>"{version}"', text, count=1
            )
            if n != 1:
                raise ValueError(f"{path}: no `version = \"...\"` line found")
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed.append(rel)

        elif kind == "driver_version_constant":
            text = path.read_text(encoding="utf-8")
            new, n = re.subn(
                r'(?m)^(DRIVER_VERSION\s*=\s*)"[^"]+"',
                rf'\g<1>"{version}"',
                text,
                count=1,
            )
            if n != 1:
                raise ValueError(f"{path}: no `DRIVER_VERSION = \"...\"` line found")
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed.append(rel)

        elif kind == "plain_version_file":
            if path.read_text(encoding="utf-8").strip() != version:
                path.write_text(version + "\n", encoding="utf-8")
                changed.append(rel)

        else:
            raise ValueError(f"{path}: unrecognised version-source kind {kind!r}")

    return changed


def release(
    root: Path,
    version: str,
    umbrella_version: str,
    *,
    date: str | None = None,
    config: ReleaseConfig | None = None,
) -> list[str]:
    """Set every configured version source and stamp CHANGELOG.md, atomically.

    `umbrella_version` is required and checked, and the changelog stamp is
    computed, before any file is written — so a rejected stamp (missing
    umbrella version, or a double-stamp of an already-released version)
    leaves the tree untouched rather than half-bumped.
    """
    if not umbrella_version:
        raise ValueError(
            "umbrella_version is required — resolve it with "
            "resolve_umbrella_version() before calling release()"
        )
    if config is None:
        config = load_release_config(root)
    if date is None:
        date = _date.today().isoformat()

    changelog_path = root / "CHANGELOG.md"
    stamped = _changelog.stamp_release(
        changelog_path.read_text(encoding="utf-8"),
        version=version,
        date=date,
        umbrella_version=umbrella_version,
    )

    changed = set_version(root, version, config)
    changelog_path.write_text(stamped, encoding="utf-8")
    changed.append("CHANGELOG.md")
    return changed


def main(argv: list[str] | None = None, *, fetch: Callable = fetch_umbrella_versions) -> int:
    """`fetch` is injectable so tests never reach PyPI (#2757).

    Resolution made this entry point do network I/O for the first time. Without
    a seam, every existing test that drives `main()` would silently acquire a
    live dependency on the index — slow, offline-fragile, and answering
    differently whenever the umbrella releases.
    """
    args = sys.argv[1:] if argv is None else argv

    umbrella_version: str | None = None
    date_arg: str | None = None
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--umbrella-version":
            if i + 1 >= len(args):
                print("--umbrella-version requires a value", file=sys.stderr)
                return 2
            umbrella_version = args[i + 1]
            i += 2
            continue
        if a == "--date":
            if i + 1 >= len(args):
                print("--date requires a value", file=sys.stderr)
                return 2
            date_arg = args[i + 1]
            i += 2
            continue
        positional.append(a)
        i += 1

    if len(positional) != 1 or not _SEMVER.match(positional[0]):
        print(
            "usage: python3 scripts/bump_version.py <X.Y.Z> "
            "[--umbrella-version <A.B.C>] [--date YYYY-MM-DD]",
            file=sys.stderr,
        )
        return 2
    version = positional[0]

    # Resolved from the index, not asserted by hand (#2757).
    try:
        umbrella_version, verified = resolve_umbrella_version(
            umbrella_version, fetch=fetch)
    except UmbrellaUnreachable as exc:
        print(
            f"error: could not read {UMBRELLA_PACKAGE}'s released versions "
            f"({exc}). Pass --umbrella-version <A.B.C> to proceed without "
            f"the index; it will be recorded unverified.",
            file=sys.stderr,
        )
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not verified:
        print(
            f"WARNING: could not reach the index; recording umbrella "
            f"{umbrella_version} unverified. Confirm it exists before tagging.",
            file=sys.stderr,
        )

    try:
        changed = release(_REPO_ROOT, version, umbrella_version, date=date_arg)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if changed:
        print(f"bumped to {version} (umbrella {umbrella_version}):")
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
