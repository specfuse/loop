---
id: FEAT-2026-0002/T05
type: implementation
effort: low
status: pending
attempts: 0
---

# Raise coverage --fail-under floor to 90

**Objective.** Flip `.specfuse/verification.yml`'s coverage gate
from `--fail-under=70` to `--fail-under=90` and remove the deviation
comment block. Depends on T01-T04 landing first so the new floor is
satisfied by the gate's own work.

**Context.** This is `FEAT-2026-0002/T05`. The current `code.coverage`
entry in `.specfuse/verification.yml` reads:

```yaml
  - name: coverage
    # --fail-under=70 is the loop repo's own floor — BELOW the methodology's
    # ≥ 90% default but climbing. Measured 80% TOTAL today (... )
    # ...
    # Raise this floor toward 90 once those land.
    command: "coverage run --source=.specfuse/scripts -m unittest discover -s tests && coverage report --fail-under=70"
```

The whole multi-line comment was a deviation note explaining why the
floor sat below 90. With T01-T04 landed, the deviation is closed; the
floor and the comment both need to move.

`scripts/smoke-test.sh` line 55 hardcodes `--fail-under=70` independently
of `verification.yml` (per the file's "keep three in sync" note in the
top comment of `ci.yml`). It must be flipped to `90` as part of this WU
or the smoke-test (and therefore CI) will diverge.

Per LEARNINGS [FEAT-2026-0007/G2-LESSONS]: a new enforcement mechanism
cannot exercise itself in the implementing gate's own GATE.md. This WU's
verification therefore runs at the **new** `--fail-under=90` against the
gate's already-landed T01-T04 work — the first independent exercise of
the raised floor belongs to the next feature.

Reference the binding rules under `.specfuse/rules/`. Edit files only;
do not commit (driver squashes).

**Acceptance criteria.**

1. `.specfuse/verification.yml`'s `code.coverage.command` ends with
   `--fail-under=90` (was `=70`).
2. The deviation comment block above `command:` in the coverage entry
   is removed in full. A single short comment line is acceptable in
   its place if it documents what the floor is (e.g. "matches the
   methodology default"); a multi-line measurement / history block is
   not.
3. `scripts/smoke-test.sh`'s coverage line (the `coverage report
   --fail-under=70` invocation, line 55 as of HEAD-before) is flipped
   to `--fail-under=90`.
4. Running `./scripts/smoke-test.sh` exits 0 against the gate's
   landed work — the new floor is satisfied today.
5. Running `python3 .specfuse/scripts/loop.py --dry-run` exits 0 on
   this feature folder (loads cleanly).
6. **Drift check.** `grep -n "fail-under" .specfuse/verification.yml
   scripts/smoke-test.sh .github/workflows/ci.yml` returns either
   `=90` everywhere it appears OR no match at all in `ci.yml` (which
   delegates to `smoke-test.sh`). No `=70` survives.

**Do not touch.** Exactly 2 files change:
`.specfuse/verification.yml` and `scripts/smoke-test.sh`. No edits to:
`.github/workflows/ci.yml` (it delegates to smoke-test.sh; no fork),
`.specfuse/scripts/`, test files (T01-T04 own them), `.specfuse/rules/`,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(now running at the new floor), PLUS the drift check AC 6. Declare
`files_changed: [.specfuse/verification.yml, scripts/smoke-test.sh]`
in the RESULT block.

**Escalation triggers.**

1. **New floor fails on the gate's own work.** If the post-flip
   `coverage report --fail-under=90` exits non-zero, do not lower the
   floor and do not pad coverage. Emit `status: blocked` naming the
   per-file shortfall — one of T01-T04 underdelivered and the right
   move is to re-dispatch the relevant WU, not to weaken this one.
2. **Smoke-test drift.** If `scripts/smoke-test.sh` already reads
   `--fail-under=90` at HEAD-before (T01-T04 leaked a change here),
   emit `status: blocked` — the upstream WU exceeded its scope and
   this WU's two-file change becomes one.
3. **CI workflow drift.** If `.github/workflows/ci.yml` is found to
   hardcode the floor (no longer delegates to smoke-test.sh), emit
   `status: blocked` — the three-way sync rule is broken and the fix
   is a separate WU.
