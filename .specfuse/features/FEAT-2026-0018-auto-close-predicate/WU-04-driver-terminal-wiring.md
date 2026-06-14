---
id: FEAT-2026-0018/T04
type: implementation
effort: xhigh
status: pending
attempts: 0
planned_cost_usd: 2.50
generated_surfaces: []
produces_driver_helper:
  - maybe_auto_close_terminal
  - write_stub_retrospective_terminal
  - mark_close_wu_auto_closed
---

# Driver integration at terminal gate boundary

**Objective.** Wire `gate_eval.evaluate_auto_close` into `loop.py` at
the terminal-gate boundary so that when the predicate fires, the
driver skips the `close` WU dispatch, writes a stub
`RETROSPECTIVE.md`, fires `fire_terminal_flips`, and still passes the
FEAT-2026-0017 post-pass invariants — without inverting the
`set_gate(awaiting_review) → fire_terminal_flips → passed` sequence.

**Context.** This is `FEAT-2026-0018/T04`. Gate 1 (T01–T03) shipped
the pure `gate_eval.py` module + tests + CLI. T04 is the first wiring
WU: terminal-gate path only. T05 covers intermediate gates (option
A); T06 adds the override escape hatch. T05 depends on this WU
because T05 reuses the predicate-call site introduced here.

Read first:
- `PLAN.md` § "Predicate v1" (criteria 1–7) and § "Scope OUT" (the
  `auto_close: true` frontmatter shape, no new lifecycle status).
- `gate_eval.py` — module surface this WU consumes. The function is
  `evaluate_auto_close(feature_dir: Path, gate_id: int) →
  AutoCloseDecision`. `AutoCloseDecision` is frozen with
  `.auto`, `.reasons`, `.metrics`, `.gate_id`, `.feature_id`,
  `.predicate_version`.
- `loop.py:1693–1730` (`close_wu_for_terminal` discovery loop) and
  `loop.py:2005–2056` (current terminal-flip wiring + post-pass
  invariant guard).
- `loop.py:1232–1242` (`assert_retrospective_exists`) and
  `loop.py:1494–1567` (`assert_terminal_flips_fired`) — the
  invariants the auto path must STILL pass.
- `.specfuse/rules/never-touch.md` and `.specfuse/rules/result-contract.md`.

**§10 helper-duplication pre-flight.** Before authoring this WU's
edits, enumerate existing close-path symbols in `loop.py`:

```bash
grep -nE '^def (fire_terminal_flips|assert_terminal_flips_fired|verdict_permits_terminal_flips|assert_retrospective_exists|verify_post_pass_invariants)\b' .specfuse/scripts/loop.py
grep -nE '\bclose_wu_for_terminal\b' .specfuse/scripts/loop.py
grep -nE '\b(POST_PASS_INVARIANTS_BY_TYPE|MODEL_BY_TYPE|EFFORT_BY_TYPE)\b' .specfuse/scripts/loop.py
```

Every hit MUST be either (a) reused unchanged, or (b) named in this
WU's Do-not-touch with the reason. T04 reuses `fire_terminal_flips`,
`assert_terminal_flips_fired`, `verdict_permits_terminal_flips`
without modification. Do NOT re-implement any of these.

**Acceptance criteria.**

1. **New driver helper — terminal auto-close branch.** Add
   `maybe_auto_close_terminal(feature_dir, feature_id, gate,
   gates, events_path, repo_root) → tuple[bool, AutoCloseDecision]`
   to `loop.py`. Returns `(True, decision)` when predicate fires
   and the auto path was taken; `(False, decision)` when predicate
   refuses (caller falls through to the existing close-WU
   dispatch path). Imports `gate_eval` at module top
   (`from gate_eval import evaluate_auto_close, AutoCloseDecision`).
   The function:
   - Calls `evaluate_auto_close(feature_dir, gate.number)`.
   - On `decision.auto is False`: returns `(False, decision)`
     without side effects.
   - On `decision.auto is True`:
     - Calls `write_stub_retrospective_terminal(feature_dir,
       gate.number, decision)` (AC2).
     - Calls `mark_close_wu_auto_closed(close_wu_for_terminal,
       decision)` (AC3) on the close WU the discovery loop
       identified.
     - Appends an `auto_close_decision` event to `events.jsonl`
       carrying `{gate: gate.number, auto: true, reasons: [...],
       predicate_version: decision.predicate_version,
       metrics: { gate_total_cost, gate_budget,
                  blocked_human_events, replan_events }}`.
       Use the existing `build_event` + `flush_events` helpers.
     - Returns `(True, decision)`.

2. **Stub `RETROSPECTIVE.md` writer.** Add
   `write_stub_retrospective_terminal(feature_dir: Path,
   gate_number: int, decision: AutoCloseDecision) → None`. Writes
   (or appends to) `feature_dir / "RETROSPECTIVE.md"` such that the
   resulting file satisfies BOTH guards on terminal close:
   - `assert_retrospective_exists` (file non-empty).
   - `assert_retrospective_gate_section`
     (heading matches `^#{1,3} Gate {gate_number}\b`).

   The stub MUST include, in this exact shape (no cost-analysis
   header — no `verdict: met` close WU dispatches on auto path, so
   `assert_cost_analysis_section_when_met` is moot):

   ```markdown
   ## Gate {N} — auto-closed (predicate=v1)

   On-plan close; full retrospective ceremony skipped per
   `evaluate_auto_close`.

   - feature_id: {feature_id}
   - predicate_version: {decision.predicate_version}
   - gate_total_cost: ${metrics.gate_total_cost:.2f}
   - gate_budget: ${metrics.gate_budget:.2f} | <unset>
   - reasons: [] (auto=True)
   ```

   When `RETROSPECTIVE.md` already exists (intermediate gates that
   previously fired auto-close from T05 will have left content),
   APPEND the section; do not overwrite.

3. **Close-WU frontmatter flip.** Add
   `mark_close_wu_auto_closed(wu: WorkUnit | None, decision:
   AutoCloseDecision) → None`. On `wu is None` (no terminal close
   WU in this gate — e.g. legacy four-WU sequence): no-op. On
   `wu is not None`: rewrites the WU file's frontmatter so:
   - `status: done`
   - `auto_close: true`
   - `auto_close_reasons: [<decision.reasons>]` (empty list when
     `auto=True`, but include the key for downstream-tool
     discoverability).
   - `verdict: met` (so `assert_terminal_flips_fired` continues
     to gate on it via `verdict_permits_terminal_flips`).
   Body untouched. Frontmatter shape stays parseable by
   `read_frontmatter` + `_miniyaml`.

4. **Driver wiring at `set_gate(awaiting_review)` site
   (loop.py:2005).** Modify the existing terminal-flip block
   (lines 2005–2056 at draft time — verify line numbers haven't
   drifted; see Escalation #2) so that, immediately AFTER
   `backend.set_gate(gate, "awaiting_review")` +
   `on_gate_passed` + `flush_events(gate_reached)` +
   `commit_bookkeeping(...)`, BEFORE the
   `if close_wu_for_terminal is not None:` branch:

   ```python
   # FEAT-2026-0018/T04 — terminal auto-close branch
   is_terminal_gate = gate is gates[-1]
   auto_closed = False
   if is_terminal_gate and close_wu_for_terminal is not None:
       auto_closed, decision = maybe_auto_close_terminal(
           feature_dir, feature_id, gate, gates,
           events_path, repo_root=REPO_ROOT,
       )
       if auto_closed:
           commit_bookkeeping(
               [feature_dir / "RETROSPECTIVE.md",
                close_wu_for_terminal.file,
                events_path],
               f"chore(loop): {close_wu_for_terminal.wu_id} "
               f"auto-closed (predicate=v1)\n\n"
               f"Feature: {feature_id}",
           )
   ```

   Then guard the existing close-WU dispatch + flip block so it
   ONLY runs when `auto_closed is False`:

   ```python
   if close_wu_for_terminal is not None and not auto_closed:
       flip_paths = fire_terminal_flips(...)
       ...
       verify_post_pass_invariants(...)
   ```

   On `auto_closed is True`, the driver MUST still call
   `fire_terminal_flips` + `verify_post_pass_invariants` for the
   close WU. Move that fire+verify block into a helper
   `fire_and_verify_terminal_flips(close_wu, feature_dir, ...)` and
   call it from both branches (auto and non-auto), OR keep the
   existing block intact and add a parallel `auto_closed` branch
   that calls it unconditionally. EITHER is acceptable;
   duplication is not.

5. **FEAT-2026-0017 invariant guard fires on auto path.**
   `assert_terminal_flips_fired` reads
   `close_wu_for_terminal.file`'s frontmatter for `verdict: met`
   then checks gate-`passed` + roadmap-`done` + archive anchor.
   AC3 sets `verdict: met` so the guard's verdict check passes
   and the side-effect checks run. Verify this with a unit test
   in `tests/test_gate_eval_terminal_wiring.py` that:
   - Sets up a feature dir with a passing PLAN.md + minimal
     events.jsonl + a close-WU file.
   - Calls `maybe_auto_close_terminal`.
   - Asserts: returns `(True, decision)`; close-WU frontmatter
     now has `auto_close: true` + `verdict: met` + `status: done`;
     RETROSPECTIVE.md has the `## Gate N` section;
     events.jsonl gained one `auto_close_decision` event with
     `predicate_version: "v1"`.

6. **No regression on non-auto path.** A second test in the same
   file: when `evaluate_auto_close` returns `auto=False` (e.g.
   feature with a `blocked_human` event in chain),
   `maybe_auto_close_terminal` returns `(False, decision)`,
   leaves all files unchanged, and writes NO event. The caller
   then falls through to today's close-WU dispatch path
   unmodified.

7. **`auto_close_decision` event schema.** Validate the new event
   shape against `validate-event.py` if that script has a schema
   table for `event_type`. If the script's `KNOWN_EVENT_TYPES` (or
   equivalent) needs updating to include `auto_close_decision`,
   patch it in the same WU (it's adjacent driver infrastructure,
   not out-of-scope). Verify:
   `python3 .specfuse/scripts/validate-event.py
   --type auto_close_decision --field feature_id=FEAT-2026-0018
   --field gate=1 --field auto=true` exits 0 (or skip if the
   script does not support per-type validation).

8. **Symbol-existence checks** before declaring complete
   (per authoring-work-units §9). Every command must exit 0:

   ```bash
   # a. Three new helpers exist in loop.py
   test "$(grep -cE '^def (maybe_auto_close_terminal|write_stub_retrospective_terminal|mark_close_wu_auto_closed)\b' .specfuse/scripts/loop.py)" = "3"

   # b. gate_eval import added to loop.py
   grep -qE '^from gate_eval import.*evaluate_auto_close' .specfuse/scripts/loop.py

   # c. Predicate-call site present at the terminal-flip block
   grep -qE 'maybe_auto_close_terminal\(' .specfuse/scripts/loop.py

   # d. Existing close-WU branch is now guarded by `not auto_closed`
   grep -qE 'close_wu_for_terminal is not None and not auto_closed' .specfuse/scripts/loop.py

   # e. New test file lands
   test -f tests/test_gate_eval_terminal_wiring.py
   python3 -m unittest tests.test_gate_eval_terminal_wiring -v

   # f. Code gate clean
   python3 -m unittest discover tests

   # g. Working-tree diff actually edits loop.py (hollow-pass guard)
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/loop.py'
   git diff --name-only HEAD | grep -qx 'tests/test_gate_eval_terminal_wiring.py'
   ```

   If any check fails, emit `status: blocked` naming the failing
   check + observed output. Do NOT flip this WU's `status` field
   as a substitute for shipping the code (priors:
   FEAT-2026-0007/T04, FEAT-2026-0008/T01, FEAT-2026-0017/T01).

**Do not touch.** Files this WU may edit / create:
- `.specfuse/scripts/loop.py` (terminal-flip block + three new
  helpers + one `import` line)
- `tests/test_gate_eval_terminal_wiring.py` (new)
- `.specfuse/scripts/validate-event.py` (only if known-event-type
  table needs `auto_close_decision`)

No edits to: `gate_eval.py` (T01 owns the predicate surface; T04
consumes it unchanged), `tests/test_gate_eval.py` and
`tests/test_gate_eval_calibration.py` (T02/T03 own; do not modify),
the intermediate-gate wiring path (T05's job; T04 stays terminal),
`lint_plan.py`, other features, skills, secrets, `.git/`. Driver
owns all git; edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in
`.specfuse/verification.yml` (tests, coverage ≥ 90%, lint,
security, zero compiler warnings). Plus AC8's symbol-existence /
import / hollow-pass checks. Plus the two new unit tests in
`tests/test_gate_eval_terminal_wiring.py` (AC5 + AC6).

**Escalation triggers.**

1. **Completeness.** AC8 command (a) does not return `3`, OR (b)
   matches nothing, OR (c)/(d) matches nothing, OR (e)/(f) raises,
   OR (g) returns no lines → emit `status: blocked`. The wiring
   is incomplete; do NOT flip frontmatter as substitute.
2. **Wiring-site drift.** The terminal-flip block was at
   `loop.py:2005–2056` at draft time. If the line range has moved
   (refactor, indent change, FEAT-2026-0019+ rewrites), update
   the edit location but keep the sequencing invariant:
   `set_gate(awaiting_review) → predicate-call → (auto branch:
   fire_terminal_flips + verify_post_pass_invariants) OR
   (non-auto branch: existing close-WU dispatch path)`. If the
   refactor inverted the sequence such that
   `verify_post_pass_invariants` no longer observes the flips,
   emit `status: blocked` — operator decides whether to rewire
   here or revert the upstream refactor.
3. **Stub-RETROSPECTIVE shape rejected by guard.** If AC5's unit
   test fails on `assert_retrospective_gate_section` because the
   `## Gate N` heading regex didn't match the AC2 stub template,
   adjust the heading text in the stub (NOT the regex in
   `assert_retrospective_gate_section`). If both heading
   variations fail, emit `status: blocked` — the stub's shape is
   borderline; operator refines.
4. **Invariant guard misses auto path.** If
   `assert_terminal_flips_fired` returns early on auto path
   because `verdict != "met"` (AC3 forgot to set `verdict: met`),
   the auto path is silently bypassing the FEAT-2026-0017
   wiring-race guard — exactly the hole T04 was instructed to
   avoid. Fix AC3 or emit `status: blocked` with the test
   failure. Do NOT relax `verdict_permits_terminal_flips`.
5. **`gate_eval` import bleed.** If satisfying the import surface
   pulls additional symbols from `gate_eval` beyond
   `evaluate_auto_close` + `AutoCloseDecision`, document why in
   the RESULT block summary. The architectural contract is a
   narrow import surface; broadening it should be a deliberate
   call.
6. **Validate-event schema mismatch.** If `validate-event.py`'s
   known-event-type table refuses `auto_close_decision` and AC7
   patch becomes non-trivial (e.g. requires schema editing in
   another file), split it into a `T04H` hygiene WU per
   authoring-work-units §7 — do not silently weaken the
   validator.
