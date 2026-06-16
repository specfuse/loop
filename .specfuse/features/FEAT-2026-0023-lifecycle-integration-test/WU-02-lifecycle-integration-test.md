---
id: FEAT-2026-0023/T02
type: implementation
model: opus
effort: high
status: pending
attempts: 0
planned_cost_usd: 3.00
produces: tests/test_lifecycle_integration.py
oracle_env: macos_local
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# End-to-end lifecycle integration test

**Objective.** Author one integration test module that drives a synthetic
feature through the FULL lifecycle in a single run — pick → loop dispatch →
terminal close (BOTH the dispatched-close and the auto-close-predicate paths) →
archive → wrap-ready — using the real driver functions and the real auto-close
predicate against a real git repo in a tmp dir, stubbing only the `claude -p`
agent dispatch. The test asserts the **terminal invariant** holds at the end.
This is the integration layer that would have caught #47, #48, and #49 before
they hit a live run.

**Context.** This is `FEAT-2026-0023/T02`; depends on T01 (consolidated
terminal flips — the test asserts PLAN.md flips on both close paths) and T03
(hardened branch seam — the test drives the dirty-tree pick→branch handoff).

Follow the established integration-test pattern in this repo: real driver code +
real git in a `tempfile.TemporaryDirectory`, with the agent dispatch stubbed.
Exemplars to mirror:
- `tests/test_loop_auto_archive.py` — real `auto_archive_feature` against a tmp
  roadmap/archive.
- `tests/test_deliverable_presence_gate.py` and
  `tests/test_empty_files_escalation.py` (FEAT-2026-0022) — stubbed-dispatch
  loop drives in a tmp git repo with synthetic WUs reaching terminal outcomes.
- `tests/_loop_loader.py` — the loader these use to import the driver under test.

The **terminal invariant** to assert at lifecycle end:
- `PLAN.md status: done`
- terminal `GATE status: passed`
- roadmap row status `done`
- archive anchor `<a id="feat-...">` present in `roadmap-archive.md`
- `RETROSPECTIVE.md` present (stub for the auto-close path; full for dispatched)

Reference the binding rules under `.specfuse/rules/`. The driver owns git; edit
files only.

**Acceptance criteria.**
1. **Red anchor (fails against the pre-fix driver).** The test asserts the
   terminal invariant including `PLAN.md == done` after a terminal **auto-close**
   — the assertion that fails on the pre-T01 driver (#49). Authored so that with
   T01 reverted the test is RED, with T01 applied it is GREEN. Name it
   `tests/test_lifecycle_integration.py::test_auto_close_lifecycle_terminal_invariant`.
2. New module `tests/test_lifecycle_integration.py` builds a synthetic
   single-gate feature in a tmp git repo (real `git init`, real `.specfuse/`
   tree, roadmap with the feature row, stubbed `claude -p` dispatch returning a
   passing RESULT for each WU) and runs the driver to a terminal outcome.
3. **Dispatched-close path** — `test_dispatched_close_lifecycle_terminal_invariant`:
   the feature closes via a dispatched close WU passing with `verdict: met`; the
   full terminal invariant holds.
4. **Auto-close path** — `test_auto_close_lifecycle_terminal_invariant`: the
   feature meets the auto-close predicate and closes via the auto path; the full
   terminal invariant holds (this is the path that left PLAN.md `active` pre-T01).
5. **Row-only / archive-anchor coverage (#47)** — a case where the synthetic
   feature's roadmap row has no inline detail section asserts the archive anchor
   still materializes and the close does not halt on `archive_anchor_missing`.
6. **Branch seam coverage (#48)** — a case exercising
   `ensure_feature_branch` with the `/pick-feature` dirty-tree flips present
   asserts the pick flips are carried onto the feature branch and no raw
   `CalledProcessError` escapes.
7. The test uses the real driver functions (no re-implementation of lifecycle
   logic in the test) and stubs ONLY the agent dispatch boundary. A regression
   in `fire_terminal_flips`, `auto_archive_feature`, `ensure_feature_branch`, or
   the auto-close predicate must surface as a failure here.
8. **Existence check.** `python3 -m pytest tests/test_lifecycle_integration.py`
   (or `python3 -m unittest tests.test_lifecycle_integration`) collects and runs
   the module; the file exists and is non-empty.

**Red-test note (§12).** This WU's deliverable IS the test surface; its
falsifiability is established by AC 1 — the auto-close terminal-invariant
assertion is RED against the pre-T01 driver and GREEN after. No separate
production behavior is introduced, so the standard red→green-on-new-behavior
form is satisfied by the lifecycle assertions themselves.

**Do not touch.** Exactly one new test file changes:
`tests/test_lifecycle_integration.py` (plus a shared test helper under `tests/`
ONLY if an existing one cannot be reused — prefer `tests/_loop_loader.py`). Do
NOT modify driver source (`loop.py`) — T01/T03 own the behavior; this WU only
tests it. If the test cannot pass without a driver change, that is an
escalation, not a quiet edit. Do NOT touch `.specfuse/verification.yml`,
existing WU files, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (the new
module runs inside the suite + counts toward coverage), plus the
red-against-pre-T01 proof in AC 1.

**Escalation triggers.**
1. **Stubbed too shallow.** If passing the test does not actually exercise the
   real `fire_terminal_flips` / `auto_archive_feature` / `ensure_feature_branch`
   / auto-close predicate (i.e. the test would stay green even if those were
   broken), the test is hollow — stop and emit `status: blocked`.
2. **Driver change needed.** If the lifecycle cannot be driven to a terminal
   outcome without modifying `loop.py`, emit `status: blocked` naming the gap —
   it belongs in T01/T03, not smuggled into the test WU.
3. **Dependency.** If T01 or T03 has not landed (the consolidated flip / the
   hardened branch seam are absent), emit `status: blocked` — do not stub around
   the missing behavior to force green.
