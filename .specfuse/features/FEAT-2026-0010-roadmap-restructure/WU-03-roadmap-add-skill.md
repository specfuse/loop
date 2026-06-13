---
id: FEAT-2026-0010/T03
type: implementation
effort: medium
status: done
attempts: 2
duration_seconds: 759.683
cost_usd: 1.674669
input_tokens: 52
output_tokens: 32715
---

# Ship the roadmap-add skill

**Objective.** Ship an interactive skill (`/roadmap-add`) that appends a
new `planned` feature to `.specfuse/roadmap.md` — one table row plus
one detail section — with the next available `FEAT-YYYY-NNNN` ID chosen
automatically and headless overrides via flags.

**Context.** Correlation ID `FEAT-2026-0010/T03`. Depends on T01 — the
`Detail` column must exist before this skill can write rows with a
canonical column count. Read `.claude/skills/pick-feature/SKILL.md` for
shape. The next-ID scan must consult three sources because IDs get
reserved before folders exist: (a) every row in
`.specfuse/roadmap.md`'s feature table, (b) every `feature_id:` in
`.specfuse/features/*/PLAN.md`, (c) any `FEAT-YYYY-NNNN` reference in
`.specfuse/LEARNINGS.md` and in `RETROSPECTIVE.md` files under
`.specfuse/features/*/`. The highest year-matching ID seen across all
three sources, plus one, is the next ID for the current calendar year.
Binding rules in `.specfuse/rules/` apply, including
`.specfuse/rules/correlation-ids.md` for the `FEAT-YYYY-NNNN` pattern.

**Acceptance criteria.**

1. New file `.claude/skills/roadmap-add/SKILL.md` with standard skill
   frontmatter (`name: roadmap-add`, descriptive one-liner) and a
   symlink `.specfuse/skills/roadmap-add` →
   `../../.claude/skills/roadmap-add`.
2. Interactive mode (no args): the skill computes the next FEAT-ID by
   scanning the three sources above; presents it for confirmation; then
   prompts for `title`, `slug` (auto-suggested as kebab-case of title),
   one-paragraph `why`, one-paragraph `goal`, one-paragraph `benefits`.
3. Headless mode: `/roadmap-add --id FEAT-YYYY-NNNN --title "..."
   --slug ... --why "..." --goal "..." --benefits "..."` short-circuits
   prompts. Missing any required flag in this mode errors out
   non-interactively with a clear message naming the missing flag.
4. The skill appends one row to the feature table immediately after the
   current last data row, with canonical column order `| ID | Title |
   Status | Folder | Detail |`, values `| <id> | <title> | planned | — |
   — |`.
5. The skill appends a `## <id> — <title>` detail section after the
   existing last detail section and before the `## Notes` section. The
   detail section contains `**Why.**` `<paragraph>`, `**Goal.**`
   `<paragraph>`, `**Benefits.**` `<paragraph>`, and a closing line
   `**Status: planned.**`.
6. The skill refuses to write if the chosen FEAT-ID is already present
   in any of the three scanned sources; the failure message names the
   conflicting source (the file and line) so the operator can resolve.
7. A self-test exists at `tests/test_roadmap_add_skill.py` covering:
   (a) headless mode appends a row + section in the right places given
   a stub roadmap; (b) the next-ID scan picks `0011` when the stub has
   `0010` as max in roadmap, `0009` in a feature PLAN, and a reference
   to `0010` in a stub LEARNINGS file (i.e. cross-source max wins);
   (c) ID collision is rejected with a message naming the colliding
   source.
8. The WU's RESULT block declares `files_changed:
   [.claude/skills/roadmap-add/SKILL.md,
   .specfuse/skills/roadmap-add,
   tests/test_roadmap_add_skill.py]`.

**Do not touch.** `.specfuse/roadmap.md` or
`.specfuse/roadmap-archive.md` content (this WU ships the skill, not
new roadmap entries). Any feature folder under `.specfuse/features/`.
Templates. Rules. The driver. Other skills. Secrets. `.git/`. **Driver
owns git — do not run `git`.**

**Verification.**

- `python3 -m unittest discover -s tests` — full suite green, including
  the new `test_roadmap_add_skill.py`.
- Skill-file existence smoke:
  `python3 -c "import pathlib;
  assert pathlib.Path('.claude/skills/roadmap-add/SKILL.md').exists();
  assert pathlib.Path('.specfuse/skills/roadmap-add').is_symlink()"`.
- Frontmatter sanity: `grep -q '^name: roadmap-add$'
  .claude/skills/roadmap-add/SKILL.md`.

**Escalation triggers.**

- If the next-ID scan finds gaps in the FEAT sequence for the current
  year (e.g. 0009 missing while 0010 and 0011 exist), emit
  `status: blocked` and report the gap — the gap might be a reserved ID
  the user named verbally only; auto-picking the gap as the next ID is
  the failure mode this trigger exists to prevent.
- If the canonical column order of `.specfuse/roadmap.md`'s table
  differs from `| ID | Title | Status | Folder | Detail |` (e.g. T01
  changed the order, or the user re-ordered manually), emit
  `status: blocked` — the skill writes new rows in the wrong shape
  otherwise.
- If `tests/test_roadmap_add_skill.py` is absent at the end of the
  attempt, emit `status: blocked` — completeness check for this WU.
