---
id: FEAT-2026-0010/T02
type: implementation
effort: medium
status: pending
attempts: 0
---

# Ship the roadmap-archive skill

**Objective.** Ship an interactive skill (`/roadmap-archive`) that moves
a feature's detail section from `.specfuse/roadmap.md` to
`.specfuse/roadmap-archive.md`, updates the main table's Detail cell
with a back-link, and is idempotent on re-invocation.

**Context.** Correlation ID `FEAT-2026-0010/T02`. Depends on T01 — the
archive file and the `Detail` column must exist. Read
`.claude/skills/pick-feature/SKILL.md` and
`.claude/skills/feature-conversion/SKILL.md` as shape exemplars: both
are interactive Specfuse skills that propose, confirm, then write. The
archive's `## Conventions` section (written by T01) is the source of
truth for the anchor format `<a id="feat-yyyy-nnnn"></a>` and the
back-link format `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)`. Both
strings are load-bearing — read them from T01's output, do not invent.
Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**

1. New file `.claude/skills/roadmap-archive/SKILL.md` exists with the
   standard skill frontmatter (`name: roadmap-archive`, `description:`
   one-liner that triggers on the user typing `/roadmap-archive` or
   asking to archive a done/abandoned feature).
2. A symlink `.specfuse/skills/roadmap-archive` points at
   `../../.claude/skills/roadmap-archive`, matching the layout of every
   other skill in this repo (see `.specfuse/skills/pick-feature` for the
   target shape).
3. The skill accepts either a positional FEAT-ID argument
   (e.g. `/roadmap-archive FEAT-2026-0003`) or `--auto` to operate on
   every row in `.specfuse/roadmap.md` whose status is `done` or
   `abandoned` AND whose Detail cell is currently `—` (i.e. still
   inline).
4. For each target FEAT-ID, the skill: locates the `## FEAT-YYYY-NNNN —
   <title>` heading in `.specfuse/roadmap.md`; cuts from that heading
   through the line immediately preceding the next `## ` heading (or
   EOF); prepends the anchor line `<a id="feat-yyyy-nnnn"></a>` above the
   heading; appends the result to `.specfuse/roadmap-archive.md` at the
   `<!-- Archived sections appended below -->` marker (and inserts a
   blank line above for readability); and updates that feature's Detail
   cell in the main table from `—` to
   `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)`.
5. Idempotency: invoking the skill against an already-archived FEAT-ID
   (Detail cell already a back-link, or no inline `## FEAT-…` section)
   makes zero file edits and reports `FEAT-YYYY-NNNN: already archived`.
6. The skill refuses to archive a row whose status is `planned` or
   `active`; reports `FEAT-YYYY-NNNN: refused (status=<status>)` and
   exits non-zero.
7. The skill emits a row-by-row summary on stdout (`FEAT-2026-0003:
   archived`, `FEAT-2026-0004: already archived`, etc.) plus the new
   line count of `.specfuse/roadmap.md` so the operator sees the
   shrinkage.
8. A self-test exists at `tests/test_roadmap_archive_skill.py`. It
   creates a tmpdir with a stub `roadmap.md` (table header with
   `Detail`, two rows: one `done` with inline detail and one `planned`
   with no detail) plus a stub `roadmap-archive.md` (the T01 scaffold).
   It exercises: (a) archiving the `done` row succeeds and the detail
   moves with the anchor prepended, (b) the Detail cell is updated, (c)
   second invocation reports `already archived` and makes zero edits,
   (d) attempting to archive the `planned` row is refused.
9. The WU's RESULT block declares `files_changed:
   [.claude/skills/roadmap-archive/SKILL.md,
   .specfuse/skills/roadmap-archive,
   tests/test_roadmap_archive_skill.py]`.

**Do not touch.** `.specfuse/roadmap.md` and `.specfuse/roadmap-archive.md`
content — this WU's product is the skill that mutates them, not the
mutation itself (T04 invokes the skill against the real files). Any
feature folder under `.specfuse/features/`. Templates. Rules. The driver.
Other skills' files. Secrets. `.git/`. **Driver owns git — do not run
`git`.**

**Verification.**

- `python3 -m unittest discover -s tests` — full suite green, including
  the new `test_roadmap_archive_skill.py`.
- Skill-file existence smoke:
  `python3 -c "import pathlib;
  assert pathlib.Path('.claude/skills/roadmap-archive/SKILL.md').exists();
  assert pathlib.Path('.specfuse/skills/roadmap-archive').is_symlink()"`.
- Frontmatter sanity: `grep -q '^name: roadmap-archive$'
  .claude/skills/roadmap-archive/SKILL.md`.

**Escalation triggers.**

- If T01's `## Conventions` section in `roadmap-archive.md` cannot be
  read or contains anchor/back-link strings that differ from what this
  WU expects, emit `status: blocked` — building on a drifted convention
  silently breaks T04.
- If `tests/test_roadmap_archive_skill.py` is absent at the end of the
  attempt (the implementation snuck through without its test), emit
  `status: blocked`. This is the symbol-existence completeness check
  for this WU.
- If the skill's `--auto` mode design risks a destructive batch mistake
  on first run (e.g. cannot be dry-run, has no confirm step), reconsider
  the design before writing; if unsure, emit `status: blocked` with a
  proposal sketch.
