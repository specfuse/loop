---
id: FEAT-2026-0041/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0041: write the retrospective, promote
generalizable lessons, reconcile documentation and roadmap, and record the terminal
verdict.

**Context.** Correlation ID `FEAT-2026-0041/G1-CLOSE`. This is the feature's only gate
and it is terminal, so this single `close` work unit collapses retrospective, lessons,
docs, and verdict into one session. Read `PLAN.md` and `GATE-01.md` first.

**Why `auto_close_disabled: true`.** This close carries obligations no predicate can
discharge: a LEARNINGS correction, a follow-on roadmap row, and a deferred-verification
list whose central entry is inherent rather than incidental. Per `close-discipline.md`,
a close carrying §1–§3 obligations is load-bearing and must not be optimized away —
and this is exactly the case issue #293 describes, where an on-plan gate auto-closes
and its close criteria are silently logged as deferred debt. FEAT-2026-0061 lost all 26
of its criteria that way; FEAT-2026-0063 lost its roadmap retitle. This close opts out
explicitly so the same thing does not happen a third time.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

## What this close must get right, specific to this feature

**Diagnosis quality is unverified, and that is the headline limitation.** Every test in
this gate asserts format, contract, and round-trip fidelity. Nothing asserts a root
cause is correct. A close that lets a green gate read as verified diagnosis quality has
misreported the feature's central claim. State it plainly in
`## What the loop did NOT verify`, and say it is inherent — not a gap someone should
close later with more tests.

**The LEARNINGS entry is wrong and must be corrected.**
`[FEAT-2026-0014/T01/gh-claudeP-broken]` attributes the `gh` failure to a
`gh`-binary/subprocess interaction and rules that no acceptance criterion may invoke
`gh` from a dispatched agent. The cause is the command **sandbox**;
`--dangerously-skip-permissions` governs permission prompts, not the sandbox, which is
why the flag appeared not to help. T04's raw evidence is the proof. That entry has
already cost two features — FEAT-2026-0040 deferred D-9, D-10 and D-11 on its basis and
its close is hedged to this day. Correcting it is this close's job, not a follow-up.

**T04's result is the evidence, not its verdict.** Quote its raw `gh` output. If T04
skipped its live test rather than reaching GitHub, the round-trip is **not** verified
and the close must say so regardless of the gate being green.

**Consumer-visible contract changes.** `close-discipline.md` §3 requires enumerating
them or writing the explicit `n/a` line. At least one is known: T01 promotes
`_redact_text` from module-private to public API. Assess also the new `diagnosis.py`
module surface and the new skill.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists at the feature root and carries a `## Cost analysis`
   section reconciling planned against actual — the $18.50 `planned_cost_usd` and the
   $23.50 gate budget against the `attempt_outcome` sum in `events.jsonl`, which is the
   authoritative source. Write the `## Cost analysis` heading literally;
   `assert_cost_analysis_section_when_met` checks for it after dispatch, so omitting it
   costs a full re-attempt.
2. The deferred-verification list is written with, for each entry, the criterion, the
   reason it was not verified in-loop, and where it actually gets checked — or the
   explicit `(nothing — every acceptance criterion was verified in-loop)` line if empty.
3. `## What the loop did NOT verify` states that diagnosis **correctness** is unverified
   and inherent, distinct from anything deferred to a later run.
4. T04's live round-trip is reported with its raw `gh` evidence quoted, including
   whether the live test actually executed or skipped, and the scratch issue's number
   and final state (closed, or still open with its number named).
5. `[FEAT-2026-0014/T01/gh-claudeP-broken]` in `.specfuse/LEARNINGS.md` is corrected to
   name the command sandbox as the cause, note that `--dangerously-skip-permissions`
   governs permissions rather than the sandbox, and record that a dispatched work unit
   can exercise `gh` when run unsandboxed — citing T04 as the evidence.
6. A follow-on roadmap row is filed for the deferred auto-trigger scope: the
   `diagnose: auto` per-component dial, harvester auto-trigger on new fingerprints, and
   one-diagnosis-per-fingerprint dedupe. Use `/roadmap-add`; do not renumber or reuse
   an existing ID.
7. Consumer-visible contract changes are enumerated per `close-discipline.md` §3, or the
   explicit `n/a` line is written. `_redact_text`'s promotion is one; assess the rest.
8. The roadmap row and detail section reflect what was actually built, including the
   narrowed scope recorded in `PLAN.md`.
9. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip via
`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`, on both the
dispatched-close and auto-close paths. Do not write it here. Source files owned by
T01–T04: this WU closes the gate, it does not finish or repair their work.

**Verification.** The `plannext` gate set for closing WUs, plus `specfuse-lint
--closing` exiting 0 (criterion 9) before this WU reports `complete`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`events.jsonl` cost sum cannot be reconciled against frontmatter (report it as a lower
bound and name the gap rather than inventing a number); T04 skipped its live test, so
the round-trip claim cannot be made — report the gap and hedge the verdict rather than
asserting live verification that did not happen; or correcting the LEARNINGS entry
would require contradicting evidence T04 actually produced. A verdict of `met_locally`
with the unverified diagnosis-quality limitation carried forward is an acceptable
outcome and is **not** a block.
