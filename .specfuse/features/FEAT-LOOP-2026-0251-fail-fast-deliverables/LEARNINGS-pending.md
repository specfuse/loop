<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-LOOP-2026-0251

`autonomy_default: auto`, so `FEAT-LOOP-2026-0251/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`). Three entries generalize.

## Entries

- [FEAT-LOOP-2026-0251/T01] **A unit that moves a guard earlier must state which refusal wins
  when two apply, for every check it now runs ahead of.** Moving `produces_not_in_diff`
  before `verify()` also moved it ahead of `files_changed_mismatch`, the blocked-verdict
  check, the smoke-import check and the closing-deliverable guards. The plan named none. The
  amendment after the first close named one, and the re-close failed on the others. List
  every overtaken check, probe each one early against late, and put the whole list in one
  follow-up; a "read in the code" aside does not reach the operator's decision. Prefer one general rule
  over a list of named exceptions: here a list cost a second re-close. Also name what else the
  order changes besides the label, such as whether the tree is kept or reset.

- [FEAT-LOOP-2026-0251/T04] **A unit that adds a lint message must run every test module
  that lints, not only the ones its Verification section names.** Existing tests filtered
  lint output on the word "directory"; the new WARN contained it, the narrow tier passed,
  and the gate's broad run went red. The named module (`tests.test_lint_plan`) did not
  exist, so check that each module a unit names can be imported before arming.

- [FEAT-LOOP-2026-0251/T03] **A "what this attempt changed" list cannot be a filter over a
  name-only diff.** On a kept tree it missed deletes and reverts, which leave the diff, and
  after that fix it still missed a renamed file's old name (rename detection), later edits
  to a non-ASCII name (git quotes it, so the file cannot be opened) and mode changes.
  Compare attempt-start and attempt-end states over the union of their paths, read with
  `--no-renames -z`. Test write, edit, delete, revert, rename and a non-ASCII name on a
  second attempt, and probe the whole matrix before the first fix, not one case per close.
