---
id: FEAT-LOOP-2026-0253/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - specfuse/loop/loop.py
  - tests/test_gate_parallel_cache.py
produces_driver_helper:
  - verify
  - gate_cache_key
model: sonnet
effort: medium
gate_set: code
driver_version: 0.33.2
started_at: 2026-11-27T04:45:59.033809+00:00
duration_seconds: 171.545
cost_usd: 0.535849
input_tokens: 20
output_tokens: 15510
---

# T03 — reuse a passing gate whose declared inputs are unchanged

**Objective.** Turn Definition-of-done clauses 5, 6 and 7 green.

**Context.** `FEAT-LOOP-2026-0253/T03`; decisions 4 and 5 in `PLAN.md`.

- `gate_cache_key(gate)` in `specfuse/loop/loop.py`: SHA-256 over the gate's command and the
  sorted (path, file mode, content digest) of every file `git ls-files -z --cached --others
  --exclude-standard -- <inputs...>` lists that exists on disk. A gate without `inputs:` has no
  key.
- Store only a PASS, keyed by gate name, in `<feature>/work/gate-cache.json`.
- `_run_gate_set()` takes the cache as an explicit argument that only the per-attempt run in
  `verify()` passes. The broad run (`run_gate_broad_set`), the baseline probe
  (`probe_baseline`) and every other caller pass none. Even in `verify()`, the
  `feature_oracle` and any gate named in another gate's `needs:` are never served from cache.
- A reused result has `ok: True`, report `### <name>: PASS (cached)`, `duration_seconds: 0`
  and `cached: True`; `build_attempt_gate_events` copies `cached` into the `gate_result`
  payload (and `driver-event.schema.json` needs no change if the payload is open; check).

**Acceptance criteria.**

1. `tests.test_gate_parallel_cache.TestCacheHit` fails on HEAD and passes after (remove its
   skip). Two `verify()` calls on an unchanged tree: the gate's command counter is 1, the second
   report reads `PASS (cached)`, and its `gate_result` event has `cached: true` and
   `duration_seconds: 0`.
2. `TestCacheMiss` passes: each of editing, adding and deleting a matching file, `chmod +x` on
   one, and changing the command makes the counter 2. A failing gate run twice counts 2. A gate
   with no `inputs:` counts 2.
3. `TestNeverForAVerdict` passes: with a stored PASS, `run_gate_broad_set`, `probe_baseline`,
   the `feature_oracle` and a gate that another gate `needs` each run their command again.
4. Show the hit test fails with the cache argument removed from `verify()`'s call (state it in
   the RESULT's notes).
5. `python3 -m unittest tests.test_gate_timings tests.test_dispatch_skeleton -b` passes.

**Do not touch.** The scheduler (T01) and the status file (T02), except to pass the cache.
Configuration errors and docs (T04). `covers` / carried criteria.

**Verification.** The narrow tier for `implementation`, plus AC5's command.

**Escalation triggers.** If any path that writes a gate-level or terminal verdict reaches the
cache, block and name the path rather than special-casing it.
