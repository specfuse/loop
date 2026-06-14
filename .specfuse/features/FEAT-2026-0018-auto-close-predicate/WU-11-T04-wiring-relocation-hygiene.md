---
id: FEAT-2026-0018/T11H
type: implementation
effort: medium
status: done
attempts: 2
planned_cost_usd: 0.80
generated_surfaces: []
produces_driver_helper: []
duration_seconds: 1625.042
cost_usd: 3.647896
input_tokens: 105
output_tokens: 68376
---

# Hygiene: relocate T04 terminal auto-close wiring into the per-WU dispatch loop

**Objective.** Relocate the terminal auto-close branch from its current
post-gate-completion site (`loop.py:2308`) into the per-WU dispatch
loop, mirroring T05's intermediate-close branch (`loop.py:1985`). The
relocated branch fires PRE-dispatch when the loop selects a `close`-type
WU on the terminal gate — so the predicate's `auto=True` verdict
actually skips the close-WU dispatch instead of merely being checked
after the WU already ran.

**Context.** This is `FEAT-2026-0018/T11H`. Hygiene WU surfaced by gate
3's recursive-dogfood self-test: T04 helpers
(`maybe_auto_close_terminal`, `write_stub_retrospective_terminal`,
`mark_close_wu_auto_closed`) ship and work; the predicate ships and
correctly returns `auto=True` for gate 3 of this very feature
(`python3 .specfuse/scripts/gate_eval.py backtest FEAT-2026-0018
--gate 3` → `auto=True`, no reasons, `gate_total_cost: $2.34 /
gate_budget: $8.00`). But the terminal-gate dispatch of `G3-CLOSE`
still ran the full close ceremony — agent diagnosed in
`RETROSPECTIVE.md`'s `# Feature-arc verdict` section: the T04 wiring
is at `loop.py:2308` (the post-gate-completion terminal-flip block),
which runs AFTER the per-WU dispatch loop has already selected and
dispatched `G3-CLOSE`. T05's intermediate branch is at
`loop.py:1985` — INSIDE the per-WU dispatch loop, PRE-dispatch — and
correctly skips intermediate-close dispatch when predicate fires.
Relocate T04's branch to the same site to mirror T05's pattern.

This WU satisfies the gate-extension test
(`[FEAT-2026-0003/G4-LESSONS]`): scope is hours of work
(a single-file relocation), evidence is contiguous on this branch
(retrospective + gate_eval CLI output), and the trigger is a
falsifiable structural claim (predicate `auto=True` did not skip the
dispatched close WU).

Reference binding rules at `.specfuse/rules/`. The driver owns all
git; edit files only.

Read first:
- `.specfuse/scripts/loop.py:1985–2010` — T05's intermediate-close
  branch. Use this as the structural template.
- `.specfuse/scripts/loop.py:2308–2356` — T04's current
  terminal-close branch. Code to relocate.
- `.specfuse/scripts/loop.py:1291–1320` — `maybe_auto_close_terminal`
  function (signature + behavior; do NOT modify, only the call site
  moves).
- `RETROSPECTIVE.md` # Feature-arc verdict section — agent's
  diagnosis of the bug; ground truth for the fix's intent.

**§10 helper-duplication pre-flight.** Confirm the existing wiring
sites before authoring:

```bash
# Confirm T05's intermediate branch lives inside the per-WU loop
grep -nE 'wu\.type == "close-intermediate"' .specfuse/scripts/loop.py

# Confirm T04's terminal branch lives in the post-loop block
grep -nE 'is_terminal_gate and close_wu_for_terminal' .specfuse/scripts/loop.py

# Confirm maybe_auto_close_terminal signature
grep -nE '^def maybe_auto_close_terminal' .specfuse/scripts/loop.py
```

The relocation must:
1. ADD a new branch inside the per-WU dispatch loop, alongside the
   existing T05 close-intermediate branch, gated on
   `wu.type == "close" and is_terminal_gate(...) and not _override_active`.
2. The terminal-ness check should be a small local helper or inline
   expression (the dispatched WU's gate is the LAST gate AND the WU
   is a terminal close). Mirror how `gate is gates[-1]` is determined
   in the post-loop block.
3. REMOVE the post-loop terminal auto-close branch (lines 2308–2329
   inclusive — the `if is_terminal_gate and ...` block and its `elif
   ... _override_active` sibling). Keep the existing
   `_fire_and_verify_terminal_flips` invocation in the post-loop
   block guarded by `if close_wu_for_terminal is not None and not
   auto_closed:` — that path still runs for non-auto closes.
4. The `_override_active` override path (currently in the post-loop
   block's `elif`) must be preserved in the new in-loop location:
   when override is active, emit the same `auto_close_decision`
   event with `override: true` and fall through to dispatch.

**Acceptance criteria.**

1. **Per-WU loop branch added** for terminal close. Inside the
   per-WU dispatch loop in `loop.py` (the same loop that contains
   T05's `if wu.type == "close-intermediate" and not _override_active:`
   branch), add an analogous branch:

   ```python
   # FEAT-2026-0018/T11H — terminal auto-close branch (relocated from post-loop)
   if wu.type == "close" and gate is gates[-1] and not _override_active:
       _auto_closed, _decision = maybe_auto_close_terminal(
           feature_dir, feature_id, gate, gates,
           events_path, wu, repo_root=REPO_ROOT,
       )
       if _auto_closed:
           commit_bookkeeping(
               [feature_dir / "RETROSPECTIVE.md",
                wu.file, events_path],
               f"chore(loop): {wu.wu_id} auto-closed "
               f"(predicate=v1)\n\nFeature: {feature_id}",
           )
           rc = _fire_and_verify_terminal_flips(
               wu, feature_dir, events_path, feature_id,
           )
           if rc:
               return rc
           done_ids.add(wu.wu_id)
           continue
   elif wu.type == "close" and gate is gates[-1] and _override_active:
       flush_events(events_path, [build_event(
           "auto_close_decision", wu.wu_id, {
               "gate": gate.number,
               "auto": False,
               "reasons": [_override_reason],
               "predicate_version": "v1",
               "override": True,
           }
       )])
       # Fall through to existing close-WU dispatch path
   ```

   Placement: immediately after the T05 close-intermediate branch +
   its `elif` override sibling, before any other type-specific
   handling. Same structural shape as T05's branch (predicate call,
   commit_bookkeeping if auto, terminal-flips invocation, mark done +
   continue).

2. **Post-loop terminal auto-close block removed.** The existing
   `# FEAT-2026-0018/T04 — terminal auto-close branch` block at
   `loop.py:2308–2329` (the `if is_terminal_gate and
   close_wu_for_terminal is not None and not _override_active:`
   conditional and its `elif` sibling) is DELETED. The subsequent
   `if close_wu_for_terminal is not None and not auto_closed:` block
   continues to fire (it dispatches the close WU when no auto-close
   happened — this path runs unchanged on non-auto terminal gates).

   The local `auto_closed = False` initialization can be REMOVED
   because nothing in the post-loop block now depends on it; or
   replaced with `auto_closed = False  # always False in post-loop
   path; in-loop branch handles auto`. Either is acceptable; the
   guarding `not auto_closed` in the subsequent dispatch block
   becomes a tautology (always True in this path) — simplify the
   condition to `if close_wu_for_terminal is not None:` if you
   prefer, OR keep `not auto_closed` for safety and code clarity.

3. **No changes to `maybe_auto_close_terminal` function.** The
   relocation moves the CALL site only; the function definition
   stays where it is at `loop.py:1291`.

4. **No changes to T05's intermediate branch** at
   `loop.py:1985`. T05 already wires correctly.

5. **Recursive self-test passes.** After the relocation, running
   the loop driver from a clean gate-3 awaiting_review state (with
   `G3-CLOSE` reset to `pending`, `attempts: 0`, and no `verdict`
   field) should:
   - See `G3-CLOSE` as the next pending WU in gate 3.
   - Hit the new in-loop terminal-close branch.
   - Call `maybe_auto_close_terminal`, which returns `auto=True`
     (matching the manual CLI check).
   - Skip `G3-CLOSE` dispatch.
   - Write the stub `RETROSPECTIVE.md` section + mark `G3-CLOSE`
     `auto_close: true` + `verdict: met` + `status: done`.
   - Fire terminal flips: PLAN.md `done`, roadmap row `done`,
     archive anchor written.
   - Emit `auto_close_decision` event with `auto: true,
     reasons: []`.

   This AC is the load-bearing falsifiable claim for T11H. If the
   relocated wiring does not auto-close gate 3 on the re-run after
   this WU lands, emit `status: blocked`.

6. **Unit tests for T04 stay green.** Existing tests in
   `tests/test_loop_auto_close_terminal.py` (or whichever file
   covers T04's helpers) must still pass after the relocation.
   The helpers themselves are unchanged; tests target the helpers,
   not the call site. If existing tests fail, investigate whether
   the test was indirectly depending on the call-site location
   (e.g., import side effects) and surface in RESULT.

7. **Symbol-existence check** before declaring complete:

   ```bash
   # a. New in-loop terminal-close branch exists
   grep -qE 'wu\.type == "close" and gate is gates\[-1\]' .specfuse/scripts/loop.py

   # b. Old post-loop block removed (no more is_terminal_gate variable used to gate maybe_auto_close_terminal)
   ! grep -qE 'if is_terminal_gate and close_wu_for_terminal is not None and not _override_active' .specfuse/scripts/loop.py

   # c. maybe_auto_close_terminal is still defined (function unchanged)
   grep -qE '^def maybe_auto_close_terminal' .specfuse/scripts/loop.py

   # d. T05's intermediate branch unchanged
   grep -qE 'wu\.type == "close-intermediate" and not _override_active' .specfuse/scripts/loop.py

   # e. Existing tests pass
   python3 -m unittest discover tests

   # f. Working-tree diff actually touches loop.py
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/loop.py'
   ```

   If any check fails, emit `status: blocked` naming the failing
   command. Do NOT flip this WU's frontmatter `status` field as a
   substitute.

**Do not touch.** Exactly 1 file changes:
- `.specfuse/scripts/loop.py` (relocate one branch, delete the
  post-loop counterpart, no other changes)

No edits to: `gate_eval.py`, `lint_plan.py`, tests (the helpers
this WU touches are pure-call-site-relocation; tests that target
helper behavior should keep passing without modification — if a
test fails, that's the diagnostic), other features, secrets,
`.git/`. The driver owns all git; edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in
`.specfuse/verification.yml` (tests, lint, security, coverage).
Plus AC7's existence checks.

**Escalation triggers.**

1. **Completeness.** AC7 commands (a)–(f) any failing → emit
   `status: blocked`. Especially (a) and (b): the relocation MUST
   move the branch — leaving both sites active would dispatch the
   predicate twice per terminal gate, polluting events.jsonl.
2. **Test regression on existing tests.** If the relocation breaks
   a test that previously passed against the post-loop call site,
   the relocation accidentally changed semantics (e.g., the
   per-WU dispatch loop's local variables don't match the
   post-loop's). Surface the failing test name in RESULT and emit
   `status: blocked`. Do NOT modify tests to make them pass — the
   semantic invariant is that the relocated call site produces the
   same outcome on auto-fire as the old site.
3. **Ambiguous `gate is gates[-1]` check.** If the per-WU dispatch
   loop's scope doesn't have `gates` or `gate` accessible as
   expected, surface the actual scope and propose a substitute
   (e.g., comparing `gate.number == max(g.number for g in gates)`).
   Do NOT silently change the terminal-gate detection — accuracy
   matters because mid-feature gates must NOT trigger the terminal
   branch.
4. **`_override_active` / `_override_reason` scope.** Per T06, these
   are computed once per gate iteration. If they're not in scope
   inside the per-WU dispatch loop, propose hoisting their
   computation or accessing them via outer scope. Do NOT
   reimplement the override resolver inline.
