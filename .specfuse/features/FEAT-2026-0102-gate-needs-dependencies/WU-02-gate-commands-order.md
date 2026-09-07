---
id: FEAT-2026-0102/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
oracle_env: macos_local
produces:
  - specfuse/loop/gate_commands.py
  - tests/test_gate_commands_needs.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.15.0
started_at: 2026-09-07T19:18:49.349019+00:00
duration_seconds: 1424.34
cost_usd: 0.80871
input_tokens: 58
output_tokens: 12359
---

# Emit gates in dependency order so CI and the driver cannot disagree

**Objective.** Make `gate_commands.py` honour `needs:` when it emits a gate
set, so the order `scripts/smoke-test.sh` and CI execute matches the order T01
gave the driver.

**Context.** FEAT-2026-0102/T02; read `PLAN.md` and T01. `gate_commands.py` is
the derivation path from #592 — `verification.yml` is the single source of
truth and the smoke runner reads it rather than carrying a copy. Its parser is
deliberately regex-based over `_miniyaml` (see its docstring) and matches only
`^  - name:` and `command:`, so a `needs:` key is currently invisible to it.
Left unfixed, CI would run `coverage` without `tests` having run — reporting
over absent coverage data while the driver ran the same set correctly. Two
oracles disagreeing about the same file is exactly what
[FEAT-2026-0002/G1-CLOSE] means by enumerating every site and flipping them
together.

**Ordering only — the skip is already handled.** `scripts/smoke-test.sh`
carries `set -euo pipefail` (line 16) and `eval`s each emitted gate in
sequence, so a failing dependency already aborts the run before its dependents.
This unit supplies order; it does **not** add skip logic to the shell, and it
does not edit `scripts/smoke-test.sh` at all.

**Acceptance criteria.**

- `tests/test_gate_commands_needs.py::test_emitted_order_is_topological` fails on HEAD and passes after: a fixture set declaring `coverage` (needs `tests`) before `tests` emits `tests` first.
- `::test_order_matches_driver`: for the same fixture, the gate-name sequence `gate_commands` emits equals the sequence `loop._run_gate_set` executes. This is the anti-drift assertion — it is the point of the unit, so assert the two orders against each other, not each against a hardcoded list.
- `::test_absent_needs_preserves_declared_order`: a set with no `needs:` key emits exactly what it emits on HEAD.
- `python3 -m unittest discover -s tests -q` reports `OK`, and `bash scripts/smoke-test.sh` exits 0 with the gate list unchanged (this repo does not declare `needs:` until T03).

**Do not touch.** `specfuse/loop/loop.py` (T01); `scripts/smoke-test.sh` — no
shell change is needed and editing it would pull §11's shellcheck/bats
obligations into this unit; `.specfuse/verification.yml` and the verification
skill (T03); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
`bash scripts/smoke-test.sh`.

**Escalation triggers.** Emit `status: blocked` if honouring `needs:` cannot be
done within the module's regex parser and would require importing `_miniyaml` —
its docstring records that dependency as deliberately avoided on a path CI
depends on, so that trade is an operator decision, not yours to make silently.
</content>
