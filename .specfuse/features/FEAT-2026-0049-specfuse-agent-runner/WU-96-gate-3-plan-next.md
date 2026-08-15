---
id: FEAT-2026-0049/G3-PLAN
type: plan-next
status: done
attempts: 1
planned_cost_usd: 6.00
model: opus
effort: high
gate_set: plannext
driver_version: 0.11.0
started_at: 2026-08-11T05:03:09.132845+00:00
duration_seconds: 1155.799
cost_usd: 11.773772
input_tokens: 168
output_tokens: 79252
---

# G3-PLAN — draft gate 4 and write its review

**Context.** `FEAT-2026-0049/G3-PLAN`. Gate 4 is the feature's terminal gate and
its last action class: the agent advances features by reading the `queue:` top,
invoking `specfuse run` **as a subprocess**, classifying the driver's halt,
escalating on `awaiting_review`, and switching to the next workable item.
`GATE-04.md` holds the definition of done and the one constraint that has had to
survive since draft time; this unit turns that into work units against the
conductor and the five providers as they actually shipped.

Two things this unit inherits and must not rediscover:

- **The subprocess invariant is not stylistic.** `GATE-04.md` names the two live
  defects that make in-process invocation wrong (#757, #1040). A drafted work
  unit that imports `loop.run` has broken the feature's central design decision;
  `GATE-04.md`'s arming discipline says to check it at arming, and this unit is
  what makes that check possible by writing WUs that can be checked.
- **Drafting features is out of scope**, per PLAN.md's scope boundary. A
  drafting-needed queue top escalates; async drafting is FEAT-2026-0050, which
  lists this feature as its blocker.

**The terminal close needs sharpening, not just renumbering.** `WU-92-gate-4-close.md`
is a placeholder written before gates 2 and 3 existed. Two known gaps: its
acceptance criteria were drafted against a guess at what the feature would build,
and `specfuse lint` currently WARNs that its body never instructs the agent to
reconcile the auto-close debt markers left by earlier gates — a guard
(`assert_autoclose_debt_reconciled`) that refuses *after* dispatch, so the
mismatch costs a full re-attempt. This unit sharpens both.

**Acceptance criteria.**

1. Gate 4's substantive work units are drafted into `PLAN.md`'s graph with real
   `depends_on` edges and matching `WU-*.md` files at `status: draft`, each
   applying `/authoring-work-units` — in particular §12's red-test bullets.
2. `GATE-04-REVIEW.md` exists and is non-empty: what gate 3 proved, what it
   deliberately did not, and what the terminal gate must therefore establish. Its
   frontmatter carries an explicit `open_questions:` list.
3. Each drafted WU carries a `planned_cost_usd`, `GATE-04.md` gains a
   `cost_budget_usd` equal to their sum plus one re-attempt of the largest, and
   `PLAN.md`'s `planned_cost_usd` is raised to the new sum of all WU estimates.
4. `WU-92-gate-4-close.md`'s `depends_on` is set to gate 4's real work units, and
   its acceptance criteria are sharpened against what the feature actually built
   — including an explicit instruction to reconcile every outstanding
   `specfuse:autoclose-debt` marker, which `specfuse lint` flags as missing today.
5. Confirm explicitly whether any drafted WU flips a default or a severity, per
   `planning-discipline.md` §4 — checked and stated, not assumed. If one does,
   run the §4 runtime probe and paste its failure list into the gate review.
6. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any `specfuse/` source. `.specfuse/roadmap.md`. Gate 1's,
gate 2's and gate 3's WU files, `RETROSPECTIVE.md`, `GATE-02-REVIEW.md`, and
`GATE-03-REVIEW.md` — this unit plans forward, it does not revise what closed.
`PLAN.md`'s `status` field: the driver owns the terminal flips. The driver owns
all git; this session edits files only and runs no `git` command.

**Verification.** The `plannext` gate set from `.specfuse/verification.yml`, plus
`specfuse lint .specfuse/features/FEAT-2026-0049-specfuse-agent-runner` passing
and `specfuse lint --closing` exiting 0.

**Escalation triggers.** If gate 3's retrospective shows the provider protocol
did not survive contact with the findings pair — a verb that did not fit, an
outcome shape that could not express what happened — stop and escalate rather
than drafting the feature provider against a seam that needs redesigning. If
halt classification turns out to need the driver to report something it does not
currently report, stop and name it: changing the driver is outside this feature's
scope boundary and is a plan change, not a gate-4 work unit. If the queue top at
drafting time is a feature that needs drafting rather than advancing, that is the
escalation path gate 4 is meant to *build*, not a blocker for planning it — draft
the escalation, do not stop.
