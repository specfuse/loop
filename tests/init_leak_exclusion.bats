#!/usr/bin/env bats
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Regression test for issue #55 — init.sh must deploy only the scaffold a target
# project needs, not specfuse-loop-internal files:
#   * scripts/ is an explicit allowlist (DEPLOYABLE_SCRIPTS) — the leak-guard
#     scanners + denylist data (leak_*) never ship, and a future internal
#     script is excluded by default.
#   * LEARNINGS.md is seeded from LEARNINGS.template.md (generic methodology
#     lessons), NOT this repo's real LEARNINGS.md (its own FEAT-2026-* history).
# See the leak_guard_specfuse_internal note.

setup() {
  REPO="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  TARGET="$(mktemp -d)"
}

teardown() {
  [ -n "$TARGET" ] && rm -rf "$TARGET"
}

INTERNAL="leak_scan.py leak_scan_content.py leak_denylist.txt leak_denylist.hashes"
DEPLOYABLE="loop.py lint_plan.py _miniyaml.py gate_eval.py gh_backend.py gh_features.py adopt_feature.py validate-event.py"

@test "init does not copy specfuse-internal leak_* files into the target" {
  run bash "$REPO/init.sh" "$TARGET"
  [ "$status" -eq 0 ]
  for f in $INTERNAL; do
    [ ! -e "$TARGET/.specfuse/scripts/$f" ]
  done
}

@test "init copies every deployable script" {
  run bash "$REPO/init.sh" "$TARGET"
  [ "$status" -eq 0 ]
  for f in $DEPLOYABLE; do
    [ -e "$TARGET/.specfuse/scripts/$f" ]
  done
}

@test "upgrade prunes stale leak_* files left by a prior init" {
  run bash "$REPO/init.sh" "$TARGET"
  [ "$status" -eq 0 ]
  # Simulate a target that received the internal files from an older init.
  printf 'stale\n' > "$TARGET/.specfuse/scripts/leak_scan.py"
  printf 'stale\n' > "$TARGET/.specfuse/scripts/leak_denylist.hashes"
  printf 'stale\n' > "$TARGET/.specfuse/scripts/leak_denylist.txt"
  run bash "$REPO/init.sh" --upgrade "$TARGET"
  [ "$status" -eq 0 ]
  for f in $INTERNAL; do
    [ ! -e "$TARGET/.specfuse/scripts/$f" ]
  done
  [ -e "$TARGET/.specfuse/scripts/loop.py" ]
}

@test "init seeds LEARNINGS.md from the template, not this repo's history" {
  run bash "$REPO/init.sh" "$TARGET"
  [ "$status" -eq 0 ]
  [ -e "$TARGET/.specfuse/LEARNINGS.md" ]
  # The template carries generic methodology lessons but NONE of this repo's
  # own FEAT-2026-* feature history.
  run grep -q 'FEAT-2026' "$TARGET/.specfuse/LEARNINGS.md"
  [ "$status" -ne 0 ]
  # Sanity: the generic meta lessons ARE present.
  grep -q 'meta/first-live-use' "$TARGET/.specfuse/LEARNINGS.md"
}

@test "the LEARNINGS template ships with the scaffold source" {
  [ -e "$REPO/.specfuse/LEARNINGS.template.md" ]
}
