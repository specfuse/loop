#!/usr/bin/env bats
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# #3491: git writes one "<local ref> <local sha> <remote ref> <remote sha>"
# line per ref to a pre-push hook's stdin. The hook must consume that list
# itself and give the smoke test no stdin; a hook that hands git's pipe to a
# long-running child left git dying with SIGPIPE (exit 141) after a green
# smoke test, so the push silently never happened. smoke-test.sh is stubbed.

setup() {
  TESTDIR="$(mktemp -d)"
  cd "$TESTDIR"
  git init -q
  mkdir -p .specfuse/hooks scripts
  cp "$BATS_TEST_DIRNAME/../.specfuse/hooks/pre-push" .specfuse/hooks/pre-push
  chmod +x .specfuse/hooks/pre-push
  REFS="refs/heads/topic 1111111111111111111111111111111111111111 refs/heads/topic 0000000000000000000000000000000000000000"
}

teardown() {
  rm -rf "$TESTDIR"
}

# The stub records whatever reached its stdin, then exits with $1.
write_smoke_stub() {
  printf '#!/usr/bin/env bash\ncat > "%s/smoke-stdin"\nexit %s\n' "$TESTDIR" "$1" > scripts/smoke-test.sh
  chmod +x scripts/smoke-test.sh
}

@test "hook consumes git's ref list instead of passing it to the smoke test" {
  write_smoke_stub 0
  run bash -c "printf '%s\n' \"$REFS\" | .specfuse/hooks/pre-push origin git@example.com:acme/repo.git"
  [ "$status" -eq 0 ]
  [ ! -s "$TESTDIR/smoke-stdin" ]
}

@test "hook propagates a failing smoke test" {
  write_smoke_stub 1
  run bash -c "printf '%s\n' \"$REFS\" | .specfuse/hooks/pre-push origin git@example.com:acme/repo.git"
  [ "$status" -eq 1 ]
}

@test "hook exits 0 with a passing smoke test and empty stdin" {
  write_smoke_stub 0
  run bash -c ".specfuse/hooks/pre-push origin git@example.com:acme/repo.git < /dev/null"
  [ "$status" -eq 0 ]
}
