---
id: FEAT-2026-0042/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 4.50
auto_close_disabled: true
---

# Close gate 1 — retrospective, lessons, docs

**Objective.** Intermediate close for gate 1: write the retrospective, promote
generalizable lessons, and reconcile documentation. Gate 2 is drafted separately by
`G1-PLAN`.

**Context.** Correlation ID `FEAT-2026-0042/G1-CLOSE-INTERMEDIATE`. This is a
non-terminal gate, so this WU collapses retrospective + lessons + docs and does **not**
write a terminal verdict — gate 2's close owns that. Read `PLAN.md` and `GATE-01.md`
first.

**Why `auto_close_disabled: true`.** This close carries §1–§3 obligations no
predicate can discharge, and per `close-discipline.md` a close carrying them is
load-bearing. This is issue #293's case: FEAT-2026-0061 lost all 26 of its close
criteria to an on-plan auto-close, and FEAT-2026-0063 lost its roadmap retitle the
same way. Opting out explicitly is the fix available today.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

## What this close must get right, specific to this gate

**The dial is still inert, and that is success.** At the end of this gate,
`autofix: "on"` changes nothing — the predicate decides, the state records, the
headless mode exists, and no caller fires. State that plainly. A close that reports it
as an incomplete deliverable has misread the gate; a close that omits it leaves a
reader thinking autofix is live.

**Fix quality is unverified and inherent.** Every criterion in this gate asserts the
*decision* is right or the *mechanism* is sound. Nothing asserts a generated patch is
correct — the same limit FEAT-2026-0041 recorded for diagnosis quality. It belongs in
`## What the loop did NOT verify` as inherent, not as a gap for gate 2 to close.

**The safety floor must be restated for gate 2's reader.** Auto-merge belongs to
FEAT-2026-0048 and is impossible in this feature. Record it in the retrospective so
`G1-PLAN` and the human arming gate 2 both meet it before drafting.

**T03 widened scope into `fix-bug`.** The roadmap row assumed headless invocation
existed; it did not. Record that the row's premise was wrong and what it cost, so the
next feature reading that row is not misled the same way.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists at the feature root and carries a literal `## Gate 1`
   section heading — `assert_retrospective_gate_section` checks for it after dispatch,
   so omitting it costs a full re-attempt — plus a literal `## Cost analysis`
   section reconciling planned against actual: the $22.00 gate-1 WU sum and the
   $28.00 gate budget against the `attempt_outcome` sum in `events.jsonl`, which is
   the authoritative source. Write the `## Cost analysis` heading literally;
   `assert_cost_analysis_section_when_met` checks for it after dispatch, so omitting
   it costs a full re-attempt.
2. The deferred-verification list is written with, for each entry, the criterion, the
   reason it was not verified in-loop, and where it actually gets checked — or the
   explicit `(nothing — every acceptance criterion was verified in-loop)` line.
3. `## What the loop did NOT verify` states that fix **correctness** is unverified and
   inherent, and that nothing fires yet by design.
4. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md` tagged with this
   WU's correlation ID. Candidates worth assessing: whether the ephemeral-runner
   state trap generalizes beyond this feature, and whether "a roadmap row assumed a
   capability that did not exist" is a recurring drafting failure worth a rule.
5. Consumer-visible contract changes are enumerated per `close-discipline.md` §3, or
   the explicit `n/a` line is written. At least one is known: `fix-bug` gains a
   documented headless mode. Assess the new modules and the new label too.
6. The safety floor — auto-merge belongs to FEAT-2026-0048, ceiling is an unwanted PR
   on a branch — is restated in the retrospective for gate 2's reader.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns terminal flips and
this is not the terminal gate regardless. Gate 2's drafts — `G1-PLAN` owns them.
Source files owned by T01–T03: this WU closes the gate, it does not finish or repair
their work.

**Verification.** The `plannext` gate set for closing WUs, plus `specfuse-lint
--closing` exiting 0 before this WU reports `complete`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`events.jsonl` cost sum cannot be reconciled against frontmatter (report it as a lower
bound and name the gap rather than inventing a number); or a gate-1 work unit turns
out to have fired something — invoked `fix-bug`, created a branch, or opened a pull
request — which would mean the gate's safety property was violated and the operator
must know before gate 2 is armed.
