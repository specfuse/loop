---
id: FEAT-2026-0109/G3-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 8.00
auto_close_disabled: true
produces:
  - .specfuse/features/FEAT-2026-0109-tiered-verification/RETROSPECTIVE.md
---

# Gate 3 close — terminal close of FEAT-2026-0109

**Objective.** Terminal close of the feature: demonstrate gate 3's definition
of done, reconcile the whole feature's cost, and record the lessons. Measure; a
separate judge session reads the evidence and decides.

**Context.** Placeholder, scaffolded at feature-planning time so the linter
reads gate 1 as non-terminal. Gate 2's `plan-next` inserts gate 3's substantive
units above this entry in `PLAN.md`'s graph and sets this unit's real
`depends_on`, and gate 3's own definition of done and `feature_oracle` are
authored at that point. Binding when dispatched:
`.specfuse/rules/close-discipline.md`. The driver owns the terminal `PLAN.md`
and roadmap flips.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries `## Gate 3` and a `## Measurements` table: for each bullet of `GATE-03.md`'s definition of done, the command run in this session and its exit status, plus the gate's `feature_oracle` verdict.
- `## Cost analysis` reconciling `planned_cost_usd` across all three gates against `events.jsonl`, naming the delta and the restart count.
- `## What the loop did NOT verify`: criterion, reason, and where each actually gets checked.
- `## Consumer-visible contract changes`: enumerate them and add the `CHANGELOG.md` entry.
- `## Lessons`: at most two entries.
- Oracles re-run fresh: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0; `specfuse lint` over every feature folder reports zero ERROR.

**Do not touch.** Source, tests, rules, templates (gate 3's substantive units
own them); `.git/`, secrets. This WU writes only its close record and the
CHANGELOG entry its criteria name.

**Verification.** The `plannext` gate set, plus gate 3's `feature_oracle` and
the fresh oracle re-runs named above.

**Escalation triggers.** Emit `status: blocked` if this unit is dispatched
while still carrying this placeholder body — gate 2's `plan-next` is required
to have rewritten it against gate 3's real definition of done, and closing on a
placeholder would report against criteria nobody authored.
</content>
