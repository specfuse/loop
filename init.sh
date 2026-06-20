#!/usr/bin/env bash
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# init.sh — thin shim: delegates to the specfuse pip CLI.
#
# This is the v1.0 legacy install path; scheduled for removal in v1.1.
# The bash copy/overlay logic now lives in the specfuse package (scaffold.py).
#
# Two modes (same surface as the old script):
#   ./init.sh [--] /path/to/target-repo
#       Delegates to: specfuse init <target>
#
#   ./init.sh --upgrade [--dry-run] [--] /path/to/target-repo
#       Delegates to: specfuse upgrade [--dry-run] <target>

set -euo pipefail

# --- deprecation banner ------------------------------------------------------- #

deprecation_banner() {
  cat <<'BANNER'

────────────────────────────────────────────────────────────────────────────
NOTE: init.sh is the legacy install path (v1.0) and will be removed in v1.1.
The forward path:
  • Driver:  pip install specfuse-loop      (run `specfuse-loop` instead of
             python .specfuse/scripts/loop.py)
  • CLI:     pip install specfuse           (`specfuse upgrade` / `specfuse init`)
  • Skills:  /plugin marketplace add specfuse/specfuse
             /plugin install specfuse@specfuse     (skills become /specfuse:*)
Your `.specfuse/` state (features, LEARNINGS, roadmap, verification.yml) is
unaffected — only how the code + skills are delivered changes.
────────────────────────────────────────────────────────────────────────────
BANNER
}

# --- argument parsing --------------------------------------------------------- #

UPGRADE=0
DRY_RUN=0
TARGET=""

usage() {
  cat >&2 <<'USAGE'
usage:
  ./init.sh                       /path/to/target-repo
  ./init.sh --upgrade [--dry-run] /path/to/target-repo

INIT mode (default): scaffold into a target without an existing .specfuse/.
UPGRADE mode: overlay versioned-scaffold updates onto an existing .specfuse/,
              preserving user-authored files and any files you added.
--dry-run     With --upgrade, preview what would change without writing.

Both modes delegate to the specfuse pip CLI (pip install specfuse).
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --upgrade)  UPGRADE=1; shift ;;
    --dry-run)  DRY_RUN=1; shift ;;
    -h|--help)  usage; exit 0 ;;
    --)         shift; TARGET="${1:-}"; shift || true; break ;;
    -*)         echo "error: unknown flag '$1'" >&2; usage; exit 2 ;;
    *)
      if [[ -z "$TARGET" ]]; then
        TARGET="$1"; shift
      else
        echo "error: unexpected extra argument '$1'" >&2; usage; exit 2
      fi
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  usage; exit 2
fi

# --- delegate to the specfuse pip CLI ----------------------------------------- #

if ! command -v specfuse >/dev/null 2>&1; then
  echo "error: 'specfuse' not found on PATH." >&2
  echo "  Install it with: pip install specfuse" >&2
  exit 1
fi

deprecation_banner

if [[ $UPGRADE -eq 1 ]]; then
  if [[ $DRY_RUN -eq 1 ]]; then
    exec specfuse upgrade --dry-run "$TARGET"
  else
    exec specfuse upgrade "$TARGET"
  fi
else
  exec specfuse init "$TARGET"
fi
