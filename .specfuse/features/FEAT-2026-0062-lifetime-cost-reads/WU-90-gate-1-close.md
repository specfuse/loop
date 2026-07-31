---
id: FEAT-2026-0062/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Close the feature in one session: re-run every oracle fresh, write
`RETROSPECTIVE.md`, promote generalizable lessons, update the roadmap, and record a
terminal verdict.

**Context.** Correlation ID `FEAT-2026-0062/G1-CLOSE`. Gate 1 is terminal, so this is
the whole closing ceremony — there is no `plan-next` and no gate 2.
`assert_gate_review_exists` does **not** apply; that guard is `plan-next`-only.

**Read `.specfuse/rules/close-discipline.md` §4 before writing anything.** The
driver's guards match literal strings and are checked *after* this WU runs, so a
mismatch costs a full re-dispatch rather than a re-arm. Run `specfuse-lint --closing`
before reporting `complete`; it is the check, and it is cheaper than the re-dispatch.

**Do not add an acceptance criterion flipping `PLAN.md` status to `done`.** The
driver owns that flip via `fire_terminal_flips`, gated on the verdict.

## What is specific to this feature

**This close reconciles against the surface the feature just made canonical.** Every
close computes actual spend from `events.jsonl`; this feature makes that the
driver's source too. So the reconciliation below is not bookkeeping — it is the
deliverable being exercised. If the close's own event-sum disagrees with what
`gate_spent_usd` now reports for this gate, that is a defect in T01/T02 found by the
close, and it must be reported rather than reconciled away by hand.

**The gate's own brake is T03's live test.** This gate declares
`cost_budget_usd: 21.00`. If the gate overran inside its final work unit, T03's new
post-dispatch check is what should have surfaced it. State plainly whether the gate
overran, and whether the new check fired — including "did not overrun, so the new
check was not exercised in production", which is an honest and useful negative.

**Neither prior feature's mistake is available as an excuse here.** FEAT-2026-0061's
gate auto-closed on-plan and logged 26 criteria as deferred debt that a human had to
verify by hand at wrap time. If this gate auto-closes the same way, the debt block
is the record and the same manual verification is owed — say so in the retrospective
rather than letting a clean auto-close read as verification.

**Close obligations.**

1. **Oracles re-run fresh (§1).** Every oracle this feature's criteria name, run
   again here with full commands and exit codes read directly — never a producing
   WU's self-report.
2. **Hedged follow-up record (§2).** On any verdict short of `met`, a named record
   per unmet criterion: the criterion, why it could not be verified here, and the
   exact re-run condition that upgrades it to `met`.
3. **Consumer-visible contract changes (§3).** Enumerate every addition, removal, or
   rename across T01–T03, or write exactly `n/a — no consumer-visible contract
   change`. **Two headline entries are expected.** A downstream project will see
   `budget_projection` begin firing on features it previously passed, because those
   features were over budget and under-read — the stop is correct and it is still new
   behaviour on upgrade. And a gate that overruns on its final work unit will begin
   reporting a breach where it previously closed silently.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in the feature directory and is non-empty.
2. A `## Cost analysis` section reconciles `planned_cost_usd` — $16.00 from
   `PLAN.md`, per-WU $4.00 / $3.50 / $3.50 / $5.00 — against actual spend computed
   from `events.jsonl`, with the delta named.
3. The same total is computed a second way, via the `wu_lifetime_cost_usd` helper
   this feature shipped, and the two figures are compared. Any disagreement is
   reported as a defect in T01/T02, not smoothed over.
4. The gate's $21.00 `cost_budget_usd` is reconciled against actual gate spend.
   State whether the gate overran and whether T03's post-dispatch check fired,
   including the negative case.
5. A `## What the loop did NOT verify` section enumerates each acceptance criterion
   whose verification was deferred, with why and where it is actually verified. Write
   `(nothing — every acceptance criterion was verified in-loop)` if the list is
   empty; the explicit count must be visible either way.
6. Every oracle named by T01–T03 is re-run in this session with its full command and
   exit code recorded: `python3 -m unittest tests.test_cost_lifetime -v`,
   `tests.test_arm_eval`, `tests.test_gate_budget`,
   `tests.test_gate_budget_post_dispatch`, and the full `code` gate set (`tests`,
   `lint`, `security`, `coverage --fail-under=90`, `leak-scan`).
7. T01's criterion-9 fallback measurement is **re-run at close** and its numbers
   recorded: how many work units across the corpus take the events path, how many the
   fallback, and how many of the fallback set are fold-never-ran. That last number is
   the residual under-read this design knowingly accepts and belongs in
   `## What the loop did NOT verify` if non-zero.
8. T02's criterion-10 sweep is re-run: how many `budget_projection` verdicts across
   all 44 features changed from `clean` to `fired`. Each one is a feature that was
   over budget and not stopped — enumerate them.
9. A consumer-visible contract-change enumeration is present per close obligation 3,
   naming both expected headline entries explicitly.
10. Whether T03 emitted a new `event_type` or reused `human_escalation` is stated,
    and if a new type was added, FEAT-2026-0060 is named as the feature that must
    sanction it.
11. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
    `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`.
12. The roadmap detail section for FEAT-2026-0062 is updated to reflect what was
    actually built — including the correction that `gate_spent_usd` was already
    partly fixed and the real defect was the fold-never-ran shape, since the roadmap
    currently states otherwise.
13. This WU's **frontmatter** carries a `verdict:` field whose value is one of `met`,
    `met_locally`, `partially_met`, `not_met`.
14. If any work unit in this gate recorded a failed attempt, a literal
    `### Failure-class breakdown` heading is present with the classes named.
15. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Source files owned by T01–T03 — this WU closes the gate, it does
not patch the work. `PLAN.md`'s `status` field. `fold_cumulative_on_rearm` and
`detect_rearm_dispatch` — out of scope per `PLAN.md`, and the follow-up row for them
is the operator's to file. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set for closing WUs, plus the oracle re-runs in
criteria 6–8, which are this WU's real verification surface. The `assert_*` guards
are checked by the driver after this WU completes; `specfuse-lint --closing`
(criterion 15) is the in-session check for them.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
oracle named in criterion 6 cannot be re-run; the two independent cost totals in
criterion 3 disagree, which means the feature's own deliverable is wrong and the fix
is a re-dispatch of T01 or T02 rather than an edit from this session; `events.jsonl`
lacks the data criterion 2 reconciles against — which would itself be evidence
against the design this feature chose; or the consumer-visible contract-change list
requires a human acknowledgment that has not been given. Record a hedged verdict
(`met_locally` / `partially_met`) with the follow-up record from close obligation 2
rather than claiming `met` for a criterion verified only by a producing WU's
self-report.
