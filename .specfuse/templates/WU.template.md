---
id: FEAT-YYYY-NNNN/T01    # FEAT-YYYY-NNNN/TNN for substantive, /G<n>-(RETRO|LESSONS|DOCS|PLAN) for closing
type: implementation       # implementation | retrospective | lessons | docs | plan-next | close
model: claude-opus-4-7     # opus for foundational/forward-design; sonnet for mechanical/synthesis
status: pending            # draft | pending | ready | in_progress | in_review | done | blocked_human
attempts: 0
generated_surfaces: []     # OPTIONAL — paths to generated files this unit's acceptance depends on
---

<!--
Frontmatter notes (single-repo):

- `id` — the task-level correlation ID. Pattern and surfaces are defined in
  `.specfuse/rules/correlation-ids.md`. The driver and the linter both read this
  field; if it disagrees with the matching entry in PLAN.md's graph, the unit is
  rejected.
- `type` — drives which gate set in `.specfuse/verification.yml` the driver runs
  (`implementation` → `code`; `retrospective`/`lessons`/`docs` → `doc`;
  `plan-next` → `plannext`; `close` → `plannext`). Same concept as the
  orchestrator's `task_type`, kept under the loop's existing field name.
  `close` is a single-gate-only alternative to the four-WU closing sequence: it
  collapses retrospective + lessons + docs + terminal verdict into one session.
  One `close` WU must produce `RETROSPECTIVE.md`, append durable entries to
  `LEARNINGS.md`, reconcile docs and roadmap, and write the terminal feature-arc
  verdict. Only valid when the feature has exactly one gate; multi-gate features
  must use the `[retrospective, lessons, docs, plan-next]` sequence.
- `model` — the Claude model the driver dispatches this unit with. Foundational
  / forward-design units (notably `plan-next`) take Opus; mechanical and
  synthesis units take Sonnet.
- `status` — the unit's lifecycle position. `draft` is what `plan-next` writes
  for the next gate's units; the human arms them by flipping to `pending`. The
  driver writes `in_progress`, `done`, and `blocked_human`. Other values are
  reserved for future use; the linter accepts them but the driver doesn't write
  them today.
- `attempts` — incremented by the driver per fresh dispatch (max 3 before
  escalation). Authors leave it at `0`; the driver owns the counter.
- `cost_usd`, `input_tokens`, `output_tokens` — written by the driver at
  outcome time (PASS / BLOCKED / SPINNING) when cost tracking is enabled
  in `.specfuse/verification.yml` (top-level `cost_tracking: true`,
  default). Cumulative across the run's attempts on this WU. Authors
  leave them off; the driver owns them. Per-attempt breakdown lives in
  `events.jsonl`'s outcome event payload.
- `generated_surfaces` — OPTIONAL. Lists paths inside this repo to generated
  files (`_generated/`, `gen-src/`, or the repo's declared equivalent) that
  this unit's acceptance depends on existing and behaving correctly. Empty list
  or omitted for units that do not depend on generated code. Authoring this
  field at plan time makes the dependency reviewable before dispatch.

Dependencies live in PLAN.md's `gates[].work_units[].depends_on` graph, not
here — see `docs/methodology.md` §2 (one fact, one home).
-->

# <imperative title, e.g. "Add health-check endpoint">

This whole body below the frontmatter is what a fresh `claude -p` session receives.
Write it so a session with no memory can execute it from this file alone. The five
sections below are mandatory — the linter rejects a dispatchable WU that is missing
any. An optional `Objective` line above them is recommended but not enforced.

**Objective.** One sentence: what this unit produces.

**Context.** What this is part of, the correlation ID, and the specs/files that
ground it. Enough for a cold session to orient. Reference the binding rules in
`.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`) and the verification skill rather
than restating them.

**Acceptance criteria.** Explicit, testable statements of done. Write them so the
verification gates — and a reviewer — can judge them objectively. Avoid compound
criteria ("X and also Y"); split them so a single failure attributes to a single
line.

**Do not touch.** Generated directories (`_generated/`, `gen-src/`, or the repo's
declared equivalent), files owned by other work units in this gate, secrets,
`.git/`. The driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md` for the full list.

**Verification.** The gates that must pass. For `implementation` units these are
the `code` gates in `.specfuse/verification.yml` (tests, coverage ≥ 90%, zero
warnings, lint, security scan). Name anything unit-specific in addition. See
`.specfuse/skills/verification/SKILL.md` for how to run and interpret them.

**Escalation triggers.** Conditions under which you stop and emit `status: blocked`
in the RESULT block rather than pushing through (spec ambiguity, a required
modification of generated code, a missing dependency, a credential the unit
should not be reading). Blocked is a respectable outcome — `result-contract.md`
rule 4.
