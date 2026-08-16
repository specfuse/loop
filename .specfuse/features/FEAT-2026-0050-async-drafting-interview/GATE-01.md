---
gate: 1
status: awaiting_review
cost_budget_usd: 27.00
baseline:
  sha: 12b97b9bcea75bcf56a65f50ab5d13947e8aa04e
  probed_at: 2026-08-16T12:17:03.442563+00:00
  failing: []
---

# Gate 1 — the async interview round-trip

The agent can study a `drafting-needed` queue entry, post the `/draft-feature`
interview as a question issue, read the operator's reply, and decide — by D1 —
whether the answers support drafting or the run falls back to a plain
escalation. **No feature folder is written in this gate.**

## Definition of done

- Every implementation work unit in this gate is `done`.
- A question set built from a real roadmap entry classifies each question
  `elicitation` or `decision`, with options and a recommendation on decisions
  and neither on elicitation.
- The interview posts as a `drafting-needed` `needs-human` issue rendered
  through `escalation.render_escalation_body`, one marker per question.
- An operator reply is parsed back to per-question answers, and D1 decides
  draft-or-fallback: any unanswered elicitation falls back; an unanswered
  decision records the agent's recommendation as an explicit assumption.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are staged to `LEARNINGS-pending.md` — this feature is
  `autonomy_default: auto`, where `close-i` forbids writing
  `.specfuse/LEARNINGS.md` directly.
- The next gate's work units are drafted, and `GATE-02-REVIEW.md` is written.

## Out of scope for this gate

- Writing a feature folder from the answers — that is gate 2.
- Any change to `/draft-feature`'s own write path.
- Adding or renaming a member of `escalation.CATEGORY_LABELS`.

## Arming discipline

Before arming gate 2, check — and record the result in `GATE-02-REVIEW.md`:

- **Runtime probe.** Gate 1's retrospective records the *observed* shape of a
  real operator reply. Gate 2's parsing units must be drafted against that
  record, not an assumed shape; if no real reply was ever received, say so and
  treat gate 2's parser criteria as unvalidated rather than planned.
- **Flag scope.** This feature introduces no flag. If gate 2's wiring adds one,
  the introducing WU carries the flag-scope table.
- **Predicate check.** `driver_edit.is_driver_module_path` against every path a
  gate 2 unit declares in `produces:` — a unit editing the driver's importable
  surface halts the run for a restart mid-gate (FEAT-2026-0075), which is worth
  knowing at arming rather than at dispatch.

## Auto-close note

**PASSED — auto-closed** (`evaluate_auto_close`, predicate=v1). The close ceremony **did not run**.

- gate_total_cost: $4.30 of $27.00
- reasons: [] (auto=True)

The per-criterion deferred-verification list was **not** enumerated. Before treating this gate as fully verified, read `RETROSPECTIVE.md` § "What the loop did NOT verify" and the `specfuse:autoclose-debt` marker it carries.
