---
id: FEAT-2026-0050/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 0
planned_cost_usd: 6.00
auto_close: true
auto_close_reasons: []
---

# Gate 1 close — retrospective, lessons, docs

**Objective.** Close gate 1 in one session: what the interview round-trip
actually produced, what generalizes, and what the docs must now say.

**Context.** FEAT-2026-0050/G1-CLOSE-INTERMEDIATE, gate 1, depends on T01–T03.
This feature is `autonomy_default: auto`, so generalizable lessons stage to
`LEARNINGS-pending.md` for human promotion — `close-i` forbids writing
`.specfuse/LEARNINGS.md` directly under this dial.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists and carries a `## Gate 1` section.
2. **Cost reconciliation.** Actual spend per WU from `events.jsonl`, compared
   against each unit's `planned_cost_usd` and the gate's `cost_budget_usd` of
   $27.00, with the delta stated. `G1-PLAN`'s $9.00 estimate was set above the
   $5.00 floor on the strength of `[FEAT-2026-0069/G2-CLOSE]`; record whether
   that held, because the next feature's planning budget is priced on it.
3. **The deferred-verification list**: for each acceptance criterion not
   verified in-loop, the criterion, why it was deferred, and where it actually
   gets checked — or the literal `(nothing — every acceptance criterion was
   verified in-loop)` if the list is empty.
4. **One thing this gate uniquely knows:** whether real operator answers arrive
   in a shape T03 can bind to questions. Record the observed reply shape
   verbatim, even if only one reply exists. Gate 2 is planned against this, and
   `[FEAT-2026-0034/G1-CLOSE/hand-check-the-invariants-before-automating-them]`
   records what it costs to plan a gate against an assumed shape rather than a
   measured one.
5. Generalizable lessons are staged to `LEARNINGS-pending.md`, or the close
   states explicitly that nothing generalizes and why.
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
