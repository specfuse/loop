#!/usr/bin/env bats
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Happy-path tests for the init.sh thin shim (FEAT-2026-0026/T08).
# Stubs the `specfuse` CLI via PATH override to capture call shape without
# running the real CLI. Per authoring-work-units §11.
#
# RED on HEAD: current init.sh runs its own copy/overlay logic and never
# invokes `specfuse`, so the CALL_LOG-based assertions below fail.
# GREEN after this WU rewrites init.sh to delegate.

SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/init.sh"

setup() {
  TESTDIR="$(mktemp -d)"

  # Stub bin — records all positional args to CALL_LOG and exits 0.
  STUB_BIN="$TESTDIR/stub-bin"
  CALL_LOG="$TESTDIR/specfuse.log"
  mkdir -p "$STUB_BIN"
  cat > "$STUB_BIN/specfuse" <<'STUB'
#!/usr/bin/env bash
echo "$*" >> "${CALL_LOG}"
exit 0
STUB
  chmod +x "$STUB_BIN/specfuse"
  export CALL_LOG
  export PATH="$STUB_BIN:$PATH"

  # Minimal target directory (init.sh validates it is a directory).
  TARGET="$TESTDIR/target"
  mkdir -p "$TARGET"
}

teardown() {
  rm -rf "$TESTDIR"
}

@test "init mode: delegates to 'specfuse init <target>'" {
  run bash "$SCRIPT" "$TARGET"
  [ "$status" -eq 0 ]
  grep -qF "init $TARGET" "$CALL_LOG"
}

@test "upgrade mode: delegates to 'specfuse upgrade <target>'" {
  run bash "$SCRIPT" --upgrade "$TARGET"
  [ "$status" -eq 0 ]
  grep -qF "upgrade $TARGET" "$CALL_LOG"
}

@test "upgrade --dry-run: forwards --dry-run flag to specfuse upgrade" {
  run bash "$SCRIPT" --upgrade --dry-run "$TARGET"
  [ "$status" -eq 0 ]
  grep -qF "upgrade" "$CALL_LOG"
  grep -qF -- "--dry-run" "$CALL_LOG"
}

@test "specfuse absent: exits non-zero with pip install hint" {
  EMPTY_BIN="$(mktemp -d)"
  run env PATH="$EMPTY_BIN:/usr/bin:/bin" bash "$SCRIPT" "$TARGET"
  rm -rf "$EMPTY_BIN"
  [ "$status" -ne 0 ]
  [[ "$output" == *"pip install specfuse"* ]]
}

@test "no target: exits non-zero with usage" {
  run bash "$SCRIPT"
  [ "$status" -ne 0 ]
}
