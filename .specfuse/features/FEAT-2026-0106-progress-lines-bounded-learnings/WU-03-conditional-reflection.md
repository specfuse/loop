---
id: FEAT-2026-0106/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces_driver_helper:
  - reflection_required
produces:
  - tests/test_conditional_reflection.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.19.0
started_at: 2026-09-14T01:02:23.873669+00:00
duration_seconds: 1275.091
cost_usd: 6.133309
input_tokens: 238
output_tokens: 94167
---

# Write reflective prose only when the gate went off-plan

**Objective.** Make the close's reflective closing requirements conditional on
`evaluate_auto_close`'s off-plan signal, leaving measurements and every
non-reflective obligation unconditional.

**Context.** FEAT-2026-0106/T03. The roadmap row asked for "a retrospective
only on `not_met`", which PLAN.md records as superseded: the close writes
`RETROSPECTIVE.md` and only then does the judge produce a verdict, so there is
no `not_met` to condition on at write time. `gate_eval.evaluate_auto_close`
already computes a verdict-independent off-plan signal from events the driver
holds — blocked WU, `replan` event, cost overrun — and it is already the
signal the methodology uses to decide a gate deserves reflection.

The split this unit must respect: `judge.py:237-238` slices
`## Measurements` out of `RETROSPECTIVE.md` for the judge's evidence bundle,
while the judge prompt forbids opening the file. Measurements are evidence and
stay unconditional. Reflective prose is what the judge may not read, and is
what becomes conditional.

**Acceptance criteria.**

- `python3 -m unittest tests.test_conditional_reflection -v -b` fails on HEAD
  before this unit's edits and passes after.
- Driving a real `loop.run()` through an **on-plan** gate: the close produces
  a `RETROSPECTIVE.md` whose `## Measurements` section is present and
  non-empty, and `judge.build_judge_bundle` over that feature directory
  returns a non-empty `measurements`. The judge's evidence survives a skipped
  reflection, asserted through the judge's own bundle builder rather than by
  reading the file.
- Driving an **off-plan** gate — one carrying a `replan` event or a
  `blocked_human` unit — produces the reflective sections in full, identical
  to today's output. The off-plan path is the regression surface: it is what
  every existing project keeps.
- This unit carries a flag-scope table naming **every** closing requirement in
  `closing_requirements.py` and whether the condition gates it, so no
  obligation changes state without being listed
  (`planning-discipline.md` §3).

**Do not touch.** `judge.py` and the judge's evidence bundle.
`assert_learnings_appended_or_noop` — bounding `LEARNINGS.md` is out of scope
for this feature and that guard keeps its current behaviour. `PROGRESS.md`'s
writer (T01's). The sibling WU files in this gate.

**Verification.** The narrow tier is NOT sufficient: this edits the closing
requirements every feature's close runs against, so run the **full** suite —
`python3 -m unittest discover -s tests -b` — before reporting complete. Plus
`python3 -m unittest tests.test_conditional_reflection tests.test_progress_lines_end_to_end -v -b`
and the symbol check (§9):
`python3 -c "from specfuse.loop.loop import reflection_required"`.

**Escalation triggers.** Stop with `status: blocked` if suppressing a
reflective section cannot be done without also suppressing something the judge
reads — that means the two roles are not separable at the registry's
granularity, and splitting the artifact is a different feature.

**Flag-scope table (`planning-discipline.md` §3).** The flag is
`reflection_required` (via `gate_eval.evaluate_off_plan_signal`). Every
requirement in `closing_requirements.py`, and whether this unit's condition
gates it:

| Requirement (`closing_requirements.py`) | Gated by `reflection_required`? | Why |
|---|---|---|
| close-a (RETROSPECTIVE.md exists, non-empty) | no | measurement-adjacent scaffolding, unconditional |
| close-b (LEARNINGS.md / staging / noop note) | no | out of scope — `assert_learnings_appended_or_noop` untouched |
| close-c (doc/roadmap/RETROSPECTIVE in squash diff) | no | unconditional deliverable-presence check |
| close-d (verdict frontmatter well-formed) | no | unconditional; the flag reads this field, doesn't gate it |
| close-e (`## Cost analysis` heading) | yes, AND `verdict==met` | reflective prose; on-plan `met` closes skip it |
| close-f (`### Failure-class breakdown` heading) | yes, AND failures present | reflective prose; on-plan gates skip it even with a transient failed attempt |
| close-h (terminal flips fire on verdict=met) | no | post-pass state flip, not prose |
| close-i (LEARNINGS.md untouched under `auto`) | no | out of scope, per Do-not-touch |
| close-k (CHANGELOG entry for contract changes) | no | unconditional consumer-contract obligation |
| close-m (FOLLOW-UPS.md on verdict=not_met) | no | unconditional not_met obligation |
| close-l (GATE-NN-CRITERIA.md well-formed) | no | unconditional oracle-state bookkeeping |
| close-n (feature_oracle verdict line in Measurements) | no | Measurements is evidence, always required |
| close-intermediate-a (`## Gate N` heading) | no | structural container, not reflective prose itself |
| close-intermediate-b (LEARNINGS obligation) | no | mirrors close-b, out of scope |
| close-intermediate-c (doc/roadmap diff) | no | mirrors close-c, unconditional |
| close-intermediate-d (`### Failure-class breakdown`) | yes, AND failures present | same rule as close-f, shared `enforced_by` |
| close-intermediate-e (LEARNINGS untouched under `auto`) | no | mirrors close-i, out of scope |
| close-intermediate-f (GATE-NN-CRITERIA.md well-formed) | no | mirrors close-l, unconditional |
| plan-next-a (GATE-(N+1)-REVIEW.md exists) | no | different WU type, untouched by this unit |
| plan-next-b (next gate drafted or terminal) | no | different WU type, untouched by this unit |

`lint_closing.py`'s `ClosingContext.off_plan()` mirrors the same flag so the
arm-time predictive check (`specfuse lint --closing`) never diverges from the
post-squash guard.
