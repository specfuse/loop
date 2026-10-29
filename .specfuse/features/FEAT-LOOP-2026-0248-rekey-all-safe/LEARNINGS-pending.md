<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-LOOP-2026-0248

`autonomy_default: auto`, so `FEAT-LOOP-2026-0248/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly. These are staged for the operator to **promote,
narrow, or reject** at PR review.

---

- **[FEAT-LOOP-2026-0248/G1-CLOSE] Rehearse a unit's real command before prescribing its
  scope.** T05 was planned with a prose scope that nobody had run; two operator
  rehearsals then showed it rewrote fixtures and vendored files, and T05 blocked three
  times before it passed, adding T06–T08. When a unit's acceptance is "this command exits
  zero on the real repository", run the command (dry run or rehearsal) at planning time
  and put its observed output in the unit's context.

- **[FEAT-LOOP-2026-0248/G1-CLOSE] A tool that validates a tree must run the tree's own
  code.** The post-apply check ran in the real checkout's process, so a rehearsal was
  judged by modules the rename had not touched (T06). A check of a copy runs in a fresh
  process with that copy on the path.

- **[FEAT-LOOP-2026-0248/G1-CLOSE] The driver's `cumulative_cost_usd` drops attempts
  before a re-arm.** T05 reads $2.37 against $3.41 summed from `attempt_outcome` events.
  Reconcile a close's cost from the events, not the frontmatter.
