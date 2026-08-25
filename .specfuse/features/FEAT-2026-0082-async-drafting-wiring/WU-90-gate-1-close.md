---
id: FEAT-2026-0082/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
auto_close_disabled: true
model: opus
effort: high
produces:
  - .specfuse/features/FEAT-2026-0082-async-drafting-wiring/RETROSPECTIVE.md
  - .specfuse/LEARNINGS-pending.md
---

# Gate 1 close — the seams closed, proven end to end

**Objective.** Terminal close: re-run the oracles fresh, record retrospective +
lessons + docs + terminal verdict in one session, and answer the one question
FEAT-2026-0050 could not — whether a `drafting-needed` queue entry now reaches a
drafted folder without an interactive session.

**Context.** Terminal close of FEAT-2026-0082. Depends on T01 (the shared
emitter), T02 (the question-issue poster), T03 (the `answer_gate` injection),
T04 (the real round trip). Binding rules in `.specfuse/rules/`
(`result-contract.md`, `close-discipline.md`) apply. The driver owns the terminal
`PLAN.md status -> done` flip — do **not** add a status-flip acceptance criterion.

**Read `GATE-01.md` § *What this gate must not claim* before writing the
verdict.** It is the difference between this close and the one it repairs.

> Run `specfuse lint --closing` and confirm it exits 0 before this WU reports
> `complete` — see `.specfuse/rules/close-discipline.md` §4.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries a `## Gate 1` heading —
  `assert_retrospective_gate_section` requires it and checks **after** dispatch.
- A `## Retrospective` section answering, from evidence: whether the gate's
  outcome-shaped definition of done was actually met, quoting T04's
  `ROUND-TRIP.md` rather than restating it; whether suppressing
  `fallback_escalation` on the success path left any queue state without an inbox
  entry; and whether `emit_escalation` was refactored onto `emit_issue_with_body`
  or left as a second path, and why. Plus `## What I'd change`.
- **The bottleneck question, answered as a measurement, not a claim.**
  FEAT-2026-0050's `WU-92` criterion 3 read: *"a `drafting-needed` queue entry
  reaches a drafted folder without an interactive session."* Answer it with
  T04's recorded legs — issue number, reply, folder path, and the `events.jsonl`
  lines showing a completed drafting dispatch rather than an escalation. If any
  leg is missing, the answer is **no**, and the verdict is hedged.
- **The claim this close is forbidden to make.** 0050's second carried-forward
  follow-up — *"one real operator reply... fed to `parse_reply_answers`"* —
  **stays open**. T04's reply was scripted. Record that in those words and record
  the re-run condition unchanged: one genuine operator reply to a real question
  issue. A close that reports this discharged has manufactured its own evidence.
- A `## Lessons` section with any durable rule worth promoting. **This feature is
  `autonomy_default: auto`, so lessons stage to
  `.specfuse/LEARNINGS-pending.md` — writing `.specfuse/LEARNINGS.md` directly is
  refused by `assert_learnings_staged_under_auto` after dispatch.** The candidate
  worth weighing: a gate whose definition of done names its work units can pass
  with every unit green and nothing reachable — 0050 is the worked example, and
  this feature's outcome-shaped definition of done is the correction.
- A `## Docs` note: whether the async drafting path is now documented anywhere an
  operator would find it, or name the doc touched. An operator who receives a
  question issue needs to know that replying to it is what advances the queue.
- A `## Cost analysis` section reconciling `planned_cost_usd` ($26.00 and the
  per-WU estimates) against actual spend from `events.jsonl`, delta named.
  `assert_cost_analysis_section_when_met` requires this heading on a `met`
  verdict and checks after dispatch.
- A `## What the loop did NOT verify` section enumerating every deferred
  criterion with why and where it actually gets checked; required even when empty
  — write `(nothing — every acceptance criterion was verified in-loop)`. The
  scripted-reply entry belongs here at minimum.
- **Oracles re-run fresh** (close-discipline §1), read directly and never from a
  producing WU's self-report: `python3 -m unittest discover -s tests -q` reports
  `OK`; `python3 -c "from specfuse.loop.escalation import emit_issue_with_body"`
  exits 0; `python3 -c "from specfuse.agent.drafting_questions import
  post_question_issue"` exits 0; `python3 -c "from
  specfuse.agent.drafting_answers import read_reply_answers, default_answer_gate"`
  exits 0; the full `code` gate set passes.
- **The seam check, re-run at close and not inherited.** `grep -rn
  "render_question_issue" specfuse/` returns at least one production caller, and
  `default_providers` constructs `FeatureProvider` **with** an `answer_gate`.
  These two greps are the exact evidence 0050's close used to prove the feature
  was disconnected; run them again and quote them.
- **Consumer-visible contract changes** (§3): enumerate them and block on human
  acknowledgment rather than writing `n/a`. Expect at least a new public function
  in `escalation.py`, a changed `default_providers` construction, and a **behavior
  change operators will notice** — a `needs_drafting` entry now files a question
  issue instead of a bare `drafting-needed` escalation. That last row is the one
  that matters; anyone with tooling reading the old escalation shape is affected.
- **Artifact cleanup:** name every issue, comment, branch and folder T04 left on
  the repository, so they can be cleaned up rather than mistaken for real work.
- On a hedged outcome, record the follow-up per close-discipline §2 with a
  `kind:` per unmet criterion.

**Do not touch.** Source and test files (T01–T04 own those); `ROUND-TRIP.md`
(T04's record — quote it, do not edit it); `.git/`, secrets. This WU writes only
its close record. The driver owns git and the terminal PLAN flip. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext`/close gates plus a fresh re-run of the oracles
and the two seam greps above. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the seam greps come back the
way they did for 0050 — no production caller for `render_question_issue`, or
`default_providers` still constructing `FeatureProvider` without an
`answer_gate`. That would mean four green units delivered a disconnected feature
for the second time, which is precisely what this feature exists to prevent and
must never be closed over. Also block if any of T04's five legs is missing from
`ROUND-TRIP.md`: this gate's definition of done is the outcome, not the units,
and a close cannot substitute the units for it. Blocked is respectable
(`result-contract.md` rule 4).
