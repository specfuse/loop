<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-LOOP-2026-0224

`autonomy_default: auto`, so `FEAT-LOOP-2026-0224/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`). These two
are staged for the operator to **promote, narrow, or reject** at PR review.

---

- **[FEAT-LOOP-2026-0224/G1-CLOSE] The `judge_editing` arm class cannot fire on a
  single-gate feature, so a plan that expects it to halt has no review gate.** PLAN
  decision 3 expected T01's edit to `arm_eval.py` (a judge module) to trip
  `judge_editing`. It did not: the class reads the *drafted* successor-gate WUs, a
  terminal gate drafts none, and the one `arm_predicate_evaluated` event reported
  `judge_editing: clean — no drafted WU touches judge-path surfaces`. The edit shipped
  with no halt and no review beyond the PR diff. When a single-gate feature must edit
  a judge module, the plan should say the PR review is the only gate, or put the edit
  in a `type: human` unit the operator marks done.

  > **Accepted 2026-10-27** — promoted to `.specfuse/LEARNINGS.md` as `[FEAT-LOOP-2026-0224/G1-CLOSE]`. Remedy updated on promotion: `review` autonomy per #3544; enforcement is FEAT-LOOP-2026-0246.

- **[FEAT-LOOP-2026-0224/G1-CLOSE] A unit that changes a seeded or rendered artifact must
  name every test that asserts the old bytes, not only its own.** T07 changed the
  roadmap template and its seed; every unit passed its narrow tier, and the first broad
  run failed on `test_init_integration.TestInitFullLayout.test_roadmap_seeded_from_template`,
  which compared the seed to the old bytes and sat in no unit's `produces:`. The fix
  was one test, but it cost a failed broad run and a gate returned to `awaiting_review`.
  When the plan edits a template or a seed, grep `tests/` for the artifact's filename
  and list each hit in the unit's `produces:` or its Do-not-touch exceptions.

  > **Accepted 2026-10-27** — promoted to `.specfuse/LEARNINGS.md` as `[FEAT-LOOP-2026-0224/G1-CLOSE]`.
