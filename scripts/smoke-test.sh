#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# scripts/smoke-test.sh — the repo's own CI-able sanity check.
#
# Two layers, in order:
#   1. SCAFFOLD INTEGRITY — lint the bundled example feature and dry-run the
#      driver. Proves the scaffold a target project installs is still coherent.
#   2. METHODOLOGY `code` GATES — the same commands declared in this repo's
#      .specfuse/verification.yml: tests, lint, security, coverage. Proves
#      this repo practices the methodology it ships. If the script and the
#      YAML drift, the verification-as-oracle property breaks.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-python3}"

if "$PYTHON" -c 'import yaml, ruff, bandit, coverage' >/dev/null 2>&1; then
  echo "==> Runtime + dev tooling already installed"
else
  echo "==> Installing runtime + dev tooling (pyyaml, ruff, bandit, coverage)"
  "$PYTHON" -m pip install --quiet --disable-pip-version-check -e '.[dev]'
fi

# --- 1. Scaffold integrity ---

echo "==> [scaffold] Linting bundled example feature"
"$PYTHON" .specfuse/scripts/lint_plan.py \
  .specfuse/features/FEAT-2026-0001-health-endpoint

echo "==> [scaffold] Dry-running the loop driver"
"$PYTHON" .specfuse/scripts/loop.py --dry-run

# --- 2. Methodology `code` gates ---
# These mirror .specfuse/verification.yml `code` set verbatim. Keep in sync.

echo "==> [gate: tests] unittest"
"$PYTHON" -m unittest discover -s tests -v

echo "==> [gate: lint] ruff"
ruff check .specfuse/scripts tests scripts

echo "==> [gate: security] bandit"
bandit -r .specfuse/scripts -ll

echo "==> [gate: coverage] coverage --fail-under=35"
coverage run --source=.specfuse/scripts -m unittest discover -s tests \
  && coverage report --fail-under=35

echo
echo "smoke test: OK"
