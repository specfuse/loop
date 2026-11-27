---
id: FEAT-LOOP-2026-0253/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - specfuse/loop/loop.py
  - .specfuse/verification.yml.example
  - specfuse/loop/data/verification.yml.example
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
  - tests/test_gate_parallel_cache.py
produces_driver_helper:
  - order_gate_set
model: sonnet
effort: medium
gate_set: code
driver_version: 0.33.2
started_at: 2026-11-27T04:48:50.873223+00:00
duration_seconds: 136.838
cost_usd: 0.370864
input_tokens: 20
output_tokens: 6699
---

# T04 — refuse bad `max_parallel` and `inputs:` values, and document both

**Objective.** Turn Definition-of-done clause 8 green and document the feature.

**Context.** `FEAT-LOOP-2026-0253/T04`; decision 2 in `PLAN.md`.

- In `specfuse/loop/loop.py`, refuse a `defaults.max_parallel` that is not an integer ≥ 1 and a
  gate `inputs:` that is not a list of non-empty strings with the same `ValueError` →
  `CONFIGURATION ERROR` path `order_gate_set` uses for an unknown `needs:` target.
- Document `defaults.max_parallel` and per-gate `inputs:` in `.specfuse/verification.yml.example`
  and `specfuse/loop/data/verification.yml.example`, next to `needs:`, including that the cache
  never serves the broad run, the baseline, the `feature_oracle` or a gate another gate needs.
- Add a paragraph to `docs/methodology.md` where it describes the per-attempt verify, and
  refresh `specfuse/loop/data/docs/methodology.md` with `scripts/sync-scaffold.sh`.

**Acceptance criteria.**

1. `tests.test_gate_parallel_cache.TestConfigurationErrors` fails on HEAD and passes after
   (remove its skip): `max_parallel` of `0`, `-1`, `"2"` and `1.5`, and `inputs:` of `"src/"`,
   `[]`, `[""]` and `[3]` each return a `CONFIGURATION ERROR` from `verify()` with no gate
   command run.
2. `tests.test_gate_parallel_cache` has no `unittest.skip` left.
3. `python3 -m unittest tests.test_gate_timings tests.test_run_progress -b` passes, and
   `scripts/sync-scaffold.sh` leaves no diff between `docs/methodology.md` and its packaged copy.

**Do not touch.** The scheduler (T01), the status file (T02), the cache (T03), apart from
calling the validation. `scripts/smoke-test.sh` and CI.

**Verification.** The narrow tier for `implementation`, plus AC3's command.

**Escalation triggers.** If `scripts/smoke-test.sh` or CI reads `max_parallel` or `inputs:` in a
way that would now disagree with the driver, block rather than changing them.
