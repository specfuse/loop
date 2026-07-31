---
id: FEAT-2026-0053/G1-PLAN
type: plan-next
status: done
attempts: 1
planned_cost_usd: 6.00
oracle_env: macos_local
model: opus
effort: high
gate_set: plannext
driver_version: 0.7.1
started_at: 2026-07-30T20:57:30.962343+00:00
duration_seconds: 866.84
cost_usd: 6.684054
input_tokens: 115
output_tokens: 64001
---

# Draft gate 2 — live arming behind the dial

**Objective.** Draft gate 2's substantive work units into `PLAN.md`, and write
`GATE-02-REVIEW.md` for the human review-and-arm checkpoint.

**Context.** Correlation ID `FEAT-2026-0053/G1-PLAN`. Depends on
`G1-CLOSE-INTERMEDIATE`, whose retrospective and lessons are this unit's
primary input — gate 2 is drafted from what gate 1 actually learned.

**The review artifact is named for the gate being armed, not the gate being
closed.** `assert_gate_review_exists` requires **`GATE-02-REVIEW.md`** —
`close-discipline.md` §4 records this as the single most expensive guard in the
system.

**What gate 2 is for.** Acting on the predicate's verdict, behind the dial.
The shape decided at drafting and not re-openable by this unit:

1. **The atomic arm transaction.** When `autonomy_default: auto` and the
   predicate returns `would_arm: True`, the driver arms in ONE bookkeeping
   commit: draft→pending flips, gate `awaiting_review → passed`, and a
   tag-before-arm revert point (`pre-arm/FEAT-YYYY-NNNN/gate-N`). A crash
   between writes must not strand a half-armed feature — atomicity via the
   single commit is the design, and a recovery rule keyed on it.
2. **The dial.** Read `autonomy_default` from PLAN frontmatter. `auto` acts on
   the verdict; `review` and `supervised` behave exactly as today. Any stop
   class firing parks at `awaiting_review` with the reason in the event —
   escalation always overrides autonomy.
3. **Lint warns flip to blocking under `auto` only.** This is a severity flip:
   planning-discipline §4's runtime probe is mandatory at arming (run the lint
   over every feature folder in this repo, paste the finding list into
   `GATE-02-REVIEW.md`), and §2's satisfiability answer is mandatory in the
   drafted WU (a correct feature with complete contract fields reports zero).
4. **FEATURE-REVIEW.md accumulation.** Each auto-armed gate's doubt summary
   appends to a feature-local `FEATURE-REVIEW.md` so the PR review — the one
   human read — sees every accumulated doubt.
5. **LEARNINGS staging.** Under `auto`, lessons append to a pending file
   (`LEARNINGS-pending.md` or equivalent) promoted by a human at PR review —
   an unread misframed gate must not write durable cross-feature rules.

**Dogfood obligation.** T02's contract fields are live in lint as warns: this
unit's own output must carry them — `open_questions:` in `GATE-02-REVIEW.md`'s
frontmatter (empty only if genuinely empty), `provenance:` on any WU this draft
adds beyond the PLAN's gate-2 sketch, `human_only: true` where warranted. This
plan-next is the contract's first producer; drafting gate 2 without the fields
would be the feature contradicting itself.

**Acceptance criteria.**

1. `GATE-02-REVIEW.md` exists in the feature directory, is non-empty, and its
   frontmatter carries an explicit `open_questions:` list.
2. `PLAN.md`'s gate 2 `work_units` list is no longer empty and contains at
   least one entry at `status: draft`.
3. Every drafted gate-2 WU file exists, is `status: draft`, and carries the
   five mandatory body sections.
4. Drafted WUs cover, at minimum: the atomic arm transaction with
   tag-before-arm; the dial read and act-on-verdict path; the
   blocking-under-auto lint flip; FEATURE-REVIEW.md accumulation; and
   LEARNINGS staging. (One WU may cover more than one item where sizing
   honestly allows; five items, not necessarily five WUs.)
5. The lint-flip WU answers escalation-predicate satisfiability (§2) in its
   body, and `GATE-02-REVIEW.md` records the §4 runtime-probe requirement with
   the instruction that the probe's finding list must be pasted in before
   arming.
6. Every drafted WU carries a `planned_cost_usd`, and `GATE-02.md` carries a
   `cost_budget_usd` equal to their sum plus one re-attempt of the largest.
7. `PLAN.md`'s `planned_cost_usd` is re-baselined to include gate 2's drafted
   units, and the delta against $28.50 is stated in `GATE-02-REVIEW.md`.
8. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0053-auto-mode`
   exits zero.

**Do not touch.** Source files owned by T01–T04. `RETROSPECTIVE.md` — the
previous unit wrote it; this one reads it. Gate 3's `close` placeholder, beyond
leaving it in place as the terminal entry. `PLAN.md`'s `status` field.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set, plus criterion 8's lint run over the
whole feature folder. Drafted WUs are prose: criteria 4–5 are the structural
floor; the human at the arming checkpoint is the real quality gate, and
`GATE-02-REVIEW.md` exists to support that read.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
gate 1's retrospective reports a finding that invalidates the drafted gate-2
shape — for example that the `awaiting_review` flip sites T04 enumerated make a
single atomic arm transaction impossible without a close-path refactor; or the
§2 satisfiability answer for the lint flip cannot honestly be "zero on a
correct input." A gate-2 draft built on a premise gate 1 disproved is worse
than no draft.
