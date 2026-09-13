---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_progress_lines_end_to_end -v -b"
---

# Gate 1 — progress lines replace unconditional reflection

## Definition of done

After a gate runs, `PROGRESS.md` in the feature folder carries one entry per
dispatched work unit, written by the driver from what the session already
returns. A gate that stayed on-plan closes without writing reflective prose;
a gate that went off-plan still gets it in full.

The `feature_oracle` above is the executable proof. It is **red today**:
`tests/test_progress_lines_end_to_end.py` does not exist. T01 is the tracer
bullet that makes it runnable and green; T02–T03 make each half correct.

Also required, as for every gate:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

Note the ordering hazard this gate creates for itself: T03 makes reflective
sections conditional, and this gate's own close is the first close to run
under that rule. If this gate stays on-plan, its own retrospective is the
first one the feature suppresses. That is the intended behaviour and also the
sharpest possible test of whether `PROGRESS.md` is a good enough substitute —
the close should say which it was.

## What this gate must not break

`judge.py:237-238` reads `RETROSPECTIVE.md` and slices `## Measurements` into
the judge's evidence bundle. Measurements are **not** reflective prose and do
not become conditional. A gate whose reflective sections were skipped must
still produce a retrospective the judge can take measurements from, or the
verdict path loses its evidence.

`assert_learnings_appended_or_noop` makes at least one added `LEARNINGS.md`
line the success signal of every close. This gate does not change that guard —
bounding `LEARNINGS.md` is deliberately out of scope (PLAN.md) — so a close
that skips reflective prose still appends its lesson or says nothing
generalizes.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** T03 changes when an
  existing obligation applies rather than flipping a default value or a
  severity, so no probe is required by §4. If the implementation turns out to
  need a `verification.yml` default to carry the opt-out, the probe applies to
  that unit.
- **Flag-scope table (§3).** T03 introduces the condition that selects between
  reflective and non-reflective closes. Confirm it carries a flag-scope table
  naming every closing requirement in the registry and whether the condition
  gates it.
- **Escalation-predicate satisfiability (§2).** No check is raised to `ERROR`
  in this gate.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and
why, anything the close got wrong. This is your record, not the agent's.>
