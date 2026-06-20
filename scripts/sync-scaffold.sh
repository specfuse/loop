#!/usr/bin/env bash
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# sync-scaffold.sh — copy canonical .specfuse/ sources into specfuse/loop/data/.
#
# The packaged scaffold data (specfuse/loop/data/) is a byte-for-byte copy of the
# canonical sources in .specfuse/. Run this after editing any canonical source,
# then commit and run the drift-guard test (tests/test_scaffold_data_in_sync.py).
#
# Usage: scripts/sync-scaffold.sh
#
# REPO_ROOT may be overridden by the environment (used by tests).

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SRC="$REPO_ROOT/.specfuse"
DEST="$REPO_ROOT/specfuse/loop/data"

if [[ ! -d "$SRC" ]]; then
  echo "error: canonical source dir not found: $SRC" >&2
  exit 1
fi
if [[ ! -d "$DEST" ]]; then
  echo "error: package data dir not found: $DEST" >&2
  exit 1
fi

synced=0

sync_file() {
  local rel="$1"
  local src_path="$SRC/$rel"
  local dest_path="$DEST/$rel"
  local dest_dir
  dest_dir="$(dirname "$dest_path")"
  if [[ ! -f "$src_path" ]]; then
    echo "error: canonical source missing: $src_path" >&2
    return 1
  fi
  mkdir -p "$dest_dir"
  if cmp -s "$src_path" "$dest_path" 2>/dev/null; then
    echo "  unchanged: $rel"
  else
    cp "$src_path" "$dest_path"
    echo "  synced:    $rel"
    synced=$((synced + 1))
  fi
}

FILES=(
  VERSION
  gitignore.snippet
  verification.yml.example
  roadmap.template.md
  LEARNINGS.template.md
  templates/GATE.template.md
  templates/PLAN.template.md
  templates/WU.template.md
  rules/correlation-ids.md
  rules/never-touch.md
  rules/result-contract.md
  rules/security-boundaries.md
)

echo "Syncing scaffold data:"
echo "  from: $SRC"
echo "  to:   $DEST"
echo

for f in "${FILES[@]}"; do
  sync_file "$f"
done

echo
if [[ "$synced" -eq 0 ]]; then
  echo "Scaffold data already in sync (${#FILES[@]} files checked)."
else
  echo "$synced file(s) updated."
fi
