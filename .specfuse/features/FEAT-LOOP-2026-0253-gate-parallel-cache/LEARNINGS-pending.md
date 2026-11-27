<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-LOOP-2026-0253

`autonomy_default: auto`, so `FEAT-LOOP-2026-0253/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`). Two entries
generalize.

## Entries

- [FEAT-LOOP-2026-0253/G1-CLOSE] **A cache keyed on a selection needs a rule for the empty
  selection.** The gate cache hashes the command and the files its `inputs:` pathspecs
  match. A pathspec that matches nothing (a typo) leaves only the command in the key, so
  one `PASS` is reused across every later edit. Every listed miss case (edit, add, delete,
  mode, command) started from a pathspec that matched, so all passed. The implementing
  unit noted the gap in its RESULT, and no later unit's criteria picked it up. When a unit
  keys, filters or narrows on a user-written pattern, give "matches nothing" its own
  acceptance criterion.
- [FEAT-LOOP-2026-0253/G1-CLOSE] **Prove "the default is unchanged" by running the old
  code beside the new.** The oracle compared the new default run with expected values
  written by the same feature. The driver's pinned build from before the feature was still
  on disk, so the close ran one script on both and compared the normalized outputs byte
  for byte. The same copy also showed which new tests were red without the feature. A
  close of a driver feature can use the first pin in `events.jsonl`
  (`driver_build_pinned`) this way while that directory exists.
