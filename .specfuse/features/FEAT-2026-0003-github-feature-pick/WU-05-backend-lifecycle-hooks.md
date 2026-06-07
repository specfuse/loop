---
id: FEAT-2026-0003/T05
type: implementation
model: claude-sonnet-4-6
status: draft
---

# Widen the Backend seam with feature/gate lifecycle hooks

**Objective.** Add no-op lifecycle hook methods to the existing
`Backend` class in `.specfuse/scripts/loop.py` (feature start,
feature complete, gate-passed) and call them from the driver at
the right lifecycle events, plus a `make_backend(feat_fm)` factory
that returns `Backend()` today. Pure offline-wiring step that
prepares the seam for T06's `GitHubBackend` subclass. No external
calls, no label transitions, no behavior change for component-local
features. Mirrors gate 1's offline-first principle
(`[FEAT-2026-0003/G1-LESSONS]`) — split the seam widening from the
live integration.

**Context.** The handoff brief §3.4 (gate 3 scope) and §"Seams to
respect" require keeping the GitHub state backend behind loop's
existing `Backend` seam — *subclass/extend it, don't fork the
driver*. Read `.specfuse/scripts/loop.py` lines 219-231 (the
current `Backend` class — just `set_wu` and `set_gate`) and the
driver's `run()` function (lines 580-755) where backend is
instantiated (`backend = Backend()` at loop.py:586) and where
`set_gate(gate, "awaiting_review")` fires (loop.py:748). Read
`.specfuse/scripts/gh_features.py`'s injectable `runner` pattern
(lines 22-36, 47-54) — T06 will mirror it. Per WU craft
(`.specfuse/skills/authoring-work-units/SKILL.md` §3, §4): name
the exact paths, name the produces-list, name the gate set
verbatim from `verification.yml`.

This WU does only the seam widening + factory + tests. T06
implements `GitHubBackend(Backend)` against this seam. T07 is the
live smoke. Three WUs because gate 1 proved separating
offline-testable wiring from live integration buys deterministic
verification (`[FEAT-2026-0003/G1-LESSONS]` offline-first).

**Acceptance criteria.**
1. `.specfuse/scripts/loop.py` `Backend` class gains three no-op
   methods with these exact signatures (return `None`, do nothing
   by default):
   - `on_feature_start(self, feature_id: str, feat_fm: dict) -> None`
   - `on_gate_passed(self, feature_id: str, gate_number: int) -> None`
   - `on_feature_complete(self, feature_id: str) -> None`
2. `.specfuse/scripts/loop.py` adds a module-level factory
   `make_backend(feat_fm: dict) -> Backend` that returns a plain
   `Backend()` instance today (the GitHubBackend selection logic
   lands in T06). The driver's `run()` replaces `backend =
   Backend()` (loop.py:586) with `backend = make_backend(feat_fm)`.
3. `run()` calls `backend.on_feature_start(feature_id, feat_fm)`
   exactly once, immediately after `backend = make_backend(feat_fm)`
   and BEFORE the early-return for all-gates-passed (so the hook
   fires even on a no-op run — observability of a poll).
4. The driver fires `backend.on_gate_passed(feature_id,
   gate.number)` immediately after the existing
   `backend.set_gate(gate, "awaiting_review")` call (loop.py:748).
   Name match the existing event semantics — the driver marks a
   gate `awaiting_review`, not `passed`, at this point; the hook
   is named `on_gate_passed` because it fires when the gate's WUs
   are all `done` and human-arming is next. Document this in a
   one-line comment.
5. The driver fires `backend.on_feature_complete(feature_id)`
   exactly once at the end of `run()` IF all gates are
   `passed` at exit — i.e. the existing "all gates passed —
   feature complete" path at loop.py:590-591.
6. `tests/test_loop.py` (or a new `tests/test_backend.py` —
   whichever is cleaner; declare which in the implementation)
   adds tests that:
   - `Backend()` instances support all three new methods and
     return `None` when called with valid args (no exception).
   - `make_backend({})` returns a `Backend` instance.
   - A subclass `StubBackend(Backend)` that records calls to
     each hook is exercised end-to-end through a minimal `run()`
     scenario asserting `on_feature_start` fired once before
     dispatch, `on_gate_passed` fired after the gate flipped to
     `awaiting_review`, and `on_feature_complete` did NOT fire
     when blocked WUs prevented completion. Use the same
     test-harness patterns already in `tests/test_loop.py`
     (subprocess stubbing, temp-dir feature folders) — do not
     invent a new harness.
7. The `code` gate set in `.specfuse/verification.yml` passes:
   `python3 -m unittest discover -s tests -v`, `ruff check
   .specfuse/scripts tests scripts`, `bandit -r
   .specfuse/scripts -ll`, `coverage run --source=.specfuse/scripts
   -m unittest discover -s tests && coverage report
   --fail-under=70`.

**Do not touch.** Exactly TWO files change (loop.py and either
the existing `tests/test_loop.py` or a new `tests/test_backend.py`
— pick one, declare in the RESULT block):

- `.specfuse/scripts/gh_features.py` — gate-1 module; the
  body-pass-through already covered T03's bundle, do not edit.
- `.specfuse/scripts/adopt_feature.py` — gate-2 module.
- `.specfuse/scripts/lint_plan.py` — out of scope.
- `.specfuse/scripts/gh_backend.py` — does NOT exist yet; T06
  creates it.
- Any binding rule under `.specfuse/rules/`.
- Any skill under `.specfuse/skills/`.
- Generated directories, secrets, `.env`, `.git/` internals.
- The driver owns all git. Do not run `git` at all (see
  `.specfuse/rules/result-contract.md` rule 1).

Numeric bound (per `[FEAT-2026-0003/G1-LESSONS]`): **exactly two
files changed**.

**Verification.** The `code` gate set in
`.specfuse/verification.yml` (tests, lint, security, coverage).
Run each command in declared order and report each result. Per
`[FEAT-2026-0003/G2-LESSONS]` failure-mode rule: the
coverage gate must continue to pass (>= 70%). If a new test fails
to exercise one of the three hooks, the coverage of loop.py
itself stays above 70% but the hook lines are uncovered — add
the hook-firing-assertion test rather than silencing.

**Escalation triggers.**
- The `Backend` seam in `loop.py` turns out to need a different
  shape than three lifecycle hooks (e.g. the driver's `run()`
  doesn't have a clean "feature complete" exit-point, or
  `on_feature_start` collides with `find_feature`'s existing
  print-on-no-gate-pending path). Block with the precise
  loop.py line numbers in `blocked_reason` and the specific
  shape problem named — do not redesign the seam unilaterally.
- The existing test harness in `tests/test_loop.py` cannot
  observe the hooks without rewriting the run-loop subprocess
  pattern. Block — a test-harness rewrite is not in scope.
- A linter / coverage gate fails because of a pre-existing
  issue not introduced by this WU (per `[meta/first-live-use]`
  scope-to-footprint rule — block, do not loosen the gate).
