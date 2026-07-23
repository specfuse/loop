#!/usr/bin/env bash
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# sync-scaffold.sh — vendor shared substrate from core, then copy canonical
# .specfuse/ sources into specfuse/loop/data/.
#
# Two stages:
#   1. Vendor-from-core (skipped when core is absent): the shared Specfuse
#      methodology substrate — the neutral rules and the event schema — has a
#      single source of truth in the methodology core (specfuse/methodology/).
#      This stage copies those files from core INTO the canonical .specfuse/, so
#      core is the vendoring source. It runs only in a dev checkout where core is
#      a sibling; CI (no core) skips it and just verifies drift between the
#      already-committed .specfuse/ and data/.
#      Vendored from core: correlation-ids, never-touch, security-boundaries,
#      verification-discipline, and the event schema. NOT vendored:
#      result-contract.md (loop-surface-specific, stays loop-local) and
#      role-switch-hygiene.md (orchestrator multi-role concept; N/A to the loop's
#      fresh-session-per-WU model).
#   2. Vendor-skills: .specfuse/skills/ is a byte-for-byte copy of the loop's
#      canonical, marketplace-published plugin at plugins/specfuse/skills/. The
#      loop operates on .specfuse/skills/ (via .claude/skills forward symlinks);
#      plugins/specfuse/ is the single source of truth. Guarded by
#      tests/test_skills_vendored_in_sync.py.
#   3. Package-sync: specfuse/loop/data/ is a byte-for-byte copy of the canonical
#      .specfuse/ sources. Run this after editing any canonical source, then
#      commit and run the drift-guard test (tests/test_scaffold_data_in_sync.py).
#
# Usage: scripts/sync-scaffold.sh
#
# REPO_ROOT and SPECFUSE_CORE may be overridden by the environment (used by tests).

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SRC="$REPO_ROOT/.specfuse"
DEST="$REPO_ROOT/specfuse/loop/data"
CORE="${SPECFUSE_CORE:-$REPO_ROOT/../specfuse/methodology}"

if [[ ! -d "$SRC" ]]; then
  echo "error: canonical source dir not found: $SRC" >&2
  exit 1
fi
if [[ ! -d "$DEST" ]]; then
  echo "error: package data dir not found: $DEST" >&2
  exit 1
fi

# Files vendored FROM core (relative both under $CORE and under $SRC).
CORE_FILES=(
  rules/correlation-ids.md
  rules/never-touch.md
  rules/security-boundaries.md
  rules/verification-discipline.md
  schemas/event.schema.json
  schemas/events/initiative_created.schema.json
  schemas/events/spec_validated.schema.json
  schemas/events/spec_issue_resolved.schema.json
  schemas/events/spec_issue_routed.schema.json
)

vendored=0
echo "Vendoring shared substrate from core:"
if [[ -d "$CORE" ]]; then
  echo "  from: $CORE"
  echo "  to:   $SRC"
  for rel in "${CORE_FILES[@]}"; do
    core_path="$CORE/$rel"
    dest_path="$SRC/$rel"
    if [[ ! -f "$core_path" ]]; then
      echo "error: core source missing: $core_path" >&2
      exit 1
    fi
    mkdir -p "$(dirname "$dest_path")"
    if cmp -s "$core_path" "$dest_path" 2>/dev/null; then
      echo "  unchanged: $rel"
    else
      cp "$core_path" "$dest_path"
      echo "  vendored:  $rel"
      vendored=$((vendored + 1))
    fi
  done
  echo "  $vendored file(s) updated from core."
else
  echo "  core not found at $CORE — skipping (dev-only stage)."
  echo "  set SPECFUSE_CORE to re-vendor; CI verifies committed .specfuse/↔data/ drift."
fi
echo

# Vendor .specfuse/skills/ from the canonical plugin source (plugins/specfuse/
# skills/), exactly as the rules above are vendored from core. plugins/specfuse/
# is the loop's canonical, marketplace-published plugin; .specfuse/skills/ is a
# byte-identical vendored copy so the loop's dogfood session (via the
# .claude/skills forward symlinks) resolves skills at .specfuse/skills/ unchanged.
PLUGIN_SKILLS="$REPO_ROOT/plugins/specfuse/skills"
echo "Vendoring skills from canonical plugin:"
if [[ -d "$PLUGIN_SKILLS" ]]; then
  echo "  from: $PLUGIN_SKILLS"
  echo "  to:   $SRC/skills"
  if diff -rq "$PLUGIN_SKILLS" "$SRC/skills" >/dev/null 2>&1; then
    echo "  unchanged: skills/ already in sync"
  else
    rm -rf "$SRC/skills"
    cp -R "$PLUGIN_SKILLS" "$SRC/skills"
    echo "  vendored:  skills/ ($(find "$SRC/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ') skills)"
  fi
else
  echo "error: canonical plugin skills dir not found: $PLUGIN_SKILLS" >&2
  exit 1
fi
echo

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
  rules/planning-discipline.md
  rules-local/README.md
  rules/result-contract.md
  rules/security-boundaries.md
  rules/verification-discipline.md
  schemas/event.schema.json
  schemas/events/initiative_created.schema.json
  schemas/events/spec_validated.schema.json
  schemas/events/spec_issue_resolved.schema.json
  schemas/events/spec_issue_routed.schema.json
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
