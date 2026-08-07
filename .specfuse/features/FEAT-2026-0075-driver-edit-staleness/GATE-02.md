---
gate: 2
status: open        # open | awaiting_review | passed
---

# Gate 2 — the hazard is prevented, and the two-invocation hold has a name

## Definition of done

<Drafted by gate 1's `plan-next` (`G1-PLAN`) from gate 1's retrospective, its observed
warn output, and `.specfuse/LEARNINGS.md`. The intent recorded at draft time, for that
session to accept, revise, or reject:>

- A gate whose plan schedules a driver-editing work unit ahead of a close in the same
  gate is refused at arm time, naming the offending pair and the split it requires.
  The refusal extends `arm_eval`'s existing class-2 `judge_editing` detection rather
  than adding a second detector.
- The two-invocation hold has a sanctioned status. Today it does not: `draft` is
  rejected by the arm check for the entire gate, and `blocked_human` is the only
  usable hold, which reads as a failure in `/attention` and every other consumer. **A
  refusal that forces the operator into an improvised hold is worse than no refusal**,
  so the hold ships with the refusal or the refusal does not ship.
- The refusal reports **zero** on a gate that is already correctly ordered — the §2
  satisfiability answer, written against gate 1's observed output rather than assumed.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

<Filled in by `G1-PLAN` when it drafts this gate's work units.>

**Already known to be required, and not `G1-PLAN`'s to drop:**

- **§2 satisfiability is load-bearing for this gate.** It introduces a blocking
  refusal. The question — *what does the refusal report on a gate that is already
  correctly ordered?* — must be answered in writing before arming, and the answer must
  be zero. Gate 1's summary output is the evidence.
- **§4 runtime probe is required** for whichever unit lands the refusal, since a tree
  that arms clean today can be refused after it. Sweep every feature folder's gate
  plans and paste the finding list; a non-empty result on correctly-ordered gates means
  the refusal is mis-scoped.
- **The driver restart applies again** if any gate-2 unit edits `specfuse/loop/` ahead
  of `G2-CLOSE` — the same step gate 1 carries, for the same reason.

## Reflection notes

<Written by the human at review time.>
