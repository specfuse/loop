#!/usr/bin/env bats
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Regression test for issue #153: scripts/install-hooks.sh and scripts/setup.sh
# each set core.hooksPath to a DIFFERENT directory, and each directory holds a
# DIFFERENT hook type. core.hooksPath is single-valued, so whichever installer
# runs last silently disables the other's hook.
#
# The invariant these tests assert: after running the installers (in EITHER
# order, or either one alone), the active core.hooksPath names a directory that
# holds BOTH the pre-push and the pre-commit hook, executable. Before the fix,
# every case below leaves one hook orphaned outside the active hooksPath.

setup() {
  TESTDIR="$(mktemp -d)"
  cd "$TESTDIR"
  git init -q

  # Mirror the tracked layout the installers act on. Copy from whichever
  # location each hook currently lives in so the test survives the fix's move.
  mkdir -p scripts .specfuse/scripts .specfuse/hooks .githooks
  cp "$BATS_TEST_DIRNAME/../scripts/install-hooks.sh" scripts/
  cp "$BATS_TEST_DIRNAME/../scripts/setup.sh" scripts/
  chmod +x scripts/install-hooks.sh scripts/setup.sh

  if [ -f "$BATS_TEST_DIRNAME/../.githooks/pre-push" ]; then
    cp "$BATS_TEST_DIRNAME/../.githooks/pre-push" .githooks/pre-push
  fi
  if [ -f "$BATS_TEST_DIRNAME/../.specfuse/hooks/pre-push" ]; then
    cp "$BATS_TEST_DIRNAME/../.specfuse/hooks/pre-push" .specfuse/hooks/pre-push
  fi
  if [ -f "$BATS_TEST_DIRNAME/../.specfuse/hooks/pre-commit" ]; then
    cp "$BATS_TEST_DIRNAME/../.specfuse/hooks/pre-commit" .specfuse/hooks/pre-commit
  fi

  # setup.sh verifies the guard by running leak_scan.py --all; stub it clean so
  # the installer under test doesn't fail for an unrelated reason.
  printf 'import sys\nsys.exit(0)\n' > .specfuse/scripts/leak_scan.py
}

teardown() {
  rm -rf "$TESTDIR"
}

# Assert the active core.hooksPath holds both hook types, executable.
assert_both_hooks_active() {
  local hp
  hp="$(git config core.hooksPath)"
  [ -n "$hp" ]
  [ -x "$hp/pre-push" ]
  [ -x "$hp/pre-commit" ]
}

@test "install-hooks.sh then setup.sh: both hooks active under hooksPath" {
  bash scripts/install-hooks.sh
  bash scripts/setup.sh
  assert_both_hooks_active
}

@test "setup.sh then install-hooks.sh: both hooks active under hooksPath" {
  bash scripts/setup.sh
  bash scripts/install-hooks.sh
  assert_both_hooks_active
}

@test "install-hooks.sh alone: both hooks active under hooksPath" {
  bash scripts/install-hooks.sh
  assert_both_hooks_active
}

@test "setup.sh alone: both hooks active under hooksPath" {
  bash scripts/setup.sh
  assert_both_hooks_active
}
