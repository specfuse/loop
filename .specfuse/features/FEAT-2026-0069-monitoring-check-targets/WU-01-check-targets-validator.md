---
id: FEAT-2026-0069/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - specfuse/loop/lint_monitoring.py
  - tests/test_lint_monitoring.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-26T16:46:22.837152+00:00
duration_seconds: 206.246
cost_usd: 0.739927
input_tokens: 24
output_tokens: 5789
---

# Accept and validate `checks[].targets` when present

**Objective.** Teach `validate_monitoring` the `checks[].targets` axis — validated
whenever present, required nowhere yet — so every later work unit in this feature has a
machine oracle for the new shape instead of a prose description of it.

**Context.** This is `FEAT-2026-0069/T01`, the first WU. Read `PLAN.md` in this folder
first: its scope boundary, its existing-mechanism verdict, and especially its
**escalation-predicate section** constrain this WU directly. The short version of that
section is the one rule this WU must not break: **`targets` becomes *required* on `dlq`
in T03, not here.** T02 migrates the shipped examples in between. If you make anything
required, the repo's own `monitoring-example-lint` gate goes red on a correct tree and
the feature halts before T02 can run.

The axis this introduces, in the terms the feature is about: a **component** is the unit
of deployment and attribution (role name, trust dials, redeploy boundary); a **check
target** is the unit of failure-artifact enumeration (what findings are counted per). A
DLQ is not a component — it is a queue belonging to a subscription that a function
inside a component consumes. A timer is not a component — it is a schedule.

One seam already exists and must be **reused, not reimplemented**: `fingerprint_by` on
`invariant` checks (`specfuse/loop/lint_monitoring.py:214`) is already this exact shape
— a per-check keying field the validator requires structurally and never interprets,
consumed downstream by FEAT-2026-0040. `targets` is its generalization. Do not invent a
parallel mechanism.

`specfuse/loop/_miniyaml.py` already parses the nested shape this WU validates
(list-of-mappings under a key of a list item, including a quoted cron expression) —
probed at draft time, confirmed working. Do **not** modify `_miniyaml`: it is
load-bearing for PLAN, GATE, WU, and `verification.yml` in every downstream project.

The target coordinates, per check type:

- `dlq` target — `subscription` (what the harvester queries) **and** `function` (what a
  human diagnoses by). Two coordinates on purpose; collapsing them to one breaks the
  feature's point.
- `heartbeat` target — `name` required; `cron` and `timezone` optional.
- `error-logs`, `http-5xx` — no targets permitted at all. These are role-name keyed and
  therefore genuinely component-scoped.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `verification-discipline.md`) apply. Do
not restate them.

**Acceptance criteria.**

1. `tests/test_lint_monitoring.py::TestCheckTargets::test_dlq_target_missing_function_is_rejected`
   exists and **fails on HEAD before this WU's edits** — the validator ignores `targets`
   entirely today, so it produces no finding and the assertion fails. The test feeds a
   config whose only defect is a `dlq` target carrying `subscription` but no `function`,
   and asserts exactly one finding whose text names the missing coordinate.
2. After this WU's edits that test passes, and
   `tests/test_lint_monitoring.py::test_valid_config_reports_no_findings` still passes.
3. A `dlq` target missing `subscription` produces exactly one finding naming it. Separate
   test from AC1 — one missing coordinate per test, so a failure attributes to one line.
4. A `heartbeat` target missing `name` produces exactly one finding naming it.
5. A `heartbeat` target carrying `cron` and `timezone` validates clean, and their
   **contents are not validated** — a cron expression and an IANA zone name are opaque to
   this layer, exactly as `invariant.query` is. A test asserts a syntactically absurd
   cron string still passes, so a later WU cannot quietly add expression parsing here.
6. An `error-logs` check carrying `targets` produces exactly one finding. Same for
   `http-5xx`, as a separate test.
7. **A target-less `dlq` check still validates clean.** T03 flips this; this WU must not.
   Assert it explicitly so the flip in T03 has a test to invert rather than a silence to
   guess at.
8. `targets` present but not a list produces exactly one finding.
9. `targets` present as an empty list produces exactly one finding — an empty enumeration
   is a config bug, not a valid "none". Omitting the key is how you say "none".
10. A target that is not a mapping produces exactly one finding naming the check index
    and the target index, so a 20-target block is diagnosable.
11. Findings remain deterministically ordered: a test asserts the same input yields the
    same finding sequence twice, extending the existing guarantee across the new nesting.
12. `python3 -c "from specfuse.loop.lint_monitoring import validate_monitoring"` exits 0.
13. `grep -n "^import yaml\|^from yaml" specfuse/loop/lint_monitoring.py` returns nothing.
14. Coverage stays ≥ 90% — every new validation branch needs a test, including the
    rejection branches.

**Do not touch.**

- `.specfuse/monitoring.yml.example` and `specfuse/loop/data/monitoring.yml.example` —
  T02 owns them. This WU ships validation, not examples.
- `docs/concepts/monitoring-schema.md` — T02 owns it.
- `CHECK_TYPES` membership — T04 adds `queue-stalled`. This WU changes only per-type
  field validation, not the type lexicon.
- `tests/test_derive_monitoring_discovery.py` — T03 owns the reference-implementation
  change. Enumerated in `PLAN.md`'s §10 note and deliberately deferred, not overlooked.
- `specfuse/loop/_miniyaml.py` — already parses the shape; out of scope.
- `specfuse/loop/lint_plan.py` — sibling validator, unrelated artifact.
- `.git/`, secrets. The driver owns all git operations — you edit files only. See
  `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — `tests`, `ruff`,
`bandit`, coverage ≥ 90%, `leak-scan`, and the bats suites — must all pass, plus the
symbol-existence check in AC12. `monitoring-example-lint` must stay green, which is
automatic if AC7 holds and fails loudly if it does not. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if:

- The target coordinates cannot be validated without importing a vendor-specific
  concept. `subscription` must stay as neutral as `dlq` already is; that boundary is what
  makes FEAT-2026-0040's adapter interface possible, and special-casing one provider here
  silently forecloses it.
- Validating the nested shape appears to require extending `_miniyaml`. It does not — the
  shape was probed at draft time — so if you conclude otherwise, something in your reading
  differs from the plan's and that is worth a halt rather than a parser change.
- `validate_monitoring` still returns zero findings for a malformed target after your
  edits. If the new validation is absent from the files you edited, emit `status: blocked`
  — do not claim complete.

Blocked is a respectable outcome (`result-contract.md` rule 4).
</content>
