---
id: FEAT-2026-0055/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
oracle_env: macos_local
produces_driver_helper: "lint_plan.check_produces_boundary — ERROR on produces paths the WU's own Do-not-touch forbids"
# Overlap with T01's lint_plan.py is the expected self-WARN this feature's PLAN names:
# T02 makes an incremental edit (adds a second check function) to the file T01 delivered.
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_lint_boundary_consistency.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.7.0
started_at: 2026-07-30T15:09:03.687261+00:00
duration_seconds: 446.978
cost_usd: 1.374473
input_tokens: 60
output_tokens: 19576
---

# ERROR when a WU declares a deliverable its own Do-not-touch forbids

**Objective.** `check_produces_boundary` in `lint_plan.py`: a WU whose `produces:` path (or
`produces_driver_helper` surface) falls inside its own Do-not-touch section's paths is a
structural deadlock — ERROR, un-armable.

**Context.** Gate 1 of FEAT-2026-0055, depends on T01 (same file, incremental edit — the
expected self-WARN). Evidence: FEAT-2026-0066/T04 was barred from `src/main/**` while its
criteria required an artifact only `src/main/**` could hold; the conjunction cost 3 attempts +
an operator re-arm. Parse the Do-not-touch section via `_slice_section` (`lint_plan.py:142`);
extract backtick-quoted tokens containing `/`, `*`, or a file extension as path patterns; match
`produces:` entries with `fnmatch` against them. Binding rules:
`.specfuse/rules/result-contract.md`, `never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

- `tests/test_lint_boundary_consistency.py::TestProducesBoundary::test_errors_when_produces_inside_own_do_not_touch`
  **fails on HEAD** before this WU runs.
- ERROR message names the WU, the offending `produces:` path, the Do-not-touch pattern it
  matches, and the post-attempt guard this preempts (`assert_produces_in_diff`) — the
  [FEAT-2026-0070] earlier-enforcer-names-the-later-one rule.
- Prose-safety: patterns are extracted only from backtick-quoted tokens; a Do-not-touch
  sentence *mentioning* a path in plain words does not fire the rule. An explicit
  carve-out phrase ("except", "**except**") on the same bullet suppresses the match for that
  pattern — 0066/T04's re-armed body used exactly that shape and must lint clean; covered by a
  fixture test.
- **§2 satisfiability run recorded:** the new lint over every feature folder in this repo
  reports **zero ERROR findings**; the run's command + output land in this WU's result. Any
  ERROR on an existing feature → stop, escalate (the rule or the feature is wrong; do not ship
  over it). Expected WARNs from T01 are enumerated, including this feature's own T01/T02
  overlap.
- Fixture tests: the T04 deadlock shape (ERROR), the carve-out shape (clean), plain-prose
  mention (clean), `produces_driver_helper` naming a forbidden surface (ERROR).
- `tests/test_lint_boundary_consistency.py` passes in full after the edits; full suite green.

**Do not touch.** `specfuse/loop/loop.py` (T03's surface); `.specfuse/templates/**`,
`plugins/**` (T04's); other features' folders; `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus the recorded
satisfiability sweep over `.specfuse/features/`.

**Escalation triggers.** If backtick-token extraction cannot distinguish a binding boundary
from an illustrative mention without semantic judgment, stop and emit `status: blocked` with
the ambiguous fixture — a boundary rule that guesses will refuse legitimate arms, which is
worse than the disease.
