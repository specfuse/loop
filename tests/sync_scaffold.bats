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
    "$TESTDIR/.specfuse/rules-local" \
    "$TESTDIR/.specfuse/schemas/events" \
    "$TESTDIR/.specfuse/skills/demo" \
    "$TESTDIR/plugins/specfuse/skills/demo" \
    "$TESTDIR/specfuse/loop/data"
  # canonical plugin skill + its vendored copy (kept in sync by the script)
  printf 'demo skill\n' > "$TESTDIR/plugins/specfuse/skills/demo/SKILL.md"
  printf 'demo skill\n' > "$TESTDIR/.specfuse/skills/demo/SKILL.md"
  printf 'v0.1\n'        > "$TESTDIR/.specfuse/VERSION"
  printf '!.specfuse/\n' > "$TESTDIR/.specfuse/gitignore.snippet"
  printf 'roadmap\n'     > "$TESTDIR/.specfuse/roadmap.template.md"
  printf 'learnings\n'   > "$TESTDIR/.specfuse/LEARNINGS.template.md"
  printf 'changelog\n'  > "$TESTDIR/.specfuse/CHANGELOG.seed.md"
  printf 'verify\n'      > "$TESTDIR/.specfuse/verification.yml.example"
  printf 'monitor\n'     > "$TESTDIR/.specfuse/monitoring.yml.example"
  printf 'overrides\n'   > "$TESTDIR/.specfuse/monitoring.overrides.yml.example"
  printf 'checklist\n'   > "$TESTDIR/.specfuse/monitoring-secrets-checklist.md"
  printf 'GATE\n'        > "$TESTDIR/.specfuse/templates/GATE.template.md"
  printf 'DECISIONS\n'   > "$TESTDIR/.specfuse/templates/DECISIONS.template.md"
  printf 'PLAN\n'        > "$TESTDIR/.specfuse/templates/PLAN.template.md"
  printf 'WU\n'          > "$TESTDIR/.specfuse/templates/WU.template.md"
  printf 'corr\n'        > "$TESTDIR/.specfuse/rules/correlation-ids.md"
  printf 'closedisc\n'   > "$TESTDIR/.specfuse/rules/close-discipline.md"
  printf 'diagnose\n'    > "$TESTDIR/.specfuse/rules/design-for-diagnosis.md"
  printf 'never\n'       > "$TESTDIR/.specfuse/rules/never-touch.md"
  printf 'opesc\n'       > "$TESTDIR/.specfuse/rules/operator-escalation.md"
  printf 'humanout\n'    > "$TESTDIR/.specfuse/rules/human-output.md"
  printf 'plandisc\n'    > "$TESTDIR/.specfuse/rules/planning-discipline.md"
  printf 'localreadme\n' > "$TESTDIR/.specfuse/rules-local/README.md"
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
  # #575: the seed wire_claude writes to a project root must reach data/ too,
  # or `specfuse init` ships without the CHANGELOG.md close-k requires.
  [ -f "$TESTDIR/specfuse/loop/data/CHANGELOG.seed.md" ]
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

# --- #581: a local edit to a core-vendored file must halt, not be clobbered ---

setup_core() {
  # Vendored-from-core layout: core is the source for CORE_FILES, and the
  # sync must be able to tell "core moved forward" from "the loop edited this".
  mkdir -p "$TESTDIR/core/rules" "$TESTDIR/core/schemas/events"
  printf 'corr\n'        > "$TESTDIR/core/rules/correlation-ids.md"
  printf 'never\n'       > "$TESTDIR/core/rules/never-touch.md"
  printf 'security\n'    > "$TESTDIR/core/rules/security-boundaries.md"
  printf 'verifdisc\n'   > "$TESTDIR/core/rules/verification-discipline.md"
  printf '{"event":1}\n' > "$TESTDIR/core/schemas/event.schema.json"
  printf '{"e":1}\n'     > "$TESTDIR/core/schemas/events/initiative_created.schema.json"
  printf '{"e":2}\n'     > "$TESTDIR/core/schemas/events/spec_validated.schema.json"
  printf '{"e":3}\n'     > "$TESTDIR/core/schemas/events/spec_issue_resolved.schema.json"
  printf '{"e":4}\n'     > "$TESTDIR/core/schemas/events/spec_issue_routed.schema.json"
}

@test "vendor records a baseline so a later local edit is detectable" {
  setup_core
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -f "$TESTDIR/.specfuse/.vendored.json" ]
}

@test "core moving forward is a clean fast-forward, not a conflict" {
  setup_core
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  printf 'corr v2\n' > "$TESTDIR/core/rules/correlation-ids.md"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  result="$(cat "$TESTDIR/.specfuse/rules/correlation-ids.md")"
  [ "$result" = "corr v2" ]
}

@test "a local edit to a vendored file halts the sync and names the file" {
  setup_core
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  # The loop edits a core-owned file (what FEAT-2026-0073 did).
  printf 'corr\nplus a loop-local block\n' > "$TESTDIR/.specfuse/rules/correlation-ids.md"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -ne 0 ]
  [[ "$output" == *"rules/correlation-ids.md"* ]]
}

@test "the halt does not clobber the local edit" {
  setup_core
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  printf 'corr\nplus a loop-local block\n' > "$TESTDIR/.specfuse/rules/correlation-ids.md"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -ne 0 ]
  # The whole point: the edit survives the refusal.
  [[ "$(cat "$TESTDIR/.specfuse/rules/correlation-ids.md")" == *"loop-local block"* ]]
}
