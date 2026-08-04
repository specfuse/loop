---
id: FEAT-2026-0034/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
verdict: met
model: opus
effort: high
gate_set: plannext
driver_version: 0.8.0
started_at: 2026-08-04T04:07:50.285929+00:00
duration_seconds: 712.701
cost_usd: 3.912955
input_tokens: 74
output_tokens: 31570
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0034: write the retrospective, promote
generalizable lessons, reconcile documentation and roadmap, and record the terminal
verdict.

**Context.** Correlation ID `FEAT-2026-0034/G1-CLOSE`. This is the feature's only gate
and it is terminal, so this single `close` work unit collapses retrospective, lessons,
docs, and verdict into one session. Read `PLAN.md` and `GATE-01.md` first.

**Why `auto_close_disabled: true`.** A terminal close carrying §1–§3 obligations is
load-bearing per `close-discipline.md`. This is issue #293's case: FEAT-2026-0061 lost
all 26 close criteria to an on-plan auto-close and FEAT-2026-0063 lost its roadmap
retitle the same way. Opt out explicitly.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

## What this close must get right, specific to this feature

**The archiver is still broken, and that is the design.** `auto_archive_feature`
produces rot shapes 3 and 4 on every run. This feature lints rather than repairs,
because the roadmap row says a failing check on the next archive *is* the durable fix.
Report it as a live defect with a now-failing check pointing at it — not as this
feature's unfinished work, and not omitted.

**ADR approval state is unchecked, deliberately.** A `**Blocked by.**` ADR link is
validated for existence, not acceptance. FEAT-2026-0011 has sat `blocked` on an
unapproved ADR-0002 all week and passes this lint. Say so, so it does not read as a
gap someone should close.

**The rot repaired ahead of this feature is not this feature's work.** Two violations
were fixed in a commit before the first WU ran, so the gate's "exits 0" criterion was
satisfiable on arrival. The close should record that the tree was made clean first and
that the red tests therefore used fixtures — otherwise a reader concludes the lint
found nothing because there was never anything to find.

**Consumer-visible contract changes.** `close-discipline.md` §3 requires enumerating
them or writing the explicit `n/a` line. At least two are known: a new shipped module
(`specfuse/loop/lint_roadmap.py`) and a new gate every downstream project inherits on
upgrade — the second matters, because a project whose roadmap carries this rot starts
failing a gate it did not previously have.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists at the feature root and carries a literal `## Gate 1`
   heading and a literal `## Cost analysis` section reconciling planned against actual
   — the $12.50 WU sum and the $17.50 gate budget against the `attempt_outcome` sum in
   `events.jsonl`, which is authoritative. Both headings are checked after dispatch, so
   omitting either costs a full re-attempt.
2. The deferred-verification list is written with, for each entry, the criterion, the
   reason it was not verified in-loop, and where it actually gets checked — or the
   explicit `(nothing — every acceptance criterion was verified in-loop)` line.
3. `## What the loop did NOT verify` names the unchecked ADR-approval state and the
   fact that the lint has not yet met a real archive run's fresh output.
4. The archiver defect is reported as outstanding and pointed at, per above.
5. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md` tagged with this WU's
   correlation ID. Candidate worth assessing: whether "check the invariants by hand
   before drafting the feature that automates them" generalizes — it was what made this
   gate satisfiable on arrival.
6. Consumer-visible contract changes are enumerated per `close-discipline.md` §3, or
   the explicit `n/a` line is written. The inherited-gate change is one.
7. The roadmap row and detail section reflect what was actually built.
8. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip via
`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`. Source files owned by
T01 and T02.

**Verification.** The `plannext` gate set for closing WUs, plus `specfuse-lint
--closing` exiting 0 (criterion 8) before this WU reports `complete`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`events.jsonl` cost sum cannot be reconciled against frontmatter (report a lower bound
and name the gap rather than inventing a number); or the new gate does not actually
exit 0 on the tree at close time, which would mean rot landed during the gate and the
feature's headline claim cannot be made as written.
