---
id: FEAT-2026-0042/G2-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
verdict: met
auto_close_disabled: true
model: opus
effort: high
gate_set: plannext
driver_version: 0.8.0
started_at: 2026-08-04T03:15:55.439455+00:00
duration_seconds: 861.893
cost_usd: 7.715448
input_tokens: 150
output_tokens: 53921
---

# Close gate 2 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0042: write the retrospective, promote
generalizable lessons, reconcile documentation and roadmap, and record the terminal
verdict for the feature.

**Context.** Correlation ID `FEAT-2026-0042/G2-CLOSE`. Pre-declared at draft time so
the linter reads gate 2 as the terminal gate; refined by `FEAT-2026-0042/G1-PLAN`
once gate 2's real shape was known. Read `PLAN.md`, `GATE-02.md`, `GATE-02-REVIEW.md`,
and the gate-1 section of `RETROSPECTIVE.md` first — this close appends gate 2's
section to that existing retrospective and writes the feature's terminal verdict.

Gate 2's three substantive work units: **T04** `specfuse/monitor/autofix_invoke.py`
(builds the headless `fix-bug` call, classifies its result), **T05**
`specfuse/monitor/autofix_run.py` (the firing wiring — decide, record, fire, label),
**T06** the live end-to-end run (the only `unsandboxed: true` work unit in the
feature).

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

1. `RETROSPECTIVE.md` gains a `## Gate 2` section covering T04, T05, and T06 — what
   each shipped, and the decisions worth carrying past this feature. Gate 1's section
   is appended to, never rewritten.
2. A `## Cost analysis` section reconciles each gate-2 work unit's
   `planned_cost_usd` against its `attempt_outcome` payload in `events.jsonl` (the
   authoritative source), and against the `$29.50` `cost_budget_usd` in `GATE-02.md`.
   Where the two surfaces disagree, say which is right rather than averaging them.
3. A failure-class breakdown for every non-passing gate-2 attempt, or the explicit
   "(no non-passing attempts in scope)" line when there were none. An attempt killed
   by infrastructure emits no `attempt_outcome` and is absent by construction — say
   so rather than classifying it as passing, the way gate 1's close did.
4. **The live-run evidence, quoted raw.** Reproduce T06's raw command output from its
   result, not a summary of it. If T06 skipped rather than actually firing, or fired
   and returned `refused` / `could_not_proceed`, the mechanism claim is **not**
   verified end to end and this close must say so plainly regardless of the gate being
   green — the same discipline FEAT-2026-0041's close applied to its `gh` round-trip.
5. **The residue report.** Name the scratch issue number, every branch T06 created,
   and the pull-request number, each with its final state — closed, or still open and
   why. A killed attempt leaving residue is information about attempt behaviour, not
   litter to hide.
6. **The safety-floor assertion.** State explicitly that no pull request was merged,
   that auto-merge was not enabled, and that nothing was pushed to a protected
   branch — or report the violation. This is the feature's central safety claim.
7. A `## What the loop did NOT verify` section carrying, at minimum: **fix
   correctness as inherent** — not a gap for a later feature to close with tests; that
   one live run is one live run on one machine against a planted bug, and is not
   evidence about ephemeral runners, real findings, or concurrency; and that nothing
   fires on a schedule, because the harvest cycle is deliberately not wired to the
   firing path.
8. Consumer-visible contract changes enumerated per `close-discipline.md` §3 — the two
   new public modules and any new entry point — with blast radius **measured, not
   assumed**: state for each whether it appears in a shipped scaffold surface. Or the
   explicit `n/a` line if nothing changed for a consumer.
9. Generalizable lessons promoted to `.specfuse/LEARNINGS.md`, and the roadmap row and
   detail section for [FEAT-2026-0042](../../roadmap.md#feat-2026-0042) reconciled
   with what was actually built — including whether its "auto-fire headless
   `/fix-bug NN`" phrasing is now true.
10. A terminal `verdict` in this WU's frontmatter, well-formed and honest.
    `met_locally` with the inherent fix-quality limitation carried forward is an
    acceptable outcome and is **not** a failure of this close.
11. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

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

This work unit is sandboxed and reads its evidence from `events.jsonl` and from T06's
recorded result. Do **not** write a `gh` call: `FEAT-2026-0042/T06` is the only work
unit in this feature permitted to reach a real repository, and re-running its live
path from a close would create objects nobody is tracking. If T06's residue needs
chasing, name it for the operator rather than closing it here. Do **not** merge a
pull request, enable auto-merge, or push to a protected branch under any
circumstance — that is FEAT-2026-0048's territory and an escalation to the operator.
