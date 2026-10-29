<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-LOOP-2026-0246

`autonomy_default: auto`, so `FEAT-LOOP-2026-0246/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`). These two
are staged for the operator to **promote, narrow, or reject** at PR review.

---

- **[FEAT-LOOP-2026-0246/G1-CLOSE] A test helper that patches module globals once per call
  must restore them in reverse order, or from a saved original.** The oracle's
  `_stub_agent()` ran once per autonomy level and `tearDown` undid `self._patches` in
  forward order, so the last `setattr` left `loop.verify` stubbed for the rest of the
  process. Every unit's narrow tier passed; the broad run failed twice on 14 tests in
  three modules outside every unit's `produces:`. When a test class patches the same
  attribute more than once, restore in reverse, and run it in one process with the
  neighbouring modules that read that attribute before calling the unit done.

- **[FEAT-LOOP-2026-0246/G1-CLOSE] Follow an operator instruction in a halt brief
  literally before shipping it.** The first `judge_editing_terminal` brief said to
  list "the paths" in `judge_edit_acknowledged`, but a `produces_driver_helper` hit is
  covered only by the literal key `produces_driver_helper`, so an operator who listed
  file paths would have re-fired the stop. The unit tests asserted the brief's six
  parts, not that its advice clears the stop. For any halt that tells a person what to
  write, add a test that takes the brief's own example and checks the stop clears.
