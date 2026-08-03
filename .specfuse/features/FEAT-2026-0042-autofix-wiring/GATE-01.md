---
gate: 1
status: open
cost_budget_usd: 28.00
baseline:
  sha: f9d47a26252ab6d3a6e7fa831efafeaba7e8b7d9
  probed_at: 2026-08-03T23:02:08.182525+00:00
  failing: []
---

# Gate 1 — the decision layer, complete and incapable of acting

## Definition of done

Given a diagnosed finding, the system can decide correctly whether an automated fix
should be attempted — reading the per-component `autofix` dial, gating on confidence
and `fix_scope`, and respecting one-run-per-fingerprint and a daily cap held in
durable state — and `fix-bug` has a headless mode whose every halt maps to a recorded
outcome. **Nothing fires.**

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.
- Gate 2's substantive work units are drafted by `G1-PLAN`.

This gate is **non-terminal**: the closing sequence is `close-intermediate` followed
by `plan-next`. Gate 2 is terminal and carries a pre-declared `G2-CLOSE`.

## Cost budget

`cost_budget_usd: 28.00` — the $22.00 sum of WU estimates ($4.00 / $4.00 / $3.50 /
$4.50 / $6.00) plus one re-attempt of the largest WU ($6.00, `G1-PLAN`), per the
defensive padding the GATE template prescribes while the closing-WU retry defect
(#260) is open. The two closing WUs sit at the `planning-discipline.md` §5 floors
($4.50 `close-intermediate`, $6.00 `plan-next`).

## Why this gate cannot fire anything, and why that is the point

Every work unit here is a pure decision function, a state reader/writer, or a mode
that nothing yet invokes. That is deliberate on a feature whose failure mode is a
confidently-wrong pull request:

- every acceptance criterion is satisfiable with unit tests and **no side effects**;
- a human reads this gate's output and arms gate 2 before anything can act;
- if the predicate is wrong, it is wrong in a file, not in a repository.

**No work unit in this gate may invoke `fix-bug`, create a branch, open a pull
request, or call `gh` in a way that writes.** A WU that believes it needs to has
misread the gate boundary — that is gate 2's territory and an escalation here.

## The safety floor, restated because it outranks this gate

Auto-merge belongs to FEAT-2026-0048 and is impossible in this feature. No work unit
in either gate may merge a pull request, enable auto-merge, or push to a protected
branch. The ceiling is an unwanted PR on a branch. `G1-PLAN` must carry this
constraint into gate 2's drafts verbatim.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`. Gate 1 is
  satisfiable by construction because nothing fires. Fix *correctness* is not
  asserted anywhere and must not be.
- **Runtime probe for a default/severity flip (§4).** Not applicable to gate 1: no
  default changes, `autofix: "off"` remains the shipped default. **`G1-PLAN` must
  re-answer §4 for gate 2 rather than inherit this answer** — gate 2 introduces
  firing behaviour and that is exactly the case §4 exists for.
- **Flag-scope table (§3).** Not applicable: `autofix` already exists in the schema;
  this feature adds its consumer.

## Known limits, recorded so the close does not misread them

**Fix quality is not verified by this gate and cannot be.** The same inherent limit
FEAT-2026-0041 recorded for diagnosis quality applies here: criteria assert the
*decision* is right and the *mechanism* is sound, never that a generated patch is
correct. A close that lets a green gate read as verified fix quality has misreported
the feature.

**The dial is still inert at the end of this gate.** `autofix: "on"` will change
nothing until gate 2 ships. That is the intended state and should be stated plainly
in the close rather than read as an incomplete deliverable.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
