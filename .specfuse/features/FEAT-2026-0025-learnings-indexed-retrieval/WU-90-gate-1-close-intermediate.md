---
id: FEAT-2026-0025/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 1.50
---

# Gate 1 close-intermediate — retrospective + lessons + docs

**Objective.** Close gate 1: write `RETROSPECTIVE.md` (with `## Cost analysis` and
`## What the loop did NOT verify`), promote durable lessons to
`.specfuse/LEARNINGS.md`, and reconcile any docs the retrieval primitive affects.
This is a non-terminal close — no feature-arc verdict, no terminal flips.

**Context.** This is `FEAT-2026-0025/G1-CLOSE-INTERMEDIATE`. Gate 1 shipped the
retrieval primitive: T01 (`parse_entries` + BM25 `rank` in
`.specfuse/scripts/learnings_query.py`) and T02 (CLI + `should_load_whole`
threshold). Read this feature's `events.jsonl`, the gate's commits, and root
`.specfuse/LEARNINGS.md`. Reference the binding rules under `.specfuse/rules/`;
honor `result-contract.md` and `never-touch.md`. The driver owns all git.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists with per-WU outcome (T01, T02) — what worked / what
   failed / attempts / final cost — a gate-level summary, surprises, and a
   `## What I'd change` section.
2. **`## Cost analysis`** present, reconciling `planned_cost_usd` (from PLAN.md and
   per-WU frontmatter) against actual spend (from `events.jsonl`), with the delta
   named.
3. **`## What the loop did NOT verify`** present, enumerating each acceptance
   criterion whose verification was deferred. Gate 1 is fully in-loop verifiable
   (pure-Python primitive + unit tests), so this section is expected to read
   `(nothing — every acceptance criterion was verified in-loop)`. Required even
   when empty.
4. Generalizable lessons are appended to `.specfuse/LEARNINGS.md` (or an explicit
   one-line note that none generalized). Candidate: keep retrieval primitives
   stdlib-only and consumer-agnostic so the query-assembly decision can be deferred
   to the consumer gate.
5. Docs reconciled if the primitive warrants a mention (e.g. `docs/` or the
   scripts inventory); otherwise a one-line note that no doc change is needed.

**Do not touch.** Gate 1's WU source (T01/T02 — the gate is done; do not re-edit to
force a pass), `GATE-01.md` status (driver owns gate flips), `.git/`, secrets. May
create/edit `RETROSPECTIVE.md`, append to `.specfuse/LEARNINGS.md`, and touch docs.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set the driver runs for `type: close-intermediate`,
plus the closing-deliverable guards: `assert_cost_analysis_section_when_met` (AC2)
and the retrospective/lessons presence checks (AC1/AC4).

**Escalation triggers.** If T01 or T02 did not produce its deliverable, do NOT paper
over it — emit `status: blocked` naming the gap. If the cost reconciliation cannot
be built because `events.jsonl` lacks outcome rows, emit `status: blocked`. Blocked
is respectable (`result-contract.md` rule 4).
