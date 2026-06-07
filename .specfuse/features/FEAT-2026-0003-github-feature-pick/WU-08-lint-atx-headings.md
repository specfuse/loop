---
id: FEAT-2026-0003/T08
type: implementation
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.463667
input_tokens: 18
output_tokens: 7826
---

# lint_plan.py accepts ATX (`## Section`) headings, not only bold

**Objective.** Broaden `lint_plan.py`'s mandatory-section detector so it
recognizes Markdown ATX headings (`## Context`) in addition to the existing
bold-preamble (`**Context.**`) and plain forms, then prove the previously
adopted orchestrator-issue folder lints clean.

**Context.** This is `FEAT-2026-0003/T08`, the sole substantive WU of gate 4 —
the terminal-case escalation gate `G3-PLAN` appended to fix the finding the live
smoke surfaced (`SMOKE-example-feature.md`, `GATE-04-REVIEW.md`). The gap:
orchestrator-dispatched `specfuse:feature` issue bodies use ATX section headings
(`## Context`, `## Acceptance criteria`, …) — confirmed in the orchestrator's
`shared/templates/work-unit-issue.md` and in live issue #287 — but
`lint_plan.py`'s section check matches only `^\**<section>` (bold or plain), so an
adopted feature folder fails lint and cannot be ground end-to-end. This is the
last mechanism blocking the feature's `roadmap_goal`.

The current check is in `lint_plan.py`'s `lint()` (the loop over
`REQUIRED_SECTIONS`): `re.search(rf"(?mi)^\**{re.escape(sec)}", wbody)`. The fix
is to broaden the leading-marker alternation to also admit one-or-more `#`
followed by optional whitespace — a union pattern `^(?:#+\s*|\**)<section>` — so
ATX, bold, and plain all match. Do not narrow the existing acceptance (the loop's
own WUs use the bold form and must keep linting clean).

Reference the binding rules under `.specfuse/rules/`; honor `result-contract.md`,
`never-touch.md`. This WU edits gate-1 code deliberately (the linter is the
target), so `lint_plan.py` is NOT off-limits here — but nothing else under
`.specfuse/scripts/` is.

**Acceptance criteria.**
1. `lint_plan.py`'s mandatory-section detector matches a section written as an ATX
   heading (`## Context`, `### Acceptance criteria`, etc.) — i.e. the leading
   marker alternation accepts `#+\s*` in addition to the existing `\**`.
2. The existing bold-preamble form (`**Context.**`) and plain form still match
   (regression — the loop's own feature folders, including the worked-example
   fixture `FEAT-2026-0001-health-endpoint` and this feature's own WUs, must keep
   linting clean).
3. `python3 .specfuse/scripts/lint_plan.py
   .specfuse/features/example-feature-conform-exampleEndpoint-to-validated-spec`
   exits 0 (the folder the gate-3 smoke adopted, which previously failed lint on
   all five sections, now passes).
4. New test cases in `tests/test_lint_correlation_id.py` (or a new
   `tests/test_lint_sections.py`) assert: an ATX-headed WU body passes the section
   check, a bold-headed body still passes, and a body genuinely missing a section
   still fails (the rejection direction is preserved).

**Do not touch.** `loop.py`, `gh_features.py`, `adopt_feature.py`,
`gh_backend.py`, `_miniyaml.py`, any binding rule under `.specfuse/rules/`, any
skill, the adopted `example-feature-…` folder's contents (lint it, do not edit
it — editing it to pass would defeat the test), generated dirs, secrets, `.git/`.
The driver owns all git — edit files only. This WU touches exactly two files:
`.specfuse/scripts/lint_plan.py` and the test file.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests,
ruff, bandit, coverage ≥ floor). Run them in order. AC 3's command (lint of the
adopted folder exiting 0) is the headline check — run it explicitly and confirm.

**Escalation triggers.** If broadening the section regex would also weaken a
different, unrelated check in `lint_plan.py` (e.g. the correlation-ID pattern or
the closing-sequence order check), stop and emit `status: blocked` — the section
detector is the only thing that should change. If the adopted folder fails lint
for a reason OTHER than the section-heading format (a malformed graph, a missing
file), block and name it — that is a separate finding, not this WU's scope.
</content>
