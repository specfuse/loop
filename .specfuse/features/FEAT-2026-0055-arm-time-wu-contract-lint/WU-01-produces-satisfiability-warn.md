---
id: FEAT-2026-0055/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
oracle_env: macos_local
produces_driver_helper: "lint_plan.check_produces_satisfiability — WARN on produces paths an earlier done WU already delivered"
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_lint_produces_satisfiability.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.7.0
started_at: 2026-07-30T15:03:17.145671+00:00
duration_seconds: 346.435
cost_usd: 1.132481
input_tokens: 46
output_tokens: 10861
---

# WARN when a produces path was already delivered by a done WU

**Objective.** `check_produces_satisfiability` in `lint_plan.py`: for every dispatchable WU
(`pending` / `ready` / `draft`), a `produces:` path that exactly matches a `done` WU's
`produces:` entry in the same feature yields a WARN naming both WUs.

**Context.** Gate 1 of FEAT-2026-0055, no dependencies. Evidence: FEAT-2026-0066/T04's re-arm
note — its declared deliverable "was already delivered in full by T03", unsatisfiable, 3
attempts / $11.43. Follow `lint_plan.py`'s existing `check_*` convention (`check_planned_cost`,
`check_closing_guard_literals`) and register in `lint(feature_dir)`. Binding rules:
`.specfuse/rules/result-contract.md`, `never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

- `tests/test_lint_produces_satisfiability.py::TestProducesSatisfiability::test_warns_when_done_wu_already_declared_path`
  **fails on HEAD** before this WU runs.
- WARN (not ERROR): message names the dispatchable WU, the `done` WU, the shared path, and the
  authoring response — "drop the path, or state the incremental edit this WU makes to it in the
  body". Lint exit code stays 0 on WARN-only output (existing WARN convention).
- Fires only on exact path equality between `produces:` entries; a glob is compared literally,
  not expanded (expansion semantics are T03's surface — do not pre-empt them here).
- No WARN when the earlier WU is not `done` (parallel drafts legitimately share surfaces), and
  no WARN for a WU's own file or `events.jsonl`.
- Fixture tests cover: the T04 shape (WARN), an incremental-edit chain like 0066 T03→T05
  (WARN fires there too — the message's "state the incremental edit" branch is the correct
  outcome, asserted on message content), and a clean feature (no WARN).
- `tests/test_lint_produces_satisfiability.py` passes in full after the edits; full suite green.

**Do not touch.** `specfuse/loop/loop.py` (T03's surface); `.specfuse/templates/**`,
`plugins/**` (T04's); other features' folders; `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. Plus a live run:
`specfuse-lint .specfuse/features/FEAT-2026-0054-close-ceremony-skeleton` exits 0 (done feature,
no dispatchable WUs → no findings).

**Escalation triggers.** If `done`-WU state is not reliably readable from frontmatter at lint
time (e.g. mid-dispatch statuses confuse the rule), stop and emit `status: blocked` — do not
guess lifecycle semantics; name the ambiguous state.
