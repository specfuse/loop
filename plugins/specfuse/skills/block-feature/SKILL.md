---
name: block-feature
description: "Flip a roadmap feature to `blocked` (or clear the block) and maintain its `**Blocked by.**` detail block with linked blockers — an ADR file under docs/adr/ awaiting approval, or an upstream FEAT-ID that must complete first. Writes the roadmap row status, the detail-section blocker block (ensuring each linked feature has a resolvable anchor), and the PLAN frontmatter status if a folder exists. Invoke on /block-feature FEAT-ID --by \"<blocker>\" [...], /block-feature FEAT-ID --unblock, or interactively."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Block / unblock a feature (interactive, single-confirm)

Roadmap counterpart to `/unblock-wu`. `/unblock-wu` re-arms a `blocked_human`
*work unit* mid-gate. This skill moves a whole *feature* into (or out of) the
roadmap-level `blocked` status and keeps its `**Blocked by.**` block truthful.

`blocked` means the feature cannot proceed because a **named** dependency is
unmet — an ADR awaiting approval, or an upstream feature that must complete
first. It differs from `deferred` (a voluntary park with no named blocker): a
`blocked` feature always names what it waits on and links to it, so the roadmap
shows the dependency at a glance. See the status legend in
`.specfuse/roadmap.md`.

> **This skill is the source of truth for the `**Blocked by.**` format — not the
> roadmap legend.** `specfuse upgrade` never rewrites a project's `roadmap.md`
> (it is user-owned, seeded from the template only at `init`), so a project that
> upgrades will not see the updated legend prose in its own roadmap. That is by
> design: the legend is optional documentation; this skill renders the correct
> block regardless of whether the legend is present. A project that wants the
> legend text can paste it in by hand once — nothing depends on its presence.

Posture mirrors `/pick-feature`: the human decides the block; the skill executes
the mechanical writes and confirms once before touching disk.

**Run interactively.** The skill presents the blocker list and the write plan,
then asks for a single confirmation. `claude -p` with redirected stdin falls
back to a degraded "show the plan and stop" mode.

## Hard rules

- **A block must name at least one blocker.** That is the entire difference from
  `deferred`. If the operator has no named dependency, refuse and point at a
  plain `deferred` flip instead (a human edit, not this skill).
- **Only `planned` or `active` may be blocked.** Refuse `done`/`abandoned`
  (terminal) and `deferred` (already parked — resume it to `active` first if it
  needs a named blocker) with
  `FEAT-YYYY-NNNN: refused (status=<status>)`.
- **Writes are bounded — three surfaces, nothing else.** (1) the roadmap row's
  Status cell, (2) the feature's `**Blocked by.**` detail block, (3) the
  feature's `PLAN.md` frontmatter `status:` if a folder exists. Plus, when a
  blocker is an inline (not-yet-archived) roadmap feature, (4) a one-line
  `<a id="…">` anchor above that blocker's heading so the intra-page link
  resolves. No other rows, no WU files, no PLAN graph surgery.
- **Validate feature-ID blockers.** A `FEAT-YYYY-NNNN` blocker must exist as a
  roadmap row. If it does not, refuse and name it. If it is already `done`, warn
  — a done blocker does not block; the operator probably wants `--unblock` or a
  different blocker.
- **Single confirmation, all surfaces shown.** Print the full write plan (row
  edit, blocker block, PLAN edit, any anchor insert) and prompt once. On
  anything but `y`/`yes`, exit with zero edits.
- **No git.** The driver owns commits. Edit files only.

## When to invoke

- `/block-feature FEAT-YYYY-NNNN --by "<blocker>" [--by "<blocker>" …]` — block
  with one or more named blockers (headless-friendly).
- `/block-feature FEAT-YYYY-NNNN --unblock` — clear the block: remove the
  `**Blocked by.**` block and flip status back (see §Unblock).
- `/block-feature` (no args) — interactive: pick the feature, then collect
  blockers.
- When the user says "block FEAT-…", "this feature is waiting on ADR-…",
  "mark it blocked on FEAT-…", or "unblock FEAT-…".

## Blocker spec grammar

Each `--by "<blocker>"` (or interactive line) is one blocker. Three shapes,
auto-detected; each renders as one Markdown link plus a short `— <reason>`:

1. **ADR** — the value starts with a path ending `.md` (by convention under
   `docs/adr/`), optionally `label | path | reason`:
   - `docs/adr/0007-event-schema-versioning.md | awaiting approval`
     → `[ADR-0007: event-schema versioning](../docs/adr/0007-event-schema-versioning.md) — awaiting approval`
   - **Path is relative to `.specfuse/roadmap.md`**, not repo root: a repo-root
     path like `docs/adr/…` is rendered with a leading `../` (→ `../docs/adr/…`)
     so the link resolves from the roadmap's directory. An absolute URL is used
     verbatim.
   - Derive the `ADR-NNNN: title` label from the filename when no explicit
     label is given (strip the `NNNN-` prefix, kebab → spaced title-case).
   - **Do not require the ADR file to exist** — a feature is often blocked
     precisely because the ADR is still a draft or unwritten. If the path is
     absent, note it in the plan (`(file not present yet)`) but proceed.
2. **Feature** — the value is (or starts with) a `FEAT-YYYY-NNNN`, optionally
   `FEAT-… | reason`:
   - `FEAT-2026-0011 | scoring data must land first`
     → `[FEAT-2026-0011](#feat-2026-0011) — scoring data must land first`
   - Resolve the link target per §Anchor resolution.
   - Run the validation in Hard rules.
3. **External / freeform** — anything else. If it contains a URL, render
   `[<text>](<url>) — <reason>`; otherwise plain `` `<text>` — <reason> ``.

Reasons are optional but recommended; the link alone is valid.

## Anchor resolution (feature blockers)

GitHub auto-anchors a `## FEAT-YYYY-NNNN — Title` heading from its *full* text,
so a bare `#feat-yyyy-nnnn` link does not resolve unless an explicit anchor
exists. Resolve each feature blocker's link target as follows:

- **Blocker is archived** (its roadmap `Detail` cell holds
  `roadmap-archive.md#…`, or its inline `## FEAT-…` section is gone): link
  `[FEAT-…](roadmap-archive.md#feat-yyyy-nnnn)`. `roadmap-archive.md` already
  carries the `<a id>` anchor (written by `/roadmap-archive`).
- **Blocker is inline and live**: link `[FEAT-…](#feat-yyyy-nnnn)`, and ensure
  an anchor line exists immediately above that blocker's `## FEAT-…` heading:
  ```
  <a id="feat-yyyy-nnnn"></a>
  ```
  Use the exact format `/roadmap-archive` uses (lower-cased ID). If the anchor
  is already present, skip — this write is idempotent. This is write surface (4).

## Method — block

### 1. Resolve the target feature

- From the `FEAT-YYYY-NNNN` arg, or interactively from the roadmap's
  `planned`/`active` rows. Read its current Status cell. Apply the
  only-`planned`-or-`active` rule.

### 2. Collect and render blockers

- Parse every `--by` (or prompt interactively, one blocker per line, blank line
  to finish; refuse an empty set per Hard rules).
- Render each per the grammar, resolving feature anchors per §Anchor resolution.
- Assemble the block — blank line above, one `**Blocked by.**` paragraph,
  blockers joined by `; `:
  ```
  **Blocked by.** <blocker-1>; <blocker-2>; …
  ```

### 3. Build the write plan

- **Row.** In `.specfuse/roadmap.md`, find the target row by ID and change its
  Status cell from `<prior>` to `blocked`. Change nothing else in the row.
- **Detail block.** In the target's `## FEAT-YYYY-NNNN — …` detail section:
  - If a `**Blocked by.**` line already exists, replace it (re-block updates the
    blocker list).
  - Otherwise insert the new block. Placement: immediately above the trailing
    `**Status: …**` line if the section has one; else at the end of the section
    (before the next `## ` heading or `## Notes`), preserving one blank line
    above and below.
  - If the section carries a `**Status: <prior>.**` line, update it to
    `**Status: blocked.**`.
- **Anchors.** For each inline-live feature blocker, the `<a id>` insert from
  §Anchor resolution.
- **PLAN.** If `.specfuse/features/FEAT-YYYY-NNNN-<slug>/PLAN.md` exists, change
  its frontmatter `status: <prior>` to `status: blocked`. If no folder, skip.

### 4. Confirm once, then write

Print the plan:
```
Block FEAT-YYYY-NNNN ("<title>")  [<prior> → blocked]
  Blocked by:
    - <rendered blocker 1>
    - <rendered blocker 2>
  Writes:
    - roadmap.md row: status <prior> → blocked
    - roadmap.md detail: + **Blocked by.** block
    - roadmap.md anchor: + <a id="feat-…"> above FEAT-… (×N)   [if any]
    - PLAN.md: status <prior> → blocked                        [if folder]
Proceed? [y/N]
```
On `y`/`yes`, apply all edits. On anything else, exit with zero edits.

### 5. Report

```
FEAT-YYYY-NNNN: blocked
  Blocked by: <N> dependency(ies)
  Surfaces written: roadmap row, detail block[, PLAN.md][, N anchor(s)]
```
When any blocker is a feature, add: `Resume with /block-feature FEAT-… --unblock
once <blocker> clears.`

End with the RESULT block per
[`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means every planned write landed; `status: blocked` only if a
roadmap edit could not be applied (row not in expected format).

## Unblock

`/block-feature FEAT-YYYY-NNNN --unblock` clears a `blocked` feature:

- Refuse if the feature's status is not `blocked` (`FEAT-…: refused
  (status=<status>)`).
- Remove the `**Blocked by.**` block from the detail section.
- Flip status back. Default target: `active` if the feature has a folder whose
  PLAN shows started work (any gate not `draft`), else `planned`. Present the
  inferred target and let the operator override in the single confirm:
  `Unblock FEAT-… → active? [y / p=planned / n]`.
- Apply the same-shaped row + detail (`**Status: …**`) + PLAN writes as blocking,
  in reverse. Leave any `<a id>` anchors in place — they are harmless and other
  links may rely on them.
- Report `FEAT-YYYY-NNNN: unblocked (→ <status>)`.

Unblock does not chase the blockers' own state — the operator asserts the
dependency cleared, exactly as `deferred` → `active` is a human call.

## What this skill does NOT do

- **Does not verify a blocker actually blocks.** It records the operator's
  stated dependency; it does not read ADR approval state or a feature's gates to
  confirm. (It does warn on a `done` feature blocker — a cheap, high-signal
  check.)
- **Does not touch WU or gate files.** Feature-level status only. For a
  `blocked_human` work unit mid-gate, use `/unblock-wu`.
- **Does not archive or add rows.** Use `/roadmap-archive` / `/roadmap-add`.
- **Does not run the loop or commit.** The driver owns dispatch and git.

## Version

**v0.1.** Block / unblock with a required, linked blocker list (ADR file,
upstream FEAT-ID, or freeform). Three write surfaces plus idempotent anchor
maintenance for intra-page feature links. Expected to grow once real blocks
surface needs it doesn't cover — e.g. auto-detecting when a feature blocker
reaches `done` and offering to unblock, or reading ADR frontmatter for approval
state. Shared methodology craft (loop is near-term author).
