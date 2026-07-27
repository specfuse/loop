---
id: FEAT-2026-0046/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces:
  - specfuse/loop/escalation.py
  - tests/test_escalation_emit.py
produces_driver_helper:
  - emit_escalation
---

# Add the escalation emission primitive, idempotent and never auto-fired

**Objective.** Add `emit_escalation(...)` to `specfuse/loop/escalation.py`: it files a
`needs-human` GitHub issue for an escalating unit, and filing twice for the same
correlation ID does not create a second issue.

**Context.** Correlation ID `FEAT-2026-0046/T02`. Depends on `T01`, which supplies
`NEEDS_HUMAN_LABEL`, `CATEGORY_LABELS`, `render_escalation_body`, and the
`<!-- specfuse:escalation id=... -->` marker this unit searches on. Reuse those; do
not re-derive them.

**Follow the existing runner seam.** `specfuse/loop/gh_backend.py` takes an injectable
`_runner` (default `_default_runner`, which shells out to `gh`) precisely so tests can
drive it without touching GitHub. Mirror that seam here: `emit_escalation` accepts a
runner argument defaulting to the same real implementation, and every test in this WU
injects a stub. Read `gh_backend.py` before writing, and match its shape rather than
inventing a second convention.

**Idempotency is the load-bearing property.** Emitting is a live mutation of an
external system. `emit_escalation` must first search for an open issue carrying the
`needs-human` label and this unit's correlation marker, and create only when that
search returns nothing. `GitHubBackend.on_feature_complete` already uses this
find-then-create shape for pull requests — the comment there reads *"Idempotent: skip
PR creation if one already exists for this branch."* Follow it.

**The primitive is invoked, never fired.** `[FEAT-2026-0003/G3-LESSONS]` established
that a work unit mutating live GitHub issues is irreversible at execution time and
cannot be safely delegated to the driver's subprocess loop. Auto-emitting on every
`blocked_human` would put that mutation inside the automatic dispatch path and would
file an issue every time a unit blocks during ordinary development. Criterion 8 asserts
that absence; it is a scope boundary this feature is committing to, not an oversight.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_escalation_emit.py::TestEmitEscalation::test_second_emit_for_same_correlation_id_creates_nothing`
   exists and **fails on HEAD before this WU runs** (the test file does not yet exist,
   which counts as red).
2. `specfuse/loop/escalation.py` defines `emit_escalation(...)` accepting an injectable
   runner argument that defaults to the real `gh`-invoking implementation, in the same
   shape `gh_backend.GitHubBackend.__init__` uses for `_runner`.
3. With a stub runner reporting no existing issue, `emit_escalation` issues a create
   call whose arguments include the `needs-human` label.
4. With a stub runner reporting no existing issue, the create call's arguments include
   exactly one member of `CATEGORY_LABELS`.
5. With a stub runner reporting no existing issue, the create call's arguments include
   the configured assignee.
6. With a stub runner reporting an existing open issue carrying this correlation ID's
   marker, `emit_escalation` issues **no** create call and returns the existing issue's
   identifier.
7. The body passed to the create call satisfies `validate_escalation_body` with an
   empty findings list.
8. `grep -rn "emit_escalation" specfuse/loop/loop.py` returns no call site — the
   dispatch loop never invokes the primitive. (An import for re-export is acceptable
   only if it is not a call; the grep must show no invocation.)
9. No test in `tests/test_escalation_emit.py` invokes the real `gh` binary: every test
   injects a stub runner.
10. `python3 -m pytest tests/test_escalation_emit.py -q` exits zero after this WU's
    edits (the same file named in criterion 1).
11. `python3 -c "from specfuse.loop.escalation import emit_escalation"` exits zero.

**Do not touch.** `specfuse/loop/loop.py` — criterion 8 asserts this WU adds no call
site there, so editing it is out of scope. `specfuse/loop/gh_backend.py` — read it for
the runner shape; do not modify it. Files owned by T01 beyond the additive
`emit_escalation` function. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set: `tests`, `lint`, `security`, `coverage`
(≥90%), `leak-scan`. Plus the scoped red/green run in criteria 1 and 10, the
symbol-existence import in criterion 11, and the grep in criterion 8 — that grep is
the only check that can catch an accidental auto-wire, and no code gate detects it.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`gh` search syntax needed to find an issue by body marker cannot be expressed without
a real API call to discover it; T01's marker format is absent or differs from this
WU's Context; or satisfying the coverage floor would require a test that invokes the
real `gh` binary, which criterion 9 forbids. If `emit_escalation` is absent from the
files you edited, emit `status: blocked` — do not claim complete.
