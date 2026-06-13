---
id: FEAT-2026-0015/G1-RETRO
type: retrospective
effort: low
status: pending
attempts: 0
planned_cost_usd: 0.30
---

# Gate 1 retrospective

**Objective.** Produce `RETROSPECTIVE.md` in this feature folder
covering Gate 1: what worked, what failed, what was surprising,
what generalizes (for the lessons WU to promote), and where the
plan-next WU should focus Gate 2.

**Context.** Correlation ID `FEAT-2026-0015/G1-RETRO`. Read this
feature's `events.jsonl` and the commits on the feature branch.
Synthesis against a concrete log, not new design. Reference the
binding rules under `.specfuse/rules/`; honor `result-contract.md`,
`never-touch.md`. The driver owns all git.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` has a Gate 1 section that, per substantive WU
   (T01, T02, T03): what worked, what failed and why, attempts taken,
   any rule/template/boundary missing or ambiguous, and the final
   per-WU `cost_usd` / `duration_seconds`.
2. A gate-level subsection records: total cost across G1 (substantive
   + closing), dispatch order, whether any WU spun, whether any
   re-arms happened.
3. **NEW for FEAT-2026-0015** — `## Cost analysis` subsection:
   per-WU table of `planned_cost_usd` vs actual `cost_usd` (from
   events.jsonl), delta % per WU, gate total delta %. Variance
   > 50% on any unit requires a one-paragraph rationale. This is
   the first dogfood of the new contract's cost-analysis section
   even though T08 ships the formal AC for it; G1-RETRO leads by
   example.
4. A `## What surprised us` section: anything the operator should
   notice about the closing-shape mechanics being authored against
   the OLD 4-WU sequence (this gate's own dogfood inversion).
5. The retrospective explicitly notes whether T01-T03 landed clean
   or whether helper-duplication (per authoring-work-units §10)
   surfaced — that rule was added based on FEAT-2026-0013's
   ship-fail-fail-fail-fail cycle, and Gate 1 is its first real test.

**Do not touch.** Source code (`loop.py`, `lint_plan.py`, templates,
skills) — this is the retrospective unit, it doesn't change behavior.
Other WU files, generated directories, secrets, `.git/`. The agent
writes `RETROSPECTIVE.md` only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in `.specfuse/verification.yml`
(file exists / something changed).

**Escalation triggers.**

1. **No evidence.** If `events.jsonl` is empty or missing entries for
   T01-T03, emit `status: blocked` — the retrospective can't be
   synthesized without dispatch records.
2. **Cost-analysis missing.** Per AC3, the `## Cost analysis`
   section is mandatory. Omit it and emit `status: blocked`.
