---
id: FEAT-2026-0059/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
verdict: met_locally
model: opus
effort: high
gate_set: plannext
driver_version: 0.8.0
started_at: 2026-08-04T13:02:24.509898+00:00
duration_seconds: 893.558
cost_usd: 5.586782
input_tokens: 104
output_tokens: 39962
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Terminal close for FEAT-2026-0059: write the retrospective, promote
generalizable lessons, reconcile documentation and roadmap, and record the terminal
verdict.

**Context.** Correlation ID `FEAT-2026-0059/G1-CLOSE`. Single terminal gate, so this
WU collapses retrospective, lessons, docs, and verdict into one session. Read
`PLAN.md` and `GATE-01.md` first.

**Why `auto_close_disabled: true`.** A terminal close carrying §1–§3 obligations is
load-bearing per `close-discipline.md`. Issue #293's case: FEAT-2026-0061 lost all 26
close criteria to an on-plan auto-close, FEAT-2026-0063 lost its roadmap retitle.

Binding rules apply by reference: `close-discipline.md`, `result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

## What this close must get right, specific to this feature

**This close is the feature's own first test.** If it hedges, its record is the first
one written under T01's new contract — so every entry must carry a `kind:`, and the
close should say plainly whether classifying them was easier or harder than writing
the old free-prose record. That is the only real evidence this feature works, and no
test can produce it.

If it closes `met`, say so and note that the contract went unexercised by its own
feature — an honest gap, not a silent one.

**The four kinds versus the roadmap row's three.** The row proposed three; this
feature ships four, adding `inherent`. Record that decision and its evidence
(FEAT-2026-0042's close inventing the category in prose because the contract had no
slot), so a reader comparing the row to the code is not left guessing whether the
fourth was an oversight or a choice.

**A release follows this feature and FEAT-2026-0064.** T01 changes a rule contract
that ships in the scaffold. Its consumer-visible enumeration is the raw material
0064's CHANGELOG will consume, so §3 matters more than usual here — enumerate
precisely rather than gesturing at "the rules changed".

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists at the feature root with a literal `## Gate 1` heading
   and a literal `## Cost analysis` section reconciling planned against actual — the
   $14.50 WU sum and $19.50 gate budget against the `attempt_outcome` sum in
   `events.jsonl`, which is authoritative. Both headings are checked after dispatch;
   omitting either costs a full re-attempt.
2. The deferred-verification list is written with, per entry, the criterion, why it
   was not verified in-loop, and where it actually gets checked — or the explicit
   `(nothing — every acceptance criterion was verified in-loop)` line.
3. If this close hedges, **its own record carries `kind:` on every entry** per T01's
   contract, and the close reports whether classifying was easier than free prose.
   If it does not hedge, the close states that the contract was not exercised by its
   own feature.
4. `## What the loop did NOT verify` names the one thing tests cannot reach: whether
   the ceiling headline actually helps a human decide faster. No test can measure
   that; it is verified only by an operator running `/accept-hedged-close` on the
   next real hedge, and the close should say so rather than imply the tests covered
   it.
5. The four-versus-three decision is recorded with its evidence.
6. Generalizable lessons are promoted to `.specfuse/LEARNINGS.md` tagged with this
   WU's correlation ID. Candidate worth assessing: whether "a contract that forces a
   close to classify its own gaps produces better records than one asking for prose"
   generalizes beyond hedged verdicts.
7. Consumer-visible contract changes are enumerated per `close-discipline.md` §3, or
   the explicit `n/a` line is written. At least two are known: `close-discipline.md`
   §2 gains a required field (every downstream project's next hedged close must
   supply it), and `/accept-hedged-close` changes its output shape.
8. The roadmap row and detail section reflect what was actually built, including the
   fourth kind.
9. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` field — the driver owns the terminal flip via
`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`. Source files owned
by T01–T03. FEAT-2026-0041's and FEAT-2026-0042's retrospectives.

**Verification.** The `plannext` gate set for closing WUs, plus `specfuse-lint
--closing` exiting 0 (criterion 9) before this WU reports `complete`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`events.jsonl` cost sum cannot be reconciled against frontmatter (report a lower
bound and name the gap rather than inventing a number); or T01's own lint refuses
this close's record, which would mean the contract is unsatisfiable by the feature
that shipped it and is a finding worth stopping for rather than working around.
