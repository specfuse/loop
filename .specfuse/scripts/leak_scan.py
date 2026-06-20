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

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Structural regexes — generic patterns only, no literal private names.
# ---------------------------------------------------------------------------

# Absolute macOS/Linux user-home paths: /Users/<username>/...
_USER_PATH_RE = re.compile(r"/Users/[^/\s]+/")

# RFC-5321-ish email addresses (broad; intent is to flag unexpected addresses)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Hostnames ending in private-network / internal-only TLDs.
# NOTE: `home` is intentionally EXCLUDED — it was never a ratified private TLD, and
# `.home` collides with the ubiquitous attribute/method suffix (`Path.home`, `x.home()`),
# which caused false positives that rejected squashes and then self-poisoned via the
# captured-error replay into events.jsonl (see #73). The retained TLDs are the real
# reserved/internal ones.
_PRIVATE_HOST_RE = re.compile(
    r"\b[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.(?:local|internal|corp|lan|intranet|localdomain)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Default allowlist — canonical samples that must never be flagged.
# INIT-2026-0001 is the reference orchestrated-initiative ID per
# .specfuse/rules/correlation-ids.md; it appears in docs and tests legitimately.
# example.com / .org / .net are RFC 2606 reserved-for-documentation domains:
# they are never real secrets and appear pervasively as git-author fixtures in
# the test suite (e.g. tests/_workspace.py). A substring match exempts any
# address at those domains (test@example.com, git@example.org, ...). Without
# this, every new test that initializes a tmp git repo trips the email regex on
# the pre-commit hook. See FEAT-2026-0023/T03.
# git@github.com is the canonical public git remote/config address (it is the
# fixed SSH user for github.com — never a private secret). The module note below
# already lists it as a known false positive on the repo gate. It also reaches
# the STAGED surface via driver bookkeeping: when a squash is rejected, the
# leak-scan FINDINGS text — which QUOTES the offending match — is captured into
# events.jsonl as the attempt-failure note; the next bookkeeping commit then
# re-scans that audit log and re-trips on the quoted address (a self-poison).
# Allowlisting it stops both the direct hit and the captured-error replay.
# See FEAT-2026-0024 (the bookkeeping-commit crash this unblocked).
# ---------------------------------------------------------------------------

DEFAULT_ALLOWLIST: frozenset[str] = frozenset({
    "INIT-2026-0001",
    "example.com",
    "example.org",
    "example.net",
    "git@github.com",
})

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
# Hashed denylist (FEAT-2026-0024/T01) — committed, CI/Action surface.
#
# The plaintext denylist (above) is gitignored and absent on surfaces where the
# repo is checked out without operator-local files (CI, the gate-2 Action). The
# hashed denylist is a COMMITTED `leak_denylist.hashes` file: salted SHA-256 of
# normalized private-org literals, generated from the plaintext one by T02's
# `--hash-denylist`. It catches ACCIDENTAL re-introduction; with low-entropy
# names + a public salt it is obfuscation, not secrecy (see PLAN.md). This WU
# ships the core primitives only; T02 wires them into scan_repo + the generator.
# ---------------------------------------------------------------------------

_HASHED_DENYLIST_PATH = Path(__file__).parent / "leak_denylist.hashes"

# Committed default salt. The value actually used to MATCH is the one read from
# the `.hashes` header (load_hashed_denylist), so regenerating the file with a
# fresh salt stays self-consistent. This constant is the generator's default
# when no salt is supplied and a documented fallback; it is intentionally public.
_DEFAULT_DENYLIST_SALT = "specfuse-leak-denylist-v1"


def normalize_token(s: str) -> str:
    """Lowercase *s* and strip every non-``[a-z0-9]`` character.

    The single normalizer shared by the generator (T02) and the matcher below,
    so both agree on what a "literal" is. ``Acme-Widget_IAC`` -> ``acmewidgetiac``.
    """
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def hash_token(normalized: str, salt: str) -> str:
    """Return the salted SHA-256 hex digest of an already-normalized token.

    Deterministic: same (normalized, salt) -> same digest. Callers normalize
    with :func:`normalize_token` first; this function does not re-normalize.
    """
    return hashlib.sha256((salt + normalized).encode("utf-8")).hexdigest()


def load_hashed_denylist(
    path: Path | None = None,
) -> tuple[str, frozenset[int], frozenset[str]]:
    """Parse a ``leak_denylist.hashes`` file into ``(salt, lengths, hashes)``.

    Header lines ``# salt: <hex>`` and ``# lengths: <comma-ints>`` are parsed;
    any other comment/blank line is skipped; every remaining line is a hash.
    Missing file -> ``("", frozenset(), frozenset())`` (mirrors load_denylist's
    absent-file behavior — no crash on surfaces that have not generated one).
    """
    target = path if path is not None else _HASHED_DENYLIST_PATH
    if not target.exists():
        return ("", frozenset(), frozenset())
    salt = ""
    lengths: set[int] = set()
    hashes: set[str] = set()
    for line in target.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            body = stripped[1:].strip()
            if body.startswith("salt:"):
                salt = body[len("salt:"):].strip()
            elif body.startswith("lengths:"):
                for part in body[len("lengths:"):].split(","):
                    part = part.strip()
                    if part:
                        lengths.add(int(part))
            continue
        hashes.add(stripped)
    return (salt, frozenset(lengths), frozenset(hashes))


def hashed_denylist_hits(
    line: str,
    salt: str,
    lengths: frozenset[int],
    hashes: frozenset[str],
) -> bool:
    """True if a normalized substring of *line* hashes into the denylist set.

    Char-sliding-window match (PLAN.md "The hashing design"): normalize the
    line, then for each committed length ``L`` slide an ``L``-char window and
    hash each window with *salt*. This preserves the plaintext denylist's
    substring fidelity — a 10-char window over ``acmewidgetapp`` yields
    ``acmewidget``, the mid-atom substring an atom-n-gram approach would miss.
    Empty *lengths*/*hashes* -> never matches.
    """
    if not hashes or not lengths:
        return False
    norm = normalize_token(line)
    n = len(norm)
    for length in lengths:
        if length <= 0 or length > n:
            continue
        for start in range(n - length + 1):
            if hash_token(norm[start:start + length], salt) in hashes:
                return True
    return False


# ---------------------------------------------------------------------------
# Generator (FEAT-2026-0024/T02) — `--hash-denylist` writes the committed
# `leak_denylist.hashes` from the gitignored plaintext. Deterministic so CI can
# regenerate and diff. The caveat below is written verbatim into every generated
# header (AC6) so a reader of the committed file understands the guarantee.
# ---------------------------------------------------------------------------

_OBFUSCATION_CAVEAT = (
    "# Obfuscation, not secrecy. Low-entropy org names + a committed public salt\n"
    "# mean these digests stop trivial rainbow-table lookup but do NOT hide the\n"
    "# names from anyone who already has the plaintext. This guard exists to catch\n"
    "# ACCIDENTAL re-introduction of private org names, not to withstand a targeted\n"
    "# brute force. Generated by leak_scan.py --hash-denylist; do not hand-edit."
)


def generate_hashed_denylist(
    entries: list[str], salt: str = _DEFAULT_DENYLIST_SALT,
) -> str:
    """Render the `.hashes` file text for *entries* in the T01 format.

    Each entry is normalized with :func:`normalize_token`; entries whose
    normalization is empty are dropped. The header carries `# salt:`,
    `# lengths:` (distinct normalized lengths, ascending) and the obfuscation
    caveat; the body is one :func:`hash_token` digest per distinct normalized
    literal, sorted so the same plaintext always regenerates byte-identically.
    """
    normed = [n for n in (normalize_token(e) for e in entries) if n]
    lengths = sorted({len(n) for n in normed})
    digests = sorted({hash_token(n, salt) for n in normed})
    lines = [
        f"# salt: {salt}",
        f"# lengths: {','.join(str(length) for length in lengths)}",
        _OBFUSCATION_CAVEAT,
        *digests,
    ]
    return "\n".join(lines) + "\n"


def write_hashed_denylist(
    plaintext_path: Path | None = None,
    out_path: Path | None = None,
    salt: str = _DEFAULT_DENYLIST_SALT,
) -> int:
    """Read the plaintext denylist, write its hashed form, return the count.

    Parses `leak_denylist.txt` (gitignored plaintext) with the same
    comment/blank-skipping rule as :func:`load_denylist`, normalizes each
    literal, and writes `leak_denylist.hashes`. A missing plaintext file writes
    an empty-set file (header only) and returns 0 — never re-leaks literals.
    """
    src = plaintext_path if plaintext_path is not None else _DENYLIST_PATH
    dst = out_path if out_path is not None else _HASHED_DENYLIST_PATH
    entries: list[str] = []
    if src.exists():
        for line in src.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                entries.append(stripped)
    dst.write_text(generate_hashed_denylist(entries, salt), encoding="utf-8")
    return len(entries)


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


# ---------------------------------------------------------------------------
# CI-surface scan (whole repo)
# ---------------------------------------------------------------------------
#
# The structural regexes (user-path / email / private-host) are heuristics
# tuned for DIFFS — a *newly introduced* path or address is worth a human
# glance. Applied to the whole tree they false-positive on doc placeholders
# (`/Users/<user>/`), the detector's own test fixtures (`build-server.internal`),
# and config addresses (`git@github.com`). So the CI gate runs only the
# high-confidence checks: the operator denylist (gitignored literal private-org
# names) and gitleaks secret detection. The pre-commit hook still runs the full
# structural scan on the staged diff.


def _list_tracked_files(root: Path) -> list[str]:
    proc = subprocess.run(  # nosec B603 – list args, no shell
        ["git", "-C", str(root), "ls-files"],
        capture_output=True,
        text=True,
    )
    return proc.stdout.splitlines() if proc.returncode == 0 else []


def _check_gitleaks_dir(path: Path) -> list[str]:
    """Run gitleaks over an on-disk directory; return RuleID hit strings."""
    proc = subprocess.run(  # nosec B603 – list args, no shell
        [
            "gitleaks",
            "detect",
            "--source",
            str(path),
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


def scan_repo(root: str = ".") -> list[str]:
    """CI-surface scan of all git-tracked files: denylist + gitleaks secrets.

    Deliberately omits the structural regexes (see module note) to stay
    false-positive-free as an absolute repo gate. The hashed denylist
    (FEAT-2026-0024/T02) adds org-name coverage that survives in CI where the
    plaintext denylist is gitignored-absent: the committed `leak_denylist.hashes`
    is loaded once and each tracked line is sliding-window matched against it.
    Additive — the plaintext `denylist` check stays as a local-convenience
    supplement, and an absent `.hashes` contributes nothing (no crash).
    """
    root_path = Path(root)
    denylist = load_denylist()
    salt, lengths, hashes = load_hashed_denylist()
    hits: list[str] = []
    for rel in _list_tracked_files(root_path):
        fpath = root_path / rel
        try:
            text = fpath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            for entry in denylist:
                if entry.lower() in low:
                    hits.append(f"{rel}:{lineno}: denylist: {entry!r}")
            if hashes and hashed_denylist_hits(line, salt, lengths, hashes):
                hits.append(f"{rel}:{lineno}: denylist-hash")
    hits.extend(_check_gitleaks_dir(root_path))
    return hits


# ---------------------------------------------------------------------------
# CLI — wired by the pre-commit hook (--staged) and the CI gate (--all)
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Leak scanner (FEAT-2026-0020). Exit 1 on any finding."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--staged",
        action="store_true",
        help="scan the staged diff (full structural + denylist + secrets) — pre-commit",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="scan all tracked files (denylist + gitleaks secrets) — CI gate",
    )
    group.add_argument(
        "--hash-denylist",
        action="store_true",
        help="regenerate committed leak_denylist.hashes from the gitignored plaintext",
    )
    args = parser.parse_args(argv)

    if args.hash_denylist:
        count = write_hashed_denylist()
        print(f"leak-scan: wrote {count} hashed denylist entr{'y' if count == 1 else 'ies'}")
        return 0

    hits = scan_staged() if args.staged else scan_repo()
    if hits:
        print("leak-scan: FINDINGS")
        for h in hits:
            print("  " + h)
        return 1
    print("leak-scan: clean")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
