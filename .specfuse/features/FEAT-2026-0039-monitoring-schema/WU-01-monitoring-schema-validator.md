---
id: FEAT-2026-0039/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/loop/lint_monitoring.py
  - tests/test_lint_monitoring.py
oracle_env: macos_local
---

# Add the monitoring.yml structural validator

**Objective.** Add `specfuse/loop/lint_monitoring.py` — a structural validator for
`.specfuse/monitoring.yml` that parses with `_miniyaml` and returns a list of
human-readable findings — so every later artifact in this feature has a machine
oracle instead of a prose specification.

**Context.** This is `FEAT-2026-0039/T01`, the first WU. Read `PLAN.md` in this
folder for the scope boundary, the existing-mechanism verdict, and the
escalation-predicate answer — all three constrain this WU directly.

Two seams already exist and must be **reused, not reimplemented**:

- `specfuse/loop/_miniyaml.py` — the repo's in-house YAML parser. The package has
  **zero runtime dependencies** (`pyproject.toml` `dependencies = []`); PyYAML is
  dev-only, used solely by the `_miniyaml` equivalence tests. Do not import
  `yaml` in the new module.
- `specfuse/loop/lint_plan.py` — the sibling validator. Read it for the finding
  format, the error-vs-warning convention, and the module-plus-CLI shape it uses.
  Follow its conventions; do **not** extend it. The two validate unrelated
  artifacts and coupling them drags PLAN linting into monitoring's failure modes.

The schema this validates (T02 authors the example that exercises it):

- Top-level keys `environments:` and `components:`.
- Each environment carries typed provider bindings — at minimum
  `telemetry: {provider: <name>, ...}` and `broker: {provider: <name>, ...}` — plus
  credential references.
- Each component carries a `name`, a component `type`, per-component dials
  `runner: local|gh-actions|in-cluster`, `diagnose: manual|auto`,
  `autofix: off|on`, and a list of `checks`.
- Each check carries a `type` from the neutral set `dlq`, `error-logs`,
  `http-5xx`, `heartbeat`, `invariant`. A `dlq` check carries
  `harvest_mode: peek|quarantine`; an `invariant` check carries a user-supplied
  query and a `fingerprint_by`.

**Provider-agnostic boundary.** The check types and the component model are neutral
concepts. This validator must be expressible without importing a single
vendor-specific concept — provider names are opaque strings it does not interpret.
Adapters that give those strings meaning are FEAT-2026-0040's scope.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `verification-discipline.md`) apply.
Do not restate them.

**Acceptance criteria.**

1. `tests/test_lint_monitoring.py::test_unknown_check_type_is_rejected` exists and
   **fails on HEAD before this WU's edits** (the module does not yet exist). It
   feeds a config whose only defect is a check `type` outside the neutral set and
   asserts exactly one finding, whose text names the offending type.
2. After this WU's edits that test passes, and so does
   `tests/test_lint_monitoring.py::test_valid_config_reports_no_findings` — a
   well-formed config produces an empty finding list.
3. `validate_monitoring` is importable:
   `python3 -c "from specfuse.loop.lint_monitoring import validate_monitoring"`
   exits 0.
4. `validate_monitoring` returns a **list of finding strings** — empty list means
   valid. A test asserts the empty-list case is distinguishable from a parse
   failure (which raises or returns a finding, but never silently returns `[]`).
5. **An absent file is not an error.** A test asserts that validating a
   non-existent path returns an empty finding list and that the CLI entry point
   exits 0. This is PLAN.md's escalation-predicate answer made executable:
   monitoring is opt-in, so a project that has not configured it is in a correct
   final state.
6. An unknown dial value (`runner`, `diagnose`, `autofix` outside its enum)
   produces exactly one finding naming both the dial and the bad value — one test
   per dial.
7. A component missing a required field produces exactly one finding naming the
   component and the missing field. A test asserts the finding names the component,
   not just the index, so a 12-component file is diagnosable.
8. **An inline credential is a finding.** A value under a credential key that looks
   like a literal secret rather than an environment-variable reference produces a
   finding. A test supplies a config whose credential is an inline
   connection-string-shaped literal and asserts it is rejected; a companion test
   asserts the env-var-name form is accepted. Use an obviously fake placeholder in
   the test fixture — never a real-looking key (see
   `.specfuse/rules/security-boundaries.md`).
9. Findings are returned in a deterministic order — a test asserts the same input
   yields the same finding sequence twice, so downstream diffs are stable.
10. `_miniyaml` is the only parser used: `grep -n "^import yaml\|^from yaml" specfuse/loop/lint_monitoring.py`
    returns nothing.
11. Every new `subprocess.run` call, if any, declares `check=` explicitly — the
    lint gate enforces `PLW1510` since FEAT-2026-0037.

**Do not touch.** `specfuse/loop/lint_plan.py` (read it for conventions; this is a
sibling module, not an extension — modifying it is out of scope);
`.specfuse/verification.yml` and `specfuse/loop/scaffold.py` (T03 owns the gate
wiring and the seeding); `.specfuse/monitoring.yml.example` (T02 owns it — this WU
ships the validator, not the example); `.git/`, secrets. The driver owns all git
operations — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — tests, `ruff`,
`bandit`, coverage ≥ 90%, `leak-scan`, and the bats suites — must all pass, plus
the symbol-existence check in AC3. Coverage applies to the new module: a validator
with untested branches will fail the floor. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the neutral check-type set
cannot be validated without importing a vendor-specific concept — that boundary is
what makes FEAT-2026-0040's adapter interface possible, and special-casing one
provider here silently forecloses it. Also block if `_miniyaml` cannot parse the
schema shape the PLAN describes without extending `_miniyaml` itself: that parser
is load-bearing for PLAN, GATE, WU, and `verification.yml` in every downstream
project, and changing it is out of scope for this WU. If `validate_monitoring` is
absent from the files you edited, emit `status: blocked` — do not claim complete.
Blocked is respectable (`result-contract.md` rule 4).
