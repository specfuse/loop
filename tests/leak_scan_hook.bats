#!/usr/bin/env bats
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Happy-path test for the leak-scan pre-commit hook (FEAT-2026-0020/T16).
# Stubs leak_scan.py to exit 0 (clean) / 1 (leak) and asserts the hook's exit
# code, with git stubbed via a real temp repo. Per authoring-work-units §11.

setup() {
  TESTDIR="$(mktemp -d)"
  cd "$TESTDIR"
  git init -q
  mkdir -p .specfuse/scripts .specfuse/hooks
  cp "$BATS_TEST_DIRNAME/../.specfuse/hooks/pre-commit" .specfuse/hooks/pre-commit
  chmod +x .specfuse/hooks/pre-commit
}

teardown() {
  rm -rf "$TESTDIR"
}

write_stub() {
  printf 'import sys\nsys.exit(%s)\n' "$1" > .specfuse/scripts/leak_scan.py
}

@test "hook exits 0 when the scanner is clean" {
  write_stub 0
  run .specfuse/hooks/pre-commit
  [ "$status" -eq 0 ]
}

@test "hook exits 1 when the scanner reports a leak" {
  write_stub 1
  run .specfuse/hooks/pre-commit
  [ "$status" -eq 1 ]
}

@test "hook exits 1 when the scanner is missing" {
  rm -f .specfuse/scripts/leak_scan.py
  run .specfuse/hooks/pre-commit
  [ "$status" -eq 1 ]
}
