---
id: FEAT-2026-0050/G2-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 6.00
auto_close_disabled: true
---

# Gate 2 terminal close

**Objective.** Close gate 2 and the feature: retrospective, lessons, docs, and
the terminal verdict.

**Context.** FEAT-2026-0050/G2-CLOSE, gate 2, terminal. Pre-declared at draft
time so the linter reads gate 2 — not gate 1 — as this feature's terminal gate;
`plan-next` inserts gate 2's substantive units before it and updates
`depends_on`, which is empty only until then.

`autonomy_default: auto`, so lessons stage to `LEARNINGS-pending.md`.

**Acceptance criteria.** Drafted by gate 1's `plan-next` alongside gate 2's
substantive units. At minimum this close must carry:

1. Cost reconciliation against `planned_cost_usd` and gate 2's budget, under
   a `## Cost analysis` heading in `RETROSPECTIVE.md`.
2. The deferred-verification list, or the literal `(nothing — every acceptance
   criterion was verified in-loop)`.
3. **Whether the feature actually removed the bottleneck it was filed for.** The
   measurable claim: a `drafting-needed` queue entry reaches a drafted folder
   without an interactive session. If no real feature was drafted end-to-end
   through this path before close, say so plainly rather than reporting the
   mechanism as proven — FEAT-2026-0080 closed `met_locally` on exactly that
   distinction and recorded it.
4. `specfuse lint --closing` exits 0 before this unit reports `complete`.

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
