---
id: FEAT-2026-0106/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces_driver_helper:
  - reflection_required
produces:
  - tests/test_conditional_reflection.py
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
