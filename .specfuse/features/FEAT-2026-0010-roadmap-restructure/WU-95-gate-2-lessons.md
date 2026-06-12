---
id: FEAT-2026-0010/G2-LESSONS
type: lessons
effort: low
status: draft
attempts: 0
---

# Gate 2 lessons

**Objective.** Promote from this feature's `RETROSPECTIVE.md` (Gate 2
section) every observation that would change how a FUTURE work unit
in any feature is written or executed, into
`.specfuse/LEARNINGS.md`.

**Context.** Correlation ID `FEAT-2026-0010/G2-LESSONS`. Read
`RETROSPECTIVE.md`'s Gate 2 section. Read the current
`.specfuse/LEARNINGS.md` to de-duplicate against existing entries —
the Gate 1 lessons already tagged `[FEAT-2026-0010/G1]` are present
and adjacent in the file. Phrase each appended entry as a rule, not
an observation, per `.specfuse/LEARNINGS.md`'s top-of-file guidance.
Tag each with `[FEAT-2026-0010/G2]`.

**Acceptance criteria.**

1. `.specfuse/LEARNINGS.md` has zero, one, or more new entries tagged
   `[FEAT-2026-0010/G2]`, appended below the latest existing entry.
2. Each new entry would change a future WU's authoring or execution
   (sizing, scoping, hook placement in the driver, idempotency
   conventions, helper-vs-skill re-implementation patterns); none
   restates a binding rule that `.specfuse/rules/` already owns.
3. No existing entry is removed or rewritten. De-duplication takes
   the form of NOT adding an entry that already exists, not editing
   what is there.
4. If Gate 2 surfaced no generalizable lesson, append a single
   one-line entry stating so explicitly so future readers can tell
   the gate ran without contributing.

**Do not touch.** Source code, other WU files, generated directories,
`.git/`, `RETROSPECTIVE.md` (read-only). This unit appends to
`.specfuse/LEARNINGS.md` only.

**Verification.** The `doc` gates. Re-read the appended entries
before declaring complete.

**Escalation triggers.** If `RETROSPECTIVE.md` is absent or has no
Gate 2 section, emit `status: blocked` — there is nothing to
promote.
