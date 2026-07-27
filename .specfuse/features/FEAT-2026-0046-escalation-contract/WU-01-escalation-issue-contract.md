---
id: FEAT-2026-0046/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - specfuse/loop/escalation.py
  - tests/test_escalation_contract.py
produces_driver_helper:
  - render_escalation_body
  - validate_escalation_body
model: sonnet
effort: medium
gate_set: code
driver_version: 0.5.0
started_at: 2026-07-27T21:24:34.141522+00:00
duration_seconds: 356.948
cost_usd: 0.999586
input_tokens: 42
output_tokens: 8346
---

# Define the escalation issue format as a machine-checkable contract

**Objective.** Ship `specfuse/loop/escalation.py` carrying the label vocabulary, a
renderer that produces a conforming escalation issue body, and a validator that names
what a non-conforming body is missing.

**Context.** Correlation ID `FEAT-2026-0046/T01`. This is the shared vocabulary the
rest of the gate consumes: T02 emits bodies this module renders, T03 displays issues
this module's labels identify.

The body format is not invented here. `.specfuse/rules/operator-escalation.md` is
already binding on every human escalation and defines the six parts, in order: what
has been done so far; what the issue is about; what decision is needed and why; why it
did not close automatically; options with pros and cons; and a recommendation. This
work unit makes that existing rule machine-checkable for the issue surface — read the
rule before writing the renderer, and take the six part names from it rather than
paraphrasing.

Two additions the rule does not cover, both from the roadmap's goal for this feature:

- **Numbered answers.** The body ends with a section offering the reader numbered
  choices and the literal instruction to reply `1`, `2`, or prose. This is what makes
  a reply unambiguous for FEAT-2026-0049 to parse later.
- **A correlation marker.** An HTML comment carrying the escalating unit's
  correlation ID, so T02 can find an existing issue instead of filing a duplicate.
  Use the shape `<!-- specfuse:escalation id=<correlation-id> -->`. This mirrors the
  existing `<!-- specfuse:autoclose-debt gate=N ... -->` marker in `loop.py`, which is
  the repo's established way to make a machine-findable claim inside prose.

Label vocabulary, from the roadmap's detail section for this feature: one
`needs-human` label carried by every escalation, plus exactly one category from
`gate-review`, `blocked-wu`, `triage-question`, `drafting-needed`, `merge-approval`.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`. Use the
`verification` skill to run the gates.

**Acceptance criteria.**

1. `tests/test_escalation_contract.py::TestEscalationBodyValidator::test_rejects_body_missing_a_required_part`
   exists and **fails on HEAD before this WU runs** (the test file does not yet exist,
   which counts as red).
2. `specfuse/loop/escalation.py` defines `NEEDS_HUMAN_LABEL = "needs-human"`.
3. The same module defines `CATEGORY_LABELS` as a `frozenset` whose members are
   exactly `gate-review`, `blocked-wu`, `triage-question`, `drafting-needed`,
   `merge-approval`.
4. The same module defines `render_escalation_body(...)` returning a `str` that
   contains all six part headings from `.specfuse/rules/operator-escalation.md`.
5. A body rendered by `render_escalation_body` contains a numbered-answers section
   whose text includes the literal substring `reply` and at least two numbered
   options.
6. A body rendered by `render_escalation_body` for correlation ID `X` contains the
   literal substring `<!-- specfuse:escalation id=X -->`.
7. The same module defines `validate_escalation_body(text)` returning a `list` of
   finding strings.
8. `validate_escalation_body` returns `[]` for a body produced by
   `render_escalation_body` — the renderer and validator are held to each other.
9. `validate_escalation_body` returns a non-empty list when any one of the six parts
   is removed from an otherwise-conforming body, and each returned finding names the
   missing part.
10. `validate_escalation_body` returns a non-empty list when the correlation marker is
    absent.
11. `python3 -m pytest tests/test_escalation_contract.py -q` exits zero after this
    WU's edits (the same file named in criterion 1).
12. `python3 -c "from specfuse.loop.escalation import NEEDS_HUMAN_LABEL, CATEGORY_LABELS, render_escalation_body, validate_escalation_body"`
    exits zero.

**Do not touch.** `.specfuse/rules/operator-escalation.md` — this WU reads it and
conforms to it; it does not edit it. No other work unit's files. Generated
directories, secrets, `.git/`. The driver owns all git operations. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus the scoped red/green run in
criteria 1 and 11, and the symbol-existence import in criterion 12 — the code gate
passes when no test asserts a symbol exists, so that import is what catches a
renamed or absent export.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
six part names cannot be read unambiguously from
`.specfuse/rules/operator-escalation.md`; a required category label conflicts with an
existing repository label whose meaning differs; or coverage cannot reach the 90%
floor without testing behaviour this WU does not own. If `escalation.py` is absent
from the files you edited, or any of the four symbols in criterion 12 is missing, emit
`status: blocked` — do not claim complete.
