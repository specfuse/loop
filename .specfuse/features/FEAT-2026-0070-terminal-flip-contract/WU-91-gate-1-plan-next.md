---
id: FEAT-2026-0070/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
---

# Gate 1 plan-next — draft gate 2's work units

**Objective.** Draft gate 2's substantive work units and write **`GATE-02-REVIEW.md`**, so
the human can review-and-arm the auto-close debt work against what gate 1 actually shipped.

**Context.** This is `FEAT-2026-0070/G1-PLAN`. Gate 2's job, per `PLAN.md`'s sketch: make
an auto-closed gate's skipped deferred-verification walk a visible debt rather than a
silent saving (#241).

**Write `GATE-02-REVIEW.md`, not `GATE-01-REVIEW.md`.** The driver's
`assert_gate_review_exists` computes the filename from the **next** gate. This is the most
expensive guard in the system — 15 fires, $53.11 measured across 9 repositories — and it
has cost three features an attempt each. `close-discipline.md` §4 states the rule; the
arm-time predictor added by #269 will also warn if this WU's body omits the literal.

Read `PLAN.md` (the gate 2 sketch is a starting point, explicitly **not binding**),
`RETROSPECTIVE.md` from the close-intermediate that just ran, this feature's
`events.jsonl`, root `.specfuse/LEARNINGS.md`, and the **actual shape** of what gate 1
shipped — especially T02's primitive, since gate 2's post-pass invariant may want to reuse
its disk-reading approach.

Apply `.specfuse/skills/authoring-work-units/SKILL.md` — §10's helper-duplication
pre-flight and §12's red-test-first rule especially. Binding rules under `.specfuse/rules/`
apply, `planning-discipline.md` included.

**Acceptance criteria.**

1. Gate 2's substantive WU files exist with `status: draft`, each with the five mandatory
   body sections, each added to `PLAN.md`'s `gates[]` graph **above** the existing
   `G2-CLOSE` entry.
2. `G2-CLOSE`'s `depends_on` is updated to list every substantive WU drafted.
3. Every drafted `implementation` WU names, as its first acceptance criterion, a scoped
   test that **fails on HEAD before that WU runs**, or carries an explicit
   `Red-test exempt: <reason>` line.
4. **`GATE-02-REVIEW.md`** exists and is non-empty: what gate 1 shipped, what changed from
   the sketch and why, the §10 enumeration, the runtime-probe failure list from AC5, per-WU
   cost estimates, and the open questions to decide at arming.
5. **Runtime probe for the severity flip (`planning-discipline.md` §4).** Gate 2's likely
   shape includes a post-pass invariant that escalates when a terminal close ignores an
   auto-closed predecessor's debt. That is a new blocking condition and may **not** be
   armed on "mechanical, nothing design-open". Apply it locally, run the **full** oracle
   (`python3 -m unittest discover -s tests -v`), and paste the failure list into
   `GATE-02-REVIEW.md`. Then revert the probe and confirm the tree is clean.
6. **Satisfiability, answered explicitly (§2).** Enumerate the features in this repo that
   have auto-closed a gate and state what the proposed invariant reports on each. If it
   fires on a feature that closed correctly, the invariant is unsatisfiable as designed and
   the review must say so rather than deferring the question to the implementing WU.
7. **§10 pre-flight run and recorded** for every symbol the drafted WUs touch — at minimum
   `evaluate_auto_close`, `AutoCloseDecision`, `fire_terminal_flips`,
   `assert_terminal_flips_fired`, and whatever T02 named its primitive. Every hit is either
   in a drafted WU's scope or named in its "Do not touch" with a reason.
8. **The cost-reintroduction trap is stated.** Auto-close exists to avoid an agent
   dispatch. A fix that writes the enumeration by dispatching a session has traded the
   defect for the cost the predicate was built to prevent — `[FEAT-2026-0039/G2-CLOSE]`
   records that an auto-closed gate's skipped ceremony is a *debt entry, not a saving*, and
   that reconciling it later cost **more** because the session had not written those WUs.
   Any drafted WU must say which side of that trade it lands on.
9. Each drafted WU carries a `planned_cost_usd` at or above its type's floor
   (`planning-discipline.md` §5: $6.00 `plan-next`, $5.00 `close`, $4.50
   `close-intermediate`; implementation priced from evidence). Their sum plus gate 1's
   actual should reconcile against `PLAN.md`'s $32.00 — if it does not, say so in the
   review rather than silently adjusting either number.
10. `GATE-02.md`'s `cost_budget_usd: 16.0` is confirmed as still right or revised with a
    reason, now that gate 1's actual spend is known.
11. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0070-terminal-flip-contract`
    passes.

**Do not touch.** Gate 1's WU files or `GATE-01.md`'s status (the human flips it to
`passed` at arming). `PLAN.md`'s `status` field — the driver owns terminal flips. The
production surfaces: this WU drafts plans, it does not implement gate 2. The local probe
from AC5 is a **probe** — revert it. `.git/`, secrets. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set the driver runs for `type: plan-next`, plus the
plan lint in AC11.

**Escalation triggers.** Emit `status: blocked` if AC5's probe shows the invariant firing
on features that closed correctly and no narrowing makes it satisfiable — that is a design
finding for the operator, and drafting a gate around an unsatisfiable predicate is worse
than halting. Also block if gate 1's retrospective contradicts `PLAN.md`'s premise that the
flip contract and the auto-close debt are separable concerns: that would mean the gate cut
was wrong, which is a replan decision. Blocked is a respectable outcome
(`result-contract.md` rule 4).
