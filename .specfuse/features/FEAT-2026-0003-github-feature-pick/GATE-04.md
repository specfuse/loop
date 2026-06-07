---
gate: 4
status: passed
---

# Gate 4 — Adopted-folder lint admits orchestrator issue bodies

## Definition of done

- `lint_plan.py`'s mandatory-section detector accepts both bold-preamble
  (`**Context.**`) and Markdown ATX (`## Context`) headings, so an orchestrator
  issue body embedded verbatim by `adopt_feature.py` lints clean — without
  weakening the rejection of a body that genuinely lacks a section.
- `lint_plan.py` over the existing adopted folder
  `.specfuse/features/INIT-2026-0001-F06-conform-publishroster-to-validated-spec/`
  (written by gate 3's T07 smoke) exits 0 — the gate-3 finding is resolved.
- A retrospective exists; generalizable lessons are promoted; docs/roadmap
  reflect that all four pipeline mechanisms (discover / adopt / report-back /
  lint-clean grind) now work; the feature-arc retrospective's `roadmap_goal`
  verdict is updated to "met after gate 4."

This gate is the terminal-case escalation (branch B) `G3-PLAN` appended to fix
the one finding the live smoke surfaced. It is intentionally narrow: one linter
change + tests + re-lint of the existing adopted folder (T08), then the closing
sequence. The re-lint is folded into T08 (AC 3), not a separate WU — it is a
single command, not a session's worth of work. No second live `#287` mutation
is required; the `state:*` label contract was settled at gate 3.

The ATX-headings assumption is confirmed: `RestoManagerApp/orchestrator`'s
`shared/templates/work-unit-issue.md` emits all five sections as `## ATX`
headings, and live issue #287 matches. The union pattern (`^(#+\s*|\**)<section>`)
accepts both ATX and bold, so it is correct regardless.

## Reflection notes

<Written by the human at gate 4 review time.>
</content>
