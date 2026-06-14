---
id: FEAT-2026-0017/T01
type: implementation
model: claude-opus-4-7
effort: high
status: pending
attempts: 0
planned_cost_usd: 3.50
produces_driver_helper:
  - POST_PASS_INVARIANTS_BY_TYPE
  - assert_terminal_flips_fired
  - verify_post_pass_invariants
prior_attempts:
  - attempts: 3
    model: claude-sonnet-4-6
    outcome: hollow_pass_x3
    initial_commit: 514beee
    notes: "Sonnet 4.6 hollow-passed 3 times. Squash modified only WU-01 frontmatter. loop.py wiring + symbols absent every attempt. tests/test_loop_post_pass_invariant.py written (untracked, survived reset). Detected by G1-CLOSE existence check. Escalating to Opus 4.7 + planned_cost raised 1.50 to 3.50."
  - attempts: 3
    model: claude-opus-4-7
    outcome: tests_fail_env_signing
    duration_seconds: 1943.08
    cost_usd: 11.947744
    notes: "Opus 4.7 wrote substantive loop.py + 293-line test file. Tests failed all 3 attempts because new tempdir-git tests omitted 'git config commit.gpgSign false' setup (operator's global commit.gpgsign=true with SSH signing). Driver reset wiped loop.py edits each attempt; test file survived as untracked. Driver then crashed during spinning-detected commit_bookkeeping (same signing flake). Fix: repo-local commit.gpgsign=false set + WU body now mandates the gpgSign-false setup pattern."
---

# Post-pass driver-state invariant guard (close-type WUs)

**⚠️ Prior hollow-pass (3 attempts on Sonnet 4.6) — read first.**
This WU was dispatched three times before being escalated to Opus
4.7. Each Sonnet attempt flipped this WU's own frontmatter
(`status: pending → done`, `produces_driver_helper`, cost) and
wrote `tests/test_loop_post_pass_invariant.py` — but made ZERO edits
to `.specfuse/scripts/loop.py`. Verify gate passed because tests
ran against unchanged code (no new symbols imported → no failure).
G1-CLOSE caught it via the authoring-work-units §9 existence check
(`grep POST_PASS_INVARIANTS_BY_TYPE loop.py` → 0 hits). The work
is shipping three symbols in `loop.py` AND wiring `verify_post_pass_invariants`
into `run()`'s passed path AND the test file. Frontmatter +
test-file-only is the documented hollow-pass shape; do not reproduce
it. Before declaring complete you MUST run the existence-check
block in AC6 below; if any command exits non-zero or returns the
wrong count, emit `status: blocked` rather than `status: done`.

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
5. New tests in `tests/test_loop_post_pass_invariant.py`. **Tempdir-
   git setup pattern (mandatory).** Any test that creates a tempdir
   git repo MUST run `git config commit.gpgSign false` immediately
   after `git init`, BEFORE the first `git commit`. The operator's
   global git config has SSH commit-signing enabled, and signing
   fails inside subprocesses that can't reach ssh-agent → tests
   fail with `subprocess.CalledProcessError` exit 128 on commit.
   Pattern reference: `tests/_workspace.py:36`,
   `tests/test_closing_deliverable_guard.py:76`. Failure to follow
   this is the documented attempts 4-6 failure mode (see
   `prior_attempts` entry 2). Sub-tests:
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
   authoring-work-units §9). Run ALL of the following from repo
   root; every command must exit 0 and meet its assertion. If any
   fails, emit `status: blocked` with the failing command + observed
   output in the RESULT block — do NOT flip this WU's frontmatter
   `status` field as a substitute for shipping the code.

   ```bash
   # a. Three new symbols present in loop.py source
   test "$(grep -cE '^(POST_PASS_INVARIANTS_BY_TYPE|def assert_terminal_flips_fired|def verify_post_pass_invariants)' .specfuse/scripts/loop.py)" = "3"

   # b. Symbols importable (catches syntax errors + name typos)
   (cd .specfuse/scripts && python3 -c "from loop import POST_PASS_INVARIANTS_BY_TYPE, assert_terminal_flips_fired, verify_post_pass_invariants; assert POST_PASS_INVARIANTS_BY_TYPE.get('close'), 'close key missing or empty'")

   # c. verify_post_pass_invariants invoked from run() (not just defined)
   grep -nE 'verify_post_pass_invariants\(' .specfuse/scripts/loop.py | grep -v 'def verify_post_pass_invariants'

   # d. Regression test file exists and references the T06 pattern
   test -f tests/test_loop_post_pass_invariant.py
   grep -qE 'test_feat_2026_0015_t06_regression|test_close_with_verdict_met_fails_when_gate_unflipped' tests/test_loop_post_pass_invariant.py

   # e. New tests run and pass
   python3 -m pytest tests/test_loop_post_pass_invariant.py -v

   # f. THE PRIOR HOLLOW-PASS GUARD: working-tree diff must touch loop.py
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/loop.py'
   ```

   If `git diff --name-only HEAD` shows ONLY this WU file (and/or
   only the test file), you have reproduced the prior 3x hollow-pass
   — STOP and emit blocked.

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
   AC6's command (a) is the canonical check — if it returns anything
   other than `3`, the WU is incomplete. Do NOT flip this WU's
   frontmatter `status` field as a substitute for shipping the code;
   that is the prior 3x hollow-pass shape and will be caught again
   by G1-CLOSE.
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
