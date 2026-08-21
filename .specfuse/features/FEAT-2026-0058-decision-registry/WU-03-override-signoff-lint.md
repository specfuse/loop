---
id: FEAT-2026-0058/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_decision_override_lint.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.13.0
started_at: 2026-08-21T12:53:37.894210+00:00
duration_seconds: 639.597
cost_usd: 1.252386
input_tokens: 4080
output_tokens: 12929
---

# Lint override sign-off provenance

**Objective.** A decision that has been overridden cannot pass lint without
naming who signed it off and when. An unsigned override blocks arming.

**Context.** FEAT-2026-0058/T03, gate 1, depends on T01. This is the third of
FEAT-2026-0066's drift shapes — *"an ADR silently overriding a ratified operator
decision, surfaced two gates later as a close blocker"* — and the one the
registry alone does not fix: recording an override is worthless if it can be
recorded silently.

`PLAN.md` D3 and `[FEAT-2026-0070/G1-CLOSE-INTERMEDIATE]`: an override that
mutates the field recording the pre-override state leaves the record
byte-identical to one that was never overridden, with the distinction surviving
only in prose that nothing parses. So the provenance fields are not optional
decoration — they are what makes "overridden then signed off" a queryable state.

**Acceptance criteria.**

1. `tests/test_decision_override_lint.py::TestOverrideSignoff::test_unsigned_override_is_an_error`
   fails on HEAD before this unit runs and passes after: a decision at
   `overridden-pending-signoff` missing any of `overridden_from`,
   `signed_off_by`, `signed_off_at` produces an ERROR and a non-zero exit.
2. A decision at `ratified` that carries `overridden_from` **must** also carry
   `signed_off_by` and `signed_off_at` — the transition this feature exists to
   make un-silenceable. A test asserts an override cannot reach `ratified`
   unsigned.
3. `signed_off_by` is required to be non-empty and not a placeholder. The
   operator's own justification is theirs to write; this unit checks that
   *someone is named*, never what they wrote — per
   `.specfuse/rules/operator-escalation.md`'s rule against authoring the human's
   justification for them.
4. A decision that was never overridden needs no provenance fields, and their
   absence is not an error. Asserted, so the check cannot become a tax on the
   common case.
5. The error message names the decision ID and the missing field, so an operator
   fixing it does not have to re-derive which of four fields is absent.
6. `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry`
   exits 0.

**Do not touch.** `.specfuse/templates/DECISIONS.template.md` and the parser
(T01). The citation and non-restatement checks (T02). `closing_requirements.py`
(D4).

**Verification.** `./scripts/smoke-test.sh` — run unsandboxed.

**Escalation triggers.** Report `status: blocked` if the override fields cannot
be validated without deciding *who counts as an operator* — that is an
authorization question this feature has no basis to answer, and inventing an
allowlist would be scope this unit must not take on its own.

**Note.** Edits `specfuse/loop/lint_plan.py`, on the driver's importable
surface — see T02's note on the expected restart halt.
