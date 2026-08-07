---
open_questions: []
---

# Gate 2 review

Written by `FEAT-2026-0075/G1-PLAN` from gate 1's `RETROSPECTIVE.md`, its observed
output, `.specfuse/LEARNINGS.md`, and two sweeps over all 57 feature folders in
`.specfuse/features/`.

`open_questions: []` is deliberate and means nothing blocks execution — every design
question this unit opened was answered by a sweep or by an existing rule, and the
answers are below. It does **not** mean nothing is contentious: three draft-time
proposals were rejected, and the operator can overrule any of them at arm time. Those
are decisions on file, not questions awaiting one.

## The headline: gate 2 is smaller than it was scaffolded to be, and it is a different shape

The draft-time `GATE-02.md` proposed an **arm-time refusal** keyed on plan shape,
extending `arm_eval`'s class-2 `judge_editing` detection, plus a **sanctioned status**
for the two-invocation hold.

Gate 2 as drafted ships **three units, $12.50 planned**: narrow the predicate to the
importable surface (`T04`), a sanctioned **halt** rather than a status (`T05`), and a
**squash-diff halt at dispatch time** rather than an arm-time refusal (`T06`). The
`arm_eval` extension is dropped entirely.

**This is not a recommendation to close the feature after gate 1.** The dispatch-brief
invited that outcome on the condition that gate 1's observed output showed the immediate
warning reliably landing in the window before the close dispatches. **It showed the
opposite.** `RETROSPECTIVE.md` §2 records that gate 1's warning, gate summary and event
fired **zero** times, corroborated on three independent surfaces, and that a repo-wide
`grep -rl driver_staleness_detected .specfuse/features/*/events.jsonl` returns nothing.
Gate 1 shipped a diagnostic that has never executed. The condition for shrinking to
nothing is not met; the condition for *changing the shape of the control* is.

The strongest evidence for gate 2 is that gate 1's own arming discipline failed under
ideal conditions: the rule was promoted in `LEARNINGS.md`, quoted verbatim in
`GATE-01.md`, set in bold as REQUIRED, and backed by a close criterion built to detect
its omission — and the restart still did not happen.
`[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]`
names the conclusion and, in rule (a), names the control this gate ships.

## The §2 answer, and why the arm-time shape was rejected

`planning-discipline.md` §2 asks: *what does this control report on an input already in
its intended final state?*

**Sweep, all 57 feature folders / 90 gates**, matching each work unit's declared
`produces:` / `produces_driver_helper` against the driver-module predicate and against
gate order:

```
features=57  gates=90
gates containing a driver-editing WU                : 41
of those, gates where that WU precedes the gate's close : 41   <-- the draft-time predicate
gates with NO driver-module edit at all             : 49
```

**The draft-time scoping reports 41 of 41 — it is unsatisfiable.** Every gate in the
methodology ends with a `close` or `close-intermediate`, so a driver-editing unit is
*always* scheduled ahead of a close in its own gate. There is no correctly-ordered gate
in this repository's entire history, and no author could write one. Per §2 that is a
stop-and-redesign, not a softening at arm time, and it is what happened.

**The shipped scoping (`T06`) reports zero.** 49 of 90 gates never set the flag and are
never interrupted. In the 41 that do edit the driver, one halt is the correct behaviour
— the halt refuses no plan and rejects no work unit; it costs one re-run.

**A second, independent argument kills the arm-time shape even if it were satisfiable.**
An arm-time check has no diff to read — nothing has run — so it must key on
author-supplied `produces:` / `produces_driver_helper`. `PLAN.md`'s own scope decision
forbids exactly that: *"`produces:` and `produces_driver_helper` are author-supplied and
the lint on the latter is WARN-only, so a unit can edit `loop.py` while declaring
nothing. A detector that trusts the declaration misses precisely the careless case it
exists to catch."* Building the feature's one *blocking* control on the evidence class
the feature's plan rejects would be the sharpest possible self-contradiction. The
squash diff is ground truth and the driver already has it.

## What was rejected, and what that costs

**1. The arm-time refusal, and the `arm_eval` class-2 extension.** Rejected for the two
reasons above. Three consequences, stated so the operator can weigh them:

- The single-detector constraint is still honoured — `specfuse/loop/driver_edit.py`
  remains the one detector, `T04` narrows it in place, no second detector is built. The
  constraint said *do not build a parallel mechanism*; dropping the arm-time consumer
  satisfies it more completely than extending it would have.
- `arm_eval`'s class-2 `judge_editing` **already fires** on any drafted WU producing
  `specfuse/loop/` — that is unchanged and untouched. It vetoes *auto*-arming and says
  nothing about staleness. Under `autonomy_default: review` (this feature's setting) it
  changes nothing, which is precisely why it did not prevent occurrences one through
  four.
- **What is lost:** nothing warns at *plan* time that a gate will halt mid-way, so an
  operator planning a driver-editing gate does not learn to budget for two invocations
  until the halt fires. This is real but cheap — the halt's message carries the resume
  command, and the cost is one re-run. An advisory arm-time class remains available as a
  follow-up (below) if the operator wants it.
- **Mechanical note, if the operator wants to restore it anyway:** the arm predicate's
  drift cap (`arm_eval.DRIFT_CAP_RATIO = 0.5` against a baseline of 6 WUs) allows **at
  most 3 added WUs** before `drift_caps` fires. Gate 2 adds exactly 3. A fourth unit
  fires the cap on the feature that exists to make planning honest.

**2. A new work-unit status for the hold.** The draft-time proposal assumed the hold
needed one, because `draft` is refused for the whole gate (`loop.py:5760-5770`) and
`blocked_human` reads as a failure. Both facts are true and both dissolve if **nothing
is marked at all**. `T05`'s halt flips no WU status and leaves the gate `open`, so
`/attention`, `gate-status`, `lint_plan.py`'s `VALID_STATUS`, and the five per-type
tables in `loop.py` all need zero changes — they see an active feature with an open gate
and pending units, which is exactly what it is. The sanctioned name lives on the halt
(`HALT_REASON_DRIVER_RESTART`, a distinguished exit code, and a
`driver_staleness_detected` event carrying `halted: true`), not on a work unit.

**Constraint check.** The dispatch brief made "the hold ships with the refusal or the
refusal does not ship" load-bearing. It is honoured, and under the shipped shape it is
structurally unavoidable: `T06` cannot fire without `T05`'s halt, and `PLAN.md`'s graph
makes `T06` depend on it.

**3. Driver re-exec.** `[…/a-rule-a-human-must-execute-is-not-a-control]` rule (a) names
re-exec as the alternative to a refusal, and it would remove the operator action
entirely. Rejected as out of scope: the run holds a `flock`, an open event buffer, and
per-attempt reset state, and `os.execv` inherits file descriptors — a re-exec that gets
any of that wrong loses the gate rather than restarting it. This is the same
blast-radius argument `PLAN.md` used to reject subprocess-per-attempt isolation, and it
lands the same way. Halt-and-resume reduces the operator's action to re-running the
command they already ran, which is the loop's existing idiom at every gate boundary.

## What gate 1 got right, and what it got wrong

**Right, and inherited unchanged:** detection keyed on the squash diff rather than on
declarations, and the warning placed in the window between a squash landing and the next
dispatch. `T06` fires from that exact seam. The two-gate split was also right for a
reason its author did not anticipate: gate 1's *failure* to observe itself is what
produced the evidence that a diagnostic is not a control.

**Wrong, and corrected by `T04`:** the predicate is broader than its own docstring's
claim. `RETROSPECTIVE.md` §4 flags this from `T03`'s own diff. Measured across the tree,
3 of 41 flagged gates are pure false positives (docs, example configs, a workflow file).
Warn-only that costs noise; under `T06` it would stop a run.

**Unverified, not refuted:** gate 1's central claim. The code is present and tested at
the seam; no run has executed it end-to-end. `GATE-02.md`'s arming discipline turns that
into free evidence — `T04` edits `specfuse/loop/driver_edit.py`, so a driver launched
after gate 1's last commit prints `T02`'s warning the moment `T04`'s squash lands.
`G2-CLOSE` criterion 4 closes out `RETROSPECTIVE.md` §5's four deferred rows against
that observation.

## The one thing gate 2 cannot fix, stated plainly

`T06`'s halt is not live in the process that dispatches `T06`. Gate 2's own arming
therefore still requires a manual driver restart between `T06` and `G2-CLOSE` — the same
step gate 1 carried, and failed. **A fifth occurrence is possible on this gate**, and if
it happens it should be recorded as the result it is rather than worked around.
`GATE-02.md` § *Arming discipline* carries the step; `G2-CLOSE` criterion 1 blocks on
it; `[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]` applies — the
restart buys a truthful observation, not a working one.

Gate 2 is the last gate in this repository that has to do this by hand.

## Deferred with a home

Not built by gate 2, each with the site where it gets picked up. `G2-CLOSE` criterion 7
carries these forward into the terminal follow-up record.

| Deferred | Why not now | Where it gets picked up |
|---|---|---|
| `/attention` + `gate-status` rendering a halted run as "awaiting driver restart — re-run `<cmd>`" | The halt marks nothing, so no consumer *misreads* it; this is positive surfacing, not a correction. Canonical skill files live in `plugins/specfuse/skills/` and sync into `.specfuse/skills/`, so it is a second sync surface for a nice-to-have | Its own roadmap row, or folded into the next `/attention` feature |
| An advisory arm-time class reporting "this gate will halt mid-way, budget for two invocations" | Redundant with the halt for *prevention*; valuable only for *budgeting*. Adding it makes 4 added WUs and fires `arm_eval`'s drift cap (see above) | Its own roadmap row if the two-invocation budgeting proves annoying in practice |
| Driver re-exec instead of halt-and-resume | Blast radius across `flock`, the event buffer, per-attempt reset state and inherited fds | Only if halt-and-resume proves insufficient in practice; would need its own feature |
| `specfuse-lint` on `PATH` resolving to a stale installed wheel (`RETROSPECTIVE.md` §8) | Same family as this feature's subject — an installed artifact diverging from the source a session believes it is running — but a different mechanism, and outside this feature's charter | Its own roadmap row; flagged here because gate 1 found it and nothing else owns it |
| `events.jsonl` losing a re-armed closing cycle (`RETROSPECTIVE.md` §8) | A bookkeeping defect gate 1 observed on its own close; unrelated to staleness | Its own roadmap row; `G2-CLOSE` criterion 5 checks whether it recurred |

## Costs

| WU | Type | Planned | Basis |
|---|---|---:|---|
| `T04` narrow the predicate | implementation | $2.00 | pure-module change + tests + a sweep. Gate 1's comparable `T01` cost $1.18 against $2.50 planned |
| `T05` sanctioned halt | implementation | $3.00 | the largest of the three: a new brake at the run-loop seam, an event, and a durable bookkeeping commit |
| `T06` wire the halt | implementation | $2.50 | one call site and a flag, but four seam cases to assert (fires / final-unit / dry-run / negative) |
| `G2-CLOSE` | close | $5.00 | `planning-discipline.md` §5 `close` floor |
| **Sum** | | **$12.50** | |
| **`cost_budget_usd`** | | **$17.50** | sum + one re-attempt of the largest WU (`G2-CLOSE`, $5.00), per §5's corollary |

Implementation estimates are calibrated down from gate 1's actuals ($1.18 / $1.44 /
$2.78 against $2.50 / $3.50 / $3.00 planned — every unit under, two of them at well
under half). Gate 1's over-estimate was not free: `PLAN.md`'s $19.50 gate-1 sum was the
number the operator planned against.

## Red-test coverage (`/authoring-work-units` §12)

Every behaviour-introducing implementation WU names a scoped test that fails on HEAD
before it runs. No `Red-test exempt:` line is used anywhere in gate 2.

| WU | Named red test |
|---|---|
| `T04` | `tests/test_driver_module_surface.py::test_data_path_is_not_a_driver_module` |
| `T05` | `tests/test_driver_restart_hold.py::test_halt_leaves_gate_open_and_units_pending` |
| `T06` | `tests/test_driver_restart_halt_wiring.py::test_driver_edit_halts_before_next_dispatch` |

## Sweep reproduction

Both sweeps in this document are offline reimplementations of the predicate over
declared plan surfaces, run by `G1-PLAN` against `.specfuse/features/*/PLAN.md` and each
WU's frontmatter. They are **planning evidence, not shipped-code evidence** —
`GATE-02.md` § *Arming discipline* makes re-running them against the real narrowed
predicate a §4 arming precondition, and `T04` criterion 9 / `T06` criterion 10 /
`G2-CLOSE` criterion 3 each require the output pasted. The expected counts are
41 broad / 38 narrow / 3 false-positive-only, and 49 gates with no driver-module edit at
all.
