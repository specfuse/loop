---
id: FEAT-2026-0001/T01
type: implementation
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Add GET /health endpoint

**Objective.** Add a `GET /health` route returning `{status, version}` as JSON.

**Context.** Part of feature FEAT-2026-0001 (operators verify health without logs).
Add the route in the application's existing router module. Read `.specfuse/rules/`
before acting.

**Acceptance criteria.** `GET /health` responds 200 with a JSON body containing
`status: "ok"` and a `version` string sourced from the build. No new dependencies.

**Do not touch.** Generated directories, other routes, secrets, `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** If no router module exists yet, emit `status: blocked` —
that is a different unit of work, not this one.
