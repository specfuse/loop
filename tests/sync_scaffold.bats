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

# --- #3285: core must be committed before it can be vendored from ------------
#
# The stage above classifies destination-vs-core. It cannot see the case where
# CORE ITSELF is dirty: the loop's copy then legitimately matches core, the run
# reports `unchanged`, and .vendored.json is rewritten with the new hash — so
# the divergence is baselined and this script can never detect it again.
#
# That is how 3194d24 shipped a `verification-discipline.md` the umbrella had
# never seen; it surfaced on the umbrella's publish PR after v0.17.0 was already
# tagged and on PyPI.

git_core() {  # make $TESTDIR/core a git work tree with everything committed
  git -C "$TESTDIR/core" init -q
  git -C "$TESTDIR/core" config user.email t@example.com
  git -C "$TESTDIR/core" config user.name t
  git -C "$TESTDIR/core" add -A
  git -C "$TESTDIR/core" commit -qm core
}

@test "vendoring from a core checkout with an uncommitted vendored file halts" {
  setup_core
  git_core
  # The edit exists only in core's working tree — never committed, so no other
  # consumer of the substrate will ever receive it.
  printf 'verifdisc\nedited in core but not committed\n' \
    > "$TESTDIR/core/rules/verification-discipline.md"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -ne 0 ]
  [[ "$output" == *"rules/verification-discipline.md"* ]]
}

@test "the dirty-core halt does not vendor the uncommitted content" {
  setup_core
  git_core
  printf 'verifdisc\nedited in core but not committed\n' \
    > "$TESTDIR/core/rules/verification-discipline.md"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -ne 0 ]
  # Nothing uncommitted reached the loop, and no baseline was written for it.
  [ ! -f "$TESTDIR/.specfuse/rules/verification-discipline.md" ] \
    || ! grep -q "not committed" "$TESTDIR/.specfuse/rules/verification-discipline.md"
}

@test "a committed core edit vendors normally" {
  setup_core
  git_core
  printf 'verifdisc\nlanded upstream\n' \
    > "$TESTDIR/core/rules/verification-discipline.md"
  git -C "$TESTDIR/core" commit -qam "core moves forward"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$(cat "$TESTDIR/.specfuse/rules/verification-discipline.md")" == *"landed upstream"* ]]
}

@test "a dirty file outside the vendored set does not block the sync" {
  setup_core
  git_core
  # Unrelated umbrella work in progress must not stop the loop from vendoring.
  printf 'scratch\n' > "$TESTDIR/core/UNRELATED.md"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
}

@test "a non-git core is vendored from as before" {
  # An installed copy has no git metadata; the check cannot be made and this
  # stage already degrades rather than failing when it cannot verify.
  setup_core
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$(cat "$TESTDIR/.specfuse/rules/verification-discipline.md")" == *"verifdisc"* ]]
}

# --- #3287: core must be PUSHED before it can be vendored from ---------------
#
# #3285 closed the uncommitted case. A commit that exists only in the local core
# checkout still reaches the loop the same way: the loop ships substrate no
# other consumer has, and .vendored.json baselines it out of detection. Narrower
# window — it takes a commit rather than a stray edit — but the same failure and
# the same late detection on the umbrella's publish PR.
#
# Answerable from local refs (`@{u}..HEAD`); a sync script does not reach the
# network to find out.

git_core_pushed() {  # core is a git work tree with an upstream, fully pushed
  git -C "$TESTDIR/core" init -q -b main
  git -C "$TESTDIR/core" config user.email t@example.com
  git -C "$TESTDIR/core" config user.name t
  git -C "$TESTDIR/core" add -A
  git -C "$TESTDIR/core" commit -qm core
  git init -q --bare "$TESTDIR/core-remote"
  git -C "$TESTDIR/core" remote add origin "$TESTDIR/core-remote"
  git -C "$TESTDIR/core" push -q -u origin main
}

@test "vendoring from a core commit that was never pushed halts" {
  setup_core
  git_core_pushed
  # Committed, so the #3285 dirty check is satisfied — and still reachable by
  # nobody but this checkout.
  printf 'verifdisc\ncommitted in core but never pushed\n' \
    > "$TESTDIR/core/rules/verification-discipline.md"
  git -C "$TESTDIR/core" commit -qam "local only"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -ne 0 ]
  [[ "$output" == *"rules/verification-discipline.md"* ]]
}

@test "the unpushed halt does not vendor the unpushed content" {
  setup_core
  git_core_pushed
  printf 'verifdisc\ncommitted in core but never pushed\n' \
    > "$TESTDIR/core/rules/verification-discipline.md"
  git -C "$TESTDIR/core" commit -qam "local only"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -ne 0 ]
  [ ! -f "$TESTDIR/.specfuse/rules/verification-discipline.md" ] \
    || ! grep -q "never pushed" "$TESTDIR/.specfuse/rules/verification-discipline.md"
}

@test "a pushed core commit vendors normally" {
  setup_core
  git_core_pushed
  printf 'verifdisc\nlanded upstream\n' \
    > "$TESTDIR/core/rules/verification-discipline.md"
  git -C "$TESTDIR/core" commit -qam "core moves forward"
  git -C "$TESTDIR/core" push -q origin main
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$(cat "$TESTDIR/.specfuse/rules/verification-discipline.md")" == *"landed upstream"* ]]
}

@test "an unpushed commit outside the vendored set does not block the sync" {
  setup_core
  git_core_pushed
  printf 'scratch\n' > "$TESTDIR/core/UNRELATED.md"
  git -C "$TESTDIR/core" add -A
  git -C "$TESTDIR/core" commit -qm "unrelated work in progress"
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
}

@test "a core branch with no upstream is vendored from as before" {
  # Nothing to compare HEAD against, so the check cannot be made. Same degrade
  # posture as a non-git core: vendor, do not fail.
  setup_core
  git_core          # committed, but no remote and no tracking branch
  REPO_ROOT="$TESTDIR" SPECFUSE_CORE="$TESTDIR/core" run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$(cat "$TESTDIR/.specfuse/rules/verification-discipline.md")" == *"verifdisc"* ]]
}
