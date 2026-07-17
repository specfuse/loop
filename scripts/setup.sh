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

echo "==> Installing git hooks (core.hooksPath)"
# core.hooksPath is single-valued: one directory holds ALL hooks. .specfuse/hooks
# carries both pre-commit (leak-scan) and pre-push (smoke-test); arm both so this
# installer and scripts/install-hooks.sh no longer clobber each other (issue #153).
git config core.hooksPath .specfuse/hooks
chmod +x .specfuse/hooks/pre-commit .specfuse/hooks/pre-push
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
echo "Setup complete. pre-commit runs leak-scan on every commit; pre-push runs"
echo "the smoke test before every push."
echo "Emergency bypass (CI still enforces secrets): git commit/push --no-verify"
