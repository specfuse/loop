#!/usr/bin/env bats
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Happy-path tests for scripts/sync-scaffold.sh. Per authoring-work-units §11.
# Uses REPO_ROOT env override so canonical .specfuse/ and dest specfuse/loop/data/
# are both rooted in a temp directory — no mutation of the real repo.

SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/scripts/sync-scaffold.sh"

setup() {
  TESTDIR="$(mktemp -d)"
  # Minimal canonical tree mirroring the real .specfuse/ shape.
  mkdir -p \
    "$TESTDIR/.specfuse/templates" \
    "$TESTDIR/.specfuse/rules" \
    "$TESTDIR/.specfuse/schemas/events" \
    "$TESTDIR/specfuse/loop/data"
  printf 'v0.1\n'        > "$TESTDIR/.specfuse/VERSION"
  printf '!.specfuse/\n' > "$TESTDIR/.specfuse/gitignore.snippet"
  printf 'roadmap\n'     > "$TESTDIR/.specfuse/roadmap.template.md"
  printf 'learnings\n'   > "$TESTDIR/.specfuse/LEARNINGS.template.md"
  printf 'verify\n'      > "$TESTDIR/.specfuse/verification.yml.example"
  printf 'GATE\n'        > "$TESTDIR/.specfuse/templates/GATE.template.md"
  printf 'PLAN\n'        > "$TESTDIR/.specfuse/templates/PLAN.template.md"
  printf 'WU\n'          > "$TESTDIR/.specfuse/templates/WU.template.md"
  printf 'corr\n'        > "$TESTDIR/.specfuse/rules/correlation-ids.md"
  printf 'never\n'       > "$TESTDIR/.specfuse/rules/never-touch.md"
  printf 'result\n'      > "$TESTDIR/.specfuse/rules/result-contract.md"
  printf 'security\n'    > "$TESTDIR/.specfuse/rules/security-boundaries.md"
  printf 'verifdisc\n'   > "$TESTDIR/.specfuse/rules/verification-discipline.md"
  printf '{"event":1}\n' > "$TESTDIR/.specfuse/schemas/event.schema.json"
  printf '{"e":1}\n'     > "$TESTDIR/.specfuse/schemas/events/initiative_created.schema.json"
  printf '{"e":2}\n'     > "$TESTDIR/.specfuse/schemas/events/spec_validated.schema.json"
  printf '{"e":3}\n'     > "$TESTDIR/.specfuse/schemas/events/spec_issue_resolved.schema.json"
  printf '{"e":4}\n'     > "$TESTDIR/.specfuse/schemas/events/spec_issue_routed.schema.json"
}

teardown() {
  rm -rf "$TESTDIR"
}

@test "sync copies all canonical files to specfuse/loop/data/" {
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -f "$TESTDIR/specfuse/loop/data/VERSION" ]
  [ -f "$TESTDIR/specfuse/loop/data/gitignore.snippet" ]
  [ -f "$TESTDIR/specfuse/loop/data/templates/PLAN.template.md" ]
  [ -f "$TESTDIR/specfuse/loop/data/rules/result-contract.md" ]
}

@test "sync copies file contents correctly" {
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  result="$(cat "$TESTDIR/specfuse/loop/data/VERSION")"
  [ "$result" = "v0.1" ]
}

@test "sync is idempotent (second run exits 0 and reports unchanged)" {
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$output" == *"already in sync"* ]]
}

@test "sync updates a stale file and reports it" {
  # Pre-populate dest with stale content.
  mkdir -p "$TESTDIR/specfuse/loop/data"
  printf 'OLD\n' > "$TESTDIR/specfuse/loop/data/VERSION"
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  result="$(cat "$TESTDIR/specfuse/loop/data/VERSION")"
  [ "$result" = "v0.1" ]
  [[ "$output" == *"synced"* ]]
}

@test "sync exits non-zero if canonical source dir is missing" {
  rm -rf "$TESTDIR/.specfuse"
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -ne 0 ]
  [[ "$output" == *"error"* ]]
}
