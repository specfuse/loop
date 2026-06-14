---
id: FEAT-2026-0018/T06
type: implementation
effort: medium
status: draft
attempts: 0
planned_cost_usd: 0.80
generated_surfaces: []
produces_driver_helper:
  - resolve_auto_close_override
---

# `--force-full-close` CLI flag + `auto_close_disabled` PLAN.md override

**Objective.** Add two operator escapes that bypass predicate
consultation entirely and run the existing close path: a CLI flag
`--force-full-close <feature-id>` on `loop.py`, and a PLAN.md
frontmatter field `auto_close_disabled: true`. Both are short-
circuits: when either is set, the driver does NOT call
`evaluate_auto_close` and the close-WU dispatch path runs unmodified
exactly as it did before this feature.

**Context.** This is `FEAT-2026-0018/T06`. Depends on T05
(`FEAT-2026-0018/T05`) because the override must hook BOTH wiring
sites T04 and T05 added (terminal + intermediate). Lands last in
the gate so the bypass surface is centralized once both wiring
sites exist.

The `auto_close_disabled` PLAN.md check is already implemented in
`gate_eval.evaluate_auto_close` (returns `auto=False,
reasons=["auto_close_disabled_per_plan"]` when set — see
`gate_eval.py:292`). T06 ADDS the CLI flag and ensures the driver
honors both surfaces at the wiring sites. The predicate's existing
short-circuit means the CLI flag's behavior is "do not even call
`evaluate_auto_close`" — same observable outcome (existing close
path runs), one fewer file read.

Read first:
- `gate_eval.py:285–302` — the `auto_close_disabled` short-circuit
  the predicate already implements.
- T04 + T05's WU files — the `maybe_auto_close_*` call sites this
  WU must guard.
- `loop.py` `argparse` setup — find with `grep -nE
  'argparse|ArgumentParser|add_argument' loop.py`.
- `.specfuse/rules/never-touch.md`, `result-contract.md`.

**§10 helper-duplication pre-flight.** Before authoring:

```bash
grep -nE 'add_argument|ArgumentParser' .specfuse/scripts/loop.py
grep -nE 'auto_close_disabled' .specfuse/scripts/loop.py .specfuse/scripts/gate_eval.py
grep -nE 'maybe_auto_close_(terminal|intermediate)' .specfuse/scripts/loop.py
```

The argparse setup is one location; reuse it. The
`auto_close_disabled` check in `gate_eval.py` is the single source
of truth for the PLAN.md side — do NOT add a second check site.

**Acceptance criteria.**

1. **CLI flag.** `loop.py` accepts
   `--force-full-close <feature-id>` as a new argument. Stored on
   the argparse namespace as `args.force_full_close`. When set,
   its value must equal the feature ID being processed (or the
   `--feature` argument's value); if mismatched, fail fast at
   startup with a clear error (`loop.py: --force-full-close
   FOO does not match feature being processed BAR`) and exit
   non-zero. Rationale: prevents the flag silently no-oping when
   the operator misnames the feature.

2. **Override resolver.** Add
   `resolve_auto_close_override(args, feature_dir) → tuple[bool,
   str]` to `loop.py`. Returns `(override_active, reason_string)`.
   - When `args.force_full_close == feature_id` → `(True,
     "force_full_close_cli_flag")`.
   - When PLAN.md frontmatter has `auto_close_disabled: true` →
     `(True, "auto_close_disabled_per_plan")`.
   - Otherwise → `(False, "")`.
   The reason string is logged + included in any `auto_close_decision`
   event when the override fires.

3. **Wiring at T04's call site (terminal).** Guard the
   `maybe_auto_close_terminal` call from AC4 of T04:

   ```python
   override_active, override_reason = resolve_auto_close_override(
       args, feature_dir,
   )
   if is_terminal_gate and close_wu_for_terminal is not None and not override_active:
       auto_closed, decision = maybe_auto_close_terminal(...)
       ...
   elif override_active:
       # Log the bypass for audit trail; existing close path runs below
       flush_events(events_path, [build_event(
           "auto_close_decision", close_wu_for_terminal.wu_id, {
               "gate": gate.number,
               "auto": False,
               "reasons": [override_reason],
               "predicate_version": "v1",
               "override": True,
           }
       )])
   ```

   The existing close-WU dispatch path (today's behavior) runs
   unchanged in the override case.

4. **Wiring at T05's call site (intermediate).** Same guard
   structure around `maybe_auto_close_intermediate`:

   ```python
   override_active, override_reason = resolve_auto_close_override(
       args, feature_dir,
   )
   if wu.type == "close-intermediate" and not override_active:
       auto_closed, decision = maybe_auto_close_intermediate(...)
       ...
   elif wu.type == "close-intermediate" and override_active:
       flush_events(events_path, [build_event(
           "auto_close_decision", wu.wu_id, {
               "gate": gate.number,
               "gate_type": "intermediate",
               "auto": False,
               "reasons": [override_reason],
               "predicate_version": "v1",
               "override": True,
           }
       )])
       # Fall through to existing close-intermediate dispatch
   ```

   Both wiring sites can be DRY'd by hoisting the
   `resolve_auto_close_override` call to once per gate
   iteration; either shape is acceptable.

5. **Unit tests** in `tests/test_force_full_close.py`:
   - `test_cli_flag_bypasses_predicate_terminal` — argparse
     receives `--force-full-close FEAT-2026-0018`; on terminal
     close, `maybe_auto_close_terminal` is NOT called; existing
     close-WU dispatch runs.
   - `test_cli_flag_bypasses_predicate_intermediate` — same for
     intermediate.
   - `test_cli_flag_mismatched_feature_id_exits_nonzero` — flag
     value differs from feature being processed; startup error.
   - `test_plan_frontmatter_disabled_bypasses_predicate` — PLAN.md
     has `auto_close_disabled: true`; even without CLI flag,
     `maybe_auto_close_*` is not called.
   - `test_no_flag_no_plan_field_predicate_runs_normally` —
     baseline: both off, predicate consulted as in T04/T05.

6. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. New helper exists in loop.py
   test "$(grep -cE '^def resolve_auto_close_override\b' .specfuse/scripts/loop.py)" = "1"

   # b. CLI flag registered
   grep -qE "['\"]--force-full-close['\"]" .specfuse/scripts/loop.py

   # c. Both call sites guarded
   test "$(grep -cE 'resolve_auto_close_override\(' .specfuse/scripts/loop.py)" -ge "1"
   grep -qE 'not override_active' .specfuse/scripts/loop.py

   # d. Tests land + pass
   test -f tests/test_force_full_close.py
   python3 -m unittest tests.test_force_full_close -v

   # e. Code gate clean
   python3 -m unittest discover tests

   # f. Working-tree diff actually edits loop.py
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/loop.py'
   git diff --name-only HEAD | grep -qx 'tests/test_force_full_close.py'
   ```

   If any check fails, emit `status: blocked` naming the failing
   check + observed output. Do NOT flip this WU's `status` field
   as a substitute for shipping the code.

**Do not touch.** Files this WU may edit / create:
- `.specfuse/scripts/loop.py` (argparse + override resolver + two
  guard sites)
- `tests/test_force_full_close.py` (new)

No edits to: `gate_eval.py` (the `auto_close_disabled` check
already lives there from T01; do not duplicate), T04's wiring
internals (only add the override guard around the call site),
T05's wiring internals (same), `lint_plan.py`, other features,
skills, secrets, `.git/`. Driver owns all git; edit files only.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in
`.specfuse/verification.yml`. Plus AC6's symbol-existence
checks. Plus AC5's five unit tests.

**Escalation triggers.**

1. **Completeness.** AC6 (a) ≠ `1`, OR (b)/(c) does not match,
   OR (d)/(e) fails, OR (f) returns no lines → emit
   `status: blocked`. Wiring incomplete.
2. **Argparse refactor.** If `loop.py` has moved argparse into
   a different file or module (separate CLI entrypoint), follow
   it there. The CLI flag must land somewhere the loop's
   dispatch sees it; if no such single seam exists, emit
   `status: blocked` — operator decides scope.
3. **`args` not in scope at wiring sites.** T04 + T05's wiring
   may not have direct access to the argparse `args` namespace
   if the loop's call hierarchy has many layers. If threading
   `args` through requires changes broader than the two guard
   sites, emit `status: blocked` and propose a hygiene WU
   (`T06H`) to plumb args (or a global) first. Do NOT widen this
   WU's scope unilaterally.
4. **PLAN.md frontmatter shape ambiguity.** `auto_close_disabled`
   is a boolean. If the PLAN.md parser used by the driver
   (`read_frontmatter` + `_miniyaml`) returns `"true"` (string)
   instead of `True` (bool), the AC2 check `auto_close_disabled
   is True` will silently miss. Normalize the comparison
   (`fm.get("auto_close_disabled") in (True, "true", "True")`)
   or, preferably, fix it in `_miniyaml` if other call sites are
   already coercing booleans there — but that's a `_miniyaml`
   edit, out of T06's scope: emit a hygiene WU instead.
