---
id: FEAT-2026-0111/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.50
produces:
  - tests/test_distilled_accept_step.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.19.0
started_at: 2026-09-14T15:01:34.373076+00:00
duration_seconds: 138.13
cost_usd: 0.486376
input_tokens: 28
output_tokens: 12150
---

# Propose a ranked cut; let a human accept it

**Objective.** Turn T02's scores into a ranked proposal against the word
budget, and land the distilled file only through a per-entry human
accept / edit / reject.

**Context.** FEAT-2026-0111/T03. The weights rank; they do not decide. Neither
`failure_signature` cost nor reach measures whether a rule improves the next
session's work, nothing in the tree does, and establishing it would need a
before/after on failure rates that would dwarf this feature. #3272's own
consumer curated its 47 lines **by hand** and reported the weights *corrected*
that judgment rather than replacing it — six high-value entries a by-hand cut
had dropped, two zero-weight singletons it had kept.

So this is a propose-and-confirm surface, the same posture `/arm-gate`,
`/pick-feature` and `/learnings-curate` already use.

**Acceptance criteria.**

- `python3 -m unittest tests.test_distilled_accept_step -v -b` fails on HEAD
  before this unit's edits and passes after.
- The proposal is ranked, shows each entry's evidence (cost, reach,
  `failure_signature`), and is cut at the word budget rather than at an entry
  count — the budget is what the dispatch path actually pays.
- **Nothing reaches `.specfuse/rules-local/learnings-distilled.md` without an
  explicit accept.** Asserted with a negative observation: running the proposal
  step and declining leaves the file byte-identical, and no `@` line is added.
- Each proposed entry carries the review prompt *"this may already be enforced
  by a guard or lint — check before spending dispatch words on it"*. Only 7 of
  234 entries name such a guard literally, so this cannot be computed and is
  surfaced for the human rather than filtered automatically.

**Do not touch.** The scoring itself (T02's). The binding block's budget
(T04's). `LEARNINGS.md`. The sibling WU files in this gate.

**Verification.** Narrow tier for `implementation`, plus
`python3 -m unittest tests.test_distilled_accept_step tests.test_learnings_weights -v -b`.

**Escalation triggers.** Stop with `status: blocked` if the accept step cannot
be made non-interactive-safe — a surface that writes on a headless invocation
with no human present is the opposite of what this unit is for.
