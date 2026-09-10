---
id: FEAT-2026-0104/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces_driver_helper:
  - synthesize_replan_brief
  - assert_replan_changed_body
produces:
  - tests/test_replan_turn_contract.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.19.0
started_at: 2026-09-10T19:39:57.154556+00:00
duration_seconds: 743.964
cost_usd: 2.713218
input_tokens: 166
output_tokens: 43302
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
- **The re-plan turn is a dispatched session, not a string transform**, and
  the test proves it: the patched dispatcher was called, its transcript is in
  the attempt record, and the rewritten body is that session's output rather
  than a function of the input body alone. A previous attempt at this unit
  satisfied every criterion here by appending the brief to the existing body
  as a Markdown section — nine lines, no dispatch, roughly what
  `synthesize_retry_directive` already did for retries. The feature's premise
  is that a fresh planner sees what two cold attempts could not.
- The brief handed to that session carries both prior attempts' failure class
  and signature and the retained notes — not a summary of them.
- The rewritten unit is **narrower**, not merely longer — fewer or more
  tightly scoped acceptance criteria, plus at least one explicit non-goal
  drawn from what the attempts hit — and still parses as a valid work unit
  with its five mandatory sections intact. Assert on the parsed sections, not
  on length; run the WU lint over the rewritten file.
- A turn returning a body byte-identical to its input is refused and the unit
  escalates, rather than dispatching an attempt that cannot differ from the
  one before it.

**Do not touch.** `gate_eval.py`. `driver-event.schema.json` (T04's).
`detect_deterministic_refusal_repeat` (T02 owns the interaction). The sibling
WU files in this gate. Never rewrite a unit's `id` or `depends_on` — the
graph is PLAN.md's and mid-gate mutation of it is out of scope.

**Verification.** The narrow tier is NOT sufficient for this unit: it edits
the central dispatch loop, which 44 test modules drive through `loop.run()`,
so run the **full** suite — `python3 -m unittest discover -s tests -b`, OK on
3901 tests in ~151s on a clean tree — before reporting complete. Narrow tier for `implementation`, plus
`python3 -m unittest tests.test_replan_turn_contract tests.test_replan_end_to_end -v -b`.

**Escalation triggers.** Stop with `status: blocked` if narrowing a unit
cannot be expressed without editing its acceptance criteria in a way the WU
linter rejects — the contract then needs a decision about which sections a
re-plan may rewrite, and that belongs to a human.
