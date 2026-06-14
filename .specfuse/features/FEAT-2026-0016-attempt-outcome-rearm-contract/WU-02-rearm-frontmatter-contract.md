---
id: FEAT-2026-0016/T02
type: implementation
effort: high
status: pending
attempts: 0
planned_cost_usd: 1.80
generated_surfaces: []
produces_driver_helper:
  - fold_cumulative_on_rearm
  - detect_rearm_dispatch
---

# Re-arm WU frontmatter contract + driver cumulative-fold logic

**Objective.** Land the WU frontmatter additions (`re_arm_count`,
`re_arm_history`, `cumulative_cost_usd`, `cumulative_duration_seconds`,
`cumulative_input_tokens`, `cumulative_output_tokens`) and the
driver's cumulative-fold logic that fires on `/unblock-wu` re-arm
detection. This is the original FEAT-2026-0016 substance — folded
into this feature because attempt-level events and re-arm
cumulative fields are at different granularities of the same audit
signal (PLAN.md § Folded scope).

**Context.** This is `FEAT-2026-0016/T02`. Re-arm contract — every
`/unblock-wu` re-arm should preserve the prior cycle's spend so
`/gate-status` (T05) and close-ceremony cost-analysis (T07) see
the true total across re-arms. Today's manual ad-hoc pattern
(FEAT-2026-0013 burned $13.50 across 5 dispatches; operator
manually wrote `historical_*` fields) is unaudited and unautomated.

Reference binding rules:
`.specfuse/rules/result-contract.md`, `.specfuse/rules/never-touch.md`.

**§10 helper-duplication pre-flight.** Before authoring:

```bash
# Existing cumulative or re-arm symbols (must not collide)
grep -nE 'cumulative_|re_arm_|historical_' .specfuse/scripts/loop.py .specfuse/scripts/lint_plan.py

# Existing /unblock-wu logic (skill-side)
ls .specfuse/skills/unblock-wu/

# Existing cost / token field writes (driver-side)
grep -nE 'write_cost_to_wu|cost_usd|input_tokens|output_tokens' .specfuse/scripts/loop.py
```

If any `cumulative_*` or `re_arm_*` field is already partially
present in `loop.py` from a prior partial fix, the spec for this WU
needs to either name + reconcile the existing field or refuse to
collide. The pre-flight catches this.

**Acceptance criteria.**

1. **WU frontmatter fields documented.** Update
   `.specfuse/templates/WU.template.md` frontmatter notes section
   with the six new fields (per PLAN.md § "Re-arm contract"):
   `re_arm_count`, `re_arm_history`, `cumulative_cost_usd`,
   `cumulative_duration_seconds`, `cumulative_input_tokens`,
   `cumulative_output_tokens`. Each field: purpose (1–2 lines),
   who writes it (driver vs `/unblock-wu` vs author), default
   value, when it's read.

2. **`lint_plan.py` accepts the new fields.** Verify the existing
   WU frontmatter schema check accepts the six new fields without
   warning. If lint currently has an "unknown field" warning,
   either widen the allowlist or confirm there's no such check.

3. **Driver helper — cumulative fold on re-arm dispatch.** Add
   `fold_cumulative_on_rearm(wu: WorkUnit) -> None` to `loop.py`.
   Called on dispatch when `detect_rearm_dispatch(wu)` returns
   True. Algorithm:
   - Read the WU's existing `cost_usd`, `duration_seconds`,
     `input_tokens`, `output_tokens` (set by the prior cycle's
     terminal outcome).
   - Add each to the corresponding `cumulative_*` field
     (initializing the cumulative field to 0 if absent).
   - Reset the per-cycle fields (`cost_usd: 0`, etc.) so the new
     cycle's spend tracks cleanly.
   - Write all six updated frontmatter values atomically via the
     existing `write_frontmatter_field` helper.

4. **Driver helper — re-arm detection.** Add
   `detect_rearm_dispatch(wu: WorkUnit) -> bool`. Returns True
   when the WU is being dispatched AND `re_arm_count > 0` AND the
   per-cycle `cost_usd > 0` (signals a prior cycle's data is
   present unfolded). False otherwise. Called at the top of the
   per-WU dispatch path; fires `fold_cumulative_on_rearm` exactly
   once per re-arm cycle.

5. **Driver emits `re_arm_dispatched` event** on first dispatch
   after a re-arm. Event shape:

   ```json
   {
     "event_type": "re_arm_dispatched",
     "correlation_id": "<wu_id>",
     "payload": {
       "re_arm_count": <int>,
       "reason": "<from re_arm_history[-1].reason>"
     }
   }
   ```

   Emitted via existing `build_event` + `flush_events` helpers
   immediately after `fold_cumulative_on_rearm` completes.

6. **`task_started` event gains `re_arm_count` field.** The
   existing `task_started` event's payload adds `re_arm_count:
   <int>` so dashboards can group attempts across re-arms without
   re-reading frontmatter. Backward-compatible additive change.

7. **No edits to `/unblock-wu` skill content.** T06 (gate 2) owns
   the skill-side changes (mandatory rationale prompt, writing
   the history entry). T02 ships the driver-side contract only.
   If the WU author finds skill-side coordination unavoidable
   (e.g. a contract handshake between `/unblock-wu` writes and
   the driver's detection), emit `status: blocked` with the
   coordination issue.

8. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. Two new helpers present
   test "$(grep -cE '^def (fold_cumulative_on_rearm|detect_rearm_dispatch)\b' .specfuse/scripts/loop.py)" = "2"

   # b. Helpers importable
   (cd .specfuse/scripts && python3 -c "from loop import fold_cumulative_on_rearm, detect_rearm_dispatch")

   # c. Cumulative fields documented in WU template
   for f in re_arm_count re_arm_history cumulative_cost_usd cumulative_duration_seconds cumulative_input_tokens cumulative_output_tokens; do
     grep -qE "^- \`$f\`" .specfuse/templates/WU.template.md || { echo "missing template doc: $f"; exit 1; }
   done

   # d. re_arm_dispatched event type referenced in driver
   grep -qE 'build_event\("re_arm_dispatched"' .specfuse/scripts/loop.py

   # e. task_started payload includes re_arm_count
   grep -qE 'task_started.*re_arm_count|re_arm_count.*task_started' .specfuse/scripts/loop.py || \
     grep -B 5 'build_event\("task_started"' .specfuse/scripts/loop.py | grep -q re_arm_count

   # f. Working-tree diff touches both files
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/loop.py'
   git diff --name-only HEAD | grep -qx '.specfuse/templates/WU.template.md'
   ```

   Any check failing → `status: blocked`. Do NOT flip frontmatter
   as substitute.

**Do not touch.** Files this WU may edit:
- `.specfuse/scripts/loop.py` (additions; do NOT modify T01's
  surfaces — T01 lands the attempt_outcome emission helpers)
- `.specfuse/templates/WU.template.md` (frontmatter notes section
  only)

No edits to: `lint_plan.py` UNLESS lint currently rejects the new
frontmatter fields (in which case widen the allowlist with a
narrow change),  `.specfuse/skills/unblock-wu/` (T06 owns),
`gate_eval.py`, T03's tests (T03 owns), other features, secrets,
`.git/`.

**Verification.** The `code` gate set + AC8 existence checks.

**Escalation triggers.**

1. **Completeness.** AC8 (a) returns anything other than `2` →
   `status: blocked`. Helpers missing.
2. **Collision with prior partial implementation.** If the §10
   pre-flight surfaces existing `cumulative_*` or `re_arm_*`
   symbols, emit `status: blocked` with the collision details
   before mutating anything. Operator decides on reconciliation.
3. **Lint-allowlist widening surface area.** If the WU
   frontmatter schema check rejects the new fields and the fix
   requires a non-trivial widening of `lint_plan.py`, surface in
   RESULT and consider whether the lint widening should be its
   own WU. Trivial allowlist additions are in-scope here.
4. **Backward compatibility on existing features.** Existing
   in-flight WUs in other features don't have the new fields.
   The driver's cumulative-fold logic MUST default each field
   to 0 when absent (via `getattr` or dict `.get(default)`); no
   `KeyError` on first dispatch against an unaware WU.
