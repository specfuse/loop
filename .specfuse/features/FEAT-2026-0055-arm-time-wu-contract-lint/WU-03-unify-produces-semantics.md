---
id: FEAT-2026-0055/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
oracle_env: macos_local
produces_driver_helper: "loop.py assert_declared_deliverables — accepts fnmatch globs (≥1 existing match), aligned with assert_produces_in_diff"
produces:
  - specfuse/loop/loop.py
  - tests/test_produces_semantics_unified.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.7.0
started_at: 2026-07-30T15:16:30.780060+00:00
duration_seconds: 329.386
cost_usd: 1.037655
input_tokens: 38
output_tokens: 10556
---

# One declaration form satisfies both deliverable gates

**Objective.** End the literal-vs-glob split: `assert_declared_deliverables` (`loop.py:4519`,
literal-only existence) learns fnmatch globs with a ≥1-existing-match requirement, so any
`produces:` entry that satisfies `assert_produces_in_diff` (`loop.py:4548`) also satisfies it.

**Context.** Gate 1 of FEAT-2026-0055, depends on T02. The split is documented only in folklore
comments copied into WU files ("a directory passes presence and fails diff; a glob passes diff
and fails presence" — 0066/WU-01, learned at $10.43 on 0065/T01). This WU is the feature's one
deliberate behavior change to an existing guard; GATE-01's §4 probe enumerates the test fallout
before arming. Binding rules: `.specfuse/rules/result-contract.md`, `never-touch.md`,
`correlation-ids.md`.

**Acceptance criteria.**

- `tests/test_produces_semantics_unified.py::TestUnifiedSemantics::test_glob_satisfies_declared_deliverables_when_match_exists`
  **fails on HEAD** before this WU runs.
- Unified contract, asserted by tests: literal path → must exist non-empty (unchanged); glob →
  ≥1 existing non-empty match; directory path → explicit ERROR-worthy refusal message naming
  the unified contract (directories were never valid; now the message says why, instead of a
  silent presence-pass/diff-fail split).
- `assert_produces_in_diff` behavior unchanged; a property-style test asserts the implication
  "accepted by declared-deliverables ⇒ same form accepted by produces-in-diff matching" across
  literal/glob fixtures.
- Behavior table (before/after per declaration form) in this WU's result; existing guard tests
  that asserted literal-only are updated **deliberately and enumerated against the §4 probe's
  failure list** — an unexpected failure outside that list is an escalation, not a quiet fix.
- Full suite green.

**Do not touch.** `specfuse/loop/lint_plan.py` (T01/T02 own it); `.specfuse/templates/**`,
`plugins/**` (T04); `gate_eval.py`; other features' folders; `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** If unifying would silently change any *recorded* historical outcome
shape (an existing feature's events replayed against the new semantics would have passed where
it failed) in a way that tests depend on, stop and report — widening forward is licensed,
rewriting history is not.
