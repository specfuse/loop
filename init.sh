#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# init.sh — scaffold the Specfuse Loop into a target single-repo project.
#
# Two modes:
#   ./init.sh /path/to/target-repo
#       INIT mode (default). Copies the canonical .specfuse/ scaffold into
#       a target that does NOT yet have a .specfuse/ directory. Refuses if
#       one already exists — use --upgrade for that case.
#
#   ./init.sh --upgrade [--dry-run] /path/to/target-repo
#       UPGRADE mode. Updates the versioned scaffold IN PLACE (scripts/,
#       templates/, rules/, skills/, README.md, verification.yml.example).
#       Leaves user-authored files alone (LEARNINGS.md, verification.yml,
#       roadmap.md, features/). Files the target added that we don't ship
#       (e.g. custom skills, custom rules) are also preserved — we overlay,
#       we don't replace the tree.
#
#       --dry-run prints what WOULD change without writing.
#
# After running, in the target repo:
#   - edit .specfuse/verification.yml so the `code` gates match your stack
#     (and your branch protection, if any)
#   - author your first feature folder under .specfuse/features/ from the
#     templates in .specfuse/templates/
#   - python .specfuse/scripts/loop.py --dry-run

set -euo pipefail

# --- argument parsing ----------------------------------------------------- #

UPGRADE=0
DRY_RUN=0
TARGET=""

usage() {
  cat >&2 <<'USAGE'
usage:
  ./init.sh                     /path/to/target-repo
  ./init.sh --upgrade [--dry-run] /path/to/target-repo

INIT mode (default): scaffold into a target without an existing .specfuse/.
UPGRADE mode: overlay versioned-scaffold updates onto an existing .specfuse/,
              preserving user-authored files (LEARNINGS.md, verification.yml,
              roadmap.md, features/) and any files the user added.
--dry-run     With --upgrade, list what would change without writing.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --upgrade)   UPGRADE=1; shift ;;
    --dry-run)   DRY_RUN=1; shift ;;
    -h|--help)   usage; exit 0 ;;
    --)          shift; TARGET="${1:-}"; shift || true; break ;;
    -*)          echo "error: unknown flag '$1'" >&2; usage; exit 2 ;;
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
if [[ ! -d "$TARGET" ]]; then
  echo "error: target '$TARGET' is not a directory" >&2
  exit 2
fi
if [[ $DRY_RUN -eq 1 && $UPGRADE -eq 0 ]]; then
  echo "error: --dry-run only applies to --upgrade" >&2
  exit 2
fi

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.specfuse"
DEST="$TARGET/.specfuse"

# The versioned scaffold — we own these; --upgrade overlays them.
VERSIONED_ITEMS=(scripts templates rules skills verification.yml.example README.md)

# User-authored — we ship seeds in INIT mode but NEVER touch on --upgrade.
USER_AUTHORED=(LEARNINGS.md verification.yml roadmap.md features)

# --- helpers -------------------------------------------------------------- #

# overlay_item <item> — copy SRC_DIR/<item> onto DEST/<item>, additively.
# Files in DEST that aren't in SRC are preserved; files in both are
# overwritten. Honors $DRY_RUN.
overlay_item() {
  local item="$1"
  local src="$SRC_DIR/$item"
  local dst="$DEST/$item"
  if [[ ! -e "$src" ]]; then
    return
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    if [[ -d "$src" ]]; then
      while IFS= read -r f; do
        local rel="${f#$src/}"
        local verb="update"
        [[ -e "$dst/$rel" ]] || verb="add"
        echo "  would $verb: ${dst#$TARGET/}/$rel"
      done < <(find "$src" -type f -not -name '__pycache__' -not -path '*/__pycache__/*')
    else
      local verb="update"
      [[ -e "$dst" ]] || verb="add"
      echo "  would $verb: ${dst#$TARGET/}"
    fi
    return
  fi
  if [[ -d "$src" ]]; then
    mkdir -p "$dst"
    # cp -r src/. dst/ overlays contents without nesting; preserves dst extras.
    cp -R "$src/." "$dst/"
  else
    cp "$src" "$dst"
  fi
}

# --- INIT mode ------------------------------------------------------------ #

if [[ $UPGRADE -eq 0 ]]; then
  if [[ -e "$DEST" ]]; then
    echo "error: '$DEST' already exists." >&2
    echo "  To update the versioned scaffold in place, run:" >&2
    echo "      ./init.sh --upgrade $TARGET" >&2
    echo "  (or --upgrade --dry-run $TARGET to preview)" >&2
    exit 1
  fi

  mkdir -p "$DEST"
  for item in "${VERSIONED_ITEMS[@]}"; do
    cp -r "$SRC_DIR/$item" "$DEST/$item"
  done

  # Strip any compiled-Python noise that may have been copied with scripts/.
  find "$DEST" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

  # Seed user-authored files (INIT only — never on --upgrade).
  cp "$SRC_DIR/LEARNINGS.md" "$DEST/LEARNINGS.md"
  cp "$DEST/verification.yml.example" "$DEST/verification.yml"
  cp "$SRC_DIR/roadmap.template.md" "$DEST/roadmap.md"
  mkdir -p "$DEST/features"

  echo "Scaffolded Specfuse Loop into $DEST"
  echo

# --- UPGRADE mode --------------------------------------------------------- #

else
  if [[ ! -d "$DEST" ]]; then
    echo "error: '$DEST' does not exist — nothing to upgrade." >&2
    echo "  To set up a new project, run without --upgrade:" >&2
    echo "      ./init.sh $TARGET" >&2
    exit 1
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY RUN — no files will be written."
    echo "Would upgrade versioned scaffold in $DEST:"
    echo
  else
    echo "Upgrading versioned scaffold in $DEST"
    echo "(user-authored files preserved: LEARNINGS.md, verification.yml, roadmap.md, features/)"
    echo
  fi

  for item in "${VERSIONED_ITEMS[@]}"; do
    overlay_item "$item"
  done

  if [[ $DRY_RUN -eq 0 ]]; then
    find "$DEST" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
    echo
    echo "Upgrade complete. Preserved user-authored files:"
    for f in "${USER_AUTHORED[@]}"; do
      if [[ -e "$DEST/$f" ]]; then
        echo "  $DEST/$f"
      fi
    done
    if git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      echo
      echo "Tip: review the update with"
      echo "    git -C $TARGET diff -- .specfuse"
      echo "and revert any clobbered local customizations to versioned files."
    else
      echo
      echo "Tip: this directory is not a git working tree, so any local edits"
      echo "you had to versioned files (rules/, skills/, etc.) have been"
      echo "overwritten without a diff trail. Consider tracking .specfuse/"
      echo "with git before the next upgrade."
    fi
  fi
  echo
fi

# --- gitignore guard (both modes) ---------------------------------------- #
# The loop uses git as its state backend (status writes via frontmatter edits,
# the squashed per-WU commit, and the `doc` gate's `git diff` check). If
# `.specfuse/` is gitignored in the target repo, those writes are invisible
# to git and the loop silently misbehaves. Warn loudly.
if [[ $DRY_RUN -eq 0 ]]; then
  if git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if git -C "$TARGET" check-ignore -q .specfuse 2>/dev/null; then
      echo "WARNING: .specfuse/ is gitignored in $TARGET — the loop will not work."
      echo "  The driver uses git as its state backend (per-WU status writes, one"
      echo "  squashed commit per work unit, and the 'doc' gate's git-diff check)."
      echo "  With .specfuse/ ignored, those writes are invisible to git and the"
      echo "  loop misbehaves. Un-ignore .specfuse/ in your .gitignore. You may"
      echo "  keep the runtime noise paths ignored, e.g.:"
      echo "      !.specfuse/"
      echo "      .specfuse/**/work/"
      echo
    fi
  fi
fi

# --- closing instructions (INIT only) ------------------------------------ #
if [[ $UPGRADE -eq 0 ]]; then
  echo "Next:"
  echo "  1. cd $TARGET"
  echo "  2. edit .specfuse/verification.yml  (match the 'code' gates to your stack)"
  echo "  3. author your first feature folder under .specfuse/features/ from .specfuse/templates/"
  echo "  4. python .specfuse/scripts/loop.py --dry-run"
  echo
  echo "The loop driver and linter have no runtime dependencies — stock Python 3"
  echo "is all you need. (You'll need whatever tools your gates in verification.yml"
  echo "call, of course — pytest, ruff, etc. — installed however your stack does it.)"
  echo
  echo "Optional — to auto-draft .specfuse/verification.yml from this repo's CI and"
  echo "tooling for your review (instead of editing the example by hand in step 2):"
  echo "    claude                     # start an interactive session in this repo"
  echo "    > run the derive-verification skill"
  echo "    # (or, equivalently, paste the contents of"
  echo "    #  .specfuse/skills/derive-verification/PROMPT.md into the session)"
  echo "Run INTERACTIVELY — the skill asks batched questions (coverage threshold,"
  echo "canonical test command, which gates to add/drop) and needs your answers."
  echo "Piping the prompt via 'claude -p < ...' consumes stdin so the skill cannot"
  echo "ask, and falls back to a gap-riddled non-interactive draft. The skill"
  echo "drafts; it does not write the file. Review and copy yourself."
fi
