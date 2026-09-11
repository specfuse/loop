---
id: FEAT-2026-0104/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces_driver_helper:
  - should_replan_instead_of_retry
produces:
  - tests/test_replan_trigger.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.19.0
started_at: 2026-09-10T19:31:44.231232+00:00
duration_seconds: 492.689
cost_usd: 1.673818
input_tokens: 104
output_tokens: 30928
---

# Decide when a re-plan fires instead of a retry

**Objective.** Replace T01's stubbed trigger with the real predicate: a unit
re-plans when its next attempt would be its last permitted one, unless it
declared `iterate_on_failure`.

**Context.** FEAT-2026-0104/T02. The ceiling is not a constant — 
`resolve_max_attempts` (`loop.py:267`) resolves it unit, then project, then
`MAX_ATTEMPTS = 3`, on the premise that a unit's author knows that unit's
oracle. A hard count of two would re-plan a unit that deliberately declared a
higher ceiling, which is the case that dial exists for (#2650). Ceiling-relative
firing yields "after two failures" at the default that every unit in the corpus
actually runs at, while respecting any unit that said otherwise. Units
declaring `iterate_on_failure` are exempt outright: they fail on purpose
against a convergent validator.

**Flag-scope table** (`.specfuse/rules/planning-discipline.md` §3). The
behavior flag is T01's `replan_stub_trigger` opt-in, replaced here by
`should_replan_instead_of_retry` — a predicate every unit is now subject to,
not an opt-in. Headline claim: *"a unit re-plans on its next-to-last
permitted attempt, unless it declared `iterate_on_failure`; every other retry
path is unaffected."*

| Code path | Gated by the new decision? | Why |
|---|---|---|
| The attempt loop's real-failure branch (`outcome == "failed"`, `loop.py` dispatch loop) | **yes** | The one path `should_replan_instead_of_retry` is consulted from — it decides whether this attempt's retry becomes a re-plan instead. |
| Guard-refusal branches (`deliverable_missing`, `no_deliverable_files`, `produces_not_in_diff`, `files_changed_mismatch`, `closing_deliverable_missing`, `smoke_import_failed`, `squash_commit_failed`) | no | These sit in the `outcome == "passed"` branch and `continue` immediately; the new predicate is never reached from them. |
| `detect_deterministic_refusal_repeat` (top-of-loop, before dispatch) | no | Unchanged. It can still escalate a unit whose next iteration would otherwise have hit the re-plan trigger — checked first, so it owns that outcome (see the dedicated AC below). |
| `detect_spinning_signature_repeat` (real-failure branch, before the re-plan check) | no | Unchanged. It `break`s before the re-plan check when a `(failure_class, failure_signature)` repeats, so its own escalation always wins. |
| `resolve_max_attempts` / the per-unit `max_attempts` ceiling | no | Read by the new predicate, not altered by it. |
| `iterate_on_failure` convergence branch | no — exempted, not gated | The predicate returns `False` unconditionally for these units; their own convergence-plateau escalation is untouched. |
| The attempt counter / `for attempt in range(1, wu_max_attempts + 1)` | no | A re-plan does not rewind or extend it — same loop, same budget, only the body dispatched on the last attempt changes. |

**Acceptance criteria.**

- `python3 -m unittest tests.test_replan_trigger -v -b` fails on HEAD before
  this unit's edits and passes after, covering as separate cases: default
  ceiling 3 fires after the 2nd failure; `max_attempts: 10` fires after the
  9th and not the 2nd; `max_attempts: 1` never fires; `iterate_on_failure:
  true` never fires at any ceiling.
- **The unit loop terminates whether or not a re-plan fires.** A unit that
  fails every attempt and re-plans reaches a terminal state in a bounded
  number of dispatches, asserted by a test that fails loudly above a dispatch
  ceiling rather than hanging. A previous attempt rewound the attempt counter
  to 0 on re-plan, so the trigger re-fired at the same point on every fresh
  budget and the unit never terminated — it hung the whole suite. A re-plan
  spends the remaining attempt slot; it does not buy a new budget. If this
  unit changes the loop's form, the guards asserting on that form are updated
  rather than left broken — `tests/test_produces_shape.py` locates the loop by
  source string, and a rewrite that breaks the lookup silently retires it.
- A unit whose attempt tripped `detect_deterministic_refusal_repeat` escalates
  there and does **not** re-plan, asserted directly: both paths key off a
  repeated failure and only one can own the outcome.
- This unit carries a flag-scope table naming every path that reaches a retry
  today and whether the new decision gates it (`planning-discipline.md` §3).

**Do not touch.** `MAX_ATTEMPTS`' value at `loop.py:137` — the default of 3 is
out of scope by PLAN.md. `resolve_max_attempts`' resolution order.
`gate_eval.py`. The sibling WU files in this gate.

**Verification.** The narrow tier is NOT sufficient for this unit: it edits
the central dispatch loop, which 44 test modules drive through `loop.run()`,
so run the **full** suite — `python3 -m unittest discover -s tests -b`, OK on
3901 tests in ~151s on a clean tree — before reporting complete. Narrow tier for `implementation`, plus
`python3 -m unittest tests.test_replan_trigger tests.test_replan_end_to_end -v -b`
— T01's oracle must still pass with the real predicate behind it.

**Escalation triggers.** Stop with `status: blocked` if the refusal-repeat
interaction cannot be resolved without changing
`detect_deterministic_refusal_repeat`'s own behaviour: which check owns a
repeated guard refusal is a design question this unit is not authorized to
settle alone.
