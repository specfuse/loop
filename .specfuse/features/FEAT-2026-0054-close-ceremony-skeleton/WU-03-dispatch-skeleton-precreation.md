---
id: FEAT-2026-0054/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 8.00
oracle_env: macos_local
produces_driver_helper: "loop.py dispatch() — closing-skeleton pre-creation from CLOSING_REQUIREMENTS; generalizes write_stub_retrospective_terminal / append_stub_retrospective_intermediate"
produces:
  - tests/test_dispatch_skeleton.py
---

# Pre-create the closing skeleton at dispatch — guards can only pass

**Objective.** When the driver dispatches a `close`, `close-intermediate`, or `plan-next` WU,
every artifact shape the closing guards assert on already exists as a stub — the agent fills
content instead of reconstructing format from prose.

**Context.** Gate 1 of FEAT-2026-0054, depends on T01 (skeleton content derives from
`CLOSING_REQUIREMENTS` — never a second copy of the contract). Reuse and generalize the
auto-close stub writers (`write_stub_retrospective_terminal`, loop.py:3575 area, and its
intermediate sibling) rather than writing a third skeleton mechanism. Hook point: `dispatch()`
(loop.py:2123), before the agent session starts. Evidence: `assert_gate_review_exists` is the
costliest guard in the system ($53.11/15 refusals, #261); FEAT-2026-0066's G3-CLOSE burned
$6.20 on shape-only refusals. Binding rules: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

- `tests/test_dispatch_skeleton.py::TestSkeletonPrecreation::test_plan_next_dispatch_precreates_gate_review_stub`
  **fails on HEAD** before this WU runs.
- On dispatch of a `plan-next` WU, `GATE-{N+1}-REVIEW.md` exists (correctly named for the gate
  being armed, derivation shared with `assert_gate_review_exists` via the registry) with a stub
  header marking it agent-completable — the #261 misnaming class becomes impossible.
- On dispatch of a `close` / `close-intermediate` WU, `RETROSPECTIVE.md` contains stub sections
  for every requirement applicable at dispatch time (gate section heading for
  close-intermediate; `### Failure-class breakdown` when events.jsonl already shows failed
  attempts for the gate; `## What the loop did NOT verify` when an autoclose-debt marker is
  present). Verdict-conditional headings (`## Cost analysis`) are **not** pre-created — the
  lint (T02) names them once the agent writes its verdict.
- **No placeholder `verdict:` value is ever written.** The field stays absent until the agent
  writes a real one ([FEAT-2026-0020]/[FEAT-2026-0070] lint-window lesson —
  `assert_verdict_well_formed` remains the outcome-time owner).
- **Idempotent and non-destructive** (in-flight features): a `RETROSPECTIVE.md` with earlier
  gates' content is appended to — existing lines byte-identical after pre-creation; an existing
  `GATE-{N+1}-REVIEW.md` is left untouched; running pre-creation twice (re-dispatch after a
  failed attempt) produces no duplicate stub sections. Each property has its own test.
- Skeleton writes happen before the agent session and are part of the WU's working tree (the
  squash the guards inspect), not a separate commit.
- The auto-close path is behavior-unchanged: `evaluate_auto_close` outcomes and the existing
  stub-retro content it writes are untouched (`gate_eval.py` not modified; existing auto-close
  tests pass unchanged).
- Same-test-passes criterion: `tests/test_dispatch_skeleton.py` passes in full after the WU's
  edits.

**Do not touch.** `specfuse/loop/gate_eval.py`; `specfuse/loop/lint_plan.py` (T02's surface);
`specfuse/loop/data/**`, `plugins/**` (T04); other features' folders; `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. Plus
`python3 .specfuse/scripts/loop.py --dry-run` on this feature loads clean.

**Escalation triggers.** If pre-creating a stub would require the driver to answer something
only the agent session can know (e.g. which gate section applies cannot be derived from
PLAN/GATE/events state), stop and emit `status: blocked` — the skeleton must stay derivable
from on-disk state, or it belongs in the lint's findings instead. If idempotency cannot be
guaranteed for some artifact, blocked — never ship a clobbering pre-creation.
