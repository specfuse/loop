---
id: FEAT-2026-0015/T06
type: implementation
model: claude-sonnet-4-6
effort: medium
status: pending
attempts: 0
planned_cost_usd: 1.50
---

# Move terminal state-flips from `/wrap-feature` into the `close` WU's post-verify driver flow

**Objective.** When a `close` WU passes verify+squash AND its
`verdict == "met"`, the driver fires the four terminal flips
(GATE-NN.md → `passed`, roadmap row → `done`, PLAN.md stays
`done` from the WU's own write, `auto_archive_feature` invoked)
before recording `task_completed`. `/wrap-feature` shrinks to
the plumbing-only handoff.

**Context.** This is `FEAT-2026-0015/T06`. Depends on T04
(`verdict_permits_terminal_flips`).

Per PLAN.md roadmap detail § "State-flip ownership consolidation"
and the live evidence cited there: FEAT-2026-0010, 0013, 0014 all
left `roadmap row = active` after PLAN.md `done` and /wrap-feature
step 1 surfaced the drift every time. FEAT-2026-0010's
`auto_archive` hook didn't fire on itself because gate-is-None
requires the cosmetic gate flip, which happens at wrap. Moving
all terminal flips into close → drift becomes impossible +
auto-archive fires cleanly on every feature including its own.

Today's split:

| Surface | Owner today | Owner after T06 |
|---|---|---|
| PLAN.md status | close WU writes | unchanged |
| Terminal gate status (`GATE-NN.md status: passed`) | `/wrap-feature` step 3 (cosmetic) | driver post-verify, conditional on verdict |
| Roadmap row status | `/wrap-feature` step 4 (manual flip) | driver post-verify, conditional on verdict |
| `auto_archive_feature` call | `loop.py::run()` gate-is-None hook | driver post-verify, conditional on verdict |

Driver-side trigger for the new flips:

- Fires ONLY when the WU's `type` is `close`.
- Fires ONLY when the verify+squash succeeded AND
  `verdict_permits_terminal_flips(wu.verdict)` returns True.
- Fires AFTER the squash, BEFORE the `task_completed` event is
  built. The flips become driver-bookkeeping commits (per
  FEAT-2026-0002/G1-CLOSE/driver-incident: force-add through
  `.gitignore`).
- Each flip is a separate file write; the commit_bookkeeping
  helper handles the squash.

Reference binding rules under `.specfuse/rules/`. Driver owns git.

**Acceptance criteria.**

1. `loop.py` defines a helper
   `def fire_terminal_flips(wu: WorkUnit, feature_dir: Path,
   repo_root: Path) -> list[Path]`
   that, for a `close`-type WU whose verdict permits flips:
   - Reads the feature's gate graph from PLAN.md; identifies
     the terminal gate (last entry).
   - Flips `<feature_dir>/GATE-NN.md` frontmatter
     `status: awaiting_review → passed`. If already `passed`,
     skip silently. If neither, leave untouched and append a
     line to the returned `notes` (separate channel — see AC2).
   - Flips this feature's row in
     `<repo_root>/.specfuse/roadmap.md` status column
     `active → done` (use the same logic
     `auto_archive_feature` already uses for row matching).
   - Calls `auto_archive_feature(wu.feature_id, repo_root)`.
   - Returns the list of file Paths that were modified (for the
     bookkeeping commit's add list).
2. Helper signature is non-fatal: if any single flip's file is
   absent or already in the target state, the helper records a
   skip via `logging` (NOT a print) and continues. Only an
   exception inside the helper aborts.
3. `loop.py::run()` post-verify flow integrates `fire_terminal_
   flips`:
   - Right after `squash_commit(wu, head_before)` returns the
     SHA on a `passed` outcome (line ~1325), but BEFORE
     `task_completed` event is built and flushed.
   - Only for `wu.type == "close"`.
   - Only when `verdict_permits_terminal_flips(wu.verdict)`
     returns True. Otherwise skip (close WU's own status flip
     to `done` ALSO must be suppressed in that case — see AC4).
   - Modified files are committed via `commit_bookkeeping` with
     message `chore(loop): {wu.wu_id} terminal flips`.
4. **Verdict suppresses PLAN.md→done flip.** When
   `wu.type == "close"` and `verdict_permits_terminal_flips`
   returns False, the existing `backend.set_wu(wu, "status",
   DONE)` line (around L1323) must be inverted to leave PLAN.md
   `active` and write WU status as `done` BUT NOT flip PLAN.md.
   (Today the close WU writes PLAN.md status directly in its
   body; that direct write is what we're now gating. The WU's
   body author MUST condition its own PLAN.md flip on
   verdict — but T06 enforces driver-side that if the WU body
   "helpfully" flipped PLAN.md despite hedged verdict, the
   driver reverses that flip. Implementation: after squash, if
   verdict does NOT permit, re-read PLAN.md, set status back to
   `active`, and amend the bookkeeping commit.)
5. The existing gate-is-None hook in `run()` (around L1114)
   that called `auto_archive_feature` is REMOVED. The
   recursive-from-the-other-direction (firing on a gate-less
   future dispatch) was always a band-aid; the close WU now
   fires it explicitly.
6. `/wrap-feature` SKILL.md shrinks: remove the cosmetic gate-
   flip step (current §3), remove the roadmap-row reconciliation
   step (current §4 if present). Skill body now reads:
   read RETRO recap, push branch, open PR, merge advisory,
   next pick. The new SKILL.md must EXPLICITLY note the
   transfer ("As of FEAT-2026-0015/T06, terminal flips are
   driver-side; /wrap-feature no longer touches GATE-NN.md
   status or the roadmap row.").
7. New unit tests in `tests/test_terminal_flips.py`:
   - `test_fire_terminal_flips_met_verdict_flips_all_three` —
     temp feature with `GATE-02.md status: awaiting_review`,
     roadmap row `active`. Construct a `close` WU with
     `verdict: met`. Call helper; assert GATE flipped, roadmap
     flipped, auto-archive returned success.
   - `test_fire_terminal_flips_skips_when_already_passed` —
     idempotent re-fire.
   - `test_run_does_not_flip_on_met_locally_verdict` —
     integration: pass a fake close WU with `verdict:
     met_locally` through `execute_unit_attempt`+post-verify
     flow; assert GATE-NN.md and roadmap row both unchanged.
   - `test_run_reverts_plan_status_on_hedged_verdict` — close
     WU body flips PLAN.md to `done`; driver detects hedged
     verdict; PLAN.md reverts to `active` in the bookkeeping
     commit.
   - `test_wrap_feature_skill_no_longer_lists_gate_flip` —
     `grep -c "GATE-NN.md status" .specfuse/skills/wrap-feature/SKILL.md`
     returns 0 in the "step" content (or whatever pattern
     matches the moved-out instruction).
8. Symbol-existence:
   `python3 -c "from loop import fire_terminal_flips"` exits 0.
9. Existing test suite stays green:
   `python3 -m unittest discover tests` exits 0. Pay
   particular attention to any
   `tests/test_wrap_feature_*` or `tests/test_auto_archive_*`
   files — their assertions about call sites MUST be updated.

**Do not touch.** Exactly 4 files change:
- `.specfuse/scripts/loop.py` (helper + run() integration +
  remove old gate-is-None hook).
- `.specfuse/skills/wrap-feature/SKILL.md` (shrink).
- `tests/test_terminal_flips.py` (new file).
- One or more existing `tests/test_wrap_feature*.py` /
  `tests/test_auto_archive*.py` files MAY change ONLY if
  their assertions break under the new call-site geometry.
  ENUMERATE these in the RESULT block's `files_changed` and
  call them out by name; do NOT silently edit.

No edits to: `lint_plan.py` (no lint surface in T06),
`/draft-feature` skill, templates, other features' WU files,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** `code` gate set in
`.specfuse/verification.yml` (tests, lint, security, coverage).
Plus AC8 symbol-existence. Plus `python3
.specfuse/scripts/lint_plan.py
.specfuse/features/FEAT-2026-0015-closing-ceremony-restructure`
exits 0.

**Escalation triggers.**

1. **Completeness.** If `fire_terminal_flips` is absent from
   `loop.py` after your edits, emit `status: blocked`.
2. **§10 helper-duplication pre-flight.** Per
   `[FEAT-2026-0013/G1-CLOSE]` ship-fail cycle. Run:
   - `grep -rn "auto_archive_feature\|fire_terminal_flips\|GATE.*status.*passed\|roadmap.*status.*done" .specfuse/scripts/ .specfuse/skills/ tests/`
   - If `auto_archive_feature` is called from more than the two
     expected sites (the gate-is-None hook you are REMOVING +
     `fire_terminal_flips` you are ADDING), name every site and
     emit `status: blocked`.
   - If GATE-NN.md status writes appear in more than the
     `/wrap-feature` skill (which you remove) and the new
     helper, name them and emit `status: blocked`.
3. **Backwards-compat hazard.** Already-merged features
   (FEAT-2026-0001 through 0014) closed under the OLD
   ownership. Their roadmap rows + gate statuses already
   reflect their final state. Your change MUST NOT
   retroactively flip anything; the helper runs only on
   `close`-type WUs being dispatched RIGHT NOW. If you
   discover a scenario where the new helper would mutate a
   historical feature, emit `status: blocked`.
4. **Verdict-revert ergonomics.** AC4 requires the driver to
   REVERT a close WU's PLAN.md `done` write when verdict is
   hedged. This is unusual — the standard pattern is "agent
   wrote, driver respects." If the implementation feels like
   it's fighting the agent, consider whether the WU body
   should instead READ verdict before writing PLAN.md status
   (a `close` WU template change). Either approach is
   acceptable; do whichever leaves the smaller surface. If
   neither is clean, emit `status: blocked` with the
   ergonomics tradeoff named.
