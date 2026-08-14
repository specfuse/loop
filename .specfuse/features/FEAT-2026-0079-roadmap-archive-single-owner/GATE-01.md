---
gate: 1
status: open
cost_budget_usd: 19.00
baseline:
  sha: 468b9d1e9211df913cdba551aeb5eddf376047df
  probed_at: 2026-08-14T15:05:20.987533+00:00
  failing: []
---

# Gate 1 — the skill invokes the archiver instead of describing it

## Definition of done

- `auto_archive_feature` is reachable from a command line, via a module `main()` and a
  `.specfuse/scripts/` re-export shim, with no `pyproject.toml` change.
- `/roadmap-archive`'s Steps 2–5 invoke that command and report its result. Step 1
  validation, `--auto` selection, and the confirmation prompt stay in the skill — human
  judgement is the skill's, mechanics are the driver's.
- A test fails if the mechanics-prose returns to the skill, so option A cannot creep back
  one paragraph at a time.
- The canonical `plugins/specfuse/skills/` copy and the vendored `.specfuse/skills/` copy
  are in sync, verified by the existing `bats tests/sync_scaffold.bats` gate.
- Every implementation work unit in this gate is `done`.
- The terminal close records the settlement in `.specfuse/LEARNINGS.md`.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## Why this gate is terminal

Two substantive work units is well inside the ceremony-proportionality threshold
(`docs/methodology.md` §6), so this feature is a single gate with a single `close` — no
`close-intermediate`, no `plan-next`. If the gate goes off-plan, `gate_eval`'s auto-close
predicate disables auto-close and the close is dispatched as a normal reflective session.

## Arming discipline

Before arming this gate, confirm by runtime probe rather than by reading the diff:

- **The CLI actually archives.** Run `python3 -m specfuse.loop.roadmap_archive` against a
  throwaway copy of a real feature's roadmap row and read the resulting `roadmap.md` /
  `roadmap-archive.md`. A green unit test on a synthetic fixture is not the same claim.
- **The shim resolves without an install.** Invoke `.specfuse/scripts/roadmap_archive.py` in a
  interpreter that cannot import `specfuse` from site-packages. This is the property T02's
  delegation depends on; if it does not hold, the feature's premise is wrong.
- **The guard bites.** Reintroduce one sentence of mechanics-prose into the skill and confirm
  `test_skill_carries_no_mechanics_prose` fails. A guard nobody has seen fail is unproven.
- **Scope check.** `pyproject.toml` unmodified; `auto_archive_feature` and
  `_reconcile_moved_section` bodies unmodified.

## Verification

Gate set `code`, per `.specfuse/verification.yml`:

- `python3 -m unittest discover -s tests -v -b`
- `ruff check specfuse .specfuse/scripts tests scripts`
- `bandit -r specfuse .specfuse/scripts -ll`
- `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90`
- `bats tests/sync_scaffold.bats` — T02 touches the vendoring path
- `python3 .specfuse/scripts/roadmap_link_gate.py`
