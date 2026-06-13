---
id: FEAT-2026-0017/T01
type: implementation
model: claude-sonnet-4-6
effort: high
status: pending
attempts: 0
planned_cost_usd: 1.50
produces_driver_helper:
  - POST_PASS_INVARIANTS_BY_TYPE
  - assert_terminal_flips_fired
  - verify_post_pass_invariants
---

# Post-pass driver-state invariant guard (close-type WUs)

**Objective.** Wire driver-side post-pass invariant assertions keyed
by WU type. Fire AFTER squash + verdict-flip but BEFORE bookkeeping
flush. For `close` type with `verdict: met`, assert all terminal
flips actually fired (gate `passed`, roadmap row `done`, archive
anchor present). On failure: reset, attempt_outcome event, retry
within budget.

**Context.** This is `FEAT-2026-0017/T01`. Closes the wiring-race
hollow-pass surface surfaced FEAT-2026-0015/T06 G2-CLOSE: the close
WU passed cleanly with `verdict: met` written to frontmatter, but
`fire_terminal_flips` was never invoked because the driver's check
read in-memory `wu.verdict` (loaded by `load_wu` BEFORE dispatch,
value `None`) instead of the agent's just-written frontmatter value.

The wu.verdict re-read fix already landed (FEAT-2026-0015 PR #11
commit `7f403bf`). This WU adds an INDEPENDENT post-pass check so a
future regression in that re-read (or any other wiring-race surface)
is caught at the close attempt, not at /wrap-feature time hours later.

Mirror the shape of `CLOSING_ASSERTIONS_BY_TYPE` / `assert_closing_deliverables`
(FEAT-2026-0015/T07, `loop.py:~1413`). Same name pattern, same
signature, same return contract, same wiring location.

Reference binding rules under `.specfuse/rules/`. The driver owns
all git; edit files only.

**Acceptance criteria.**

1. New `POST_PASS_INVARIANTS_BY_TYPE: dict[str, list]` constant in
   `loop.py`, mirroring `CLOSING_ASSERTIONS_BY_TYPE`'s shape. Initial
   population: `{"close": [assert_terminal_flips_fired]}`. Other
   types (`implementation`, `close-intermediate`, `plan-next`,
   `retrospective`, `lessons`, `docs`) get empty lists OR are absent
   from the dict (both forms are valid).
2. New top-level function
   `assert_terminal_flips_fired(wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str) -> tuple[bool, str]`:
   - Re-read WU frontmatter from disk; extract `verdict`. If `verdict`
     is anything other than the string `"met"` (including `None`,
     `met_locally`, `partially_met`, `not_met`), return `(True, "")` —
     hedged / not-met verdicts don't demand flips.
   - Read PLAN.md, find the last gate entry, locate the matching
     `GATE-NN.md` file in `feature_dir`. Read its frontmatter `status`.
     Must be `passed`. Otherwise return
     `(False, "terminal_gate_not_passed: GATE-NN.md status=<observed>")`.
   - Read `<repo_root>/.specfuse/roadmap.md`, find row whose first
     cell is `wu.feature_id` (derive from `wu.wu_id`: split on `/`,
     take first segment). Status column must be `done`. Otherwise
     `(False, "roadmap_row_not_done: status=<observed>")`.
   - Read `<repo_root>/.specfuse/roadmap-archive.md`, check for
     anchor literal `<a id="<feat_lc>"></a>` (lower-cased feature ID).
     Must be present. Otherwise
     `(False, "archive_anchor_missing: <feat_lc>")`.
   - All three pass → return `(True, "")`.
3. New top-level function
   `verify_post_pass_invariants(wu, feature_dir, repo_root, head_before) -> tuple[bool, str]`:
   - Lookup `POST_PASS_INVARIANTS_BY_TYPE.get(wu.type, [])`. If empty,
     return `(True, "")`.
   - For each callable, invoke with `(wu, feature_dir, repo_root,
     head_before)`. On first `(False, reason)` return that tuple.
   - All pass → `(True, "")`.
4. Wire `verify_post_pass_invariants` into `run()`'s passed-outcome
   path: AFTER `squash_commit` returns sha AND AFTER the close-path
   verdict-flip / `close_wu_for_terminal` assignment AND AFTER
   `fire_terminal_flips` is invoked (when applicable), but BEFORE
   the per-WU bookkeeping flush (`flush_events` + `done_ids.add`).
   On `(False, reason)`:
   - `reset_preserving_events(head_before, events_path)` to wipe the
     squash + flip commits and any working-tree state.
   - Append event:
     `attempt_outcome` with `outcome: "post_pass_invariant_failed"`,
     `attempt`, `assertion: reason.split(":", 1)[0].strip()`,
     `summary: reason`.
   - Set `failure_note = reason`.
   - Print `   POST-PASS INVARIANT FAILED attempt N/3 — <reason>`.
   - `continue` to the next attempt iteration (count as failed for
     spinning detection).
5. New tests in `tests/test_loop_post_pass_invariant.py`:
   - `test_close_with_verdict_met_passes_when_flips_fire`: integration
     stub — close WU passes, gate=passed, row=done, archive anchor
     present. Guard returns `(True, "")`.
   - `test_close_with_verdict_met_fails_when_gate_unflipped`: close
     passes + verdict met, but gate stays awaiting_review. Guard
     returns `(False, "terminal_gate_not_passed: ...")`.
   - `test_close_with_verdict_met_fails_when_row_active`: gate passed
     but roadmap row stays active. `(False, "roadmap_row_not_done:
     ...")`.
   - `test_close_with_verdict_met_fails_when_archive_anchor_absent`:
     gate + row done but archive missing anchor.
     `(False, "archive_anchor_missing: ...")`.
   - `test_close_with_hedged_verdict_skips_guard`: verdict=met_locally.
     Guard returns `(True, "")` without checking flips.
   - `test_feat_2026_0015_t06_regression`: reproduces FEAT-2026-0015/T06
     bug pattern — close WU with `verdict: met` frontmatter but
     fire_terminal_flips not invoked (stub the wiring). Asserts new
     guard returns `(False, ...)`. This test is the canary against
     re-introducing the wu.verdict-re-read race.
6. **Existence check** before declaring complete (per
   authoring-work-units §9):
   `python3 -c "from loop import POST_PASS_INVARIANTS_BY_TYPE, assert_terminal_flips_fired, verify_post_pass_invariants"` exits 0.

**Do not touch.** Exactly 2 files change:
- `.specfuse/scripts/loop.py` (additions only; do not modify
  `CLOSING_ASSERTIONS_BY_TYPE`, `assert_closing_deliverables`, or
  any existing behavior).
- `tests/test_loop_post_pass_invariant.py` (new file).

No edits to: `lint_plan.py` (T02 owns), templates (T02 owns
WU.template.md), skills, production WUs / features, secrets,
`.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage) must pass. Plus AC6's symbol-
existence check. Plus T07's hollow-pass guard (this WU is
`implementation` type — covered by FEAT-2026-0008's three guards,
not T07's closing guards).

**Escalation triggers.**

1. **Completeness.** If any of `POST_PASS_INVARIANTS_BY_TYPE`,
   `assert_terminal_flips_fired`, or `verify_post_pass_invariants`
   is absent from `loop.py` after your edits, emit `status: blocked`.
2. **Behavior drift.** If your edit modifies `CLOSING_ASSERTIONS_BY_TYPE`,
   `assert_closing_deliverables`, or any other existing constant /
   function beyond the documented additions, emit `status: blocked`.
   This WU adds; it does not refactor.
3. **Helper-duplication.** Per authoring-work-units §10: before
   editing `loop.py`, run
   `grep -n "CLOSING_ASSERTIONS_BY_TYPE\|assert_closing_deliverables\|verify_post_pass_invariants" .specfuse/scripts/loop.py`
   to confirm the existing pattern lives in exactly one place and
   the new pattern doesn't collide. If any duplicate-shape dict /
   function exists, name it in the RESULT block and emit
   `status: blocked` rather than editing only one site.
4. **Wiring-site ambiguity.** The passed path has several locations
   that could host the new check (right after `squash_commit`, after
   the verdict-flip, after `fire_terminal_flips`). The AC4 spec says
   AFTER `fire_terminal_flips` but BEFORE bookkeeping flush. If the
   passed path's structure makes that exact ordering impossible
   without restructuring, emit `status: blocked` with the observed
   ordering and propose the closest viable site in the RESULT block.
