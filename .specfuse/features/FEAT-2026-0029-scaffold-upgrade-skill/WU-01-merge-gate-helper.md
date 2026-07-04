---
id: FEAT-2026-0029/T01
type: implementation
status: blocked_human
attempts: 0
planned_cost_usd: 1.75
produces: .specfuse/scripts/upgrade_merge_gate.py
oracle_env: macos_local
duration_seconds: 86.287
cost_usd: 0.714617
input_tokens: 13279
output_tokens: 3921
---

# Add the merge-safety gate helper for scaffold upgrades

**Objective.** A small, unit-tested predicate that decides whether a
post-upgrade PR is safe to auto-merge: `merge` only when CI is green AND the
post-upgrade health report is clean; `halt` (with a reason) otherwise.

**Context.** This is `FEAT-2026-0029/T01`, the one piece of real decision logic
in the `scaffold-upgrade` skill (T02 calls it). The `scaffold-upgrade` skill runs
`specfuse upgrade <target>`, which emits a health report classifying each feature
folder as PASS/FAIL against the current scaffold contract (the same report
`/feature-conversion` keys off — see `.specfuse/skills/feature-conversion/SKILL.md`).
A FAIL means an existing feature no longer conforms and must be converted before
the upgrade is safe to land. This helper turns "CI status + health report" into a
merge/halt verdict so the skill never lands a scaffold that breaks feature folders.

Live under `.specfuse/scripts/upgrade_merge_gate.py`, importable by file path in
the test (the pattern other `.specfuse/scripts` helpers use — not a package
import). Reference the binding rules under `.specfuse/rules/`
(`result-contract.md`, `never-touch.md`, `security-boundaries.md`); honor them
rather than restating.

**Acceptance criteria.**

1. **Red test (fails on HEAD):** `tests/test_upgrade_merge_gate.py::test_halts_on_health_fail`
   asserts `decide(...)` returns a `halt` verdict when the health report contains
   a FAIL row. It fails on HEAD because the module does not yet exist
   (`ModuleNotFoundError` / import error is an acceptable red).
2. `decide(ci_all_green: bool, health_report: str) -> tuple[str, str]` returns
   `("merge", "")` only when `ci_all_green is True` AND the health report parses
   to zero FAIL rows; otherwise `("halt", <reason>)` where the reason names the
   cause (health FAIL feature id(s), or "CI not green").
3. The same red test passes after this WU. Additional table-driven cases pass:
   clean report + green CI → `merge`; any FAIL row → `halt`; green CI but FAIL →
   `halt`; clean report but CI not green → `halt`.
4. **Empty / unrecognized report → fail safe:** when the report string is empty or
   has no parseable PASS/FAIL rows, `decide` returns `halt` with a reason saying
   the health report could not be confirmed clean (never `merge` on absence of
   evidence).
5. **Symbol-existence check:** `python3 -c "import importlib.util,pathlib; s=importlib.util.spec_from_file_location('umg', pathlib.Path('.specfuse/scripts/upgrade_merge_gate.py')); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert callable(m.decide)"`
   exits 0.

**Do not touch.** The driver and linter internals, other WUs' files,
`specfuse upgrade` itself, `.git/`, secrets, generated dirs. The driver owns all
git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests`), `coverage` (≥ 90%), `lint`
(`ruff check`), `security` (`bandit`). Plus the AC5 symbol check above.

**Escalation triggers.** If the health-report format `specfuse upgrade` emits is
ambiguous or undiscoverable from the codebase (no fixture, no example output),
emit `status: blocked` naming the ambiguity rather than guessing a parser — T02's
correctness depends on this parser matching the real report. If `decide` cannot be
added to `.specfuse/scripts/upgrade_merge_gate.py` (file absent from your edits),
emit `status: blocked` — do not claim complete. Blocked is a respectable outcome
(`result-contract.md` rule 4).
