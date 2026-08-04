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
# Pin --feature to the bundled example: this scaffold-integrity probe must
# stay stable as new in-flight features land in .specfuse/features/. Without
# the pin, every new `status: active` feature breaks CI on multi-active.
"$PYTHON" .specfuse/scripts/loop.py --dry-run --feature FEAT-2026-0001-health-endpoint

# --- 2. Methodology `code` gates ---
# Derived from .specfuse/verification.yml, NOT copied from it (#592). The old
# hand-maintained mirror carried the comment "Keep in sync" and drifted by six
# gates; two of them shipped with features and were never once executed here.
# A declared-but-unrun gate is worse than an absent one, because the
# declaration reads as coverage.
#
# The declared commands say `python3` because that is what a target project's
# driver invokes. This script substitutes "$PYTHON" so the gates run under the
# virtualenv interpreter that actually has the dependencies.

while IFS=$'\t' read -r gate command; do
  [ -n "$gate" ] || continue
  echo "==> [gate: $gate] ${command%% *}"
  # shellcheck disable=SC2086  # commands are declared, not user input
  eval "${command/#python3 /$PYTHON }"
done < <("$PYTHON" -m specfuse.loop.gate_commands .specfuse/verification.yml)

echo
echo "smoke test: OK"
