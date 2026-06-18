#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# sync-skills.sh — copy this repo's canonical skills (.specfuse/skills/) into the
# specfuse/specfuse plugin (plugins/specfuse/skills/). The loop repo is the single
# source of truth for skill craft; the plugin ships a copy. Run this after editing
# any skill, then commit + validate in the umbrella repo.
#
# Usage:
#   scripts/sync-skills.sh [UMBRELLA_REPO_PATH]
#
# UMBRELLA_REPO_PATH defaults to $SPECFUSE_UMBRELLA, else ../specfuse (sibling).

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.specfuse/skills"
UMBRELLA="${1:-${SPECFUSE_UMBRELLA:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/specfuse}}"
DEST_DIR="$UMBRELLA/plugins/specfuse/skills"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "error: source skills dir not found: $SRC_DIR" >&2
  exit 1
fi
if [[ ! -d "$DEST_DIR" ]]; then
  echo "error: umbrella plugin skills dir not found: $DEST_DIR" >&2
  echo "  pass the umbrella repo path, or set \$SPECFUSE_UMBRELLA." >&2
  echo "  (clone: git clone git@github.com:specfuse/specfuse.git)" >&2
  exit 1
fi

echo "Syncing skills:"
echo "  from: $SRC_DIR"
echo "  to:   $DEST_DIR"

# Copy contents (overlay); does not delete skills removed from source — those are
# rare and removal is a deliberate act the maintainer makes explicitly.
cp -R "$SRC_DIR/." "$DEST_DIR/"

count="$(find "$SRC_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
echo "Synced $count skill(s)."
echo
echo "Next, in the umbrella repo:"
echo "  claude plugin validate $UMBRELLA/plugins/specfuse   # strict YAML + structure"
echo "  git -C $UMBRELLA add -A && git -C $UMBRELLA commit -m 'chore: sync skills from specfuse/loop'"
