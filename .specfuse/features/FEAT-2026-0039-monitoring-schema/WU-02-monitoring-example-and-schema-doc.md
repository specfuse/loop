---
id: FEAT-2026-0039/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - .specfuse/monitoring.yml.example
  - docs/concepts/monitoring-schema.md
  - tests/test_monitoring_example.py
oracle_env: macos_local
---

# Author the shipped monitoring.yml example and its schema reference doc

**Objective.** Write `.specfuse/monitoring.yml.example` — the artifact every
scaffolded project copies from and this repo's own gate validates — and
`docs/concepts/monitoring-schema.md`, the reference the `derive-monitoring` skill
will cite, with a test that keeps the two from drifting apart.

**Context.** This is `FEAT-2026-0039/T02`, following T01. Read `PLAN.md` in this
folder for the scope boundary and the schema's security posture.

**T01's validator is the source of truth for the schema.** It shipped in
`specfuse/loop/lint_monitoring.py` and its tests in `tests/test_lint_monitoring.py`
enumerate what is and is not accepted. Read both before writing a line of the
example. Where this WU's understanding of the schema disagrees with the validator,
the validator wins — do not "fix" the validator to match the example you wanted to
write; that inverts the oracle. Escalate instead (see triggers).

The example's audience is an operator bootstrapping monitoring for the first time,
so it must exercise the full vocabulary rather than the minimum: every check type
(`dlq`, `error-logs`, `http-5xx`, `heartbeat`, `invariant`) and every dial value
worth showing, with comments explaining what each does and when to change it. The
existing `.specfuse/verification.yml.example` is the tone to match — heavily
commented, opinionated about why, honest about what is deliberately absent.

**Security posture — structural, not incidental.** Monitoring config names
telemetry workspaces, broker namespaces, and the credentials to read them. Every
credential in this example is an **environment-variable name**, never a literal.
Every organization name, host name, workspace ID, and queue name is an obvious
placeholder. This repo's `leak-scan` gate reads prose and config alike, and its
pre-commit hook runs a structural scan on the staged diff — a realistic-looking
sample value will block the commit.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `verification-discipline.md`) apply. Do not restate them.

**Acceptance criteria.**

1. `tests/test_monitoring_example.py::test_shipped_example_validates_clean` exists
   and **fails on HEAD before this WU's edits** (the example does not yet exist).
   It loads `.specfuse/monitoring.yml.example` and asserts
   `validate_monitoring` returns an empty finding list.
2. After this WU's edits that test passes.
3. `.specfuse/monitoring.yml.example` exercises **every** check type in the neutral
   set. A test asserts each of `dlq`, `error-logs`, `http-5xx`, `heartbeat`,
   `invariant` appears at least once in the parsed config — not by grepping the
   raw text, but by inspecting the parsed structure, so a type named only in a
   comment does not satisfy it.
4. The example declares at least two components of different types (an
   HTTP-serving component and a message-consuming component), so the per-component
   dial model is visible rather than implied.
5. **Zero inline credentials.** A test asserts every credential-bearing value in
   the parsed example is an environment-variable name, matching the same rule T01's
   validator enforces. A second assertion: `python3 .specfuse/scripts/leak_scan.py --all`
   exits 0.
6. `docs/concepts/monitoring-schema.md` exists and documents each top-level key,
   each check type, and each dial with its enum values, and states plainly that an
   absent `monitoring.yml` is valid (monitoring is opt-in).
7. **Doc and validator agree — no drift.**
   `tests/test_monitoring_example.py::test_doc_and_validator_agree` asserts that
   every check type named as supported in `docs/concepts/monitoring-schema.md` is
   accepted by `validate_monitoring`, and that every type the validator accepts is
   documented. A type in one and not the other fails the test.
8. The doc names FEAT-2026-0040 as the consumer that will read this schema, and
   states that provider names are opaque strings this layer does not interpret —
   so a later reader does not mistake the absence of adapters for an omission.

**Do not touch.** `specfuse/loop/lint_monitoring.py` (T01 owns the validator — if
the example cannot be made valid, escalate rather than editing the oracle);
`.specfuse/verification.yml`, `.specfuse/verification.yml.example`, and
`specfuse/loop/scaffold.py` (T03 owns gate wiring and seeding);
`.specfuse/rules/` (gate 2 owns the design-for-diagnosis rule); `.git/`, secrets.
The driver owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — tests, `ruff`,
`bandit`, coverage ≥ 90%, `leak-scan`, the bats suites. The `leak-scan` gate is
load-bearing for this WU specifically, not incidental: it is the check that catches
a realistic-looking sample credential or a real organization name in the example.
See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the example cannot be made to
validate clean without changing T01's validator — that is a genuine schema
disagreement between two WUs and it needs a human decision, not a unilateral edit
to whichever artifact is easier to change. Also block if the schema as validated
cannot express one of the five check types the PLAN names (for instance, if
`invariant`'s user-supplied query has no home in the accepted shape): a check type
this feature promises but cannot express is a contract gap that
FEAT-2026-0040 would inherit. If `.specfuse/monitoring.yml.example` is absent from
the files you edited, emit `status: blocked` — do not claim complete. Blocked is
respectable (`result-contract.md` rule 4).
