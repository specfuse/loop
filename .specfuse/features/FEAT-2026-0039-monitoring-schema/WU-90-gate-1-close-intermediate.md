---
id: FEAT-2026-0039/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
auto_close: true
auto_close_reasons: []
---

# Gate 1 close-intermediate — retrospective + lessons + docs

**Objective.** Close gate 1: write `RETROSPECTIVE.md` (with `## Cost analysis` and
`## What the loop did NOT verify`), promote durable lessons to
`.specfuse/LEARNINGS.md`, and reconcile the docs the new validator and seed affect.
This is a non-terminal close — no feature-arc verdict, no terminal flips.

**Context.** This is `FEAT-2026-0039/G1-CLOSE-INTERMEDIATE`. Gate 1 shipped the
monitoring contract: T01 (`specfuse/loop/lint_monitoring.py` +
`validate_monitoring`), T02 (`.specfuse/monitoring.yml.example` +
`docs/concepts/monitoring-schema.md`), T03 (the `.specfuse/scripts/` shim, scaffold
seeding, and the `monitoring-example-lint` gate). Read this feature's
`events.jsonl`, the gate's commits, `PLAN.md`, and root `.specfuse/LEARNINGS.md`.
Reference the binding rules under `.specfuse/rules/`; honor `result-contract.md`
and `never-touch.md`. The driver owns all git.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists with per-WU outcome (T01, T02, T03) — what worked,
   what failed, attempts, final cost — plus a gate-level summary, surprises, and a
   `## What I'd change` section.
2. **`## Cost analysis`** present, reconciling `planned_cost_usd` (from `PLAN.md`
   and per-WU frontmatter) against actual spend (from `events.jsonl`), with the
   delta named. Gate 1 planned $18.00 total; state the actual and the direction of
   the miss.
3. **`## What the loop did NOT verify`** present, enumerating each acceptance
   criterion whose verification was deferred, with why and where it actually gets
   verified. Required even when empty — write
   `(nothing — every acceptance criterion was verified in-loop)` if so. Gate 1 is
   expected to be fully in-loop verifiable (pure-Python validator, a static example,
   scaffold seeding — all testable locally), so a non-empty list here is itself a
   finding worth explaining.
4. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or an explicit
   one-line note that none generalized. Candidates to weigh, not to assume:
   whether "a gate for an opt-in artifact validates the shipped example, not a live
   config" generalizes beyond monitoring; and whether the T01→T02 oracle-ownership
   split (the validator wins, the example escalates) is a reusable rule for any
   producer/consumer WU pair inside one gate.
5. Docs reconciled: confirm `docs/concepts/monitoring-schema.md` matches what
   shipped, and check whether the scripts inventory or `docs/` index needs the new
   shim listed. A one-line note suffices if no change is needed.
6. **The FEAT-2026-0040 handoff is recorded.** State plainly what the harvester now
   inherits — the neutral check-type vocabulary, `validate_monitoring` as a
   reusable loader, and the deliberately-deferred GitHub Actions workflow — so 0040's
   drafting does not re-derive it from commit archaeology.

**Do not touch.** Gate 1's WU source (T01/T02/T03 — the gate is done; do not
re-edit to force a pass); `GATE-01.md` status (the driver owns gate flips); gate
2's WU drafts (G1-PLAN owns those); `.git/`, secrets. May create/edit
`RETROSPECTIVE.md`, append to `.specfuse/LEARNINGS.md`, and touch docs. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set the driver runs for `type: close-intermediate`,
plus the closing-deliverable guards: `assert_cost_analysis_section_when_met` (AC2)
and the retrospective/lessons presence checks (AC1/AC4).

**Escalation triggers.** If any of T01/T02/T03 did not produce its declared
deliverable, do NOT paper over it — emit `status: blocked` naming the gap. If the
cost reconciliation cannot be built because `events.jsonl` lacks outcome rows, emit
`status: blocked` rather than estimating. Blocked is respectable
(`result-contract.md` rule 4).
