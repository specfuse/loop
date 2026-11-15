<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

<!--
PROMPT.md — the agent instruction for the derive-monitoring skill.

INTENDED USE: run interactively. Start `claude` in the target repo root and
ask it to run the derive-monitoring skill, or paste this prompt's body into
the session. The skill's whole value is conducting the batched question
round (which environments exist, provider bindings, credential env-var
names, invariant queries, dial loosening); piping this file via
`claude -p < PROMPT.md` consumes stdin so the skill cannot ask and silently
degrades to the non-interactive `[gap]` fallback — that fallback exists for
CI / dispatched sessions where no user is reachable, not as the intended
invocation.

This prompt operationalizes the method documented in
.specfuse/skills/derive-monitoring/SKILL.md. Read both before changing either.
-->

You are drafting a candidate `.specfuse/monitoring.yml` (plus a drafted
`.specfuse/monitoring.overrides.yml` and a filled-in reading of
`monitoring-secrets-checklist.md`) for the repository you are currently
invoked in. Your job: **draft** the files based on evidence in the repo, ask
the user only what evidence cannot answer, and present a reconciliation
report. You do NOT write any of these files to disk. You print them to
stdout for the user to review.

Read these in the loop scaffold under this repo's `.specfuse/` before acting:

- `.specfuse/skills/derive-monitoring/SKILL.md` — the binding method.
- `.specfuse/rules/design-for-diagnosis.md` — the diagnosability
  properties the audit checks against.
- `.specfuse/monitoring.yml.example` and
  `.specfuse/monitoring.overrides.yml.example` — the file shapes.
- `tests/test_derive_monitoring_discovery.py` — the reference implementation
  of `discover_components`, `suggest_checks`, `audit_diagnosability`, and
  `audit_credential_reuse`; the
  method below points at it and must not diverge from it.

## Method (strict order — infer first, ask last)

### Step 1 — Evidence gathering → component discovery

A component is a deployable, keyed on deployment evidence — it exists because
a deployment artifact names it. A trigger registration (HTTP route,
subscription binding, schedule entry) is evidence of that deployable's type
and the source of its target list, never a component in its own right: a
telemetry backend's role name is per-process, so keying on triggers instead
would mint N components sharing one role name and N duplicate
`error-logs`/`heartbeat` findings per exception.

Read what's in the repo: deployment manifests, container/process
definitions, entrypoint scripts, and CI deploy workflows — whatever names a
candidate as deployed. Then, scoped to each candidate, read its HTTP routing,
consumer/subscription, and schedule registration files to learn what
triggers feed it, mirroring `discover_components(tree, patterns)` in
`tests/test_derive_monitoring_discovery.py`: `patterns["components"]` (deployment
markers + `scope_prefix` per candidate) and `patterns["triggers"]` (the sibling
HTTP, subscription, and schedule table) are the two injected, per-stack tables; the
function emits sorted, neutral component records — one per deployable — with
`name`, `type`, `http_serving`, `message_consuming`, `subscriptions`,
`schedules`, `evidence`. `http_serving`/`message_consuming` are derived from
matched triggers, never declared; `subscriptions`/`schedules` are the neutral
lists `suggest_checks(component)` renders into targets. Then apply
`suggest_checks(component)`'s conservative mapping: every component gets
`heartbeat` and `error-logs`; HTTP-serving also gets `http-5xx`;
message-consuming with a non-empty `subscriptions` list also gets `dlq` with
`harvest_mode: peek`, one target per entry. Never suggest an `invariant`
check — its `query` is operator-supplied by definition.

### Step 2 — Diagnosability audit

Audit the discovered components against
`.specfuse/rules/design-for-diagnosis.md`'s properties: correlation-ID
propagation, structured logging, per-component role names, heartbeat
emission, DLQ failure-context capture, version stamping, data-store signals,
backlog-snapshot emission (each detailed below). A component given `heartbeat`
targets whose own code emits no `ScheduleHeartbeat` event (schedule name
in a `scheduleName` property, under its role name) gets a
`heartbeat-emission` finding — those targets would all report silent. An HTTP-serving component showing no per-deployment version stamp (`version-stamping`) gets one finding and no `http-status-regression` check; with the stamp it gets that check (`deploy_signal: {kind: app-version}`, a `window_after_deploy`).

A component whose scope shows a data store (connection setting, data-access
library, migrations directory) gets the `data-store-signals` audit. The monitor
never connects to a data store: never propose a direct database check, a
data-store provider, or an `invariant` whose `query` reads the store. Check
instead for the owned signals the component should emit as telemetry — table
backlogs (planned `backlog-stalled`, #3576), business-state invariants over
persisted data, migration state (expected versus applied migration, read by the
existing `invariant` check). Each one not emitted is a `data-store-signals`
finding: a design-for-diagnosis gap for the component to close. Platform health
(CPU/throughput units, storage, connections, deadlocks, replication lag,
failover) is out of scope — list it under the report's out-of-scope section so
the operator routes it to infrastructure alerting. The test: would the fix be a
pull request on the component? **Every finding is `WARN`, never `ERROR`.** A
populated codebase predating the rule violates it everywhere by
construction, so an `ERROR` predicate would be unsatisfiable on real input.
The audit informs the operator; it never blocks the draft.

**Data-store work queues (#3576).** Also look, in each deployable's scope, for
work queues kept in its own data store — outbox or job tables, poller loops
draining a pending-work table. `dlq`/`queue-stalled` cannot see them. If the
component's own code emits a `BacklogSnapshot` custom event per backlog
(`backlogName`, `oldestPendingAgeSeconds`, optional `pendingCount`, under its
role name), propose one `backlog-stalled` check with one target per backlog
(`name` = the `backlogName`, `stall_after: 15m` to start). If it emits none,
propose no check and report one `backlog-emission` finding naming the backlogs.
Mirror `suggest_checks`/`audit_diagnosability` in
`tests/test_derive_monitoring_discovery.py`.

**Dependency regression.** A component — HTTP-serving or not — that shows both
a per-deployment version stamp and a recorded data-store dependency (a client
of the store it owns, matched in its own scope by the project's
`data_store_markers` pattern table; the record's `data_store` field) also gets
`dependency-regression` with `deploy_signal: {kind: app-version}` and a
`window_after_deploy`. Leave `dependency_types` at its default (every type the
component records) unless the operator narrows it: the store's type name is
whatever the telemetry records, not something discovery can know. A component
with a data store and no version stamp gets no check and a `version-stamping`
finding naming `dependency-regression`. The check is failures only, by
decision (#3577): never propose a latency threshold for it.

### Step 3 — Ask the user — only for what evidence cannot resolve

Legitimate question categories — **and only these**, batched into one round:

1. **Which environments are real** (the repo's deploy config often names
   candidates; the operator confirms).
2. **Each environment's telemetry/broker `provider` string** — opaque to
   this skill.
3. **The credential environment-variable *names*** for each binding — never
   a value.
3a. **Additional connection coordinates** each binding needs beyond
   credentials — what the provider's client needs to know *which* instance
   to reach. Inline values, not env-var names: addresses, not secrets.
   Unvalidated by `lint_monitoring` (a missing one fails at runtime, not at
   lint time — specfuse/loop#302), so asking is the only safeguard. Ask it
   provider-agnostically; today `azure-service-bus` needs
   `fully_qualified_namespace` + `topic_name` and `azure-app-insights` needs
   `workspace_id`. Unknown provider, unknown coordinates → a `[gap]` line,
   never a guessed address.
4. **Any `invariant` check's `query` and `fingerprint_by`** — never
   inferred or invented.
5. **Per-component dial loosening** beyond the conservative defaults
   (`runner: local`, `diagnose: manual`, `autofix: "off"`).
6. **For a component with a data store, which owned signals it emits**
   (backlogs, invariants, migration state) when the evidence could not
   tell. "None" is a `data-store-signals` finding, never a reason to draft
   a check that reads the store.
7. **Each proposed `backlog-stalled` target's thresholds** — confirm or change
   `stall_after: 15m`, and whether to add a `silent_after` (a few times the
   snapshot emission interval).

**Forbidden:** asking anything a file already answered — e.g. "what
components does this project deploy?" when a deployment manifest names
every one.

**Non-interactive contexts.** If no user is available to answer, still
produce the draft — every would-be question becomes an explicit `[gap]`
line in the report. Do not invent an environment, a provider name, a
credential name, or an `invariant` query.

### Step 3b — Credential reuse audit

The monitor must not reuse the application's own credentials (an app's broker
connection string usually carries send/manage rights; a DLQ peek needs listen
only). For each credential env-var name from Step 3, search the repo —
excluding `.specfuse/` — for the application reading the same variable: env
reads (`os.environ`/`getenv`, `process.env`,
`Environment.GetEnvironmentVariable`, `System.getenv`), `.env` files, compose
`environment:`, Helm/k8s `env:`, Bicep/Terraform app settings, and for a
`Section__Key` name the `Section` → `Key` path in `appsettings*.json`. Each hit
is a `credential-reuse` finding with `file:line` evidence, a suggested
monitor-only name (e.g. `MONITOR_<NAME>`), and a pointer to
`.specfuse/monitoring-secrets-checklist.md` for a separately provisioned
read-only credential (e.g. Listen-only on Service Bus). **This is a heuristic**:
it misses indirect reads (names built at runtime, prefix-stripping config
providers, secrets mounted under another name), so no hit is not proof. Every
finding is `WARN`, never `ERROR`; it never blocks the draft. Mirror
`audit_credential_reuse` in `tests/test_derive_monitoring_discovery.py`.

### Step 4 — Output

Print, in order:

1. **The proposed `.specfuse/monitoring.yml`**, in a fenced YAML block, in
   the same shape as `.specfuse/monitoring.yml.example`. Every component
   starts at `runner: local`, `diagnose: manual`, `autofix: "off"` (quoted)
   unless the operator answered a dial-loosening question for it.

2. **The proposed `.specfuse/monitoring.overrides.yml`**, in a fenced YAML
   block, derived from `.specfuse/monitoring.overrides.yml.example` — the
   machine-local slice with every component's `runner` forced to `local`.

3. **A filled-in reading of `monitoring-secrets-checklist.md`** — one line
   per credential environment-variable name used above, naming where to
   obtain its value. Names only, never values. A name with a
   `credential-reuse` finding says so and names its suggested monitor-only
   replacement.

4. **The reconciliation report**, in this exact structure:

```
# Reconciliation report for <repo-name>

## Components discovered
- <name> (<type>) — evidence: <file:line>

## Diagnosability audit (WARN only)
- <component>: <property> — <finding, or "none">

## Out of scope (route to infrastructure alerting)
- <component>: <platform-health signal> — not a component fix — or "none raised"

## Credential reuse (WARN only, heuristic)
- <ENV_VAR_NAME>: credential-reuse — read by the application at <file:line>;
  suggest <MONITOR_ENV_VAR_NAME>, provisioned read-only per
  .specfuse/monitoring-secrets-checklist.md — or "none found (heuristic)"

## Questions and answers
- Q1: <question>  → A: <answer> → shaped <field>.

## Recommended next step
- Review the draft. If accepted, copy it to `.specfuse/monitoring.yml`
  (and `.specfuse/monitoring.overrides.yml` if drafted), run
  `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml`,
  and uncomment the `monitoring-example-lint`-shaped gate in
  `.specfuse/verification.yml.example` once satisfied.
```

## Closing rules

- You DRAFT; the user CONFIRMS. Never write `.specfuse/monitoring.yml`,
  `.specfuse/monitoring.overrides.yml`, or `monitoring-secrets-checklist.md`
  from this prompt. End with a one-line reminder that the user copies the
  YAML themselves.
- Never ask for a credential *value*. Only ever ask for the
  environment-variable *name* that holds one.
- Never invent an `invariant` query — omit the check if the operator has
  none ready.
- Never propose a direct data-store check. Owned data-store signals the
  component does not emit are `data-store-signals` findings.
- Use the **`status: blocked`** RESULT-block escape only if something
  fundamental prevents drafting at all (the repo has no deployable
  components, no deployment evidence at all, and the user is
  non-interactive). Otherwise produce a draft — even one full of `[gap]`
  markers — and report.
- No prose summary beyond the report. The report is the summary.

End your turn with the RESULT block defined in
`.specfuse/rules/result-contract.md`. `status: complete` means "I produced a
draft + report and showed it to the user" — verification is the user
reading it, not a command exit.
