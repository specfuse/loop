---
id: FEAT-2026-0224/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - tests/test_layout_validation.py
  - tests/test_layout_end_to_end.py
  - specfuse/loop/layout.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.29.1
started_at: 2026-10-28T00:40:54.119604+00:00
duration_seconds: 62.847
cost_usd: 0.246509
input_tokens: 16
output_tokens: 7476
---

# T02 — an invalid layout is reported, and `paths:` is a warning

**Objective.** Oracle clause 4 goes green: `layout.validate(repo_root) -> list[Finding]`
and `python3 -m specfuse.loop.layout check` report every malformed layout instead of
silently resolving it.

**Context.** `Finding` reuses `lint_roadmap`'s `Finding` / `SEVERITY_ERROR` /
`SEVERITY_WARN` shape (import them; do not redefine) so T05 can append these findings
unchanged. `check` prints one finding per line and exits 1 on any ERROR, 0 otherwise.
`load()` must still never raise on a bad file: it returns defaults, and `validate()`
is where the problem surfaces.

Rules, each with exactly one negative test in `tests/test_layout_validation.py`:

- `location` absolute (`/abs`) → ERROR.
- `location` containing a `..` segment → ERROR.
- Windows drive (`C:\x`, `C:/x`) → ERROR; a backslash anywhere → ERROR.
- `location` resolving through a symlink to outside the repo root → ERROR (test
  builds the symlink in a temp dir; skip on platforms without symlink support).
- Trailing slash normalised: `docs/decisions/` and `docs/decisions` resolve equal
  (positive test).
- `style` not in `{adr, entries}` → ERROR naming both values.
- `link` with a placeholder outside `{location}`, `{path}`, `{id}`, `{domain}` →
  ERROR naming the placeholder.
- A top-level `paths:` block → WARN whose message names the authoring follow-up
  ("`paths:` is not supported yet; the authoring follow-up to FEAT-2026-0224 adds
  it") — never an ERROR, never silently accepted.
- Any other unknown top-level key → WARN.
- Positive control: no file, and a valid entries file, both return `[]`.

Un-skip `InvalidLayoutIsReported` in the oracle module: `check` on an absolute-location
layout exits 1 naming the path; on a `paths:` layout exits 0 with the WARN line.

**Acceptance criteria.**

1. `tests/test_layout_validation.py` (every case above) and
   `tests/test_layout_end_to_end.py::InvalidLayoutIsReported` fail on HEAD and pass
   after.
2. Each rejected form has exactly one test whose name states it (e.g.
   `test_rejects_dotdot_segment`).
3. `tests.test_layout` still passes, and `load()` on every invalid fixture returns a
   `Layout` without raising.

**Do not touch.** `lint_roadmap.py` (T05 wires the findings in).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_layout -b`.

**Escalation triggers.** If importing `Finding` from `lint_roadmap` creates an import
cycle once T05 imports `layout`, move `Finding` to a shared module only by escalating
first — it is used by other lints.
