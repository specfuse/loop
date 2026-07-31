---
id: FEAT-2026-0053/G2-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 1
planned_cost_usd: 4.50
oracle_env: macos_local
auto_close_disabled: true
provenance: "Required by .specfuse/rules/close-discipline.md and by the linter's non-terminal closing-shape check (close-intermediate immediately followed by plan-next); not part of PLAN.md's gate-2 sketch, which enumerated only the five substantive items."
model: opus
effort: high
gate_set: plannext
driver_version: 0.7.1
started_at: 2026-07-31T02:41:49.822710+00:00
duration_seconds: 674.554
cost_usd: 5.671201
input_tokens: 1882
output_tokens: 47997
---

# Close gate 2 — retrospective, lessons, docs

**Objective.** Fold the retrospective, the lessons promotion, and the docs and
roadmap update into one session for gate 2. Non-terminal gate: `G2-PLAN` runs
next; this unit records no terminal verdict.

**Context.** Correlation ID `FEAT-2026-0053/G2-CLOSE-INTERMEDIATE`. Depends on
T05–T09 — the gate that made `auto` real: the arm transaction module, the dial
and verdict wiring, the contract-field severity flip, `FEATURE-REVIEW.md`
accumulation, and LEARNINGS staging.

**Run `specfuse-lint --closing` before emitting your RESULT block** and confirm
it exits 0. Per `.specfuse/rules/close-discipline.md` §4 that lint reads the same
registry the driver checks, so a format mismatch is caught while it is still
cheap to fix; the guard-required files and headings are pre-created at dispatch,
so fill the skeleton in rather than reconstructing its shape. Note the
`### Failure-class breakdown` obligation applies only if a failed attempt
occurred in this gate. `assert_verdict_well_formed` does not apply — terminal
verdicts belong to `G3-CLOSE`.

**Close obligations.**

1. **Oracles re-run fresh (§1).** Every oracle T05–T09 name, re-run here with
   full commands and exit codes read directly — never a producing unit's
   self-report.
2. **Consumer-visible contract changes (§3).** Gate 2's list is larger and less
   purely additive than gate 1's, and at least one item changes an existing
   payload rather than adding beside it. Enumerate every one, or write exactly
   `n/a — no consumer-visible contract change`.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` contains the literal heading `## Gate 2` — spelled with
   the digit, not "Gate two" — non-empty, with gate 1's section left intact and
   unedited. `assert_retrospective_gate_section` matches this after dispatch, so
   a wrong spelling costs a full re-attempt.
2. A `## Cost analysis` section reconciles gate 2's `planned_cost_usd` — $25.50
   across seven units (T05 $3.50, T06 $3.50, T07 $3.00, T08 $2.50, T09 $2.50,
   this unit $4.50, `G2-PLAN` $6.00) — against actual spend read from
   `events.jsonl`, with the delta named, counting every attempt including
   non-passing ones. State gate spend against `GATE-02.md`'s `cost_budget_usd`.
3. A `## What the loop did NOT verify` section enumerates each deferred
   criterion with why and where it is actually verified. **Two entries are known
   in advance and must appear unless this gate proves them wrong:**
   - **No live arm happened on this feature.** FEAT-2026-0053 runs
     `autonomy_default: review` by decision (`[FEAT-2026-0007/G2-LESSONS]` — an
     enforcement mechanism cannot be exercised by the gate that builds it), so
     every auto-arm path is verified by tests and by no production ride. The
     first live arm belongs to a successor feature after this branch merges.
   - **`drift_caps` is unproven on this feature.** Per `RETROSPECTIVE.md`
     Findings §2, this feature's `PLAN.baseline.json` was captured *after* its
     own gate-2 drafting, so it already contains gate 2. A clean `drift_caps`
     verdict here measures nothing. Do not cite it as evidence drift detection
     works.
4. Every oracle named by T05–T09 is re-run in this session with command and exit
   code recorded: `python3 -m unittest tests.test_arm_txn -v`,
   `tests.test_arm_wiring`, `tests.test_arm_eval_lint_class`,
   `tests.test_arm_eval`, `tests.test_feature_review_accumulation`,
   `tests.test_learnings_staging`, `tests.test_scaffold_data_in_sync`, plus the
   symbol-existence imports for `arm_txn` and for `plan_next_lint` in
   `CLASS_NAMES` / `VETO_CLASSES`.
5. A consumer-visible contract-change enumeration is present per close
   obligation 2, covering at minimum: the new module `specfuse/loop/arm_txn.py`;
   the eighth predicate class `plan_next_lint` and the resulting change to the
   `arm_predicate_evaluated` payload's `classes` map and to the published
   `CLASS_NAMES` / `VETO_CLASSES` constants; the new event type
   `gate_auto_armed`; the new tag namespace `pre-arm/<feature-id>/gate-<N>`; the
   new per-feature artifacts `FEATURE-REVIEW.md` and `LEARNINGS-pending.md`; the
   new template `LEARNINGS-pending.template.md`; and the new behavior that an
   `auto` feature's gate flips to `passed` without a human.
6. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
   `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`. This
   feature is `review`, so T09's staging invariant is inert here and lessons go
   to the durable file as usual — say so explicitly rather than leaving the
   reader to wonder whether the new mechanism was bypassed.
7. The roadmap detail section for FEAT-2026-0053 reflects what gate 2 actually
   built.
8. If any work unit in this gate recorded a failed attempt, a literal
   `### Failure-class breakdown` heading is present with the classes named.

**Do not touch.** Source files owned by T05–T09 — this unit closes the gate, it
does not patch the work. `PLAN.md`'s `status` field. Gate 3's work units —
`G2-PLAN` drafts those. Gate 1's `RETROSPECTIVE.md` section. Generated
directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set for closing units, plus the oracle
re-runs in criterion 4 and `specfuse-lint --closing` exiting 0, which together
are this unit's real verification surface.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
an oracle in criterion 4 cannot be re-run; `events.jsonl` lacks the cost data
criterion 2 reconciles against; or a T05–T09 deliverable turns out to contradict
another (for example, the arm's single-commit guarantee not actually holding
once `FEATURE-REVIEW.md` joined the write set). Per
`.specfuse/rules/result-contract.md` closing obligation 2, a plan-level
contradiction is `blocked`, not a finding written into a gate document and
closed `complete`.
