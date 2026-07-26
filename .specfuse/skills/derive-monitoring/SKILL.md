---
name: derive-monitoring
description: "Interactively draft a target project's `.specfuse/monitoring.yml` — plus a drafted `.specfuse/monitoring.overrides.yml` and a filled-in reading of `monitoring-secrets-checklist.md` — by discovering deployable components from repo evidence, auditing them against the design-for-diagnosis rule, and asking the user only what evidence cannot resolve. Drafts; never auto-writes. Use this once a project has real deployed components to monitor and gate 1's monitoring.yml schema is already in place."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Derive monitoring (interactive)

This skill is `derive-verification`'s post-deploy sibling: where `derive-verification`
drafts how a change is proven correct **before** it merges, this skill drafts how a
project notices that a deployed component is misbehaving **after** it ships. It
combines **evidence in the target repo** — deployment manifests, entrypoints,
process definitions — with **a small batched round of questions only the operator
can answer**, and produces a candidate `.specfuse/monitoring.yml`. The output is
always *proposed*; the operator reviews it before it lands on disk. Posture mirrors
`plan-next`: draft, then arm.

**Run interactively.** The skill's whole value is the batched question round in
Step 3 (which environments exist, each environment's provider bindings, credential
env-var names, `invariant` queries, per-component dial loosening), so it needs an
operator it can ask. A non-interactive `[gap]` fallback is documented below for
when no human is reachable (CI, a dispatched session, no stdin) — it is a degraded
mode, not the intended path. Piping `PROMPT.md` via `claude -p < PROMPT.md`
consumes stdin and silently degrades to gap-mode; use an interactive `claude`
session and ask it to run this skill instead.

The companion `PROMPT.md` is what the operator pipes to `claude -p` or pastes into
a session. This SKILL.md is the method that prompt operationalizes — read it as the
contract.

## Why this exists

A deployed system's components, their evidence of being HTTP-serving or
message-consuming, and the deployment manifests that describe them already sit in
the repo. Hand-writing `monitoring.yml` against that evidence is mechanical work
that mostly duplicates what the tree already says. The error-prone parts are (a)
noticing which components exist without asking the operator to enumerate them by
hand, and (b) never inventing the parts only the operator can supply — a credential
value, an `invariant` query, which environments are real.

The single guarantee the skill makes: **every produced line traces to evidence the
user can audit, or to a question the user explicitly answered.** No silent
invention.

## Hard rules

- **Draft, do not write.** The produced YAML is printed and discussed with the
  user. It lands at `.specfuse/monitoring.yml` only after the user explicitly says
  so, and only if the existing file is absent or backed up. This matches
  `plan-next`'s "drafts but never arms" posture — see `docs/methodology.md` §7.
- **Infer first, ask last.** A question is legitimate only if no file in the repo
  could have answered it. Asking which components exist when deployment manifests
  are sitting in the tree is a skill bug, not a clarification.
- **Credentials by environment-variable name only.** An inline connection string or
  key is a validator finding, not a style preference — gate 1's
  `lint_monitoring._CREDENTIAL_KEY_RE` / `_ENV_VAR_NAME_RE` enforce it. This skill
  never asks the user for a credential *value* and never writes one; it only asks
  for the environment-variable *name* that holds it.
- **`provider` is an opaque string.** The skill does not interpret it and must not
  branch on it. Adapters that give it meaning are FEAT-2026-0040's scope.
- **Never invent an `invariant` query.** Its `query` is operator-supplied by
  definition; fabricating one would be the skill inventing evidence. If no
  `invariant` check is answered for a component, the drafted config simply omits
  one for that component.
- **Conservative defaults.** Every drafted component starts at `runner: local`,
  `diagnose: manual`, `autofix: "off"`, loosened one dial at a time as confidence
  builds. `autofix` is **quoted** — `_miniyaml` does not accept the bare
  `off`/`on` spellings.
- **The draft must validate.** The closing step tells the operator to run
  `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml`. A
  non-empty finding list means the draft is wrong, not the validator — the
  validator is gate 1's shipped oracle, never loosened to fit an example.
- **Uncomment the gate afterwards.** `.specfuse/verification.yml.example` carries a
  commented-out `monitoring-example-lint`-shaped gate pointed at the project's own
  `monitoring.yml`. The skill's closing step tells the operator to uncomment it
  once the draft is accepted.
- **The `.claude/skills/derive-monitoring` discovery symlink is an operator
  prerequisite, not agent work.** Claude Code's sandbox lists `.claude/skills`
  under `denyWithinAllow` — a deny rule nested inside an allow scope that survives
  `unsandboxed: true`. This skill does not attempt to create that symlink and does
  not instruct an agent session to create it; the operator runs, once, before
  dispatching anything that needs `/derive-monitoring` interactively:
  `ln -s ../../.specfuse/skills/derive-monitoring .claude/skills/derive-monitoring`.

## The method (in strict order)

This ordering is the whole point. Infer first, ask last.

### Step 1 — Evidence gathering → component discovery

**A component is a deployable, keyed on deployment evidence: it exists because
a deployment artifact names it.** A trigger registration — an HTTP route, a
subscription binding, a schedule entry — is evidence of that deployable's
type and the source of its target list; it is never a component in its own
right. The reason this ordering is decisive, not stylistic: the role name a
telemetry backend reports is **per-process**, so a host running N trigger
registrations still reports one role name. Keying discovery on triggers
instead of deployables would mint N components sharing that one role name,
and each would carry the same role-name-keyed `error-logs` and `heartbeat`
query — N duplicate findings per exception. Keying on the deployment artifact
first avoids this by construction.

Read what's in the target repo: deployment manifests, container/process
definitions, entrypoint scripts, and CI deploy workflows — whatever names a
candidate as deployed. Then, scoped to each candidate found that way, read
its HTTP routing, consumer/subscription registration, and schedule
definitions — whatever the project actually uses — to learn what triggers
feed it.

**The algorithm is not reinvented here — it is pointed at.** The deterministic
core this step follows is `tests/test_derive_monitoring_discovery.py`'s three pure
functions: `discover_components(tree, patterns)` takes two injected, per-stack
tables — `patterns["components"]`, deployment markers plus a `scope_prefix` per
candidate, and `patterns["triggers"]`, a sibling table of HTTP, subscription,
and schedule markers matched inside that same scope — and returns sorted, neutral
component records, one per deployable, not one per trigger: `name`, `type`,
`http_serving`, `message_consuming`, `subscriptions`, `schedules`, `evidence`.
`http_serving` and `message_consuming` are **derived** from matched triggers,
never declared inputs; `subscriptions` and `schedules` are the neutral
`{subscription, function}` / `{name, cron, timezone}` lists `suggest_checks(component)`
renders into `dlq` and `heartbeat` targets. `suggest_checks` maps a neutral
record to a conservative check list (never `invariant`). Reading that
test module alongside this section keeps the prose and the tested algorithm from
diverging into two different things.

### Step 2 — Diagnosability audit

Audit the discovered components against
`.specfuse/rules/design-for-diagnosis.md` (T04)'s four properties: correlation-ID
propagation, structured logging, per-component role names matching
`monitoring.yml`, and DLQ failure-context capture. **Findings are reported as
`WARN`, never `ERROR`.** A populated codebase that predates the design-for-diagnosis
rule violates it everywhere by construction, so an `ERROR` predicate would be
unsatisfiable on real input and would force the operator to fix unrelated
instrumentation gaps before they could even see a draft. The audit informs the
operator about diagnosability gaps; it never blocks the draft from being produced.

### Step 3 — Ask only what the repo cannot answer

The legitimate question set is small and is batched into **one round**, presented
together with the evidence that motivated each:

1. **Which environments exist** (staging, production, ...) — the repo's deploy
   config often names them, but the operator confirms which are real.
2. **Each environment's telemetry and broker `provider` string.** Opaque to this
   skill; the operator names whatever their telemetry/broker vendor calls itself.
3. **The credential environment-variable *names*** for each environment's
   `telemetry`/`broker` bindings — never a value.
4. **Any `invariant` check's `query` and `fingerprint_by`.** Operator-supplied by
   definition; never inferred or invented.
5. **Per-component dial loosening** beyond the conservative defaults
   (`runner`/`diagnose`/`autofix`), if the operator already has enough confidence
   in a check to loosen it.

**Forbidden questions** — anything answerable by reading a file. "What components
does this project deploy?" when a deployment manifest names every one is a skill
bug, not a clarification. A `dlq` or `heartbeat` check's `targets[]` is one such
case: it is derived from Step 1's `subscriptions`/`schedules` evidence and is
never an operator question — asking the operator to enumerate subscriptions by
hand would be a Forbidden question by this same rule. If discovery cannot name a
target, the check is omitted, the same rule §4a already states for `dlq`; it is
never asked about.

**Non-interactive fallback.** If the skill runs where the operator cannot answer
(CI invocation, dispatched session, no stdin), it still produces a draft — every
would-be question becomes an explicit `[gap]` line in the reconciliation report
rather than a guess. Silence is never permission to invent an environment, a
provider name, a credential name, or an `invariant` query.

### Step 4 — Output

Four artifacts, in this order:

#### 4a. The proposed `.specfuse/monitoring.yml`

A complete YAML file printed to stdout, in the same shape as
`.specfuse/monitoring.yml.example`:

```yaml
environments:
  staging:
    telemetry:
      provider: acme-telemetry
      credentials:
        api_key: ACME_TELEMETRY_STAGING_API_KEY
    broker:
      provider: acme-broker
      credentials:
        connection_string: ACME_BROKER_STAGING_CONNECTION_STRING

components:
  - name: acme-web-api
    type: http-service
    runner: local
    diagnose: manual
    autofix: "off"
    checks:
      - type: http-5xx
      - type: heartbeat
      - type: error-logs

  - name: acme-order-worker
    type: queue-consumer
    runner: local
    diagnose: manual
    autofix: "off"
    checks:
      - type: dlq
        harvest_mode: peek
        targets:
          - subscription: acme-orders-created-sub
            function: ProcessOrderCreated
          - subscription: acme-orders-cancelled-sub
            function: ProcessOrderCancelled
      - type: heartbeat
      - type: error-logs
```

`targets[]` is the enumeration axis the schema doc's "Check targets" section
documents. It is **required on every `dlq` and `queue-stalled` check**, whether
the deployable carries one subscription or twenty — a single-subscription
consumer still names its subscription and its handler function, because
`subscription` is what the harvester queries and `function` is what a human
diagnoses by, and neither is recoverable from the component name. On
`heartbeat` the list is optional and worth emitting wherever discovery found
more than one schedule feeding one deployable; on `error-logs` and `http-5xx`
it is rejected outright.

If discovery cannot name a real subscription, emit **no `dlq` check at all**
rather than a target-less or fabricated one. A missing check is a visible gap
the operator can fill; an invented coordinate is a wrong answer that validates.

#### 4b. The proposed `.specfuse/monitoring.overrides.yml`

Derived from `.specfuse/monitoring.overrides.yml.example` (T06), the
machine-local slice with every component's `runner` forced to `local`:

```yaml
environments:
  staging:
    telemetry:
      provider: acme-telemetry
      credentials:
        api_key: ACME_TELEMETRY_STAGING_API_KEY
    broker:
      provider: acme-broker
      credentials:
        connection_string: ACME_BROKER_STAGING_CONNECTION_STRING

components:
  - name: acme-web-api
    type: http-service
    runner: local
    diagnose: manual
    autofix: "off"
    checks:
      - type: heartbeat
      - type: error-logs

  - name: acme-order-worker
    type: queue-consumer
    runner: local
    diagnose: manual
    autofix: "off"
    checks:
      - type: dlq
        harvest_mode: peek
        targets:
          - subscription: acme-orders-dlq-sub
            function: ProcessOrder
```

#### 4c. A filled-in reading of `monitoring-secrets-checklist.md`

One line per credential environment-variable name used above, naming where
the operator obtains its value. Names only, never values.

#### 4d. The reconciliation report

A per-component, per-check readout stating whether each line came from
evidence (naming the file) or from an answer to one of Step 3's questions,
plus the diagnosability audit's `WARN` findings:

```
# Reconciliation report for <target-repo-name>

## Components discovered
- acme-web-api (http-service) — evidence: <file:line>
- acme-order-worker (queue-consumer) — evidence: <file:line>

## Diagnosability audit (WARN only)
- <component>: <property> — <finding, or "none">

## Questions and answers
- Q1: <question> → A: <answer> → shaped <field>.

## Recommended next step
- Review the draft above. If accepted, copy it to
  `.specfuse/monitoring.yml`, run
  `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml`,
  and uncomment the `monitoring-example-lint`-shaped gate in
  `.specfuse/verification.yml.example` once satisfied.
```

## Seams

The skill separates "discover candidate components from evidence" from "reconcile
against the schema and ask what's missing," the same seam `derive-verification`
holds for CI discovery:

| Step | Generic | Stack-specific |
|------|---------|-----------------|
| 1 component discovery | `discover_components(tree, patterns)` — generic matcher | `patterns["components"]`: deployment markers + `scope_prefix` per candidate; `patterns["triggers"]`: the sibling trigger table |
| 1 check suggestion | `suggest_checks(component)` — generic, conservative | none — the function takes no stack input |
| 2 diagnosability audit | `audit_diagnosability(tree, components, patterns)` — generic | the `patterns["diagnosability"]` marker table |
| 3 ask | Generic | — |
| 4 output | Generic | — |

Adding a new stack's evidence vocabulary is a new pattern table, never a change to
`discover_components`, `suggest_checks`, or `audit_diagnosability` themselves —
see `tests/test_derive_monitoring_discovery.py`'s boundary tests.

## What this skill does *not* do

- It does not write `.specfuse/monitoring.yml`, `.specfuse/monitoring.overrides.yml`,
  or `monitoring-secrets-checklist.md` to disk on its own. It is an authoring aid;
  the operator copies the accepted draft themselves.
- It does not run any of the checks it drafts, and it does not invoke
  `specfuse-monitor run` — that CLI is FEAT-2026-0040's scope.
- It does not modify `specfuse/loop/lint_monitoring.py`,
  `.specfuse/monitoring.yml.example`, or `.specfuse/rules/design-for-diagnosis.md`.
  If applying this skill reveals that those need to change, the skill stops and
  reports the need — it never edits them as part of its work.
- It does not invent an `invariant` query, a credential value, or a component the
  repo has no evidence for.
- It does not create the `.claude/skills/derive-monitoring` discovery symlink —
  that is the documented operator prerequisite above.
- It does not auto-run from `init.sh`. `init.sh` stays deterministic and
  agent-free; the closing instructions of gate 1's monitoring scaffolding point at
  this skill as an optional next step.

## Worked example

A target repo with an `acme-web-api` HTTP service and an `acme-order-worker` queue
consumer — the same shape `tests/test_derive_monitoring_discovery.py`'s Stack A
fixture models. Evidence gathering finds a route registration for `acme-web-api`
and a consumer registration for `acme-order-worker`; `suggest_checks` proposes
`http-5xx`/`heartbeat`/`error-logs` for the first and `dlq`/`heartbeat`/`error-logs`
for the second. The diagnosability audit finds no correlation-ID propagation
evidence and reports it `WARN`. Step 3 asks which environments are real (operator
answers "staging only"), the telemetry/broker provider strings, and the two
credential env-var names — no `invariant` question, because the operator has no
query ready yet. Step 4 prints the two YAML drafts above (component list narrowed
to what was actually discovered) and the reconciliation report, then stops.
