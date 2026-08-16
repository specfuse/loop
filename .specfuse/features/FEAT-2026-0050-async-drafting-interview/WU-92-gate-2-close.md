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
time so the linter reads gate 2 — not gate 1 — as this feature's terminal gate.
`G1-PLAN` has since inserted gate 2's four substantive units (T04–T07) before
it and updated `depends_on` to name them.

Gate 1 auto-closed, so its per-criterion deferred-verification list was never
enumerated — `RETROSPECTIVE.md` carries the `specfuse:autoclose-debt` marker
for T01–T03 (19 criteria). This close must reconcile that debt; auto-close
cannot.

`autonomy_default: auto`, so lessons stage to `LEARNINGS-pending.md`.

**Acceptance criteria.**

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
4. **Whether a real operator reply was ever observed, and in what shape.**
   `GATE-02-REVIEW.md` § Runtime probe records that none was as of gate 2's
   arming, and that gate 2's parsing criteria were drafted against a measured
   round-trip rather than a human. If that is still true at close, say so
   plainly — the parser is unvalidated against a human, and reporting it as
   validated is the failure `GATE-01.md`'s arming discipline names.
5. Gate 1's auto-close debt is reconciled: the 19 deferred criteria the
   `specfuse:autoclose-debt` marker names are each verified or carried into the
   deferred-verification list of criterion 2.
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
