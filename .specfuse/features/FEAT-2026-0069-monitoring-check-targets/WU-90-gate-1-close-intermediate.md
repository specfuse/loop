---
id: FEAT-2026-0069/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
auto_close_disabled: true
---

# Gate 1 close-intermediate — retrospective + lessons + docs

**Objective.** Close gate 1: write `RETROSPECTIVE.md` (with `## Cost analysis` and
`## What the loop did NOT verify`), promote durable lessons to `.specfuse/LEARNINGS.md`,
reconcile the docs the new axis affects, and enumerate the consumer-visible contract
change for human acknowledgment. This is a non-terminal close — no feature-arc verdict,
no terminal flips.

**Context.** This is `FEAT-2026-0069/G1-CLOSE-INTERMEDIATE`. Gate 1 shipped the check-target
axis: T01 (validation of `targets` when present), T02 (migration of every shipped YAML
surface plus the `## Check targets` doc section), T03 (the contract flip making `targets`
required on `dlq`, plus the minimal discovery reference-implementation carry), T04 (the
`queue-stalled` check type). Read this feature's `events.jsonl`, the gate's commits,
`PLAN.md`, and root `.specfuse/LEARNINGS.md`.

`auto_close_disabled: true` is set deliberately: AC5 blocks on human acknowledgment of a
breaking contract change, and the auto-close predicate must not be able to skip it.

Binding rules under `.specfuse/rules/` apply — `close-discipline.md` especially. The
driver owns all git.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists with per-WU outcome (T01–T04) — what worked, what failed,
   attempts, final cost — plus a gate-level summary, surprises, and a `## What I'd change`
   section.
2. **`## Cost analysis`** present, reconciling `planned_cost_usd` (from `PLAN.md` and
   per-WU frontmatter) against actual spend (from `events.jsonl`), with the delta named.
   Gate 1 planned $21.00 total ($11.00 substantive + $10.00 planning). State the actual
   and the direction of the miss.
3. **`## What the loop did NOT verify`** present, enumerating each acceptance criterion
   whose verification was deferred — the criterion, why it was deferred (loop-sandbox
   limit, cross-repo coordination, real-system access), and where verification actually
   happens. Required even when empty; write
   `(nothing — every acceptance criterion was verified in-loop)` if so. If the list
   exceeds 2 entries **or** 30% of the gate's criteria, flag the gate's sizing under
   `## What I'd change`.
   **Two entries are known at drafting time and must appear unless gate 1 actually
   verified them:**
   - `/derive-monitoring` still emits N components for a deployable carrying N triggers.
     Gate 1 makes the *schema* able to express the right answer; it does not make
     discovery able to produce it. Verified in gate 2.
   - The issue's claim that all target coordinates are mechanically extractable
     (subscription names from trigger attributes, function names from the
     `[Function(nameof(...))]` form, cron and IANA timezone from named constants) is
     confirmed only against a repo outside this tree. Gate 1 verifies nothing about it.
4. **Oracles re-run fresh** (`close-discipline.md` §1): re-run every oracle this gate's
   criteria name — the full `code` gate set, `python3 .specfuse/scripts/lint_monitoring.py
   .specfuse/monitoring.yml.example`, and `cmp` on the two example copies — reading exit
   codes directly. Do **not** trust a producing WU's self-report.
5. **Consumer-visible contract changes** (§3): this is **not** `n/a`. Enumerate every
   addition, removal, and rename across T01–T04 — at minimum that `dlq` checks gained a
   **required** `targets` field (a breaking schema change), that `queue-stalled` is a new
   check type, and that `error-logs`/`http-5xx` now reject a field they previously
   ignored. Block on human acknowledgment.
6. Durable lessons promoted to `.specfuse/LEARNINGS.md`, tagged
   `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`. Candidates worth weighing — promote what
   generalizes, not everything:
   - Whether expand → migrate → contract should be the *named default* for any breaking
     change to a schema this repo's own gates validate, given that a flip-first ordering
     is unsatisfiable by construction under FEAT-2026-0051's preflight baseline probe.
   - Whether a fixture that cannot express the bug class it guards (one trigger per
     deployable, when the failure needs N) is a recognizable and preventable authoring
     defect — this is the second time 0039's surface has produced that lesson.
7. `docs/concepts/monitoring-schema.md` reflects what actually shipped, including the
   final required/optional matrix per check type. If T02 wrote "targets are not yet
   required on `dlq`" and T03 then made them required, this close fixes the stale
   sentence.
8. The feature's roadmap detail section reflects gate 1's real outcome.
9. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0069-monitoring-check-targets`
   passes (the cost-delta WARN documented in `PLAN.md`'s Notes is expected and
   acceptable while gate 2's WUs are undrafted).

**Do not touch.** Gate 1's WU source (T01–T04 — the gate is done; do not retro-edit their
bodies or acceptance criteria). Gate 2's WU files — `G1-PLAN` drafts those, not this WU.
`PLAN.md`'s `status` field — the driver owns terminal flips. `.git/`, secrets. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set the driver runs for `type: close-intermediate`, plus
the fresh oracle re-runs named in AC4 and the plan lint in AC9.

**Escalation triggers.** Emit `status: blocked` if any of T01–T04 did not produce its
declared `produces:` files, if a fresh oracle re-run disagrees with a WU's self-reported
outcome (say which, and by how much), or if the human acknowledgment required by AC5 is
unavailable in this session — a breaking contract change must not be closed on silence.
Blocked is a respectable outcome (`result-contract.md` rule 4).
</content>
