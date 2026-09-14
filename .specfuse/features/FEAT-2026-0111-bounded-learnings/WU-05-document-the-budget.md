---
id: FEAT-2026-0111/T05
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - docs/methodology.md
  - .specfuse/rules-local/README.md
---

# Document the budget, the accept step, and what the weights do not mean

**Objective.** Record where the word budget lives, how the distilled set is
chosen, and the limits of the weights — on the surfaces a human reads before
touching either.

**Context.** FEAT-2026-0111/T05. The 2,500-word figure has lived in a
`scaffold.py` comment where no operator finds it. `.specfuse/rules-local/README.md`
is what a project reads before adding a rule, and after this feature that
choice costs shared budget.

**Acceptance criteria.**

- `docs/methodology.md` states the binding-block budget, that it is enforced,
  and that `rules-local` entries are counted against it — so a project adding a
  local rule knows it is spending a shared allowance.
- `.specfuse/rules-local/README.md` states the sub-budget, points at the accept
  step, and says plainly that an entry already enforced by a guard or lint does
  not belong in the block.
- Both surfaces state that `reach` is a **tiebreaker with an age bias**, not a
  ranking, and that neither weight measures whether a rule improves a session's
  work — the honest limit, recorded where someone tuning the weights will read
  it rather than only in this feature's `PLAN.md`.
- `python3 .specfuse/scripts/leak_scan.py --all` exits 0 over the edited prose.

**Do not touch.** Driver code — every behaviour here is built by T01–T04.
`LEARNINGS.md`. The sibling WU files in this gate.

*Red-test exempt: prose across two existing documents; the checks are the
greps and the leak scan above, and no behaviour changes.*

**Verification.** Narrow tier for `implementation`, plus
`python3 .specfuse/scripts/leak_scan.py --all` and
`grep -n "2,500\|2500" docs/methodology.md .specfuse/rules-local/README.md`.

**Escalation triggers.** Stop with `status: blocked` if what T01–T04 built
contradicts what this plan says they would.
