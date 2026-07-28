---
id: FEAT-2026-0040/T11
type: implementation
status: draft
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/loop/data/workflows/specfuse-monitor.yml
  - specfuse/monitor/cli.py
  - tests/test_monitor_runner_surfaces.py
  - docs/concepts/monitoring-runners.md
model: sonnet
effort: medium
gate_set: code
---

# Where the cycle runs — the local and GitHub Actions runner surfaces

**Objective.** Ship the two runner surfaces `PLAN.md`'s scope boundary names: the
**local** runner (an operator or a cron entry invoking `specfuse-monitor run`) and
the **GitHub Actions** workflow surface (a shipped, scheduled workflow that runs the
same cycle in CI), plus the `runner` dial that says which one a component belongs to.

**Context.** Correlation ID `FEAT-2026-0040/T11`. Gate 3, depends on `T10` — there is
no point shipping a surface that runs a cycle before the cycle exists. The schema
already carries the dial: `.specfuse/monitoring.yml.example` documents
`runner — where diagnosis/autofix executes for this component. one of: local |
gh-actions | in-cluster`, and advises starting every component at `runner: local`.
**`in-cluster` is FEAT-2026-0043's** and explicitly out of scope here
(`PLAN.md`); this unit ships two of the three and must say so where a reader would
otherwise assume all three.

**Existing-mechanism search for this surface — `no existing mechanism, building
new`** (`planning-discipline.md` §1). Commands and verdict:

- `ls .github/workflows` → `ci.yml`, `leak-scan-content.yml`, `release.yml`. All
  three are this repository's own gates; none runs a monitoring cycle and none is a
  template for a consumer project.
- `grep -rn "workflows" --include='*.sh' --include='*.py' scripts/ specfuse/loop/*.py`
  → no match. **The scaffold ships no workflow to target projects today**, and
  `specfuse/loop/data/` has no `workflows/` directory. So the shipping mechanism is
  new, and its first question — where the file lands in a consumer repo, and whether
  the scaffold copies it or the operator does — is a real decision this unit makes
  rather than inherits.

**The dial is a routing decision, not a feature flag.** `runner` says *where a
component's cycle executes*; it does not gate code paths inside the cycle, which is
why this unit carries no flag-scope table and `T10`'s covers the one flag gate 3
introduces. What the dial must do is be **honoured and visible**: a run on one
surface reports which components it handled and, just as importantly, which it
skipped because they belong to another surface. A component silently handled by
nobody is the failure this criterion set exists to prevent — it looks exactly like a
healthy component.

**The workflow is a template that ships, not a workflow that runs here.** This
repository "is a CLI tool with no deployable components and will never carry a real
monitoring.yml" (`verification.yml`). Installing the shipped workflow *into this
repo's* `.github/workflows/` would schedule a monitoring run with nothing to
monitor, against a config that does not exist, and would make this repo's CI the
oracle for a file meant for consumers. The template ships under
`specfuse/loop/data/`, where the scaffold's other seed files live, and is asserted
structurally.

**Secrets are referenced, never embedded.** The workflow needs a token to file
issues and environment credentials to read telemetry. Every one is a
`${{ secrets.NAME }}` / environment-variable reference, matching the schema's own
posture — `monitoring.yml.example`: *"every credential-bearing value below is an
ENVIRONMENT-VARIABLE NAME … never a literal secret."* See `security-boundaries.md`.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**In-loop evidence — this unit's GitHub Actions half produces none.**
`[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]` records `gh` returning auth errors inside
`claude -p`, and a scheduled workflow cannot be executed from a work-unit session at
all. The split is explicit:

- **In-loop and real:** the local runner path (criteria 2, 3, 4), the dial's routing
  and skip reporting, and the *structural* properties of the shipped workflow —
  it parses as YAML, declares a schedule and a manual trigger, invokes
  `specfuse-monitor run`, names its secrets by reference, and requests the minimum
  permissions. These are assertions about a file in this tree and are decidable here.
- **Out of loop, deferred criterion D-11, carried into `G3-CLOSE`:** *"The shipped
  workflow, installed in a consumer repository, completes a scheduled run and files
  the findings."* No test in this unit may claim it. **Verification proxy: an
  operator-journal artifact** — the operator installs the template in a scratch
  repository, triggers it manually, and records the run URL, its outcome, and the
  resulting issue list in the feature folder's operator journal. `G3-CLOSE` cites
  that record. A green structural suite is not evidence for D-11 and must not be
  reported as such.

**Acceptance criteria.**

1. `tests/test_monitor_runner_surfaces.py::TestRunnerDial::test_components_for_another_runner_are_skipped_and_reported`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. **The dial routes.** `specfuse-monitor run` gains a way to declare which surface
   it is running as (a flag, defaulting to `local`), and enumerates only the
   components whose `runner` matches. A fixture config with one `local` and one
   `gh-actions` component yields, on a local run, findings from the first only.
3. **Skipped components are reported, not silent.** The same run's summary names
   each skipped component and the surface it belongs to. **Negative observation:**
   a component whose `runner` is `in-cluster` — valid in the schema, unimplemented
   here — is reported as unhandled-by-design with FEAT-2026-0043 named, and is
   **not** silently dropped and **not** an error that fails the run.
4. **An unknown `runner` value is an error naming the value and the supported set**,
   not a skip. A typo'd dial that silently monitors nothing is the same failure as
   criterion 3's, arriving by a different route.
5. `specfuse/loop/data/workflows/specfuse-monitor.yml` exists and parses: a test
   loads it with the project's YAML reader and asserts it is a mapping with `on` and
   `jobs` keys. A template that ships broken is discovered by the consumer, which is
   the worst place to discover it.
6. **The workflow declares both a schedule and a manual trigger.** `on.schedule`
   carries a cron expression and `on.workflow_dispatch` is present — a monitoring
   workflow nobody can trigger by hand cannot be debugged.
7. **It invokes the real entry point.** A step's `run` contains
   `specfuse-monitor run`, and the installed-package invocation matches the entry
   point `T10` added to `pyproject.toml`. Asserted against that file, not
   hand-copied, so a rename breaks the test rather than the consumer.
8. **Least privilege, asserted.** The workflow declares an explicit `permissions:`
   block granting `issues: write` and `contents: read` and **nothing more**. A test
   asserts the exact key set; a workflow that inherits default write-all permissions
   to file an issue is a security regression shipped as a convenience.
9. **No literal secret, anywhere.** **Negative observation:** every
   credential-bearing value in the template is a `${{ secrets.* }}` or
   `${{ vars.* }}` reference or an environment-variable name; a test greps the file
   for an inline value shape and finds none, and `leak-scan` passes over it. Use
   obvious placeholder names, not real ones (see `security-boundaries.md`; the
   `leak-scan` pre-commit form is stricter than its CI form).
10. **It ships as a template and is not installed here.** The file lives under
    `specfuse/loop/data/`, and `ls .github/workflows` still shows exactly
    `ci.yml`, `leak-scan-content.yml`, and `release.yml` after this WU. A test
    asserts the template is not present in this repository's own workflow directory.
11. **`docs/concepts/monitoring-runners.md` documents both surfaces**: what the
    `runner` dial means, how to install the template in a consumer repository, which
    secrets it needs and why, and — stated plainly rather than left to be inferred —
    that `in-cluster` is FEAT-2026-0043 and unimplemented, and that the local surface
    is the recommended starting point per the schema's own advice.
12. `python3 -m unittest tests.test_monitor_runner_surfaces -v` exits zero after
    this WU's edits, `python3 -m unittest tests.test_monitor_cli` still exits zero,
    and the `code` gate set passes in full — `tests`, `lint`, `security`,
    `coverage` (≥90%), `leak-scan`, `monitoring-example-lint`, and the `bats`
    suites. If a packaging test asserts the contents of `specfuse/loop/data/`,
    it is updated in the same WU rather than left red.

**Do not touch.** This repository's own `.github/workflows/` — criterion 10 asserts
it is unchanged; installing the template here would schedule a monitoring run
against a config that will never exist. Everything under `specfuse/monitor/` except
`cli.py` — gates 1–3 own those modules and this unit composes them.
`specfuse/loop/lint_monitoring.py` and both `monitoring.yml.example` copies — the
`runner` dial is already in the schema and needs no change; if it does, that is an
escalation. `specfuse/loop/escalation.py`. Generated directories, secrets, `.git/`.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, in declared
order. Plus the scoped red/green run in criteria 1 and 12 and the negative
observations in criteria 3, 4, 9, and 10 — `verification-discipline.md` §3 requires
a rule be observed rejecting a purpose-built bad input, and criteria 3 and 4 are the
two ways a component ends up monitored by nobody. Note the `bats` `mktemp` sandbox
effect recorded in `[FEAT-2026-0072/G1-CLOSE]`: report which sandbox each gate ran
under rather than reporting a manufactured regression. **Report the D-11 deferral
explicitly in the RESULT block** — the workflow is asserted structurally and has
never executed.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
`runner` dial cannot be honoured without a schema change, which is a cross-gate
contract question; shipping the template under `specfuse/loop/data/` breaks the
packaging gates in a way that needs a `pyproject.toml` package-data change beyond
adding the path — that is a distribution decision worth a human's eye; the least-privilege
permission set in criterion 8 turns out to be insufficient for the issue lifecycle
`T09` builds, which is a real finding about the surface and not a reason to widen
the grant quietly; or criterion 10's assertion cannot be written because a packaging
test already copies `data/` contents into this repo's workflow directory.
