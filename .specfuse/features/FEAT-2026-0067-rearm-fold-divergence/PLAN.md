---
feature_id: FEAT-2026-0067
title: One fold path — cumulative_* always means lifetime
slug: rearm-fold-divergence
branch: feat/FEAT-2026-0067-rearm-fold-divergence
roadmap_goal: Decide whether the frontmatter has one fold path or two, and make the code and the contract agree either way — so a reader cannot mistake "never re-armed" for "re-armed and the fold silently did not run".
autonomy_default: review
status: done
planned_cost_usd: 16.50
---

# Plan: one fold path

A re-armed work unit's prior-cycle spend lands in one of two different places
depending on a condition nobody chose. `fold_cumulative_on_rearm` moves it into
`cumulative_cost_usd` and zeroes `cost_usd` — but it runs only when
`detect_rearm_dispatch` returns true, and that helper requires `cost_usd > 0` at
dispatch time.

Both shapes exist in this repository right now. Measured, not estimated:

```
re-armed WUs: fold ran = 6    fold never ran = 2
```

## The defect is the guard, not the fold

`detect_rearm_dispatch` decides "already folded" by reading a **value**:

```python
cost_usd = fm.get("cost_usd", 0)
return isinstance(cost_usd, (int, float)) and float(cost_usd) > 0
```

A zero here means either "the prior cycle cost nothing" or "a prior fold already
moved it". The function cannot tell those apart, so it guesses, and when it
guesses wrong the fold never runs and the spend survives only in
`re_arm_history[].prior_cost_usd`.

This is the exact shape `LEARNINGS [FEAT-2026-0053/G2-CLOSE]` warns about, and
the same shape this week's #593 and #306 turned out to be: a check inferring
state from a value that has two meanings. The fix is not a better inference. It
is an explicit signal.

## The decision this feature takes: converge

The roadmap row names two viable shapes and says to choose one rather than
splitting the difference.

**Chosen: converge.** The fold runs on every re-arm regardless of `cost_usd`,
driven by an explicit marker. `cumulative_*` becomes unconditionally the
lifetime accumulator; `re_arm_history[].prior_*` becomes a pure audit record.

**Rejected: admit two paths.** It documents the ambiguity instead of removing
it, and every future reader still needs the helper to know which shape they
hold. `cost.py` already half-implements this option — its module docstring
names "fold-ran" and "fold-never-ran" as two supported shapes — which is the
strongest argument against it: the workaround already exists and the ambiguity
survived anyway. FEAT-2026-0062 shipped `wu_lifetime_cost_usd` so *consumers*
stopped caring about the shape. That was the right scope for that feature and
is not a reason to leave the written contract ambiguous forever.

The duration and token accumulators come along for free: `fold_cumulative_on_rearm`
already folds `cumulative_duration_seconds`, `cumulative_input_tokens`, and
`cumulative_output_tokens` in the same call. They carry the identical split today
and no consumer gates on them yet — fixing the trigger fixes all four before one
does.

## Existing-mechanism search (`.specfuse/rules/planning-discipline.md` §1)

Run before drafting, so this feature does not rebuild something already present.

| Question | Command | Verdict |
|---|---|---|
| Does an explicit fold marker already exist? | `grep -rn "folded\|folded_through" specfuse/loop/*.py` | **No.** Only prose in docstrings; no frontmatter field, no state. |
| Is there already a shape-independent reader? | `grep -rn "cumulative_cost_usd\|wu_lifetime_cost_usd" specfuse/loop/*.py` | **Yes** — `cost.py:wu_lifetime_cost_usd`, FEAT-2026-0062. It reads around the divergence; it does not remove it. Kept, not rebuilt. |
| Who consumes the accumulators? | same | `arm_eval.py:172` only, via `wu_lifetime_cost_usd`. No consumer reads `cumulative_*` directly, so changing when it is written breaks no reader. |
| How many WUs carry each shape? | frontmatter census over `.specfuse/features/**/WU-*.md` | 6 fold-ran, 2 fold-never-ran. Small enough to migrate explicitly rather than tolerate. |

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

Every escalation trigger below can actually be evaluated by the session that
carries it:

- **T01's** triggers read `detect_rearm_dispatch`'s inputs and the fixture WUs
  it constructs — all in-repo, all in-process.
- **T02's** migration operates on 8 real WU files whose current shape the WU
  itself enumerates; "the census disagrees with the plan" is checkable by
  re-running the same census the plan quotes.
- **T03's** trigger is a documentation/contract mismatch the session can read
  directly in `WU.template.md` and `cost.py`.

None depends on an oracle outside the repository.

## Deliberately out of scope

- **Changing what `wu_lifetime_cost_usd` returns.** It stays the canonical
  accessor and keeps its events-first precedence. Only its fallback branch's
  *documentation* changes, to say the frontmatter fallback now has one shape.
- **Back-filling cost onto `done` features' records.** The two fold-never-ran
  WUs are `done`; their spend is not lost (it is in `re_arm_history` and in
  `events.jsonl`). T02 decides migrate-or-annotate explicitly and records the
  reason; it does not rewrite historical cost values.
- **`attempts` / `cumulative_attempts`.** A different accumulator with its own
  contract (#199); untouched here.

```yaml
# Single terminal gate: 3 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0067/T01
        file: WU-01-explicit-fold-marker.md
        depends_on: []
      - id: FEAT-2026-0067/T02
        file: WU-02-migrate-existing-shapes.md
        depends_on: [FEAT-2026-0067/T01]
      - id: FEAT-2026-0067/T03
        file: WU-03-contract-and-accessor.md
        depends_on: [FEAT-2026-0067/T01]
      # T04: fix WU added after G1-CLOSE hedged on a defect T02 introduced and
      # the close was not permitted to repair. See RETROSPECTIVE.md FU-1.
      - id: FEAT-2026-0067/T04
        file: WU-04-fix-offline-fold-double-count.md
        depends_on: [FEAT-2026-0067/T02]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0067/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0067/T01
          - FEAT-2026-0067/T02
          - FEAT-2026-0067/T03
          - FEAT-2026-0067/T04
```
