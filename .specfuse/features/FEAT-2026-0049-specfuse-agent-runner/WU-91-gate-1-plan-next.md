---
id: FEAT-2026-0049/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
---

# G1-PLAN — draft gate 2 and write its review

**Context.** Gate 2 is the four action providers over already-shipped
composition: bugs (`run_bug_lane`), triage (`apply_triage`, honouring
`rules.triage.auto`), findings-diagnose (`diagnose_cli`), findings-autofix
(`run_autofix`), plus parsing answered needs-human issues. PLAN.md's gate map is
the intent; this unit turns it into work units against the conductor's real
shape, which only exists now that gate 1 has run.

**The sizing decision this unit owns.** Gate 2 was drafted as the largest gate and
PLAN.md records the risk explicitly: if drafting it against real code shows it
oversized, the split is findings into their own gate, making this a four-gate
feature. Take that decision here, with evidence, and record which way it went and
why. Deferring it again is not an option — this is the unit that has the
evidence.

**Acceptance criteria.**

1. `GATE-02-REVIEW.md` exists and is non-empty: what gate 1 proved, what it
   deliberately did not, and what gate 2 must therefore establish.
2. Gate 2's substantive work units are drafted into PLAN.md's graph with real
   `depends_on` edges and matching `WU-*.md` files at `status: draft`. Each
   applies `/authoring-work-units` — in particular §12's red-test bullets, since
   every provider introduces new behavior.
3. Each drafted WU carries a `planned_cost_usd`, and `GATE-02.md` gains a
   `cost_budget_usd` equal to their sum plus one re-attempt of the largest.
4. The gate-2-vs-four-gate sizing decision is recorded in `GATE-02-REVIEW.md`
   with the evidence that settled it.
5. Confirm explicitly whether any drafted gate-2 WU flips a default or a
   severity. The expectation is none — the providers consume existing predicates
   rather than changing them — but per `planning-discipline.md` §4 that must be
   checked and stated, not assumed.
6. Each drafted provider WU names the shipped function it composes and asserts it
   is consumed unmodified. PLAN.md's scope boundary forbids modifying the driven
   surfaces; a WU that needs to change one is a plan change, not a WU detail.
7. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any `specfuse/` source. Gate 3's WUs (`G2-PLAN`'s, when gate 2
closes) — except the terminal `close` placeholder's `depends_on`, which stays as
it is until gate 3 is actually drafted. `.specfuse/roadmap.md`. Gate 1's WUs or
`RETROSPECTIVE.md`.

**Verification.** The `plannext` gate set from `.specfuse/verification.yml`, plus
`specfuse lint .specfuse/features/FEAT-2026-0049-specfuse-agent-runner` passing
and `specfuse lint --closing` exiting 0.

**Escalation triggers.** If gate 1's retrospective shows the provider protocol
does not survive contact with a real provider — the risk T04's own escalation
trigger names — stop and escalate rather than drafting four WUs against a
protocol that needs redesigning first. If the sizing evidence is genuinely
ambiguous, say which way you lean and what evidence would settle it, rather than
splitting the gate on a coin flip.
