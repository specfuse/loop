---
id: FEAT-2026-0075/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
oracle_env: macos_local
produces_driver_helper:
  - specfuse.loop.loop.format_driver_staleness_summary
produces:
  - tests/test_driver_staleness_gate_summary.py
generated_surfaces: []
model: sonnet
effort: medium
gate_set: code
driver_version: 0.9.3
started_at: 2026-08-07T04:21:20.975561+00:00
duration_seconds: 1071.227
cost_usd: 2.779493
input_tokens: 2352
output_tokens: 24799
---

# Summarize driver staleness at gate completion and record it as an event

**Objective.** At gate completion, name which work units edited the driver and which
units were dispatched after them, and emit a machine-readable event so a close reads
the fact instead of reconstructing it.

**Why the record matters as much as the summary.** All three real occurrences were
diagnosed the same way: a human compared `ps -eo pid,lstart,command` output against a
work unit's `started_at` and worked out that the process predated the code. That is
`[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]` rule (b), and it is a
reconstruction a close should never have to perform. After this unit the fact is in
`events.jsonl` and in the gate's own output, so a close reads it.

**Context.** This is `FEAT-2026-0075/T03`, gate 1. `T01` built the detection
predicate; `T02` wired the immediate warning at the squash site. This unit is the
gate-end half — the two are not substitutes and neither replaces the other. Read
`PLAN.md` and `GATE-01.md` in this folder.

**Where it goes.** The gate-completion block already exists and prints a summary
before flipping the gate to `awaiting_review` (`specfuse/loop/loop.py`, near the
`gate {gate.number} awaiting_review` bookkeeping commit). Add the staleness summary
there. The unit ordering the summary reports is the order the driver already
dispatched in this run — do not re-derive it from the PLAN graph, which describes
intent rather than what happened.

**Event registration is part of this unit, not an afterthought.** This repository
validates every `events.jsonl` entry against a registry: `event-type-gate` in
`.specfuse/verification.yml` runs `validate_event.py` over every feature's event log,
and `load_driver_event_types` reads the driver-local registry at
`specfuse/loop/data/schemas/driver-event.schema.json`. An event type absent from that
registry fails the gate for **every** feature in the tree, not only this one. Note
that this schema is package-local — it is not in `scripts/sync-scaffold.sh`'s manifest
and has no `.specfuse/` counterpart, so it is edited directly and needs no sync.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_driver_staleness_gate_summary.py::test_summary_names_units_dispatched_after`
   exists and **fails on HEAD before this WU's edits**. Record the failing output in
   the RESULT block before editing production code.
2. `specfuse/loop/loop.py` exports
   `format_driver_staleness_summary(edits, dispatched_after) -> str`, returning
   exactly `""` when `edits` is empty and a non-empty summary otherwise.
3. For a gate in which unit A edited the driver and units B and C were dispatched
   after it, the summary names A, the driver paths A touched, and both B and C as
   having executed pre-edit modules — each asserted separately.
4. A unit dispatched **before** the driver-editing unit is not named as affected —
   the ordering claim is the substance of the summary and an off-by-one here would
   make it wrong in the direction that reads as alarming rather than silent.
5. The summary is emitted at gate completion, before the gate flips to
   `awaiting_review`, and appears in the driver's output for a gate containing a
   driver-editing unit — asserted by driving the real gate-completion path, not by
   calling the formatter alone.
6. A gate containing no driver-editing unit produces **no** summary and **no** event,
   asserted through the same harness.
7. A `driver_staleness_detected` event is appended to the feature's `events.jsonl`,
   carrying at minimum the editing unit's ID, the driver paths it touched, and the IDs
   of the units dispatched after it.
8. `driver_staleness_detected` is added to the `event_types` list in
   `specfuse/loop/data/schemas/driver-event.schema.json`, and
   `python3 -c "from specfuse.loop.validate_event import load_driver_event_types; assert 'driver_staleness_detected' in load_driver_event_types()"`
   exits 0.
9. The `event-type-gate` gate passes over every feature's `events.jsonl`:
   `python3 .specfuse/scripts/validate_event.py --all` (or the exact command
   `.specfuse/verification.yml` declares for that gate) exits 0. Paste the command and
   its output — a new event type that fails validation breaks the gate for every
   feature in the tree, not just this one.
10. `python3 -c "from specfuse.loop.loop import format_driver_staleness_summary"`
    exits 0.
11. The test named in criterion 1 **passes** after this WU's edits.
12. The full `code` gate set passes, including `coverage report --fail-under=90`.

**Do not touch.** `specfuse/loop/driver_edit.py` — T01's; import it, do not extend it.
The squash-site warning T02 added — this unit adds the gate-end half and must not
move, reword, or suppress the immediate one; they are deliberately two sites.
`specfuse/loop/arm_eval.py` (gate 2's surface). `.specfuse/verification.yml` — this
unit adds an event type to the existing registry, it does not add or edit a gate.
`.specfuse/schemas/` (the vendored orchestrator schemas; the driver-local registry
this unit edits is the package-local one named in Context). `.specfuse/rules/` and
`.specfuse/templates/`. Any other feature's folder under `.specfuse/features/` —
including their `events.jsonl`. Generated directories, secrets, `.git/`. The driver
owns all git operations — you edit files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (`--fail-under=90`), `leak-scan`, and `event-type-gate` — the
last is load-bearing for this unit rather than incidental, per criterion 9. In
addition run criteria 8 and 10's symbol checks verbatim and paste both outputs. Do
**not** report the running driver's in-situ behaviour as evidence; this session's
process predates your edits by construction.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
dispatch order needed for criterion 3 is not available at the gate-completion site
without re-deriving it from the PLAN graph — intent is not history, and substituting
one for the other silently would make the summary wrong in exactly the runs that
matter; adding `driver_staleness_detected` to the registry makes `event-type-gate`
fail for any existing feature (criterion 9), which means the envelope contract needs a
change this unit is not scoped to make; `format_driver_staleness_summary` is absent
from the file you edited or criterion 10's import fails — do not claim complete; or
criterion 5's gate-completion path cannot be driven in a test, leaving the wiring
unverifiable.
