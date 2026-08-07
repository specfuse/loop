---
id: FEAT-2026-0075/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.00
oracle_env: macos_local
provenance: "PLAN.md § Notes — 'The sanctioned hold is gate 2's, and it is a hard dependency of the refusal': `draft` is rejected by the arm check for the entire gate (`loop.py:5760-5770`, `return 2`) and `blocked_human` reads as a failure in `/attention`. `[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]` rule (c) — 'prefer a precondition the process can enforce on itself to one a human must satisfy between two dispatches' — is what sets the shape: the hold is a halt the process performs on itself, not a status a human must set and later clear. `G1-PLAN` re-scoped it from 'a new WU status' to 'a named halt' after finding that a halt leaves every WU in `pending` and the gate in `open`, so no consumer needs teaching a new vocabulary."
produces_driver_helper:
  - specfuse.loop.loop.format_driver_restart_halt
produces:
  - specfuse/loop/loop.py
  - tests/test_driver_restart_hold.py
generated_surfaces: []
model: sonnet
effort: high
gate_set: code
---

# Give the two-invocation split a sanctioned halt the driver performs on itself

**Objective.** Build the mechanism that ends a driver invocation mid-gate, cleanly and
by design — a named halt reason, a distinguished exit code, a resume instruction, and
an event — leaving every remaining work unit `pending` and the gate `open`, so a fresh
process picks the gate up exactly where it stopped. This unit builds the halt. `T06`
decides when to fire it.

**Context.** This is `FEAT-2026-0075/T05`, gate 2's second unit. Gate 1 shipped
detection and a warning at the squash site (`loop.py:6284-6296`) and a gate-completion
summary — all of which print and none of which stop anything, which is why gate 1's own
close was dispatched by a process that predated the entire gate (`RETROSPECTIVE.md` §1).
`T04` narrowed the predicate to the importable surface. This unit builds the halt that
`T06` will fire; it introduces no firing decision of its own. Read `PLAN.md` § Notes,
`GATE-02.md`, `GATE-02-REVIEW.md` § *What was rejected*, and `RETROSPECTIVE.md` before
editing.

**Why this is not a new work-unit status, which is what the gate-2 sketch assumed.**
`PLAN.md` framed the problem as "the two-invocation split has no usable status": `draft`
is refused for the whole gate at `loop.py:5760-5770`, and `blocked_human` reads as a
failure everywhere. Both are true, and both dissolve if nothing is marked at all. A
halt that flips **no** WU status and leaves the gate `open` needs no new vocabulary in
`lint_plan.py`'s `VALID_STATUS`, no new entry in `MODEL_BY_TYPE` / `EFFORT_BY_TYPE` /
`GATES_FOR_TYPE` / `CLOSING_ASSERTIONS_BY_TYPE` / `POST_PASS_INVARIANTS_BY_TYPE`, and
no re-teaching of `/attention`, `gate-status` or any other consumer — they see an active
feature with an open gate and pending units, which is precisely what it is. The
sanctioned name lives on the *halt*, not on a work unit.

**Existing-mechanism search (`planning-discipline.md` §1).** Commands run by `G1-PLAN`:

```
grep -n "^MODEL_BY_TYPE\|^EFFORT_BY_TYPE\|^GATES_FOR_TYPE\|^DISPATCHABLE\|^VALID_TYPES" specfuse/loop/loop.py
grep -n "VALID_STATUS" specfuse/loop/lint_plan.py
grep -n "_should_halt_for_budget\|while True\|for wu in pending" specfuse/loop/loop.py
```

**Verdict: found the halt-between-WUs mechanism, mirroring its shape — building no
second halt path.** `_should_halt_for_budget` (called at `loop.py:5856`, at the top of
the `for wu in pending` body opened at `loop.py:5846`) is the established seam for stopping a run *between* work
units so an in-progress unit always reaches a terminal outcome and the squash contract
stays intact. This unit adds a sibling brake at the same seam. It differs in exactly
one respect and the difference is the point: the budget brake flips the gate to
`awaiting_review` because the run is over; the restart brake leaves the gate `open`
because the run is *suspended*.

`grep -n "VALID_STATUS" specfuse/loop/lint_plan.py` confirms the status set is
`{draft, pending, ready, in_progress, in_review, done, blocked_human, abandoned}` — no
hold status exists, and this unit deliberately does not add one.

**The event needs no schema change**, and this was checked rather than assumed:
`specfuse/loop/data/schemas/driver-event.schema.json` is an `event_types` **enum
widener** and a `correlation_id` pattern widener; it does not constrain payload keys.
`driver_staleness_detected` is already in that enum (gate 1's `T03`). Reuse it with
additional payload keys rather than minting a second event type — a new type is a
consumer-visible contract change for every downstream project, and this one buys
nothing a payload key does not.

**The halt must be the last thing the process does.** Flush the events, commit the
bookkeeping, print, return. Do not attempt to re-exec — `[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]`
rule (a) names re-exec as an alternative, and `GATE-02-REVIEW.md` § *What was rejected*
records why it is out of scope: the run holds a `flock`, an open event buffer and
per-attempt reset state, and `os.execv` inherits file descriptors, so a re-exec that
gets any of that wrong loses the gate rather than restarting it. Halt-and-resume reduces
the operator's action to re-running the command they already ran, which is the loop's
existing idiom at every gate boundary.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_driver_restart_hold.py::test_halt_leaves_gate_open_and_units_pending`
   exists and **fails on HEAD before this WU's edits**. Paste the failing output in the
   RESULT block before editing production code.
2. `specfuse/loop/loop.py` defines a module-level constant
   `HALT_REASON_DRIVER_RESTART = "driver_restart_required"` and a module-level
   `EXIT_DRIVER_RESTART_REQUIRED` integer that is not `0`, `1`, or `2` — `2` is already
   taken by the unarmed-drafts check at `loop.py:5770` and a shared code makes the two
   halts indistinguishable to any script reading the exit status.
3. `specfuse/loop/loop.py` exports
   `format_driver_restart_halt(wu_id, driver_paths, remaining_wu_ids, resume_command) -> str`,
   returning exactly `""` when `driver_paths` is empty and a non-empty message
   otherwise — the same empty-input contract as `format_driver_staleness_warning`
   (`loop.py:2166`), so the two formatters behave alike at their edges.
4. The rendered message names, each asserted separately against the string: the work
   unit that edited the driver, every path in `driver_paths`, every ID in
   `remaining_wu_ids`, the fact that this process cannot execute the edited modules,
   and the literal `resume_command` the operator should run. A halt message that does
   not carry the resume command sends the reader to the source, which is the failure
   `T02`'s objective already names.
5. **The halt is a brake at the `for wu in pending` seam**, alongside
   `_should_halt_for_budget` and before the next unit's `set_wu(in_progress)` — not
   mid-attempt and not inside `squash_commit`. `grep -n "HALT_REASON_DRIVER_RESTART" specfuse/loop/loop.py`
   shows no occurrence inside `squash_commit`'s body or inside an attempt loop. Paste
   the grep.
6. On halt, asserted separately: the gate file's `status` is still `open`; **no** WU's
   `status` was changed by the halt; and the function returns
   `EXIT_DRIVER_RESTART_REQUIRED`.
7. A `driver_staleness_detected` event is appended to the feature's `events.jsonl`
   carrying `halted: true`, the remaining work-unit IDs, and the resume command. Assert
   against the written file, not against the in-memory payload.
8. The bookkeeping commit for the halt is made through the existing
   `commit_bookkeeping` path, so the event is durable if the operator does not re-run
   immediately. Assert the events file survives the halt.
9. `python3 -c "from specfuse.loop.loop import format_driver_restart_halt, HALT_REASON_DRIVER_RESTART, EXIT_DRIVER_RESTART_REQUIRED"`
   exits 0.
10. `python3 .specfuse/scripts/event_type_gate.py` exits 0 — confirming the reused
    event type validates with the added payload keys and that no schema edit was
    needed. Paste the output.
11. No new entry is added to `VALID_STATUS`, `VALID_TYPES`, `MODEL_BY_TYPE`,
    `EFFORT_BY_TYPE`, `GATES_FOR_TYPE`, `CLOSING_ASSERTIONS_BY_TYPE`, or
    `POST_PASS_INVARIANTS_BY_TYPE`. State this as a checked fact with the diff, not as
    an intention.
12. The full `code` gate set passes, including `coverage report --fail-under=90`.

**Do not touch.** `specfuse/loop/driver_edit.py` — `T04`'s; import it, do not extend
it. `specfuse/loop/arm_eval.py`. The squash site's existing `T02` warning and the
gate-completion `T03` summary — this unit adds the halt mechanism, `T06` wires it, and
a firing decision made here would be the drift the two units exist to keep apart.
`specfuse/loop/data/schemas/driver-event.schema.json` — criterion 10 asserts no schema
change is needed. `plugins/specfuse/skills/` and `.specfuse/skills/` — consumer
rendering is a deferred follow-up recorded in `GATE-02-REVIEW.md`, not this unit's
scope. `.specfuse/verification.yml`. `.specfuse/rules/` and `.specfuse/templates/`.
`GATE-01.md` and gate 1's work units. Any other feature's folder under
`.specfuse/features/`. Generated directories, secrets, `.git/`. The driver owns all git
operations — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition
run criterion 5's grep and criterion 9's symbol-existence check verbatim, pasting both
outputs. Do **not** report the running driver's in-situ behaviour as evidence — this
session's process predates your edits by construction, which is the hazard this feature
exists to fix.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the halt
cannot be placed at the `for wu in pending` seam without changing an attempt loop's
control flow, which would put a squash at risk and needs an operator decision; leaving
the gate `open` while returning a non-zero exit code makes the next invocation re-run a
unit that already completed, which would mean resume-from-halt is not free and the
whole shape needs rethinking; criterion 10 shows the added payload keys fail event
validation, which would make this a schema change and therefore a consumer-visible
contract change outside this unit's scope; or `commit_bookkeeping` cannot be called at
the halt site without flipping a gate or WU status.
