---
id: FEAT-2026-0018/T05
type: implementation
effort: xhigh
status: done
attempts: 2
planned_cost_usd: 2.20
generated_surfaces: []
produces_driver_helper:
  - maybe_auto_close_intermediate
  - append_stub_retrospective_intermediate
duration_seconds: 1040.325
cost_usd: 2.653762
input_tokens: 203
output_tokens: 46390
---

# Driver integration at intermediate gate boundary (option A)

**Objective.** Wire `gate_eval.evaluate_auto_close` into the
intermediate-gate close path in `loop.py` so that when the predicate
fires for a non-terminal gate, the driver skips the
`close-intermediate` WU dispatch, appends a stub gate-section to
`RETROSPECTIVE.md`, marks the close-intermediate WU `auto_close:
true`, and STILL dispatches the gate's `plan-next` WU so the next
gate's substantives get drafted (option A from PLAN.md).

**Context.** This is `FEAT-2026-0018/T05`. Depends on T04
(`FEAT-2026-0018/T04`) because T05 reuses the predicate-call site,
the stub-frontmatter helper, and the event-emission pattern T04
introduces. T05 is intermediate-gate-only; do not touch the
terminal-gate branch T04 owns.

Option A (per PLAN.md): on intermediate auto-close, skip
`close-intermediate` but DO dispatch `plan-next` so the next gate
gets drafted before the loop halts at `awaiting_review`. Option B
(drafts upfront) and Option C (no intermediate auto-close) were
considered and rejected; T05 implements A only. Re-check this
choice against `RETROSPECTIVE.md` gate-1 evidence at arm time —
see Open verifications in `GATE-02-REVIEW.md`.

Read first:
- `PLAN.md` § "Predicate v1" (criteria same as terminal — predicate
  is gate-agnostic; only the post-fire actions differ).
- T04's WU file (`WU-04-driver-terminal-wiring.md`) — reuse the
  helpers it adds, do NOT re-implement.
- `loop.py` close-intermediate dispatch path — find with:
  `grep -nE 'close-intermediate|close_intermediate' loop.py`.
- `loop.py:1353–1375` (`assert_retrospective_gate_section`) — the
  guard the appended stub section must satisfy.
- `.specfuse/rules/never-touch.md`, `.specfuse/rules/result-contract.md`.

**§10 helper-duplication pre-flight.** Before authoring this WU's
edits, enumerate existing close-path symbols T04 added or that
already exist:

```bash
grep -nE '^def (maybe_auto_close_terminal|write_stub_retrospective_terminal|mark_close_wu_auto_closed|fire_terminal_flips|assert_terminal_flips_fired|verdict_permits_terminal_flips)\b' .specfuse/scripts/loop.py
grep -nE '\bclose_wu_for_terminal\b|\bclose-intermediate\b' .specfuse/scripts/loop.py
grep -nE 'plan-next|plan_next' .specfuse/scripts/loop.py
```

If T04 already landed `mark_close_wu_auto_closed`, T05 MUST reuse
it (it's a gate-agnostic frontmatter writer). If T04 named its
stub-writer `write_stub_retrospective_terminal` (terminal-only),
T05 adds a sibling `append_stub_retrospective_intermediate`
that APPENDS (not overwrites) a `## Gate N` section. Do not
duplicate the file-writing logic — extract a private
`_write_retro_section(retro_path, gate_n, decision, mode)` if both
T04 and T05 need it (`mode` = `"create"` | `"append"`).

**Acceptance criteria.**

1. **New driver helper — intermediate auto-close branch.** Add
   `maybe_auto_close_intermediate(feature_dir, feature_id, gate,
   gates, events_path, repo_root, close_intermediate_wu,
   plan_next_wu) → tuple[bool, AutoCloseDecision]` to `loop.py`.
   Returns `(True, decision)` when predicate fires and the auto
   path was taken; `(False, decision)` when predicate refuses
   (caller falls through to the existing close-intermediate
   dispatch).
   On `decision.auto is True`:
   - Calls `append_stub_retrospective_intermediate(feature_dir,
     gate.number, decision)` (AC2).
   - Calls `mark_close_wu_auto_closed(close_intermediate_wu,
     decision)` — reuse T04's helper unchanged. Sets
     `auto_close: true`, `auto_close_reasons: [...]`,
     `status: done`. Do NOT set `verdict: met` on
     close-intermediate WUs (close-intermediate has no terminal
     verdict to gate on).
   - Appends an `auto_close_decision` event to `events.jsonl`
     carrying `{gate: gate.number, gate_type: "intermediate",
     auto: true, reasons: [...], plan_next_dispatched: true,
     predicate_version: decision.predicate_version}`.
   - Returns `(True, decision)`. The CALLER is responsible for
     proceeding to dispatch `plan_next_wu` afterward (AC4).

2. **Intermediate stub appender.** Add
   `append_stub_retrospective_intermediate(feature_dir: Path,
   gate_number: int, decision: AutoCloseDecision) → None`. Must:
   - Create `RETROSPECTIVE.md` if absent (intermediate gate 1
     scenario where prior gate didn't write one).
   - APPEND (never overwrite) a `## Gate {N} — auto-closed
     (predicate=v1)` section satisfying
     `assert_retrospective_gate_section`'s
     `^#{1,3} Gate {N}\b` regex.
   - Section body shape:
     ```markdown
     ## Gate {N} — auto-closed (predicate=v1)

     On-plan intermediate close; full close-intermediate ceremony
     skipped per `evaluate_auto_close`. `plan-next` WU dispatched
     to draft gate {N+1}.

     - feature_id: {feature_id}
     - predicate_version: {decision.predicate_version}
     - gate_total_cost: ${metrics.gate_total_cost:.2f}
     - gate_budget: ${metrics.gate_budget:.2f} | <unset>
     - reasons: [] (auto=True)
     ```

3. **Driver wiring at intermediate close-WU discovery site.**
   Find the loop where `close_intermediate` WUs are resolved
   (same per-WU dispatch loop that resolves
   `close_wu_for_terminal` for terminal gates — confirm with the
   `grep -nE` pre-flight above). Immediately BEFORE dispatching
   a `close-intermediate` WU (i.e. before the
   `dispatch_one(wu)` call for that WU), insert:

   ```python
   # FEAT-2026-0018/T05 — intermediate auto-close branch
   if wu.type == "close-intermediate":
       # Look ahead to the gate's plan-next WU for the AC4 dispatch
       plan_next_wu = next(
           (w for w in gate_wus if w.type == "plan-next"),
           None,
       )
       auto_closed, decision = maybe_auto_close_intermediate(
           feature_dir, feature_id, gate, gates,
           events_path, REPO_ROOT, wu, plan_next_wu,
       )
       if auto_closed:
           commit_bookkeeping(
               [feature_dir / "RETROSPECTIVE.md",
                wu.file, events_path],
               f"chore(loop): {wu.wu_id} auto-closed "
               f"(predicate=v1)\n\nFeature: {feature_id}",
           )
           # AC4 — still dispatch plan-next; do not skip it
           done_ids.add(wu.wu_id)
           continue   # skip close-intermediate dispatch, fall to next iter
   ```

   The exact statement (`continue` vs structured branch) depends
   on the dispatch loop's existing control flow; the binding
   contract is: when `auto_closed is True`, the
   `close-intermediate` WU's `dispatch_one` MUST NOT be called.

4. **`plan-next` MUST still dispatch on auto-intermediate.** AC3's
   wiring records `done_ids.add(wu.wu_id)` for the SKIPPED
   close-intermediate WU but does NOT add the plan-next WU's id.
   The dispatch loop then resolves `plan_next_wu` on its next
   iteration (its `depends_on` is satisfied because the
   close-intermediate is now `done`) and dispatches it. Verify
   with a unit test (AC6) that observes `dispatch_one` being
   called for `plan_next_wu` after the auto-intermediate skip.

5. **Stub-section appended, not duplicated.** The stub appender
   must be idempotent under re-arm: if the loop is restarted on
   a previously auto-closed gate (e.g. operator re-arms via
   `--force-full-close`), the appender SHOULD detect an existing
   `## Gate {N} — auto-closed` section and skip rather than
   stack a second. Implementation hint: read the file, regex
   `^##\s+Gate\s+{N}\b.*auto-closed`; if present, return
   without writing.

6. **Unit tests** in `tests/test_gate_eval_intermediate_wiring.py`:
   - `test_auto_close_intermediate_fires_when_predicate_passes`
     — mocked / fixture feature dir, gate 1 of a two-gate
     feature, all checks passing, no events. Asserts:
     `maybe_auto_close_intermediate` returns `(True, decision)`;
     `RETROSPECTIVE.md` has `## Gate 1 — auto-closed`;
     close-intermediate WU frontmatter has `auto_close: true`
     + `status: done` (no `verdict: met`); events.jsonl gained
     `auto_close_decision` event.
   - `test_auto_close_intermediate_refuses_on_blocked_human`
     — fixture with `blocked_human` event for one substantive WU.
     Asserts: returns `(False, decision)`; files unchanged.
   - `test_plan_next_dispatched_after_auto_intermediate` — full
     dispatch-loop scenario (or close enough). Asserts:
     `close-intermediate` WU never enters `dispatch_one` (mock
     it); `plan-next` WU's `dispatch_one` is called exactly once.
   - `test_idempotent_append_on_re_arm` — call
     `append_stub_retrospective_intermediate` twice in a row;
     assert file content has exactly one `## Gate N` section.

7. **Symbol-existence checks** before declaring complete
   (per authoring-work-units §9). Every command must exit 0:

   ```bash
   # a. Two new helpers exist in loop.py
   test "$(grep -cE '^def (maybe_auto_close_intermediate|append_stub_retrospective_intermediate)\b' .specfuse/scripts/loop.py)" = "2"

   # b. T04's mark_close_wu_auto_closed is reused (not redefined)
   test "$(grep -cE '^def mark_close_wu_auto_closed\b' .specfuse/scripts/loop.py)" = "1"

   # c. Predicate-call site exists in the dispatch loop
   grep -qE 'maybe_auto_close_intermediate\(' .specfuse/scripts/loop.py

   # d. New test file lands + passes
   test -f tests/test_gate_eval_intermediate_wiring.py
   python3 -m unittest tests.test_gate_eval_intermediate_wiring -v

   # e. Code gate clean
   python3 -m unittest discover tests

   # f. Working-tree diff actually edits loop.py (hollow-pass guard)
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/loop.py'
   git diff --name-only HEAD | grep -qx 'tests/test_gate_eval_intermediate_wiring.py'
   ```

   If any check fails, emit `status: blocked` naming the failing
   check + observed output. Do NOT flip this WU's `status` field
   as a substitute for shipping the code.

**Do not touch.** Files this WU may edit / create:
- `.specfuse/scripts/loop.py` (intermediate dispatch-loop branch
  + two new helpers; the terminal-flip block T04 owns is NOT
  modified)
- `tests/test_gate_eval_intermediate_wiring.py` (new)

No edits to: `gate_eval.py`, T04's terminal-gate wiring (only
reuse via call), T02/T03's tests, `lint_plan.py`, other features,
skills, secrets, `.git/`. Driver owns all git; edit files only.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in
`.specfuse/verification.yml` (tests, coverage ≥ 90%, lint,
security, zero warnings). Plus AC7's symbol-existence checks.
Plus AC6's four unit tests in
`tests/test_gate_eval_intermediate_wiring.py`.

**Escalation triggers.**

1. **Completeness.** AC7 command (a) does not return `2`, OR
   (b) does not return `1`, OR (c)/(d)/(e) fails, OR (f) returns
   no lines → emit `status: blocked`. Wiring is incomplete.
2. **Dispatch-loop control flow doesn't admit a clean skip.** If
   the loop's structure (sort order, dependency resolution,
   `done_ids` propagation) makes "skip close-intermediate, then
   dispatch plan-next" awkward enough to require restructuring
   the dispatch loop itself, emit `status: blocked` — that is
   T05 expanding scope. Operator decides whether to refactor the
   loop or change the option (A → C: no intermediate
   auto-close).
3. **`plan-next` does NOT dispatch after auto-skip.** AC6
   `test_plan_next_dispatched_after_auto_intermediate` failing
   means option A's contract is broken — the entire feature loop
   loses the "next gate gets drafted" property. Emit
   `status: blocked` with the dispatch-loop trace; do NOT ship
   a partial fix.
4. **Append duplicates on re-arm.** AC5 idempotence test fails
   → fix the dedup regex. If it cannot reliably dedup (e.g.
   operator edits between runs in unpredictable ways), document
   in the RESULT and flag for Open Verifications.
5. **T04 helpers absent.** If `mark_close_wu_auto_closed` is
   missing because T04 didn't land it (pre-flight grep shows
   `0` matches), emit `status: blocked` with the missing-helper
   name. T05 does NOT re-implement T04's deliverables; the gate
   dependency was supposed to enforce ordering.
