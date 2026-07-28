#!/usr/bin/env bats
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Happy-path tests for the .claude/skills discovery-link step in
# scripts/sync-scaffold.sh (#284). Per authoring-work-units §11.
# Uses REPO_ROOT env override so .specfuse/, .claude/skills/, and
# specfuse/loop/data/ are all rooted in a temp directory — no mutation of the
# real repo.

SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/scripts/sync-scaffold.sh"

setup() {
  TESTDIR="$(mktemp -d)"
  mkdir -p \
    "$TESTDIR/.specfuse/templates" \
    "$TESTDIR/.specfuse/rules" \
    "$TESTDIR/.specfuse/rules-local" \
    "$TESTDIR/.specfuse/schemas/events" \
    "$TESTDIR/.specfuse/skills/demo" \
    "$TESTDIR/.specfuse/skills/linked-demo" \
    "$TESTDIR/.claude/skills" \
    "$TESTDIR/plugins/specfuse/skills/demo" \
    "$TESTDIR/plugins/specfuse/skills/linked-demo" \
    "$TESTDIR/specfuse/loop/data" \
    "$TESTDIR/elsewhere/target"
  printf 'demo skill\n'   > "$TESTDIR/plugins/specfuse/skills/demo/SKILL.md"
  printf 'demo skill\n'   > "$TESTDIR/.specfuse/skills/demo/SKILL.md"
  printf 'linked demo\n'  > "$TESTDIR/plugins/specfuse/skills/linked-demo/SKILL.md"
  printf 'linked demo\n'  > "$TESTDIR/.specfuse/skills/linked-demo/SKILL.md"
  # a pre-existing, already-correct entry: must be left byte-identical (same target)
  ln -s "../../.specfuse/skills/linked-demo" "$TESTDIR/.claude/skills/linked-demo"
  # an operator-tooling entry resolving OUTSIDE .specfuse/skills/: not this script's business
  ln -s "../../elsewhere/target" "$TESTDIR/.claude/skills/external-tool"
  printf 'v0.1\n'        > "$TESTDIR/.specfuse/VERSION"
  printf '!.specfuse/\n' > "$TESTDIR/.specfuse/gitignore.snippet"
  printf 'roadmap\n'     > "$TESTDIR/.specfuse/roadmap.template.md"
  printf 'learnings\n'   > "$TESTDIR/.specfuse/LEARNINGS.template.md"
  printf 'verify\n'      > "$TESTDIR/.specfuse/verification.yml.example"
  printf 'monitor\n'     > "$TESTDIR/.specfuse/monitoring.yml.example"
  printf 'overrides\n'   > "$TESTDIR/.specfuse/monitoring.overrides.yml.example"
  printf 'checklist\n'   > "$TESTDIR/.specfuse/monitoring-secrets-checklist.md"
  printf 'GATE\n'        > "$TESTDIR/.specfuse/templates/GATE.template.md"
  printf 'PLAN\n'        > "$TESTDIR/.specfuse/templates/PLAN.template.md"
  printf 'WU\n'          > "$TESTDIR/.specfuse/templates/WU.template.md"
  printf 'corr\n'        > "$TESTDIR/.specfuse/rules/correlation-ids.md"
  printf 'closedisc\n'   > "$TESTDIR/.specfuse/rules/close-discipline.md"
  printf 'diagnose\n'    > "$TESTDIR/.specfuse/rules/design-for-diagnosis.md"
  printf 'never\n'       > "$TESTDIR/.specfuse/rules/never-touch.md"
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

@test "sync creates a missing discovery link for a skill with no .claude/skills entry" {
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -L "$TESTDIR/.claude/skills/demo" ]
  resolved="$(cd "$TESTDIR/.claude/skills" && cd "$(readlink demo)" && pwd)"
  expected="$(cd "$TESTDIR/.specfuse/skills/demo" && pwd)"
  [ "$resolved" = "$expected" ]
}

@test "sync leaves an existing discovery link byte-identical" {
  before="$(readlink "$TESTDIR/.claude/skills/linked-demo")"
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  after="$(readlink "$TESTDIR/.claude/skills/linked-demo")"
  [ "$before" = "$after" ]
}

@test "sync does not modify or remove an entry resolving outside .specfuse/skills/" {
  before="$(readlink "$TESTDIR/.claude/skills/external-tool")"
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -L "$TESTDIR/.claude/skills/external-tool" ]
  after="$(readlink "$TESTDIR/.claude/skills/external-tool")"
  [ "$before" = "$after" ]
}

@test "sync is idempotent for discovery links (second run creates nothing)" {
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  REPO_ROOT="$TESTDIR" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$output" == *"no missing links"* ]]
}
