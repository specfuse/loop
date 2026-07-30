---
id: FEAT-2026-0055/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
oracle_env: macos_local
produces:
  - .specfuse/templates/WU.template.md
  - plugins/specfuse/skills/authoring-work-units/SKILL.md
  - plugins/specfuse/skills/arm-gate/SKILL.md
model: sonnet
effort: medium
gate_set: code
driver_version: 0.7.0
started_at: 2026-07-30T15:22:00.266363+00:00
duration_seconds: 317.996
cost_usd: 0.675363
input_tokens: 38
output_tokens: 5021
---

# Surface the lint, delete the folklore

**Objective.** The per-WU deliverable contract's human surfaces point at the arm-time lint
instead of restating path-semantics folklore; authors stop copying warning comments into every
`produces:` block.

**Context.** Gate 1 of FEAT-2026-0055, depends on T03 (semantics must be unified before prose
declares them unified). Canonical direction per the FEAT-2026-0054/T04 lesson: `.specfuse/`
(templates) and `plugins/specfuse/skills/` (skills) are canonical; `specfuse/loop/data/` is the
mirror written only by `scripts/sync-scaffold.sh`. Binding rules:
`.specfuse/rules/result-contract.md`, `never-touch.md`.

Red-test exempt: documentation/template prose only — no runtime behavior
(`/authoring-work-units` §12 pure-data carve-out).

**Acceptance criteria.**

- `.specfuse/templates/WU.template.md`'s `produces` frontmatter note states the unified
  contract in one line (literal or glob, both gates, glob needs ≥1 match) and drops the
  dual-gate warning prose; grep for "passes presence and fails diff" returns nothing.
- `plugins/specfuse/skills/authoring-work-units/SKILL.md`: the produces-authoring rule points
  at `specfuse-lint`'s satisfiability/boundary checks as the arm-time verification, replacing
  any copy-the-warning-comment guidance.
- `plugins/specfuse/skills/arm-gate/SKILL.md`: step 3 gains one line — run `specfuse-lint` on
  the feature before walking drafts; WARN/ERROR findings are review input for the
  accept/revise/reject decision.
- `scripts/sync-scaffold.sh` run; `specfuse/loop/data/` mirror reflects the template change;
  mirror-consistency tests green.
- Full suite green.

**Do not touch.** Driver code (`specfuse/loop/*.py` — T01–T03 own it);
`specfuse/loop/data/**` directly (sync-only mirror); other features' folders; `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
`specfuse-lint .specfuse/features/FEAT-2026-0055-arm-time-wu-contract-lint` exits 0.

**Escalation triggers.** If deleting a folklore comment would remove information the lint does
not surface (a contract nuance T01–T03 missed), stop and emit `status: blocked` naming it —
the fix belongs in the lint, not in keeping the prose.
