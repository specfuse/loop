---
id: FEAT-2026-0020/T18
type: implementation
status: draft
attempts: 0
oracle_env: macos_local
planned_cost_usd: 0.30
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Operator runs FLIP-CHECKLIST (dry-run rehearsal) — human checkpoint, blocked_human by design

**Objective.** Record the operator's rehearsal of `FLIP-CHECKLIST.md`: walk every pre-flip
step, confirm each gating check passes (or its residual risk is accepted), and capture the
outcome as a dated rehearsal log. The visibility flip itself is NOT performed here — this WU
verifies readiness and is a **designed human checkpoint**.

**Context.** Terminal substantive WU of FEAT-2026-0020 gate 2; depends on WU-08
(`FEAT-2026-0020/T17`), which writes the checklist. The flip is operator-side (GitHub UI),
and the pre-flip gating includes steps the loop structurally cannot reach (the `gh`
issue/PR surface — `RETROSPECTIVE.md` §"What the loop did NOT verify" entry 4; the GitHub
edit-history residual, entry 6; the destructive phase-2 history rewrite, entry 5). A
dispatched `claude -p` session cannot run these, so this WU is expected to terminate
`blocked_human` until the operator records the rehearsal — that is the intended shape, not a
failure (`PLAN.md` "Notes": autonomy is `supervised`; destructive/flip ops are operator-side).

Correlation ID `FEAT-2026-0020/T18`. Grounding: `FLIP-CHECKLIST.md` (T08 output),
`RETROSPECTIVE.md` open actions, `history-scrub/RUNBOOK.md`.

Binding rules in `.specfuse/rules/` apply — `security-boundaries.md` (`gh`-auth from a
dispatched session is the documented-broken surface; do not attempt the flip).

Red-test exempt: human-checkpoint WU — its acceptance is an operator-recorded rehearsal
outcome, not a code behavior.

**Acceptance criteria.**

1. A rehearsal-log artifact exists (e.g. a `## Rehearsal` section appended to
   `FLIP-CHECKLIST.md` or a sibling `FLIP-REHEARSAL.md`) recording, per pre-flip step:
   pass / fail / residual-risk-accepted, with a date and the operator as the recorder.
2. Every pre-flip gating check from the checklist has a recorded disposition — none left
   blank. Any "residual-risk-accepted" entry names what risk and why (e.g. GitHub
   edit-history residual, org-names-only, no credentials).
3. The flip step itself is recorded as **NOT performed in-loop** — readiness only.
4. If the operator has not yet run the rehearsal at dispatch time, the WU emits
   `status: blocked` (→ `blocked_human`) with a `blocked_reason` naming the missing
   operator action — the designed checkpoint, not a defect.

**Do not touch.**

- The GitHub repo visibility setting — the actual flip is out-of-loop, operator-only.
- `gh` issue/PR mutation (documented-broken from a dispatched session).
- Gate-2 deliverable files except the rehearsal-log artifact this WU appends/creates.
- Generated directories, secrets, `.git/`. The driver owns all git — edit files only.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- `code` gates per `.specfuse/verification.yml` — pass unchanged on a docs-only edit.
- Existence (when not blocked): the rehearsal-log artifact exists and every pre-flip step
  carries a disposition (mechanically checkable — no blank disposition rows).
- Oracle environment: `macos_local` (the rehearsal walk); the actual flip's oracle is the
  GitHub UI, operator-side.

**Escalation triggers.**

1. **Operator rehearsal not yet run** → emit `status: blocked` (`blocked_human`). This is
   the expected default outcome until the operator records the walk; the driver halts and
   the operator re-arms via `/unblock-wu` after recording.
2. **A pre-flip gating check actually fails** (e.g. leak-scan CI gate red, history rewrite
   still open and not accepted) → emit `status: blocked` naming the failed check. Do NOT
   record a green rehearsal over a red gate.
3. **Operator attempts to fold the live flip into this WU** → decline and emit
   `status: blocked`; the flip is out-of-loop by design (`PLAN.md` "Notes").
