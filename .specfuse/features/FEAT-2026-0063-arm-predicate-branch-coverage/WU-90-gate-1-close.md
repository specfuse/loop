---
id: FEAT-2026-0063/G1-CLOSE
type: close
status: done
attempts: 0
planned_cost_usd: 5.00
verdict: met
auto_close: true
auto_close_reasons: []
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0063: write the retrospective, promote
generalizable lessons, reconcile documentation and roadmap, and record the terminal
verdict for the feature.

**Context.** Correlation ID `FEAT-2026-0063/G1-CLOSE`. This is the feature's only
gate and it is terminal, so this single `close` work unit collapses retrospective,
lessons, docs, and verdict into one session. Read `PLAN.md` and `GATE-01.md` first.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

## What this close must get right, specific to this feature

**The unverified list is the deliverable, not a failure.** This gate ships a report
saying five of eight stop classes have never fired on real input and no class has
ever reported `not_evaluable`. `GATE-01.md` records this as the gate's correct
output. A close that reads it as a gate failure has misunderstood the feature; a
close that omits it has hidden the deliverable. It belongs in `## What the loop did
NOT verify` as a named, dated list, with the reason it was not closed — manufacturing
inputs to force those branches is out of scope by decision, not by oversight.

**Report the sweep's numbers as executed, not as planned.** `PLAN.md` records 4
evaluable features and 41 clean / 7 fired / 0 `not_evaluable` measured 2026-08-03. If
the corpus moved during the gate, the close reports what the sweep actually returned
and notes the drift. That this row's premise went stale twice in two days is the
feature's own motivating evidence; a close that quietly restates the planned figures
would repeat the defect it was built to fix.

**Consumer-visible contract changes.** `close-discipline.md` §3 requires enumerating
them or writing the explicit `n/a` line. Candidates to assess: a new gate in
`.specfuse/verification.yml` that a downstream project inherits on upgrade, and a new
shipped module (`specfuse/loop/arm_sweep.py`) that becomes importable API. Decide
whether either reaches a consumer and say so either way.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists at the feature root and carries a `## Cost analysis`
   section reconciling planned against actual — the $16.00 `planned_cost_usd` and the
   $21.00 gate budget against the `attempt_outcome` sum in `events.jsonl`, which is
   the authoritative source. Write the `## Cost analysis` heading literally;
   `assert_cost_analysis_section_when_met` checks for it after dispatch, so omitting
   it costs a full re-attempt.
2. The deferred-verification list is written with, for each entry, the criterion, the
   reason it was not verified in-loop, and where it actually gets checked — or the
   explicit `(nothing — every acceptance criterion was verified in-loop)` line if
   empty.
3. The never-fired branch list appears in `## What the loop did NOT verify` with its
   measurement date and the regenerate command, framed as unexercised rather than
   defective.
4. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md` with this WU's
   correlation ID as their tag. Candidate worth assessing: whether "a premise
   re-derived by hand at pick time is a premise that will be wrong again" generalizes
   beyond this feature, given it went stale twice in two days.
5. Consumer-visible contract changes are enumerated per `close-discipline.md` §3, or
   the explicit `n/a` line is written.
6. The roadmap row and its detail section reflect what was actually built, including
   the retitle from "Live-input verification for the arm predicate's fail-closed
   branches" recorded in `PLAN.md`.
7. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip via
`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`, on both the
dispatched-close and auto-close paths. Do not write it here. Source files owned by
T01–T03: this WU closes the gate, it does not finish or repair their work.

**Verification.** The `plannext` gate set for closing WUs, plus `specfuse-lint
--closing` exiting 0 (criterion 7) before this WU reports `complete`. Re-run T02's
gate fresh rather than quoting T02's recorded result — the corpus may have moved
during the gate, and this feature exists because stale figures get restated.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`events.jsonl` cost sum cannot be reconciled against the frontmatter (report it as a
lower bound and name the gap rather than inventing a number); `specfuse-lint
--closing` fails for a reason that would require editing T01–T03's deliverables; or
the terminal verdict would be `met` while the never-fired branch list is absent from
`## What the loop did NOT verify` — that list is the gate's deliverable and a close
omitting it has hidden what shipped. A verdict of `met_locally` with the unverified
list carried forward is an acceptable outcome and is **not** a block.
