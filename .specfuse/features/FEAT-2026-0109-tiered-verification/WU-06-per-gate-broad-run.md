---
id: FEAT-2026-0109/T06
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
oracle_env: macos_local
produces_driver_helper: ensure_gate_broad_run
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/data/schemas/driver-event.schema.json
  - tests/test_gate_broad_run.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.16.0
started_at: 2026-09-08T17:08:04.353054+00:00
duration_seconds: 1250.977
cost_usd: 2.258197
input_tokens: 104
output_tokens: 44693
---

# The broad set runs once per gate, before the close, and red halts the gate

**Objective.** Make the full `code` set run exactly once per gate — before the
gate's closing sequence dispatches — and make a red broad run stop the gate
reaching its close. This is the half that makes T04's narrowing safe rather
than merely cheap.

**Context.** FEAT-2026-0109/T06; read `PLAN.md`, `GATE-02.md`, and T04, which
this depends on. T04 lets a gate be declared per-gate-only and stops running it
per attempt. Without this unit those gates would not run at all, and gate 2
would ship a driver that verifies less and claims the same — the exact hollow
pass `GATE-02.md`'s oracle contract exists to prevent.

**Incremental edit to `specfuse/loop/loop.py`.** T01 delivered this file in
gate 1 and T04 added the tier resolution. This unit adds one guard on the
dispatch path — "has the broad set run at this tree yet?" — plus the record it
reads and writes. T04's tier resolution and T05's selector are untouched.

**Where the run belongs.** The closing sequence is ordinary graph units: a
`close-intermediate` (or terminal `close`) followed by `plan-next`, both
`gate_set: plannext`. So the hook is the point where the driver is about to
dispatch the first closing-type unit of a gate — every substantive unit has
landed and the tree is what the gate will be judged on. Running it earlier
measures a tree that is not the gate's result; running it after the close means
the close wrote a verdict against unverified work.

**Tree-keyed, so a restart does not re-pay 169.4s.** Every unit in gate 1
tripped `driver_staleness_detected` and forced a restart; a broad run that
re-executed on each resume would hand back most of what this feature saves.
Record the result on the gate file — a `broad_run:` block alongside the
existing `baseline:` one — carrying at least the tree hash, a timestamp and the
outcome, and skip when the recorded tree equals the current `HEAD^{tree}`.
Reuse T02's `_current_tree_hash` and `write_frontmatter_block`; do not invent a
second tree primitive, and do not reflow the rest of the gate's frontmatter
(`GATE-01.md`'s `feature_oracle` and `baseline:` block must survive the write
byte-identical — T03's `test_source_does_not_disturb_other_frontmatter` is the
precedent to copy).

**Red halts the gate; it does not blame a unit.** A broad-run failure is not an
attempt failure: every unit already passed its own verification, so counting it
against anybody is wrong. Halt the gate for review with a message naming the
failing gate commands and the tree they were measured on, in the shape
`preexisting_gate_failure` already uses — an operator reading it must be able
to tell "the narrow tier let something through" from "this unit failed".

**The event, and the gate that will check it.** A new driver event type must be
added to `specfuse/loop/data/schemas/driver-event.schema.json` before it is
emitted: the `event-type-gate` in `.specfuse/verification.yml` validates every
feature's `events.jsonl` against that schema, so an unschema'd event type turns
a `code` gate red on the attempt that introduced it. T01's `baseline_attribution`
entry is the shape to follow, including its `$comment` provenance line.

**Acceptance criteria.**

- `tests/test_gate_broad_run.py::test_broad_set_runs_before_the_closing_sequence` fails on HEAD and passes after: driving the real `loop.run()` through a gate with a recording `_run_gate_set`, the per-gate-only gates execute exactly once, and that execution is ordered before the first closing-type unit's dispatch.
- `::test_broad_run_does_not_repeat_at_an_unchanged_tree`: a second entry into the same gate at the same `HEAD^{tree}` — the driver-restart case — executes the broad set zero further times, and the recorded `broad_run:` block is unchanged.
- `::test_a_moved_tree_re_runs_the_broad_set`: a real code change between the two entries does re-run it, so the record is never trusted for a tree it did not measure.
- `::test_a_red_broad_run_halts_the_gate_before_the_close`: with an injected failing per-gate-only gate, the closing-type unit is never dispatched, the gate is left for review, and the halt message names the failing gate command.
- `::test_a_red_broad_run_counts_against_no_unit`: no unit's `attempts` is incremented and no `attempt_outcome` event is emitted for the halt.
- `::test_broad_run_write_leaves_other_frontmatter_byte_identical`: writing the `broad_run:` block leaves the gate file's `feature_oracle` and `baseline:` lines unchanged, character for character.
- `python3 .specfuse/scripts/event_type_gate.py` exits 0 — the new event type is in the schema before it is emitted.
- `python3 -m unittest tests.test_tiered_verification_e2e -q` reports `OK`, including its liveness assertion that the broad set runs before the close.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** T04's tier declaration and its absent-key default; T05's
selector and its map; T07's attribution bound; `probe_baseline`,
`gate_baseline_check` and `attribute_failure_to_baseline` — the broad run is a
separate mechanism from attribution and must not be folded into either; gate
1's units and `RETROSPECTIVE.md`; `GATE-01.md`'s `baseline:` block, which this
unit reads around and never rewrites; what any existing gate in
`.specfuse/verification.yml` asserts; `.specfuse/rules/`, `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if the driver has no single
point at which "about to dispatch this gate's first closing unit" is
determinable without restructuring the dispatch loop — inserting a new phase
into `run()` is a design change an operator should approve, not something to
improvise. Also block if halting on a red broad run cannot be expressed without
reusing a status that already means "a unit failed": mislabelling a gate-level
failure as a unit failure would corrupt the attribution gate 1 just built.
