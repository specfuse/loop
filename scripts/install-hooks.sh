#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# scripts/install-hooks.sh — point git at the repo's tracked hooks dir
# (.specfuse/hooks) so the pre-push hook runs scripts/smoke-test.sh before each
# push. Idempotent. Run once per clone.
#
# core.hooksPath is single-valued: one directory holds ALL hooks. Both this
# script and scripts/setup.sh point at .specfuse/hooks, which carries both the
# pre-push (smoke-test) and pre-commit (leak-scan) hooks — running either
# installer arms both (issue #153).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

git config core.hooksPath .specfuse/hooks
chmod +x .specfuse/hooks/pre-push .specfuse/hooks/pre-commit

echo "Installed git hooks: core.hooksPath=.specfuse/hooks"
echo "Pre-push runs ./scripts/smoke-test.sh; pre-commit runs the leak scanner (bypass either with --no-verify)."
