---
id: FEAT-2026-0010/G1-LESSONS
type: lessons
effort: low
status: done
attempts: 1
duration_seconds: 64.96
cost_usd: 0.23318
input_tokens: 7
output_tokens: 3201
---

# Gate 1 lessons

**Objective.** Promote from this feature's `RETROSPECTIVE.md` (Gate 1
section) every observation that would change how a FUTURE work unit
in any feature is written or executed, into `.specfuse/LEARNINGS.md`.

**Context.** Correlation ID `FEAT-2026-0010/G1-LESSONS`. Read
`RETROSPECTIVE.md`. Read the current `.specfuse/LEARNINGS.md` to
de-duplicate against existing entries. Phrase each appended entry as a
rule, not an observation, per `.specfuse/LEARNINGS.md`'s top-of-file
guidance. Tag each with `[FEAT-2026-0010/G1]`.

**Acceptance criteria.**
1. `.specfuse/LEARNINGS.md` has zero, one, or more new entries tagged
   `[FEAT-2026-0010/G1]`, appended below the latest existing entry.
2. Each new entry would change a future WU's authoring or execution
   (sizing, scoping, dependencies, verification shape, anchor/back-link
   conventions, skill-shape rules); none restates a binding rule that
   `.specfuse/rules/` already owns.
3. No existing entry is removed or rewritten. De-duplication, when
   applied, takes the form of NOT adding an entry that already exists,
   not editing what is there.
4. If Gate 1 surfaced no generalizable lesson, append a single
   one-line entry stating so explicitly so future readers can tell the
   gate ran without contributing.

**Do not touch.** Source code, other WU files, generated directories,
`.git/`, `RETROSPECTIVE.md` (read-only). This unit appends to
`.specfuse/LEARNINGS.md` only.

**Verification.** The `doc` gates. Re-read the appended entries before
declaring complete.

**Escalation triggers.** If `RETROSPECTIVE.md` is absent or has no
Gate 1 section, emit `status: blocked` — there is nothing to promote.
