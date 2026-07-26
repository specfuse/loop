---
id: FEAT-2026-0039/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.00
produces:
  - tests/test_derive_monitoring_discovery.py
oracle_env: macos_local
model: sonnet
effort: high
---

# Add the component-discovery reference implementation and its fixture tests

**Objective.** Add `tests/test_derive_monitoring_discovery.py` — a deterministic
reference implementation of the `derive-monitoring` skill's discovery and
diagnosability-audit algorithms, plus a stylized repo-tree fixture that exercises
them and proves their output passes gate 1's `validate_monitoring`.

**Context.** This is `FEAT-2026-0039/T05` of gate 2. Read `PLAN.md` in this folder
(its **Gate 2 sketch** section and its **escalation-predicate** section — the latter
records the WARN-not-ERROR decision this WU must honor) and `GATE-02.md`'s
definition of done.

**Follow the established pattern, do not invent one.** `tests/test_roadmap_add_skill.py`
and `tests/test_roadmap_archive_skill.py` are this repo's shape for testing an
interactive skill: the deterministic core of the skill's algorithm is written as a
**reference implementation inside the test module**, and the tests exercise it
hermetically with `tempfile` + `textwrap`. Read both before writing a line. There is
no production module here on purpose — the skill itself is prose, and a reference
implementation the skill's method section points at is the honest artifact. Do not
add a module under `specfuse/loop/`.

**Gate 1's schema is the target contract.** Read
`specfuse/loop/lint_monitoring.py` and `.specfuse/monitoring.yml.example`. The
records this WU emits must satisfy it: required component fields
`name`/`type`/`runner`/`diagnose`/`autofix`/`checks`; dials from
`local|gh-actions|in-cluster`, `manual|auto`, `"off"|"on"`; check types from
`dlq`/`error-logs`/`http-5xx`/`heartbeat`/`invariant`; a `dlq` check carries
`harvest_mode: peek|quarantine`; an `invariant` check carries `query` and
`fingerprint_by`. Note `autofix` must be **quoted** in emitted YAML — `_miniyaml`
does not accept the bare `off`/`on` spellings.

**Three functions, all deterministic and all pure.**

1. `discover_components(tree, patterns)` — `tree` is a `{relpath: content}` mapping
   modelling a repo; `patterns` is an **injected** evidence-pattern table. Returns
   neutral component records: a `name`, a component `type`, and the evidence
   relpaths that justified each. Sorted output — a fixed input yields a fixed
   sequence, so the skill's draft diffs are stable.
2. `suggest_checks(component)` — maps a neutral component record to a suggested
   check list. Conservative and mechanical: every component gets `heartbeat` and
   `error-logs`; an HTTP-serving component also gets `http-5xx`; a
   message-consuming component also gets `dlq` with `harvest_mode: peek`. An
   `invariant` check is **never** auto-suggested — its `query` is operator-supplied
   by definition, so inventing one would be the skill fabricating evidence.
3. `audit_diagnosability(tree, components, patterns)` — returns findings against
   `.specfuse/rules/design-for-diagnosis.md`'s four properties (correlation-ID
   propagation, structured logging, per-component role names, DLQ error-context
   capture). **Every finding's severity is `WARN`. There is no `ERROR` path.**

**Why WARN and not ERROR — this is a recorded decision, not a default.** A populated
codebase that predates the design-for-diagnosis rule violates it everywhere by
construction, so an `ERROR` predicate is unsatisfiable on real input: the audit
would fire on every correct-for-its-age project and force wrong changes. This is
`planning-discipline.md` §2 applied, and LEARNINGS records the general form
(`[FEAT-2026-0015/G2-CLOSE]`: lint surfaces introduced into a populated codebase
default to WARN). Drafting an `ERROR` severity here fails this WU.

**The provider-agnostic boundary is the thing most likely to break silently.**
Evidence patterns are a stack-specific *input*, never baked into the core. The core
consumes the table and emits neutral records; a new stack is a new table, not a
patch to `discover_components`. This is the same boundary FEAT-2026-0040's provider
adapters depend on, and gate 1's validator already holds its half (provider names
are opaque strings it does not interpret).

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `verification-discipline.md`) apply.
Do not restate them.

**Acceptance criteria.**

1. `tests/test_derive_monitoring_discovery.py::test_discovered_config_passes_lint_monitoring`
   exists and **fails on HEAD before this WU's edits** (the module does not yet
   exist). It runs `discover_components` + `suggest_checks` over the fixture tree,
   renders a complete `monitoring.yml` text, writes it to a temporary path, calls
   `specfuse.loop.lint_monitoring.validate_monitoring` on it, and asserts the
   finding list is **empty**. This is gate 2's definition of done reduced to one
   assertion.
2. After this WU's edits that test passes, and so does
   `test_fixture_tree_yields_expected_components` — a stylized two-component fixture
   tree (one HTTP-serving, one message-consuming) yields exactly two component
   records with the expected names, types, and evidence relpaths.
3. `test_output_is_deterministic` asserts the same tree yields the identical record
   sequence across two calls, so the skill's drafts diff cleanly.
4. **Boundary test — swapped pattern table.** `test_neutral_records_survive_a_second_stack`
   runs `discover_components` over a *second* fixture tree written in a differently
   named stack, with a second pattern table, and asserts the emitted neutral records
   are structurally identical to the first (same types, same dials, same suggested
   check types) — differing only in names and evidence paths. If the core has
   absorbed stack knowledge, this test fails.
5. **Boundary test — no stack tokens in the core.** `test_core_names_no_stack_tokens`
   reads the reference implementation's own source and asserts it contains no member
   of a denylist of framework / logging-library / cloud-vendor tokens the test
   declares inline. Pattern tables are declared in the fixture section and excluded
   from the scan by construction (the test slices the core functions' source, or the
   core lives in a module-level block the test locates by marker comment) — say
   which mechanism you used in a comment, because a scan that silently covers the
   fixtures too would pass vacuously.
6. **Severity test.** `test_audit_findings_are_all_warn` asserts every finding
   `audit_diagnosability` returns on a deliberately undiagnosable fixture tree
   carries severity `WARN`, and that the audit exposes no `ERROR` severity at all —
   assert on the set of severities the function can emit, not merely on this
   fixture's output, so a future `ERROR` branch cannot hide behind a passing case.
7. **Negative observation.** `test_audit_fires_on_an_undiagnosable_tree` supplies a
   fixture with no correlation-ID propagation and no structured logging and asserts a
   non-empty finding list naming both gaps; a companion
   `test_audit_is_quiet_on_a_diagnosable_tree` asserts zero findings on a fixture
   that satisfies all four properties. An audit that fires on nothing passes every
   test (`verification-discipline.md` §3).
8. `suggest_checks` never emits an `invariant` check. A test asserts this directly —
   the `query` is operator-supplied, and auto-generating one would make the skill
   invent evidence.
9. Fixtures are built in a `tempfile` directory from an in-test manifest; **no**
   fake repo tree is committed under `tests/fixtures/`. Every organization name,
   host, queue name, and service name in the fixtures is an obvious `acme-*`
   placeholder — `leak-scan` runs on this diff and the pre-commit hook is stricter
   than the CI gate.
10. Emitted YAML quotes `autofix` (`autofix: "off"`). A test round-trips the emitted
    text through `_miniyaml.parse` and asserts the value is the string `"off"`.
11. Every new `subprocess.run` call, if any, declares `check=` explicitly
    (`PLW1510`, enforced since FEAT-2026-0037).

**Do not touch.** `specfuse/loop/lint_monitoring.py` and
`.specfuse/monitoring.yml.example` (gate 1 shipped both; this WU consumes them as
the oracle — if the emitted config fails the validator, that is a real disagreement
to escalate, not a validator to loosen); `specfuse/loop/_miniyaml.py`;
`tests/test_roadmap_add_skill.py` and `tests/test_roadmap_archive_skill.py` (read
them for the pattern; do not edit); the skill files under
`plugins/specfuse/skills/derive-monitoring/` and `.specfuse/skills/` (T07 owns
them); `.specfuse/rules/design-for-diagnosis.md` (T04 owns it); the bootstrap
artifacts (T06 owns them); `.git/`, secrets. The driver owns all git operations. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — `tests`,
`lint`, `security`, `coverage` ≥ 90%, `leak-scan`, `monitoring-example-lint`, and
the bats suites — must all pass, plus
`python3 -m pytest tests/test_derive_monitoring_discovery.py -v` run directly and
read for the AC1–AC10 test names. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if discovery cannot be factored into
a deterministic function at all — if every part of it needs model judgment, gate 2's
verification story collapses to structural-only and that is a human decision about
the feature's worth, not a workaround to improvise. Also block if the emitted config
cannot satisfy `validate_monitoring` without changing the validator — that is a
gate-1/gate-2 contract disagreement and the fix belongs wherever the disagreement
is, not in a loosened oracle. Also block if holding the provider-agnostic boundary
requires importing a vendor-specific concept into the core (AC4/AC5): that boundary
is what makes FEAT-2026-0040's adapter interface possible. If
`tests/test_derive_monitoring_discovery.py` is absent from the files you edited,
emit `status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
