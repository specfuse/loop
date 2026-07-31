---
id: FEAT-2026-0053/G3-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
auto_close_disabled: true
---

# Close the feature — terminal verdict

**Objective.** Terminal close for FEAT-2026-0053: gate 3's retrospective
section, the lessons, the docs pass, and the **feature-arc verdict** across all
three gates, in one session.

**Context.** Correlation ID `FEAT-2026-0053/G3-CLOSE`. This is the terminal gate
of a feature that made the `auto` autonomy level real: gate 1 built the arm
predicate and the plan baseline and wired a passive shadow trail, gate 2 made
the dial live behind an atomic one-commit arm, gate 3 made the result legible.
`auto_close_disabled: true` is set because this close carries close-discipline
§3 (consumer-visible contract changes across all gates), which is always
load-bearing.

`RETROSPECTIVE.md` already carries full `## Gate 1` and `## Gate 2` sections
written by the two intermediate closes — **read them, do not rewrite them.**
This close appends `## Gate 3` and the feature-arc verdict.

**This feature runs `autonomy_default: review`.** T09's LEARNINGS-staging
invariant is therefore inert here and lessons go to the durable
`.specfuse/LEARNINGS.md` as usual — no `LEARNINGS-pending.md` is created and
none should be. Gate 2's close said so explicitly for the same reason; say it
again, because a terminal close on the feature that *built* the staging
mechanism is exactly where a reader will wonder whether it was bypassed.

**Close obligations (`.specfuse/rules/close-discipline.md`).**

1. **Oracles re-run fresh (§1).** Every oracle T10–T13 name, re-run in this
   session against the working tree, full commands, exit codes read directly —
   not after a pipe, and never inherited from a producing WU's self-report. At
   minimum: `python3 -m unittest discover -s tests -v`,
   `python3 -m unittest tests.test_scaffold_data_in_sync -v`,
   `python3 -m unittest tests.test_skills_vendored_in_sync -v`, and T11's
   class-coverage assertion.
2. **Hedged follow-up record (§2).** On `met_locally`, one named record per
   unmet criterion: the criterion verbatim, why it is unverifiable in this
   environment, and the exact re-run condition that upgrades it to `met`.
   **Expect to need this.** Both prior gates carry criteria whose real oracle is
   a driver run on a *successor* feature — the first live arm, `drift_caps` on a
   feature whose first dispatch postdates this branch, `plan_next_lint`'s firing
   path on a real folder, and the `LEARNINGS-pending.md` promotion step no human
   has yet performed. A verdict of `met` that ignores them would be false.
3. **Consumer-visible contract changes (§3), enumerated across all three
   gates.** Gate 1's five items and gate 2's ten are already written in
   `RETROSPECTIVE.md`; this close adds gate 3's and presents the consolidated
   list for explicit human acknowledgment. Gate 2 flagged three items as needing
   it by name — the eight-key `classes` map, the force-created `pre-arm/` tag
   namespace, and the changed bookkeeping commit message. If gate 3 adds none of
   its own, write exactly `n/a — no consumer-visible contract change` for gate 3
   rather than fabricating an empty enumeration.
4. **Run `specfuse-lint --closing` before emitting the RESULT block (§4).** It
   reads the same registry the driver checks and reports per-requirement in
   session, so a shape mismatch is fixed while it is still cheap.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` gains a `## Gate 3` section covering T10–T13: what
   shipped, what each WU's oracle actually proved, and — for the documentation
   WUs specifically — the honest statement that a green test suite proves the
   copies match and nothing regressed, not that the prose is correct.
2. A `## Cost analysis` section **reconciles planned against actual for gate 3
   and for the whole feature**, with actuals summed from `attempt_outcome`
   payloads in `events.jsonl` across **all** attempts including non-passing
   ones and every dispatch cycle before a re-arm. Gate 3's planned figure is
   $17.00 across five units against `GATE-03.md`'s `cost_budget_usd: 22.00`;
   the feature's `planned_cost_usd` is $66.00.
3. The cost analysis states the feature-level spend against the $66.00 plan and
   **carries forward gate 2's Findings §1 rather than re-deriving it**: the arm
   predicate's `budget_projection` under-reads lifetime spend because it reads
   only `cost_usd`, never `cumulative_cost_usd` and never
   `re_arm_history[].prior_cost_usd` — measured at $6.23 (14.8%) on this feature
   at gate 2's close. Re-measure it at terminal, name a home for the fix, and do
   not fix it here.
4. A `### Failure-class breakdown` section is present whenever gate 3 has any
   non-passing attempt, with one row per `failure_class` and its dominant
   signature. An agent-reported block carries `failure_class: null` and is still
   an attempt — count it, and name its class by hand as both prior gates did.
5. A `## What the loop did NOT verify` section **enumerates** every
   definition-of-done criterion across all three gates whose real oracle lies
   outside this feature, each with: what was verified in-loop, what was not, why,
   and **where it is actually verified**. The four named in obligation 2 above
   are the floor, not the ceiling — gate 2's own section lists six.
6. A **feature-arc verdict** states whether the feature delivered its roadmap
   goal — *"a four-gate feature costs one human touch (the PR review) instead of
   four"* — and is honest about the fact that no feature has yet ridden `auto`
   in production. The frontmatter `verdict` field is one of `met`,
   `met_locally`, `partially_met`, `not_met` and matches the prose.
7. Durable cross-feature lessons are appended to `.specfuse/LEARNINGS.md` under
   `[FEAT-2026-0053/G3-CLOSE]`, and the close states explicitly that staging to
   `LEARNINGS-pending.md` correctly did not apply because this feature runs
   `review`.
8. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0053-auto-mode`
   exits `0`, and `specfuse-lint --closing` reports every requirement met before
   the RESULT block is written.
9. Every oracle in obligation 1 was re-run in this session with its exit code
   recorded in `RETROSPECTIVE.md`'s gate-3 oracle table. A cited exit code that
   was not observed in this session fails this criterion.

**Do not touch.** `RETROSPECTIVE.md`'s existing `## Gate 1` and `## Gate 2`
sections — they are the record of what those closes found, and a terminal close
that edits them destroys the evidence a reviewer needs. Source files owned by
T01–T13. The `budget_projection` under-read from gate 2's Findings §1: measure
it, name a home, do not fix it — a driver behavior change inside a terminal
close is unreviewable. Gate 1's and gate 2's `GATE-NN.md` files and their review
files. Historical feature folders. `.specfuse/rules/`. Generated directories,
secrets, `.git/`. The driver owns all git — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set, plus the four oracles named in
obligation 1 re-run fresh, plus `specfuse-lint --closing` and the structural
lint in criterion 8. `assert_verdict_well_formed` checks the frontmatter
`verdict` at outcome time; the prose must agree with it.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if
an oracle T10–T13 named cannot be re-run in this environment — a close that
cites an exit code it did not observe is the specific failure
`close-discipline.md` §1 exists to prevent. Emit `status: blocked` if the
consolidated contract-change list cannot be assembled because a producing WU's
consumer-visible surface is undetermined. Do **not** resolve a hedged verdict by
narrowing the criterion: `met_locally` with a follow-up record is the honest
outcome here and `partially_met` is available below it. Blocked remains a
respectable outcome (`result-contract.md` rule 4).
