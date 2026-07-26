---
id: FEAT-2026-0069/G1-PLAN
type: plan-next
status: done
attempts: 2
planned_cost_usd: 5.00
oracle_env: macos_local
duration_seconds: 2260.813
cost_usd: 16.43642
input_tokens: 3289
output_tokens: 138242
---

# Gate 1 plan-next — draft gate 2's work units

**Objective.** Draft gate 2's substantive work units and write `GATE-01-REVIEW.md`, so
the human can review-and-arm the discovery re-keying against what gate 1 actually
emitted rather than against what gate 1 was predicted to emit.

**Context.** This is `FEAT-2026-0069/G1-PLAN`. Gate 1 landed the check-target axis in the
schema and the validator. Gate 2's job, per `PLAN.md`'s "Gate 2 sketch": make
`/derive-monitoring` emit **1 component with N targets** for a deployable carrying N
triggers, instead of N components.

Read `PLAN.md` (the gate 2 sketch is a starting point, explicitly **not binding**),
`RETROSPECTIVE.md` from the close-intermediate that just ran, this feature's
`events.jsonl`, root `.specfuse/LEARNINGS.md`, and — load-bearing here — the **actual
emitted shape** of `targets` as gate 1 shipped it, in `.specfuse/monitoring.yml.example`
and `specfuse/loop/lint_monitoring.py`. The whole reason gate 2 is drafted now rather
than at feature-drafting time is that the fixture must be authored against a real emitted
shape.

Apply `.specfuse/skills/authoring-work-units/SKILL.md` for per-WU craft — §10's
helper-duplication pre-flight and §12's red-test-first rule especially. Binding rules
under `.specfuse/rules/` apply, `planning-discipline.md` included.

**Acceptance criteria.**

1. Gate 2's substantive WU files exist with `status: draft` (unarmed), each with the five
   mandatory body sections, and each added to `PLAN.md`'s `gates[]` graph **above** the
   existing `G2-CLOSE` entry.
2. `G2-CLOSE`'s `depends_on` is updated to list every substantive WU drafted.
3. Every drafted `implementation` WU names, as its first acceptance criterion, a scoped
   test that **fails on HEAD before that WU runs** (`/authoring-work-units` §12), or
   carries an explicit `Red-test exempt: <reason>` line.
4. Gate 2's definition of done is preserved as the falsifiable core: a fixture whose
   **single deployable carries N triggers** yields **one** component with **N** targets.
   The sketch's four elements — re-key `discover_components` onto deployment evidence, the
   N-trigger fixture, mechanical target-list generation, skill method prose — are each
   either drafted as a WU or explicitly deferred with a reason.
5. **§10 pre-flight run and recorded** for every symbol the drafted WUs touch. At minimum
   enumerate `discover_components`, `suggest_checks`, `render_monitoring_yml`,
   `audit_diagnosability`, and the `_STACK_A_PATTERNS` / `_STACK_A_TREE` fixtures — gate 1
   already found that these are coupled through `TestDiscoveredConfigPassesLint`, and the
   re-key touches more of them than T03 did. Every hit is either in scope for a drafted WU
   or named in that WU's "Do not touch" with an explicit reason.
6. **The extractability claim is not laundered through a fixture.** `PLAN.md` records that
   the issue's "mechanically extractable" claim is confirmed only against a repo outside
   this tree. A fixture authored in gate 2 is evidence that the *algorithm* works on the
   fixture — it is not evidence that the claim holds on real repos. Any drafted WU whose
   acceptance rests on that claim must say so, and `G2-CLOSE` must carry it as a
   `## What the loop did NOT verify` entry.
7. `GATE-01-REVIEW.md` exists: what gate 1 shipped, what changed from the sketch and why,
   the §10 enumeration from AC5, the per-WU cost estimates, and the open questions the
   human should decide at arming.
8. **Runtime probe for the re-key (`planning-discipline.md` §4, and `GATE-01.md`'s arming
   discipline).** The re-key changes what discovery returns for existing fixtures — a
   behavioral default change, which may not be armed on "mechanical, nothing
   design-open." Apply the re-key locally, run the **full** oracle
   (`python3 -m unittest discover -s tests -v`), and paste the failure list into
   `GATE-01-REVIEW.md`. That list becomes the drafted WU's enumerated test surface.
9. Each drafted WU carries a `planned_cost_usd`. Their sum plus gate 1's actual should
   reconcile against `PLAN.md`'s $34.00 feature-level figure; if it does not, say so in
   the review artifact rather than silently adjusting either number. `PLAN.md`'s Notes
   predict the lint cost-delta WARN converges once this WU runs — confirm it did, or
   explain why not.
10. Gate 2's `cost_budget_usd: 18.0` in `GATE-02.md` is either confirmed as still right or
    revised with a reason, now that gate 1's actual spend is known.
11. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0069-monitoring-check-targets`
    passes.

**Do not touch.** Gate 1's WU files or `GATE-01.md`'s status (the human flips it to
`passed` at arming). `PLAN.md`'s `status` field — the driver owns terminal flips. The
production surfaces themselves: this WU drafts plans, it does not implement gate 2. The
local re-key from AC8 is a **probe** — revert it; do not leave it in the tree. `.git/`,
secrets. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set the driver runs for `type: plan-next`, plus the
plan lint in AC11.

**Escalation triggers.** Emit `status: blocked` if the AC8 probe shows the re-key cascades
beyond what one gate can hold (for instance, if it forces changes to the diagnosability
audit or to the skill's Step 1 contract in ways that are themselves multi-WU) — that is a
scope finding for the operator, and drafting a gate that cannot fit is worse than halting.
Also block if gate 1's retrospective contradicts `PLAN.md`'s premise that the two gates
are separable. Blocked is a respectable outcome (`result-contract.md` rule 4).
