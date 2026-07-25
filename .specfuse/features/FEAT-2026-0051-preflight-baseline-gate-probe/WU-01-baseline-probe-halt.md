---
id: FEAT-2026-0051/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.00
produces_driver_helper: probe_baseline, _should_halt_for_preexisting_failure
produces:
  - specfuse/loop/loop.py
  - tests/test_baseline_probe.py
---

# Probe the code gate set at gate entry and halt on a red baseline

**Objective.** Add `probe_baseline()` — one run of the `code` gate set at gate
entry, before any WU is dispatched — and halt the run with
`preexisting_gate_failure` when it comes back red, so zero work units are
dispatched against a failure they did not cause.

**Context.** Part of FEAT-2026-0051, first WU; read `PLAN.md` in this folder for
the scope boundary and the existing-mechanism verdict. Two seams already exist
and must be **reused, not reimplemented**:

- `verify(wu, feature_dir, cfg)` (`specfuse/loop/loop.py:2314`) runs a named gate
  set and returns `(ok_all, report)`. It selects the set via
  `GATES_FOR_TYPE[wu.type]`. The probe needs the `code` set specifically,
  independent of any WU — factor the set-running loop so both callers share it,
  or call it with a minimal probe-shaped argument. Do not copy the subprocess
  block: its stdin/process-group hang defenses are load-bearing.
- `parse_gate_failure_signature(stdout)` (`loop.py:660`) already maps a gate
  report to `(failure_class, failure_signature)`. The baseline's per-gate
  signature uses this, so a baseline signature is directly comparable to a WU
  failure signature (which is what FEAT-2026-0052's ratchet will need).

The halt reuses the per-gate budget brake's mechanics verbatim
(`loop.py:4157-4178`): `backend.set_gate(gate, "awaiting_review")` →
`flush_events(... build_event("human_escalation", ...))` → `commit_bookkeeping`
→ `return 1`. Fire it at **gate entry**, before the `while True` frontier loop at
`loop.py:4145` — not inside the per-WU loop where the budget brake lives.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`verification-discipline.md`) apply. Do not restate them.

**Acceptance criteria.**
- `tests/test_baseline_probe.py::test_red_baseline_halts_before_any_dispatch`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). It stubs the gate runner to report a failing `code` gate and asserts
  the dispatch stub is called **exactly zero times**.
- After this WU's edits that same test passes, and so does
  `tests/test_baseline_probe.py::test_green_baseline_dispatches_normally` — a
  green probe leaves dispatch behavior unchanged (the escalation-predicate check
  in PLAN.md made executable).
- `probe_baseline()` is importable: `python3 -c "from specfuse.loop.loop import
  probe_baseline"` exits 0.
- `probe_baseline()` returns the failing set as a list of
  `{"gate": <name>, "failure_class": <class>, "failure_signature": <sig>}` —
  empty list when every gate passes. A test asserts the empty-list case is
  distinguishable from a probe that did not run.
- The probe runs the **`code`** set only. A test asserts a configured-but-failing
  `doc` gate does not appear in the returned failing set.
- On a non-empty failing set the run emits a `human_escalation` event whose
  payload carries `"reason": "preexisting_gate_failure"`, the gate number, and
  the failing set. A test reads the event off the events path and asserts the
  reason string exactly.
- The gate is flipped to `awaiting_review` and the flip is committed via
  `commit_bookkeeping` on the halt path — asserted by a test, because an
  uncommitted status flip silently reverts on the next `git reset --hard`.
- `run()` returns `1` on the halt path (same contract as the budget brake).
- The probe is skipped when `dry_run` is set and when the gate is already
  `awaiting_review` — two tests, mirroring the budget brake's skip conditions.
- Every new `subprocess.run` (if any) declares `check=` explicitly — the lint
  gate enforces `PLW1510` since FEAT-2026-0037.

**Do not touch.** `verify()`'s subprocess block internals (the stdin=DEVNULL and
process-group kill defenses — reuse, don't rewrite); the gate frontmatter writer
and the kill-switch (T02 owns both); the escalation message text and evidence
payload (T03 owns those — T01 emits a minimal factual message). `.git/`,
secrets. The driver owns git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` (tests, lint,
security, coverage ≥ 90%, leak-scan, the bats suites) must pass, plus the symbol
check above. Note that from this WU onward the driver is running your probe code
against this feature's own gates. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if factoring the gate-set runner
out of `verify()` cannot be done without changing `verify()`'s observable
`(ok, report)` contract — that contract is every WU's exit oracle in every
downstream project, and changing it is out of scope for this WU. Also block if
the probe cannot be placed before the frontier loop without reordering existing
gate-entry side effects (status flips, event emission), since a reorder there
can double-emit bookkeeping. If `probe_baseline` is absent from the files you
edited, emit `status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
