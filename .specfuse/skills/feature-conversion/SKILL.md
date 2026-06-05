---
name: feature-conversion
description: Bring an existing Specfuse feature folder into conformance with the current scaffold's structural contract. Runs after `init.sh --upgrade` flags a feature as FAIL in the health report. Interactive only — drafts edits per lint error and asks before writing. Lint-driven; will not propose changes the linter doesn't require.
---

# Feature conversion (interactive, lint-driven)

This skill walks a single existing feature folder through the structural
edits needed to pass `lint_plan.py` against the **current** scaffold. It is
the second half of the `--upgrade` story: the upgrade flag refreshes the
versioned scaffold; this skill refreshes user-authored features against
that scaffold when the linter flags drift.

The skill exists because some lint errors have an obvious mechanical fix
(rename a malformed correlation ID; add a missing closing-sequence WU
that newer templates require) and some don't (a renamed field, a real
semantic mismatch). A blanket auto-fix would be wrong for the latter
class. So the skill is **interactive**: it reads the failing feature,
reads the current templates and rules as the conformance target, and
proposes one edit per lint error, asking the user to accept, modify,
or skip each.

**Run interactively.** Start `claude` in the target repo and ask it to
run this skill against the failing feature folder. The skill prompts the
user multiple times — `claude -p < ...` consumes stdin, so the skill
cannot ask and the conversion stops being useful. The non-interactive
path is "stop and emit `status: blocked` with the diagnostic list," not
"silently apply a best guess."

## When to invoke

Specifically: when `./init.sh --upgrade [--dry-run] <target>` prints a
`FAIL <feature-folder>` line in its feature-health report. The skill
takes that feature folder as its input.

You can also invoke the skill manually against any feature folder you
suspect has drifted, even without running `--upgrade` — the skill's
discovery surface is `lint_plan.py`'s output, which you can read any
time with:

    python .specfuse/scripts/lint_plan.py .specfuse/features/<feature-folder>

## Method

### 1. Read the conformance target

Before reading the failing feature, ground in the current scaffold:

  - `.specfuse/templates/PLAN.template.md` — the PLAN frontmatter +
    graph block shape.
  - `.specfuse/templates/GATE.template.md` — gate frontmatter.
  - `.specfuse/templates/WU.template.md` — WU frontmatter + the five
    mandatory body sections.
  - `.specfuse/rules/correlation-ids.md` — the ID pattern lint enforces.
  - `.specfuse/rules/result-contract.md` — the agent-to-driver contract
    (relevant when surfacing edits that affect dispatchable status).

### 2. Run the linter, capture every error verbatim

    python .specfuse/scripts/lint_plan.py <feature-folder>

`lint_plan.py` is the source of truth for what passes. **Every proposed
edit must trace to a specific error in this output**, named by the
linter. Do not propose edits the linter is silent about — adding fields
the templates document but the linter doesn't require is a quiet way to
churn user files for no behavior change.

### 3. Propose one edit per lint error, in order

For each error in the linter's output:

  - **Quote the error verbatim** so the user sees the exact diagnostic
    that motivates the edit.
  - **State the conformance source** the edit aligns to (a specific rule
    or template section).
  - **Show the proposed edit as a diff** (small, scoped — one file, the
    minimal change that resolves the error).
  - **Ask the user**: accept this edit, modify it, or skip this error?
    Accept = write; modify = take the user's revision and write; skip =
    leave the file alone and move on. Do not batch — each error is its
    own decision point.

### 4. Common error → fix map (the obvious half)

These shapes have a clear mechanical resolution; the skill should
propose them confidently but still ask for confirmation:

  - **`malformed correlation id '<x>'`** — propose the closest conformant
    ID. `T1` → `T01` (two-digit padding); `t01` → `T01` (uppercase);
    `G1-retro` → `G1-RETRO` (uppercase). For ambiguous cases, ask.
  - **`frontmatter id '<x>' != graph id '<y>'`** — surface both; ask
    which is canonical; align the other to it.
  - **`<id> -> file not found: <path>`** — propose either (a) creating
    the missing WU file from `WU.template.md`, or (b) removing the
    graph entry. Ask which.
  - **`<wu> missing section '<name>'`** — propose adding the section
    header with a placeholder body sourced from `WU.template.md`'s
    matching section. The user fills in real content; do not invent
    acceptance criteria.
  - **`closing sequence must be exactly [...]; found <list>`** — propose
    the missing closing-sequence WUs (`retrospective`, `lessons`,
    `docs`, `plan-next`) using the correlation-ID form
    `G<n>-(RETRO|LESSONS|DOCS|PLAN)` for the relevant gate number, each
    bodied from the WU template with a placeholder Objective.
  - **`invalid type '<x>'`** — surface the valid set
    (`implementation, retrospective, lessons, docs, plan-next`) and
    ask which the user meant.
  - **`invalid status '<x>'`** — surface the valid set
    (`draft, pending, ready, in_progress, in_review, done,
    blocked_human, abandoned`) and ask.
  - **`missing model`** — propose `claude-sonnet-4-6` for substantive
    units, `claude-opus-4-7` for `plan-next`; ask before writing.

### 5. The not-obvious half — defer to the user

If a linter error doesn't fit the map above (e.g. a new error class the
linter has grown that this skill hasn't catalogued), do NOT guess. Show
the user the error, point at the relevant template/rule, and ask what
the edit should look like. Then propose-and-confirm normally.

### 6. After all edits — re-run the linter

Once the user has accepted (or skipped) every proposal:

  - Re-run `python .specfuse/scripts/lint_plan.py <feature-folder>`.
  - Report the new state: either "PASS" or the remaining errors.
  - For remaining errors (skipped or unresolved), report them so the
    user knows the feature still needs attention.

## What this skill does NOT do

  - **Does not propose changes the linter is silent about.** No
    speculative bumps for fields that newer templates document but the
    linter doesn't require (e.g. an optional `generated_surfaces`
    field). When the linter starts requiring something, this skill
    starts proposing it.
  - **Does not touch files outside the feature folder.** The roadmap,
    the templates, the rules, other features — out of scope.
  - **Does not run git.** Edits are file writes; the user reviews via
    git diff after the skill finishes. (If the user wants atomic
    commits per accepted edit, that's a per-edit git invocation they
    run themselves between accepts.)
  - **Does not bulk-convert multiple features.** One feature folder
    per invocation. Run it again for the next.
  - **Does not apply edits in `--dry-run`-style preview mode.** Either
    the user accepts and we write, or they skip and we don't. There's
    no "show me everything you would do, then apply" pseudo-batch —
    that pattern caused the original derive-verification mistake of
    silent gap-mode fallbacks.

## Closing rule

End with the RESULT block defined in
`.specfuse/rules/result-contract.md`. `status: complete` means "I
walked every lint error and the user decided on each." If the user
abandoned the conversion partway, emit `status: blocked` with the
remaining error list as `blocked_reason`.

## Version

**v0.1.** The "common error → fix map" in §4 covers every error
`lint_plan.py` produces as of today. When the linter grows new error
classes, add them here once the obvious fix is established (and not
before — a speculative fix proposal that turns out wrong is the worst
outcome). This is shared methodology craft; the loop is its near-term
author, like the architecture addendum.
