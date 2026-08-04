---
id: FEAT-2026-0073/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0073: write the retrospective, promote
generalizable lessons, reconcile documentation and roadmap, and record the terminal
verdict.

**Context.** Correlation ID `FEAT-2026-0073/G1-CLOSE`. Single terminal gate, so this WU
collapses retrospective, lessons, docs, and verdict into one session. Read `PLAN.md` and
`GATE-01.md` first.

**Why `auto_close_disabled: true`.** A terminal close carrying §1–§3 obligations is
load-bearing per `close-discipline.md`. Issue #293's case: FEAT-2026-0061 lost all 26
close criteria to an on-plan auto-close, FEAT-2026-0063 lost its roadmap retitle.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

## What this close must get right, specific to this feature

**File the upstream need.** This feature widens a field another repository owns, on a
deep copy, because editing the vendored file would be reverted by the next vendor sync.
That is the right call here and it is still a **local fork of a shared protocol
field**. The close files an issue (or the project's equivalent) recording that the
orchestrator's `event.schema.json` should accept the closing-sequence and hygiene shapes
upstream, so the override is a documented bridge rather than a silent divergence. Cite
`correlation-ids.md` as the contract and this feature as the local implementation.

**Report the corpus numbers as measured, not as planned.** `PLAN.md` records 285 errors
across 38 folders at drafting time; the number grows with every feature that closes. Say
what T01 and T02 actually measured. A close that restates the planned figure repeats the
defect FEAT-2026-0063 was created to fix.

**The vendored file is untouched — assert it, do not claim it.** Quote
`git diff --exit-code specfuse/loop/data/schemas/event.schema.json`. This is the
feature's central boundary and the one a future reader is most likely to doubt.

**Consumer-visible contract changes.** `close-discipline.md` §3 requires enumerating
them or the explicit `n/a` line. At least two are known: the driver-local registry gains
a correlation-ID surface, and the repo's event gate widens from one field to the whole
envelope — the second means a downstream project with malformed events starts failing a
gate that previously ignored them.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists at the feature root with a literal `## Gate 1` heading and
   a literal `## Cost analysis` section reconciling planned against actual — the $12.50
   WU sum and $17.50 gate budget against the `attempt_outcome` sum in `events.jsonl`,
   which is authoritative. Both headings are checked after dispatch; omitting either
   costs a full re-attempt.
2. The deferred-verification list is written with, per entry, the criterion, why it was
   not verified in-loop, and where it actually gets checked — or the explicit
   `(nothing — every acceptance criterion was verified in-loop)` line.
3. `## What the loop did NOT verify` names the upstream divergence risk: the two
   definitions can drift, and nothing in this repository detects that.
4. An upstream issue is filed per the section above, and its reference recorded.
5. The corpus error counts T01 and T02 actually measured are reported, with any
   difference from `PLAN.md`'s 285 explained as corpus growth rather than restated.
6. `git diff --exit-code` on the vendored schema is quoted, proving it is untouched.
7. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md` tagged with this WU's
   correlation ID. Candidate worth assessing: whether "measure every error class before
   asserting zero errors" generalizes — it is the check FEAT-2026-0060 skipped, at a cost
   of $4.48 and a blocked attempt, and the check this feature made first.
8. Consumer-visible contract changes are enumerated per `close-discipline.md` §3, or the
   explicit `n/a` line is written.
9. The roadmap row and detail section reflect what was actually built, including which
   of the two options the row left open was chosen and why.
10. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip via
`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`. Source files owned by
T01 and T02. `specfuse/loop/data/schemas/event.schema.json`.

**Verification.** The `plannext` gate set for closing WUs, plus `specfuse-lint --closing`
exiting 0 (criterion 10) before this WU reports `complete`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`events.jsonl` cost sum cannot be reconciled against frontmatter (report a lower bound
and name the gap rather than inventing a number); the corpus is not error-free at close
time, since the feature's headline claim is that the log validates end to end and a
close cannot assert that against a red corpus; or the upstream issue cannot be filed,
in which case record the exact text that should be filed and hedge the verdict rather
than dropping the obligation.
