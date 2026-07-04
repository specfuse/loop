#!/usr/bin/env bats
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Regression test for issue #56 — skills must live in the canonical source layout:
# a REAL dir under .specfuse/skills/<name>/ plus a FORWARD discovery symlink
# .claude/skills/<name> -> ../../.specfuse/skills/<name> (created by wire_claude_code).
#
# roadmap-add / roadmap-archive were once committed with an INVERTED symlink (real
# dir under .claude/skills/, .specfuse/skills/<name> a git symlink back into
# .claude), which produced dangling symlinks and aborted `cp -R` on --upgrade.
#
# NOTE (issue #121): earlier tests here asserted `init.sh` DEPLOYS skills into a
# target. That is obsolete — since FEAT-2026-0026 `init.sh` is a thin shim to
# `specfuse init`, and skill delivery moved to the Claude Code plugin
# (`/plugin install specfuse@specfuse`); the pip scaffold deliberately does NOT
# copy skills (see docs/getting-started.md). Those tests were silently red and not
# run in CI. They are retired; this file now guards only the live invariant — the
# source-repo symlink layout the plugin publishes from — and IS wired into CI
# (scripts/smoke-test.sh) and the driver gate set (.specfuse/verification.yml).

setup() {
  REPO="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
}

@test "source repo holds skill content in .specfuse (real), not .claude" {
  # .specfuse is the canonical home; .claude/skills/<name> is a forward discovery
  # symlink that must RESOLVE to the real, non-empty SKILL.md (a dangling symlink
  # is the #56 failure mode).
  for s in roadmap-add roadmap-archive arm-gate; do
    [ ! -L "$REPO/.specfuse/skills/$s" ]                # .specfuse side is a real dir
    [ -s "$REPO/.specfuse/skills/$s/SKILL.md" ]         # real, non-empty content
    [ -L "$REPO/.claude/skills/$s" ]                    # .claude side IS the symlink
    [ -s "$REPO/.claude/skills/$s/SKILL.md" ]           # ...and it resolves (not dangling)
  done
}
