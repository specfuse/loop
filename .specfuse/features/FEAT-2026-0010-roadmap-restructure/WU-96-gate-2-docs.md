---
id: FEAT-2026-0010/G2-DOCS
type: docs
effort: low
status: draft
attempts: 0
---

# Gate 2 docs

**Objective.** Update user-facing docs to reflect that the driver now
auto-archives a feature's roadmap detail section on completion, and
update this feature's own roadmap entry with the Gate 2 outcome.

**Context.** Correlation ID `FEAT-2026-0010/G2-DOCS`. Read
`RETROSPECTIVE.md` for the ground truth of what Gate 2 shipped. The
likely touched surfaces are: `.specfuse/skills/roadmap-archive/SKILL.md`
("When to invoke" section may want a note that completion is now
automatic, manual invocation remains valid for retro-archiving older
features); `docs/methodology.md` if it mentions the manual-archive
flow; `.specfuse/roadmap.md`'s detail section for FEAT-2026-0010
(Gate 2 status note analogous to past done-feature entries); any
README references to roadmap structure or the archive flow.

**Acceptance criteria.**

1. Every doc that mentions manual archiving, the `roadmap-archive`
   skill, or the roadmap structure has been re-read and either
   confirmed still-correct OR updated to mention the new auto-archive
   trigger. Cite each path in the RESULT summary, even when no edit
   was needed (proves the check ran).
2. `.specfuse/roadmap.md`'s detail section for FEAT-2026-0010 is
   updated to reflect what Gate 2 actually shipped (a "Gate 2
   (passed)." line analogous to past done-feature entries).
3. No source code, no other feature's detail section, no other
   feature's folder, no Gate 1 WU file is touched. The
   `roadmap-archive` skill SKILL.md may be edited only to add the
   auto-archive note in its "When to invoke" section — algorithm and
   hard-rule sections stay untouched.

**Do not touch.** Source code, tests, other WU files in this gate,
other features' detail sections in `roadmap.md`, archived sections in
`roadmap-archive.md`, `.git/`. `RETROSPECTIVE.md` is read-only here.
The skill's algorithm / hard-rule / string-format sections are
read-only; only the "When to invoke" section may gain a one-line
note.

**Verification.** The `doc` gates. Re-read the edited paragraphs
before declaring complete.

**Escalation triggers.** If a doc cited in AC 1 cannot be found at
its referenced path (rename, removal, doc drift), emit
`status: blocked` — do not paper over with a guess.
