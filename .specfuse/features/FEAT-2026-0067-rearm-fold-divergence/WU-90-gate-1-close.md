---
id: FEAT-2026-0067/G1-CLOSE
type: close
status: done
planned_cost_usd: 5.00
auto_close_disabled: true

model: opus
effort: high
gate_set: plannext
driver_version: 0.9.2
started_at: 2026-08-05T10:20:24.342563+00:00
attempts: 1
duration_seconds: 835.56
cost_usd: 7.250347
input_tokens: 138
output_tokens: 53540
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-08-05T01:20:00+00:00
    prior_status: done
    prior_attempts: 1
    prior_cost_usd: 8.102319
    prior_duration_seconds: 953.536
    reason: "Operator chose fix-and-re-close over accepting the hedge; T04 discharges FU-1 so this close re-verifies the reconciliation."
cumulative_cost_usd: 8.102319
cumulative_duration_seconds: 953.536
cumulative_input_tokens: 140
cumulative_output_tokens: 60331
cumulative_attempts: 1
folded_through_re_arm: 1
verdict: met
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0067: write the retrospective,
promote generalizable lessons, reconcile documentation and roadmap, and record
the terminal verdict.

**Context.** Correlation ID `FEAT-2026-0067/G1-CLOSE`. Single terminal gate, so
this WU collapses retrospective, lessons, docs, and verdict into one session.
Read `PLAN.md` and `GATE-01.md` first.

**Why `auto_close_disabled: true`.** A terminal close carrying §1–§3
obligations is load-bearing per `close-discipline.md`. Issue #293's case:
FEAT-2026-0061 lost all 26 close criteria to an on-plan auto-close.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

## What this close must get right, specific to this feature

**The feature's whole claim is that one shape now exists.** Verify it rather
than asserting it: re-run the census over `.specfuse/features/**/WU-*.md` and
report the counts. If any re-armed WU still lacks `folded_through_re_arm`, the
feature is not done, whatever the gates say.

**This close is itself a re-armable work unit.** If this close is re-armed, it
exercises the very path the feature changed. Say so if it happens — a close
that folded its own prior cycle correctly is the best evidence available, and a
close that did not is a defect found at the last possible moment.

**T02 made a choice only a human-facing record can justify.** It chose either
migrate or annotate for the two fold-never-ran units. Restate that choice and
its reason in the retrospective, so a later reader finds it without opening a
work unit body.

**Consumer-visible contract changes are real here.** `folded_through_re_arm` is
a new frontmatter field every downstream project's WUs will carry, and
`cumulative_*`'s meaning is now unconditional. Both belong in §3, and therefore
in `CHANGELOG.md`'s `Unreleased` per `close-k`.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists at the feature root with a literal `## Gate 1`
   heading and a literal `## Cost analysis` section reconciling planned against
   actual — the $10.00 WU sum and $14.00 gate budget against the
   `attempt_outcome` sum in `events.jsonl`, which is authoritative.
2. The deferred-verification list is written with, per entry, the criterion,
   why it was not verified in-loop, and where it actually gets checked — or the
   explicit `(nothing — every acceptance criterion was verified in-loop)` line.
3. The census is re-run and its result quoted: every re-armed WU in this
   repository carries `folded_through_re_arm`, or the close reports which do
   not and returns a hedged verdict rather than `met`.
4. `## What the loop did NOT verify` states plainly that no downstream project
   has been migrated, and that the migration's behaviour against a real
   downstream repo is unverified here.
5. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md` tagged with
   this WU's correlation ID. The candidate worth assessing: **a guard that
   infers "already done" from a value cannot distinguish it from "never
   happened"** — this is the third instance this week (#593's `produces:` shape
   checked post-session, #306's frontmatter scan running off the end, and this
   fold guard). Promote it if the pattern holds across all three; say so
   plainly if on inspection it does not.
6. Consumer-visible contract changes are enumerated per `close-discipline.md`
   §3, and appended to `CHANGELOG.md`'s `Unreleased` carrying this FEAT-ID.
7. The roadmap row and detail section reflect what was actually built,
   including which of the two shapes the feature converged on.
8. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal
flip via `fire_terminal_flips`, gated on `verdict_permits_terminal_flips`.
Source files owned by T01–T03. Any already-`done` feature's records beyond what
T02's migration explicitly stamped.

**Verification.** The `plannext` gate set for closing WUs, plus
`specfuse-lint --closing` exiting 0 (criterion 8) before this WU reports
`complete`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the `events.jsonl` cost sum cannot be reconciled against frontmatter (report a
lower bound and name the gap rather than inventing a number); the census shows
a re-armed WU without a marker, which means T02 did not finish; or T01's
idempotence guarantee cannot be demonstrated on a real re-armed unit, which
would make the converged contract unproven on anything but fixtures.
