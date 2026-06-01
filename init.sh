#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# init.sh — scaffold the Specfuse Loop into a target single-repo project.
#
# Copies the canonical .specfuse/ scaffold (scripts, templates, rules, skills,
# the LEARNINGS seed, and the verification.yml example) into a target repo, and
# drops the roadmap in place. It deliberately does NOT copy the bundled example
# feature or any runtime state — the target starts clean.
#
# Usage:
#   ./init.sh /path/to/target-repo
#
# After running, in the target repo:
#   - edit .specfuse/verification.yml so the `code` gates match your stack
#     (and your branch protection, if any)
#   - author your first feature folder under .specfuse/features/ from the
#     templates in .specfuse/templates/
#   - python .specfuse/scripts/loop.py --dry-run

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.specfuse"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "usage: ./init.sh /path/to/target-repo" >&2
  exit 2
fi
if [[ ! -d "$TARGET" ]]; then
  echo "error: target '$TARGET' is not a directory" >&2
  exit 2
fi
if [[ -e "$TARGET/.specfuse" ]]; then
  echo "error: '$TARGET/.specfuse' already exists; refusing to overwrite" >&2
  exit 1
fi

DEST="$TARGET/.specfuse"
mkdir -p "$DEST"

# Copy the scaffold, excluding the bundled example feature and any runtime state.
for item in scripts templates rules skills verification.yml.example README.md; do
  cp -r "$SRC_DIR/$item" "$DEST/$item"
done

# Strip any compiled-Python noise that may have been copied with scripts/.
find "$DEST" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

# Seed files that start empty-ish in a new project.
cp "$SRC_DIR/LEARNINGS.md" "$DEST/LEARNINGS.md"

# Put live working copies in place. The roadmap ships as `roadmap.md` only —
# the `.template` form is the SOURCE the loop's own repo uses to seed new
# projects; destinations don't need (and shouldn't carry) a stray template
# twin. verification.yml.example IS retained as a reference because the gate
# set is more involved than the roadmap and a per-stack example is useful.
cp "$DEST/verification.yml.example" "$DEST/verification.yml"
cp "$SRC_DIR/roadmap.template.md" "$DEST/roadmap.md"

# Start with an empty features directory.
mkdir -p "$DEST/features"

echo "Scaffolded Specfuse Loop into $DEST"
echo

# Gitignore guard: the loop uses git as its state backend (status writes via
# frontmatter edits, the squashed per-WU commit, and the `doc` gate's
# `git diff` check). If `.specfuse/` is gitignored in the target repo, those
# writes are invisible to git and the loop silently misbehaves. Warn loudly.
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
