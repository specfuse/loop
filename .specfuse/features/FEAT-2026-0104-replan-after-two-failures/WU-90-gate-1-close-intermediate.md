---
id: FEAT-2026-0104/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 1
planned_cost_usd: 4.50
auto_close_disabled: true
model: opus
effort: high
gate_set: plannext
driver_version: 0.19.0
started_at: 2026-09-10T20:19:52.502186+00:00
duration_seconds: 431.957
cost_usd: 2.918651
input_tokens: 70
output_tokens: 28717
---

# Close gate 1 — the re-plan trigger

**Objective.** Fold gate 1's retrospective, lessons and documentation
reconciliation into one session, and record what the trigger did and did not
prove.

**Context.** FEAT-2026-0104/G1-CLOSE-INTERMEDIATE. Non-terminal close; it
pairs with `G1-PLAN`, which drafts gate 2 from what this session writes. Close
obligations bind by reference (`.specfuse/rules/close-discipline.md` §§1–5);
the required sections are scaffolded at dispatch, so write their substance,
not their headings.

**Acceptance criteria.**

- Cost is reconciled against this gate's `planned_cost_usd` figures and the
  spend `events.jsonl` actually recorded, per WU, with the variance explained
  rather than noted. `[FEAT-2026-0040/G3-CLOSE]` is the standing warning:
  padding priced as one re-attempt of the largest unit prices the retry at the
  figure a retry disproves.
- The deferred-verification list names every acceptance criterion this gate
  did not verify in-loop, each with its reason and where it actually gets
  checked — or the explicit `(nothing — every acceptance criterion was
  verified in-loop)` line if it is empty.
- The retrospective states plainly whether any unit in **this** gate
  re-planned, and if one did, whether the re-planned unit then passed. A
  feature that builds a re-plan trigger and trips it on itself is the most
  direct evidence gate 2 will get, and it must not be left as an anecdote.
- The interaction with FEAT-2026-0103's retained-tree repair is recorded: how
  often a guard refusal became a repair versus a re-plan, from the attempt
  record, since both now sit on the same path.
- `RETROSPECTIVE.md` carries a `## Gate 1` section holding this gate's record —
  `assert_retrospective_gate_section` checks the heading after dispatch, so a
  missing one costs a full re-attempt.
- `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` — the driver owns the terminal flip via
`fire_terminal_flips`, and this is not the terminal gate anyway. Gate 2's WU
files, which are `G1-PLAN`'s to draft. Any driver code: a close that fixes
what it is meant to be reporting on has nothing left to report.

**Verification.** Narrow tier for `close-intermediate`, plus
`specfuse lint --closing`.

**Escalation triggers.** Stop with `status: blocked` if the cost reconciliation
cannot be built because `events.jsonl` and the committed WU frontmatter
disagree — that disagreement is itself the finding, and #3296 is the precedent
for taking it seriously rather than papering over it.
