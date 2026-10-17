---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_diagnosis_severity_end_to_end -v -b"
cost_budget_usd: 24.00
---

# Gate 1 — a diagnosed finding carries a severity that orders autofix

## Definition of done

**Stated as an outcome.** Driven through the findings-diagnose and findings-autofix
providers with a stub `gh` and a stub headless session:

1. A headless analysis result carrying `"severity": "high"` posts a diagnosis whose
   marker carries `severity=high`, and the finding issue gets exactly one
   `severity:high` label; a later diagnosis with `"severity": "low"` leaves exactly
   one severity label, `severity:low`.
2. A diagnosis marker without a severity (every diagnosis posted before this
   feature) parses with severity absent, and an unknown severity value reads as
   absent; neither raises, and neither writes a label.
3. With three eligible diagnosed findings of severities `low`, `critical` and none,
   the findings-autofix provider advertises them `critical`, `low`, none — and its
   eligibility decisions are unchanged.
4. A finding issue carrying a `severity:` label and no triage marker is not
   advertised by the bug lane.
5. The headless prompt and `/diagnose-issue` ask for severity against one rubric
   defined once in code.

The `feature_oracle` proves 1–4 end to end. It is red on the current tree (the
module does not exist); `FEAT-2026-0205/T01` is the walking skeleton that creates it
first and turns clauses 1 and 2 green, with clauses 3 and 4 as `unittest.skip`
naming their owners (T03, T04). A skip surviving to the close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Fail closed.** T01's parser pairs "an old marker still parses" with "an unknown
  value reads as absent and never raises", as a lookup, not a caller's try/except.
- **Eligibility untouched.** T03 changes order only; a drafted change to
  `autofix.decide` is out of scope.
- **Lesson `[FEAT-2026-0204/G1-CLOSE]` (live render).** The close runs one opt-in
  live headless diagnosis or records in Deferred verification why not.

## Reflection notes

<Written by the human at review time.>
