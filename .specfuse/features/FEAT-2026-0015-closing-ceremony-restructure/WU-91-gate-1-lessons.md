---
id: FEAT-2026-0015/G1-LESSONS
type: lessons
effort: low
status: pending
attempts: 0
planned_cost_usd: 0.20
---

# Gate 1 lessons

**Objective.** Promote durable, generalizable rules from Gate 1's
retrospective to `.specfuse/LEARNINGS.md`. Feature-specific noise
stays in `RETROSPECTIVE.md`.

**Context.** Correlation ID `FEAT-2026-0015/G1-LESSONS`. Reads
this feature's `RETROSPECTIVE.md` (just-written by G1-RETRO) and
the existing `.specfuse/LEARNINGS.md` to de-duplicate. Reference
binding rules under `.specfuse/rules/`.

**Acceptance criteria.**

1. For every generalizable rule surfaced in `RETROSPECTIVE.md`,
   append an entry to `.specfuse/LEARNINGS.md` tagged
   `[FEAT-2026-0015/G1]`. Phrase each as a rule that would change
   how a FUTURE WU is written or executed — not a one-off
   observation. De-duplicate against entries already in LEARNINGS.
2. If nothing generalizes, append nothing and explicitly state so
   in the RESULT block. A blank lessons append IS a valid outcome
   per the methodology.
3. Likely candidates to consider (not exhaustive, not required):
   - Whether the `close-intermediate` vs `close` distinction
     surfaced any naming or documentation ambiguity worth a rule.
   - Whether T02's helper-duplication trigger fired and produced a
     new rule beyond the existing §10 (e.g. a specific search
     pattern to add).
   - Whether T03's `tests/test_template_closing_shapes.py` shape
     suggests a general template-coverage rule.
4. Authoring-work-units `[FEAT-2026-0015/G1]` entries follow the
   format documented at the top of `.specfuse/LEARNINGS.md`.

**Do not touch.** Source code, templates, skills, other WU files,
secrets, `.git/`. Agent writes to `.specfuse/LEARNINGS.md` only
(append). See `.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in `.specfuse/verification.yml`
(file exists / something changed) — unless AC2's "nothing
generalized" outcome fires, in which case the WU emits
`status: complete` with a brief justification and the gate set
verifies that no garbage was appended.

**Escalation triggers.**

1. **Retrospective missing.** If `RETROSPECTIVE.md` is empty or
   absent (G1-RETRO didn't land), emit `status: blocked`.
2. **Duplicate-rule risk.** If a candidate rule appears to
   duplicate an existing LEARNINGS entry, do NOT append a duplicate;
   note in the RESULT block that the rule was already captured.
