---
feature_id: FEAT-2026-0063
title: Branch-observation sweep for the arm predicate
slug: arm-predicate-branch-coverage
branch: feat/FEAT-2026-0063-arm-predicate-branch-coverage
roadmap_goal: Make the arm-predicate sweep honest and standing rather than ad-hoc — exclude baseline-less features, and record per class which branches have been observed on real input and which have not, so "unverified" is a named list rather than an assumption.
autonomy_default: review
status: active
planned_cost_usd: 16.00
---

# Plan: Branch-observation sweep for the arm predicate

The arm predicate (`specfuse/loop/arm_eval.py`) is the mechanical gate standing
between an `auto` feature and an unattended arm. It has eight stop classes. Nobody
knows which of them work, because nothing has ever asked the question in a form that
survives being asked twice.

## What is actually true, measured 2026-08-03

Restricted to the four features that carry a `PLAN.baseline.json` — the only input on
which the predicate can say anything at all:

```
FEAT-2026-0053  g1  arm=False  fired=[judge_editing, retroactive_edits, open_questions_human_only]
FEAT-2026-0053  g2  arm=False  fired=[judge_editing, retroactive_edits, open_questions_human_only]
FEAT-2026-0053  g3  arm=False  fired=[retroactive_edits]
FEAT-2026-0060  g1  arm=True   fired=-
FEAT-2026-0061  g1  arm=True   fired=-
FEAT-2026-0062  g1  arm=True   fired=-

4 baselined features; class-verdict totals: 41 clean, 7 fired, 0 not_evaluable
```

Per class, which *branches* have ever been observed on real input:

```
budget_projection          clean            NEVER fired, NEVER not_evaluable
decision_class_paths       clean            NEVER fired, NEVER not_evaluable
drift_caps                 clean            NEVER fired, NEVER not_evaluable
missing_provenance         clean            NEVER fired, NEVER not_evaluable
plan_next_lint             clean            NEVER fired, NEVER not_evaluable
judge_editing              clean, fired     NEVER not_evaluable
retroactive_edits          clean, fired     NEVER not_evaluable
open_questions_human_only  clean, fired     NEVER not_evaluable
```

Five of the eight stop classes have never fired on real input. `not_evaluable` — the
fail-closed path — has never been observed for **any** class outside fixtures. Every
firing observation in the corpus comes from a single feature, FEAT-2026-0053.

## Why this feature reports rather than verifies

The roadmap row was titled "Live-input verification for the arm predicate's
fail-closed branches." This plan deliberately does not verify them, and the row is
retitled to match.

Making a never-fired branch fire requires constructing a feature folder that trips
it — an over-budget feature, an uncovered manifest, a drift breach. That artefact is
a fixture wearing a costume, and `LEARNINGS [FEAT-2026-0053/G1-CLOSE]` is precisely
the rule that says green-on-fixtures for a fail-closed path is the evidence shape
that already fooled this project once. Manufacturing the input would produce a
number that looks like coverage and is not.

What can honestly be delivered is a sweep that reports only what it can evaluate,
names the unverified branches as a list rather than an assumption, and is a standing
mechanism instead of something a human runs at wrap time. Verification of the five
arrives on its own schedule as the corpus grows — one baselined feature at a time,
at no cost to us.

## Why this row's own premise is the argument for it

This row has now been drafted against a wrong premise twice in two days.

On 2026-08-02 it was pulled `active` and returned to `planned` the same day: its
headline figure (42 of 44 features `not_evaluable`) was an artefact of sweeping the
42 features that predate `write_baseline_if_absent` and structurally cannot carry a
baseline. On 2026-08-03, the corrected premise had itself gone stale — FEAT-2026-0060
had shipped and carried a baseline, moving the sample from three features to four,
and a per-*branch* reading showed the unverified surface was five never-fired classes
rather than the two branches the row named.

Both errors have the same cause: the measurement was re-derived by hand each time it
was needed. That is the defect this feature closes.

## Existing-mechanism search (`.specfuse/rules/planning-discipline.md` §1)

```
Command: grep -rn "evaluate_arm_predicate" --include=*.py --include=*.yml --include=*.sh .
         ls .specfuse/scripts/ | grep -iE "sweep|report|coverage|audit"

Verdict: NO existing mechanism performs this measurement. evaluate_arm_predicate has
         exactly ONE production caller — loop.py:708, the live arm path. Every other
         call site (30+) is a fixture-based test. No script under .specfuse/scripts/
         sweeps feature folders for predicate verdicts.

Precedent: .specfuse/scripts/event_type_gate.py (FEAT-2026-0060/T02, merged
         2026-08-03) is a structural twin and the model this feature follows — a
         corpus sweep, DELIBERATELY SCOPED to a subset so it can be green on this
         tree today, wired into verification.yml, exit 0/1, with the scoping reason
         written into its docstring rather than left implicit.

Recurrence: ad-hoc predicate sweeps have been hand-run at close time four times
         (FEAT-2026-0053 ×3 consecutive runs, FEAT-2026-0061 close criterion 7,
         FEAT-2026-0062 which deferred a tree-wide sweep). The roadmap row cites a
         "second instance earns the tooling" bar; the real count is past it.
```

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

The trap on this feature is a gate that asserts coverage.

A gate requiring every class to have fired on real input, or every `not_evaluable`
branch to have been observed, is **red on this tree today and cannot be made green by
any work this feature is allowed to do** — five classes have never fired and no class
has ever reported `not_evaluable`. Asserting it would be an unsatisfiable acceptance
criterion, the exact shape that cost FEAT-2026-0060 two blocked attempts and $4.48
last week, where criterion 9 demanded zero validator errors while the WU's
Do-not-touch list forbade the only file that could deliver them.

So T02's gate asserts **completeness of the sweep**, not coverage of the branches: it
fails when a baselined feature could not be evaluated, or when an `not_evaluable`
verdict appears among evaluable features without an explanation. Both are satisfiable
today — the sweep currently reports 0 `not_evaluable` across 4 of 4 evaluable
features — and both would genuinely fire on a real regression. The never-fired list
is *output*, not an assertion.

## Runtime probe for a default/severity flip (§4)

Not applicable. No default value, threshold, or severity is flipped. `arm_eval.py` is
not modified by this feature at all — the sweep is a new reader of an unchanged
predicate.

## Flag-scope table (§3)

Not applicable. No behaviour flag is introduced.

## Scope boundary — explicitly OUT

- **Manufacturing inputs to make a never-fired branch fire.** The fixture trap named
  above. The five never-fired classes are reported as unverified, not exercised.
- **Fixing or changing any stop class.** FEAT-2026-0061 and FEAT-2026-0062 own
  `decision_class_paths` and `budget_projection` respectively. This feature reads.
- **Ratchet, waiver, and tracking-issue machinery.** FEAT-2026-0052 owns that. T02's
  gate is a plain assert, not a ratchet, specifically so the two do not collide.
  Regression protection for the observed-branch set is 0052's to add if it wants it.
- **Widening `event_type_gate.py`.** FEAT-2026-0073 owns the `correlation_id` envelope
  gap that keeps it scoped.
- **The first `auto` ride against an external target project.** It remains the
  strongest single source of live input and is not a precondition for this row.

## The trap that will otherwise be rediscovered

`docs/concepts/autonomy-stop-classes.md` is **mirrored** into
`specfuse/loop/data/docs/concepts/autonomy-stop-classes.md`, and
`tests/test_scaffold_data_in_sync.py::test_package_docs_match_canonical` byte-matches
the two. A WU that edits the canonical doc and not its mirror fails the `tests` gate
on a diff it did not know it owed. T03 writes both.

## Gates

```yaml
# Single terminal gate: 3 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0063/T01
        file: WU-01-arm-sweep-module.md
        depends_on: []
      - id: FEAT-2026-0063/T02
        file: WU-02-coverage-gate.md
        depends_on: [FEAT-2026-0063/T01]
      - id: FEAT-2026-0063/T03
        file: WU-03-observed-branch-record.md
        depends_on: [FEAT-2026-0063/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0063/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0063/T01
          - FEAT-2026-0063/T02
          - FEAT-2026-0063/T03
```
