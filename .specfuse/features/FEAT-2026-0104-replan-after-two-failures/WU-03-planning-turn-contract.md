---
id: FEAT-2026-0104/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces_driver_helper:
  - synthesize_replan_brief
  - assert_replan_changed_body
produces:
  - tests/test_replan_turn_contract.py
---

# Define what the re-plan turn is told and what it must produce

**Objective.** Replace T01's stubbed planning turn with its real contract: the
brief it receives, the narrowed unit body it must write, and the guard that
refuses a re-plan which changed nothing.

**Context.** FEAT-2026-0104/T03. The turn's whole value is that it sees what
the two attempts actually hit — their failure classes, signatures and notes —
which the failing session never did, because each attempt starts cold. What it
writes back is a **narrower** unit: a tightened objective, criteria scoped to
what one attempt can carry, and explicit non-goals drawn from what the attempts
already proved hard. It does not author new units or touch `depends_on`
(PLAN.md scope boundary). `synthesize_retry_directive` (`loop.py:1530`) is the
neighbouring surface that writes a retry's lead; read it before inventing a
second vocabulary for the same idea.

**Acceptance criteria.**

- `python3 -m unittest tests.test_replan_turn_contract -v -b` fails on HEAD
  before this unit's edits and passes after.
- The test asserts the brief handed to the turn contains both prior attempts'
  failure class and signature, and the retained notes — not a summary of them.
- A turn that returns a body **byte-identical** to the one it was given is
  refused, and the unit escalates rather than dispatching an attempt that
  cannot differ from the one before it. A re-plan that re-plans nothing is the
  spinning this feature exists to stop, one level up.
- The narrowed body still parses as a valid work unit: the five mandatory
  bold sections survive the rewrite, asserted by running the existing WU lint
  over the rewritten file.

**Do not touch.** `gate_eval.py`. `driver-event.schema.json` (T04's).
`detect_deterministic_refusal_repeat` (T02 owns the interaction). The sibling
WU files in this gate. Never rewrite a unit's `id` or `depends_on` — the
graph is PLAN.md's and mid-gate mutation of it is out of scope.

**Verification.** Narrow tier for `implementation`, plus
`python3 -m unittest tests.test_replan_turn_contract tests.test_replan_end_to_end -v -b`.

**Escalation triggers.** Stop with `status: blocked` if narrowing a unit
cannot be expressed without editing its acceptance criteria in a way the WU
linter rejects — the contract then needs a decision about which sections a
re-plan may rewrite, and that belongs to a human.
