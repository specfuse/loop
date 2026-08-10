---
id: FEAT-2026-0044/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/loop/agent_policy.py
  - .specfuse/agent-policy.yml.example
  - tests/test_agent_policy_schema.py
produces_driver_helper: validate_agent_policy
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T03:01:38.255102+00:00
duration_seconds: 623.635
cost_usd: 1.227266
input_tokens: 2
output_tokens: 30
---

# Ship the agent-policy.yml schema, its example, and a structural validator

**Objective.** Create `specfuse/loop/agent_policy.py` exposing
`validate_agent_policy(path) -> list[str]`, ship
`.specfuse/agent-policy.yml.example` conforming to it, and wire a CI gate that
runs the validator.

**Context.** Correlation ID `FEAT-2026-0044/T01`. This is the foundation WU of a
single-gate feature: T02, T03, and T04 all consume the strings this unit fixes.

The operator's priorities currently live nowhere. FEAT-2026-0045 shipped
triage's `auto` dial as a bare keyword argument reading no configuration
*because this file did not exist* — see that feature's `RETROSPECTIVE.md`. This
WU creates the file; T03 wires the dial to it.

**Copy the shape of `specfuse/loop/lint_monitoring.py`.** Read it before
writing. It is the working precedent for a schema validator in this repo:
module-level `frozenset` enums for dial values, a `REQUIRED_*_FIELDS` tuple, a
top-level `validate_*(path) -> list[str]` that returns human-readable finding
strings, per-section `_check_*` helpers, and a `main() -> int` that prints
findings and returns non-zero when any ERROR is present. **Do not import from
it** — two validators over unrelated schemas sharing a helper couples them for
no gain (`[FEAT-2026-0072/T01]` precedent).

**Load-bearing strings — these are fixed here and quoted verbatim by T02, T03,
and T04.** Do not rename them:

- canonical config path: `.specfuse/agent-policy.yml`
- example path: `.specfuse/agent-policy.yml.example`
- module: `specfuse/loop/agent_policy.py`
- validator: `validate_agent_policy(path: str | Path | None = None) -> list[str]`
- finding severity prefixes: `ERROR: ` and `WARN: ` (exactly these, with the
  trailing space — `lint_roadmap.py` uses the same convention and the gate
  script greps on it)

**The schema.** Top-level keys, all required unless marked:

```yaml
version: 1                      # int, must equal 1

queue:                          # list of FEAT-YYYY-NNNN strings, may be empty
  - FEAT-2026-0048

rules:
  bugs:
    preempt: true               # bool
    min_severity: low           # low | medium | high | critical
    automerge: off              # off | on  — enforcement is FEAT-2026-0048's
  features:
    gate_review: human          # human | auto
    wip_limit: 1                # int >= 1
    overrides: {}               # OPTIONAL map FEAT-ID -> human|auto
  triage:
    auto: false                 # bool — wired to apply_triage(..., auto=) by T03

budgets:
  max_tokens_per_run: 2000000   # int > 0
  max_open_prs: 3               # int > 0
  max_items_per_day: 10         # int > 0

escalation:
  webhook: ""                   # str, may be empty; FEAT-2026-0047 consumes it
  assignee: ""                  # str, may be empty
  quiet_hours: ""               # str, may be empty; "HH:MM-HH:MM" when set
  sla_hours: 24                 # int > 0
```

An **empty `queue:` is valid and meaningful** — the roadmap row defines it as
"agent works bugs only and asks for priorities". It must not be a finding.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
module does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_agent_policy_schema.py::TestValidateAgentPolicy::test_shipped_example_validates_clean`
   exists and **fails on HEAD before this WU runs** (the module and the test
   file do not yet exist, which counts as red).
2. `specfuse/loop/agent_policy.py` defines
   `validate_agent_policy(path: str | Path | None = None) -> list[str]`,
   defaulting `path` to `.specfuse/agent-policy.yml`, and returns `[]` for a
   conforming file.
3. Every finding string the validator returns starts with either `ERROR: ` or
   `WARN: ` (exact literals including the trailing space).
4. Module-level enums exist as `frozenset`s and are the single source of their
   values: severity (`low`/`medium`/`high`/`critical`), automerge (`off`/`on`),
   gate_review (`human`/`auto`). A test asserts each rejects a value outside it
   with an `ERROR: ` finding.
5. A missing required top-level key (`version`, `queue`, `rules`, `budgets`,
   `escalation`) produces exactly one `ERROR: ` finding naming that key.
6. An unknown top-level key produces one `ERROR: ` finding naming it — unknown
   keys are rejected, not ignored, so a typo in a dial name cannot read as a
   default.
7. A `version` other than `1` produces an `ERROR: ` finding.
8. A queue entry not matching `^FEAT-\d{4}-\d{4}$` produces an `ERROR: `
   finding naming the offending entry. A **duplicate** queue entry produces an
   `ERROR: ` finding naming it.
9. An **empty** `queue:` list produces **zero** findings — a test asserts this
   explicitly, because "agent works bugs only" is a valid declared state.
10. Wrong-typed values produce `ERROR: ` findings rather than raising:
    `wip_limit: 0`, `wip_limit: "one"`, `max_open_prs: -1`, `sla_hours: 0`, and
    a non-bool `preempt` are each covered by a test.
11. `rules.features.overrides` is optional; when present, every key matches the
    FEAT-ID pattern and every value is in the gate_review enum, else `ERROR: `.
12. `.specfuse/agent-policy.yml.example` exists, carries the Apache-2.0 comment
    header used by the other shipped examples, comments every dial with its
    permitted values, and `validate_agent_policy` returns `[]` against it.
13. `main() -> int` prints each finding one per line and returns `1` when any
    finding starts with `ERROR: `, `0` otherwise — so a WARN-only file does not
    fail the gate.
14. `.specfuse/scripts/lint_agent_policy.py` exists as a thin shim delegating to
    the package module, matching the pattern of the other shims in that
    directory.
15. `.specfuse/verification.yml` gains a `code` gate named
    `agent-policy-example-lint` running
    `python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example`,
    with a comment saying it targets the example because this repo's live policy
    file does not exist until T02.
16. `python3 -m unittest tests.test_agent_policy_schema -v` exits zero after
    this WU's edits.
17. `python3 -c "from specfuse.loop.agent_policy import validate_agent_policy"`
    exits zero.

**Do not touch.** `specfuse/loop/lint_monitoring.py` — read it for shape, do not
edit or import it. `specfuse/loop/triage.py` — T03 owns the dial wiring.
`.specfuse/agent-policy.yml` (the live file) — T02 creates it; this WU ships only
the example. `.specfuse/roadmap.md`. Generated directories, secrets, `.git/`.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, plus the newly added
`agent-policy-example-lint`. Plus the scoped red/green run in criteria 1 and 16
and the symbol check in criterion 17.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`_miniyaml` cannot parse the nested-map-and-list shape this schema needs and a
different parser would have to be introduced (that is a dependency decision, not
this WU's call); or adding the gate to `verification.yml` conflicts with an
existing gate name. If `specfuse/loop/agent_policy.py` is absent from the files
you edited, emit `status: blocked` — do not claim complete.
