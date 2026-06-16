#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# scripts/setup.sh — one-time local setup for contributors.
#
# Installs the leak-prevention pre-commit guard (FEAT-2026-0020) and seeds the
# gitignored org-name denylist. Run once per fresh clone:
#
#     bash scripts/setup.sh
#
# Idempotent: safe to re-run.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Installing the leak-scan pre-commit hook (core.hooksPath)"
git config core.hooksPath .specfuse/hooks
echo "    core.hooksPath = $(git config core.hooksPath)"

DENYLIST=".specfuse/scripts/leak_denylist.txt"
if [ -f "$DENYLIST" ]; then
  echo "==> Denylist already present: $DENYLIST"
else
  echo "==> Seeding gitignored denylist template: $DENYLIST"
  cat > "$DENYLIST" <<'TEMPLATE'
# Private-org identifier denylist for leak_scan.py.
#
# GITIGNORED — never commit this file (committing the literals re-leaks them).
# One literal substring per line; case-insensitive; blank lines and # ignored.
# Add the private org / repo / product / hostname strings this clone must never
# let into a commit. Do NOT add shared sample IDs (e.g. INIT-2026-0001) — those
# are allowlisted in leak_scan.py.
#
# Example (delete and replace with your own):
# acme-internal
# acme-private-repo
TEMPLATE
  echo "    EDIT $DENYLIST to add your private-org strings."
fi

echo "==> Verifying the guard"
if python3 .specfuse/scripts/leak_scan.py --all >/dev/null 2>&1; then
  echo "    leak-scan --all: clean"
else
  echo "    leak-scan --all: found issues (run 'python3 .specfuse/scripts/leak_scan.py --all')"
fi

echo
echo "Setup complete. The pre-commit hook now runs leak-scan on every commit."
echo "Emergency bypass (CI still enforces secrets): git commit --no-verify"
