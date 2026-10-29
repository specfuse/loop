# Learnings pending — FEAT-LOOP-2026-0203

- **A walking skeleton's oracle must pin the schema unit's field shapes, not guess
  them; its own fixture config is the first thing the lint unit will reject.**
  `FEAT-LOOP-2026-0203/T01` wrote the end-to-end oracle with a literal
  `deploy_signal: {kind: app-version}` config before `T03` had settled how that
  nested mapping was parsed and linted, and T03 then failed twice on its own
  gate with `test_one_deployment_files_one_finding_per_code` red. Generalizable:
  when a skeleton's fixture embeds a new schema field, the task graph should make
  the schema/lint unit's acceptance criterion name the skeleton's fixture as a
  known-valid input, so the disagreement is caught by the lint unit's own narrow
  tier rather than by the next gate-entry probe's `preexisting_gate_failure`.

  > **Accepted 2026-10-16** — promoted to `.specfuse/LEARNINGS.md` as `[FEAT-LOOP-2026-0203/G1-CLOSE]`.

- **Plan estimates that overshoot real spend 5–10x on every unit teach nothing; a
  budget that never binds is not evidence the plan was well sized.** Across five
  units this feature spent $2.63 against $14.50 planned, with every unit under
  plan by 63–90%. The spread, not the total, is the signal; `planned_cost_usd`
  for single-file, test-first monitoring units of this shape can be set near
  $1, which keeps the arm predicate's budget class meaningful.

  > **Rejected 2026-10-16** — `LEARNINGS.md` already carries the cost-estimation rules
  > (`[FEAT-LOOP-2026-0039/G2-CLOSE]` and others); one feature's under-spend adds a data point,
  > not a rule, and the "near $1" figure is specific to this feature's unit shape.

- **A feature's roadmap row and detail section must be flipped to `active` in the
  same commit as `PLAN.md`'s `status: active`.** The first gate-entry probe failed
  `roadmap-link-gate` on `roadmap.md:1089` — drafting left `**Status: planned.**`
  under a plan that was already active — and the driver attributed that to T01 and
  escalated `preexisting_gate_failure`. Arm-time lint over the roadmap for the
  feature being armed would catch this before the first dispatch.

  > **Not promoted 2026-10-16** — filed as specfuse/loop#3483 instead: an arm-time check
  > enforces this, where a lesson only reminds the next author.
