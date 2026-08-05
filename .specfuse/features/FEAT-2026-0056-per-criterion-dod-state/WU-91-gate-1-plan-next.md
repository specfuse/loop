---
id: FEAT-2026-0056/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
---

# Draft gate 2 — the incremental re-close policy

**Objective.** Draft gate 2's substantive work units and write `GATE-02-REVIEW.md`,
from gate 1's retrospective and `.specfuse/LEARNINGS.md`.

**Context.** This is `FEAT-2026-0056/G1-PLAN`, gate 1's forward-design unit. Gate 1
made per-criterion close state *recorded* and *linted*. Gate 2 makes it *consumed*:
a re-dispatched close reads the prior attempt's `GATE-NN-CRITERIA.md` and re-verifies
only the worklist. Read `PLAN.md`, `GATE-01.md`, `GATE-02.md`, and this gate's
`RETROSPECTIVE.md` before drafting.

`GATE-02.md` already records the intent captured at draft time — the worklist
definition, the run-once-per-oracle-command dedupe, the exclusion of the close's
feature-level question from the cache, and the requirement that a close say which
criteria it carried forward. **That is a proposal from a session that had not yet
seen gate 1 run.** Accept, revise, or reject it against what the retrospective
actually shows, and say which you did and why. A drafted intent inherited without
challenge is the failure `plan-next` exists to prevent.

Three constraints from `PLAN.md` are load-bearing and are not gate 2's to relitigate
without surfacing it loudly:

- **A `broad` oracle's green is never carried forward.** This is what makes the
  feature sound; T03's lint already enforces it. A gate 2 WU that weakens it is a
  design change, not an implementation detail.
- **The close's feature-level question never caches.** `[FEAT-2026-0057/G1-CLOSE]` —
  re-running every producing unit's own oracle is not the feature-level re-run
  `close-discipline.md` §1 asks for.
- **The savings claim was already re-baselined by T04.** Do not draft gate 2 against
  the roadmap's original "roughly halves close cost" wording; it no longer exists.

Apply `.specfuse/rules/planning-discipline.md` at draft time — §1's existing-mechanism
search for anything gate 2 designs, §2's satisfiability answer for any severity flip,
§3's flag-scope table for any behavior flag, §4's runtime probe requirement recorded
as an arming precondition in `GATE-02.md`, and §5's cost floors. Apply
`/authoring-work-units` §12: every behaviour-introducing implementation WU names a
scoped test that fails on HEAD before it runs.

Gate 2 is the terminal gate. Its closing sequence is the single `close` WU already
scaffolded as `WU-90-gate-2-close.md` — insert gate 2's substantive WUs **before** it
in `PLAN.md`'s graph and update that WU's `depends_on` to name them. Do not add a
`close-intermediate` or a second `plan-next`.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `GATE-02.md`'s `## Definition of done` is rewritten from the retrospective, with
   each drafted bullet traceable to a stated goal in `PLAN.md` or to something gate 1
   observed. Any bullet inherited unchanged from the draft-time proposal is marked as
   deliberately accepted, with one line of why.
2. Gate 2's substantive work units are written as `WU-*.md` files in this folder with
   `status: draft`, each carrying the five mandatory sections and a
   `planned_cost_usd`.
3. `PLAN.md`'s gate 2 `work_units` list names each drafted WU with its `depends_on`,
   ordered before the `G2-CLOSE` entry, and `G2-CLOSE`'s `depends_on` names every
   substantive WU drafted.
4. Every behaviour-introducing implementation WU drafted names a scoped test that
   fails on HEAD before it runs, or carries an explicit `Red-test exempt: <reason>`
   line.
5. `GATE-02.md`'s `## Arming discipline` section records the §4 runtime-probe
   requirement if any drafted WU flips a default or a severity, and states `not
   applicable` with a reason if none does.
6. `GATE-02-REVIEW.md` is written, with `open_questions` in its frontmatter as an
   explicit list — `[]` if nothing blocks execution. A missing field is not an empty
   list.
7. `GATE-02.md` carries a `cost_budget_usd` equal to the sum of its WU estimates plus
   one re-attempt of its largest WU, per `planning-discipline.md` §5's corollary.
8. Any revision to a not-yet-reached part of the plan is surfaced loudly in
   `GATE-02-REVIEW.md` rather than applied silently.
9. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0056-per-criterion-dod-state`
   exits 0 after the edits.

**Do not touch.** `GATE-01.md`'s status or its work units — gate 1 is closed and
`plan-next` never touches a passed gate. Any file under `specfuse/`. Any other
feature's folder under `.specfuse/features/`. `.specfuse/verification.yml`.
`.specfuse/rules/` and `.specfuse/templates/`. Generated directories, secrets,
`.git/`. The driver owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in `.specfuse/verification.yml` is this
unit's exit oracle. In addition run criterion 9's `lint_plan.py` invocation verbatim
and paste its output.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: gate
1's retrospective shows the recorded per-criterion state is not trustworthy enough to
build a skip policy on — that invalidates gate 2's premise and is an operator
decision, not something to draft around; a drafted WU would need to weaken the
"`broad` greens never carry forward" contract to be implementable; `lint_plan.py`
fails for a reason this unit did not introduce; or `GATE-02-REVIEW.md` cannot be
written with an explicit `open_questions` list because a genuine blocking question
exists — record the question rather than writing `[]`.
