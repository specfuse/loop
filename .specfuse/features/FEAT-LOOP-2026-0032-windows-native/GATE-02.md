---
gate: 2
status: passed
cost_budget_usd: 5.0
---

# Gate 2 — Gate commands execute correctly on Windows (via Git-Bash)

## Definition of done

- On `windows-latest` CI, a real `.specfuse/verification.yml` gate command runs
  green through Git-Bash (`bash -c`).
- `python3`-style gate commands and the `SMOKE_IMPORT_RE` smoke-import path
  resolve to the Windows interpreter (`python`/`py`).
- The `claude` CLI resolves on Windows (`shutil.which` + `PATHEXT`) so agent
  dispatch finds `claude.cmd`.
- Closing `close` WU: retrospective + lessons + docs + terminal verdict.

**This gate is skeletal.** Its substantive work units are drafted by gate 1's
`plan-next` closing WU (`WU-91`), which reads gate 1's outcome and this DoD,
then inserts the gate-2 WUs *before* the pre-declared `G2-CLOSE` and updates
`G2-CLOSE`'s `depends_on`. The lone `G2-CLOSE` placeholder here exists only so
the linter reads this (the last non-empty gate) as terminal and gate 1 as
non-terminal.

## Reflection notes

<Written by the human at review time.>
