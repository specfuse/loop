# The monitoring.yml schema

`verification.yml` declares how a change is proven correct before it merges.
`monitoring.yml` is the post-deploy counterpart: it declares how a project
notices that a deployed component is misbehaving *after* it ships.

**Monitoring is opt-in.** An absent `.specfuse/monitoring.yml` is a correct,
valid final state — `validate_monitoring` returns no findings for a missing
file, and the shipped gate does not fail on it. Add the file only once you
have real components to watch; a fresh scaffold ships with a commented-out
gate and `.specfuse/monitoring.yml.example` to copy from.

The structural validator is `specfuse/loop/lint_monitoring.py`
(`validate_monitoring`); its tests in `tests/test_lint_monitoring.py` are the
authoritative enumeration of what is accepted. This document is a reference
alongside that validator, not a replacement for it — where the two disagree,
the validator wins.

**Consumer.** FEAT-2026-0040's harvester CLI is the thing that reads this
schema at runtime, dispatching each `environments.*.telemetry`/`broker`
`provider` name to a provider-specific adapter and each component's checks to
the harvesting logic for that check type. **Provider names are opaque
strings this layer does not interpret** — `lint_monitoring.py` accepts any
non-empty `provider` value. The absence of telemetry/broker adapters in this
feature is not an omission; adapters are FEAT-2026-0040's scope, built against
the contract this schema fixes.

## Top-level keys

| Key | Required | Shape |
|---|---|---|
| `environments` | yes | mapping of environment name (e.g. `staging`, `production`) to its provider bindings |
| `components` | yes | list of component mappings |

Both keys are required once the file exists at all; there is no valid
half-populated `monitoring.yml` (missing either key is a validator finding).

## `environments.<name>`

Each environment must declare both provider bindings:

| Binding | Required | Shape |
|---|---|---|
| `telemetry` | yes | mapping with a non-empty `provider` string |
| `broker` | yes | mapping with a non-empty `provider` string |

Either binding may additionally carry a `credentials` mapping (or any
nested structure) whose credential-shaped keys (`*_key`, `*_token`,
`*_secret`, `*_password`, `*_credential`, `*_connection_string`, matched
case-insensitively) must hold an **environment-variable name**
(`^[A-Za-z_][A-Za-z0-9_]*$`), never an inline literal. This is the same rule the
validator enforces everywhere a credential-shaped key appears, at any
nesting depth, in a list or a mapping.

Both `UPPER_SNAKE_CASE` and the `Section__Key` form are accepted — case is not
constrained. `UPPER_SNAKE_CASE` is a convention, not a rule: POSIX permits
lowercase, and `Section__Key` is the canonical environment-variable spelling for
hierarchical configuration in .NET, Spring, and other stacks, so an operator
naming a variable their application actually reads must be able to write its
true name (#246).

The property enforced is **"this is a variable name, not a secret value."** It is
a structural shape check, not a secret detector — a value that happens to be
name-shaped is indistinguishable from a name here. Secret detection belongs to
the `leak-scan` gate; this check catches the common authoring slip of pasting a
connection string where a variable name belongs, which every marker a literal
carries (whitespace, `=`, `;`, `://`, `.`, `,`) still trips.

## `components[]`

Each component is a mapping with five required fields:

| Field | Required | Notes |
|---|---|---|
| `name` | yes | free-form string; used in validator findings and issue titles |
| `type` | yes | free-form string describing the component's shape (e.g. `http-service`, `queue-consumer`) — not enum-constrained |
| `runner` | yes | one of `local`, `gh-actions`, `in-cluster` — where diagnosis/autofix executes |
| `diagnose` | yes | one of `manual`, `auto` — whether a harvested finding is investigated automatically |
| `autofix` | yes | one of `"off"`, `"on"` — whether a diagnosed finding may trigger an automated fix. Must be quoted in YAML; the bare `off`/`on` spellings are rejected (the "Norway problem") |
| `checks` | yes | list of check mappings |

Recommended starting posture for a new component: `runner: local`,
`diagnose: manual`, `autofix: "off"` — loosen one dial at a time as
confidence in the checks grows.

## Check types

Every check has a required `type`, one of six neutral values. This set is
provider-agnostic by construction: a check type names a concept
(a dead-letter queue, a heartbeat), never a vendor.

| Type | Extra required fields | Meaning |
|---|---|---|
| `dlq` | `harvest_mode` (`peek` or `quarantine`), `targets` | Alerts on messages landing in this component's dead-letter queue. `peek` reads without removing; `quarantine` removes after reading. `targets` is **required**: a dead-lettered message is attributed to a subscription, and a target-less `dlq` check on a multi-subscription host cannot say which one. |
| `error-logs` | none | Scans structured application logs for error-level entries. |
| `http-5xx` | none | Alerts when the rolling 5xx rate crosses a threshold. For HTTP-serving components. |
| `heartbeat` | none | Alerts when the component stops reporting in at all. |
| `invariant` | `query`, `fingerprint_by` | Runs an operator-supplied query (opaque to this schema — not parsed or executed here) and alerts on unexpected rows. `fingerprint_by` names the field used to dedupe repeat findings into one issue. |
| `queue-stalled` | `targets` | Alerts when a consumer stops consuming from a subscription — no message failed (so `dlq` sees nothing), the host is still alive (so `heartbeat` sees nothing), and the symptom is a broker coordinate (queue depth / age of oldest message), not a telemetry query, so `invariant` cannot express it either. `targets` is required from birth: a wedged consumer on a multi-subscription host raises the identical "which one" question `dlq`/`heartbeat` targets already answer. |

A check `type` outside this set is a validator finding.

## Check targets

`component` and check `targets` are two different axes, and the schema keeps
them separate on purpose:

- **Component** is the unit of deployment and attribution — the redeploy
  boundary, the `runner`/`diagnose`/`autofix` dials, the thing whose name
  should match the role name it reports at runtime.
- **Check target** is the unit of failure-artifact enumeration — what a
  single check counts findings *per*, when one deployable produces more than
  one of the thing a check is about (a subscription, a schedule).

Those two coincide only when a deployable carries exactly one trigger. A
functions host with 3 queue subscriptions and 2 timer schedules is still
**one component** — one process, one role name — but its `dlq` check needs
per-subscription attribution and its `heartbeat` check needs per-schedule
attribution. `targets[]` is the list on a check that expresses that — required on
some check types, optional on others, and forbidden on the rest (see the matrix
below).

**Why N components per trigger is not the fix.** `cloud_RoleName` (and its
equivalent in every other telemetry backend) is reported **per process**, not
per trigger. Splitting one host into N components — one per subscription or
schedule — would not give each component a distinct role name; all N would
still report the same one. Each of those N components would then carry its
own `error-logs`/`heartbeat` check running the literal same role-name-scoped
query, producing N duplicate findings for a single exception. Worse, the
design-for-diagnosis property "a component's `monitoring.yml` `name` matches
the role name it reports" becomes unsatisfiable by construction — N names
cannot all equal one runtime identity. Keeping one component and enumerating
triggers as `targets[]` is what keeps that property satisfiable.

**Per-type matrix — is `targets` required, optional, or forbidden:**

| Check type | `targets` | Target coordinates | Notes |
|---|---|---|---|
| `dlq` | **required** | `subscription` (required), `function` (required) | `subscription` is what the harvester queries; `function` is what a human diagnoses by — a subscription name alone rarely tells an on-call engineer which handler failed. |
| `queue-stalled` | **required** | `subscription` (required), `function` (required), a stall-threshold coordinate (optional, opaque) | Same `subscription`/`function` coordinates as `dlq` — same subscription, same on-call-facing handler name. The stall-threshold value (how long is too long since the last message) is accepted but never parsed or bounded here, exactly like `invariant.query`; range-checking it is explicitly not this layer's job. |
| `heartbeat` | optional | `name` (required), `cron` (optional), `dialect` (required when `cron` present), `timezone` (optional) | One target per schedule, so a single silent timer among several stays individually visible. A single-schedule component may omit the list. |
| `invariant` | **forbidden** | — | `fingerprint_by` is already this check type's enumeration key; permitting `targets` too would give it two competing enumeration keys. |
| `error-logs` | **forbidden** | — | Role-name keyed and genuinely component-scoped; the validator rejects `targets` here. |
| `http-5xx` | **forbidden** | — | Same reason as `error-logs`. |

Where `targets` is present it must be a non-empty list of mappings, and every
entry must carry that check type's required coordinates. An empty list is a
finding — omit the key to mean "none". Coordinate *contents* are opaque, with
one exception: a `heartbeat` target's `cron` expression has its *field count*
checked against its declared `dialect` (below); its field *values* are never
parsed. An IANA timezone name is checked only for presence, never parsed, the
same way `invariant.query` is.

**`heartbeat`'s `dialect` field.** A `heartbeat` target that carries `cron`
must also carry `dialect`, naming which cron dialect the expression is
written in. A 5-field standard cron and a 6-field seconds-first cron are both
well-formed and mean different things, and cannot be told apart by field
count alone once a second dialect exists — inferring from arity degrades
silently the moment a new dialect arrives, which is the worst time for a
monitoring tool to start guessing. The dialect is declared, not inferred, so
a mismatch is a validation error at lint time instead of a wrong verdict at
3am.

| `dialect` value | fields | field order |
|---|---|---|
| `standard-5` | 5 | minute hour day-of-month month day-of-week |
| `seconds-first-6` | 6 | second minute hour day-of-month month day-of-week |

A `dialect` declared with no `cron` is itself a finding — a dialect for no
expression means the expression was dropped, not that the dialect means
nothing. A `heartbeat` target with only `name` stays valid and needs no
`dialect`; `cron` remains optional.

**`targets` is required on `dlq`.** A `dlq` check with no `targets` key is a
validator finding. This tightened in this repo's FEAT-2026-0069 gate 1: the
field was introduced permissive, every shipped surface was migrated to carry it,
and the requirement was flipped once nothing target-less remained. `dlq` is the
only check type that had a permissive window — `queue-stalled` shipped with
`targets` required from birth. Existing configs carrying a target-less `dlq`
check must add the list; the finding message names the required coordinates
inline.

`specfuse/loop/lint_monitoring.py`'s `_check_checks` and `_check_targets` are the
executable form of the matrix above.

## Example

See `.specfuse/monitoring.yml.example` for a fully-commented example that
exercises every check type across three components of different types (an
HTTP-serving component, a single-subscription message-consuming component,
and a multi-trigger functions host demonstrating `targets[]`). It is
validated by this repo's own `code` gate, so it cannot silently drift from
the schema above.
