#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Insert Apache-2.0 license headers into source files missing them.

Remediation for FEAT-2026-0020/T05 (§licenses). Scans the same trees T05
scanned, detects file type (Python-with-shebang / Markdown-with-frontmatter /
Markdown-plain), and inserts the matching header template. Idempotent: a file
that already carries the header (per the same detection string T05 used) is
left untouched, so re-runs are safe and T06 can run it as the remediation step.

Modes:
  (default)     insert headers, print what changed
  --dry-run     report what WOULD change; write nothing
  --check       exit 1 if any in-scope file is missing a header; write nothing
                (use in CI / T06 verification)

Run from the repo root.
"""

import argparse
import sys
from pathlib import Path

# Trees + extensions are the SAME scope as T05's scan command. If T05's scope
# changes, change this too — drift defeats the audit-as-oracle property.
SCAN_DIRS = [
    ".specfuse/rules",
    ".specfuse/scripts",
    ".specfuse/skills",
    ".specfuse/templates",
]
EXTENSIONS = {".py", ".sh", ".md"}

# Same detection T05 used: header present if either string appears in the
# first 30 lines.
DETECT_STRINGS = (
    "Apache License, Version 2.0",
    "SPDX-License-Identifier: Apache-2.0",
)
DETECT_WINDOW = 30

PY_HEADER = (
    "#\n"
    "# Copyright 2026 Specfuse contributors\n"
    "# Licensed under the Apache License, Version 2.0. See LICENSE.\n"
    "#\n"
)

MD_NOFM_HEADER = (
    "<!--\n"
    "Copyright 2026 Specfuse Contributors\n"
    "Licensed under the Apache License, Version 2.0. See LICENSE.\n"
    "-->\n\n"
)

# Leading blank line so the comment sits one line below the closing `---`.
MD_FM_HEADER = (
    "\n"
    "<!--\n"
    "Copyright 2026 Specfuse Contributors\n"
    "Licensed under the Apache License, Version 2.0. See LICENSE.\n"
    "-->\n\n"
)


def has_header(text: str) -> bool:
    head = "\n".join(text.splitlines()[:DETECT_WINDOW])
    return any(s in head for s in DETECT_STRINGS)


def insert_header(path: Path, text: str):
    """Return (new_text, kind) or (None, reason) if not applicable."""
    lines = text.splitlines(keepends=True)
    suffix = path.suffix

    if suffix in (".py", ".sh"):
        # Insert after a shebang line if present, else at the very top.
        if lines and lines[0].startswith("#!"):
            return lines[0] + PY_HEADER + "".join(lines[1:]), "PY-HEADER (after shebang)"
        return PY_HEADER + text, "PY-HEADER"

    if suffix == ".md":
        # Frontmatter: first line is exactly '---'; insert after its close.
        if lines and lines[0].rstrip("\n") == "---":
            for i in range(1, len(lines)):
                if lines[i].rstrip("\n") == "---":
                    head = "".join(lines[: i + 1])
                    rest = "".join(lines[i + 1:])
                    return head + MD_FM_HEADER + rest, "MD-FM-HEADER"
            # Opened '---' but never closed — treat as plain to avoid corruption.
        return MD_NOFM_HEADER + text, "MD-NOFM-HEADER"

    return None, f"unsupported suffix {suffix}"


def iter_targets(root: Path):
    for d in SCAN_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in EXTENSIONS and not p.is_symlink():
                yield p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="report, write nothing")
    g.add_argument("--check", action="store_true",
                   help="exit 1 if any file is missing a header; write nothing")
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    scanned = inserted = skipped = 0
    missing = []

    for path in iter_targets(root):
        scanned += 1
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)
        if has_header(text):
            skipped += 1
            continue
        missing.append(rel)
        if args.check:
            continue
        new_text, kind = insert_header(path, text)
        if new_text is None:
            print(f"SKIP  {rel}  ({kind})")
            continue
        if args.dry_run:
            print(f"WOULD {rel}  [{kind}]")
        else:
            path.write_text(new_text, encoding="utf-8")
            print(f"INSERT {rel}  [{kind}]")
            inserted += 1

    print(f"\nScanned: {scanned}. Already-headered: {skipped}. "
          f"Missing: {len(missing)}.", file=sys.stderr)

    if args.check:
        if missing:
            print("MISSING headers:", file=sys.stderr)
            for m in missing:
                print(f"  {m}", file=sys.stderr)
            return 1
        print("OK — all in-scope files carry a header.", file=sys.stderr)
        return 0

    if not args.dry_run:
        print(f"Inserted: {inserted}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
