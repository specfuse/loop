---
gate: 2
status: awaiting_review
cost_budget_usd: 31.00
baseline:
  sha: d7a96b960e06dcceaf958fdc4416fa3b5a8b09c8
  probed_at: 2026-08-07T15:50:38.454866+00:00
  failing: []
---

# Gate 2 — the hazard is prevented, and the two-invocation hold has a name

## Definition of done

Rewritten by `G1-PLAN` from gate 1's `RETROSPECTIVE.md`, its observed output, and
`.specfuse/LEARNINGS.md`. Each bullet is traceable to a stated goal in `PLAN.md` or to
something gate 1 observed; the traceability is named inline. `GATE-02-REVIEW.md`
records what was accepted, revised and rejected against the draft-time proposal, and
why.

- **The driver's staleness predicate matches its own claim — the importable surface,
  not everything under `specfuse/loop/`.** *(Traces to: `RETROSPECTIVE.md` §4, the
  finding gate 1 was forbidden from repairing — `T03`'s own diff touched
  `specfuse/loop/data/schemas/driver-event.schema.json`, a JSON file read from disk that
  cannot stale a process, and the predicate flagged it. Measured: 3 of 41 flagged gates
  across the repository are pure false positives.)* Warn-only, a false positive costs
  noise; the halt below makes it cost a stopped run.

- **The two-invocation split has a sanctioned name, and it is a halt the process
  performs on itself rather than a status a human must set and later clear.**
  *(Traces to: `PLAN.md` § Notes, "the sanctioned hold is gate 2's, and it is a hard
  dependency" — `draft` is refused for the whole gate at `loop.py:5760-5770` and
  `blocked_human` reads as a failure. Sharpened by
  `[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]`
  rule (c).)* **Revised from the draft-time proposal**, which assumed the hold needed a
  new work-unit status. It does not: a halt that flips no WU status and leaves the gate
  `open` needs no new vocabulary in any consumer.

- **When a squash lands touching the driver and the gate still has units to dispatch,
  the driver halts instead of dispatching into a process that cannot execute the
  change.** *(Traces to: `PLAN.md`'s roadmap goal — "impossible to arm into" — and to
  `RETROSPECTIVE.md` §1 and §2, which record that gate 1's warning, summary and event
  fired exactly zero times because the dispatching process predated the entire gate.
  The control is named verbatim in
  `[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]`
  rule (a).)* **Revised from the draft-time proposal's arm-time refusal** — see the
  satisfiability answer below, and `GATE-02-REVIEW.md` for the full argument.

- **The control reports zero on a gate that is already correctly ordered**, answered
  against a measured sweep rather than asserted. *(Traces to: `PLAN.md` §
  *Escalation-predicate satisfiability*, which deferred this question to `G1-PLAN`
  explicitly, and to `planning-discipline.md` §2.)* See the next section.

- **Gate 1's central claim is verified in situ, or its non-verification is recorded as
  a result.** *(Traces to: `RETROSPECTIVE.md` §5's deferred-verification table, which
  names "the first gate completion under a driver started after `cbc3b23`" as the site
  and says "gate 2's own dispatch is the natural site".)* Gate 2's arming precondition
  makes this free — `T04` edits `specfuse/loop/driver_edit.py`, so a driver started
  after gate 1's last commit will print `T02`'s warning on `T04`'s squash. That is the
  first execution of gate 1's code in a live dispatch.

- `RETROSPECTIVE.md` carries a `## Gate 2` section; lessons are promoted or their
  absence stated; the terminal verdict is recorded. *(Inherited unchanged from the
  draft-time scaffold — **deliberately accepted**: it is `close-discipline.md`'s fixed
  obligation for a terminal gate, not a gate-2 design choice.)*

**Deliberately dropped from the draft-time proposal:** the arm-time refusal keyed on
plan shape, and the extension of `arm_eval`'s class-2 `judge_editing` detection. Both
are rejected with reasoning in `GATE-02-REVIEW.md` § *What was rejected*. The
single-detector constraint is honoured — `specfuse/loop/driver_edit.py` remains the one
detector, `T04` narrows it in place, and no second detector is built.

## Escalation-predicate satisfiability (`planning-discipline.md` §2)

> **What does this control report on a gate that is already correctly ordered?**

**Zero, for the shipped shape (`T06`'s squash-diff halt).** The evidence is a sweep
`G1-PLAN` ran over all 57 feature folders in `.specfuse/features/` — 90 gates — matching
each work unit's declared surface against the driver-module predicate:

```
features=57  gates=90  gates with a driver-editing WU = 41
gates flagged by BROAD prefix specfuse/loop/  : 41
gates flagged by NARROW (.py, excl data/)     : 38
gates flagged ONLY by broad (false positives) : 3
```

- **49 of 90 gates contain no unit that edits the driver's importable surface.** In
  those, `T06`'s flag is never set and the run is never interrupted. That is the zero.
- In the 41 that do, one halt is the **correct** behaviour, not a false positive: a gate
  that edits the driver and keeps dispatching in the same process is the defect this
  feature exists to remove. The halt refuses no plan and rejects no work unit; it costs
  one re-run of a command the operator already ran.
- `T04`'s narrowing removes 3 of the 41 — docs, example configs and a workflow file that
  cannot stale a process.

**The draft-time scoping was unsatisfiable, and this is why it was rejected rather than
softened at arm time.** The proposal was "a gate whose plan schedules a driver-editing
work unit ahead of a close in the same gate is refused at arm time." Applied to the same
90 gates, that reports **41 of 41** — every gate in the methodology ends with a close, so
a driver-editing unit is *always* ahead of a close in its own gate and **no compliant
plan exists to write**. Per `planning-discipline.md` §2 the predicate is unsatisfiable
and the WU is re-drafted before arming, which is what `G1-PLAN` did. `GATE-02-REVIEW.md`
§ *The §2 answer, and why the arm-time shape was rejected* carries the reasoning and the
second, independent argument: an arm-time refusal must key on author-supplied
`produces:` declarations, and `PLAN.md`'s scope decision already rules that out —
"detection keys on the unit's actual squash diff, never on its declarations."

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe before arming (§4). REQUIRED, and it is `T04` criterion 9 /
  `T06` criterion 10.** `G1-PLAN`'s sweep above is an *offline reimplementation* of the
  predicate, not the shipped code. Before gate 2 is armed, and again inside each unit,
  the sweep is re-run against the real narrowed predicate over every feature folder and
  its output pasted. **A halt reported on any of the 49 gates with no driver-module
  edit means the control is mis-scoped**, and per §2 the unit is re-drafted rather than
  softened. The 41/38/3 counts are the expected result; a discrepancy must be explained
  before arming.

- **Driver restart between the last `specfuse/loop/`-editing unit and `G2-CLOSE`.
  REQUIRED, operator action.** `T04`, `T05` and `T06` all edit `specfuse/loop/`, and
  `G2-CLOSE` is the unit contracted to verify them. **This is the same shape that has
  now cost four dispatches, the fourth of them gate 1's own close** — see
  `RETROSPECTIVE.md` §1, where the process that dispatched the close was byte-for-byte
  the process that had probed the gate's baseline ninety minutes before the first unit
  ran.

  **The mitigation cannot mitigate its own gate.** `T06`'s halt is not live in the
  process that dispatches `T06`, for exactly the reason `T06` exists. Gate 2 is the last
  gate that has to do this by hand. Stop the driver after `T06` reports `done`; start a
  fresh one before `G2-CLOSE` dispatches. `G2-CLOSE` criterion 1 checks the dispatching
  process's start time and blocks if the restart did not happen.

- **Start gate 2 under a driver launched after gate 1's last commit. REQUIRED,
  operator action, and it is free evidence.** `T04`'s squash touches
  `specfuse/loop/driver_edit.py`, so a driver carrying gate 1's code prints `T02`'s
  `STALE DRIVER PROCESS:` warning the moment `T04` lands. That is the first live
  execution of gate 1's code in this repository's history and it clears three rows of
  `RETROSPECTIVE.md` §5's deferred-verification table at no cost. Started from a stale
  process, gate 2 both re-runs gate 1's failure and loses the observation.

- **Escalation-predicate satisfiability (§2).** Answered above, against the sweep, not
  asserted. This is the load-bearing check for this gate.

- **Flag-scope table (§3).** Stated in `T06`'s body. Gate 2 introduces **no** behavior
  flag, deliberately: an opt-out from the halt is a control a human can forget, which is
  the failure `[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]`
  names. `DRIVER_MODULE_PREFIXES` / `DRIVER_DATA_PREFIXES` are data consulted by a
  predicate, not flags gating a code path on a configurable value.

- **Cost budget (§5 corollary).** `cost_budget_usd: 17.50` = $12.50 (T04 $2.00 + T05
  $3.00 + T06 $2.50 + G2-CLOSE $5.00) plus one re-attempt of the largest WU
  (`G2-CLOSE`, $5.00). `G2-CLOSE` carries the §5 `close` floor of $5.00. Implementation
  estimates are calibrated down from gate 1's actuals, where T01/T02/T03 came in at
  $1.18/$1.44/$2.78 against $2.50/$3.50/$3.00 planned.

## Budget re-baseline — operator decision, 2026-08-07

`cost_budget_usd` was raised **$17.50 → $31.00** by operator decision after the brake
fired. Recorded here rather than edited quietly, because a budget silently raised
whenever it fires is a decorative budget.

**What fired.** The brake halted before `G2-CLOSE`'s dispatch with
`spent $21.3764 >= budget $17.5000`. It halted correctly, no work unit was dispatched,
and nothing was spent on the halted run.

**Why the overrun happened**, since the number matters more than the delta:

- `T06` came in at **$7.90 against $2.50** (3.2×). It was the gate's hardest unit —
  the halt wiring at the dispatch seam — and its estimate was the one `GATE-02-REVIEW.md`
  flagged as least certain.
- `G2-CLOSE`'s first dispatch burned **$9.32 across three attempts and produced nothing**:
  no retrospective section, no verdict, no lessons, its only `files_touched` being
  `GATE-02-CRITERIA.md`. It was dispatched into a process that predated `T04`–`T06`, so
  `T06`'s halt could not stop it — this feature's own subject, occurrence five, exactly
  as `GATE-02-REVIEW.md` § *The one thing gate 2 cannot fix* predicted.

Neither overrun is evidence the remaining work is mis-estimated. The gate's three
substantive units are `done` and green; what remains is the close.

**The new figure is $21.38 already spent plus $9.62 of headroom** — more than the $8.68
FEAT-2026-0056's comparable terminal close cost, and matching the $9.32 this close burned
on its failed run. It is not a re-forecast of the remaining work; it is the sunk cost
plus one close.

**For `G2-CLOSE`'s cost analysis:** reconcile against **both** figures. The $17.50 is
what the gate was planned to cost and the honest baseline for the variance; the $31.00 is
what it was permitted to cost after this decision. Reporting only the second would hide
the overrun the brake exists to surface.

## Reflection notes

<Written by the human at review time.>
