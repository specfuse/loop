---
id: FEAT-2026-0073/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
produces:
  - specfuse/loop/data/schemas/driver-event.schema.json
  - specfuse/loop/validate_event.py
  - .specfuse/rules/correlation-ids.md
  - tests/test_correlation_id_override.py
produces_driver_helper:
  - load_driver_correlation_patterns
oracle_env: macos_local
---

# The correlation-ID override: widen on a deep copy, never edit the vendored file

**Objective.** Make the envelope accept the correlation-ID shapes
`.specfuse/rules/correlation-ids.md` documents — closing-sequence `G<n>-<NAME>` and
hygiene `TNNH[N…]` — through the driver-local registry, and reconcile the rules file
so the two state one contract.

**Context.** Correlation ID `FEAT-2026-0073/T01`. Read `PLAN.md` first — it records why
this is a driver-local override rather than an edit to the vendored schema, and the
measurement that makes the next work unit satisfiable. Do not reopen those decisions.

**Extend the existing mechanism; do not invent a second one.** FEAT-2026-0060 built
exactly this shape one feature ago:

```
specfuse/loop/data/schemas/driver-event.schema.json   the driver-local registry
validate_event.load_driver_event_types()              reads it, degrades to empty set
validate_event.load_validator()                       fall-through on a DEEP COPY
```

`load_validator` already deep-copies the vendored schema before widening its
`event_type` enum, precisely so the file on disk is never touched. Widen
`correlation_id` on that same copy, in that same function, reading from that same
registry file. A second override path would mean two places to look when the next
field needs one.

**Never write to `specfuse/loop/data/schemas/event.schema.json`.** Its `$id` is
`https://specfuse.dev/orchestrator/schemas/event.schema.json` and its `$comment` is the
orchestrator's changelog — a file with live upstream history. An edit here is a fork
that the next vendor sync reverts **silently**, reinstating every failure with no
signal that anything regressed.

**The widening must be strictly additive.** Every correlation ID that validates today
must still validate. This is a superset, not a replacement.

**Both surfaces or neither.** The whole defect is that `correlation-ids.md` and the
schema disagree. A change that widens the pattern without reconciling the rules file
leaves the same class of disagreement in place, just shifted. This WU owns both.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_correlation_id_override.py::TestCorrelationIdOverride::test_closing_sequence_ids_validate`
   exists and **fails on HEAD before this WU runs** (`G1-CLOSE` is rejected by the
   vendored pattern today, which counts as red).
2. That test asserts a representative ID of each documented closing shape validates —
   at minimum `G1-CLOSE`, `G1-PLAN`, `G1-CLOSE-INTERMEDIATE`, `G1-RETRO`, `G1-LESSONS`,
   `G1-DOCS`, and a two-digit gate such as `G10-CLOSE` — and passes after this WU.
3. A test asserts a hygiene ID (`TNNH` form, e.g. `T01H`, `T01H2`) validates.
4. **The widening is additive.** A test asserts every shape that validates on HEAD still
   validates: `FEAT-2026-0001`, `FEAT-2026-0001/T01`, `FEAT-2026-0001/F01`,
   `FEAT-2026-0001/F01/T01`, and the `INIT-` forms.
5. **It is still a constraint.** A test asserts genuinely malformed IDs are still
   rejected — a bare word, a wrong-shaped prefix, an empty suffix after `/`, and a
   closing name that is not in the documented set. A pattern widened into `.*` would
   pass criteria 2–4 and is the failure this criterion exists to catch.
6. `specfuse/loop/data/schemas/event.schema.json` is **byte-identical to HEAD**. Assert
   with `git diff --exit-code specfuse/loop/data/schemas/event.schema.json` and quote
   the (empty) output.
7. The registry read degrades safely: a test asserts a missing or unparseable
   `driver-event.schema.json` leaves the vendored pattern in force rather than raising,
   matching `load_driver_event_types`'s existing contract.
8. `.specfuse/rules/correlation-ids.md` and the registry state the same set of shapes.
   Assert mechanically — enumerate the shapes from the rules file and from the registry
   and compare — not by eye.
9. **Run the validator over the corpus and record the numbers.** Report the error count
   and the breakdown by kind before and after. `PLAN.md` records 285 across 38 folders
   at drafting time; a **different total is expected** and is not a block. A new error
   *class* is a finding worth reporting.
10. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**Do not touch.** `specfuse/loop/data/schemas/event.schema.json` — the hard boundary of
this feature, asserted by criterion 6. `.specfuse/scripts/event_type_gate.py` — T02 owns
widening it. Historical `events.jsonl` files anywhere: the emitted IDs are correct and
nothing rewrites them.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (≥90%), `leak-scan`. Criteria 5 and 6 are load-bearing — a
pattern widened too far passes every positive test while enforcing nothing, and an edit
to the vendored file would look like a fix until the next vendor sync erased it.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
documented shapes cannot be expressed as a pattern without also admitting malformed IDs
(say which shape and why — that is a real contract problem in `correlation-ids.md`, not
a regex-golf problem); the rules file turns out to document a shape the corpus never
emits or vice versa, since criterion 8 would then be reconciling a contract that is
itself wrong; or widening `correlation_id` requires touching `event.schema.json`, which
would mean `load_validator`'s deep-copy path is not the mechanism `PLAN.md` believes it
is. A corpus error count different from 285 is **not** a block.
