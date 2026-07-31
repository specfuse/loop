---
id: FEAT-2026-0062/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces:
  - specfuse/loop/cost.py
  - tests/test_cost_lifetime.py
produces_driver_helper:
  - wu_lifetime_cost_usd
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-07-31T18:27:44.929695+00:00
duration_seconds: 829.591
cost_usd: 1.59496
input_tokens: 66
output_tokens: 15079
---

# One lifetime-cost reader: events first, frontmatter fallback

**Objective.** Ship `specfuse/loop/cost.py` with a single function that answers
"what has this work unit cost over its whole life" correctly on every re-arm shape
in the corpus, without double-counting and without returning a false zero.

**Context.** Correlation ID `FEAT-2026-0062/T01`. Read `PLAN.md` first — it records
the two re-arm shapes, the measured $5.01 under-read, and why an events-only read
and a shape-aware frontmatter read were both rejected. Do not reopen those
decisions.

**Why this module and not an existing one.** `arm_eval.py`'s module docstring states
the dependency runs `loop.py → arm_eval`; `arm_eval` must not import `loop`. Both
consumers need this function, so it lives in a third module that neither owns.
`cost.py` must not import `loop.py` or `arm_eval.py`.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The contract

`wu_lifetime_cost_usd(wu_path, events_path)` returns a float.

1. **Events first.** Sum `payload.cost_usd` across every `attempt_outcome` event in
   `events_path` whose correlation ID identifies this work unit. This is
   shape-independent: it needs no knowledge of folds, cumulative fields, or re-arm
   history.
2. **Fallback only when the work unit has no `attempt_outcome` events at all.** Then
   return `cost_usd + cumulative_cost_usd` from frontmatter — today's behaviour, so
   the fallback is never worse than the current code.
3. **Never both.** A work unit with events must not also add frontmatter, and a work
   unit without events must not return 0.0 because the event file was empty or
   missing.

**The trap, stated so it is not rediscovered.** On the fold-ran shape
`cumulative_cost_usd` and `re_arm_history[].prior_cost_usd` are the same money.
Nothing in this function may add `prior_cost_usd` to `cumulative_cost_usd` — that
double-counts $0.47 on `FEAT-2026-0020/WU-02` and $5.26 on `FEAT-2026-0069/WU-03`.
The events path avoids the question entirely; the fallback path must not
reintroduce it.

Missing file, unreadable line, absent field, and a `bool` where a number is expected
all contribute 0.0 rather than raising — this function is called from a brake, and a
brake that crashes is a brake that does not brake.

**Acceptance criteria.**

1. `tests/test_cost_lifetime.py::TestLifetimeCost::test_fold_never_ran_wu_reads_full_lifetime`
   exists and **fails on HEAD before this WU runs** (`specfuse/loop/cost.py` does not
   exist, which counts as red).
2. That test asserts a `FEAT-2026-0053/WU-07`-shaped fixture — `cost_usd: 4.281823`,
   no `cumulative_cost_usd`, `re_arm_history[].prior_cost_usd: 5.01`, with five
   `attempt_outcome` events summing 9.29 — returns **9.29** (± 0.01), and it passes
   after this WU's edits.
3. A test asserts the fold-ran shape does **not** double-count: a fixture with
   `cost_usd`, a `cumulative_cost_usd` equal to its single
   `re_arm_history[].prior_cost_usd`, and matching events returns the events sum,
   not the sum plus either frontmatter field.
4. A test asserts a work unit with **no** `attempt_outcome` events falls back to
   `cost_usd + cumulative_cost_usd`, and a separate test asserts it does **not**
   return 0.0 in that case.
5. A test asserts a missing `events.jsonl` takes the fallback path rather than
   raising.
6. A test asserts a never-re-armed work unit (no cumulative, no history) returns
   exactly its `cost_usd` — the satisfiability guarantee from `PLAN.md`, held as a
   test rather than a claim.
7. Malformed input contributes 0.0 without raising: an unparseable JSONL line, an
   `attempt_outcome` with no `cost_usd`, and a `cost_usd` that is a bool. One test
   each.
8. `specfuse/loop/cost.py` imports neither `loop.py` nor `arm_eval.py`. Assert with
   `grep -n "^from \.\|^import \|^from specfuse" specfuse/loop/cost.py` and quote the
   output in the result.
9. **Fallback blast radius measured, not assumed.** Run the helper across all 44
   feature folders and record in the result: how many work units take the events
   path, how many take the fallback, and how many of the fallback set are
   fold-never-ran (frontmatter carries `re_arm_history` but no
   `cumulative_cost_usd`). That last number is the residual under-read this design
   knowingly accepts; if it is not zero, name the work units.
10. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**Do not touch.** `specfuse/loop/arm_eval.py` and `specfuse/loop/loop.py` — T02 wires
the consumers; this WU only creates the reader. `fold_cumulative_on_rearm` and
`detect_rearm_dispatch` — the fold divergence is explicitly out of scope per
`PLAN.md`, and changing what gets *written* is a different feature. Generated
directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus the scoped red/green run in
criteria 1–2 and the corpus measurement in criterion 9.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
red test in criterion 1 cannot be made to fail for the stated reason; correlating an
`attempt_outcome` event to its work unit is ambiguous — the events carry a
correlation ID whose exact shape must be read from real `events.jsonl`, not assumed,
and if two work units cannot be distinguished the whole events path is unsound and
that is a design problem, not an implementation one; or the corpus measurement in
criterion 9 shows the fallback taken by a majority of work units, which would mean
the events path is far less load-bearing than `PLAN.md` assumes and the design
should be revisited before wiring anything to it. If `specfuse/loop/cost.py` is
absent from the files you edited, emit `status: blocked` — do not claim complete.
