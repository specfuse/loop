---
id: FEAT-2026-0018/T07
type: implementation
effort: medium
status: draft
attempts: 0
planned_cost_usd: 1.00
generated_surfaces: []
produces_driver_helper:
  - lint_plan_next_draft
---

# Plan-next-draft lint extension + driver hook

**Objective.** Add a focused plan-next-draft lint pass that runs after a
`plan-next` WU squashes and BEFORE the dispatch loop iterates to the next
WU, catching malformed next-gate drafts at the cheapest point (the operator
is already reviewing) rather than at gate-(N+1) dispatch time. Warn-only
v1 — surface findings without blocking the loop.

**Context.** This is `FEAT-2026-0018/T07`. Gate 1 (T01–T03) shipped the
predicate module; gate 2 (T04–T06) wired it into the driver. Gate 3 is the
plumbing pass: lint hook (T07), `/wrap-feature` trim (T08), migrate skill
(T09), docs (T10). T07 is first because the lint hook reuses helpers the
driver already loads.

Read first:
- `.specfuse/scripts/lint_plan.py` — existing five-section check at
  `lint_plan.py:313–318` runs over `status in {draft, pending, ready}`. T07
  adds an entry point that focuses ONLY on next-gate-draft WUs the
  immediately-prior `plan-next` produced, with extra checks the general
  pass does not run.
- `.specfuse/scripts/loop.py:2110–2198` — the PASS branch where squash +
  smoke-import + closing-deliverable-guard fire. T07's driver hook fires
  AFTER `assert_closing_deliverables` and BEFORE `wu_events.append(
  task_completed)` when `wu.type == "plan-next"`.
- `PLAN.md` § "Predicate v1" + `GATE-03.md` "Definition of done" — `lint
  plan-next-draft pass v1` (warn-only; block-on-error deferred).
- `.specfuse/rules/never-touch.md`, `.specfuse/rules/result-contract.md`.

**§10 helper-duplication pre-flight.** Enumerate existing lint helpers
before authoring:

```bash
grep -nE '^def (lint_plan|check_planned_cost|detect_oracle_verbs|detect_driver_wiring|_slice_ac_section)\b' .specfuse/scripts/lint_plan.py
grep -nE '\b(REQUIRED_SECTIONS|SECTION_CHECK_STATUSES|CORRELATION_ID_RE)\b' .specfuse/scripts/lint_plan.py
grep -nE '\bassert_closing_deliverables\b' .specfuse/scripts/loop.py
```

Every hit MUST be either (a) reused unchanged, or (b) named in this WU's
Do-not-touch with the reason. T07 reuses `REQUIRED_SECTIONS`,
`SECTION_CHECK_STATUSES`, `CORRELATION_ID_RE`, `_slice_ac_section`, and
`detect_driver_wiring` without modification. Do NOT re-implement.

**Acceptance criteria.**

1. **New lint entry point — plan-next-draft pass.** Add
   `lint_plan_next_draft(feature_dir: Path, just_closed_gate: int) →
   list[str]` to `lint_plan.py`. Walks PLAN.md's gate-(just_closed_gate+1)
   `work_units` graph and applies, for each WU file whose
   `status == "draft"`:
   - Existing five-section check (reuse `REQUIRED_SECTIONS`).
   - Correlation-ID match against `CORRELATION_ID_RE` (frontmatter +
     graph).
   - `planned_cost_usd` present and parses as a positive float.
   - `type` ∈ `VALID_TYPES`.
   - Five mandatory sections each non-empty (i.e. not just the heading
     followed by another `**Heading.**`).
   - When `type == "implementation"` and the body matches
     `detect_driver_wiring`: a non-empty `produces_driver_helper`
     frontmatter field (this surfaces the same WARN the general pass
     emits, but tied to the draft cohort the operator is about to arm).

   Returns a list of WARN strings (empty list = clean). T07 v1 is
   warn-only: callers must not raise on a non-empty return.

2. **Driver hook in `loop.py`.** In the PASS branch
   (`loop.py:2110–2198`), after `assert_closing_deliverables` passes and
   BEFORE the `wu_events.append("task_completed", ...)` line, add:

   ```python
   # FEAT-2026-0018/T07 — plan-next-draft lint hook (warn-only v1)
   if wu.type == "plan-next":
       try:
           from lint_plan import lint_plan_next_draft
           _warns = lint_plan_next_draft(feature_dir, gate.number)
       except Exception as _exc:
           _warns = [f"lint_plan_next_draft raised: {_exc}"]
       for _w in _warns:
           print(f"   WARN (plan-next-draft lint): {_w}")
       if _warns:
           wu_events.append(build_event(
               "plan_next_draft_lint", wu.wu_id,
               {"gate": gate.number, "warns": list(_warns),
                "blocking": False},
           ))
   ```

   Warn-only contract: the hook MUST NOT change `outcome`, MUST NOT
   reset the tree, and MUST NOT prevent `wu_events.append(task_completed)`
   from running. Block-on-error is deferred (see PLAN.md `GATE-03.md`).

3. **Lint CLI exposes the new pass.** Extend `lint_plan.py`'s
   `__main__` to accept an optional `--just-closed-gate N` flag that
   runs `lint_plan_next_draft(feature_dir, N)` IN ADDITION to the
   existing full-feature lint. Exit code stays 0 on warn-only output;
   exit 1 only if the underlying full-feature lint detects an ERROR
   (existing semantics unchanged).

4. **No regression on full-feature lint.** Existing
   `python3 .specfuse/scripts/lint_plan.py <feature_dir>` invocation
   (no `--just-closed-gate`) produces identical output to today,
   modulo any new lint WARNs that the general pass would have already
   surfaced. Confirm: lint clean run on this feature folder before T07
   landing produces identical output after.

5. **Unit tests.** Add `tests/test_lint_plan_next_draft.py` covering:
   - Clean draft cohort → empty list.
   - Missing `planned_cost_usd` on a draft WU → one WARN naming the WU.
   - Implementation WU with `loop.py` body but empty
     `produces_driver_helper` → one WARN.
   - Empty section (heading present, body empty) → one WARN.
   - Non-implementation type (e.g. `docs`) without driver-wiring → no
     warning regardless of `produces_driver_helper`.
   - Terminal gate (no gate N+1) → returns empty list cleanly (no
     crash on missing gate).

6. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. New lint entry point exists
   grep -qE '^def lint_plan_next_draft\b' .specfuse/scripts/lint_plan.py

   # b. Driver hook in PASS branch (loop.py)
   grep -qE 'lint_plan_next_draft' .specfuse/scripts/loop.py

   # c. CLI flag --just-closed-gate added
   grep -qE 'just-closed-gate|just_closed_gate' .specfuse/scripts/lint_plan.py

   # d. Test file lands
   test -f tests/test_lint_plan_next_draft.py
   python3 -m unittest tests.test_lint_plan_next_draft -v

   # e. Existing lint clean on this feature folder
   python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0018-auto-close-predicate/

   # f. Working-tree diff actually edits the named files (hollow-pass guard)
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/lint_plan.py'
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/loop.py'
   git diff --name-only HEAD | grep -qx 'tests/test_lint_plan_next_draft.py'
   ```

   If any check fails, emit `status: blocked` naming the failing check
   + observed output. Do NOT flip this WU's `status` field as a
   substitute for shipping the code.

**Do not touch.** Files this WU may edit / create:
- `.specfuse/scripts/lint_plan.py` (new entry point + CLI flag only)
- `.specfuse/scripts/loop.py` (one hook insertion in PASS branch only;
  do NOT modify intermediate auto-close branch, terminal-flip block,
  or close-WU verdict path)
- `tests/test_lint_plan_next_draft.py` (new)

No edits to: `gate_eval.py` and its tests (T01–T03 own), the auto-close
helpers `maybe_auto_close_terminal` / `maybe_auto_close_intermediate` /
`resolve_auto_close_override` (T04–T06 own), other features, secrets,
`.git/`. Driver owns all git; edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(tests, coverage ≥ 90%, lint, security, zero compiler warnings). Plus
AC6's symbol-existence + hollow-pass checks. Plus the new unit-test file.

**Escalation triggers.**

1. **Completeness.** AC6 commands (a)–(f) any failing → emit
   `status: blocked`. The hook is incomplete; do NOT flip frontmatter
   as substitute.
2. **PASS-branch site drift.** Hook site was at `loop.py:2110–2198`
   at draft time (between `assert_closing_deliverables` and
   `wu_events.append(task_completed)`). If the block has been
   refactored (closing-deliverable-guard moved, plan-next branch
   inverted), update insertion location but keep the sequencing
   invariant: hook MUST fire AFTER squash succeeds AND AFTER closing
   guards pass, BEFORE `task_completed` event. If the refactor inverted
   the sequence, emit `status: blocked` — operator decides.
3. **Block-vs-warn scope creep.** T07 is explicitly warn-only.
   If the hook surfaces a failure mode you think SHOULD block, name
   it in the RESULT block summary but do NOT add a raising path —
   block-on-error is a deliberate v2 decision (see PLAN.md).
4. **Lint surface expansion.** If a check you want to add requires
   parsing PLAN.md's frontmatter shape, reuse existing
   `_miniyaml.parse` + `read_frontmatter`; do NOT introduce a YAML
   library dependency.
