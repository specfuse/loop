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
  if [ -f "$BATS_TEST_DIRNAME/../scripts/smoke-stamp.sh" ]; then
    cp "$BATS_TEST_DIRNAME/../scripts/smoke-stamp.sh" scripts/smoke-stamp.sh
    chmod +x scripts/smoke-stamp.sh
  fi
  REFS="refs/heads/topic 1111111111111111111111111111111111111111 refs/heads/topic 0000000000000000000000000000000000000000"
}

teardown() {
  rm -rf "$TESTDIR"
}

# The stub records whatever reached its stdin, then exits with $1.
write_smoke_stub() {
  printf '#!/usr/bin/env bash\ntouch "%s/smoke-ran"\ncat > "%s/smoke-stdin"\nexit %s\n' "$TESTDIR" "$TESTDIR" "$1" > scripts/smoke-test.sh
  chmod +x scripts/smoke-test.sh
}

# A real commit, so a ref line can name a sha whose tree the stamp can match.
commit_something() {
  git -c user.name=t -c user.email=t@example.com commit -q --allow-empty -m "c$1"
  git rev-parse HEAD
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

# #3516: git opens the connection before running the hook, so a long smoke run
# in the hook lets the SSH session drop. A tree stamped by a prior smoke run
# makes the hook return at once without running the smoke test.

@test "a stamped tree skips the smoke test" {
  write_smoke_stub 1
  sha="$(commit_something 1)"
  scripts/smoke-stamp.sh record
  run bash -c "printf 'refs/heads/topic %s refs/heads/topic 0000000000000000000000000000000000000000\n' $sha | .specfuse/hooks/pre-push origin url"
  [ "$status" -eq 0 ]
  [ ! -e "$TESTDIR/smoke-ran" ]
}

@test "an unstamped tree still runs the smoke test" {
  write_smoke_stub 0
  sha="$(commit_something 2)"
  run bash -c "printf 'refs/heads/topic %s refs/heads/topic 0000000000000000000000000000000000000000\n' $sha | .specfuse/hooks/pre-push origin url"
  [ "$status" -eq 0 ]
  [ -e "$TESTDIR/smoke-ran" ]
}

@test "a stamp for another tree does not cover a new commit" {
  write_smoke_stub 1
  commit_something 3 > /dev/null
  scripts/smoke-stamp.sh record
  echo change > file.txt && git add file.txt
  git -c user.name=t -c user.email=t@example.com commit -q -m c4
  sha="$(git rev-parse HEAD)"
  run bash -c "printf 'refs/heads/topic %s refs/heads/topic 0000000000000000000000000000000000000000\n' $sha | .specfuse/hooks/pre-push origin url"
  [ "$status" -eq 1 ]
  [ -e "$TESTDIR/smoke-ran" ]
}

@test "a dirty tree is not stamped" {
  commit_something 5 > /dev/null
  echo tracked > tracked.txt && git add tracked.txt
  git -c user.name=t -c user.email=t@example.com commit -q -m c6
  echo edited > tracked.txt
  scripts/smoke-stamp.sh record
  run scripts/smoke-stamp.sh covers HEAD
  [ "$status" -eq 1 ]
}

@test "a branch deletion needs no smoke test" {
  write_smoke_stub 1
  run bash -c "printf '(delete) 0000000000000000000000000000000000000000 refs/heads/topic 1111111111111111111111111111111111111111\n' | .specfuse/hooks/pre-push origin url"
  [ "$status" -eq 0 ]
  [ ! -e "$TESTDIR/smoke-ran" ]
}

