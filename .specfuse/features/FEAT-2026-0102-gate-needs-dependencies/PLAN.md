---
feature_id: FEAT-2026-0102
title: Gate dependencies — a gate declares `needs:` so shared work runs once per pass
slug: gate-needs-dependencies
branch: feat/FEAT-2026-0102-gate-needs-dependencies
roadmap_goal: A gate set is a dependency graph rather than a flat list — a gate declaring `needs: [tests]` runs after its dependency, may reuse its artifacts, and is skipped when it fails — so a test-derived coverage gate stops re-executing the suite, while `failure_class` and `failure_signature` stay distinguishable per gate.
autonomy_default: review
status: active
planned_cost_usd: 29.00
---

# Plan: Gate dependencies

A gate set is a list of independent shell commands, and the loop gives an
author no way to say *"this gate's work is already done by that one."* In any
project whose `coverage` gate is "run the suite, then report coverage", the
suite therefore runs twice per gate pass. This repo measured it at gate entry:
118s of wall clock across the `code` set, **93% of it duplicated test
execution** ([FEAT-2026-0051/G1-CLOSE]). `specfuse-generator` measured the same
shape at 5:10 of a ~11-minute pass, on 4303 tests
(specfuse/specfuse#162, clabonte/generator#1713).

The duplication is not a misconfiguration. It falls out of the gate-set
contract and its authoring rule — *gate commands are self-contained*, with
`clean` included so stale artifacts cannot make a gate falsely pass. That rule
is sound; the gap is that the contract offers no third option between paying
for the duplicate run and dropping the guarantee. The two obvious workarounds
each give something up: merging `tests` and `coverage` collapses two
`failure_class` values into one, which spinning detection
(`spinning_signature_repeat`) and `learnings-suggest` both key on; dropping
`clean` from `coverage` reintroduces exactly the false pass the rule forbids.

This feature adds the third option. A gate may declare `needs: [<gate>]`. The
runner orders the set topologically, and the declaring gate may reuse its
dependency's artifacts **because the runner guarantees the dependency ran, in
this same invocation, in this same working tree**. The staleness discipline
moves from a per-command convention to a runner invariant — the same guarantee,
enforced once instead of re-asserted in every command string. A gate whose
dependency failed is skipped, never passed.

## Scope boundary

**IN.** `needs:` support in `_run_gate_set` (`loop.py`), matching dependency
ordering in `gate_commands.py` so the driver and CI agree, this repo's own
`verification.yml` flipped onto it, and the authoring rule reworded in the
canonical `plugins/` copy of the verification skill.

**OUT, deliberately.**

- **Tiered per-attempt vs per-gate gate sets.** Running a cheap subset per
  attempt and the full suite once per gate is FEAT-2026-0109. Its per-attempt
  tier also wants FEAT-2026-0101's `feature_oracle`, which does not exist yet.
- **Caching the baseline probe by tree hash.** Also FEAT-2026-0109.
- **Running the driver from an installed copy.** Also FEAT-2026-0109, and it
  is a packaging migration in its own right — [FEAT-2026-0019/G1]'s literal
  scenario, which cost $5.63 and 49 minutes of thrash the last time it was
  attempted inside a dispatched gate.
- **Parallel gate execution.** Artifact reuse across gates forecloses it.
  `mvn clean` already races on `target/`, so it was never available.
- **Per-tool output parsing.** The rejected alternative: one command emitting
  several named verdicts (`emits: [tests, coverage]`) would need the driver to
  split surefire / pytest / jest / jacoco output into per-gate pass-fail. That
  makes the driver toolchain-aware, which it deliberately is not, and grows
  `_SIG_PATTERNS` — already the subject of four bug fixes (#207, #2557, #2885,
  #167) — without bound.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  ```
  grep -rn "needs\b|depends_on|skip.*gate|gate.*skip|subsumes|provides:" specfuse/loop/loop.py
  grep -rln "verification.yml|load_verification|VERIFICATION_PATH" specfuse/ .specfuse/scripts/
  ```
- **Verdict:** `no existing mechanism, building new`. `depends_on` exists only
  for work units (`loop.py:431`, from the PLAN.md graph); there is no
  gate-level dependency, ordering, or skip mechanism. `_run_gate_set`
  (`loop.py:4025`) iterates the set unconditionally, one subprocess per gate.
- **Two findings in favour, one against.** `_miniyaml` already parses
  `needs: [tests]` into `{'needs': ['tests']}` — verified against the real
  parser, so no parser work. `load_verification` (`loop.py:3874`) is a bare
  parse that passes unknown keys through untouched, so the key is inert until
  a consumer reads it. Against: `gate_commands.py` — the CI/smoke derivation
  path (#592) — matches only `- name:` and `command:` by regex and would
  silently ignore `needs:`, running `coverage` over no coverage data while the
  driver ran it correctly. That is the second mandatory site, per
  [FEAT-2026-0002/G1-CLOSE]: enumerate every site that asserts the contract
  and flip them atomically.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

T01 makes an unresolvable `needs:` target and a dependency cycle
CONFIGURATION ERRORs, mirroring the existing unknown-`extra_gates` branch at
`loop.py:4159`.

- **What does the rule report on an input already in its intended final state?**
  Zero. A gate set with no `needs:` key resolves to the declared order and
  reports nothing — every currently shipped `verification.yml`, and every
  target project's, is already in its final state under this rule. A gate set
  whose `needs:` targets all resolve within the effective set (after the
  `extra_gates` union) likewise reports nothing. The predicate fires only on a
  name that does not exist or an edge that cycles, neither of which any correct
  input contains.

## Task graph

```yaml
# Single gate, terminal `close` — 3 planned substantive WUs, under the
# threshold of 8 in `docs/methodology.md` §6 "Ceremony proportionality".
# No close-intermediate, no plan-next.
#
# Order is load-bearing, not merely topological. T01 and T02 land the
# mechanism INERT: nothing declares `needs:` yet, so every gate still runs
# exactly as it does today and each WU is verified by the same oracle it was
# dispatched under. T03 flips this repo's verification.yml, and is last for
# that reason. See [FEAT-2026-0019/G1] in `.specfuse/LEARNINGS.md`.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0102/T01
        file: WU-01-gate-needs-runner.md
        depends_on: []
      - id: FEAT-2026-0102/T02
        file: WU-02-gate-commands-order.md
        depends_on: [FEAT-2026-0102/T01]
      - id: FEAT-2026-0102/T03
        file: WU-03-flip-verification-yml.md
        depends_on: [FEAT-2026-0102/T01, FEAT-2026-0102/T02]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0102/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0102/T01, FEAT-2026-0102/T02, FEAT-2026-0102/T03]
```

## Notes

- **Baseline to beat, measured before this feature.** `[FEAT-2026-0051/G1-CLOSE]`
  recorded the `code` set at **118s** wall clock, **93% of it the same suite run
  bare and again under coverage**, zero model tokens. T03's acceptance re-measures
  against that number. That same lesson concluded the duplication was "a
  `verification.yml` authoring concern rather than a driver one" — this feature
  falsifies the second half, and the close revises the entry.
- **Why `autonomy_default: review`.** Normally the judge is what makes `auto`
  trustworthy. Here the feature changes the gate runner that produces the
  judge's own evidence, so a `needs:` defect would corrupt the evidence bundle
  and the verdict read from it in the same run. One human checkpoint on the one
  close where the oracle itself moved. Note that `judge_editing` does not
  apply: it evaluates the *next* gate's drafted WUs at arm time
  (`arm_eval.py:435-450`) and a single-gate feature never arms one — even
  though this feature's `produces:` set is squarely judge surface
  (`.specfuse/verification.yml`, `specfuse/loop/loop.py`,
  `specfuse/loop/gate_commands.py` are all in `JUDGE_PATHS`).
- **`scripts/smoke-test.sh` needs no edit.** It carries `set -euo pipefail`
  (line 16) and `eval`s each derived gate in sequence, so a failing dependency
  already aborts the run before its dependents. T02 supplies ordering; the skip
  is free. This is why no WU here trips `/authoring-work-units` §11
  (operator-script shellcheck/bats obligations).
- **Skill sync direction.** The authoring rule lives in
  `plugins/specfuse/skills/verification/SKILL.md`, which is canonical; the
  `.specfuse/skills/` copy is generated from it. T03 edits the `plugins/` copy.
  Rules and templates flow the other way (`.specfuse/` → `specfuse/loop/data/`);
  do not generalize one direction to the other.
</content>
</invoke>
