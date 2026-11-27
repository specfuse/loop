<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-LOOP-2026-0252

`autonomy_default: auto`, so `FEAT-LOOP-2026-0252/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`). Two entries
generalize.

## Entries

- [FEAT-LOOP-2026-0252/G1-CLOSE] **A position remembered in a tracked file is not valid
  across a branch checkout.** "What this run wrote" was read as everything in `events.jsonl`
  after the byte size taken at the start of `run()`. `run()` can then switch to the feature
  branch, which holds a different log, so older lines counted as new ones and new ones were
  skipped. The test for "earlier runs are not read" kept one file for the whole run. When a
  unit reads "only what this run wrote", list what can replace the file between the two
  reads (checkout, reset, merge), and test at least one of them.
- [FEAT-LOOP-2026-0252/G1-CLOSE] **Show that a regression test fails with the old code
  put back.** For #3626 the re-close restored the byte-offset reader in a temporary copy
  and ran the new real-checkout tests there: both failed, with the same two wrong stop
  reasons the first close had seen. A green run alone would not have shown that the
  fixture's checkout really changed the log. Selecting a run's records by a value each
  record carries (here its timestamp) held across the checkout, but it relies on the
  clock, so state that limit.
