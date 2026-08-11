---
id: FEAT-2026-0049/G2-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
---

# G2-PLAN — draft the findings gate and write its review

**Context.** `G1-PLAN` split the findings action classes out of gate 2 with the
evidence recorded in `GATE-02-REVIEW.md` § "The sizing decision". It could not
place them: inserting a findings gate ahead of the features gate moves the
terminal close from gate 3 to gate 4, and gate 3's WUs were outside `G1-PLAN`'s
boundary. **This unit owns that restructure**, and it is the first thing to do —
everything else here depends on the gate numbers being settled.

The findings classes are two: undiagnosed finding issues through
`specfuse.monitor.diagnose_cli`, and diagnosed ones through
`specfuse.monitor.autofix_run.run_autofix`. Both are consumed unmodified per
PLAN.md's scope boundary. `GATE-02-REVIEW.md` records two facts about them that a
draft must be written against rather than rediscover: `diagnose_cli` *renders* a
diagnosis body from analysis JSON and neither produces the analysis nor posts the
comment, and `run_autofix` needs a `monitoring_config` with named components,
which this repo — a CLI tool with no deployable components — will never have.

**Acceptance criteria.**

1. The gate restructure lands in `PLAN.md`: a findings gate is inserted ahead of
   the features gate, the features gate and the terminal close move to their new
   numbers, and the terminal close WU's correlation ID, filename, and body agree
   with the new number. `specfuse lint <feature-dir>` passes afterwards.
2. `GATE-03-REVIEW.md` (or the review file matching the next gate's number after
   the restructure) exists and is non-empty: what gate 2 proved, what it
   deliberately did not, and what the next gate must therefore establish. Its
   frontmatter carries an explicit `open_questions:` list.
3. The next gate's substantive work units are drafted into `PLAN.md`'s graph with
   real `depends_on` edges and matching `WU-*.md` files at `status: draft`, each
   applying `/authoring-work-units` — in particular §12's red-test bullets.
4. Each drafted WU carries a `planned_cost_usd`, the gate file gains a
   `cost_budget_usd` equal to their sum plus one re-attempt of the largest, and
   `PLAN.md`'s `planned_cost_usd` is raised to the new sum of all WU estimates.
5. Each drafted provider WU names the shipped function it composes and asserts it
   is consumed unmodified. State explicitly how a WU whose target surface
   (`run_autofix`) cannot be exercised against this repository is verified, and
   what that leaves unproven.
6. Confirm explicitly whether any drafted WU flips a default or a severity. The
   expectation is none; per `planning-discipline.md` §4 that must be checked and
   stated, not assumed.
7. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any `specfuse/` source. `.specfuse/roadmap.md`. Gate 1's and
gate 2's WU files, `RETROSPECTIVE.md`, and `GATE-02-REVIEW.md` — this unit plans
forward, it does not revise what closed. The terminal close WU is in scope for
the renumbering in AC1 **only**: its acceptance criteria and body content stay as
drafted apart from the gate number it names.

**Verification.** The `plannext` gate set from `.specfuse/verification.yml`, plus
`specfuse lint .specfuse/features/FEAT-2026-0049-specfuse-agent-runner` passing
and `specfuse lint --closing` exiting 0.

**Escalation triggers.** If the restructure in AC1 cannot be done without
rewriting a `done` WU's frontmatter or an already-passed gate's file, stop and
say which — renumbering history is not a planning action. If gate 2's
retrospective shows the provider protocol did not survive contact with the four
real providers, stop and escalate rather than drafting two more against a seam
that needs redesigning. If the findings providers turn out to be unverifiable in
this repository in a way that makes the gate's definition of done unreachable —
not merely deferred — say so and name what would make it reachable, rather than
drafting WUs whose acceptance criteria cannot be met here.
