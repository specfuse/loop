---
feature_id: FEAT-LOOP-2026-0253
title: Run independent verification gates in parallel, and reuse a passing gate whose inputs are unchanged
slug: gate-parallel-cache
branch: feat/FEAT-LOOP-2026-0253-gate-parallel-cache
roadmap_goal: A project can opt in to running gates whose `needs:` are met concurrently (`defaults.max_parallel`) and to reusing a gate's earlier PASS on a retry when the files it declares as `inputs:` are unchanged, without changing any verdict the gate's fresh broad run or a close reads.
autonomy_default: auto
status: done
planned_cost_usd: 15.00
---

# Plan: Run independent verification gates in parallel, and reuse a passing gate whose inputs are unchanged

`_run_gate_set()` runs a gate set one command at a time (`for gate in gate_set:`), and a retry
runs the whole set again, including gates whose inputs the retry did not touch. An operator
report measured 48 of 184 attempts retried, each paying the full set (12 independent
commands in that project). FEAT-LOOP-2026-0250 now records each gate's duration, so the cost
is measurable.

This feature adds two opt-in mechanisms: concurrent gates within the order `needs:` already
defines, and a per-gate result cache keyed by the gate's command and the content of the
files it declares as inputs.

## Decisions (2026-11-27)

The operator asked for the remaining internal ideas to be handled "taking your
recommendations". No interview was run; each item is the drafter's recommendation, applied on
that instruction, and is recorded here as an assumption for review.

1. **Both asks, one gate.** Parallelism and the cache share `_run_gate_set()`; four
   substantive units and a terminal `close` (`docs/methodology.md` §6).
2. **Both off by default.** `defaults.max_parallel` (integer ≥ 1, default 1) in
   `verification.yml`; 1 is today's order exactly. A gate is cacheable only when it declares
   `inputs:` (a list of git pathspec globs); no `inputs:` means never cached. A whole-tree
   oracle simply declares none, which is the opt-out the issue asks for.
3. **Parallel within `needs:`.** A gate starts only once every gate it `needs` has finished
   and passed; a failed dependency still makes it `SKIP`. Results are returned in the set's
   declared order whatever the finishing order, so reports, failure signatures and
   `gate_result` events read as today.
4. **The cache never feeds a gate-level or terminal verdict.** Only the per-attempt run inside
   `verify()` may reuse a result. The gate's broad run, the baseline probe and any run a close
   or judge reads always run every gate fresh. The `feature_oracle` and any gate another gate
   `needs` (its dependents may reuse its artifacts, which a cached result did not produce) are
   never served from cache.
5. **Cache key.** SHA-256 over the gate's command string and the sorted (path, file mode,
   content digest) of every tracked or untracked, non-ignored file matching its `inputs:`.
   Only a PASS is stored, in `<feature>/work/gate-cache.json` (gitignored). A reused result is
   reported `PASS (cached)` and its `gate_result` event carries `cached: true` and
   `duration_seconds: 0`.
6. **Autonomy `auto`.** A fresh judge writes the terminal verdict from evidence only.
   `loop.py` and the `verification.yml` examples are judge surfaces, so the terminal
   judge-editing stop fires before the close: acknowledge it with your own reason and
   `/unblock-wu`.

**Out of scope:** parallel work units (FEAT-LOOP-2026-0105); caching across features or
machines; caching a FAIL; inferring a gate's inputs; changing `scripts/smoke-test.sh` or CI.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -n "needs\|covers\|carried\|max_parallel\|cache" specfuse/loop/loop.py`;
  `sed -n '/PER-GATE `needs:`/,/FEAT-2026-0102/p' .specfuse/verification.yml.example`.
- **Verdict:** extend. `needs:` ordering (`order_gate_set`, FEAT-2026-0102) and its
  configuration-error path are reused for the parallel schedule and for refusing bad
  `max_parallel` / `inputs:` values. `covers` / `carried_from_attempt` carry a close's
  per-criterion greens (FEAT-2026-0117); they are not gate results and are not changed. The
  `broad_run` tree identity in `GATE-NN.md` dedups the broad run only; no gate result is
  reused anywhere today.
- **If reusing:** `verification.yml.example` already states that the `needs:` artifact
  guarantee "is never cached across attempts"; decision 4 keeps that true.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — no check changes severity.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-LOOP-2026-0253/T01
        file: WU-01-parallel-gate-runner.md
        depends_on: []
      - id: FEAT-LOOP-2026-0253/T02
        file: WU-02-parallel-safety.md
        depends_on: [FEAT-LOOP-2026-0253/T01]
      - id: FEAT-LOOP-2026-0253/T03
        file: WU-03-gate-result-cache.md
        depends_on: [FEAT-LOOP-2026-0253/T01]
      - id: FEAT-LOOP-2026-0253/T04
        file: WU-04-config-validation-and-docs.md
        depends_on: [FEAT-LOOP-2026-0253/T02, FEAT-LOOP-2026-0253/T03]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-LOOP-2026-0253/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-LOOP-2026-0253/T01, FEAT-LOOP-2026-0253/T02, FEAT-LOOP-2026-0253/T03, FEAT-LOOP-2026-0253/T04]
```

## Post-merge checklist

- In a project with several independent gates, set `defaults.max_parallel: 4` and compare
  one attempt's `gate_result` durations and the attempt's `verify_seconds` with a run at 1.
- In a project with per-package test gates, declare `inputs:` on one gate, force a retry that
  touches another package, and confirm the gate reports `PASS (cached)` on the retry and runs
  fresh in the gate's broad run.

## Notes

- LEARNINGS `[FEAT-LOOP-2026-0251/T04]`: a unit that changes driver output runs every test
  module that matches driver output text, not only its own.
- LEARNINGS `[FEAT-LOOP-2026-0250/T04]`: a unit that edits `docs/*.md` refreshes its packaged
  copy under `specfuse/loop/data/docs/` in the same unit (`scripts/sync-scaffold.sh`).
- LEARNINGS `[FEAT-LOOP-2026-0252/G1-CLOSE]`: a regression test is shown to fail with the old
  code put back; a "this run only" selection lists what can replace the file between reads.
- `produces:` lists only `.py` files under `tests/` (#3539).
- The definition of done is stated as checkable facts (FEAT-LOOP-2026-0251 took seven closes
  on loose wording). A unit that finds a clause ambiguous blocks and names it.
