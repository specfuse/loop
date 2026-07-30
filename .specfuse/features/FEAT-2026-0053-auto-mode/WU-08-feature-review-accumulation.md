---
id: FEAT-2026-0053/T08
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/loop/arm_txn.py
  - tests/test_feature_review_accumulation.py
---

# `FEATURE-REVIEW.md` — every auto-armed gate's doubt reaches the one human read

**Objective.** Make each auto-arm append the gate's doubt summary to a
feature-local `FEATURE-REVIEW.md`, inside the same single arm commit, so the PR
review sees every doubt that no human read at a gate boundary.

**Context.** Correlation ID `FEAT-2026-0053/T08`. Depends on T05 (the arm
transaction) and T06 (the arm branch). `auto` removes the per-gate human read;
PLAN.md's scope decisions accept that removal explicitly — *"the PR read is fed
by accumulated per-gate doubt summaries"* — and this WU is that feed. Without
it, `auto` does not relocate the checkpoint, it deletes it.

**What accumulates.** At each auto-arm of gate `N+1`, append one section to
`FEATURE-REVIEW.md` in the feature directory containing, for the just-closed
gate `N`:

- the gate number and the arm timestamp;
- the `open_questions:` list from `GATE-{N+1}-REVIEW.md` frontmatter, verbatim
  (an empty list is recorded as empty — that is information, not absence);
- the `## Doubt` section of `GATE-{N+1}-REVIEW.md`, verbatim;
- the predicate verdict line: `would_arm` plus each class's status, so the
  reader can see *which* checks let this gate through.

**Doubt prose stays decoupled from the arming signal.** The `## Doubt` section
is copied and never parsed for a verdict — PLAN.md's drafting decision is that
being doubtful in prose must stay free, or the drafting model learns hedging is
expensive and stops hedging anywhere. This WU must not introduce any read of
that section that could influence whether an arm happens.

**Only on auto-arm.** A `review` or `supervised` feature already gets a human
read at each gate boundary; appending there would duplicate what the human just
did. Accumulation fires exactly where the human read was skipped.

**Atomicity is inherited, not re-invented.** `FEATURE-REVIEW.md` joins the arm
transaction's path list so it lands in the one arm commit alongside the
draft→pending flips and the gate flip. It must not be committed separately —
a second commit would reintroduce the half-armed state the single commit exists
to prevent.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_feature_review_accumulation.py::TestFeatureReviewAccumulation::test_auto_arm_appends_gate_section`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist — red).
2. `specfuse/loop/arm_txn.py` exposes `append_feature_review_entry` and
   `FEATURE-REVIEW.md` appears in the arm transaction's `paths` list, verified
   by `python3 -c "from specfuse.loop.arm_txn import append_feature_review_entry"`
   plus a test asserting the path is in the transaction.
3. One auto-arm of gate `N+1` appends exactly one section for gate `N`
   containing the gate number, the verbatim `open_questions` list, the verbatim
   `## Doubt` section text, and the per-class verdict line.
4. Two successive auto-arms produce two sections in gate order, and neither
   rewrites nor reorders the other's text — the file is append-only.
5. The appended `FEATURE-REVIEW.md` is present in the **same** commit as the
   arm's status flips, asserted by reading that single commit's changed-path
   list.
6. A `review` and a `supervised` feature closing the same gate write no
   `FEATURE-REVIEW.md` at all.
7. A `GATE-{N+1}-REVIEW.md` with no `## Doubt` section, or with an unparseable
   frontmatter, still produces a section — recording the absence explicitly
   rather than raising. An arm must not crash on a malformed review file.
8. `tests/test_feature_review_accumulation.py::TestFeatureReviewAccumulation::test_auto_arm_appends_gate_section`
   **passes after this WU's edits**, and
   `python3 -m unittest tests.test_feature_review_accumulation -v` exits 0.

**Do not touch.** The arm predicate's inputs — nothing in `FEATURE-REVIEW.md`
and nothing in the `## Doubt` section may become a predicate input; that
coupling is the exact thing PLAN.md's drafting decision forbids. `specfuse/loop/arm_eval.py`.
The severity flip (T07). LEARNINGS staging (T09). The commit structure of the
arm (T06) beyond adding this path to the existing write set. Gate review files
of other features. Generated directories, secrets, `.git/`. The driver owns all
git — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration run: `python3 -m unittest tests.test_feature_review_accumulation -v`,
plus `python3 -m unittest tests.test_arm_txn -v` — this WU extends T05's module
and must not regress its suite. Plus the symbol check in criterion 2.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`GATE-{N+1}-REVIEW.md` has no stable, agreed section name for the doubt prose
(this WU copies a named section; inventing a second convention for where doubt
lives is a plan-level contradiction, not an implementation detail); or if
appending `FEATURE-REVIEW.md` cannot be made part of the arm's single commit
without restructuring the close path. If `append_feature_review_entry` is absent
from the files you edited, emit `status: blocked` — do not claim complete.
