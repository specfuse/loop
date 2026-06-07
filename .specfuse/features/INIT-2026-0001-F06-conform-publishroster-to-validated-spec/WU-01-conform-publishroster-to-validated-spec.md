---
id: INIT-2026-0001/F06/T01
type: implementation
model: claude-sonnet-4-6
status: draft
attempts: 0
---

# Conform publishRoster to validated spec

**Objective.** TODO

```yaml
correlation_id: INIT-2026-0001/F06
task_type: implementation
autonomy: review
component_repo: RestoManagerApp/Backend
depends_on: []
generated_surfaces:
  - RestoManager.Api/gen-src/Application/Interfaces/IRostersApplicationService.g.cs
  - RestoManager.Domain/gen-src/Services/Interfaces/IRosterService.g.cs
```

## Context

Part of **INIT-2026-0001**. F06 owns `publishRoster` (roster domain). Impl exists at
`RostersApplicationService.cs:47` — a real status transition to `Published` that sets `PublishedAt` and
emits `RosterPublishedEvent`. This task verifies conformance to the spec + closes drift.

- Operation spec: `restomanager-specs/api/specs/v3/domains/roster/operations/publish-roster.yaml`

**Drafted 2026-06-06T15:00:00Z; verified at draft time:**

1. Real impl present: `sed -n '47,57p' RostersApplicationService.cs` → transitions to `RosterStatus.Published`, sets `PublishedAt`, emits `RosterPublishedEvent`.

## Acceptance criteria

1. `PublishRoster` response + status code match `publish-roster.yaml`; emits `Roster.Published` per the async contract.
2. The published-state precondition (only a draft may be published) matches the spec's documented error responses.
3. `RostersApplicationServiceTests` covers publish happy-path + invalid-source-state; suite green.

## Do not touch

- `gen-src/` paths; `/business/`; branch protection; secrets.
- Sibling-task files (F07 lock, F08 archive).

## Verification

```sh
dotnet test RestoManager.Test --filter "FullyQualifiedName~RostersApplicationServiceTests" --verbosity normal
grep -nE "PublishRoster" RestoManager.Api/src/ApplicationService/RostersApplicationService.cs
```

## Escalation triggers

- If `publish-roster.yaml` mandates a precondition the impl does not enforce and adding it changes the contract, escalate `spec_level_blocker`.
- None beyond the four universal triggers.

