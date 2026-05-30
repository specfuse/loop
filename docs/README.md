# Specfuse Loop — docs index

- [`methodology.md`](methodology.md) — the canonical definition of the gate
  cycle: unit hierarchy, ownership split, the five-section work-unit contract,
  verification-as-oracle, plan-next, LEARNINGS, and autonomy. Shared vocabulary
  between the loop and the orchestrator.
- [`ralph-lineage.md`](ralph-lineage.md) — why the loop exists: the Ralph / Gas
  Town lineage and what the loop adds on top (planning rigor at work-unit
  granularity).
- [`architecture-addendum-gates-and-iterative-planning.md`](architecture-addendum-gates-and-iterative-planning.md)
  — the architectural extension that introduces the gate / closing-sequence /
  plan-next / learnings layer. The loop is the **near-term author** of these
  contracts: this is the loop's canonical copy of the addendum until the
  orchestrator's architecture document absorbs it.

## Binding rules (under `.specfuse/rules/`)

The rules below are read by every work-unit session before it acts; the
verification skill in [`../.specfuse/skills/verification/SKILL.md`](../.specfuse/skills/verification/SKILL.md)
operationalizes them. They are intentionally the single-repo expression of
the shared-vocabulary rules ported from the orchestrator surface.

- [`result-contract.md`](../.specfuse/rules/result-contract.md) — the
  state-intent / act / verify / report cycle, and the RESULT-block format the
  driver consumes as the agent-to-driver interface.
- [`correlation-ids.md`](../.specfuse/rules/correlation-ids.md) — the
  `FEAT-YYYY-NNNN` and `FEAT-YYYY-NNNN/<task-id>` scheme, the surfaces an ID
  must appear on, and how the next ID is chosen.
- [`never-touch.md`](../.specfuse/rules/never-touch.md) — generated directories,
  secrets, and `.git/` internals, off-limits without exception.
- [`security-boundaries.md`](../.specfuse/rules/security-boundaries.md) — the
  posture for secrets, privileged access, authenticated tooling, and log
  hygiene.
