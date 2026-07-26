---
id: FEAT-2026-0039/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - .specfuse/scripts/lint_monitoring.py
  - tests/test_monitoring_seed.py
produces_driver_helper: scaffold seed registration for monitoring.yml.example
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-25T21:32:58.414431+00:00
duration_seconds: 739.812
cost_usd: 3.225256
input_tokens: 5550
output_tokens: 20227
---

# Ship the validator shim, seed the example, and wire the gate

**Objective.** Make the monitoring contract reachable from outside the package: a
`.specfuse/scripts/` shim, seeding of `monitoring.yml.example` into freshly
scaffolded projects, a `code` gate in this repo that validates the shipped example,
and a commented-out gate in `verification.yml.example` for target projects.

**Context.** This is `FEAT-2026-0039/T03`, following T02. Read `PLAN.md` in this
folder — its **escalation-predicate satisfiability** section constrains this WU
more than any other, because this is the WU that creates the new blocking gate.

Three seams already exist and must be **followed, not invented**:

- **The shim pattern.** `.specfuse/scripts/lint_plan.py` is the exact template: a
  path-inserting re-export of the package module that mirrors its public namespace
  and delegates `main()`. Copy its shape for `lint_monitoring.py`. Canonical code
  stays in `specfuse/loop/`; the shim holds no logic.
- **Seeding.** `specfuse/loop/scaffold.py` registers seed files; `_SEED_RENAME`
  (`scaffold.py:120`) maps `verification.yml.example -> verification.yml` because
  gates are mandatory. **Monitoring is opt-in, so `monitoring.yml.example` gets NO
  rename entry.** It seeds under its own name; the `derive-monitoring` skill (gate
  2) writes the live `monitoring.yml`. Adding a rename would auto-create a live
  monitoring config in every scaffolded project, including ones that deploy nothing.
- **Drift coverage.** `tests/test_scaffold_data_in_sync.py` guards seed/source
  drift. A new seed file that is not covered there is a silent drift hole.

**The gate this WU adds validates the EXAMPLE, not a live config.** This repository
is a CLI tool with no deployable components; it will never carry a
`monitoring.yml`. A gate pointed at a live config would fail permanently on an
absent file or pass vacuously forever. Pointed at `.specfuse/monitoring.yml.example`
it has real signal: the shipped example cannot silently drift from the validator.
This is PLAN.md's satisfiability answer; do not "improve" the gate by repointing it.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `verification-discipline.md`) apply. Do not restate them.

**Acceptance criteria.**

1. `tests/test_monitoring_seed.py::test_example_is_seeded_by_init` exists and
   **fails on HEAD before this WU's edits**. It runs the scaffold init path into a
   temporary directory and asserts `.specfuse/monitoring.yml.example` is present in
   the written relpaths.
2. After this WU's edits that test passes, and so does
   `tests/test_monitoring_seed.py::test_example_is_not_renamed_on_init` — asserting
   the seeded tree contains `monitoring.yml.example` and does **not** contain a
   `monitoring.yml`. Monitoring is opt-in; this test is the guard on that decision.
3. `.specfuse/scripts/lint_monitoring.py` exists, follows the `lint_plan.py` shim
   pattern, and holds no validation logic of its own:
   `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example`
   exits 0.
4. A `code` gate named `monitoring-example-lint` is added to
   `.specfuse/verification.yml`, invoking the shim against
   `.specfuse/monitoring.yml.example`, with a comment stating why it targets the
   example rather than a live config. Running the gate command directly exits 0.
5. `.specfuse/verification.yml.example` carries the same gate **commented out**,
   pointed at the target project's own `.specfuse/monitoring.yml`, with a one-line
   comment saying to uncomment it after running `/derive-monitoring`. A test asserts
   the line is present and is commented — an uncommented gate would fail every
   freshly-scaffolded project on day one.
6. `tests/test_scaffold_data_in_sync.py` covers the new seed file, so a future edit
   to the example that is not propagated to the packaged seed fails the suite.
7. The shim resolves the package from source without a pip install — the same
   property `lint_plan.py`'s shim has. A test invokes the shim as a subprocess from
   a clean working directory and asserts exit 0, declaring `check=` explicitly
   (`PLW1510`, enforced since FEAT-2026-0037).
8. Nothing in this WU changes the pass/fail behavior of an existing gate. A
   sanity assertion: the full `code` set passes both before and after, with the new
   gate the only addition.

**Do not touch.** `specfuse/loop/lint_monitoring.py` (T01 owns the validator — this
WU wires it, it does not change its behavior); `.specfuse/monitoring.yml.example`'s
content (T02 owns it — if it fails the new gate, that is a real defect to escalate,
not to patch here); `_SEED_RENAME`'s existing entries; `.git/`, secrets. The driver
owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — tests, `ruff`,
`bandit`, coverage ≥ 90%, `leak-scan`, and the bats suites — plus the newly added
`monitoring-example-lint` gate itself, which from this WU onward is part of the set
the driver runs against this feature's own remaining work units. Note the
self-hosting consequence: if the new gate misfires, it blocks this feature's
closing sequence. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if seeding `monitoring.yml.example`
cannot be done without adding a `_SEED_RENAME` entry — auto-creating a live
`monitoring.yml` in every scaffolded project is explicitly out of scope and needs a
human decision, not a workaround. Also block if the shipped example fails the new
gate: that is a T01/T02 contract disagreement surfacing late, and the fix belongs
in whichever of those WUs is wrong, not in a gate loosened to accommodate it.
Finally, block if adding the gate changes the outcome of any existing gate — a new
gate must be additive. If `.specfuse/scripts/lint_monitoring.py` is absent from the
files you edited, emit `status: blocked` — do not claim complete. Blocked is
respectable (`result-contract.md` rule 4).
