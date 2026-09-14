---
feature_id: FEAT-2026-0106
title: Progress lines and conditional reflection
slug: progress-lines-bounded-learnings
branch: feat/FEAT-2026-0106-progress-lines-bounded-learnings
roadmap_goal: Each dispatched unit leaves a short progress note the next unit can read, and a gate that stayed on-plan closes without writing reflective prose nobody asked for.
autonomy_default: review        # edits the driver; judge_editing vetoes an auto-arm
                                # regardless, so review states that up front
status: done
planned_cost_usd: 16.50
---

# Plan: Progress lines and conditional reflection

Closing ceremony is the largest single line item left in the 2026-09-01
methodology review. 713 close, close-intermediate, plan-next and legacy
ceremony units account for 39% of all spend and 28% of agent hours, and
re-measured on 2026-09-13 the figure had moved the wrong way: 41% on drivers
up to 0.14.x, 43% on 0.15.0 and later, against a 12% target.

This feature takes the half of the roadmap row that targets that number: a
short progress note per unit, and reflective prose written only when a gate
actually went off-plan. The LEARNINGS half of the original row is deliberately
not here — see the scope boundary.

This file owns the **shape** of the feature: the gate order, which work units
belong to it, and the dependency edges between them. It does **not** own
status — each WU file owns its own status, and each GATE file owns its gate's
status.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Commands run:**
  - `grep -rn "PROGRESS.md\|progress_note" specfuse/loop/*.py .specfuse/rules/*.md`
  - `grep -n "assert_learnings_appended_or_noop\|file=RETROSPECTIVE_FILENAME" specfuse/loop/closing_requirements.py`
  - `grep -n "RETROSPECTIVE_FILENAME\|MEASUREMENTS_SECTION" specfuse/loop/judge.py`
  - `sed -n '4648,4670p' specfuse/loop/loop.py`
- **Verdict:** `no PROGRESS.md machinery exists; the inputs for it already do`.

  `parse_result_block` (`loop.py:4648`) returns the agent's entire RESULT
  block, `summary` included, on every attempt with well-formed output — and
  nothing persists it on the pass path. Measured across this repo's corpus,
  8% of `attempt_outcome` events carry a `summary`, and those are **driver**-set
  on guard-refusal and smoke paths (`loop.py:7790, 10244, 10347`), not
  agent-supplied. So the data arrives and is dropped; how often an agent
  actually emits `summary:` is unmeasured, and T01 measures it.

  The seven retrospective-bound closing requirements all live in one registry
  (`closing_requirements.py`), so making a subset conditional is a registry
  edit, not new machinery. `gate_eval.evaluate_auto_close` already computes the
  off-plan signal T03 keys on.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — this feature raises no check to `ERROR`, flips no `WARNING` to blocking,
and asserts no "zero issues" close predicate. It makes an existing obligation
conditional and adds one file.

## The roadmap goal's "only on `not_met`" is superseded

The row says the terminal close should write a retrospective "only on
`not_met` or on request". That is not implementable as written, for an
ordering reason: the close writes `RETROSPECTIVE.md`, and only **then** does
the judge run and produce the verdict. There is no `not_met` to condition on
at the moment the file is written.

It would also starve the judge. `judge.py:237-238` opens `RETROSPECTIVE.md`
and slices `## Measurements` into the evidence bundle — while the judge prompt
forbids the judge from opening the file, precisely because the bundle already
extracted that section. The retrospective therefore carries two separable
roles: evidence the judge needs, and reflective prose the judge is banned from
reading. Only the second can become conditional.

T03 keys the reflective half on `evaluate_auto_close`'s off-plan predicate
instead — blocked WU, replan event, cost overrun — which is verdict-independent,
computed from events the driver already holds, and already the signal the
methodology uses to decide a gate deserves reflection.

## Decisions taken at drafting

- **Ceremony half only.** The original row also capped `LEARNINGS.md` at 40
  entries. That half moves a different metric (planning context, which the
  review has never successfully measured) and has a far more finished proposal
  behind it than this draft would produce — see the scope boundary.
- **Driver-side write, agent-supplied insight.** The driver writes
  `PROGRESS.md` so the note cannot be skipped and costs no prompt tokens; the
  forward-looking half arrives as an optional RESULT field (T02) rather than
  as an append instruction in every work unit. An append obligation enforced
  by a guard is exactly the mechanism that produced an unbounded
  `LEARNINGS.md` nothing reads.

## Scope boundary — deliberately out

- **The LEARNINGS cap, and everything in #3272.** That issue carries a
  consumer's measured design — 219 entries, 91 never cited, computable reach
  and cost weights, a shipped 47-line distilled file — and deserves a feature
  that adopts it rather than a second half someone rushes. One correction to
  record for whoever picks it up: #3272 claims `learnings_query.py` no longer
  ships and the skills' lookup errors. Both skills call the module form
  `python3 -m specfuse.loop.learnings_query`, which ships with the driver; that
  diagnosis is stale, the rest of the issue stands.
- **The judge's evidence bundle.** Untouched. Two defects were found in that
  path this month (#3307, and a finding with fabricated evidence); it is not
  getting a third change in the same quarter from a feature about ceremony.
- **A separate retrospective file, and any migration of existing ones.**
- **`GATE-NN-CRITERIA.md` carry-forward.** This is what actually caused
  FEAT-2026-0104's $31.47 closing overrun — four close dispatches re-running
  the same twelve oracles — and it is a different mechanism from anything here.
  It deserves its own issue, not a ride on this branch.
- **Single-session mode for small features**, which is FEAT-2026-0107.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0106/T01
        file: WU-01-progress-lines-tracer-bullet.md
        depends_on: []
      - id: FEAT-2026-0106/T02
        file: WU-02-forward-looking-result-field.md
        depends_on: [FEAT-2026-0106/T01]
      - id: FEAT-2026-0106/T03
        file: WU-03-conditional-reflection.md
        depends_on: [FEAT-2026-0106/T01]
      - id: FEAT-2026-0106/T04
        file: WU-04-document-the-shape.md
        depends_on: [FEAT-2026-0106/T02, FEAT-2026-0106/T03]
      # --- closing sequence: 1-WU close (terminal gate, <=8 substantive WUs) ---
      - id: FEAT-2026-0106/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0106/T01
          - FEAT-2026-0106/T02
          - FEAT-2026-0106/T03
          - FEAT-2026-0106/T04
```

## Notes

- Four substantive work units is under `docs/methodology.md` §6's
  ceremony-proportionality threshold, so this drafts as a single gate with a
  single terminal `close` — no `close-intermediate`, no `plan-next`. A feature
  about ceremony cost paying the minimum ceremony is the intended shape, not a
  coincidence.
- Dependencies live here, not in WU frontmatter.
