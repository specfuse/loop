---
id: FEAT-2026-0050/G1-PLAN
type: plan-next
status: done
attempts: 1
planned_cost_usd: 9.00
model: opus
effort: high
gate_set: plannext
driver_version: 0.12.1
started_at: 2026-08-16T12:53:54.664708+00:00
duration_seconds: 1173.957
cost_usd: 6.368013
input_tokens: 110
output_tokens: 44143
---

# Draft gate 2 and write its arming review

**Objective.** Draft gate 2's substantive work units from what gate 1 actually
established, and write `GATE-02-REVIEW.md`.

**Context.** FEAT-2026-0050/G1-PLAN, gate 1, depends on
G1-CLOSE-INTERMEDIATE. Gate 2 extends `/draft-feature` with an
answered-questions mode (D2) and wires `FeatureProvider` to dispatch it.

The budget here is **$9.00**, deliberately above the $5.00 floor.
`[FEAT-2026-0069/G2-CLOSE]` records a `plan-next` that cost $16.44 and bought a
gate running 4 WUs, 0 failures, $4.43 against $12.00 — because it probed at
planning time and handed the next gate an enumerated problem list. That is the
shape wanted here: gate 2 touches a skill whose current hard rule is that it
never writes without a live human, and the cheap version of this unit produces a
gate that discovers that at dispatch.

**Acceptance criteria.**

1. Gate 2's substantive work units are drafted into `PLAN.md`'s graph **before**
   the pre-declared `G2-CLOSE`, with `depends_on` edges, and `G2-CLOSE`'s own
   `depends_on` updated to name them.
2. Each drafted unit follows `/authoring-work-units`, including the
   red-test-first rule: a named scoped test that fails on HEAD before the unit
   runs.
3. **The units are drafted against gate 1's measured reply shape**, not an
   assumed one — the retrospective's record of what a real answer looked like is
   cited in the gate 2 units that parse or consume it.
4. `GATE-02-REVIEW.md` is written, carrying the open questions a human must
   settle at arming. At minimum: whether restating `/draft-feature`'s
   "never writes without a live human" rule as "never writes without answers"
   is acceptable to the humans who rely on it (D2 asserts it is; the arming
   review is where that gets challenged rather than assumed).
5. The provider-wiring overlap flagged in `PLAN.md`'s Notes — one file touched
   by both gates — is checked against `driver_edit.is_driver_module_path`: if a
   gate 2 unit would edit the driver's importable surface, say so in the review,
   since a unit that does halts the run for a restart (FEAT-2026-0075).
6. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Any surface outside this feature's folder except the staged
`LEARNINGS-pending.md` this close is required to write. No source file under
`specfuse/`, no skill, no rule, no other feature's folder — a closing session
that edits the code it is judging cannot judge it.

**Verification.** `specfuse lint --closing` exits 0, and
`python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0050-async-drafting-interview`
exits 0. Run the full gate set with `./scripts/smoke-test.sh` unsandboxed — a
sandboxed run hits unrelated network restrictions during pip build-dependency
resolution.

**Escalation triggers.** Report `status: blocked` rather than writing a verdict
you cannot support: if the cost data needed for reconciliation is absent from
`events.jsonl`, if an acceptance criterion cannot be checked without a surface
this unit may not touch, or if the honest verdict is not `met` and the reason
does not fit the hedged-verdict record's shape.
