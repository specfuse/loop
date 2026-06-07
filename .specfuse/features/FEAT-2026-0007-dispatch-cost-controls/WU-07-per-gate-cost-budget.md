---
id: FEAT-2026-0007/T07
type: implementation
model: claude-opus-4-7
effort: high
status: pending
attempts: 0
---

# Per-gate cost budget with `blocked_human` halt

**Objective.** A gate carries an optional cumulative-cost ceiling in its
`GATE.md` frontmatter (`cost_budget_usd: <float>`). When the running total
of `cost_usd` summed across this gate's *completed* WUs exceeds the
ceiling, the loop halts to `blocked_human` between WUs — mirroring the
`MAX_ATTEMPTS` brake, but per-gate instead of per-WU.

**Context.** This is `FEAT-2026-0007/T07`. Reads:

- The dispatch loop's per-WU outer loop in `.specfuse/scripts/loop.py`
  around `run()` (`loop.py:715` for the attempt loop, the outer for-loop
  over WUs sits above it).
- `MAX_ATTEMPTS = 3` at `loop.py:64` — the existing brake whose shape we
  mirror.
- The `cost_usd` field flow: per-attempt accumulation into `cum_usage`
  (`loop.py:786`), then `write_cost_to_wu` at outcome time. The gate
  budget reads completed WUs' cumulative `cost_usd` from each WU file's
  frontmatter — the same surface `gate-status` and the lint already
  observe.
- `GATE.template.md` — frontmatter currently has `gate:` and `status:`
  only. The budget field is new and optional.

**Decision the review flags:** *halt-after-current-WU* (this WU's design),
not *halt-mid-WU*. Mid-WU halt risks an inconsistent tree (agent ran,
nothing committed); halt-between-WU is atomic with the existing squash
contract. See `GATE-02-REVIEW.md` for the rationale.

Reference the binding rules under `.specfuse/rules/`. The driver owns git;
edit files only.

**Acceptance criteria.**
1. New helper `gate_budget_usd(gate_file: Path) -> float | None` returns
   the `cost_budget_usd` value from a GATE.md's frontmatter, or `None`
   when the field is absent. A present-but-non-numeric value raises
   `ValueError` naming the gate file.
2. New helper `gate_spent_usd(plan: dict, gate: dict, feature_dir: Path)
   -> float` sums `cost_usd` from the frontmatter of every WU file listed
   in this gate's `work_units` whose loaded `status == "done"`. WUs whose
   frontmatter omits `cost_usd` (cost tracking off, or attempt didn't
   record) contribute `0.0`. Closing-sequence WUs are included — their
   cost counts against the gate.
3. The outer WU dispatch loop in `run()` calls these two helpers at the
   **top** of each iteration (before `backend.set_wu(wu, "status",
   IN_PROGRESS)`). When budget is set and `spent >= budget`:
   (a) set the gate's status to `awaiting_review` (the existing
       value used by the closing-sequence halt; do **not** invent a new
       status),
   (b) append a `human_escalation` event with
       `reason: "gate_budget_exceeded"` and payload fields
       `budget_usd`, `spent_usd`, `next_wu_id`,
   (c) `commit_bookkeeping` the event + gate file edit,
   (d) `return` from `run()` (mirrors the existing `blocked` exit path
       around `loop.py:869`).
4. The halt is **between WUs**, not mid-attempt. A WU that is mid-dispatch
   when the previous WU's completion pushed the total over budget runs to
   completion; the halt fires before the *next* WU's `set_wu(IN_PROGRESS)`.
   This is by design — see the rationale in `GATE-02-REVIEW.md` "Flagged
   for attention" #1.
5. `GATE.template.md` is updated: add `cost_budget_usd: <float>` to the
   commented-frontmatter notes (an optional field), with a one-line note
   pointing to the halt semantics.
6. `lint_plan.py` accepts `cost_budget_usd` as an optional GATE.md key
   (float; reject non-numeric with a precise message). No other GATE.md
   field validation changes.
7. New unit tests in `tests/test_loop_gate_budget.py`:
   (a) `gate_budget_usd` returns the parsed float when the field is set.
   (b) `gate_budget_usd` returns `None` when the field is absent.
   (c) `gate_spent_usd` sums `cost_usd` across done WU frontmatters and
       ignores WUs whose status is not `done`.
   (d) Integration: a fixture gate with budget `1.00` and one done WU at
       `cost_usd: 1.50` causes the run loop helper (a test-extracted
       `_should_halt_for_budget(plan, gate, feature_dir) -> bool`) to
       return `True`; below budget returns `False`.
   (e) `lint_plan.py` exits 0 on a GATE.md with `cost_budget_usd: 2.5`
       and exits non-zero on `cost_budget_usd: "two-fifty"`.
8. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`):
   `python3 -c "from loop import gate_budget_usd, gate_spent_usd"` must
   succeed before claiming complete.

**Do not touch.** Exactly 4 files change: `.specfuse/scripts/loop.py`,
`.specfuse/scripts/lint_plan.py`, `.specfuse/templates/GATE.template.md`,
and one new test file `tests/test_loop_gate_budget.py`. No edits to:
existing GATE.md files under `.specfuse/features/` (the budget is opt-in;
back-filling is out of scope), `WU.template.md`, `.specfuse/verification.yml`,
binding rules, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
plus the existence smoke check in AC 8.

**Escalation triggers.**
1. **Completeness.** If `gate_budget_usd` or `gate_spent_usd` is absent
   from `loop.py` after your edits, emit `status: blocked` — do not claim
   complete.
2. **Halt placement.** If structuring the budget check at the **top** of
   the per-WU iteration requires moving WU lookup logic in a way that
   breaks any existing test in `tests/`, stop and emit `status: blocked`
   naming the conflict. Do not silently reorganize `run()`.
3. **Closing-sequence interaction.** The retrospective/lessons/docs/
   plan-next sequence already runs after all substantive WUs. If a budget
   halt fires *during* the closing sequence (substantive WUs done; gate
   over budget; G2-RETRO about to dispatch), the correct behavior is the
   same halt — but a reviewer should not be surprised by a half-closed
   gate. If your implementation cannot fire the halt cleanly during
   closing without leaving the gate in a status inconsistent with
   `awaiting_review`, emit `status: blocked` and flag the question.
4. **Gate status overwrite.** If the gate is already `awaiting_review`
   (closing sequence completed, human reviewing), do **not** overwrite
   the status to `awaiting_review` a second time with the budget event;
   skip the halt and let the human review observe the overshoot via the
   spent vs budget numbers in the next gate review.
