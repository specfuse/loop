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

# Baseline of what was last vendored, so a destination that differs from core
# can be classified rather than clobbered (#581). A destination matching its
# recorded hash means core moved forward -> fast-forward. A destination that
# does NOT match means the loop edited a core-owned file -> stop and let a
# human decide. Before this, both cases looked identical ("differs from core")
# and the sync silently reverted loop-local edits: FEAT-2026-0073's
# enforcement-surfaces block was deleted with only a routine `vendored:` line.
VENDOR_BASELINE="$SRC/.vendored.json"

baseline_hash() {  # $1=rel — recorded hash, or empty when unknown
  # awk with a literal index() match: relpaths contain `/`, which collides with
  # sed's default substitute delimiter and made this silently abort mid-run.
  [[ -f "$VENDOR_BASELINE" ]] || return 0
  awk -v key="\"$1\":" '
    index($0, key) && match($0, /"[a-f0-9][a-f0-9]*"[[:space:]]*,?[[:space:]]*$/) {
      print substr($0, RSTART + 1, RLENGTH - 2)
    }' "$VENDOR_BASELINE" | tr -d '", \t'
}

file_hash() {  # $1=path
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else sha256sum "$1" | cut -d' ' -f1; fi
}

vendored=0
echo "Vendoring shared substrate from core:"
if [[ -d "$CORE" ]]; then
  echo "  from: $CORE"
  echo "  to:   $SRC"
  diverged=()
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
      continue
    fi
    # Differs from core. Local edit, or core moving forward?
    if [[ -f "$dest_path" ]]; then
      recorded="$(baseline_hash "$rel")"
      if [[ -n "$recorded" && "$(file_hash "$dest_path")" != "$recorded" ]]; then
        diverged+=("$rel")
        continue
      fi
    fi
    cp "$core_path" "$dest_path"
    echo "  vendored:  $rel"
    vendored=$((vendored + 1))
  done

  if [[ ${#diverged[@]} -gt 0 ]]; then
    {
      echo
      echo "error: core-vendored file(s) edited locally; refusing to overwrite:"
      for rel in "${diverged[@]}"; do echo "  $rel"; done
      echo
      echo "These files are owned by the methodology core ($CORE) and this repo"
      echo "has changed them since they were last vendored. Overwriting would"
      echo "silently revert that work, which is how FEAT-2026-0073's"
      echo "enforcement-surfaces block was lost."
      echo
      echo "Resolve by choosing one, then re-run:"
      echo "  - the change belongs to everyone: land it in core, then re-vendor;"
      echo "  - the change is loop-specific: move it out of the vendored file"
      echo "    (a loop-local rule, repo docs, or a comment at the code it"
      echo "    describes) and restore the file to core-identical;"
      echo "  - the local copy is the one to keep for now: update the baseline"
      echo "    hash in $VENDOR_BASELINE deliberately, recording why."
    } >&2
    exit 1
  fi

  # Record what is now vendored, so the next run can classify a difference.
  {
    echo "{"
    last=$((${#CORE_FILES[@]} - 1))
    for i in "${!CORE_FILES[@]}"; do
      rel="${CORE_FILES[$i]}"
      sep=","; [[ "$i" -eq "$last" ]] && sep=""
      printf '  "%s": "%s"%s\n' "$rel" "$(file_hash "$SRC/$rel")" "$sep"
    done
    echo "}"
  } > "$VENDOR_BASELINE"

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

# Discovery links: .claude/skills/ forward symlinks into .specfuse/skills/, so
# Claude Code's discovery (which reads .claude/skills/) picks up every skill.
# Creates only what's missing; an existing entry is left exactly as found —
# never replaced, never re-pointed, even if it resolves outside
# .specfuse/skills/ (operator tooling under .agents/skills/ is not this
# script's business). Guarded by tests/test_skill_discovery_links.py.
CLAUDE_SKILLS="$REPO_ROOT/.claude/skills"
echo "Creating missing skill discovery links:"
mkdir -p "$CLAUDE_SKILLS"
linked=0
for skill_dir in "$SRC/skills"/*/; do
  [[ -d "$skill_dir" ]] || continue
  name="$(basename "$skill_dir")"
  link_path="$CLAUDE_SKILLS/$name"
  if [[ -e "$link_path" || -L "$link_path" ]]; then
    continue
  fi
  ln -s "../../.specfuse/skills/$name" "$link_path"
  echo "  linked: $name"
  linked=$((linked + 1))
done
if [[ "$linked" -eq 0 ]]; then
  echo "  no missing links; all skills already linked."
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
  monitoring.yml.example
  monitoring.overrides.yml.example
  monitoring-secrets-checklist.md
  roadmap.template.md
  LEARNINGS.template.md
  CHANGELOG.seed.md
  templates/GATE.template.md
  templates/PLAN.template.md
  templates/WU.template.md
  rules/close-discipline.md
  rules/correlation-ids.md
  rules/design-for-diagnosis.md
  rules/never-touch.md
  rules/operator-escalation.md
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
