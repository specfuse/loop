---
id: FEAT-2026-0070/T05
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.00
produces:
  - specfuse/loop/_wu_sections.py
  - specfuse/loop/lint_plan.py
oracle_env: macos_local
produces_driver_helper: slice_wu_section
model: sonnet
effort: medium
---

# Extract the WU body-section slicers into a module both `loop.py` and `lint_plan.py` can import

**Objective.** Move `_slice_ac_section` / `_slice_section` out of `lint_plan.py` into a new
dependency-free module `specfuse/loop/_wu_sections.py`, so `FEAT-2026-0070/T06` can read a
work unit's `**Acceptance criteria.**` section from `loop.py` **without a second copy of the
parser**. Pure extraction: no behavior change, no new caller.

**Context.** This is `FEAT-2026-0070/T05`, the first WU of gate 2 and a precursor to T06.
Read `PLAN.md` and `GATE-02.md` in this folder first; `GATE-02-REVIEW.md` records why this
WU exists.

**Why a new module and not an import.** `lint_plan.py:35` already does
`from .loop import VERDICT_VALUES`. `loop.py` therefore **cannot** import `lint_plan` —
that is a circular import, and it fails at interpreter start, not at the call. A neutral
third module is the only shape that lets both sides share one parser. `_miniyaml.py` and
`_filelock.py` are the existing precedent for a leaf module in this package.

**§10 helper-duplication pre-flight, run at drafting time** (`authoring-work-units` §10 —
the enumeration is complete and every hit is in scope below):

```
grep -rn "_slice_ac_section" --include="*.py" .
    -> specfuse/loop/lint_plan.py:126  (def)
       specfuse/loop/lint_plan.py:652  (call — check_oracle_env)
       tests/test_lint_oracle_env.py:117 (call — via lint_plan._slice_ac_section)
grep -rn "_slice_section" --include="*.py" .
    -> specfuse/loop/lint_plan.py:137  (def)
       specfuse/loop/lint_plan.py:458, :474, :684, :891  (4 calls)
grep -rn "_AC_START_RE\|_AC_END_RE" --include="*.py" .
    -> specfuse/loop/lint_plan.py:120, :123 (defs); :128, :133, :145 (uses, both
       inside the two functions above — no other consumer)
```

**Files modified to switch to the new helper.** Only `lint_plan.py`. The five internal call
sites and the one test call site are **deliberately not edited**: `_slice_ac_section` and
`_slice_section` keep their existing names, signatures, and return values and become
one-line delegations to the new module. That is what makes this a zero-risk extraction —
if a call site needed editing, the extraction would not be behavior-preserving.

`Red-test exempt: pure extraction — the two functions keep their names, signatures, and
outputs, and no caller changes. There is no new behavior to assert red. The existing
lint_plan suite (tests/test_lint_oracle_env.py, tests/test_lint_plan_*.py) is the
regression oracle, and AC1 requires it green both before and after.`

Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**

1. **Regression oracle, established before and after.**
   `python3 -m unittest discover -s tests -p "test_lint*.py" -v` exits zero on HEAD before
   any edit, and exits zero again after this WU's edits, with the same test count. Record
   both counts in the RESULT block. A changed count means the extraction was not
   behavior-preserving.
2. `specfuse/loop/_wu_sections.py` exists and imports **nothing** from `loop`, `lint_plan`,
   or `gate_eval` — `grep -nE "^(from|import)" specfuse/loop/_wu_sections.py` shows only
   `re` (and `from __future__ import annotations`). This is the property that makes it
   importable from both sides.
3. It exports two public functions: `slice_acceptance_criteria(body: str) -> str` and
   `slice_wu_section(body: str, section_name: str) -> str`, with the bodies moved verbatim
   from `lint_plan._slice_ac_section` / `_slice_section`, plus the `_AC_START_RE` /
   `_AC_END_RE` patterns they depend on.
4. `lint_plan._slice_ac_section` and `lint_plan._slice_section` still exist under those
   exact names and delegate to the new functions. `tests/test_lint_oracle_env.py:117` calls
   `lint_plan._slice_ac_section` and must keep working **unedited** — if that file needs a
   change, AC1 has already failed.
5. `python3 -c "from specfuse.loop._wu_sections import slice_acceptance_criteria, slice_wu_section"`
   exits 0, and `python3 -c "import specfuse.loop.loop, specfuse.loop.lint_plan"` exits 0
   (no import cycle introduced) — `authoring-work-units` §9 symbol-existence check.
6. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0070-terminal-flip-contract`
   still exits 0 with the same findings as before the edit.
7. The full `code` gate set passes, coverage ≥ 90%.

**Cost-reintroduction trade (`[FEAT-2026-0039/G2-CLOSE]`).** This WU dispatches nothing at
runtime and adds no runtime work of any kind — it is a compile-time refactor. It lands on
the **keeps the saving** side of the trade by construction.

**Do not touch.**

- `loop.py` — T05 does not add the caller. `FEAT-2026-0070/T06` is the first consumer, and
  splitting the extraction from the behavior change keeps each squash reviewable.
- The five `_slice_section` call sites (`lint_plan.py:458, :474, :684, :891`) and the one
  `_slice_ac_section` call site (`:652`) — out of scope by design; the delegation shim is
  what keeps them unedited. See the §10 enumeration above.
- `tests/test_lint_oracle_env.py` — AC4 makes editing it a failure signal, not a task.
- The regex bodies themselves. Moving them is in scope; *changing* what they match is not —
  `lint_plan`'s section detection is load-bearing for five other checks.
- `.git/`, secrets. The driver owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests, ruff, bandit,
coverage ≥ 90%, leak-scan, the four `bats` gates). Scoped regression proof per AC1:
`python3 -m unittest discover -s tests -p "test_lint*.py" -v`. Symbol and no-cycle checks
per AC5. Plan lint per AC6.

> Sandbox note: the four `bats` gates call `mktemp -d` in `setup`, which the default session
> sandbox denies before any assertion runs (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`).
> Report which sandbox each gate ran under.

**Escalation triggers.** Emit `status: blocked` if the extraction cannot be made
behavior-preserving — if any of the six existing call sites needs an edit to keep passing,
the two functions are not the pure text slicers this WU assumes and T06's design needs
re-checking before the extraction is worth doing. Also block if `_wu_sections.py` cannot
avoid importing `loop` or `lint_plan`: a leaf module that is not a leaf reintroduces the
cycle this WU exists to avoid, and the right answer is an operator decision about module
layout, not a lazy import inside a function. Blocked is a respectable outcome
(`result-contract.md` rule 4).
