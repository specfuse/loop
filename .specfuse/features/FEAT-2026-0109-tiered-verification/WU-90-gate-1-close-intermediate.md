---
id: FEAT-2026-0109/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 1
planned_cost_usd: 4.50
oracle_env: macos_local
auto_close_disabled: true
produces:
  - .specfuse/features/FEAT-2026-0109-tiered-verification/RETROSPECTIVE.md
model: opus
effort: high
gate_set: plannext
driver_version: 0.16.0
started_at: 2026-09-08T12:40:57.906724+00:00
duration_seconds: 942.355
cost_usd: 3.114668
input_tokens: 76
output_tokens: 31050
---

# Gate 1 close — measure what the lazy probe actually saved, and what it cost

**Objective.** Non-terminal close of gate 1: demonstrate each behaviour in
`GATE-01.md`'s definition of done in this session, measure the saving against
the recorded baseline, and record the lessons. Measure; do not decide a
feature-level verdict — gate 1 is not the terminal gate.

**Context.** Depends on T01-T03. Binding: `.specfuse/rules/close-discipline.md`.
Run `specfuse lint --closing` before reporting `complete`.

**The measurement that matters is a comparison, not a number.** The claim is
that verification stopped running when nothing was wrong. Evidence is the
`code`-set wall clock on a green gate entry before and after — the recorded
before is roughly 3 minutes per entry, from five probes across the
FEAT-2026-0101 run that each returned `failing: []` (`PLAN.md` § Notes) — plus
a count of how many times attribution actually fired during this gate's own
execution. If attribution fired zero times here, say so plainly: it means the
happy path was measured and the failure path was not, and the close must not
imply otherwise.

**The cost half is not optional.** `PLAN.md` accepts one wasted dispatch when
the tree is pre-broken. Report whether that occurred in this gate, and if it
did, what it cost. A close that reports only the saving is reporting half a
trade.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries `## Gate 1` and a `## Measurements` table: for each bullet of `GATE-01.md`'s definition of done, the command run in this session and its exit status; the `code`-set wall clock on a green gate entry before and after, with the percentage stated; and the number of times attribution fired during this gate.
- This gate's `feature_oracle` verdict recorded in `## Measurements` — required by the closing lint (FEAT-2026-0101/T02) whenever the gate declares one.
- `## Retrospective`: whether the lazy probe ever attributed a failure to the wrong side, and whether the once-per-gate bound held.
- `## Cost analysis` reconciling `planned_cost_usd` ($18.00, gate 1 only) against `events.jsonl`, naming the delta and the restart count.
- `## What the loop did NOT verify`: at minimum, the failure path if attribution never fired, and the CI fast path that `PLAN.md` scopes out. State criterion, reason, and where each actually gets checked.
- `## Lessons`: at most two entries.
- Oracles re-run fresh: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0; `specfuse lint` over every feature folder reports zero ERROR.

**Do not touch.** Source, tests, rules, templates (T01-T03 own them); gate 2's
drafting — that is `G1-PLAN`'s job, dispatched after this unit; `.git/`,
secrets. This WU writes only its close record.

**Verification.** The `plannext` gate set, plus this gate's `feature_oracle`
and the fresh oracle re-runs named above.

**Escalation triggers.** Emit `status: blocked` if the before/after wall-clock
comparison cannot be made on the same tree — an incommensurable comparison is
what FEAT-2026-0102's close had to caveat, and the honest move is to say the
numbers do not compare rather than to present them as if they do.
</content>
