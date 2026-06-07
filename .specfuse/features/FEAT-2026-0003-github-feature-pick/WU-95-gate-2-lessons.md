---
id: FEAT-2026-0003/G2-LESSONS
type: lessons
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Gate 2 lessons learned

**Objective.** Promote the generalizable subset of gate 2's retrospective into
durable entries appended to `.specfuse/LEARNINGS.md` (the root, cross-feature
file).

**Context.** Read this feature's `RETROSPECTIVE.md` (gate-2 section, written by
`G2-RETRO`). `LEARNINGS.md` is read at planning time for every future feature —
this is the pump that turns one feature's experience into better plans for the
next. Gate 2 is the loop's first gate that authors both code (a scaffolding
script) AND a skill (interactive flow). Lessons about the script/skill split,
about authoring skills as WUs, and about cross-WU file-count discipline at
scale are especially valuable here. Append only; de-duplicate against existing
entries (including the gate-1 entries tagged `[FEAT-2026-0003/G1-LESSONS]`).

**Acceptance criteria.**
1. New entries appended to the root `.specfuse/LEARNINGS.md`, each phrased as
   a reusable rule that would change how a future WU is written or executed,
   tagged with this gate's ID (`[FEAT-2026-0003/G2-LESSONS]`).
2. Feature-specific observations stay in `RETROSPECTIVE.md` and are NOT
   promoted (the bar from gate 1's lessons holds — "would this change a
   FUTURE WU?").
3. Entries de-duplicate against existing LEARNINGS (a near-restatement of an
   existing rule is not appended; refine the existing rule via a separate
   edit if needed — but not in this WU).
4. If gate 2 surfaced a lesson that contradicts an existing LEARNINGS entry,
   note the contradiction explicitly in the new entry rather than silently
   overriding.

**Do not touch.** Source code, existing `LEARNINGS.md` entries (append only
— never edit prior entries), `RETROSPECTIVE.md`, any binding rule, any
skill, generated directories, secrets, `.git/`. This WU edits exactly one
file: `.specfuse/LEARNINGS.md` (append only).

**Verification.** The `doc` gates in `.specfuse/verification.yml`.

**Escalation triggers.** If nothing in gate 2 generalizes beyond this
feature, append nothing and say why in the RESULT block. Promoting noise is
worse than promoting nothing (gate 1's lessons WU established this
posture).
