---
id: FEAT-2026-0109/G1-PLAN
type: plan-next
status: blocked_human
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
produces:
  - .specfuse/features/FEAT-2026-0109-tiered-verification/GATE-02-REVIEW.md
  - .specfuse/features/FEAT-2026-0109-tiered-verification/GATE-02.md
escalation_reason: deterministic_refusal_repeat
duration_seconds: 450.221
cost_usd: 3.093962
input_tokens: 62
output_tokens: 30356
---

# Draft gate 2 — the per-attempt tier — and its own oracle

**Objective.** Forward design: draft gate 2's work units and its
`feature_oracle`, and write the human review summary for gate 1.

**Context.** FEAT-2026-0109/G1-PLAN; read `PLAN.md`, `GATE-01.md`, and gate 1's
`RETROSPECTIVE.md`. Gate 2 is the per-attempt vs per-gate tier split: per
attempt, the unit's declared tests, tests touching changed files, lint, and the
feature oracle; once per gate before the close, the full suite with coverage,
bats, leak-scan and security.

**Gate 2 must declare its own `feature_oracle` (#3262).** A gate with no
substantive units carries no oracle requirement, which is why gate 2 has none
today — the moment you give it work units, the requirement lands and
`specfuse lint` will ERROR without one. Draft the oracle in the same pass as
the units, and state in the review summary **how gate 2's oracle advances
gate 1's**, per the `plan-next` obligation FEAT-2026-0101/T04 added. Nothing
can decide mechanically whether one shell command is a stronger proof than
another; that judgement is yours to write down.

**The open design question gate 1 was sequenced to inform.** "Tests touching
changed files" needs a concrete rule — import graph, path convention, a
declared mapping, or the unit's own `produces:` list. Gate 1 makes the driver's
failure path explicit, which is the context that should decide it. Surface the
options and your recommendation in the review summary rather than settling it
silently in a WU body.

**Do not draft gate 3.** The installed-copy driver is deliberately alone in its
own gate — `[FEAT-2026-0019/G1]` records that a harness migration cannot be
decomposed into separately-gated units, and the last attempt cost $5.63 and 49
minutes of thrash. Gate 2's own `plan-next` drafts it, with the same atomicity
constraint restated there.

**Acceptance criteria.**

- `GATE-02.md` carries a definition of done, substantive work units drafted at `status: draft`, and a non-empty `feature_oracle` — `grep -n "feature_oracle" GATE-02.md` returns it.
- Each drafted unit carries the five mandatory sections and a `planned_cost_usd`; `specfuse lint .specfuse/features/FEAT-2026-0109-tiered-verification` reports zero ERROR.
- `GATE-02-REVIEW.md` carries the decisions and their rationale, an explicit "if you check only three things, check these" list, a roadmap-anchor check against `PLAN.md`'s `roadmap_goal`, and open questions each mapped to the draft WU it affects.
- The review summary states how gate 2's `feature_oracle` advances gate 1's, and names the chosen rule for "tests touching changed files" with the alternatives considered.
- The drafted units are left `draft` — arming is the human's act.

**Do not touch.** Source, tests, rules, templates; gate 1's WUs or its
`RETROSPECTIVE.md`; `GATE-03.md`; `.git/`, secrets.

**Verification.** The `plannext` gate set.

**Escalation triggers.** Emit `status: blocked` if gate 1's retrospective shows
attribution never fired — the per-attempt tier's safety rests on the failure
path working, and drafting a tier that narrows what runs per attempt on top of
an unexercised failure path is a decision for an operator, not a drafting
judgement.
</content>
