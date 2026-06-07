---
id: FEAT-2026-0005/G1-DOCS
type: docs
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.718378
input_tokens: 323
output_tokens: 13512
---

# Gate 1 documentation update

**Objective.** Reconcile docs and roadmap with what gate 1 delivered (the `close` WU type).

**Context.** Read the gate's commits and `RETROSPECTIVE.md`. Update this feature's
row/section in `.specfuse/roadmap.md`. Update `docs/methodology.md` §3 (work-unit types)
and §6 (the gate cycle) to mention the single-gate `close` option, and the
`draft-feature` skill if it should emit a `close` WU for single-gate features.

**Acceptance criteria.** Docs describe the delivered `close` type and its single-gate-only
constraint; the roadmap reflects gate 1's completion.

**Do not touch.** Source behaviour — documents, does not change code. `lint_plan.py`,
`loop.py`, `WU.template.md` (owned by T01), generated directories, secrets, `.git/`.

**Verification.** The `doc` gates.

**Escalation triggers.** If a doc change implies a code change is needed, raise it in the
RESULT block rather than changing code here.
</content>
