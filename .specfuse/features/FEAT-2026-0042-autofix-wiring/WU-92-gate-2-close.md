---
id: FEAT-2026-0042/G2-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
---

# Close gate 2 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0042: write the retrospective, promote
generalizable lessons, reconcile documentation and roadmap, and record the terminal
verdict for the feature.

**Context.** Correlation ID `FEAT-2026-0042/G2-CLOSE`. Placeholder, pre-declared at
draft time so the linter reads gate 2 as the terminal gate. `FEAT-2026-0042/G1-PLAN`
inserts gate 2's substantive work units **before** this one and updates its
`depends_on`. This body is refined by `G1-PLAN` once gate 2's real shape is known.

**Why `auto_close_disabled: true`.** A terminal close carrying §1–§3 obligations is
load-bearing per `close-discipline.md`, and this one carries the feature's
consumer-visible contract list and its terminal verdict. Issue #293's case:
FEAT-2026-0061 lost all 26 close criteria to an on-plan auto-close and
FEAT-2026-0063 lost its roadmap retitle. Opt out explicitly.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

## What this close must get right — known at draft time

**The live end-to-end run is the evidence, not its verdict.** Quote the raw command
output from gate 2's live WU. If it skipped rather than actually firing, the mechanism
is **not** verified and the close must say so regardless of the gate being green —
the same discipline FEAT-2026-0041's close applied to its `gh` round-trip.

**Fix correctness is unverified and inherent.** Nothing in either gate asserts a
generated patch is correct. It belongs in `## What the loop did NOT verify` as
inherent, not as a gap someone should close later with more tests.

**Report any residue.** The live run creates a scratch issue and a pull request. Name
their numbers and final states — closed, or still open and why. A killed attempt
leaving residue is information about attempt behaviour, not litter to hide.

**The safety floor held, or it did not.** State explicitly that no pull request was
merged, no auto-merge was enabled, and nothing was pushed to a protected branch — or
report the violation. This is the feature's central safety claim and the close is
where it is asserted.

**Acceptance criteria.**

<Refined by `G1-PLAN` against gate 2's actual work units. At minimum, carry forward:
a `## Cost analysis` section reconciling planned against `events.jsonl`; the
deferred-verification list or its explicit empty line; the inherent fix-quality
limitation; the live-run evidence with raw output; the residue report; the safety-floor
assertion; consumer-visible contract changes per §3 or the `n/a` line; roadmap row and
detail reconciled with what was built; and `specfuse-lint --closing` exiting 0.>

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip via
`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`, on both the
dispatched-close and auto-close paths. Source files owned by gate 2's work units.

**Verification.** The `plannext` gate set for closing WUs, plus `specfuse-lint
--closing` exiting 0 before this WU reports `complete`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
live run did not actually fire, so the mechanism claim cannot be made — report the gap
and hedge the verdict rather than asserting verification that did not happen; the
safety floor was violated; or the `events.jsonl` cost sum cannot be reconciled against
frontmatter. A verdict of `met_locally` with the inherent fix-quality limitation
carried forward is an acceptable outcome and is **not** a block.
