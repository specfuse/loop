---
gate: 1
status: awaiting_review
cost_budget_usd: 45.00
baseline:
  sha: 65b4c74fa188b5ab3d702f607f9d049413dc2f99
  probed_at: 2026-09-03T11:34:02.704748+00:00
  failing: []
---

# Gate 1 — a close can only say met or not_met, and every other outcome has an honest home

## Definition of done

Stated as behaviours the close can demonstrate on fixtures, not as five units:

- A close dispatched on a fixture feature that writes `verdict: met_locally`
  is refused at outcome time with a reason naming the two legal values; the
  same close writing `not_met` without `FOLLOW-UPS.md` is refused; writing
  `not_met` with one entry per failed criterion passes, leaves every terminal
  surface un-flipped, and files one issue per entry through an injected runner
  whose argv carries the follow-up label and the entry body verbatim.
- An auto-closed gate's retrospective stub contains no `deferred:` line and no
  `autoclose-debt` marker, and the terminal close of a feature with an
  auto-closed predecessor passes without a "What the loop did NOT verify"
  section.
- A `type: human` unit that is ready halts the driver without a dispatch,
  prints the six-part operator brief, and after the operator marks it `done`
  with `evidence:`, the driver proceeds to the next unit; a `done` human unit
  without evidence is a lint ERROR.
- `grep -rl "met_locally\|partially_met"` over `specfuse/ plugins/ .specfuse/rules .specfuse/templates tests/` names zero files, and over `docs/` names only the migration section.
- The full suite is green and `specfuse lint` over every feature folder reports the same ERROR count as before this gate.

If all five units are `done` and any behaviour above cannot be demonstrated,
this gate is not done.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **T01 narrows a guard, T03 and T04 add ERROR-level checks.** PLAN.md answers
  §2 for each: zero on the existing corpus because the guards run only on
  closes dispatched from now on and on unit types that do not exist yet.
  Before arming, run `specfuse lint` over every feature folder with the
  branch's `lint_plan` and paste any new ERROR here.
- **This feature is sequenced after FEAT-2026-0084.** Do not arm until 0084
  is merged and this branch is rebased onto `main`; T05 edits files 0084
  reshapes.
- **The close is load-bearing** and carries `auto_close_disabled: true`.
- Expect five `driver_restart_required` halts; every unit edits
  `specfuse/loop/`.

## Reflection notes

<Written by the human at review time.>
