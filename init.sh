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

# Detect ci-check.sh in the target and write .specfuse/verification.yml.
# Sets CI_CHECK_PATH to the relative path found (empty if none).
# Reads globals: $TARGET, $SRC_DIR, $DEST.
seed_verification_yml() {
  CI_CHECK_PATH=""
  for candidate in ci-check.sh script/ci-check.sh scripts/ci-check.sh; do
    if [[ -f "$TARGET/$candidate" ]]; then
      CI_CHECK_PATH="$candidate"
      break
    fi
  done
  if [[ -n "$CI_CHECK_PATH" ]]; then
    cat > "$DEST/verification.yml" <<EOF
# .specfuse/verification.yml — auto-configured from $CI_CHECK_PATH
#
# $CI_CHECK_PATH was detected in the repo. The code gate delegates
# to it so your Specfuse verification stays in sync with CI automatically.
# Replace or extend if you need gate-level granularity (e.g. split tests
# from lint so the driver can report which check failed).
#
# See verification.yml.example for the full field reference.

code:
  - name: ci-check
    command: "bash $CI_CHECK_PATH"

# Reflective units (retrospective, lessons, docs): the artifact exists /
# something changed. Tighten as you like.
doc:
  - name: artifact-changed
    command: "git -C {feature_dir} diff --quiet HEAD -- . && exit 1 || exit 0"

# plan-next: structural integrity of what it drafted.
plannext:
  - name: plan-lint
    command: "python .specfuse/scripts/lint_plan.py {feature_dir}"
EOF
  else
    cp "$DEST/verification.yml.example" "$DEST/verification.yml"
  fi
}

# Claude Code wiring: make the loop's scaffold-shipped skills discoverable,
# import the binding rules into session context, and allowlist the loop
# scripts so dispatch isn't gated on per-invocation permission prompts.
#
# Claude Code only auto-discovers skills directly under `.claude/skills/`
# (not arbitrary subdirs), so we bridge with relative symlinks from there
# into `.specfuse/skills/`. Binding rules under `.specfuse/rules/` are
# imported into `.claude/CLAUDE.md` via Claude Code's `@path` syntax so
# they load at session start.
#
# Idempotent and conservative: existing user files are NEVER overwritten;
# we create-if-missing, and if a file already exists without our additions
# we print a paste-in snippet rather than mutate it. Honors $DRY_RUN.
wire_claude_code() {
  local claude_dir="$TARGET/.claude"
  local rel_claude="${claude_dir#$TARGET/}"  # ".claude" for printing

  # --- 1. symlinks for skill discovery ---
  local linked=0 already=0
  local want=()
  for d in "$DEST/skills"/*/; do
    [[ -d "$d" ]] || continue
    local name=$(basename "$d")
    local link="$claude_dir/skills/$name"
    if [[ -e "$link" || -L "$link" ]]; then
      already=$((already + 1))
    else
      want+=("$name")
      linked=$((linked + 1))
    fi
  done
  if [[ $DRY_RUN -eq 1 ]]; then
    if [[ $linked -gt 0 ]]; then
      echo "  would link $linked skill(s) into $rel_claude/skills/:"
      for n in "${want[@]}"; do
        echo "    $rel_claude/skills/$n -> ../../.specfuse/skills/$n"
      done
    fi
    [[ $already -gt 0 ]] && echo "  $rel_claude/skills/: $already already present (left alone)"
  else
    mkdir -p "$claude_dir/skills"
    if [[ $linked -gt 0 ]]; then
      for n in "${want[@]}"; do
        ln -s "../../.specfuse/skills/$n" "$claude_dir/skills/$n"
      done
      echo "Claude Code skills: linked $linked into $rel_claude/skills/."
    elif [[ $already -gt 0 ]]; then
      echo "Claude Code skills: $rel_claude/skills/ already has all $already (left alone)."
    fi
  fi

  # --- 2. CLAUDE.md — @import binding rules ---
  local claude_md="$claude_dir/CLAUDE.md"
  local rel_md="$rel_claude/CLAUDE.md"
  local rules_block='## Specfuse binding rules (read before any work-unit dispatch)
@.specfuse/rules/result-contract.md
@.specfuse/rules/correlation-ids.md
@.specfuse/rules/never-touch.md
@.specfuse/rules/security-boundaries.md'
  if [[ ! -f "$claude_md" ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "  would create $rel_md with the binding-rules @import block"
    else
      mkdir -p "$claude_dir"
      printf '# Project notes\n\n%s\n' "$rules_block" > "$claude_md"
      echo "Claude Code rules: created $rel_md with the binding-rules @import block."
    fi
  elif grep -q '@\.specfuse/rules/' "$claude_md" 2>/dev/null; then
    [[ $DRY_RUN -eq 1 ]] && echo "  $rel_md already imports the binding rules" \
                         || echo "Claude Code rules: $rel_md already imports the binding rules — left alone."
  else
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "  $rel_md exists but doesn't import the binding rules (would print paste-in snippet)"
    else
      echo "Claude Code rules: $rel_md exists but doesn't import the binding rules."
      echo "  Append this block to wire them up:"
      printf '%s\n' "$rules_block" | sed 's/^/    /'
    fi
  fi

  # --- 3. settings.json — permissions allowlist ---
  local settings="$claude_dir/settings.json"
  local rel_settings="$rel_claude/settings.json"
  if [[ ! -f "$settings" ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "  would create $rel_settings with the loop-script allowlist"
    else
      mkdir -p "$claude_dir"
      cat > "$settings" <<'EOF'
{
  "permissions": {
    "allow": [
      "Bash(python3 .specfuse/scripts/loop.py:*)",
      "Bash(python3 .specfuse/scripts/lint_plan.py:*)"
    ]
  }
}
EOF
      echo "Claude Code permissions: created $rel_settings with the loop-script allowlist."
    fi
  elif grep -q '\.specfuse/scripts/loop\.py' "$settings" 2>/dev/null; then
    [[ $DRY_RUN -eq 1 ]] && echo "  $rel_settings already allows the loop scripts" \
                         || echo "Claude Code permissions: $rel_settings already allows the loop scripts — left alone."
  else
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "  $rel_settings exists but doesn't allow the loop scripts (would print paste-in snippet)"
    else
      echo "Claude Code permissions: $rel_settings exists but doesn't allow the loop scripts."
      echo "  Add these to its permissions.allow array:"
      echo '    "Bash(python3 .specfuse/scripts/loop.py:*)",'
      echo '    "Bash(python3 .specfuse/scripts/lint_plan.py:*)"'
    fi
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
  CI_CHECK_PATH=""
  seed_verification_yml
  cp "$SRC_DIR/roadmap.template.md" "$DEST/roadmap.md"
  mkdir -p "$DEST/features"

  echo "Scaffolded Specfuse Loop into $DEST"
  echo
  wire_claude_code
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

  # Seed any user-authored files that are missing — happens when the
  # orchestrator or a partial init created .specfuse/ bare.
  if [[ $DRY_RUN -eq 1 ]]; then
    [[ ! -f "$DEST/LEARNINGS.md" ]]     && echo "  would seed missing: .specfuse/LEARNINGS.md"
    [[ ! -f "$DEST/verification.yml" ]] && echo "  would seed missing: .specfuse/verification.yml"
    [[ ! -f "$DEST/roadmap.md" ]]       && echo "  would seed missing: .specfuse/roadmap.md"
    [[ ! -d "$DEST/features" ]]         && echo "  would seed missing: .specfuse/features/"
    true  # ensure set -e doesn't trigger on the last [[ ]] above being false
  else
    CI_CHECK_PATH=""
    if [[ ! -f "$DEST/LEARNINGS.md" ]]; then
      cp "$SRC_DIR/LEARNINGS.md" "$DEST/LEARNINGS.md"
      echo "Seeded missing: .specfuse/LEARNINGS.md"
    fi
    if [[ ! -f "$DEST/verification.yml" ]]; then
      seed_verification_yml
      echo "Seeded missing: .specfuse/verification.yml"
    fi
    if [[ ! -f "$DEST/roadmap.md" ]]; then
      cp "$SRC_DIR/roadmap.template.md" "$DEST/roadmap.md"
      echo "Seeded missing: .specfuse/roadmap.md"
    fi
    if [[ ! -d "$DEST/features" ]]; then
      mkdir -p "$DEST/features"
      echo "Seeded missing: .specfuse/features/"
    fi
  fi

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

  # Claude Code wiring — symlinks, CLAUDE.md, settings allowlist.
  # In dry-run, this lists what would change without writing.
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "Claude Code wiring (would happen):"
  fi
  wire_claude_code
  echo

  # --- feature health report ---------------------------------------------- #
  # Lint every existing feature folder against the new scaffold's structural
  # contract (the linter that --upgrade is bringing in). Useful both live
  # ("which features still pass post-upgrade?") and dry-run ("which features
  # WOULD break if I upgrade?") — we run the SOURCE linter against the
  # destination's features in both cases, so the answer doesn't depend on
  # whether the overlay has happened yet.
  shopt -s nullglob
  feature_dirs=("$DEST"/features/*/)
  shopt -u nullglob
  if [[ ${#feature_dirs[@]} -gt 0 ]]; then
    echo "Feature health (each feature lint-checked against the new scaffold):"
    any_failed=0
    for f in "${feature_dirs[@]}"; do
      name=$(basename "$f")
      if [[ ! -f "$f/PLAN.md" ]]; then
        echo "  SKIP $name  (no PLAN.md — not a feature folder)"
        continue
      fi
      if output=$(python3 "$SRC_DIR/scripts/lint_plan.py" "$f" 2>&1); then
        echo "  OK   $name"
      else
        echo "  FAIL $name"
        echo "$output" | sed 's/^/       /'
        any_failed=1
      fi
    done
    if [[ $any_failed -eq 1 ]]; then
      echo
      echo "One or more features failed structural lint against the new scaffold."
      echo "To review the diagnostics and apply per-error edits interactively,"
      echo "run the feature-conversion skill in a Claude session:"
      echo "    claude"
      echo "    > run the feature-conversion skill against <feature-folder>"
      echo "The skill drafts edits per lint error and asks before writing — see"
      echo "    .specfuse/skills/feature-conversion/SKILL.md"
    fi
    echo
  fi
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

# --- lock-file gitignore (both modes) ------------------------------------ #
# Ensure .specfuse/.loop.lock is never committed in the target repo.
# This is a targeted ignore of just the lock file — not .specfuse/ itself,
# which must remain tracked (the driver uses git as its state backend).
LOCK_IGNORE_LINE=".specfuse/.loop.lock"
GITIGNORE_FILE="$TARGET/.gitignore"
if [[ $DRY_RUN -eq 1 ]]; then
  if [[ ! -f "$GITIGNORE_FILE" ]]; then
    echo "  would create $TARGET/.gitignore containing '$LOCK_IGNORE_LINE'"
  elif ! grep -qxF "$LOCK_IGNORE_LINE" "$GITIGNORE_FILE" 2>/dev/null; then
    echo "  would add '$LOCK_IGNORE_LINE' to $TARGET/.gitignore"
  else
    echo "  $TARGET/.gitignore already has '$LOCK_IGNORE_LINE' — left alone"
  fi
else
  if [[ ! -f "$GITIGNORE_FILE" ]]; then
    printf '%s\n' "$LOCK_IGNORE_LINE" > "$GITIGNORE_FILE"
    echo "Added $LOCK_IGNORE_LINE to $TARGET/.gitignore (created)."
  elif ! grep -qxF "$LOCK_IGNORE_LINE" "$GITIGNORE_FILE" 2>/dev/null; then
    printf '\n%s\n' "$LOCK_IGNORE_LINE" >> "$GITIGNORE_FILE"
    echo "Added $LOCK_IGNORE_LINE to $TARGET/.gitignore."
  fi
fi

# --- closing instructions (INIT only) ------------------------------------ #
if [[ $UPGRADE -eq 0 ]]; then
  echo "Next:"
  echo "  1. cd $TARGET"
  if [[ -n "$CI_CHECK_PATH" ]]; then
    echo "  2. review .specfuse/verification.yml  (auto-configured from $CI_CHECK_PATH)"
  else
    echo "  2. edit .specfuse/verification.yml  (match the 'code' gates to your stack)"
  fi
  echo "  3. author your first feature folder under .specfuse/features/ from .specfuse/templates/"
  echo "  4. python .specfuse/scripts/loop.py --dry-run"
  echo
  echo "The loop driver and linter have no runtime dependencies — stock Python 3"
  echo "is all you need. (You'll need whatever tools your gates in verification.yml"
  echo "call, of course — installed however your stack does it.)"
  echo
  if [[ -z "$CI_CHECK_PATH" ]]; then
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
fi
