---
id: FEAT-2026-0113/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 4.50
---

# G1-CLOSE-INTERMEDIATE — close gate 1

**Context.** Gate 1 proved the triage marker reads both shapes with no writer
changed. This unit folds the retrospective, the durable lessons and the
documentation pass into one session.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` carries a `## Gate 1` section recording what gate 1
   actually proved, per criterion, and — the
   load-bearing one for this feature — **whether any marker shape was found in the
   wild that the old regex parsed and the new scan does not**. A clean answer here
   is what licenses gate 2 to start writing the new shape; an unclean one stops it.
2. That section includes a `## Cost analysis` heading. Cost is reconciled against each unit's `planned_cost_usd` and the per-attempt
   records in `events.jsonl`, not estimated.
3. The deferred-verification list names every acceptance criterion not verified
   in-loop, each with its reason and where it actually gets checked — or the
   explicit line `(nothing — every acceptance criterion was verified in-loop)`.
4. Any durable rule this gate surfaced is promoted to `.specfuse/LEARNINGS.md`.
   Candidate already visible at draft time: whether a positionally-anchored regex
   over a published marker is a recurring shape worth a rule, given
   `monitor/issues.py` uses the same `_MARKER_TEMPLATE` convention.
5. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Any source file under `specfuse/` — this unit closes a gate, it
does not implement. Other features' folders.

**Verification.** `specfuse lint --closing`, plus the gate set in
`.specfuse/verification.yml`.

**Escalation triggers.** If criterion 1's answer is that a real marker shape
regressed, stop and escalate rather than recording it and closing green — that
finding invalidates the gate's definition of done.
