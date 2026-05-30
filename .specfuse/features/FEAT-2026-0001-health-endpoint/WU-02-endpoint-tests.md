---
id: FEAT-2026-0001/T02
type: implementation
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Test the /health endpoint

**Objective.** Add tests covering the `/health` endpoint's contract.

**Context.** Depends on the endpoint from FEAT-2026-0001/T01 already existing. Read
`.specfuse/rules/` and the verification skill before acting.

**Acceptance criteria.** Tests assert 200, `status: "ok"`, and a non-empty `version`.
Coverage for the route file is ≥ 90%.

**Do not touch.** The endpoint implementation (this unit only adds tests), generated
directories, secrets, `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** If the endpoint's contract is ambiguous, emit blocked rather
than guessing.
