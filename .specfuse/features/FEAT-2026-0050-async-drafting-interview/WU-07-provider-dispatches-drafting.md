---
id: FEAT-2026-0050/T07
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
oracle_env: macos_local
produces:
  - specfuse/agent/providers/feature.py
  - tests/test_feature_provider_drafting_dispatch.py
model: sonnet
effort: medium
---

# Dispatch the drafting path instead of escalating

**Objective.** Wire `FeatureProvider`'s `needs_drafting` branch to run the
answered-questions drafting path when the answer gate says `draft_ready`, and
to emit today's escalation unchanged when it says `fallback`.

**Context.** FEAT-2026-0050/T07, gate 2, depends on T06. This is the unit
`PLAN.md`'s Notes flagged as the file both gates touch;
`GATE-02-REVIEW.md` § Predicate check records the check that matters —
`driver_edit.is_driver_module_path("specfuse/agent/providers/feature.py")` is
`False`, so this unit does **not** halt the run for a driver restart.

Today `execute()` handles `queue_read.DISPOSITION_NEEDS_DRAFTING` by building an
`EscalationPayload` inline and returning `STATUS_ESCALATED`. The module
docstring states the current contract in as many words: "`needs_drafting`
always escalates, never invokes anything under `/draft-feature`." That sentence
becomes false when this unit lands and must be updated in the same change — a
docstring that describes the previous behaviour is worse than none.

D3, from `PLAN.md`: the fallback is the current behaviour, so there is no
regression path. `drafting_answers.fallback_escalation` already reproduces this
branch's payload field-for-field, and
`tests/test_drafting_answer_gate.py::FallbackMatchesFeatureProviderTests` already
asserts the equality. That assertion must keep passing after this unit — it is
the mechanical form of "worst case is status quo."

**Acceptance criteria.**

1. `tests/test_feature_provider_drafting_dispatch.py` names
   `DraftReadyDispatchesTests::test_draft_ready_invokes_drafting_not_escalation`
   and it **fails on HEAD before this unit runs** — the file does not yet exist,
   and `python3 -m unittest tests.test_feature_provider_drafting_dispatch` exits
   non-zero on an absent module.
2. On `DISPOSITION_NEEDS_DRAFTING` with a `draft_ready` answer-gate result,
   `execute()` invokes the drafting session through the provider's injected
   `runner` and does not return `STATUS_ESCALATED`. Asserted with a recording
   runner, the idiom the provider's existing tests already use. This is the
   criterion above, green.
3. On `DISPOSITION_NEEDS_DRAFTING` with a `fallback` result, the returned
   `EscalationPayload` is equal field-for-field to what HEAD's branch produces —
   asserted directly against `drafting_answers.fallback_escalation`, not by
   eyeballing the strings.
4. The module docstring no longer claims `needs_drafting` always escalates, and
   states the two branches it now has.
5. `python3 -m unittest tests.test_drafting_answer_gate -v` still passes — the
   D3 equality assertion T03 shipped is not broken by this change.

**Do not touch.** `specfuse/loop/*.py` — the driver's importable surface; a unit
editing it halts the run for a restart (FEAT-2026-0075). `specfuse/agent/
drafting_answers.py`, `drafting_questions.py`, and `drafting_invoke.py` — T04
and T06 own those; this unit calls them and adds no logic of its own to them.
`specfuse/agent/queue_read.py` — the dispositions are read, never added to or
renamed; `PLAN.md`'s scope boundary forbids changing
`escalation.CATEGORY_LABELS` and the same reasoning applies here. The other
providers under `specfuse/agent/providers/`. Do not touch `.git/` or any
secrets file. **The driver owns all git — this session edits files only and
never runs `git`.**

**Verification.** `./scripts/smoke-test.sh` — run unsandboxed; a sandboxed run
hits unrelated network restrictions during pip build-dependency resolution.
Scoped red/green run:
`python3 -m unittest tests.test_feature_provider_drafting_dispatch -v`.
Regression check: `python3 -m unittest tests.test_drafting_answer_gate -v`.

**Escalation triggers.** If wiring the drafting path requires a change under
`specfuse/loop/` — a new hook in the driver's own modules, a new escalation
category, a change to `render_escalation_body` — report `status: blocked`
naming the path, because a
unit editing the driver's importable surface restarts the run mid-gate and that
is an arming decision, not this session's. If the `fallback` payload cannot be
made equal to HEAD's without restructuring the branch, report `status: blocked`
with the diverging fields rather than accepting a near-match: D3's "worst case
is status quo" is asserted mechanically or not at all.
