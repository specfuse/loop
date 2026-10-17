#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Records and checks "the smoke test passed on this exact tree" stamps, so the
# pre-push hook can skip a smoke run that already happened (#3516).
#
# git opens the connection to the remote before it runs a pre-push hook; a
# ~4-minute smoke run inside the hook let the idle SSH session drop, and git
# then died with SIGPIPE (exit 141) after "smoke test: OK" without pushing.
# Running the smoke test before `git push` and stamping the tree makes the hook
# instant, so nothing sits idle on the connection.
#
# Stamps are tree hashes, so one stamp file is shared by every worktree of the
# clone: the same tree is the same tested content wherever it is checked out.
#
#   smoke-stamp.sh record          stamp HEAD's tree, only if no tracked file
#                                  differs from HEAD (a dirty run tested
#                                  something other than the commit)
#   smoke-stamp.sh covers SHA...   exit 0 iff every SHA's tree is stamped

set -euo pipefail

stamp_file() {
  printf '%s/specfuse-smoke-pass' "$(git rev-parse --git-common-dir)"
}

case "${1:-}" in
  record)
    if ! git diff --quiet HEAD -- 2>/dev/null; then
      echo "smoke-stamp: tracked changes differ from HEAD — not stamping" >&2
      exit 0
    fi
    file="$(stamp_file)"
    git rev-parse 'HEAD^{tree}' >> "$file"
    # Keep the file small: the last 200 stamps are plenty.
    tail -n 200 "$file" > "$file.tmp" && mv "$file.tmp" "$file"
    ;;
  covers)
    shift
    file="$(stamp_file)"
    [ -f "$file" ] || exit 1
    for sha in "$@"; do
      tree="$(git rev-parse --verify --quiet "${sha}^{tree}")" || exit 1
      grep -qxF "$tree" "$file" || exit 1
    done
    ;;
  *)
    echo "usage: smoke-stamp.sh record | covers SHA..." >&2
    exit 2
    ;;
esac
