---
id: FEAT-2026-0060/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces:
  - tests/test_driver_event_registry_covers_emitters.py
  - .specfuse/verification.yml
oracle_env: macos_local
---

# Catch the eighth type in CI, not in a retrospective

**Objective.** Add the two standing checks that make this gap self-detecting: a
drift guard asserting every event type the driver can emit is registered, and a
`verification.yml` gate running the validator over this repository's own event
logs.

**Context.** Correlation ID `FEAT-2026-0060/T02`. Depends on T01 — and the
dependency is load-bearing, not tidiness. **The gate this WU wires reports 7
errors on the tree until T01's registry lands.** Wiring it first turns the `code`
gate set red for every subsequent work unit in this gate, including its own
close. If T01 is not `done` when you start, emit `status: blocked` rather than
proceeding.

Why this exists: seven unsanctioned types accumulated over the driver's entire
history, and **four arrived after the roadmap row was filed naming three**.
Sanctioning them (T01) fixes today. Only these checks fix tomorrow.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

## Copy the shape, do not import it

This repository has built this guard twice. Read both before writing:

- `tests/test_label_registry_covers_consumers.py` (FEAT-2026-0071) — recomputes
  the consumer set at test time so a name added to a consumer without a registry
  entry fails.
- `tests/test_bats_suites_gated.py` (FEAT-2026-0072) — asserts a declared set
  matches an actual set, in both directions, with the reverse filtered.

**Do not import from either.** Three guards over unrelated surfaces sharing a
helper couples them for no gain — the same call FEAT-2026-0072 made about the
precedent it copied.

## State what the guard does not cover

`LEARNINGS [FEAT-2026-0071/G1-CLOSE]` is directly on point:

> *"A registry that imports its vocabulary from consumer modules guards the names
> and nothing else — say so, or the drift test reads as broader than it is … when
> a WU claims a registry 'cannot drift', the close states which fields the guard
> covers and which are unguarded by construction."*

This guard covers **event type names**. It does not cover payload shapes — those
would need the per-type schemas `PLAN.md` scoped OUT. Say so in the test's own
docstring, not only in the close, so the next reader of the file learns it from
the file.

**Acceptance criteria.**

1. `tests/test_driver_event_registry_covers_emitters.py::TestRegistryCoversEmitters::test_every_emitted_type_is_registered`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. That test passes after this WU's edits, with T01's registry in place.
3. The test derives the emitted-type set at **test time** rather than hard-coding
   it — from the driver's `build_event` call sites, from the corpus event logs,
   or both. A hard-coded list is the drift this guard exists to catch.
4. The test asserts every derived type resolves against either the vendored
   envelope or the driver-local registry, and **names the offenders** when it
   fails.
5. A test asserts the guard actually fails on an unregistered type — introduce a
   synthetic type in a fixture and confirm a non-zero result. A guard never
   observed failing is a guard nobody knows works.
6. The test's docstring states which fields it covers (type names) and which are
   unguarded by construction (payload shapes), per the LEARNINGS entry above.
7. A `verification.yml` gate runs the validator over this repository's
   `.specfuse/features/*/events.jsonl` and fails on any **`event_type`**
   validation error. Give it a name consistent with the file's existing
   convention.

   **The gate is scoped to `event_type`, and that scoping is deliberate.** A gate
   failing on *any* validation error cannot be green on this tree: **279
   `correlation_id` errors across 36 files** remain, because the vendored
   envelope's pattern rejects the closing-sequence (`G<n>-CLOSE`, `G<n>-PLAN`, …)
   and hygiene (`TNNH`) ID shapes `.specfuse/rules/correlation-ids.md` documents
   as valid. That gap is filed as
   [FEAT-2026-0073](../../roadmap.md#feat-2026-0073) and is **not this feature's
   work** — wiring an unconditional gate would make the `code` set red for every
   subsequent WU including this gate's own close. Widen the gate to all error
   classes only once 0073 has landed.

8. The new gate is confirmed to exit **0** on the current tree — run it and quote
   the command and exit code. If it is non-zero **on `event_type` errors**, T01 is
   incomplete and this WU must block rather than weaken the gate to make it pass.
   A non-zero `correlation_id` count is expected per criterion 7 and is not a
   reason to block.
9. If the new test suite is a bats suite rather than a Python test,
   `tests/test_bats_suites_gated.py` requires it to be registered in
   `verification.yml` — check which applies and satisfy it.
10. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**Do not touch.** `specfuse/loop/data/schemas/` — T01 owns the registry; if a
type is missing, report it rather than adding it here, because a guard that
edits the thing it guards proves nothing. `specfuse/loop/validate_event.py` —
T01 owns the resolution logic. `tests/test_label_registry_covers_consumers.py`
and `tests/test_bats_suites_gated.py` — read for shape, do not edit or import.
Existing `verification.yml` gates and their commands — this WU adds one, it does
not retune others. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. The real verification surface
is criterion 5 (the guard observed failing) and criterion 8 (the new gate green
on the current tree).

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
T01 is not `done` — see the Context; the emitted-type set cannot be derived at
test time without hard-coding, which would make the guard cosmetic and is a
design problem worth surfacing rather than papering over; the new gate is
non-zero **on `event_type` errors** on the current tree, which means T01 is
incomplete — **do not** narrow the gate further or exclude a failing file to make
it green (the `event_type` scoping in criterion 7 is the only narrowing
sanctioned, and it is already applied); or a feature's
`events.jsonl` fails for a reason that is neither an event-type nor the known
correlation-ID gap (a malformed line, say), which is a different defect and should be
reported, not fixed here. If `.specfuse/verification.yml` is absent from the
files you edited, emit `status: blocked` — do not claim complete.
