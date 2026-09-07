---
feature_id: FEAT-2026-0100
title: Separate judge session — a fresh evaluator decides the close verdict
slug: separate-judge-session
branch: feat/FEAT-2026-0100-separate-judge-session
roadmap_goal: The verdict on every terminal close is written by a fresh session that sees only evidence — the gate's definition of done, per-criterion state, the gate's diff, the close's measurements, and the oracles it may re-run — never by the session that did the work; a judge can lower a verdict and never raise one; and with that judge in place, auto-arm becomes the default a drafted feature recommends.
autonomy_default: review
status: done
planned_cost_usd: 40.00
---

# Plan: Separate judge session

FEAT-2026-0085 made the close verdict binary. The close still writes it, and
the close is the same kind of session that did the work, reading its own
retrospective while it decides. Every surveyed loop that works moves the
verdict elsewhere: Claude Code's own guidance runs a verification subagent "so
the agent doing the work isn't the one grading it", `/goal` uses a fresh model
per turn, and the practitioners' line is that models reliably skew positive
when grading their own output. FEAT-2026-0108's first close is the counter-
example that proves the point the other way: it wrote an honest `not_met`, but
only because its own demonstration script happened to fail; nothing structural
made that honesty likely.

This feature puts a judge between the work and the flip. After a close's
squash passes the closing-deliverable guards, the driver dispatches a short,
fresh session that receives evidence only and writes the verdict. The close's
own `verdict:` becomes advisory. A judge can lower `met` to `not_met`, writing
`FOLLOW-UPS.md` from its per-criterion findings; it cannot raise a `not_met`.
With that in place, the one human checkpoint the methodology keeps — the plan —
is enough, and `autonomy_default: auto` becomes what a drafted feature
recommends.

## Scope boundary

**IN.** `specfuse/loop/judge.py` (new), the close path in `loop.py` between
the closing guards and the verdict read, the judge's cost accounting, the
`judged` event, one lint rule, and the rule/template/docs changes that move
the verdict's authorship.

**OUT, deliberately.**

- **A feature-level oracle.** The judge reads criteria and diffs; it does not
  yet have a single end-to-end command per feature to run. That is
  FEAT-2026-0101, drafted after this lands so the judge has something binary
  to read.
- **Judging intermediate closes** (`close-intermediate`). Terminal closes
  only; intermediate gates keep their ceremony until the next-gate plan is
  itself judged, which is 0101's territory.
- **Changing the arm predicate.** `arm_eval.py` is untouched; only the
  *default* a drafted feature recommends changes.
- **Retiring the close's retrospective.** Still written; it just stops
  carrying the verdict's authority. FEAT-2026-0106 owns the ceremony diet.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -n "^def dispatch(\|^def execute_unit_attempt(" specfuse/loop/loop.py
  -> :3537, :4421. Dispatch takes a WorkUnit and a failure note and pipes the
     body to `claude -p`. The judge is not a work unit: T02 adds a sibling
     entry point that takes a prompt string, reusing dispatch's argv builder
     and JSON envelope parse rather than a fourth copy.

grep -n "^def assert_verdict_well_formed\|^def verdict_permits_terminal_flips" specfuse/loop/loop.py
  -> :5775, :411. The verdict is re-read from the close WU's frontmatter after
     the squash and must be in VERDICT_VALUES. T02 runs the judge before that
     re-read and writes the judge's verdict into the same field, so every
     downstream reader (flips, FOLLOW-UPS filing, gate-status) is unchanged.

grep -n "^def \|^CRITERION_STATES" specfuse/loop/criteria_state.py
  -> parse_criteria_state, build_reverification_worklist, render_criteria_state;
     states pass/fail/unverified. GATE-NN-CRITERIA.md is the per-criterion
     evidence the judge reads; nothing new is invented for it.

grep -n "^def format_reverification_worklist\|^def precreate_dispatch_skeleton" specfuse/loop/loop.py
  -> :3471, :3400. The close's prompt already receives the criteria worklist;
     the judge's prompt receives the same artifact plus the diff and the
     close's Measurements section.

grep -rn "output-format" specfuse/agent/invoke.py
  -> FEAT-2026-0108/T01's run_claude returns the usage envelope. T03 folds the
     judge's usage through the same shape rather than re-parsing.
```

**Verdict: reusing four shipped mechanisms (dispatch argv and envelope parse,
the verdict field and its readers, the criteria artifact, the usage
envelope); building one new module (`judge.py`) and one lint rule.**

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

T05 adds an ERROR-level lint: a `close` WU body that instructs the session to
write a specific verdict (`verdict: met`, "the verdict is hedged", "record
`not_met`") is refused at arm time. **What does the rule report on an input
already in its intended final state?** Zero: a correctly drafted close names
what to measure and never names the verdict. The sweep over this repository's
corpus is part of T05's acceptance; `done` closes are skipped as sealed
history. (Correction after the close's first attempt: FEAT-2026-0082's close
on `main` was `pending`, not `done`, and its pre-decided hedge did fire the
rule; the operator rewrote those sentences on 2026-09-06 and the sweep now
reports zero.)

The judge itself flips no severity. It can only lower a verdict, and the driver
records both verdicts in the `judged` event, so a judge that is wrong is
visible and re-armable, never silent.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0100/T01
        file: WU-01-judge-module.md
        depends_on: []
      - id: FEAT-2026-0100/T02
        file: WU-02-close-path-wiring.md
        depends_on: [FEAT-2026-0100/T01]
      - id: FEAT-2026-0100/T03
        file: WU-03-judge-cost-accounting.md
        depends_on: [FEAT-2026-0100/T02]
      - id: FEAT-2026-0100/T04
        file: WU-04-rules-templates-auto-default.md
        depends_on: [FEAT-2026-0100/T02]
      - id: FEAT-2026-0100/T05
        file: WU-05-lint-no-predecided-verdict.md
        depends_on: [FEAT-2026-0100/T04]
      # --- hygiene precursors to the close's re-run, authored from the close's
      # first attempt (not_met on three criteria; see each WU body) ---
      - id: FEAT-2026-0100/T01H
        file: WU-01H-redaction-respects-heading-levels.md
        depends_on: [FEAT-2026-0100/T05]
      - id: FEAT-2026-0100/T02H
        file: WU-02H-judge-diffs-from-gate-entry.md
        depends_on: [FEAT-2026-0100/T01H]
      # --- second round of hygiene, from the close's second attempt: the judge
      # lowered met to not_met on two evidence-bundle defects (see WU bodies) ---
      - id: FEAT-2026-0100/T01H2
        file: WU-01H2-section-slicing-respects-heading-levels.md
        depends_on: [FEAT-2026-0100/T02H]
      - id: FEAT-2026-0100/T02H2
        file: WU-02H2-entry-sha-for-in-flight-gates.md
        depends_on: [FEAT-2026-0100/T01H2]
      # --- terminal gate: single close WU ---
      - id: FEAT-2026-0100/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0100/T01
          - FEAT-2026-0100/T02
          - FEAT-2026-0100/T03
          - FEAT-2026-0100/T04
          - FEAT-2026-0100/T05
          - FEAT-2026-0100/T01H
          - FEAT-2026-0100/T02H
          - FEAT-2026-0100/T01H2
          - FEAT-2026-0100/T02H2
```

## Post-merge checklist

- Over the next five features closed with the judge in place, record the
  judge's verdict against the close's own in each `judged` event: the
  disagreement rate, and for each disagreement whether the judge was right.
  A judge that never disagrees is not reading; a judge that is usually wrong
  needs a better evidence bundle.

## Notes

- **Single gate, five substantive units** (threshold 8).
- **`review` autonomy, on purpose.** Every unit here edits `specfuse/loop/`,
  which the arm predicate's `judge_editing` class vetoes under `auto` anyway,
  and this is the feature that makes `auto` safe for the ones after it.
- **This feature's own close is judged.** T02 lands before the close runs, so
  the first judged close is this one. Its close does not know that in
  advance and must not be told to expect a verdict; T05 forbids that shape.
- **Every unit edits the driver.** Expect a `driver_restart_required` halt
  after each of T01 through T05.
- **Measurement baseline** for the close: 0 judged closes; the close WU is the
  sole writer of `verdict:`; `PLAN.template.md` defaults to `review`.
