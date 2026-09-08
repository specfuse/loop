---
id: FEAT-2026-0109/G2-CLOSE-INTERMEDIATE
type: close-intermediate
status: draft
attempts: 0
planned_cost_usd: 4.50
oracle_env: macos_local
auto_close_disabled: true
produces:
  - .specfuse/features/FEAT-2026-0109-tiered-verification/RETROSPECTIVE.md
model: opus
effort: high
gate_set: plannext
---

# Gate 2 close — measure what the narrow tier saved, and what it let through

**Objective.** Non-terminal close of gate 2: demonstrate each behaviour in
`GATE-02.md`'s definition of done in this session, measure the per-attempt
saving against `GATE-02.md`'s recorded table, and report what the narrow tier
failed to catch. Measure; do not decide a feature-level verdict — gate 2 is not
the terminal gate.

**Context.** Depends on T04-T07. Binding: `.specfuse/rules/close-discipline.md`.
Append to the existing `RETROSPECTIVE.md` under a `## Gate 2` heading; gate 1's
section is not yours to edit. Run `specfuse lint --closing` before reporting
`complete`.

**The saving is a per-attempt comparison on this tree.** `GATE-02.md` records
the before: 169.4s for the full `code` set, 146.1s for the suite alone, 3.9s
for a unit's declared modules, 0.05s for `ruff`. Report the narrow tier's
actual wall clock per attempt in this gate, the broad run's wall clock, and the
gate total — narrow × attempts + one broad run — against what the same gate
would have cost at 169.4s × attempts. Gate 1's own arithmetic is the model to
follow: state the counterfactual and show how the record determines it.

**The half a saving cannot show.** Gate 1's lesson 1 was that a feature betting
failures are rare measures its saving on the happy path and its safety nowhere.
Gate 2 has a sharper version of the same obligation, and it is answerable here
rather than deferrable: **did the broad run ever go red on work every narrow
tier had passed?** That is the number that says whether narrowing lost anything.
If it is zero, say zero plainly and say what that does and does not establish.

Report alongside it: how many attempts ran the narrow tier; how many fell back
to the full command and why (empty selection, unmapped path, no map); how often
the changed-file map resolved anything at all; and how many times the broad run
was skipped at an unchanged tree.

**T07's correction is a close-discipline §3 surface.** The bound's wording moved
on three surfaces outside this gate's own units. Enumerate them in the contract
section so the terminal close does not have to re-derive them.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries `## Gate 2` and a `## Measurements` table: for each bullet of `GATE-02.md`'s definition of done, the command run in this session and its exit status.
- `## Measurements` states the narrow-tier wall clock per attempt, the broad-run wall clock, the gate total, and the counterfactual at 169.4s per attempt — with the number of attempts each figure is computed over.
- The count of broad runs that went red on work the narrow tier had passed, stated explicitly even when it is zero, with what a zero does and does not establish.
- The fallback counts: attempts that ran the full command instead of a selection, broken down by reason; and broad runs skipped at an unchanged tree.
- This gate's `feature_oracle` verdict recorded in `## Measurements` — required by the closing lint (FEAT-2026-0101/T02) whenever the gate declares one.
- `## Retrospective`: whether the narrow tier ever let a regression reach the broad run, and whether the changed-file selector earned its cost over the declared-tests rule alone.
- The contract surface gate 2 changed, for the terminal close to enumerate: the `tier:` key in `verification.yml`, the new driver event type, the `broad_run:` gate block, and T07's three reworded claims.
- `## Cost analysis` reconciling gate 2's `planned_cost_usd` against `events.jsonl`, naming the delta and the restart count.
- `## What the loop did NOT verify`: at minimum, whatever the narrow tier's fallback path never exercised. State criterion, reason, and where each actually gets checked.
- `## Lessons`: at most two entries.
- Oracles re-run fresh: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0; `specfuse lint` over every feature folder reports zero ERROR.

**Do not touch.** Source, tests, rules, templates (T04-T07 own them);
`RETROSPECTIVE.md`'s `## Gate 1` section; gate 3's drafting — that is
`G2-PLAN`'s job, dispatched after this unit; `.git/`, secrets. This WU writes
only its close record.

**Verification.** The `plannext` gate set, plus this gate's `feature_oracle`
and the fresh oracle re-runs named above.

**Escalation triggers.** Emit `status: blocked` if the narrow-tier and broad-run
wall clocks cannot be measured on the same tree as `GATE-02.md`'s recorded
before — an incommensurable comparison is what gate 1's close had to guard
against, and saying the numbers do not compare is the honest move. Also block
if the gate's own execution provides no way to count broad runs that went red
on narrow-tier-passed work: that count is the gate's safety evidence, and
inferring it from the absence of complaints is not a measurement.
