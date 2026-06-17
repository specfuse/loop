#!/usr/bin/env bats
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Regression test for issue #56 — every skill must deploy as a real, readable
# SKILL.md in the target, and init then --upgrade must be idempotent.
#
# roadmap-add / roadmap-archive were committed with an INVERTED symlink: the real
# dir lived under .claude/skills/ and .specfuse/skills/<name> was a git symlink
# pointing back into .claude. Consequences: init copied a dangling symlink into
# the target (skill unavailable), and `cp -R` over the existing symlink on
# --upgrade failed ("unlink: Operation not permitted" on macOS), aborting the
# upgrade. The canonical pattern is real-dir-in-.specfuse + a forward discovery
# symlink in .claude (created by wire_claude_code).

setup() {
  REPO="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  TARGET="$(mktemp -d)"
}

teardown() {
  [ -n "$TARGET" ] && rm -rf "$TARGET"
}

# The two skills that were inverted, plus a canonical one as a control.
SKILLS="roadmap-add roadmap-archive arm-gate"

@test "init deploys every skill as a readable SKILL.md in the target" {
  run bash "$REPO/init.sh" "$TARGET"
  [ "$status" -eq 0 ]
  for s in $SKILLS; do
    # -s follows symlinks; a dangling symlink (the #56 bug) is NOT readable.
    [ -s "$TARGET/.specfuse/skills/$s/SKILL.md" ]
  done
}

@test "init then --upgrade is idempotent with skills present" {
  run bash "$REPO/init.sh" "$TARGET"
  [ "$status" -eq 0 ]
  # Re-run upgrade WITHOUT removing skills/ — the #56 bug aborted here.
  run bash "$REPO/init.sh" --upgrade "$TARGET"
  [ "$status" -eq 0 ]
  for s in $SKILLS; do
    [ -s "$TARGET/.specfuse/skills/$s/SKILL.md" ]
  done
}

@test "source repo holds skill content in .specfuse (real), not .claude" {
  # .specfuse is the canonical home; .claude/skills/<name> is a discovery symlink.
  for s in roadmap-add roadmap-archive; do
    [ ! -L "$REPO/.specfuse/skills/$s" ]               # not a symlink
    [ -s "$REPO/.specfuse/skills/$s/SKILL.md" ]        # real, non-empty
    [ -L "$REPO/.claude/skills/$s" ]                   # .claude side IS the symlink
  done
}
