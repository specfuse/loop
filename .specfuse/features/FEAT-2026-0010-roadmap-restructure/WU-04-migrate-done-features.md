---
id: FEAT-2026-0010/T04
type: implementation
effort: low
status: done
attempts: 1
duration_seconds: 582.829
cost_usd: 0.91579
input_tokens: 606
output_tokens: 29050
---

# Migrate FEAT-2026-0003..0008 detail sections to the archive

**Objective.** Dogfood the T02 skill: archive the six existing `done`
feature detail sections (FEAT-2026-0003 through FEAT-2026-0008) out of
`.specfuse/roadmap.md` and into `.specfuse/roadmap-archive.md`, and
update each row's Detail cell with the back-link.

**Context.** Correlation ID `FEAT-2026-0010/T04`. Depends on T02 — the
`roadmap-archive` skill must exist. The six target FEAT-IDs are the
six `done` rows in the roadmap table immediately preceding this
feature's own row: 0003, 0004, 0005, 0006, 0007, 0008. After this WU,
the main roadmap should be measurably leaner with no semantic content
lost — the archive owns the moved sections byte-for-byte modulo the
prepended anchor line. Read the current `.specfuse/roadmap.md` to
confirm the six target rows are still `done` and still have inline
detail sections (Detail cell `—`). Binding rules in `.specfuse/rules/`
apply.

**Acceptance criteria.**

1. After this WU, `grep -c '^## FEAT-2026-000[3-8] '
   .specfuse/roadmap.md` returns `0` (no inline detail for any of the
   six target features).
2. `grep -c '^## FEAT-2026-000[3-8] '
   .specfuse/roadmap-archive.md` returns `6` (all six sections landed
   in the archive).
3. For each of the six target IDs, the main table's Detail cell now
   contains `[→ archive](roadmap-archive.md#feat-2026-000N)` (literal
   string, with N matching the FEAT-ID's last digit).
4. The body of each archived section is byte-equivalent to the
   pre-migration content, modulo a single `<a id="feat-2026-000N"></a>`
   line prepended above the `## FEAT-…` heading. Verify by diffing
   against `git show HEAD:.specfuse/roadmap.md` for each target range.
5. No row in the main table outside the six target rows is modified.
   No section header outside the six target detail sections is removed
   or added.
6. The WU's RESULT block declares `files_changed:
   [.specfuse/roadmap.md, .specfuse/roadmap-archive.md]`.

**Do not touch.** Detail sections of `planned` or `active` features
(0002, 0010, 0011 at minimum, plus any others present at attempt time —
do not assume the table shape; read it). The archive file's `## Conventions`
header and explainer (only append to the marker). Any feature folder.
Skills (T02 already exists; this WU only invokes it, does not edit it).
Templates. Rules. The driver. Tests (T02's self-tests already exist;
this WU adds none). Secrets. `.git/`. **Driver owns git — do not run
`git`.**

**Verification.**

- `python3 -m unittest discover -s tests` — full suite green.
- `python3 .specfuse/scripts/lint_plan.py
  .specfuse/features/FEAT-2026-0010-roadmap-restructure` PASS.
- Structural assertions: the two `grep -c` commands in AC 1 and 2
  return `0` and `6` respectively.
- Back-link presence:
  `grep -c '\[→ archive\](roadmap-archive.md#feat-2026-0003)'
  .specfuse/roadmap.md` returns at least 1; same for 0004..0008.
- Sanity sizing: `wc -l .specfuse/roadmap.md` returns at least 150
  fewer lines than `git show HEAD:.specfuse/roadmap.md | wc -l`.
  (Sanity, not load-bearing — AC 1 is the structural assertion.)

**Escalation triggers.**

- If T02's skill (the dependency) emits any `archived` line for an ID
  outside `0003..0008`, emit `status: blocked` — scope leak; the
  migration must touch exactly the six target rows.
- If any pre-migration detail section cannot be byte-recovered from
  the archive (diff fails AC 4), emit `status: blocked` — content
  corruption; do not paper over.
- If any of the six target rows have already been archived (Detail
  cell already a back-link or no inline section present), report that
  the work is already partially done; if T02's idempotency holds, the
  remaining IDs should still migrate cleanly; if any inconsistency
  remains, emit `status: blocked`.
- If reading the table reveals additional `done` or `abandoned` rows
  beyond 0003..0008 with inline detail, do NOT migrate them — they are
  out of scope for this WU; report them in the RESULT summary so the
  retro captures the case.
