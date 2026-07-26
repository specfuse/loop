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

Every check has a required `type`, one of five neutral values. This set is
provider-agnostic by construction: a check type names a concept
(a dead-letter queue, a heartbeat), never a vendor.

| Type | Extra required fields | Meaning |
|---|---|---|
| `dlq` | `harvest_mode` (`peek` or `quarantine`) | Alerts on messages landing in this component's dead-letter queue. `peek` reads without removing; `quarantine` removes after reading. |
| `error-logs` | none | Scans structured application logs for error-level entries. |
| `http-5xx` | none | Alerts when the rolling 5xx rate crosses a threshold. For HTTP-serving components. |
| `heartbeat` | none | Alerts when the component stops reporting in at all. |
| `invariant` | `query`, `fingerprint_by` | Runs an operator-supplied query (opaque to this schema — not parsed or executed here) and alerts on unexpected rows. `fingerprint_by` names the field used to dedupe repeat findings into one issue. |

A check `type` outside this set is a validator finding.

## Example

See `.specfuse/monitoring.yml.example` for a fully-commented example that
exercises every check type across two components of different types (an
HTTP-serving component and a message-consuming component). It is validated
by this repo's own `code` gate, so it cannot silently drift from the schema
above.
