<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-LOOP-2026-0251

`autonomy_default: auto`, so `FEAT-LOOP-2026-0251/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`). Two entries generalize.

## Entries

- [FEAT-LOOP-2026-0251/T01] **A unit that moves a guard earlier must state which refusal wins
  when two apply, for every guard it now runs ahead of.** "Change only when, not what" is
  not satisfiable on its own: moving `produces_not_in_diff` before `verify()` also moved it
  ahead of `files_changed_mismatch`, which changed the recorded outcome for an input both
  guards refuse. List the overtaken guards and the intended precedence in the plan.

- [FEAT-LOOP-2026-0251/T04] **A unit that adds a lint message must run every test module
  that lints, not only the ones its Verification section names.** Existing tests filtered
  lint output on the word "directory"; the new WARN contained it, the narrow tier passed,
  and the gate's broad run went red. The named module (`tests.test_lint_plan`) did not
  exist, so check that each module a unit names can be imported before arming.
