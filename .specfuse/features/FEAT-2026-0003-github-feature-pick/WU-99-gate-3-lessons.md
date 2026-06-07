---
id: FEAT-2026-0003/G3-LESSONS
type: lessons
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.404542
input_tokens: 8
output_tokens: 11364
---

# Gate 3 lessons learned

**Objective.** Promote the generalizable subset of gate 3's
retrospective into durable entries appended to
`.specfuse/LEARNINGS.md`.

**Context.** Read this feature's `RETROSPECTIVE.md` (gate-3
section, written by `G3-RETRO`). `LEARNINGS.md` is read at
planning time for every future feature — this is the pump that
turns one feature's experience into better plans for the next.
Gate 3 is the loop's first gate that delivers a *live*
integration (the smoke against `RestoManagerApp/Backend#287`),
the first gate that ships a new state backend, AND the closing
gate of the loop's first multi-gate dogfood. Lessons about:
- The offline/live split (T05+T06 offline; T07 live) — did the
  cut work the way `[FEAT-2026-0003/G1-LESSONS]` predicted?
- Authoring a WU whose verification is fundamentally human
  (T07's smoke journal) — the prose-artifact-gates problem from
  `[FEAT-2026-0003/G2-LESSONS]`, applied to a *live integration*
  rather than a *skill markdown*.
- Multi-gate forward design — how well `plan-next` drafts hold
  up after three gates of compounding context drift.

Append only; de-duplicate against existing entries (including
the gate-1 entries tagged `[FEAT-2026-0003/G1-LESSONS]` and
gate-2 entries tagged `[FEAT-2026-0003/G2-LESSONS]`).

**Acceptance criteria.**
1. New entries appended to the root `.specfuse/LEARNINGS.md`,
   each phrased as a reusable rule that would change how a
   future WU is written or executed, tagged
   `[FEAT-2026-0003/G3-LESSONS]`.
2. Feature-specific observations stay in `RETROSPECTIVE.md` and
   are NOT promoted (the bar from gates 1-2 lessons holds —
   "would this change a FUTURE WU?").
3. Entries de-duplicate against existing LEARNINGS (a near-
   restatement of an existing rule is not appended; refine the
   existing rule via a separate edit if needed — but not in this
   WU).
4. If gate 3 surfaced a lesson that contradicts an existing
   LEARNINGS entry, note the contradiction explicitly in the
   new entry rather than silently overriding (gates 1-2 lessons
   discipline).
5. Multi-gate-specific lessons (rules about plan-next quality,
   gate-arc coherence, cross-gate context drift) are flagged
   in their tag suffix so a future feature can grep for them:
   `[FEAT-2026-0003/G3-LESSONS/multi-gate]` for those entries.

**Do not touch.** Source code, existing `LEARNINGS.md` entries
(append only — never edit prior entries), `RETROSPECTIVE.md`,
any binding rule, any skill, generated directories, secrets,
`.git/`. This WU edits exactly one file:
`.specfuse/LEARNINGS.md` (append only).

**Verification.** The `doc` gates in
`.specfuse/verification.yml`.

**Escalation triggers.** If nothing in gate 3 generalizes
beyond this feature, append nothing and say why in the RESULT
block. Promoting noise is worse than promoting nothing (gate-1
posture). If the gate-3 retrospective's `## Multi-gate proof`
subsection implies the loop's *methodology itself* needs
revision (not just per-WU craft), flag LOUDLY in the RESULT
block — that is a methodology-level escalation that belongs in
`docs/methodology.md`'s evolution, not a LEARNINGS append.
