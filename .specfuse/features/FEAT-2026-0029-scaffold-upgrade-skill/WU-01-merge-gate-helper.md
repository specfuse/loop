---
id: FEAT-2026-0029/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.75
produces: .specfuse/scripts/upgrade_merge_gate.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.3.6
started_at: 2026-07-04T01:36:25.921688+00:00
duration_seconds: 469.239
cost_usd: 1.240963
input_tokens: 12992
output_tokens: 11946
---

# Add the merge-safety gate helper for scaffold upgrades

**Objective.** A small, unit-tested module that decides whether a post-upgrade PR
is safe to auto-merge: `merge` only when CI is green AND every existing feature
folder still passes the scaffold-conformance lint; `halt` (with a reason)
otherwise.

**Context.** This is `FEAT-2026-0029/T01`, the one piece of real decision logic in
the `scaffold-upgrade` skill (T02 calls it). After `specfuse upgrade` overlays a
newer scaffold, existing feature folders can fall out of conformance with the new
structural contract — exactly the FAIL condition `/feature-conversion` exists to
fix (see `.specfuse/skills/feature-conversion/SKILL.md`). The **implemented,
in-repo** signal for that condition is `.specfuse/scripts/lint_plan.py`: run per
feature folder, it exits `0` when the folder is structurally valid and non-zero
(printing the specific errors) when it is not. This module turns "CI status + the
per-feature lint results" into a merge/halt verdict so the skill never lands a
scaffold that breaks feature folders.

**Do not invent a `specfuse upgrade` "health report" string format.** An earlier
draft of this WU pointed at a health report emitted by `specfuse upgrade`; that
format is not defined or implemented anywhere in this repo (only described in prose
in the feature-conversion skill). The contract is therefore a **Python data
structure**, not a parsed report string — see `decide` below.

Live under `.specfuse/scripts/upgrade_merge_gate.py`, importable by file path in
the test (the pattern other `.specfuse/scripts` helpers use — not a package
import). Reference the binding rules under `.specfuse/rules/`
(`result-contract.md`, `never-touch.md`, `security-boundaries.md`); honor them
rather than restating.

**Acceptance criteria.**

1. **Red test (fails on HEAD):** `tests/test_upgrade_merge_gate.py::test_halts_when_a_feature_fails_conformance`
   asserts `decide(...)` returns a `halt` verdict when any feature report is not
   ok. It fails on HEAD because the module does not yet exist (`ModuleNotFoundError`
   / import error is an acceptable red).
2. `decide(ci_all_green: bool, feature_reports: list[dict]) -> tuple[str, str]`
   where each report is `{"feature": str, "ok": bool, "detail": str}`. Returns
   `("merge", "")` only when `ci_all_green is True` AND every report has
   `ok is True`; otherwise `("halt", <reason>)` naming the cause — the failing
   feature id(s), or `"CI not green"`.
3. `collect_reports(repo_root) -> list[dict]` runs `lint_plan.py` once per
   `<repo_root>/.specfuse/features/*/` directory and maps each result to a report
   dict (`ok = (exit code == 0)`, `detail` = a short trailing slice of the lint
   output on failure). Returns one report per feature folder found.
4. The red test passes after this WU. Additional table-driven `decide` cases pass:
   all-ok reports + green CI → `merge`; any not-ok report → `halt`; green CI but a
   not-ok report → `halt`; all-ok reports but CI not green → `halt`.
5. **Empty input → fail safe:** `decide(True, [])` returns `halt` with a reason
   that no feature folders were checked (never `merge` on absence of evidence). A
   `collect_reports` run against a repo with no feature folders returns `[]`.
6. `collect_reports` is covered by a test that builds a tmp repo with one
   structurally-valid feature folder and one invalid one, and asserts the returned
   list marks them `ok=True` / `ok=False` respectively.
7. **Symbol-existence check:** `python3 -c "import importlib.util,pathlib; s=importlib.util.spec_from_file_location('umg', pathlib.Path('.specfuse/scripts/upgrade_merge_gate.py')); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert callable(m.decide) and callable(m.collect_reports)"`
   exits 0.

**Do not touch.** The driver and linter internals (call `lint_plan.py` as a
subprocess — do not import or modify it), other WUs' files, `specfuse upgrade`
itself, `.git/`, secrets, generated dirs. The driver owns all git. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests`), `coverage` (≥ 90%), `lint`
(`ruff check`), `security` (`bandit`). Plus the AC7 symbol check above.

**Escalation triggers.** If `lint_plan.py` cannot be invoked as a per-feature
conformance check the way this WU assumes (e.g. it takes no single-feature-folder
argument), emit `status: blocked` naming the mismatch rather than inventing an
alternative signal. If `decide` / `collect_reports` cannot be added to
`.specfuse/scripts/upgrade_merge_gate.py` (file absent from your edits), emit
`status: blocked` — do not claim complete. Blocked is a respectable outcome
(`result-contract.md` rule 4).
