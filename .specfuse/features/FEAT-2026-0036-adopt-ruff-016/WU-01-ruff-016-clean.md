---
id: FEAT-2026-0036/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
---

# Make the tree pass `ruff check` under ruff 0.16

**Objective.** Fix every ruff 0.16 lint error (≈300, mostly import
sorting/consolidation in `tests/`) so `ruff check` exits 0 under ruff 0.16.x,
without changing any runtime or test behavior.

**Context.** Part of FEAT-2026-0036. ruff 0.16.0 tightened import rules; the
tree currently only lints clean under the pinned ruff 0.15.x
(`pyproject.toml`, `ruff>=0.6,<0.16`). This unit does the mechanical cleanup so
the pin can be lifted in T02. Install ruff 0.16 for this unit only (e.g.
`pip install 'ruff>=0.16'` in the working venv, or `uvx ruff@latest`) — do NOT
edit the `pyproject.toml` pin here; T02 owns that. Binding rules in
`.specfuse/rules/` (`result-contract.md`, `never-touch.md`) apply.

`Red-test exempt: pure lint/import-formatting change — no new behavior. §12
carve-out (refactor). The proof of done is ruff exit 0 + the unchanged suite,
not a new red→green test.`

**Acceptance criteria.**
- `ruff check` (ruff ≥ 0.16) over the repo exits 0 — quote the version
  (`ruff --version`) and the `All checks passed!` line.
- `ruff check --fix` was run first for the auto-fixable subset; remaining
  errors were resolved by hand (import ordering/consolidation only).
- Every edit is confined to import statements / import blocks. No change to any
  function body, test assertion, string literal, or runtime code — confirm with
  `git diff` that non-import lines are untouched.
- The full suite still passes with the SAME test count as HEAD before this WU:
  `python3 -m unittest discover -s tests -q` reports `OK` and the count did not
  drop.
- The `pyproject.toml` ruff pin is left unchanged (`>=0.6,<0.16`) — T02 lifts it.

**Do not touch.** `pyproject.toml` (T02 owns the pin flip), any non-`tests/`
source unless ruff flags it there too, `.git/`, secrets. The driver owns git.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` (tests,
coverage, warnings, lint, security) must pass under the still-pinned ruff. In
addition, the unit-specific oracle: with ruff ≥ 0.16 installed, `ruff check`
exits 0. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if a ruff 0.16 error cannot be
fixed by an import-only edit (i.e. it demands a real code change) — that is out
of this unit's import-only scope and needs a plan revision. Also block if the
test count would drop or any test starts failing after the import edits: that
means an edit was not behavior-preserving. Blocked is a respectable outcome
(`result-contract.md` rule 4).
