---
id: FEAT-2026-0049/G3-CLOSE-INTERMEDIATE
type: close-intermediate
status: draft
attempts: 0
planned_cost_usd: 4.50
---

# G3-CLOSE-INTERMEDIATE — gate 3 retrospective, lessons, docs

**Context.** `FEAT-2026-0049/G3-CLOSE-INTERMEDIATE`. Gate 3 is the first gate
whose deliverables cannot be exercised against the repository that ships them:
both findings providers are verified against fixtures, because this repo has no
deployable components and no `monitoring.yml`. This unit folds the
retrospective, the lessons, and the documentation for that gate into one session,
and it carries one obligation the other gates' closes did not.

**The obligation.** Gate 3's honest verification ceiling is *not* the same as
gates 1 and 2's. Those gates' criteria were met against this repo's live issues;
gate 3's were met against test doubles. The retrospective must say so in the
`## What the loop did NOT verify` section in those terms — naming which criteria
were proven only against fixtures and what live condition would prove them — so
the terminal close (`G4-CLOSE`) inherits a written record rather than having to
re-derive it. `GATE-03-REVIEW.md` § "What cannot be proven here, precisely" is the
starting point; do not simply copy it, check it against what the gate actually
built.

**Also inherited.** Gates 1 and 2 both auto-closed, so neither enumerated its
per-criterion deferred-verification list. `RETROSPECTIVE.md` carries a
`specfuse:autoclose-debt` marker for each — gate 1 (T01–T04, 27 criteria) and
gate 2 (T05–T08, 30 criteria). `WU-93` was drafted to reconcile gate 1's and
itself auto-closed, so **both markers are still open**. This unit reconciles what
it can at gate scope; whatever it cannot, it names explicitly for `G4-CLOSE`
rather than leaving the marker to be discovered at terminal-verdict time, where
`assert_autoclose_debt_reconciled` refuses after dispatch and costs a full
re-attempt.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` gains a `## Gate 3` section — cost against
   `cost_budget_usd`, attempts per work unit, and what actually happened, read
   from `events.jsonl` and WU frontmatter rather than estimated.
2. `RETROSPECTIVE.md`'s `## What the loop did NOT verify` carries a gate-3 entry
   naming, per acceptance criterion that was met only against fixtures, the live
   condition that would prove it — not a blanket "no live components" sentence.
3. The still-open `specfuse:autoclose-debt` markers for gates 1 and 2 are
   reconciled, or each unreconciled criterion is named individually with the
   reason it cannot be reconciled at this gate. A marker left silently in place
   is not a valid close.
4. Generalizable lessons are staged in `LEARNINGS-pending.md` in this feature
   folder. Under `autonomy_default: auto`, `assert_learnings_staged_under_auto`
   forbids touching `.specfuse/LEARNINGS.md`.
5. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any `specfuse/` source — a closing unit records, it does not
fix. `.specfuse/LEARNINGS.md` (staging file only, per criterion 4).
`.specfuse/roadmap.md`. `PLAN.md`'s `status` field and the gate-4 files —
`G3-PLAN` owns forward planning, this unit owns the record of what closed.
Gate 1's and gate 2's WU files, `GATE-01.md`, `GATE-02.md`, `GATE-02-REVIEW.md`.
The driver owns all git; this session edits files only and runs no `git` command.

**Verification.** The `plannext` gate set from `.specfuse/verification.yml`, plus
`specfuse lint --closing` exiting 0 and
`specfuse lint .specfuse/features/FEAT-2026-0049-specfuse-agent-runner` passing.

**Escalation triggers.** If cost reconciliation cannot complete because
`events.jsonl` rows are missing for some work unit, name the work unit rather
than estimating: #1024 records that those rows can be lost between a squash and
the next bookkeeping commit. If reconciling the gate-1 or gate-2 debt would
require re-running an oracle that no longer exists — a test deleted or renamed
since — say which and stop, rather than marking a criterion verified on a
substitute. If gate 3's fixture-only verification turns out to have hidden a real
defect that only a live run would catch, that is a finding for the retrospective
and an escalation, not a lesson to soften into prose.
