---
feature_id: FEAT-2026-0075
title: Driver-editing work units cannot take effect in the process that dispatches them
slug: driver-edit-staleness
branch: feat/FEAT-2026-0075-driver-edit-staleness
roadmap_goal: Make the driver-staleness hazard visible while it can still be acted on, and then impossible to arm into, rather than rediscovered after the money is spent.
autonomy_default: review
status: active
planned_cost_usd: 32.00
---

# Plan: Driver-editing work units cannot take effect in the process that dispatches them

Python caches modules in `sys.modules` at first import. A work unit that edits the
driver therefore changes nothing for any work unit the same driver process dispatches
afterwards — including the close armed to verify it. The close runs the pre-edit
function object, observes none of the new behaviour, and reports honestly that the
thing does not work.

Nothing in a gate can catch this from the inside. Unit tests, symbol imports, and
close-time probes all run in fresh interpreters and all report the new behaviour
correctly, which is exactly why the disagreement reads as a mystery rather than a
staleness bug.

**This has now happened three times, across two features, with the mitigating rule
already written down.** `[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]` states
the hazard precisely and prescribes the fix. FEAT-2026-0056 was planned with that
lesson present in `.specfuse/LEARNINGS.md` and hit the hazard anyway — its own
retrospective records that the lesson "was already in `LEARNINGS.md` when gate 1 was
planned and was simply not consumed at plan time." Then its terminal close was
dispatched from a process that predated the four units it was armed to observe, spun
three attempts, and escalated `spinning_detected` at **$3.66**.

That is the argument for this feature, and it is not "the rule is missing." The rule
is written, promoted, and ignored. A hazard that depends on an operator remembering it
at plan time has to become a property of the system.

This file owns the **shape** of the feature: the gate order, which work units belong
to each gate, and the dependency edges between them. It does **not** own status —
each WU file owns its own status, and each GATE file owns its gate's status. Detail
only as far as the next gate; plan-next drafts the gate after that from the
retrospective and lessons.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**

  ```
  grep -rn "produces_driver_helper" specfuse/loop/*.py
  grep -rniE "stale|sys\.modules|restart" specfuse/loop/*.py
  grep -nE "def (changed_paths|modified_paths|diff_names|files_changed)" specfuse/loop/loop.py
  ```

- **Verdict:** `found one adjacent mechanism, extending it — no staleness detection
  exists, and no changed-paths helper exists.`

- **What the greps surfaced:**

  - **`arm_eval.py:294-305` already detects driver-editing work units.** Its class-2
    `judge_editing` check flags any *drafted* WU whose `produces:` matches a judge
    path or whose `produces_driver_helper` is non-empty, and fires an autonomy veto.
    **The driver already knows which units edit itself.** What it does not do is treat
    that as a *staleness* hazard, and it only looks at drafted units at arm time —
    never at the ordering of units inside a gate that is already running, which is
    where all three losses occurred. Gate 2 extends this surface; gate 1 does not
    touch it.
  - **No staleness or restart detection anywhere.** The `stale` hits are unrelated —
    a stale flock file, a stale divergent branch, stale failure-note advice, and the
    untracked-file sweep's local variable. Building new.
  - **No changed-paths helper.** `squash_commit` (`loop.py:2175`, called at
    `loop.py:6182`) produces the commit whose diff is the ground truth for what a unit
    changed, but nothing extracts that path list. T01 builds it.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

Gate 1 is warn-only and flips no severity, so this section's question does not arise
for it. Nothing in gate 1 blocks, refuses, or fails a gate; it prints and records.
There is no "zero issues" predicate to satisfy.

Gate 2 raises a blocking control and needs the full §2 answer. **`G1-PLAN` wrote it —
see `GATE-02.md` § *Escalation-predicate satisfiability*, and `GATE-02-REVIEW.md` for
the argument.** The short form: the question was *what does the arm-time refusal report
on a gate that is already correctly ordered?*, and a sweep of all 57 feature folders /
90 gates answered **41 of 41** — every gate in the methodology ends with a close, so a
driver-editing unit is always ahead of a close in its own gate and no compliant plan
exists to write. The arm-time scoping was therefore unsatisfiable and was re-drafted, not
softened. The shipped control is a squash-diff halt whose §2 answer is **zero**: 49 of
90 gates contain no driver-module edit and are never interrupted.

Gate 1's output was expected to be the evidence for this. It was not, and the reason is
itself the finding: gate 1's warning, summary and event fired **zero** times, because
the process that dispatched its close predated the entire gate (`RETROSPECTIVE.md` §1
and §2). The §2 answer above is therefore derived from a sweep over declared plan
surfaces rather than from observed warn output, and `GATE-02.md`'s arming discipline
carries the §4 requirement to re-run that sweep against the shipped code before arming.

## Scope decision: what this feature builds, and what it deliberately does not

The roadmap row named three viable shapes and left the choice to gate 1. The operator
chose the **detect-and-warn → refuse-at-arm** pair, in that order, one gate each.

**Subprocess-per-attempt isolation is rejected**, and the reason is not that it would
fail. It is the only shape that makes the hazard *impossible* rather than visible, and
that guarantee is real. But the driver's per-attempt `git reset --hard`, its
untracked-file cleanup, its event buffer, and its `flock` all assume a single process,
so the feature would spend both gates on plumbing and be judged on bookkeeping rather
than on the hazard. Against that,
`[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]` is the decisive
evidence: a stronger guarantee buys a *truthful observation*, not a working one — and
a truthful observation is exactly what detect-and-warn already delivers, at a fraction
of the blast radius.

**Two properties of the gate-1 design are load-bearing and should not be relaxed
without re-opening this section:**

- **The warning fires immediately, not only at gate completion.** The roadmap row
  proposed gate-completion timing. On all three real occurrences the close was the
  very next unit dispatched after the driver-editing one, so a gate-end warning would
  have printed a correct message immediately *after* each loss. The window between the
  wiring unit passing and the close dispatching is where the money went, and that is
  where the immediate warning lands. The gate-end summary is retained as the second
  half because it is what a close reads when writing its retrospective.
- **Detection keys on the unit's actual squash diff, never on its declarations.**
  `produces:` and `produces_driver_helper` are author-supplied and the lint on the
  latter is WARN-only, so a unit can edit `loop.py` while declaring nothing. A
  detector that trusts the declaration misses precisely the careless case it exists to
  catch. The squash commit's diff is ground truth and the driver already has it.

## This feature will trigger its own hazard, and that is planned for

`T02` and `T03` both edit `specfuse/loop/loop.py`, and `G1-CLOSE-INTERMEDIATE` is the
unit contracted to verify them. That is the exact shape that cost FEAT-2026-0057 and
FEAT-2026-0056. `GATE-01.md` § *Arming discipline* carries the driver restart as a
required step between `T03` and the close, and the close carries a process-start-time
check as its first acceptance criterion, blocking if the restart did not happen.

If gate 1 works, its own close should be the first close in this repository's history
to see this warning in its own dispatch. If the restart is skipped instead, the tax
will have been paid a fourth time while building the fix for it — which would be the
strongest possible evidence for gate 2's refusal, and should be recorded as such
rather than hidden.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0075/T01
        file: WU-01-driver-edit-detection.md
        depends_on: []
      - id: FEAT-2026-0075/T02
        file: WU-02-immediate-staleness-warning.md
        depends_on: [FEAT-2026-0075/T01]
      - id: FEAT-2026-0075/T03
        file: WU-03-gate-summary-and-record.md
        depends_on: [FEAT-2026-0075/T01]
      # --- OPERATOR STEP between T03 and the close: restart the driver. ---
      # Not a work unit — there is nothing in the graph schema that represents an
      # operator action. Enforced by G1-CLOSE-INTERMEDIATE's criterion 1, which
      # blocks if the dispatching process predates T03's started_at. See
      # GATE-01.md § Arming discipline.
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0075/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0075/T01
          - FEAT-2026-0075/T02
          - FEAT-2026-0075/T03
      - id: FEAT-2026-0075/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0075/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0075/T04
        file: WU-04-narrow-driver-module-surface.md
        depends_on: [FEAT-2026-0075/T01]
      - id: FEAT-2026-0075/T05
        file: WU-05-sanctioned-restart-hold.md
        depends_on: [FEAT-2026-0075/T02]
      - id: FEAT-2026-0075/T06
        file: WU-06-halt-before-dispatching-into-a-stale-process.md
        depends_on:
          - FEAT-2026-0075/T04
          - FEAT-2026-0075/T05
      # --- OPERATOR STEP between T06 and the close: restart the driver. ---
      # Same step gate 1 carried, for the same reason, and gate 2 is the last
      # gate that has to do it by hand: T06's halt is not live in the process
      # that dispatches T06. Not a work unit — there is nothing in the graph
      # schema that represents an operator action. Enforced by G2-CLOSE's
      # criterion 1, which blocks if the dispatching process predates T06's
      # started_at. See GATE-02.md § Arming discipline.
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0075/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on:
          - FEAT-2026-0075/T04
          - FEAT-2026-0075/T05
          - FEAT-2026-0075/T06
```

## Notes

- **Gate 1 blocks nothing.** It prints and records; no gate fails because of it. That
  is what keeps gate 1 free of a severity flip and lets gate 2's refusal be designed
  against real observed output instead of an assumption.
- **The sanctioned hold is gate 2's, and it is a hard dependency of the refusal.** The
  two-invocation split has no usable status today: `draft` is rejected by the arm
  check for the whole gate, and `blocked_human` reads as a failure in `/attention` and
  every other consumer. An arm-time refusal that forces the operator into an
  improvised hold is worse than no refusal, so if gate 2 ships the refusal it must
  ship the hold with it.
- **`[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]` applies to this
  feature's own close.** A restart buys a truthful observation, not a working one.
  Budget for gate 1's honest answer being "the warning did not fire", and treat that
  as a result rather than a failure of the run.
- Dependencies live here, not in WU frontmatter.
- WU file numbers track the correlation sub-ID; closing units use the reserved 90+
  range so they sort last.
