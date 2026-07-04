---
id: FEAT-2026-0025/G2-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 0.75
oracle_env: macos_local
---

# Gate 2 close — terminal close ceremony (drafted placeholder)

**Objective.** Close this feature in one session after gate 2's consumer-wiring WUs
complete: produce `RETROSPECTIVE.md`, append durable `LEARNINGS`, reconcile
docs/roadmap, write the feature-arc verdict, and include the `## Cost analysis` and
`## What the loop did NOT verify` sections. Driver-side terminal flips (gate →
passed, roadmap row → done, auto-archive) fire when `verdict: met`.

**Placeholder note.** This close is pre-declared at draft time so the gate graph is
valid and gate 1 reads as non-terminal. Gate 1's `plan-next` (G1-PLAN) inserts gate
2's substantive WUs BEFORE this close and updates this WU's `depends_on` to list
them. Until then it stays `status: draft` (unarmed).

**Context.** This is `FEAT-2026-0025/G2-CLOSE`. Read this feature's `events.jsonl`,
both gates' commits, PLAN.md's `roadmap_goal`, and the gate-1/gate-2 retrospectives.
Reference the binding rules under `.specfuse/rules/`; honor `result-contract.md` and
`never-touch.md`. The driver owns all git and the terminal `PLAN.md status` flip.

Set `verdict: met` ONLY when the roadmap_goal is genuinely achieved AND gate 2's
consumers actually load the LEARNINGS slice via `learnings_query` (with the
load-whole fallback) AND you have audited the `## Cost analysis` section against
`events.jsonl`.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists with per-WU outcomes across both gates, a feature-level
   summary, surprises, and a `## What I'd change` section.
2. Generalizable lessons are appended to `.specfuse/LEARNINGS.md` (or an explicit
   one-line note that none generalized).
3. Docs and the roadmap reflect what was built; this feature's roadmap row/detail
   are consistent with the delivered shape.
4. A `## Cost analysis` section is present, reconciling `planned_cost_usd` (PLAN.md +
   per-WU frontmatter) against actual spend (from `events.jsonl`), delta named.
5. A `## What the loop did NOT verify` section is present, enumerating each deferred
   acceptance criterion (why deferred, where verified). If retrieval *relevance
   quality* (does the slice actually contain the lessons a planner needed?) could
   only be judged by real planning sessions rather than unit tests, name that here.
6. `verdict:` is set to a value in the driver's `VERDICT_VALUES`.

**Do not touch.** Source files owned by the substantive WUs (do not re-edit to force
a pass), `.git/`, secrets. The driver owns all git and the terminal `PLAN.md status`
flip. See `.specfuse/rules/never-touch.md`.

**Verification.** The close gates the driver runs for `type: close`, plus the
hollow-pass guards: `assert_cost_analysis_section_when_met` (AC4), the
closing-deliverable presence checks (AC1/AC2), and `assert_terminal_flips_fired`
(fires on `verdict: met`).

**Escalation triggers.** If gate 2's substantive WUs did not produce their
deliverables, do NOT paper over it with `verdict: met` — emit `status: blocked`. If
cost reconciliation cannot be built from `events.jsonl`, emit `status: blocked`.
Blocked is respectable (`result-contract.md` rule 4).
