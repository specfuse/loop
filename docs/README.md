# Specfuse Loop — docs index

Start here:

- [`getting-started.md`](getting-started.md) — from `specfuse init` to a delivered
  feature, then how to operate a running loop (diagnose halts, arm gates, unblock
  WUs). Read this first.
- [`skills.md`](skills.md) — the Claude Code skills catalog, ordered by lifecycle
  phase (pick → draft → arm → diagnose → wrap).
- [`methodology.md`](methodology.md) — the canonical definition of the gate cycle:
  unit hierarchy, ownership split, the five-section work-unit contract,
  verification-as-oracle, auto-close, plan-next, LEARNINGS, and autonomy. Shared
  vocabulary between the loop and the orchestrator. Reference-grade.

`getting-started.md`, `skills.md`, `methodology.md`, and `concepts/` are also
shipped into target repos by `specfuse init`/`upgrade` (under `.specfuse/docs/`),
so an initialized project is self-documenting.

## Concepts (under `concepts/`)

- [`concepts/ralph-lineage.md`](concepts/ralph-lineage.md) — why the loop exists:
  the Ralph / Gas Town lineage and what the loop adds on top (planning rigor at
  work-unit granularity).
- [`concepts/architecture-addendum-gates-and-iterative-planning.md`](concepts/architecture-addendum-gates-and-iterative-planning.md)
  — the architectural extension that introduces the gate / closing-sequence /
  plan-next / learnings layer, and how it maps onto the orchestrator's state
  machine. The loop is the **near-term author** of these contracts.

## Binding rules (under `.specfuse/rules/`)

Read by every work-unit session before it acts; the `verification` skill
([`../.specfuse/skills/verification/SKILL.md`](../.specfuse/skills/verification/SKILL.md))
operationalizes them. The single-repo expression of the shared-vocabulary rules
ported from the orchestrator surface.

- [`result-contract.md`](../.specfuse/rules/result-contract.md) — the
  state-intent / act / verify / report cycle, and the RESULT-block format the
  driver consumes as the agent-to-driver interface.
- [`correlation-ids.md`](../.specfuse/rules/correlation-ids.md) — the
  `FEAT-YYYY-NNNN` and `FEAT-YYYY-NNNN/<task-id>` scheme, the surfaces an ID must
  appear on, and how the next ID is chosen.
- [`never-touch.md`](../.specfuse/rules/never-touch.md) — generated directories,
  secrets, and `.git/` internals, off-limits without exception.
- [`security-boundaries.md`](../.specfuse/rules/security-boundaries.md) — the
  posture for secrets, privileged access, authenticated tooling, and log hygiene.

## Authoring craft (under `.specfuse/skills/`)

The full skills catalog is [`skills.md`](skills.md). The reference docs that
inform authoring and conversion:

- [`authoring-work-units/SKILL.md`](../.specfuse/skills/authoring-work-units/SKILL.md)
  — how to fill the five-section WU contract well. Evidence-backed rules, each
  tied to a failure mode observed in a real run.
- [`feature-conversion/SKILL.md`](../.specfuse/skills/feature-conversion/SKILL.md)
  — bring an existing feature folder into conformance with the current scaffold's
  structural contract (the second half of the `--upgrade` story).

## Internal working notes (under `dev/`)

Not user-facing — historical drafts and implementation notes kept for provenance:

- [`dev/handoff-github-feature-pick.md`](dev/handoff-github-feature-pick.md)
- [`dev/wu-draft-loop-concurrency-lock.md`](dev/wu-draft-loop-concurrency-lock.md)
- [`dev/leak-scan-content-action.md`](dev/leak-scan-content-action.md)
