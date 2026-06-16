#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Leak-detection core: structural-regex + gitleaks secret scanner.

Public API:
  scan_text(text, allowlist=DEFAULT_ALLOWLIST) -> list[str]
  scan_staged() -> list[str]

WU-07 wires these into the pre-commit hook, CI runner, and history auditor.
Correlation ID: FEAT-2026-0020/T15
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Structural regexes — generic patterns only, no literal private names.
# ---------------------------------------------------------------------------

# Absolute macOS/Linux user-home paths: /Users/<username>/...
_USER_PATH_RE = re.compile(r"/Users/[^/\s]+/")

# RFC-5321-ish email addresses (broad; intent is to flag unexpected addresses)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Hostnames ending in private-network / internal-only TLDs
_PRIVATE_HOST_RE = re.compile(
    r"\b[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.(?:local|internal|corp|lan|home|intranet|localdomain)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Default allowlist — canonical samples that must never be flagged.
# INIT-2026-0001 is the reference orchestrated-initiative ID per
# .specfuse/rules/correlation-ids.md; it appears in docs and tests legitimately.
# ---------------------------------------------------------------------------

DEFAULT_ALLOWLIST: frozenset[str] = frozenset({"INIT-2026-0001"})

# ---------------------------------------------------------------------------
# Optional literal denylist — loaded from a gitignored file, never inlined.
# Operators place private org names / hostnames in this file; it is never
# committed (added to .gitignore alongside this module).
# ---------------------------------------------------------------------------

_DENYLIST_PATH = Path(__file__).parent / "leak_denylist.txt"


def load_denylist() -> list[str]:
    """Return entries from the gitignored denylist file, or [] if absent."""
    if not _DENYLIST_PATH.exists():
        return []
    entries: list[str] = []
    for line in _DENYLIST_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            entries.append(stripped)
    return entries


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _line_exempt(line: str, allowlist: frozenset[str]) -> bool:
    return any(token in line for token in allowlist)


def _check_patterns(
    text: str,
    allowlist: frozenset[str],
    denylist: list[str],
) -> list[str]:
    hits: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if _line_exempt(line, allowlist):
            continue
        for m in _USER_PATH_RE.finditer(line):
            hits.append(f"line {lineno}: user-path: {m.group()!r}")
        for m in _EMAIL_RE.finditer(line):
            hits.append(f"line {lineno}: email: {m.group()!r}")
        for m in _PRIVATE_HOST_RE.finditer(line):
            hits.append(f"line {lineno}: private-host: {m.group()!r}")
        for entry in denylist:
            if entry.lower() in line.lower():
                hits.append(f"line {lineno}: denylist: {entry!r}")
    return hits


def _check_gitleaks(text: str) -> list[str]:
    """Run gitleaks over *text*; return list of RuleID hit strings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "content.txt").write_text(text, encoding="utf-8")
        proc = subprocess.run(  # nosec B603 – list args, no shell expansion; tmpdir is process-local
            [
                "gitleaks",
                "detect",
                "--source",
                tmpdir,
                "--no-git",
                "--report-format",
                "json",
                "--report-path",
                "-",
                "--exit-code",
                "1",
                "--redact",
            ],
            capture_output=True,
            text=True,
        )
    if proc.returncode == 0:
        return []
    try:
        findings = json.loads(proc.stdout)
        if isinstance(findings, list):
            return [f"secret:{f.get('RuleID', 'unknown')}" for f in findings]
    except (json.JSONDecodeError, AttributeError):
        pass
    return ["gitleaks:secrets-detected"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_text(
    text: str,
    allowlist: frozenset[str] = DEFAULT_ALLOWLIST,
) -> list[str]:
    """Scan *text* for leaks. Returns list of finding descriptions; [] = clean."""
    denylist = load_denylist()
    hits = _check_patterns(text, allowlist, denylist)
    hits.extend(_check_gitleaks(text))
    return hits


def _get_staged_diff() -> str:
    proc = subprocess.run(  # nosec B603 – list args, no shell
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
    )
    return proc.stdout if proc.returncode == 0 else ""


def scan_staged() -> list[str]:
    """Scan the current staged diff for leaks."""
    return scan_text(_get_staged_diff())
