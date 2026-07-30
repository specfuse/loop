---
id: FEAT-2026-0055/T05
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
produces_driver_helper: "_wu_sections.slice_wu_section — bold-preamble label-line content included; lint_plan._extract_do_not_touch_patterns — prohibition-scoped, ambiguous matches degrade to WARN"
produces:
  - specfuse/loop/_wu_sections.py
  - specfuse/loop/lint_plan.py
  - tests/test_lint_boundary_extraction.py
---

# Fix the boundary rule's extraction: see the bold form, ERROR only on certainty

**Objective.** `check_produces_boundary` fires on the canonical `**Do not touch.**`
bold-preamble form (327/327 real WU bodies) and stops false-ERRORing legitimate features:
ERROR only on an unambiguous deadlock, WARN on anything extraction cannot be sure about.

**Context.** Gate 1 of FEAT-2026-0055, depends on T04. Chartered by G1-CLOSE's `not_met`
(RETROSPECTIVE.md §2a, §3 — read both before coding; the 15 false ERRORs and the controlled
variants there are this WU's fixture set). Root cause confirmed there: `slice_wu_section`
(`specfuse/loop/_wu_sections.py:35-44`) takes content from the line after the heading, so the
bold form's label-line content is discarded; `slice_acceptance_criteria` in the same file
already handles both forms — mirror it. Binding rules: `.specfuse/rules/result-contract.md`,
`never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

- `tests/test_lint_boundary_extraction.py::TestBoldPreamble::test_canonical_bold_form_deadlock_errors`
  **fails on HEAD** before this WU runs — the retro's `fx-deadlock` fixture (bold form,
  `produces` inside `src/main/**`) currently exits 0.
- `slice_wu_section` returns label-line content for the bold-preamble form and behaves
  unchanged for ATX headings; `slice_acceptance_criteria`'s existing tests stay green (shared
  helper — do not fork a second slicer).
- Extraction is **prohibition-scoped**: backtick patterns are taken only from clauses without
  allow-signals. Minimum honored signals, each with a fixture drawn from the retro's real
  cases: an explicit carve-out (`except`), an allow-enumeration (`These files change:` /
  "adds" / "new" preceding the token — the FEAT-2026-0023/T01 shape), and a semantic
  qualifier (`existing` — the FEAT-2026-0070/T08 shape). A match the scoping cannot classify
  degrades to **WARN**, never ERROR — the WU's design rule: ERROR only on certainty.
- The 2a fixture ERRORs with the existing (correct) message; the retro's four false-positive
  features each lint with **zero ERRORs** as fixtures (copied section text, not live paths).
- **Satisfiability sweep re-run and recorded** (command + output in this WU's result):
  `specfuse-lint` over every feature folder — zero ERROR findings tree-wide.
  `FEAT-2026-0020-public-readiness-prep` stays excluded via its pre-existing crash (issue
  filed; not this WU's surface — do not fix the MiniYAML parser here).
- T01's and T02's existing tests pass unchanged, except tests asserting the old (broken)
  extraction, which are updated deliberately and enumerated in the result.
- Full suite green.

**Do not touch.** `specfuse/loop/loop.py` and `specfuse/loop/_miniyaml.py`; `.specfuse/templates/**`,
`plugins/**`; other features' folders; `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus the recorded tree-wide
sweep.

**Escalation triggers.** If prohibition-scoping cannot separate the retro's four
false-positive shapes from the true deadlock without semantic judgment beyond the listed
signals, stop and emit `status: blocked` with the unresolvable fixture — proposing WARN-only
for the whole rule is then the operator's call, not this WU's.
