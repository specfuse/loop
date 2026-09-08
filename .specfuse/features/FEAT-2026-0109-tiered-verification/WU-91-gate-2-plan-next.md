---
id: FEAT-2026-0109/G2-PLAN
type: plan-next
status: draft
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
produces:
  - .specfuse/features/FEAT-2026-0109-tiered-verification/GATE-03-REVIEW.md
  - .specfuse/features/FEAT-2026-0109-tiered-verification/GATE-03.md
  - .specfuse/features/FEAT-2026-0109-tiered-verification/PLAN.md
model: opus
effort: high
gate_set: plannext
---

# Draft gate 3 — the installed-copy driver, as one unit — and its own oracle

**Objective.** Forward design: draft gate 3's work unit and its
`feature_oracle`, and write the human review summary for gate 2.

**Context.** FEAT-2026-0109/G2-PLAN; read `PLAN.md`, `GATE-02.md`,
`GATE-03.md`, and gate 2's `## Gate 2` section of `RETROSPECTIVE.md`. Gate 3 is
the last gate and the terminal one: the driver runs from an installed copy, so
a unit editing `specfuse/loop/` no longer halts the run for a restart. Gate 2
measured that tax directly — gate 1 paid three restarts across three units, and
gate 2's own restart count is in its close.

**Gate 3 must declare its own `feature_oracle` (#3262).** A gate with no
substantive units carries no oracle requirement, which is why gate 3 has none
today; the moment you give it work, `specfuse lint` ERRORs without one. Draft
the oracle in the same pass as the unit, and state in the review summary **how
gate 3's oracle advances gate 2's**, per the `plan-next` obligation
FEAT-2026-0101/T04 added. Gate 2's oracle asserts which gates run per attempt
and that the broad set runs once before the close; gate 3's must assert
something about the driver's *own* execution surface that gate 2's cannot.
Nothing decides mechanically whether one shell command is a stronger proof than
another; that judgement is yours to write down.

**Gate 3 is deliberately atomic — this is binding on the draft.**
`[FEAT-2026-0019/G1]` records that a feature migrating the harness the driver
itself runs cannot be decomposed into separately-gated work units: each unit's
exit oracle is the very surface being migrated, so no unit can pass alone and
the driver thrashes. The last attempt cost $5.63 and 49 minutes before
abandonment. Draft gate 3 as **one** substantive unit, or as a `human` unit
recording an interactive migration — not as three units that look tidy in a
graph and deadlock in execution. If you conclude it genuinely needs more than
one, say why in the review summary and let the human decide at arm time rather
than drafting the decomposition and hoping.

**Drafting a gate means editing `PLAN.md`'s task graph, not only writing
files.** The deterministic guard `assert_next_gate_drafted_or_terminal` reads
`PLAN.md`'s `gates:` graph, not the files on disk; two attempts at gate 1's
`plan-next` were refused for writing a gate document and no graph entry. Gate 3
already carries a scaffolded `FEAT-2026-0109/G3-CLOSE` entry so lint reads gate
2 as non-terminal — insert the substantive unit's entry **above** it, with
`id`, `file` and `depends_on`, and make `G3-CLOSE` depend on it. Do this before
reporting, and re-read the graph afterwards to confirm the entry is there.

**The terminal close is different from gate 1's and gate 2's.** Gate 3's close
is a `close` (terminal), not a `close-intermediate`: it records a feature-level
`verdict`, the `close-discipline.md` §3 consumer-visible contract enumeration
across all three gates, and the §1-§2 obligations. `WU-90-gate-3-close.md`
already exists as a scaffold; check it says those things and revise it if it
does not.

**Acceptance criteria.**

- `PLAN.md`'s gate 3 entry has a non-empty `work_units` list with the substantive unit ahead of `G3-CLOSE`, each naming a `file` that exists on disk — this is what `assert_next_gate_drafted_or_terminal` reads.
- `GATE-03.md` carries a definition of done, the substantive unit drafted at `status: draft`, and a non-empty `feature_oracle` — `grep -n "feature_oracle" GATE-03.md` returns it.
- The drafted unit carries the five mandatory sections and a `planned_cost_usd`; `specfuse lint .specfuse/features/FEAT-2026-0109-tiered-verification` reports zero ERROR.
- `GATE-03-REVIEW.md` carries the decisions and their rationale, an explicit "if you check only three things, check these" list, an `open_questions:` frontmatter list (explicit, empty if nothing is open), a roadmap-anchor check against `PLAN.md`'s `roadmap_goal`, and open questions each mapped to the draft WU it affects.
- The review summary states how gate 3's `feature_oracle` advances gate 2's, and states explicitly whether gate 3 is drafted as one unit — and if not, why the `[FEAT-2026-0019/G1]` atomicity constraint does not apply.
- The drafted unit is left `draft` — arming is the human's act.

**Do not touch.** Source, tests, rules, templates; gate 1's and gate 2's WUs or
their `RETROSPECTIVE.md` sections; `.git/`, secrets. `PLAN.md` is in scope for
gate 3's graph entries only — edit that one list and nothing else in the file,
unless the close's cost reconciliation shows `planned_cost_usd` needs the
correction gate 2's review already flagged, in which case say so in the review
summary and leave the number to the human.

**Verification.** The `plannext` gate set.

**Escalation triggers.** Emit `status: blocked` if drafting gate 3 would require
editing gate 1's or gate 2's completed units, or if the installed-copy
migration cannot be given an exit oracle that runs against the *installed*
driver rather than the working tree — a gate whose oracle measures the copy it
is migrating away from proves nothing, and choosing a different oracle
environment is an operator decision.
