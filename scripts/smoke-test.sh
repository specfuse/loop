#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# scripts/smoke-test.sh — the repo's own CI-able sanity check.
#
# Runs against the bundled self-demonstrating example feature:
#   1. ensures PyYAML is installed,
#   2. lints the example feature folder,
#   3. dry-runs the loop driver from the repo root.
#
# Both Python invocations must exit 0. No `claude -p` is dispatched.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-python3}"

if "$PYTHON" -c 'import yaml' >/dev/null 2>&1; then
  echo "==> PyYAML already installed"
else
  echo "==> Installing PyYAML"
  "$PYTHON" -m pip install --quiet --disable-pip-version-check 'PyYAML>=6.0'
fi

echo "==> Linting bundled example feature"
"$PYTHON" .specfuse/scripts/lint_plan.py \
  .specfuse/features/FEAT-2026-0001-health-endpoint

echo "==> Dry-running the loop driver"
"$PYTHON" .specfuse/scripts/loop.py --dry-run

echo
echo "smoke test: OK"
