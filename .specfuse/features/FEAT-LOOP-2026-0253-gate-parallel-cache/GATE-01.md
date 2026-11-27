---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_gate_parallel_cache -v -b"
cost_budget_usd: 19.00
---

# Gate 1 — independent gates can run concurrently, and an unchanged passing gate can be reused on a retry

## Definition of done

**Stated as an outcome.** In temporary repositories and feature folders, with stub gate
commands that record when they start and end:

1. **Default unchanged.** With no `defaults.max_parallel` (or `1`) and no gate declaring
   `inputs:`, `_run_gate_set()` starts each gate only after the previous one has ended, in
   `order_gate_set` order, and returns the same results (names, `ok`, `skipped`, report text
   apart from durations) as before this feature for a set mixing passing, failing and
   dependency-skipped gates.
2. **Parallel.** With `defaults.max_parallel: N`, at most N gate commands run at any moment;
   with N ≥ 2, two gates with no `needs:` edge between them overlap in time (each stub sleeps
   long enough that the recorded intervals overlap). A gate never starts before every gate it
   `needs` has ended; a gate whose dependency failed is `SKIP`, never run.
3. **Order of results.** Whatever the finishing order, the returned results, the joined
   report, the attempt's failure signature and its `gate_result` events are in the set's
   declared order.
4. **Parallel safety.** A gate that exceeds `GATE_TIMEOUT_SECONDS` (patched short in the test)
   is killed with its process group and reported as a timeout while the other gates finish
   normally. Each gate's `gate_started` and `gate_finished` event is written once, and
   `events.jsonl` holds only whole lines. While gates run in parallel, `STATUS.json` has `phase:
   gate`, `gate` set to one running gate's name, and `gates_running` listing every running
   gate.
5. **Cache hit.** A gate declaring `inputs:` that passed in an earlier attempt of the same
   unit, whose command and matching files (path, mode, content) are unchanged, is not run in
   the per-attempt `verify()`: its report reads `PASS (cached)` and its `gate_result` event has
   `cached: true` and `duration_seconds: 0`.
6. **Cache miss.** Changing, adding or deleting a file matching `inputs:`, changing a matched
   file's mode, or changing the gate's command runs it fresh. A gate that failed is never
   stored. A gate with no `inputs:` is never served from cache.
7. **Never for a verdict.** The gate's broad run, the baseline probe and the `feature_oracle`
   always run every gate fresh, cache or not, and so does any gate named in another gate's
   `needs:`.
8. **Configuration errors.** A `max_parallel` that is not an integer ≥ 1, or an `inputs:` that
   is not a list of non-empty strings, is refused as a CONFIGURATION ERROR before any gate
   runs, the way an unknown `needs:` target is.
9. **Nothing else changes.** Every existing test passes unchanged, apart from edits forced by
   moving the loop into a scheduler or by new report text a text-matching assertion picks up;
   no such edit removes or weakens an assertion, and each is named in the close.

The `feature_oracle` proves 1–8. It is red on the current tree; `FEAT-LOOP-2026-0253/T01` is the
walking skeleton that creates `tests/test_gate_parallel_cache.py` and turns clauses 1–3 green,
with the other classes `unittest.skip` naming their owner (T02–T04). A skip surviving to the
close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Overlap is measured, not assumed.** Concurrency is asserted from intervals each stub
  records, never from total wall time.
- **Positive controls.** Clause 5 pairs every hit with the miss in clause 6 that differs by one
  input; clause 2 pairs N = 2 with N = 1.
- **The verdict path stays fresh.** Clause 7 is asserted by a counter on each gate command, not
  by reading reports.
- **No reading chosen silently.** A unit that finds a clause ambiguous blocks and names it.
- **Expected self-halt.** `loop.py` and the `verification.yml` examples are judge surfaces;
  acknowledge the stop with your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
