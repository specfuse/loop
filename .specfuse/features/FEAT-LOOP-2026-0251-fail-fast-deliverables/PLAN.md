---
feature_id: FEAT-LOOP-2026-0251
title: Refuse a missing deliverable before the verification gates run
slug: fail-fast-deliverables
branch: feat/FEAT-LOOP-2026-0251-fail-fast-deliverables
roadmap_goal: An attempt whose declared deliverable is missing or untouched is refused before any verification gate runs, its retry note names the files it did change, and `specfuse lint` warns before arming when a `produces:` path appears nowhere in its unit's text.
autonomy_default: auto
status: active
planned_cost_usd: 11.00
---

# Plan: Refuse a missing deliverable before the verification gates run

Three driver refusals judge only the attempt's diff against the unit's `produces:` list:
`produces_not_in_diff`, `deliverable_missing` and `no_deliverable_files` (`loop.py`, the
deliverable-presence and produces-in-diff guards after `execute_unit_attempt()` returns).
Today they run only after `verify()` has passed, so each refusal pays for a full verification
run first. An operator report measured 19 of 48 non-passing attempts (of 184) ending in one of
these three, and 6 of 26 escalations were `deterministic_refusal_repeat`.

This feature moves those three decisions ahead of `verify()`, adds the attempt's own changed
paths to their retry note, and adds an arm-time warning for a `produces:` path its unit never
mentions. It does not change what is refused, only when.

## Decisions (2026-11-25)

The operator said "take your recommendations" and then accepted this list. Each item is a
recommendation applied on that instruction.

1. **All three asks of the report, item 3 narrowed.** The retry note already names the missing
   path and shows the `produces_unchanged:` / `produces_amended:` fence
   (`PRODUCES_REPAIR_EXAMPLE`, #1415). The missing piece is the list of paths the attempt did
   change; only that is added.
2. **Autonomy `auto`.** A fresh judge session writes the terminal verdict from evidence only.
   `loop.py` and `lint_plan.py` are judge surfaces, so the terminal judge-editing stop fires
   before the close: acknowledge it with your own reason and `/unblock-wu`.
3. **One gate**, four substantive units and a terminal `close` (`docs/methodology.md` §6).
4. **Fail-fast covers exactly the three diff-only refusals.** The smoke-import guard, the
   closing-deliverable guards and `files_changed_mismatch` stay where they are.
5. **Same tree handling.** An early refusal keeps or resets the tree by the same
   `defaults.retain_on_guard_refusal` rule the late one uses, so no finished work is
   discarded; its note says verification did not run, never that it passed.
6. **Opt-out for gate-written deliverables.** A deliverable that only a verification gate
   writes (a code generator, say) passes the late check today and would be refused by an early
   one on every attempt. `defaults.fail_fast_deliverables` in `verification.yml`, read the way
   `retain_on_guard_refusal` is, defaults to `true`; `false` restores today's order exactly.
7. **The arm-time lint is a WARN, measured before it ships.** T04 reports how many of this
   repository's `done` units it fires on; above 10% it is narrowed before reporting complete
   (the #771 lesson: a warning that fires on most features trains operators to ignore it).

**Out of scope:** moving the smoke-import or closing-deliverable guards; changing
`detect_deterministic_refusal_repeat`; live progress or halt notification; parallel gates or a
result cache.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -n "produces_not_in_diff\|deliverable_missing\|no_deliverable_files\|deterministic_refusal_repeat" specfuse/loop/loop.py`
  and `grep -n "produces" specfuse/loop/lint_plan.py`
- **Verdict:** reuse and extend. The three guards exist and run after `verify()`; this feature
  reorders them, it does not add a refusal. The retry note exists (`_RETRY_CLASS_HINT`,
  `PRODUCES_REPAIR_EXAMPLE`, `format_deliverable_missing_note`). Arm-time `produces:` lints
  exist for an already-delivered path (`check_produces_satisfiability`), a directory entry
  (`check_produces_shape`) and a Do-not-touch conflict (`check_produces_boundary`); none checks
  that the unit's text mentions the path.
- **If reusing:** the produces-in-diff and presence decisions are lifted into callable helpers
  so the early and late call sites share one implementation; `prep` sets (FEAT-2026-0057/T04)
  are the precedent for a fail-fast step that skips work.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — no check changes severity; the new lint is a WARN.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-LOOP-2026-0251/T01
        file: WU-01-produces-before-verify.md
        depends_on: []
      - id: FEAT-LOOP-2026-0251/T02
        file: WU-02-presence-and-opt-out.md
        depends_on: [FEAT-LOOP-2026-0251/T01]
      - id: FEAT-LOOP-2026-0251/T03
        file: WU-03-retry-note-paths.md
        depends_on: [FEAT-LOOP-2026-0251/T01]
      - id: FEAT-LOOP-2026-0251/T04
        file: WU-04-arm-time-lint-and-docs.md
        depends_on: [FEAT-LOOP-2026-0251/T02, FEAT-LOOP-2026-0251/T03]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-LOOP-2026-0251/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-LOOP-2026-0251/T01, FEAT-LOOP-2026-0251/T02, FEAT-LOOP-2026-0251/T03, FEAT-LOOP-2026-0251/T04]
```

## Post-merge checklist

- On the next real feature run that hits one of the three refusals, confirm its
  `attempt_outcome` carries `verify_seconds: 0` and no `gate_result` events (FEAT-LOOP-2026-0250
  timings), i.e. the refusal really cost no gate run.
- In a project whose gates generate tracked files, confirm `fail_fast_deliverables: false`
  restores the old order.

## Notes

- LEARNINGS `[FEAT-LOOP-2026-0250/T04]`: a unit that edits `docs/*.md` refreshes its packaged
  copy under `specfuse/loop/data/docs/` in the same unit (`scripts/sync-scaffold.sh`).
- LEARNINGS `[FEAT-LOOP-2026-0250/T01]`: a test that validates events through `validate_event`
  pins the packaged schemas and clears the validator caches.
- `produces:` lists only `.py` files under `tests/` (#3539).
- **Review follow-ups (2026-11-26, before the close, operator-approved).** An independent review
  of the gate's diff found three behaviour changes the early order introduced; fixed on this
  branch, test-first, in `tests/test_fail_fast_deliverables.py` (`TestEarlyRefusalRecovery`,
  `TestEarlyRetainedNoteWording`):
  1. An early refusal now consults the re-plan trigger (`replan_before_last_attempt`, extracted
     from the failed-verification path), unless it is a repeat on an unmoved tree, which stays
     #597's halt. Before, a unit that never wrote its deliverable lost the re-plan a failed
     verification used to give it.
  2. The refusal measurement `_refusal_touched` counts uncommitted edits to tracked files
     (`git_diff_names(..., worktree=True)`, excluding the unit file). Before, an attempt that only
     edited tracked files read as an untouched tree and could be halted as
     `deterministic_refusal_repeat` after two early refusals. `detect_deterministic_refusal_repeat`
     itself is unchanged; its #1415 rule (identical summary and identical changed-file set) still
     halts.
  3. An early refusal with a retained tree gets its own retry lead: the edits are kept but NOT
     verified, and the missing deliverable is the work to do — not "apply only the mechanical
     fix".
  Accepted, not fixed: a deliverable that only a verification gate writes (a code generator, a
  formatter) is refused early on every attempt; `fail_fast_deliverables: false` is the remedy,
  and no in-loop test covers a gate-written deliverable.
- **Third-close follow-up (2026-11-26, #3612).** With the tree kept, a later attempt's retry note
  listed the earlier attempt's kept edits as its own, so "this attempt changed no files" never
  showed after the first attempt. The driver now snapshots the content of every already-dirty path
  when each attempt starts (`snapshot_dirty_tree`) and the note lists only paths that were clean
  then or have changed since (`attempt_own_paths`). The guards' own diff and the events'
  `files_touched` are unchanged, so `detect_deterministic_refusal_repeat` is unaffected. Tested in
  `TestTreeAndNote` (kept edits left out, nothing-changed stated, a re-edited kept file listed),
  both with and without `fail_fast_deliverables`.
- **Fourth-close follow-up (2026-11-26, #3613).** A kept file the attempt deleted, or reverted to
  its committed content, had left the diff the guard judged, so the note missed it and could say
  "changed no files". `attempt_own_paths` now also lists every attempt-start snapshot path that
  is no longer in that diff and whose content has changed. Tested in `TestTreeAndNote` (deleted,
  reverted tracked edit, deleted plus a new file), with and without `fail_fast_deliverables`.
- **Fifth-close follow-up (2026-11-26, #3614).** The list still missed renames, mode-only changes
  and non-ASCII names, because each earlier fix filtered the guard's diff. It is now built by
  comparison: every path that differs from the attempt's starting commit at its start or at the
  refusal (`git diff --no-renames -z` plus untracked, read NUL-separated) is compared by state
  (file type, executable bits, content digest) across the attempt. Tested in `TestTreeAndNote`
  for each case, with and without `fail_fast_deliverables`; a non-ASCII kept edit left alone
  still reads "changed no files". The driver crash on `git add -N` for a new non-ASCII file is a
  separate, pre-existing defect (it predates this feature) and is not fixed here.
