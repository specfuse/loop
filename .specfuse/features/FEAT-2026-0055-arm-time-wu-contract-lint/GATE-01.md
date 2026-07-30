---
gate: 1
status: awaiting_review
cost_budget_usd: 27.00
baseline:
  sha: 6ef2eb4427226c13616630d5b991bbd102b16dfa
  probed_at: 2026-07-30T15:01:00.326964+00:00
  failing: []
---

# Gate 1 — WU-contract defects die at arm time, not after burned attempts

## Definition of done

- `specfuse-lint` (and the driver's plan-load lint) WARNs on a dispatchable WU whose
  `produces:` path an earlier `done` WU already declared, naming both WUs and the authoring
  response; ERRORs on a `produces:` path the WU's own Do-not-touch section forbids, naming
  `assert_produces_in_diff` as the guard it preempts.
- The ERROR rule reports zero findings across every existing feature folder in this repo;
  expected WARNs are enumerated, including this feature's own T01/T02 overlap.
- `assert_declared_deliverables` and `assert_produces_in_diff` accept one declaration form:
  literal paths and fnmatch globs both satisfy both gates (a glob requires ≥1 existing match),
  with the behavior table in the WU and existing guard tests updated deliberately.
- `WU.template.md` carries no literal-vs-glob folklore comment; `arm-gate` and
  `authoring-work-units` skills name the lint as the arm-time step.
- Full suite green; `RETROSPECTIVE.md` exists; lessons promoted or `nothing generalizes`;
  terminal verdict via G1-CLOSE.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **§4 runtime probe**: T03 changes an existing guard's accepted inputs (widens
  `assert_declared_deliverables` to globs). Probe before arming T03: run the full suite with
  the change applied locally; the failure list (existing guard tests asserting literal-only)
  is T03's enumerated test surface.
- **§3 flag-scope table**: no behavior flag. n/a.
- **§2 satisfiability**: bound and answered in PLAN — the ERROR rule must report zero on the
  existing tree; T02 verifies and records the run.

## Reflection notes

<Written by the human at review time.>
