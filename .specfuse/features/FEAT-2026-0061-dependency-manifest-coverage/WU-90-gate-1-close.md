---
id: FEAT-2026-0061/G1-CLOSE
type: close
status: done
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
verdict: met
auto_close: true
auto_close_reasons: []
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Close the feature in one session: re-run every oracle fresh, write
`RETROSPECTIVE.md`, promote generalizable lessons, update the roadmap, and record a
terminal verdict.

**Context.** Correlation ID `FEAT-2026-0061/G1-CLOSE`. Gate 1 is terminal, so this
is the whole closing ceremony — there is no `plan-next` and no gate 2.
`assert_gate_review_exists` does **not** apply; that guard is `plan-next`-only.

**Read `.specfuse/rules/close-discipline.md` §4 before writing anything.** The
driver's guards match literal strings and are checked *after* this WU runs, so a
mismatch costs a full re-dispatch rather than a re-arm. Run
`specfuse-lint --closing` before reporting `complete`; it is the check, and it is
cheaper than the re-dispatch.

**Do not add an acceptance criterion flipping `PLAN.md` status to `done`.** The
driver owns that flip via `fire_terminal_flips`, gated on the verdict. An agent flip
is redundant and reopens the divergence that cost issue #49.

## What is specific to this feature, and worth checking

**This feature edits the arm predicate.** Gate 1 is terminal, so there is no
successor gate for the modified predicate to evaluate and no bootstrap problem here
— but say so explicitly in the retrospective, because the next feature to touch
`arm_eval.py` in a multi-gate shape will have one, and that is exactly the kind of
thing that is obvious now and invisible in six weeks.

**The satisfiability claim was measured, so re-measure it.** `PLAN.md` asserts zero
on a correct input, backed by 0 of 169 corpus `produces:` entries using a glob or
trailing slash. Re-run that count at close against the corpus as it stands — this
feature added work units of its own, so the denominator has moved.

**The `not_evaluable` branch may be half-dead, and that is reportable either way.**
If T01's named-uncovered list emptied out, trigger 1 ships as an extension point
with no live entries and trigger 2 has never fired on real input. That is the shape
`LEARNINGS FEAT-2026-0053/G1-CLOSE` warns about — a refusal path proven on fixtures
says nothing about behaviour on real input. Name it in `## What the loop did NOT
verify` rather than letting green tests read as coverage.

**Close obligations.**

1. **Oracles re-run fresh (§1).** Every oracle this feature's criteria name, run
   again here with full commands and exit codes read directly — never a producing
   WU's self-report.
2. **Hedged follow-up record (§2).** On any verdict short of `met`, a named record
   per unmet criterion: the criterion, why it could not be verified here, and the
   exact re-run condition that upgrades it to `met`.
3. **Consumer-visible contract changes (§3).** Enumerate every addition, removal, or
   rename across T01–T02, or write exactly `n/a — no consumer-visible contract
   change`. **The widened stop class is the headline entry**: a downstream project
   running `auto` whose work units produce a newly-covered manifest will begin
   halting for human arming where it previously armed silently. That is the intended
   behaviour and it is still a behaviour change on upgrade. Say so plainly.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in the feature directory and is non-empty.
2. A `## Cost analysis` section reconciles `planned_cost_usd` — $11.50 from
   `PLAN.md`, per-WU $4.00 / $2.50 / $5.00 — against actual spend computed from
   `events.jsonl`, with the delta named. Sum every field a work unit's lifetime is
   spread across, not only frontmatter `cost_usd`: a re-armed unit's prior spend
   lives in `cumulative_cost_usd` and `re_arm_history[].prior_cost_usd`, and reading
   only the current cycle under-counts exactly the units that were retried
   (`LEARNINGS FEAT-2026-0053/G2-CLOSE`).
3. The gate's $16.50 `cost_budget_usd` is reconciled against actual gate spend, and
   any overrun is reported plainly.
4. A `## What the loop did NOT verify` section enumerates each acceptance criterion
   whose verification was deferred, with why and where it is actually verified.
   Write `(nothing — every acceptance criterion was verified in-loop)` if the list
   is empty; the explicit count must be visible either way. The `not_evaluable`
   branch's real-input status belongs here per the Context above.
5. Every oracle named by T01–T02 is re-run in this session with its full command and
   exit code recorded: `python3 -m unittest tests.test_arm_eval -v`,
   `python3 -m unittest tests.test_scaffold_data_in_sync -v`, and the full `code`
   gate set (`tests`, `lint`, `security`, `coverage --fail-under=90`, `leak-scan`).
6. The corpus sweep is re-run at close: the count of unique `produces:` entries
   across `.specfuse/features/*/WU-*.md` and how many contain a glob or trailing
   slash, compared against the 169 / 0 recorded in `PLAN.md`. Any drift is explained.
7. `evaluate_arm_predicate` is run over the real feature corpus and the
   `decision_class_paths` verdict distribution is recorded — how many `clean`,
   `fired`, `not_evaluable`. A uniformly `not_evaluable` result is reported as an
   unproven approval path, not a pass.
8. A consumer-visible contract-change enumeration is present per close obligation 3,
   naming the newly-covered manifests explicitly so a downstream operator can
   predict the behaviour change on upgrade.
9. The documented coverage list in `docs/concepts/autonomy-stop-classes.md` §3 is
   verified against the shipped table in `specfuse/loop/arm_eval.py` **in this
   session**, independently of T02's self-report, and the mirror under
   `specfuse/loop/data/docs/` is confirmed identical.
10. Whether T01's named-uncovered list shipped populated or empty is stated
    explicitly, with the rationale that decided it.
11. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
    `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`.
12. The roadmap detail section for FEAT-2026-0061 is updated to reflect what was
    actually built, including which of the two chartered decisions were settled and
    how.
13. This WU's **frontmatter** carries a `verdict:` field whose value is one of
    `met`, `met_locally`, `partially_met`, `not_met`.
14. If any work unit in this gate recorded a failed attempt, a literal
    `### Failure-class breakdown` heading is present with the classes named.
15. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Source files owned by T01–T02 — this WU closes the gate, it does
not patch the work. `PLAN.md`'s `status` field. `JUDGE_PATHS` and the other seven
stop classes. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set for closing WUs, plus the oracle re-runs
in criteria 5–7 and 9, which are this WU's real verification surface. The `assert_*`
guards are checked by the driver after this WU completes; `specfuse-lint --closing`
(criterion 15) is the in-session check for them.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
oracle named in criterion 5 cannot be re-run; `events.jsonl` lacks the cost data
criterion 2 reconciles against; the documented list and the shipped table disagree
at criterion 9, which means T02 shipped a defect and the fix is a re-dispatch of T02
rather than an edit from this session; or the consumer-visible contract-change list
requires a human acknowledgment that has not been given. Record a hedged verdict
(`met_locally` / `partially_met`) with the follow-up record from close obligation 2
rather than claiming `met` for a criterion verified only by a producing WU's
self-report.
