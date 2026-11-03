<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-LOOP-2026-0249

`autonomy_default: auto`, so `FEAT-LOOP-2026-0249/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`). Nothing generalizes
beyond what the plan already cites: the feature's two borrowed lessons
(`[FEAT-LOOP-2026-0058/G1-CLOSE]`, `[FEAT-LOOP-2026-0023/G1-CLOSE]`) both held, so the close
staged no new entry. The entry below was added by the operator's session at wrap, after the close.

## Entries

- [FEAT-LOOP-2026-0249/T01] **A unit that gives a function its first production caller must
  drop that function from the caller-check ratchet's `BASELINE` in the same unit.** T01 made
  `append_entry` a real caller target, which shrank the baseline, and
  `test_the_baseline_has_not_silently_shrunk` went red. Its narrow tier did not select that
  repo-wide test, so T01 passed and the failure surfaced at T06's baseline probe, attributed to
  T06, as a `preexisting_gate_failure` halt that needed a human. Rule: when a unit wires up
  previously uncalled code, name the ratchet update in its acceptance and run
  `tests.test_caller_check_ratchet` in its verification; a green narrow tier does not cover
  repo-wide ratchets.
