---
id: FEAT-2026-0036/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
---

# Lift the `<0.16` ruff pin

**Objective.** Now that the tree is clean under ruff 0.16 (T01), remove the
temporary upper bound so the linter tracks current again.

**Context.** Part of FEAT-2026-0036, depends on T01. The emergency pin lives in
`pyproject.toml`'s `[project.optional-dependencies].dev` list as
`ruff>=0.6,<0.16`, with a multi-line comment above it explaining the pin and
naming this feature. Binding rules in `.specfuse/rules/` apply.

`Red-test exempt: dependency-constraint change — no new behavior. §12 carve-out.
The proof is CI resolving ruff 0.16 and the lint gate passing, verified below.`

**Acceptance criteria.**
- `pyproject.toml` `dev` extra lists `ruff>=0.16` (or a bare `ruff>=0.6` open
  floor) — the `<0.16` upper bound is gone.
- The explanatory pin comment (the block naming FEAT-2026-0036 and the ~300
  errors) is removed, since it no longer describes the constraint.
- `pyproject.toml` remains valid TOML: `python3 -c "import tomllib;
  tomllib.load(open('pyproject.toml','rb'))"` exits 0.
- With ruff resolved at ≥ 0.16, `ruff check` over the repo exits 0 (the T01
  cleanup holds under the now-unpinned linter).
- The full suite still passes: `python3 -m unittest discover -s tests -q`
  reports `OK`.

**Do not touch.** Any file other than `pyproject.toml`. Test files were made
clean in T01 — do not re-edit them here. `.git/`, secrets. The driver owns git.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — which now
resolve ruff 0.16 — must pass, including the lint gate. The smoke-test's
"scaffold smoke-test + code gates" step is the CI-side oracle. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if lifting the pin resurfaces
ruff errors (T01 missed a case, or 0.16.x moved again) — do not re-pin silently;
report so T01's scope can be reopened. Blocked is a respectable outcome
(`result-contract.md` rule 4).
