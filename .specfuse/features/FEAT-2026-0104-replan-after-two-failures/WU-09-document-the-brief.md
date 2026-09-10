---
id: FEAT-2026-0104/T09
type: implementation
status: draft
attempts: 0
planned_cost_usd: 1.50
produces:
  - docs/methodology.md
---

# Document what a spun-out unit's brief tells an operator

**Objective.** Record, where operators read it, that an exhausted unit now
escalates with a six-part brief whose default option is re-planning the
remaining gate — and that the driver recommends it rather than performing it.

**Context.** FEAT-2026-0104/T09. `docs/methodology.md` §2 already documents
the re-plan from the auto-close side, and T05 added the trigger's own half at
lines 187–193; this unit adds the operator-facing half and reconciles with
those sentences rather than opening a third account of the same mechanism.
The reader question to answer is the one the probe exposed: a unit that
escalates `spinning_detected` has *already* been re-planned once
automatically, so the brief's option is widening a spent remedy, not trying
one. `.specfuse/rules/operator-escalation.md` owns the six-part contract —
link it, do not restate it.

**Acceptance criteria.**

- `docs/methodology.md` states what a `blocked_human` spin-out now prints and
  records, names the six-part contract by link, and says which escalation
  reasons carry the re-plan option — consistent with T07's flag-scope table
  rather than a second, drifting list.
- The same section states that the option is a recommendation the operator
  executes, and names the command T07 chose.
- `grep -n "replan" docs/methodology.md` shows the auto-close sentence, T05's
  trigger paragraph and this unit's operator paragraph reading as one
  account, not three.
- `python3 .specfuse/scripts/leak_scan.py --all` exits 0 over the edited
  prose: no real paths, org names or home directories.

*Red-test exempt: prose reconciliation across three existing paragraphs; the
check is the grep above plus the human reflection note, and no behaviour
changes.*

`produces: docs/methodology.md` is deliberately re-declared after T05
delivered it — `check_produces_satisfiability` WARNs on that and asks for the
incremental edit in writing. The incremental edit is one new paragraph
adjacent to T05's, covering the operator-facing half (what the brief prints,
which reasons carry the re-plan option, and that it recommends rather than
executes); T05's paragraph is edited only where the two would otherwise read
as separate accounts.

**Do not touch.** Driver code — every behaviour this unit describes is built
by T06–T08 and this unit changes none of it. `.specfuse/LEARNINGS.md`, which
the close owns. `.specfuse/rules/operator-escalation.md`. The sibling WU
files in this gate.

**Verification.** Narrow tier for `implementation`: the `code` gates minus
`tier: broad`, plus `python3 .specfuse/scripts/leak_scan.py --all` and the
grep above.

**Escalation triggers.** Stop with `status: blocked` if T06–T08 built
something other than what this unit is asked to describe — documenting the
plan's intent over the tree's behaviour is how a doc becomes a lie.
