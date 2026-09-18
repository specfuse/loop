---
id: FEAT-2026-0113/G2-PLAN
type: plan-next
status: draft
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
---

# G2-PLAN — draft gate 3

**Context.** Gate 3 is backfill: the 31 measured issues that carry a triage marker
with no severity field, which nothing revisits because the marker is the
idempotency key and it is already written. `PLAN.md`'s Notes carry the sketch —
an explicit mode, never part of a normal run. This unit turns it into dispatchable
work units, informed by what gate 2's retrospective learned about the write path
in practice.

**Acceptance criteria.**

1. Gate 3's substantive work units are drafted into `PLAN.md`'s graph and written
   as `status: draft` files, and `GATE-03.md` gets its `feature_oracle` — the
   command that proves an already-marked, severity-less issue is re-read and
   recorded under the explicit mode, and untouched without it.
2. `GATE-03-REVIEW.md` is written — the review names the gate being **drafted**,
   not the one being closed (`assert_gate_review_exists`) — including an "if you
   check only three things" block and an explicit `open_questions:` list.
3. The drafted units honour `PLAN.md`'s **Record precedence**: marker
   authoritative, label a projection, marker written first. A backfill unit that
   labels an issue without first amending its marker is wrong rather than a
   variation.
4. The drafted units state how a backfill run bounds its blast radius — what
   selects the issues it touches, and what stops it re-writing a marker that
   already carries a severity.
5. Gate 1's carried residual is resolved or explicitly re-carried: no oracle in
   this feature has yet read a real issue body outside this repository, and gate 3
   is the first surface that reads already-marked issues.

**Do not touch.** Gate 1's and gate 2's work units and their files. Any source
file under `specfuse/`. `rules.bugs.min_severity` — where the floor sits stays the
operator's, in gate 3 as in gate 2.

**Verification.** `specfuse lint .specfuse/features/FEAT-2026-0113-triage-severity`
exits 0.

**Escalation triggers.** If gate 2's retrospective says the opt-out equality did
not hold, do not draft a backfill on top of it — escalate instead, since a
backfill amends markers in bulk and the write path it amends them with must be
known safe first.
