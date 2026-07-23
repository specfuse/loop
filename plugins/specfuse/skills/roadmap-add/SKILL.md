---
name: roadmap-add
description: "Append a new planned feature row + detail section to .specfuse/roadmap.md, auto-picking the next FEAT-YYYY-NNNN ID by scanning four sources (roadmap table, PLAN.md files, LEARNINGS/RETROSPECTIVE files, and GitHub issue/PR titles+bodies when reachable). Invoke on /roadmap-add (interactive) or /roadmap-add --id ... --title ... --slug ... --why ... --goal ... --benefits ... (headless)."
---

# roadmap-add

Appends one table row and one detail section for a new `planned` feature to
`.specfuse/roadmap.md`. The next `FEAT-YYYY-NNNN` ID is computed automatically
from four sources so that IDs reserved in comments, closed folders, or GitHub
issue/PR titles are not reused.

## When to invoke

- `/roadmap-add` — interactive: compute next ID, confirm, then prompt for fields
- `/roadmap-add --id FEAT-YYYY-NNNN --title "..." --slug ... --why "..." --goal "..." --benefits "..."` — headless: skip all prompts
- When the user says "add a feature to the roadmap", "reserve a new FEAT ID",
  "plan a new feature", or "append a planned entry"

## Hard rules

- **Never write if the chosen ID already appears in any scanned source.** Report
  the collision with the exact file path and line number so the operator can
  resolve before retrying.
- **Detect sequence gaps and stop.** If the scan finds gaps in the year's FEAT
  sequence (e.g. `0009` missing while `0010` and `0011` exist), emit
  `status: blocked` — a gap may be a verbally-reserved ID; auto-filling it is the
  failure mode this check exists to prevent.
- **Canonical column order only.** The skill writes rows in
  `| ID | Title | Status | Folder | Detail |` order. If the roadmap table header
  does not match that shape exactly, refuse with a clear error naming the mismatch.
- **New rows are always `planned`.** That's the only status this skill
  writes. For reference, the full roadmap status vocabulary is
  `planned | active | blocked | deferred | done | abandoned` (`blocked` = a
  named dependency is unmet — an ADR or upstream feature, linked from the
  detail section's `**Blocked by.**` block; `deferred` = a voluntary park with
  no named blocker); later transitions are owned by /pick-feature, the driver,
  or a human — not this skill.

  (Do not confuse a roadmap *feature* `blocked` status with this skill's own
  RESULT `status: blocked` on a sequence-gap escalation below — the latter is
  this run's outcome, never written into the roadmap table.)
- **No git.** The driver owns all commits. Edit files only.
- **Interactive mode only confirms once** — the presented next ID, then collects
  fields. It does not re-ask for confirmation before writing.

## String formats (load-bearing — do not alter)

Table row:

```
| <FEAT-YYYY-NNNN> | <title> | planned | — | — |
```

Detail section heading:

```
## <FEAT-YYYY-NNNN> — <title>
```

Detail section body (five blocks, blank line between each):

```
**Why.** <why paragraph>

**Goal.** <goal paragraph>

**Benefits.** <benefits paragraph>

**Status: planned.**
```

## Next-ID algorithm

The next ID for the current calendar year is one greater than the highest
`NNNN` found across **four sources**:

### Source (a) — roadmap table rows

Read `.specfuse/roadmap.md`. For every line that begins with
`| FEAT-<YYYY>-<NNNN>` (a table data row), record the FEAT ID and its line number.

### Source (b) — feature PLAN.md files

For every file matching `.specfuse/features/*/PLAN.md`, scan lines that match
`^feature_id:\s*FEAT-<YYYY>-<NNNN>`. Record the FEAT ID and its file path + line
number.

### Source (c) — LEARNINGS.md and RETROSPECTIVE.md files

Read `.specfuse/LEARNINGS.md`. Read every file matching
`.specfuse/features/*/RETROSPECTIVE.md`. For every occurrence of
`FEAT-<YYYY>-<NNNN>` anywhere in those files, record the ID and its first
occurrence (file path + line number).

### Source (d) — GitHub issue and PR titles + bodies

Teams also reserve FEAT IDs directly on GitHub — an issue or PR titled
`FEAT-<YYYY>-<NNNN>: ...` that never gets a roadmap row. Those IDs are invisible
to sources (a)–(c), so a purely local scan can hand out an ID already taken on
GitHub (the collision this skill exists to prevent).

When `gh` is available and authenticated, search the current repo's issues and
PRs — both open and closed — for `FEAT-<YYYY>-` in the title or body, and record
each ID with its issue/PR number as the source location:

```
gh search issues  --repo <owner/repo> "FEAT-<YYYY>-" --json number,title
gh search prs      --repo <owner/repo> "FEAT-<YYYY>-" --json number,title
```

(Resolve `<owner/repo>` from `gh repo view --json nameWithOwner -q .nameWithOwner`,
or `git remote get-url origin`.)

**Degrade gracefully — never hard-fail on this source.** The skill runs offline.
If `gh` is missing, unauthenticated, or the search errors/times out, print a
one-line warning and continue with sources (a)–(c) only:

```
WARN: GitHub not reachable — next-ID scan skipped issue/PR-reserved IDs.
      An ID reserved only on GitHub could still collide; verify before writing.
```

When GitHub IS reachable, an issue/PR-reserved ID blocks reuse exactly like a
roadmap row (see the collision check below).

Scope note: source (d) searches the current repo only. IDs reserved in a
different repo (cross-repo reservations) are out of scope for the automatic scan.

### Computing the next ID

1. Collect all `NNNN` ordinals for the current year from sources (a), (b), (c),
   and (d) when GitHub was reachable.
2. If none found: next ordinal is `0001`.
3. Otherwise: next ordinal is `max(ordinals) + 1`.
4. **Gap check:** verify the ordinals form a contiguous sequence from `0001` to
   `max`. A GitHub-reserved ID (source d) counts as **present** — it fills its
   own ordinal and raises `max`; it is never itself reported as the gap. But a
   reserved ID beyond the local max still exposes the intervening ordinals as
   genuinely unaccounted (e.g. roadmap reaches `0010`, issue reserves `0016` →
   `0011`–`0015` are gaps). If any ordinal is missing, stop immediately:
   ```
   ERROR: FEAT-<YYYY> sequence has gap at <NNNN> — resolve before adding.
   Seen ordinals: 0001 0002 0003 0005 0006 ...
   Missing: 0004
   ```
   This is an escalation condition; emit `status: blocked` with the gap named.

## Collision check

Before writing, verify the proposed ID does not appear in any of the four
sources — including, when GitHub is reachable, an issue/PR title or body that
reserves it. If it does:

```
ERROR: <FEAT-YYYY-NNNN> already exists.
  Source: <filepath>:<lineno>   (or: GitHub issue/PR #<n>)
```

Stop without writing.

## Write algorithm

### Step 1 — Validate table header

Read `.specfuse/roadmap.md`. Find the table header line (begins with
`| Feature ID`). Verify the column order is:
`| Feature ID ... | Title ... | Status ... | Folder ... | Detail ... |`

If the header does not match:
```
ERROR: roadmap.md table header has unexpected column order.
  Expected: | ID | Title | Status | Folder | Detail |
  Found: <actual header>
```
Stop without writing.

### Step 2 — Find the last table data row

Scan for lines beginning `| FEAT-`. The last such line is the insertion point.
The new row is inserted immediately after it.

### Step 3 — Find the ## Notes section

Scan for a line matching `^## Notes`. The new detail section is inserted
immediately before this line (with any leading blank line preserved).

If `## Notes` is not found, stop:
```
ERROR: ## Notes section not found in roadmap.md — cannot place detail section.
```

### Step 4 — Build and insert the new row

```
| <feat-id> | <title> | planned | — | — |
```

### Step 5 — Build and insert the detail section

```
## <feat-id> — <title>

**Why.** <why>

**Goal.** <goal>

**Benefits.** <benefits>

**Status: planned.**

```

Insert before the `## Notes` line.

### Step 6 — Report

```
<FEAT-YYYY-NNNN>: added
  Folder slug: <slug>
  roadmap.md: <N> lines (was <M>)
```

The `slug` field is for the operator's reference when creating the feature folder
(`FEAT-YYYY-NNNN-<slug>`). The skill does not create the folder.

## Interactive mode

1. **Compute the next ID** using the four-source scan. Present:
   ```
   Next available ID: FEAT-YYYY-NNNN
   (Highest seen: FEAT-YYYY-MMMM in <source>)
   Use this ID? [Y/n]
   ```
   On `n`, prompt:
   ```
   Enter ID (FEAT-YYYY-NNNN format):
   ```
   Validate format; run collision check on the entered ID.

2. **Collect fields** (present current suggestion, accept empty to confirm):
   - `Title:` — one-line title (required)
   - `Slug:` — auto-suggested as kebab-case of title (edit or accept)
   - `Why:` — one paragraph explaining the motivation (required)
   - `Goal:` — one paragraph describing the outcome (required)
   - `Benefits:` — one paragraph listing the benefits (required)

3. **Confirm before writing:**
   ```
   About to add:
     ID:    FEAT-YYYY-NNNN
     Title: <title>
     Slug:  <slug>
   Proceed? [Y/n]
   ```
   On `n`, exit without changes.

4. Run Steps 1–6 of the write algorithm.

## Headless mode

All six required flags must be present:

```
/roadmap-add \
  --id FEAT-YYYY-NNNN \
  --title "Feature title" \
  --slug feature-slug \
  --why "Why paragraph." \
  --goal "Goal paragraph." \
  --benefits "Benefits paragraph."
```

If any required flag is missing, exit with:

```
ERROR: missing required flag: --<flag-name>
```

No file changes are made on a missing-flag error.

In headless mode, always run the collision check even though the ID was passed
explicitly.

## What this skill does NOT do

- Does not create the feature folder — use `/draft-feature` after adding.
- Does not flip status from `planned` to `active` — use `/pick-feature`.
- Does not archive detail sections — use `/roadmap-archive`.
- Does not commit — the driver owns git.
- Does not modify any file other than `.specfuse/roadmap.md`.
- Does not guess `--slug` in headless mode; the caller must supply it.
