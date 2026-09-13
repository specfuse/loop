---
id: FEAT-2026-0106/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
produces:
  - docs/methodology.md
  - .specfuse/rules/close-discipline.md
---

# Document what a close now writes, and what it no longer does

**Objective.** Record the new closing shape where the surfaces that govern
behaviour are actually read: the methodology's ceremony section and the
close-discipline rule.

**Context.** FEAT-2026-0106/T04. `docs/methodology.md` §6 already states the
ceremony-proportionality threshold and `close-discipline.md` §§1–5 state what
a close owes. Both now describe something that is only conditionally true.
This unit reconciles them rather than opening a third account of the same
rule — the same failure `[FEAT-2026-0104/operator/...]` names for criteria and
#3272 names for LEARNINGS entries: a rule with three homes drifts in two of
them.

**Acceptance criteria.**

- `docs/methodology.md` states when reflective prose is written and when it is
  not, naming the off-plan signal rather than restating its implementation,
  and reconciles with §6's existing threshold rather than duplicating it.
- `.specfuse/rules/close-discipline.md` states which of its obligations are
  now conditional and which are not, with measurements explicitly named as
  unconditional and the reason given — the judge reads them.
- The roadmap row's superseded "only on `not_met`" is recorded once, with the
  ordering reason, in the methodology rather than only in this feature's
  `PLAN.md`, so a later reader of the roadmap finds why it changed.
- `python3 .specfuse/scripts/leak_scan.py --all` exits 0 over the edited
  prose: no real paths, org names or home directories.

**Do not touch.** Driver code — every behaviour this unit describes is built
by T01–T03 and this unit changes none of it. `.specfuse/LEARNINGS.md`, which
the close owns. The sibling WU files in this gate.

*Red-test exempt: prose reconciliation across two existing documents; the
checks are the greps above plus the human reflection note, and no behaviour
changes.*

**Verification.** Narrow tier for `implementation`, plus
`python3 .specfuse/scripts/leak_scan.py --all` and
`grep -n "reflect" docs/methodology.md .specfuse/rules/close-discipline.md`
to confirm both surfaces carry the same account.

**Escalation triggers.** Stop with `status: blocked` if what T01–T03 built
contradicts what this plan says they would — documenting the plan's intent
over the tree's behaviour is how a doc becomes a lie.
