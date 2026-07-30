---
id: FEAT-2026-0054/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.00
oracle_env: macos_local
produces_driver_helper: "lint_plan.py — `--closing` mode reading closing_requirements.CLOSING_REQUIREMENTS"
produces:
  - tests/test_lint_closing.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.7.0
started_at: 2026-07-30T12:28:38.091920+00:00
duration_seconds: 582.043
cost_usd: 2.135465
input_tokens: 4339
output_tokens: 29159
---

# `specfuse-lint --closing` — the closing contract, checkable before the attempt ends

**Objective.** An in-session lint mode that tells a close/close-intermediate/plan-next agent
exactly which closing requirements its artifacts do not yet satisfy — before it ends the
attempt, while fixing costs cents instead of a full re-dispatch.

**Context.** Gate 1 of FEAT-2026-0054, depends on T01 (reads
`specfuse.loop.closing_requirements.CLOSING_REQUIREMENTS`; invents no requirement of its own).
Evidence: 28% of closing-WU spend is post-squash refusals; `closing_deliverable_missing` cost
~$42/15 attempts portfolio-wide. Binding rules: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

- `tests/test_lint_closing.py::TestClosingLintMode::test_reports_missing_verdict_naming_postsquash_guard`
  **fails on HEAD** (`--closing` flag not recognized) before this WU runs.
- `specfuse-lint --closing <feature-dir>` (and `python3 .specfuse/scripts/lint_plan.py
  --closing <feature-dir>` through the shim) evaluates the feature's closing WU(s) and artifacts
  against the registry for the gate currently closing: exit 0 with `CLOSING-READY` when every
  applicable requirement is satisfied; exit 1 with one line per unmet requirement otherwise.
- Every finding line names: the requirement, the artifact/path inspected, **and the post-squash
  guard that would fire** (e.g. `... would fail assert_verdict_well_formed after squash`) — the
  FEAT-2026-0070 rule made mechanical.
- Conditional requirements are evaluated with their conditions: verdict-dependent headings
  (`## Cost analysis` only when `verdict: met`), failed-attempts-dependent
  (`### Failure-class breakdown` from events.jsonl attempt outcomes), autoclose-debt marker
  scanning, `plan-next`'s `GATE-{N+1}-REVIEW.md` naming derived the same way
  `assert_gate_review_exists` derives it.
- A verdict field that is **absent** is reported as a finding (actionable), not a crash; an
  invalid value is reported with the allowed set. The mode never writes anything — read-only.
- Post-pass-phase requirements (registry entries marked post-pass, per T01) are reported as
  advisory `NOTE:` lines, clearly separated — they cannot be satisfied pre-squash and must not
  block exit 0.
- Fixture coverage in `tests/test_lint_closing.py`: a fully-ready close (exit 0), each guard
  class from T01's equivalence fixtures (exit 1 with the right guard named), and a plan-next
  case reproducing the #261 naming trap (review file named for the closed gate instead of the
  armed one → finding names `assert_gate_review_exists`).
- Same-test-passes criterion: `tests/test_lint_closing.py` passes in full after the WU's edits.

**Do not touch.** `specfuse/loop/loop.py` guard bodies and `dispatch()` (T01/T03 surfaces);
`specfuse/loop/data/**`, `plugins/**` (T04); other features' folders; `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. Plus a live run:
`specfuse-lint --closing .specfuse/features/FEAT-2026-0072-structural-invariant-guards` (a done
feature) exits 0 — a correct historical close must lint clean.

**Escalation triggers.** If the registry (T01) is missing a requirement the post-squash guards
actually check — i.e. you would need to hardcode a string here to match guard behavior — stop
and emit `status: blocked` naming the gap; the fix belongs in T01's registry, not inline here.
