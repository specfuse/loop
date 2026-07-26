# Gate-1 review — see `GATE-02-REVIEW.md`

`WU-91`'s AC7 and `GATE-01.md`'s definition of done both name this file. The driver names a
different one: `assert_gate_review_exists` (`specfuse/loop/loop.py:4005-4026`) computes the
expected filename from the **next** gate, `GATE-{this_gate+1:02d}-REVIEW.md`, so for a
gate-1 `plan-next` the file the closing-deliverable guard checks is
**`GATE-02-REVIEW.md`**.

The review artifact is written there in full. This file exists so the name `GATE-01.md`
promises also resolves, and so a reader arriving from `GATE-01.md` is not left thinking the
document was never written.

**→ [`GATE-02-REVIEW.md`](GATE-02-REVIEW.md)** — what gate 1 shipped, what changed from
`PLAN.md`'s gate 2 sketch and why, the §10 symbol enumeration, the runtime-probe failure
list, the per-WU cost estimates and the $34.00 reconciliation, the cross-repo contracts
table, and the seven open questions to decide before arming.

The same divergence is recorded in `FEAT-2026-0026` and `FEAT-2026-0027`, both of which
also failed an attempt on `assert_gate_review_exists: GATE-0N-REVIEW.md absent or empty`
before writing the driver-expected name. Three features have now paid for it. The durable
fix is a scaffold change — either `WU.template.md` and the gate template say
`GATE-{N+1}-REVIEW.md`, or the driver accepts both names — and it belongs in the loop's own
roadmap, not in another per-feature workaround. **Filed as issue #261.**
