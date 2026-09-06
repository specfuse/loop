---
gate: 1
status: open
cost_budget_usd: 55.00
baseline:
  sha: 7f50a473b99f0483eb71a390bea995cf1a6af689
  probed_at: 2026-09-06T13:26:04.150571+00:00
  failing: []
---

# Gate 1 — the verdict is written by a session that did not do the work

## Definition of done

Stated as behaviours demonstrable on fixtures with an injected runner:

- A terminal close whose session writes `verdict: met` is followed, in the
  same driver run, by a judge dispatch whose prompt contains the gate's
  definition of done, the `GATE-NN-CRITERIA.md` entries, the gate's diff, and
  the close's `## Measurements` section, and does not contain the close's
  `## Verdict` or `## Retrospective` prose.
- When the injected judge answers `not_met` with two criterion findings, the
  close WU's on-disk `verdict:` reads `not_met`, `FOLLOW-UPS.md` carries two
  entries in the judge's words, no terminal surface flips, and a `judged`
  event records `close_verdict: met`, `judge_verdict: not_met`.
- When the close writes `not_met` and the injected judge answers `met`, the
  verdict stays `not_met` and the `judged` event records the disagreement.
- When the judge's session times out or returns no parseable verdict, the
  close's own verdict stands, the event says `judge_verdict: null` with the
  reason, and the run does not crash.
- `judge_disabled: true` in PLAN frontmatter skips the dispatch and prints a
  one-line notice naming the escape hatch.
- The judge's usage is folded into the close WU's `cost_usd` and the
  `attempt_outcome` event; the retrospective's cost analysis can see it.
- `specfuse lint` reports ERROR on a `pending` close WU whose body says
  `verdict: met`, and zero ERROR over every existing feature folder.
- `PLAN.template.md` and `/draft-feature`'s autonomy recommendation read
  `auto`; `close-discipline.md` §1 says the judge writes the verdict.

If all five units are `done` and any behaviour above cannot be demonstrated,
this gate is not done.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **T05 raises a check to ERROR.** PLAN.md answers §2: zero on a correctly
  drafted close; `done` closes are skipped. Before arming, run `specfuse lint`
  over every feature folder with T05's rule applied and paste any ERROR here.
- **No flag is introduced.** `judge_disabled` is an escape hatch, not a
  behaviour flag; it has one reader and no flag-scope table.
- **The close is load-bearing** and carries `auto_close_disabled: true`. It
  is also the first close this repository judges; that is deliberate.
- Expect a `driver_restart_required` halt after every unit.

## Reflection notes

<Written by the human at review time.>
