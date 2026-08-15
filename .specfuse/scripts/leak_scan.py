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

# A `Co-authored-by:` git trailer, anchored to the START of the line (git trailer
# keys are case-insensitive, and a trailer may be indented). Its address is
# machine-written by the commit convention, and `gh pr create --fill` copies a
# single commit's message into the PR body verbatim — so `leak_scan_content.py`,
# which scans `pull_request.body`, tripped `_EMAIL_RE` on EVERY single-commit PR
# opened that way, on a clean diff. See #1171.
#
# This exempts the EMAIL rule only, and only on a matching line: user-path,
# private-host and denylist checks all still run, so the trailer cannot be used
# to smuggle a home path or a private org name past the scan. It is deliberately
# NOT a DEFAULT_ALLOWLIST entry — `_line_exempt` is a substring match over the
# whole line, which would exempt the address anywhere in any file and bake a
# specific vendor address into the scaffold.
_COAUTHOR_TRAILER_RE = re.compile(r"^\s*co-authored-by:", re.IGNORECASE)

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
        if not _COAUTHOR_TRAILER_RE.match(line):
            for m in _EMAIL_RE.finditer(line):
                hits.append(f"line {lineno}: email: {m.group()!r}")
        for m in _PRIVATE_HOST_RE.finditer(line):
            hits.append(f"line {lineno}: private-host: {m.group()!r}")
        for entry in denylist:
            if entry.lower() in line.lower():
                hits.append(f"line {lineno}: denylist: {entry!r}")
    return hits


# The pinned gitleaks version. CI, the release workflow, and the content-scan
# workflow all install exactly this build; `tests/test_gitleaks_pinning.py`
# asserts the workflows and this constant agree, so the three cannot drift.
#
# Pinning is not tidiness. The gate's verdict used to depend on an UNPINNED
# binary in both directions: CI did `apt-get install gitleaks || curl <release>`,
# so a runner whose apt carries gitleaks silently got Ubuntu's build (8.18.x on
# noble) while a developer had whatever their package manager shipped. The two
# rulesets disagree, so pass/fail could change with NO change to the repo — the
# time-varying-oracle failure mode `[FEAT-2026-0007/G1-CLOSE]` records, except
# varying across machines rather than over time. See #250.
GITLEAKS_PINNED_VERSION = "8.30.1"

_GITLEAKS_MISSING_HINT = (
    "gitleaks:not-installed: the leak-scan gate requires the `gitleaks` binary "
    f"on PATH (pinned v{GITLEAKS_PINNED_VERSION}). Install it from "
    "https://github.com/gitleaks/gitleaks/releases"
)


def gitleaks_version() -> str:
    """Return the gitleaks version string on PATH, or a marker if unavailable.

    Reported in the gate output so a version divergence is visible immediately
    instead of requiring someone to diff two CI logs (#250).
    """
    try:
        proc = subprocess.run(  # nosec B603 – list args, no shell
            ["gitleaks", "version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return "not-installed"
    if proc.returncode != 0:
        return "unknown"
    return (proc.stdout or proc.stderr).strip().splitlines()[0] if (
        proc.stdout or proc.stderr
    ) else "unknown"


def _run_gitleaks(source: Path | str) -> list[str]:
    """Run gitleaks over *source*; return finding strings. `[]` means clean.

    Single implementation for both the text and directory scans — they differ
    only in what they point `--source` at, and the two hand-written copies had
    the same defect, so fixing one and not the other would have shipped half a
    fix (the `[FEAT-2026-0015/G1]` enumeration rule).

    Three outcomes, deliberately distinguished (#250 defect 2). The old code
    collapsed the last two into the string `gitleaks:secrets-detected`, so a
    version that does not support `--report-path -`, a malformed config, an
    unreadable path, or an OOM were all reported as "a secret exists" — with no
    rule id, no file, and no line. That cried wolf on tool failure AND hid which
    rule fired on a real finding; it is why diagnosing the CI incident in #250
    needed a version-archaeology dig instead of reading a rule name.

      exit 0                      -> [] (clean)
      non-zero + parseable JSON   -> ["secret:<RuleID> (<file>)", ...] (real findings)
      non-zero + unparseable      -> ["gitleaks:scan-failed: <stderr>"] (tool broke)

    Both non-clean outcomes fail the gate, but they are different failures and
    now say so. A missing binary is a fourth case: `FileNotFoundError` used to
    escape as a traceback (`check=False` does not suppress it), so a contributor
    without gitleaks got a stack trace from a test rather than an actionable
    message (#250 defect 3).
    """
    try:
        proc = subprocess.run(  # nosec B603 – list args, no shell expansion; source is process-local
            [
                "gitleaks",
                "detect",
                "--source",
                str(source),
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
            check=False,
        )
    except FileNotFoundError:
        return [_GITLEAKS_MISSING_HINT]

    if proc.returncode == 0:
        return []
    try:
        findings = json.loads(proc.stdout)
    except (json.JSONDecodeError, AttributeError, TypeError):
        findings = None
    if isinstance(findings, list):
        hits = []
        for f in findings:
            if not isinstance(f, dict):
                continue
            rule = f.get("RuleID", "unknown")
            where = f.get("File") or f.get("file")
            hits.append(f"secret:{rule} ({where})" if where else f"secret:{rule}")
        return hits
    stderr = (proc.stderr or "").strip() or "(gitleaks produced no stderr)"
    return [f"gitleaks:scan-failed: {stderr}"]


def _check_gitleaks(text: str) -> list[str]:
    """Run gitleaks over *text*; return finding strings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "content.txt").write_text(text, encoding="utf-8")
        return _run_gitleaks(tmpdir)


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
        check=False,
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
        check=False,
    )
    return proc.stdout.splitlines() if proc.returncode == 0 else []


def _check_gitleaks_tracked(root: Path) -> list[str]:
    """Run gitleaks over the repo's *git-tracked* files only.

    `scan_repo`'s contract is "all git-tracked files", and its denylist half
    honours that by iterating `_list_tracked_files`. Pointing gitleaks at the
    working directory instead swept in everything untracked and gitignored —
    `__pycache__`, `.venv`, `build/`, `dist/` — none of which is in the repo
    and none of which a repo gate should judge.

    That was not theoretical: CI runs the test suite before this gate, and
    gitleaks 8.18.2 (what Ubuntu's apt ships) matches its `aws-access-token`
    rule against byte sequences in compiled `.pyc` files, so the gate failed on
    bytecode that is gitignored and never committed. Locally, with a newer
    gitleaks, the same tree passed — see #250 for the version-pinning half of
    this problem.

    Materialising the tracked set into a temp dir keeps the scan aligned with
    the documented contract and makes the verdict independent of whatever
    build artifacts happen to be lying around.
    """
    with tempfile.TemporaryDirectory() as td:
        staged = Path(td)
        for rel in _list_tracked_files(root):
            src = root / rel
            if not src.is_file():  # deleted-but-tracked, submodules
                continue
            dst = staged / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                dst.write_bytes(src.read_bytes())
            except OSError:
                continue
        return _check_gitleaks_dir(staged)


def _check_gitleaks_dir(path: Path) -> list[str]:
    """Run gitleaks over an on-disk directory; return finding strings."""
    return _run_gitleaks(path)


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
    hits.extend(_check_gitleaks_tracked(root_path))
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
    # Report the gitleaks build that produced this verdict. Without it, a
    # divergence between two machines is invisible until someone diffs two logs
    # — which is exactly how #250 was diagnosed, expensively.
    version = gitleaks_version()
    # `gitleaks version` prints a bare `8.30.1` on some builds and `v8.30.1` on
    # others, so normalise the optional prefix before comparing — otherwise a
    # correctly-pinned runner reports a mismatch against itself.
    matches = version.lstrip("v") == GITLEAKS_PINNED_VERSION
    suffix = "" if matches else f" — expected v{GITLEAKS_PINNED_VERSION}"
    print(f"leak-scan: gitleaks {version}{suffix}")
    if hits:
        print("leak-scan: FINDINGS")
        for h in hits:
            print("  " + h)
        return 1
    print("leak-scan: clean")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
