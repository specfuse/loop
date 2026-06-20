---
id: FEAT-2026-0028/G1-PLAN
type: plan-next
effort: high
status: pending
attempts: 0
planned_cost_usd: 2.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 plan-next — draft gate 2 (umbrella CLI rewire, interactive)

**Objective.** Author gate 2's substantive WU files (the umbrella `specfuse` CLI rewire
in the `specfuse/specfuse` repo), wire them into `PLAN.md`'s gate-2 graph with real
`depends_on`, set the terminal `G2-CLOSE` `depends_on`, and write `GATE-02-REVIEW.md`.

**Context.** This is `FEAT-2026-0028/G1-PLAN`, following G1-CLOSE-INTERMEDIATE. Gate 1
put docs in the seed and made `scaffold.py` write them. Gate 2 rewires the umbrella CLI
to call the scaffold API. **Gate 2 is cross-repo (lives in `specfuse/specfuse`) and
interactive — the loop driver runs in this repo and cannot dispatch/verify edits to the
sibling repo.** Draft the WUs as specs for that interactive work; mark clearly that their
verification happens in the umbrella repo (the close records it under "what the loop did
NOT verify"). `plan-next` takes the strongest model — see `docs/methodology.md` §7.

Gate 2's expected scope (refine against the retrospective):

- **`cmd_init` rewire** — `specfuse init <repo>` calls
  `specfuse.loop.scaffold.init(target, ci_check=...)` instead of printing curl-bash;
  refusal (`.specfuse/` exists) surfaces cleanly; `--dry-run` wired (escalate if the
  scaffold API has no dry-run path — decide preview semantics).
- **`cmd_upgrade` rewire** — `specfuse upgrade <repo>` calls `upgrade_specfuse(target)`
  (never-downgrade honored) then the pip-upgrade + `/plugin update` hint.
- **Tests** in the umbrella repo against the **real** scaffold API (editable
  `specfuse-loop`), replacing the stub-era cli tests; `--dry-run` writes nothing.
- **Dependency bump note** — the umbrella's `pyproject` dep stays `specfuse-loop>=0.2.0`
  until the coordinated release bumps it to `>=0.3.0` (OUT of this feature).

**Acceptance criteria.**

1. **Gate 2 WU files authored** (e.g. `WU-03-*.md`, `WU-04-*.md`) — each dispatchable
   form (five sections, `status: draft`, `planned_cost_usd`), but each **explicitly
   flagged interactive / cross-repo** in its Context (verified in `specfuse/specfuse`,
   not this loop run). Per-WU craft per `/authoring-work-units`.
2. **`PLAN.md` gate-2 graph updated** — real `id`/`file`/`depends_on` per WU, and the
   terminal `G2-CLOSE` `depends_on` set to all gate-2 substantive WUs.
3. **`GATE-02-REVIEW.md`** written — weighted toward doubt: decisions + rationale, an
   "if you check only three things" list, a roadmap-anchor check, open questions
   (notably the `--dry-run` preview semantics + the cross-repo verification boundary),
   each mapped to a draft WU.
4. **Lint clean** —
   `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0028-umbrella-cli-wiring`
   passes.
5. **No arming** — gate 2's WUs stay `draft`.

**Do not touch.** Gate 1's WUs and `GATE-01.md` status (driver owns gate flips); the
`specfuse/specfuse` repo itself (this WU only DRAFTS gate 2's specs, it does not edit the
umbrella); secrets; `.git/`.

**Verification.** `plannext` gate set (the linter, AC4) + AC1–AC3 existence checks. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If gate 1's retrospective implies the umbrella rewire should be
its own feature (not a gate of this one) — e.g. the cross-repo verification boundary is
too lossy to track here — surface it loudly in `GATE-02-REVIEW.md` and emit
`status: blocked` rather than drafting WUs the loop fundamentally cannot verify.
