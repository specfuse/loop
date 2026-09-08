---
feature_id: FEAT-2026-0101
title: Feature oracle and walking skeleton — the gate's definition of done is one end-to-end check
slug: feature-oracle-walking-skeleton
branch: feat/FEAT-2026-0101-feature-oracle-walking-skeleton
roadmap_goal: Every gate declares one `feature_oracle` command in its `GATE-NN.md` — the executable proof of that gate's definition of done — which the driver runs as part of every unit's verification in that gate and again at the close, so the gate's definition of done is the oracle rather than a list of units that each went green.
autonomy_default: review
status: done
planned_cost_usd: 21.50
---

# Plan: Feature oracle and walking skeleton

Per-unit gates verify units. Nothing verifies the feature. FEAT-2026-0050
shipped seven green units connected to nothing and needed FEAT-2026-0082 to
wire them together; nine hedged features across the corpus were green on
fixtures and never given a real ride. Every unit's `done` was honest in all of
them.

The sharpest record of the gap is `[FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question]`:
fifteen oracles re-ran green in one close — three scoped red→green tests, two
symbol imports, a structural config guard, and the full sixteen-entry `code`
gate set at 2325 tests and 93% coverage — **and not one of them could observe
the defect**, because none asserts on the path the feature was supposed to
change. The escalation trigger for "a re-run oracle disagrees with a producing
unit's self-report" correctly did not fire. No oracle disagreed. The definition
of done was still unmet.

This feature adds the missing question. A gate declares one `feature_oracle`
command that exercises the user-visible outcome end to end. The driver runs it
as part of every unit's verification in that gate, and the close re-runs it and
records the result. A gate whose oracle is red is not done, however many units
report `done`.

## Why the oracle lives with the gate and not in `verification.yml`

`verification.yml` answers "did you break anything?" — project-scoped,
identical for every feature and every unit, and required green at all times
(the baseline probe halts a gate that enters red). A feature oracle answers
"does the thing this gate promised actually do it?" It is **required to start
red** — the feature is not built yet — and goes green at the tracer bullet.
Something that is required-red-then-green cannot live in a file whose contract
is always-green without conflating achievement with regression, and it would
leave `verification.yml` accumulating a set per feature that nothing prunes.

So declaration lives with the gate; execution reuses the existing runner. A
shipped oracle is often exactly the end-to-end regression test worth keeping
forever, at which point promoting it into `verification.yml` is a deliberate
act rather than the default.

## Why `GATE-NN.md` and not `PLAN.md`

The oracle proves a *definition of done*, and the DoD section already lives in
`GATE-NN.md`, beside `status`, `baseline:` and `cost_budget_usd` — the gate's
other operational state. It also matches the drafting rhythm: gate 1's oracle
is authored at feature planning, every later gate's by the prior gate's
`plan-next`, which already drafts that gate and never touches a passed one. A
`PLAN.md`-level oracle would have to describe the *final* user-visible outcome
at draft time, for gates not yet designed — which contradicts "detail only as
far as the next gate" — and it would be red for legitimate reasons throughout
gates 1..N-1, making it useless as the per-attempt signal FEAT-2026-0109 wants.

The feature-scoped slot already exists and is prose: `roadmap_goal` in
`PLAN.md` frontmatter, which `plan-next` is already required to anchor every
drafted gate to. Feature intent stays prose there; the per-gate proof is
executable here.

**Known limit, stated rather than faked.** Nothing structurally prevents gate
N's oracle from being weaker than gate N-1's. Asserting subsumption would mean
comparing two shell commands for strength, which is not decidable. T04 handles
it as a `plan-next` review-summary obligation — that summary is already
weighted toward doubt and already carries the roadmap-anchor check — not as a
lint rule pretending to enforce it.

## Scope boundary

**IN.** The `feature_oracle` key in `GATE-NN.md` and its reader; execution
through the existing `_run_gate_set`; union into `verify()` for units in that
gate; the close's re-run and its recorded measurement; one lint rule; the
template, skill and methodology changes that make it the drafted default.

**OUT, deliberately.**

- **Tiered per-attempt gate sets.** FEAT-2026-0109 consumes this oracle as one
  of its cheap per-attempt gates. This feature makes the oracle exist and run;
  it does not change which *other* gates run per attempt.
- **Retrofitting oracles onto the four existing drafted gates** (FEAT-2026-0052,
  -0081 ×2, -0082). Writing a real oracle for each means designing three
  unrelated features inside this one. They are the WARN backlog the lint rule
  surfaces, to be filled when each feature is picked up.
- **Enforcing "stubs allowed only in the tracer bullet."** T04 writes it as an
  authoring rule. Machine-detecting a stub is a different feature.
- **Promoting shipped oracles into `verification.yml`.** A deliberate later act
  per feature, not automated here.
- **Changing the judge.** The judge already reads the close's `## Measurements`;
  T02 puts the oracle result there, so the binary signal arrives with no judge
  change.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  ```
  grep -rn "feature_oracle" specfuse/ .specfuse/
  grep -n "oracles" specfuse/loop/loop.py specfuse/loop/prerun.py specfuse/loop/lint_plan.py
  grep -n "def _run_gate_set" specfuse/loop/loop.py
  ```
- **Verdict:** `no existing mechanism, building new — but reusing the runner`.
  `feature_oracle` appears only in roadmap and PLAN prose; no code reads it.
- **Two adjacent mechanisms, one reusable.** The per-WU `oracles:` key
  (FEAT-2026-0057/T04, `prerun.py`) resolves `verification.yml` sets run
  **pre-dispatch**, capture-all, output appended to the session's prompt — an
  *input* mechanism, not an exit oracle, so not reusable here. `extra_gates:`
  is exit-oracle plumbing but is per-WU and config-resolved.
- **The reuse that matters:** `_run_gate_set(gate_set: list, feature_dir)`
  (`loop.py:4025` pre-0102 numbering) takes an **arbitrary list of
  `{name, command}` dicts**, not a `verification.yml` set name. `probe_baseline`
  and `verify()` merely happen to pass config-derived lists. So a gate-declared
  oracle can be synthesized into a one-element list and handed to the existing
  runner, inheriting its timeout, process-group kill, Windows bash routing,
  degraded-oracle detection, report format and `failure_class` attribution —
  all of which took four bug fixes to get right (#207, #2557, #2885, #167).
  **No second execution path is built.**

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

T03 raises "a gate declares no `feature_oracle`" to ERROR when the feature is
`active`, WARN when it is `planned` / `blocked` / `deferred`, and skips gates
already `passed` and features already `done` / `abandoned`.

- **What does the rule report on an input already in its intended final state?**
  **Zero ERRORs**, measured before drafting rather than asserted. A sweep of
  every non-`done`, non-`abandoned` feature's non-`passed` gate files returns
  five hits today: `FEAT-2026-0052/GATE-01`, `FEAT-2026-0081/GATE-01` and
  `GATE-02`, `FEAT-2026-0082/GATE-01`, and `FEAT-2026-0011` (no gate files,
  `blocked`). **All five sit in `planned` or `blocked` features, so all five are
  WARN.** No feature is `active` with a gate file, so the ERROR set is empty.
- **Why the naive scoping was rejected.** Scoping ERROR to "non-`passed` gate in
  a non-`done` feature" — the first shape drafted — fires on all five, i.e. on
  correct inputs. Graduating by feature status makes the rule satisfiable now
  and blocking exactly when a feature is picked up, which is the moment its
  author is thinking about it.
- **Why not a marker-gated variant** ("only gates drafted after this key
  exists"): `[FEAT-2026-0070/G2-CLOSE]` — a marker-gated guard is inert on every
  artifact that exists, its first real firing is necessarily in someone else's
  future run, and the close that ships it cannot honestly count its own vacuous
  pass as evidence.

## Task graph

```yaml
# Single gate, terminal `close` — 4 planned substantive WUs, under the
# threshold of 8 in `docs/methodology.md` §6 "Ceremony proportionality".
#
# T01 is the tracer bullet in this feature's own sense: it makes this gate's
# `feature_oracle` runnable and green. T02-T04 deepen rather than assemble.
# T01, T02 and T03 each edit `specfuse/loop/*.py`, so each completion trips
# the sanctioned `driver_restart_required` brake — expect three restarts.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0101/T01
        file: WU-01-declare-read-run-oracle.md
        depends_on: []
      - id: FEAT-2026-0101/T02
        file: WU-02-close-reruns-and-records.md
        depends_on: [FEAT-2026-0101/T01]
      - id: FEAT-2026-0101/T03
        file: WU-03-lint-oracle-declared.md
        depends_on: [FEAT-2026-0101/T01]
      - id: FEAT-2026-0101/T04
        file: WU-04-authoring-surfaces.md
        depends_on: [FEAT-2026-0101/T01, FEAT-2026-0101/T02, FEAT-2026-0101/T03]
      # T05 added after the gate's first close recorded `not_met`. The judge
      # found that an oracle naming a command the shell cannot run is reported
      # as an ordinary gate FAIL rather than a configuration problem, so a
      # typo'd declaration reads to the next agent as "your code is broken"
      # (issue #3260). Attribution, not detection: the run already fails.
      - id: FEAT-2026-0101/T05
        file: WU-05-unrunnable-oracle-attribution.md
        depends_on: [FEAT-2026-0101/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0101/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0101/T01, FEAT-2026-0101/T02, FEAT-2026-0101/T03, FEAT-2026-0101/T04, FEAT-2026-0101/T05]
```

## Notes

- **This gate's oracle demonstrates this feature.** `GATE-01.md` declares
  `python3 -m unittest tests.test_feature_oracle_e2e -q`, an end-to-end test
  that builds a temp feature folder whose gate declares an oracle, drives a unit
  through `verify()`, and asserts the oracle executed and its result was
  recorded at close. It is red on HEAD by construction; T01 makes it green. A
  feature about feature oracles that could not state its own would be the
  recursive hollow pass `[FEAT-2026-0008/G1-CLOSE]` warns about.
- **The close owes a recursive audit.** Per `[FEAT-2026-0008/G1-CLOSE]`, any
  feature fixing a methodology failure mode must verify at close that its guards
  both landed **and are wired** — `grep -n "<helper>(" <target>` returning a call
  site in the path the feature names, not merely a definition. An unwired helper
  is a hollow pass with extra steps.
- **Cost calibration.** FEAT-2026-0102's per-WU estimates ran 2.6× high
  ($3.31 actual against $19.00 planned for three substantive units), and
  `planned_cost_usd` feeds `evaluate_auto_close`'s per-WU ratio checks, so loose
  estimates make every gate auto-close. These are set from 0102's actuals
  (~$1.10 per substantive unit, $7.96 for a judged close) with headroom, not
  from the earlier guesses.
- **Why `autonomy_default: review`.** This feature changes what verification
  means, and `verify()` is what produces the evidence the judge reads. As with
  FEAT-2026-0102, `judge_editing` does not apply — it evaluates the *next*
  gate's drafted WUs at arm time and a single-gate feature never arms one — but
  the close is worth a human read on the one feature that moves the oracle
  itself.
</content>
