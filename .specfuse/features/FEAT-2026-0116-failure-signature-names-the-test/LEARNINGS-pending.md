# LEARNINGS-pending

**What this file is.** This feature runs under `autonomy_default: auto` — a
closing WU here dispatches without a human reading the gate first. Under
`review` or `supervised`, a promoted lesson lands straight in the repo's
`.specfuse/LEARNINGS.md`, because a human already reviewed the gate that
produced it. Under `auto` nobody did, so the lesson stages here instead. A
closing WU's own post-pass check refuses to pass if its diff touches
`.specfuse/LEARNINGS.md` while this feature is in `auto` mode.

**How a human promotes an entry from here.** At PR review for this feature:
read each entry, judge whether it generalizes into a rule that should change
how a future work unit is written or executed, and copy accepted entries into
`.specfuse/LEARNINGS.md` below its append marker. Leave rejected or narrowed
entries here with a short note on why.

## Entries

<!-- closing work units append below this line -->

- [FEAT-2026-0116/G1-CLOSE] **Recurrence, not a new lesson: the
  `_gate_number_from_wu_id` / `summarize_attempt_failure_classes` gate-scope
  bug (`[FEAT-2026-0016/G3-CLOSE]`, confirmed again at
  `[FEAT-2026-0101/G1-CLOSE]`) is still open, and it silently starves this
  close's own pre-created skeleton, not just the `close-f` guard.**
  `_gate_number_from_wu_id` only parses closing-WU IDs (`G\d+-…`); every
  substantive WU in this repo is named `T01`, `T02`, … and resolves to
  `None`. `summarize_attempt_failure_classes(feature_dir, gate_n, …)` filters
  each `attempt_outcome` event's own correlation_id through that same
  parser, so a `gate_n`-scoped call drops every implementation-WU event and
  returns the `(no non-passing attempts in scope)` sentinel even when one
  genuinely failed. Measured fresh in this session on two trees: this
  feature's own `FEAT-2026-0116/T01` failed its attempt 1 (`ERROR:
  test_failure_signature_names_the_test`, a real red-before-green), and
  `FEAT-2026-0115/T02` failed twice — in both cases
  `summarize_attempt_failure_classes(feature_dir, gate_n=1, …)` returns the
  empty sentinel, while the unscoped call (`gate_n=None`) correctly surfaces
  the failures. This close's own generic RETROSPECTIVE.md skeleton
  (`precreate_dispatch_skeleton` → `_precreate_retrospective_stub`) calls the
  same scoped helper before dispatch, at gate `1` again returning the
  sentinel, so the skeleton wrote nothing — this close authored
  `RETROSPECTIVE.md` from a blank file rather than a pre-seeded one, which is
  why this feature's closing session could not "fill in a skeleton" the way
  `close-discipline.md` §4 describes. Two promoted write-ups already name the
  parser gap and its effect on `close-f`; neither one has led to a fix in the
  four features since (`0016` → `0101` → `0115` → `0116`, all single-gate,
  all named `T01`/`T02`/…). Authoring/ops rule, restated because restating it
  has not been enough: `_gate_number_from_wu_id` needs a second resolution
  path — reading `PLAN.md`'s task graph to map a `TNN` id to its gate — before
  any `gate_n`-scoped caller (there are three: `lint_closing.py`'s
  `failures_present()`, `loop.py`'s `assert_failure_class_breakdown_when_failures_present`,
  and `_precreate_retrospective_stub`) can be trusted on a real feature. A
  fourth recurrence is itself evidence the fix belongs on a backlog with
  priority, not in another retrospective paragraph.
