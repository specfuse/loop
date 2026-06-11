#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# scripts/install-hooks.sh — point git at the repo's tracked hooks dir
# (.githooks) so the pre-push hook runs scripts/smoke-test.sh before each
# push. Idempotent. Run once per clone.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

git config core.hooksPath .githooks
chmod +x .githooks/pre-push

echo "Installed git hooks: core.hooksPath=.githooks"
echo "Pre-push will run ./scripts/smoke-test.sh (bypass with --no-verify)."
