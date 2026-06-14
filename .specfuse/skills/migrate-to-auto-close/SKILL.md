---
name: migrate-to-auto-close
description: Scan a Specfuse project's `.specfuse/features/` for features whose PLAN.md predates the deterministic auto-close predicate (FEAT-2026-0018). For each feature, surface eligibility for auto-close on its remaining gates, the predicate's verdict on already-passed gates (read-only), and a recommended action — without auto-rewriting any PLAN.md. Opt-in per feature. Triggers: /migrate-to-auto-close, "migrate to auto-close", "audit auto-close eligibility".
---

# Migrate to auto-close (interactive, read-only survey)

This skill scans a Specfuse project's `.specfuse/features/` directory for
features that were authored before the deterministic auto-close predicate
shipped with FEAT-2026-0018. For each feature it surfaces: the predicate's
read-only verdict on already-passed gates, the eligibility picture for
remaining open gates, and a recommended action — without auto-rewriting any
PLAN.md.

**The auto-close path takes effect automatically.** Any feature whose PLAN.md
does not declare `auto_close_disabled: true` will be evaluated by the predicate
at its next gate boundary without any migration edit. This skill is a
discoverability surface, not a migration engine.

**Run interactively.** The opt-in flip step (Step 5) requires y/n confirmation
per feature; running with redirected stdin degrades to report-and-stop mode.

## When to invoke

When FEAT-2026-0018 has shipped and you want to understand how existing
in-flight or recently-completed features relate to the auto-close predicate —
which would have auto-closed, which would not, and whether any active feature
should opt out explicitly. Also useful after adding a new gate to a feature
mid-flight to see if the predicate will fire on it.

## Hard rules

- **Read-only on PLAN.md content.** This skill DOES NOT rewrite in-flight
  PLAN.md files. The auto-close path takes effect automatically on next gate
  close for any feature whose PLAN.md does not declare `auto_close_disabled:
  true`; no migration edit is required for that path.
- **Surface, do not decide.** For each scanned feature, print status + a
  recommended action; the operator confirms or overrides per feature.
- **Refuse to scan if the project is not Specfuse-shaped.** No `.specfuse/`
  directory → stop with a one-line diagnostic: `Error: .specfuse/ not found in
  <pwd>. Is this a Specfuse-integrated project?`
- **Predicate-version transparency.** Every recommendation references
  `predicate=v1` explicitly; future v2+ revisions will require re-running this
  skill.
- **No git.** This skill is read-only on `.specfuse/features/**` content and
  does not run `git`.
- **Per-feature confirm before any flip.** When the operator opts in to set
  `auto_close_disabled: true` on a specific feature (the only write this skill
  is allowed to perform), ask a single y/n confirm per feature naming the path:
  `Flip auto_close_disabled: true on <feature_id> (<path>)? (y/n)`.

## Method

### 1. Locate and validate target project

Check that a `.specfuse/` directory exists in the current working directory. If
absent, stop immediately:

```
Error: .specfuse/ not found in <pwd>. Is this a Specfuse-integrated project?
```

Confirm that `.specfuse/features/` also exists and contains at least one
`FEAT-*-*/` subdirectory. If `features/` is empty, print:

```
No features found under .specfuse/features/. Nothing to scan.
```

### 2. Enumerate features

List all directories matching `.specfuse/features/FEAT-*-*/`. For each, read
`PLAN.md` frontmatter fields:

- `feature_id` — canonical ID (e.g. `FEAT-2026-0018`)
- `status` — one of `active`, `done`, `abandoned`, `planned`
- `auto_close_disabled` — boolean, optional (absent = `false`)

Bucket into three groups: **done**, **active**, **abandoned/planned**.

Print a compact inventory before proceeding:

```
Scanned N features: A active, D done, X abandoned/planned.
```

Skip `abandoned` and `planned` features in Steps 3–5 (they have no open gates
to evaluate). List them in the final summary with status = no-action.

### 3. Per-feature eligibility report

For each `active` and `done` feature, build a one-paragraph report. Run the
predicate read-only via:

```bash
python3 .specfuse/scripts/gate_eval.py backtest <feature_id>
```

Capture the per-gate auto verdict (`auto: True/False`, `reasons: [...]`). If
the script is not found or exits non-zero, note the error inline but continue
scanning remaining features.

Per-feature report format:

```
─── <feature_id> [<slug>] ─────────────────────────────────────────
status: <active|done>
auto_close_disabled: <true|false|absent>
predicate=v1 backtest:
  Gate 1: auto=<True|False>  reasons=<[] or [list]>
  Gate 2: auto=<True|False>  ...
  (one line per gate)
recommended action: <see Step 4>
```

### 4. Recommended action per feature

Determine the recommendation for each feature after reading the backtest
output.

**Done features:**
> no action — feature is closed. Predicate backtest shown for audit only.

**Active features — predicate would fire on remaining gates:**
> leave default (predicate=v1 will auto-close gate N on next boundary — no
> PLAN.md edit needed).

**Active features — predicate refuses on all remaining gates and
`auto_close_disabled` is absent:**
> Two options; the skill names BOTH and asks — it does NOT pick:
>
> (a) **Leave default** — predicate refuses correctly; full ceremony will run
>     automatically on gate close. No change needed.
>
> (b) **Flip `auto_close_disabled: true`** — locks current behavior and
>     prevents a future predicate v2+ upgrade from auto-closing this feature's
>     remaining gates unexpectedly. Useful when the feature is intentionally
>     off-plan and you want ceremony guaranteed.
>
> Print: `Options: (a) leave default  (b) flip auto_close_disabled: true — which? (a/b/skip)`

**Active features with `auto_close_disabled: true` already set:**
> no action — already opted out. Predicate=v1 will not fire.

### 5. Opt-in flip (one feature at a time)

When the operator chooses option (b) on an active feature:

1. Ask: `Flip auto_close_disabled: true on <feature_id> (<path>/PLAN.md)? (y/n)`
2. **On y:**
   - Write `auto_close_disabled: true` into the PLAN.md frontmatter block,
     between the existing `---` delimiters, adding the field if absent or
     setting it to `true` if already present with another value.
   - Leave ALL other frontmatter fields and body content unchanged.
   - Print the first 10 lines of the updated PLAN.md as confirmation.
   - Print: `Reminder: driver owns git. No commit from this skill.`
3. **On n:** skip; move to the next feature.

**Scope of this write:** ONLY the `auto_close_disabled: <bool>` field in the
PLAN.md frontmatter. Title, branch, status, roadmap_goal, gates graph, and
body prose are untouched.

### 6. Final summary

After all features are processed, print:

```
Scanned <N>: left <M> unchanged, flipped <K>.
predicate=v1 applied. Next: monitor next gate close to see predicate
behavior on the live path.
```

If K > 0, list the feature IDs that were flipped.

## What this skill does NOT do

- **Does not auto-rewrite PLAN.md content** beyond the single `auto_close_disabled`
  frontmatter field. Multi-field migration is explicitly out of scope per
  FEAT-2026-0018 PLAN.md § "Scope OUT."
- **Does not run gate ceremonies.** Read-only evaluation only.
- **Does not run git.** No staging, no commits, no pushes. Driver owns git.
- **Does not add, remove, or reorder gates** in any PLAN.md.
- **Does not suppress full ceremony.** Predicate=v1 decides at runtime; this
  skill only surfaces what the predicate would have decided, not what it will
  decide (gate cost/event data may change before the boundary fires).
- **Does not handle predicate=v2+.** If a newer predicate version ships, this
  skill's recommendations reference v1 constants only. Re-run this skill after
  a predicate upgrade.

## Version

**v0.1** (FEAT-2026-0018/T09). Initial release — read-only survey, opt-in
`auto_close_disabled` flip, predicate=v1 backtest via `gate_eval.py backtest`.
