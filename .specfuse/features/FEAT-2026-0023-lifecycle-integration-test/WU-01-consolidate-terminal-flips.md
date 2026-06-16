---
id: FEAT-2026-0023/T01
type: implementation
model: opus
effort: high
status: done
attempts: 1
planned_cost_usd: 2.00
produces: tests/test_terminal_flip_ownership.py
produces_driver_helper: apply_terminal_flips
duration_seconds: 424.455
cost_usd: 3.361127
input_tokens: 9635
output_tokens: 25147
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Consolidate terminal-state ownership into one driver-side owner

**Objective.** Make a single driver-side function the authoritative owner of
every terminal flip — `PLAN.md status -> done`, terminal `GATE status ->
passed`, roadmap row `-> done`, and auto-archive — called identically by BOTH
the dispatched-close path and the auto-close path. This closes #49 structurally:
the terminal auto-close currently leaves `PLAN.md status: active` because only
the normal path's *agent* flips PLAN.md and the auto-close path runs no agent.

**Context.** This is `FEAT-2026-0023/T01`. Today terminal state is applied in
scattered places:

- `fire_terminal_flips` (loop.py:1488) flips the terminal GATE and the roadmap
  row + calls `auto_archive_feature` — but never touches `PLAN.md`.
- In the **normal** close path, the close WU's *agent* flips `PLAN.md -> done`
  as an acceptance criterion (see any close WU body).
- The **auto-close** path (`maybe_auto_close_terminal`, loop.py:1674) writes the
  stub retrospective + marks the close WU done, then the caller invokes
  `_fire_and_verify_terminal_flips` (loop.py:1805) → `fire_terminal_flips`.
  Nobody flips `PLAN.md`, so the post-pass invariant
  `assert_terminal_flips_fired` (loop.py:2331) — which only checks GATE +
  roadmap + archive anchor — passes, but `PLAN.md` stays `active` and the
  driver's separate PLAN-consistency check halts.

Make `fire_terminal_flips` (or a renamed `apply_terminal_flips` it delegates to)
ALSO flip `PLAN.md status -> done`, idempotently, as part of the same modified-
paths set it already returns. Then the auto-close path gets the PLAN flip for
free (it already calls `_fire_and_verify_terminal_flips`), and the normal path
no longer depends on the agent doing it. Respect the existing hedged-verdict
revert (loop.py ~2785) that flips `PLAN.md` back to `active` when the verdict
does not permit terminal flips — the driver flip must be gated on the same
`verdict_permits_terminal_flips` condition so a hedged close does not flip
PLAN to done.

Reference the binding rules under `.specfuse/rules/`. The driver owns git; edit
files only.

**Acceptance criteria.**
1. **Red test (fails on HEAD).** New test file
   `tests/test_terminal_flip_ownership.py::test_auto_close_terminal_flips_plan_done`
   drives the terminal auto-close path against a synthetic feature in a tmp repo
   and asserts `PLAN.md` ends at `status: done`. This **fails on HEAD** — the
   auto-close path leaves it `active` (the #49 shape).
2. `fire_terminal_flips` flips `PLAN.md status -> done` (idempotent: a no-op when
   already `done`), gated on `verdict_permits_terminal_flips(wu.verdict)` so a
   hedged/non-met verdict does NOT flip PLAN to done. The PLAN path is added to
   the returned modified-paths list so the existing bookkeeping commit includes
   it.
3. Both close paths converge on this one owner: confirm the dispatched-close
   path (loop.py ~2770 close branch) and the auto-close path
   (`_fire_and_verify_terminal_flips`) both reach the PLAN flip via
   `fire_terminal_flips`, with no second place writing `PLAN.md status`.
4. **Auto-close green path** — `test_auto_close_terminal_flips_plan_done` passes
   after the edit: PLAN `done`, GATE `passed`, roadmap row `done`.
5. **Dispatched-close path preserved** —
   `test_dispatched_close_flips_plan_done`: a normal close WU passing with
   `verdict: met` ends with PLAN `done` via the driver (no longer dependent on
   the agent's edit).
6. **Hedged verdict does not flip** —
   `test_hedged_verdict_leaves_plan_active`: a close WU whose verdict does not
   permit terminal flips leaves PLAN `active` (existing revert behavior intact).
7. **Doc reconciliation.** The close-WU authoring guidance that instructs the
   agent to "flip PLAN.md status to done" is updated in
   `.specfuse/skills/draft-feature/SKILL.md` and
   `.specfuse/skills/authoring-work-units/SKILL.md` to state the **driver** owns
   the terminal PLAN flip (the agent need not, and a manual flip is redundant).
8. **Existence check.** `python3 -c "from loop import fire_terminal_flips"`
   succeeds and the new test file exists and is non-empty.

**Do not touch.** These files change: `.specfuse/scripts/loop.py`,
`.specfuse/skills/draft-feature/SKILL.md`,
`.specfuse/skills/authoring-work-units/SKILL.md`, and one new test file
`tests/test_terminal_flip_ownership.py`. Do NOT modify `auto_archive_feature`,
`assert_terminal_flips_fired`, `ensure_feature_branch` (T03 owns it), or
`.specfuse/verification.yml`. Do NOT edit existing WU files, secrets, `.git/`.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, plus the
red→green proofs in AC 1/4/5/6 and the smoke import in AC 8.

**Escalation triggers.**
1. **Completeness.** If `fire_terminal_flips` does not flip `PLAN.md` after your
   edits, emit `status: blocked` — do not claim complete.
2. **Hedged-verdict regression.** If the PLAN flip fires regardless of verdict
   (flipping a hedged close to done), stop and emit `status: blocked` — the flip
   must be gated on `verdict_permits_terminal_flips`.
3. **Split ownership.** If after your edits `PLAN.md status` is still written in
   more than one place (e.g. the agent AC plus the driver), the consolidation is
   incomplete — surface it; redundant idempotent writes are acceptable only if
   the driver is unambiguously authoritative.
