---
name: roadmap-archive
description: "Move a done or abandoned feature's detail section from .specfuse/roadmap.md to .specfuse/roadmap-archive.md, updating the Detail cell with a back-link. Invoke on /roadmap-archive <FEAT-ID>, /roadmap-archive --auto, or when the user asks to archive a done or abandoned feature."
---

# roadmap-archive

Moves a feature's inline detail section out of `.specfuse/roadmap.md` into
`.specfuse/roadmap-archive.md`, updates the feature's `Detail` table cell
with a back-link, and shrinks the hot roadmap file.

## When to invoke

- `/roadmap-archive FEAT-2026-0003` — archive one specific feature
- `/roadmap-archive --auto` — archive every `done`/`abandoned` feature that
  still has an inline detail section (batch mode with confirmation)
- When the user says "archive feature X", "move X to the archive",
  "clean up the roadmap", or "the roadmap is too long, archive the done features"
- **Note:** As of FEAT-2026-0010 Gate 2, `loop.py` automatically archives a
  feature's detail section when it flips `PLAN.md` status to `complete`. Manual
  invocation of this skill remains valid for back-filling older features or
  correcting a failed auto-archive.

## Hard rules

- **Archive only `done` or `abandoned`.** Refuse any other status
  (`planned`, `active`, `blocked`, `deferred`) with message
  `FEAT-YYYY-NNNN: refused (status=<status>)`.
- **Idempotent.** If the `Detail` cell already contains a back-link, or if
  the inline `## FEAT-YYYY-NNNN —` section is absent from `roadmap.md`,
  report `FEAT-YYYY-NNNN: already archived` and make zero file edits.
- **`--auto` requires confirmation.** Before writing anything, show the list
  of features that would be archived and prompt `Archive these N features?
  (y/N)`. Exit without changes on anything other than `y`/`yes`.
- **Anchor and back-link are machine-read.** Use exactly the formats below,
  no variations.

## String formats (load-bearing — do not alter)

Anchor (placed on its own line immediately above the `## FEAT-…` heading):

```
<a id="feat-yyyy-nnnn"></a>
```

Back-link (replaces `—` in the `Detail` cell):

```
[→ archive](roadmap-archive.md#feat-yyyy-nnnn)
```

In both strings replace `feat-yyyy-nnnn` with the lower-cased feature ID
(e.g. `FEAT-2026-0003` → `feat-2026-0003`).

## Algorithm — single feature

Given a `FEAT-YYYY-NNNN` target:

### Step 1 — Read and validate the table row

Read `.specfuse/roadmap.md`. Locate the table row whose first cell is
`FEAT-YYYY-NNNN`. Extract:

- `Status` (third column)
- `Detail` (fifth column)

**Guard checks (stop here if triggered):**

- `Detail` contains `roadmap-archive.md#` → `FEAT-YYYY-NNNN: already archived`
- `Status` is anything other than `done` or `abandoned` (i.e. `planned`,
  `active`, `blocked`, or `deferred`) → `FEAT-YYYY-NNNN: refused (status=<status>)`.
  Archive only terminal features; a parked or blocked feature is still live.

### Step 2 — Extract the inline detail section

Locate the line that begins exactly `## FEAT-YYYY-NNNN — ` (at column 0).
If no such line exists → `FEAT-YYYY-NNNN: already archived` (stop).

Take from that heading through the line immediately before the next `## `
heading at column 0 (or through EOF). Strip trailing blank lines, preserving
one final newline.

**Include a preceding `<a id="feat-yyyy-nnnn"></a>` anchor** if one sits on the
line immediately above the heading (a live feature blocked via `/block-feature`
gets one so intra-page `#feat-…` links resolve). Extend the extracted span
upward to swallow it, so Step 5 removes it from `roadmap.md` rather than leaving
an orphan anchor pointing at a section that has moved to the archive. Step 3
re-emits the canonical anchor above the section in the archive file, so the
link target travels with it — do not emit a second one.

### Step 3 — Append to archive

Read `.specfuse/roadmap-archive.md`. Locate the marker line:

```
<!-- Archived sections appended below -->
```

After that marker, insert:

```
<blank line>
<a id="feat-yyyy-nnnn"></a>
<the extracted section>
```

Write the updated content back to `.specfuse/roadmap-archive.md`.

### Step 4 — Update the `Detail` cell

In the table row for `FEAT-YYYY-NNNN`, replace the `Detail` cell content
(currently `—`) with:

```
[→ archive](roadmap-archive.md#feat-yyyy-nnnn)
```

### Step 5 — Remove the inline section

Remove the extracted section (Step 2) from `.specfuse/roadmap.md`. Normalize
any run of three or more consecutive blank lines down to two. Write the
updated content back.

### Step 6 — Report

Emit: `FEAT-YYYY-NNNN: archived`

## Algorithm — `--auto` mode

1. Read `.specfuse/roadmap.md`. Collect every table row where:
   - `Status` is `done` or `abandoned`, AND
   - an inline `## FEAT-id — ` section still exists for it, AND
   - `Detail` does NOT already contain `roadmap-archive.md#` (a back-link means
     already archived).

   **Do NOT gate on the `Detail` cell being `—`.** Eligibility is "has
   un-archived inline prose," not "Detail happens to be `—`." A `Detail` cell
   holding a **folder path** (e.g. `features/FEAT-…/`, an older convention) is
   orthogonal to whether the inline prose was archived — gating on `Detail ==
   —` silently skips those done features and leaves their prose inline forever
   (#102). Step 4 rewrites whatever the `Detail` cell holds (`—` *or* a folder
   path) to the back-link; the feature folder stays discoverable at its
   conventional `.specfuse/features/FEAT-…/` path.
2. If none match: report `No features eligible for archiving.` and exit.
3. Print the candidate list, then prompt:

   ```
   Eligible for archiving:
     FEAT-2026-0002 — Driver run-loop test coverage (done)
     FEAT-2026-0003 — GitHub feature-pick for the loop (done)
   Archive these 2 features? (y/N)
   ```

4. Read the user's reply. On anything other than `y`/`yes` (case-insensitive):
   exit without any file changes.
5. For each eligible feature in table order, run Steps 1–6 of the
   single-feature algorithm.
6. After all features processed, emit the final line count of
   `.specfuse/roadmap.md`:

   ```
   roadmap.md: <N> lines (was <M>)
   ```

## Summary output format

After all targets processed, emit one line per feature followed by the
line-count line:

```
FEAT-2026-0002: archived
FEAT-2026-0003: already archived
FEAT-2026-0004: archived
roadmap.md: 42 lines (was 187)
```

## What this skill does NOT do

- Does not archive `planned` or `active` features.
- Does not create `.specfuse/roadmap-archive.md` — T01 ships that file; it
  must already exist with the `<!-- Archived sections appended below -->`
  marker.
- Does not touch `.specfuse/features/<folder>` — the driver owns those.
- Does not commit — the driver owns git.
- Does not delete the feature's table row — the row stays in `roadmap.md`
  with its `Detail` cell updated to a back-link.
