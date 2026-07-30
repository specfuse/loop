---
id: FEAT-2026-0053/G2-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
provenance: "Required by .specfuse/rules/close-discipline.md and by the linter's non-terminal closing-shape check (close-intermediate immediately followed by plan-next); not part of PLAN.md's gate-2 sketch, which enumerated only the five substantive items."
---

# Draft gate 3 — docs and methodology rewrite

**Objective.** Draft gate 3's substantive work units into `PLAN.md` ahead of the
existing `G3-CLOSE` entry, and write `GATE-03-REVIEW.md` for the human
review-and-arm checkpoint.

**Context.** Correlation ID `FEAT-2026-0053/G2-PLAN`. Depends on
`G2-CLOSE-INTERMEDIATE`, whose retrospective and lessons are this unit's primary
input — gate 3 is drafted from what gate 2 actually learned, not from the sketch
gate 1 wrote.

**The review artifact is named for the gate being armed, not the gate being
closed.** `assert_gate_review_exists` requires **`GATE-03-REVIEW.md`** —
`close-discipline.md` §4 records this as the single most expensive guard in the
system ($53.11 of refused-attempt spend across the observed corpus).

**Gate 3 is the terminal gate and already holds `G3-CLOSE`.** Insert gate 3's
substantive WUs **before** that entry in `PLAN.md`'s task graph and set
`G3-CLOSE`'s real `depends_on` (it currently carries an empty list with a
comment saying this unit sets it). The terminal gate keeps a single `close` WU —
do not convert it to the intermediate pair.

**What gate 3 is for.** Making `auto` legible to someone who did not build it.
PLAN.md's scope boundary names gate 3 as *"docs and methodology rewrite"*. The
concrete surface, at minimum:

- `docs/methodology.md` — the autonomy dial as a first-class concept: what
  `auto` / `review` / `supervised` each mean now that the run loop reads them,
  what an auto-arm is, and where the human checkpoints actually live (PR review,
  and every escalation).
- The seven-plus-one stop classes documented as an operator-facing reference —
  a parked `auto` feature is diagnosable only if the reader can map a fired
  class to a fix.
- `docs/dev/auto-arm-recovery.md` (shipped by T06) folded into the methodology
  rather than left as a dev note.
- Migration guidance for existing features and downstream projects: what
  appears in a repo when a driver at this version runs (`PLAN.baseline.json`,
  `FEATURE-REVIEW.md`, `LEARNINGS-pending.md`, `pre-arm/*` tags, two new event
  types), and what an operator must do to opt a feature into `auto`.
- Whatever gate 2's retrospective surfaces as needing a durable home.

**Dogfood obligation.** The plan-next contract fields are, by gate 2, blocking
under `auto` — this unit's own output must carry them: `open_questions:` in
`GATE-03-REVIEW.md`'s frontmatter (empty only if genuinely empty),
`provenance:` on any WU added beyond gate 2's understanding of gate 3, and
`human_only: true` where warranted.

**Acceptance criteria.**

1. `GATE-03-REVIEW.md` exists in the feature directory, is non-empty, and its
   frontmatter carries an explicit `open_questions:` list.
2. `GATE-03-REVIEW.md` contains a `## Doubt` section — the same named section
   T08's accumulation copies verbatim.
3. `PLAN.md`'s gate 3 `work_units` list contains at least one substantive entry
   at `status: draft`, ordered before `G3-CLOSE`, and `G3-CLOSE`'s `depends_on`
   names them.
4. Every drafted gate-3 WU file exists, is `status: draft`, and carries the five
   mandatory body sections.
5. Drafted WUs cover, at minimum: the methodology rewrite of the autonomy dial;
   the operator-facing stop-class reference; and migration guidance for existing
   features and downstream projects. Sizing may merge these; three subjects, not
   necessarily three WUs.
6. Every drafted WU carries a `planned_cost_usd`, and `GATE-03.md` carries a
   `cost_budget_usd` equal to their sum plus one re-attempt of the largest.
7. `PLAN.md`'s `planned_cost_usd` is re-baselined to include gate 3's drafted
   units, and the delta against the value this unit found is stated in
   `GATE-03-REVIEW.md`.
8. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0053-auto-mode`
   exits zero, and
   `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0053-auto-mode --just-closed-gate 2`
   prints no plan-next-draft warnings — under the contract gate 2 made blocking,
   a warning here would park this very feature if it were running `auto`.

**Do not touch.** Source files owned by T05–T09. `RETROSPECTIVE.md` — the
previous unit wrote it; this one reads it. `PLAN.md`'s `status` field — the
terminal flip belongs to `G3-CLOSE`. The terminal gate's single-`close` shape.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set, plus criterion 8's two lint runs over
the whole feature folder. Drafted WUs are prose: criteria 4–5 are the structural
floor; the human at the arming checkpoint is the real quality gate, and
`GATE-03-REVIEW.md` exists to support that read.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if
gate 2's retrospective reports a finding that invalidates the drafted gate-3
shape — for example that `auto` as shipped cannot be described without also
changing behavior, which would make gate 3 an implementation gate wearing a docs
label. A docs gate drafted on a premise gate 2 disproved is worse than no draft.
