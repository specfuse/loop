---
id: FEAT-2026-0113/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
---

# G1-PLAN — draft gate 2

**Context.** Gate 2 is classification and the write path. `PLAN.md`'s Notes carry
its sketch; this unit turns that into dispatchable work units, informed by what
gate 1's retrospective actually learned about marker shapes in the wild.

**Acceptance criteria.**

1. Gate 2's substantive work units are drafted into `PLAN.md`'s graph and written
   as `status: draft` files, and `GATE-02.md` gets its `feature_oracle` — the
   command that proves a triage run records severity in a repository that defines
   `severity:*` labels, and changes nothing in one that does not.
2. `GATE-02-REVIEW.md` is written — the review names the gate being **drafted**,
   not the one being closed (`assert_gate_review_exists`) — including an "if you
   check only three things" block.
3. The drafted units honour `PLAN.md`'s **Record precedence** section — marker
   authoritative, label a projection, marker written first. A drafted unit that
   reorders those is wrong rather than a variation.
4. The rubric reader is drafted as an **extraction** of `labels.py:267`'s existing
   `gh label list --json name,color,description` call, not a second listing, per
   this feature's Existing-mechanism search.
5. The open questions carried forward are named explicitly, including the one
   `PLAN.md` flags as uncertain: whether that extraction belongs in gate 2 at all
   or should have landed in gate 1.

**Do not touch.** Gate 1's work units and their files. Gate 3's shape beyond what
gate 2's outcome actually constrains. Any source file under `specfuse/`.

**Verification.** `specfuse lint .specfuse/features/FEAT-2026-0113-triage-severity`
exits 0.

**Escalation triggers.** If gate 1's retrospective says a marker shape regressed,
do not draft a write path on top of it — escalate instead, since gate 2's whole
premise is that the reader is safe.
