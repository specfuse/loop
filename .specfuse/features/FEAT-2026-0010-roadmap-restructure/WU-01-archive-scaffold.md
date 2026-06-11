---
id: FEAT-2026-0010/T01
type: implementation
effort: low
status: pending
attempts: 0
---

# Create roadmap-archive.md and add Detail column to roadmap.md

**Objective.** Land the two structural artifacts that the rest of Gate 1
depends on: the archive file, and a `Detail` column on the main roadmap
table so back-links from migrated rows have somewhere to live.

**Context.** Correlation ID `FEAT-2026-0010/T01`. Foundation WU; T02
(`roadmap-archive` skill), T03 (`roadmap-add` skill), and T04 (migrate
0003..0008) all assume the archive file exists and the table has a
`Detail` column. Read `.specfuse/roadmap.md` to learn the current table
shape and column order. Read FEAT-2026-0010's own detail section in that
roadmap for the conventions narrative (anchor format, back-link form).
Anchor convention: `<a id="feat-yyyy-nnnn"></a>` placed on its own line
immediately above each archived feature's `## FEAT-YYYY-NNNN —` heading
in the archive file. Back-link convention in the main table's Detail
cell: `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)`. Both strings are
load-bearing for T02 and T04 — keep them exact. Binding rules in
`.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`correlation-ids.md`) apply.

**Acceptance criteria.**

1. `.specfuse/roadmap-archive.md` exists, with YAML frontmatter
   containing `project: specfuse-loop`, a `# Archived feature details`
   top-level heading, a one-paragraph explainer, a `## Conventions`
   section that names the exact anchor string `<a id="feat-yyyy-nnnn"></a>`
   and the exact back-link string `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)`,
   and a placeholder line `<!-- Archived sections appended below -->`
   marking where T02/T04 will append.
2. `.specfuse/roadmap.md`'s feature table header gains a final column
   labeled `Detail` (column header `| Detail |` and the corresponding
   `|---|` separator cell).
3. Every existing data row in that table receives `| — |` as its Detail
   cell. No row is deleted, reordered, or otherwise edited. No other
   column's cells change.
4. The `## Conventions` section in `roadmap-archive.md` also names which
   statuses get archived (`done`, `abandoned`) and which stay inline
   (`planned`, `active`).
5. The WU's RESULT block declares `files_changed: [.specfuse/roadmap.md,
   .specfuse/roadmap-archive.md]` and the squash commit touches exactly
   those two paths.

**Do not touch.** Detail sections in `.specfuse/roadmap.md` (T02 and T04
own those). Any feature folder under `.specfuse/features/`. Any file
under `.specfuse/templates/`, `.specfuse/rules/`, or `.specfuse/scripts/`.
The driver. The `## Notes`, `## Status`, `## Conventions`, or any other
section of `roadmap.md` outside the feature table itself. Skills under
`.claude/skills/` and `.specfuse/skills/`. Tests. Generated directories
(none here, but the rule stands). Secrets (`.env`, `*.pem`, `*.key`,
`credentials.json`). `.git/`. **The driver owns all git operations — do
not run `git`.** See `.specfuse/rules/never-touch.md`.

**Verification.**

- `python3 -m unittest discover -s tests` — full suite must stay green
  (no test changes expected; sanity).
- Existence smoke: `python3 -c "import pathlib; assert
  pathlib.Path('.specfuse/roadmap-archive.md').exists()"`.
- Structural assert: `grep -c '| Detail |' .specfuse/roadmap.md` must
  return at least 1 (header row present).
- Anchor string presence: `grep -q '<a id="feat-yyyy-nnnn"></a>'
  .specfuse/roadmap-archive.md` must succeed (the conventions section
  documents the literal pattern).
- Back-link string presence:
  `grep -q '\[→ archive\](roadmap-archive.md#feat-yyyy-nnnn)'
  .specfuse/roadmap-archive.md` must succeed.

**Escalation triggers.**

- If the existing feature table in `.specfuse/roadmap.md` has irregular
  row widths (rows whose pipe count differs from the header row), emit
  `status: blocked` — the schema change cannot be safely applied to a
  malformed table, and guessing the right shape is worse than stopping.
- If a non-table block appears between the header and what looks like
  the last data row (interleaved prose), emit `status: blocked`.
- If `.specfuse/roadmap-archive.md` already exists with non-trivial
  content (more than the scaffold this WU would produce), emit
  `status: blocked` — someone has been here before; do not overwrite.
- If either the anchor string or the back-link string above cannot be
  written verbatim because of markdown-parsing constraints in the
  archive's `## Conventions` section, emit `status: blocked` — the
  strings are load-bearing for T02 and T04.
