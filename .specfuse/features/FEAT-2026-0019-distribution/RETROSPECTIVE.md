# Retrospective — FEAT-2026-0019 (Distribution)

## Gate 1 — Repackage: pip-installable driver, package as single source

Completed **interactively** (operator + Claude in a live session), not via the loop
driver. The autonomous run was abandoned mid-gate; see "What the loop did NOT verify"
and the lesson below.

### T01 — Extract the `specfuse.loop` namespace package
Landed autonomously (commit `f834420`). Created `specfuse/loop/` (PEP 420 namespace,
8 modules + `__init__`), console scripts `specfuse-loop`/`specfuse-lint`, editable
install. **Surprise:** T01 *copied* the modules into the package but left the full
originals in `.specfuse/scripts/` — a two-source duplicate, not the intended
move-to-canonical. T02/T03 reconciled it.

### T02 — Vendored shims  ·  T03 — test/coverage/gate migration
Completed interactively in one atomic change (commit `25cb7e1`). The two WUs are not
independently verifiable — see lesson. Delivered: `.specfuse/scripts/*.py` reduced to
shims that path-insert the repo root and re-export `specfuse.loop.<module>`;
`_loop_loader` and `test_validate_event` import the package directly; coverage source
moved to `specfuse/`. The path-insert is the load-bearing fix: it makes the vendored
scripts resolve the package from source even when the running interpreter lacks the
editable install — which is exactly what broke the autonomous run.

## Cost analysis

Planned substantive (PLAN.md): T01 $2.50 + T02 $1.50 + T03 $2.00 = **$6.00**.

Actual: the autonomous loop burned **$5.63 on a single failed T02 attempt** (2930s,
`failure_class: tests`, signature `ModuleNotFoundError: No module named 'specfuse'`,
9 test failures + coverage fail) before the operator stopped it. T01's autonomous cost
is not in this feature's `events.jsonl` (it ran in an earlier driver session). T02+T03
were then completed interactively (cost folded into the live session, not per-WU
tracked). Net: the per-WU autonomous approach spent ~$5.63 producing zero passing work
on this gate; the interactive redo landed all gates green in one pass.

Variance note (>50%): the failed attempt's $5.63 against T02's $1.50 plan is a 3.8×
overrun on a *failed* attempt — the signature of a WU whose oracle could not pass by
construction, not of underestimation.

## What the loop did NOT verify

The autonomous loop verified **nothing on this gate** — its one T02 attempt failed and
the gate was abandoned. Everything was instead verified in the interactive session
against the real gate set: 808 tests, ruff, bandit (exit 0), coverage 93%
(`--source=specfuse`), plus dogfood dry-run, `from loop import` back-compat, and a
PYTHONPATH-cleared shim run (path-insert robustness). Two items remain genuinely
out-of-loop and deferred to later gates:

- **Offline / no-pip vendored generation** — `init.sh` does not yet generate real
  vendored code (vs shims) for consumers without PyPI access. Deferred (gate 2+),
  flagged in WU-02's scope boundary.
- **Real consumer-repo install** — `pip install specfuse-loop` from a published wheel
  is gate 2 (Publish); only the editable `-e .` path is exercised here.

## What I'd change

This gate should not have been authored as three loop-dispatched WUs. See the lesson;
promoted to LEARNINGS.

## Lesson (promoted to LEARNINGS.md)

A feature that migrates the verification harness the driver uses to gate itself cannot
be split into separately-gated WUs: each WU's oracle is the very thing mid-migration,
so no WU passes alone. Author such features as a single atomic change (or run them
interactively), not as a per-WU loop sequence.

## Gate 2 — Publish

Completed interactively (commit `f4f1d02`). Delivered the tag-triggered `release.yml`
(build → test-against-artifact → OIDC publish), the `check_scaffold_version()` startup
guard + `.specfuse/VERSION` stamping via init.sh, and scoped the wheel to `specfuse*`.

Surprise: setuptools auto-discovery swept `tests/`, `docs/`, `scripts/` into the first
wheel — `packages.find` had to be scoped to `specfuse*`. Caught by inspecting the
built wheel's top-level, not by any test; `release.yml`'s artifact step is the
standing guard.

### Cost analysis
Gate authored interactively (cost folded into the live session, not per-WU tracked).
No autonomous dispatch, so no per-WU `planned_cost_usd` reconciliation applies.

### What the loop did NOT verify
- **Real PyPI publish** — only OIDC-trusted-publishing *wiring* is in `release.yml`;
  the actual publish needs the operator to configure the trusted publisher on
  pypi.org for `specfuse-loop` and push a `v*` tag.
- **The wheel build in CI** — built and inspected once locally (sandbox-off); the
  standing verification is `release.yml`'s build+install+test job on tag. Local
  rebuild needs network and was deferred.

## Gate 3 — Plugin

Completed interactively. Created the separate **`specfuse/specfuse`** umbrella repo
(public, Apache-2.0) as a Claude Code marketplace + the `specfuse` plugin shipping
the 18 gate-cycle skills (namespaced `/specfuse:`). Loop-side change: quoted all
skill `description:` frontmatter (commit `dfee510`).

Surprise: `claude plugin validate` (strict JS YAML parser) rejected skills whose
unquoted `description` contained a `: ` — Claude Code's lenient skill loader had
accepted them all along, so the bug was invisible until the plugin context. Caught
by the validator, not by any loop test. Fix: quote every description as a JSON
double-quoted YAML scalar.

Decisions refining roadmap Part B: dropped the "caveman hooks → plugin hooks.json"
line (caveman is external/personal; the public plugin ships skills only), and
hard-cut to `/specfuse:` with no back-compat aliases (no external consumers of the
bare names yet).

### Cost analysis
Interactive; cost folded into the live session. No autonomous dispatch.

### What the loop did NOT verify
- **Live marketplace install** — validator passes; actually adding the marketplace
  + installing in a fresh Claude Code session is an operator step.
- **Dogfood cutover + skill sync** — this repo still uses `.claude/skills/` symlinks;
  cutover to the published plugin, retiring the symlinks, and a `.specfuse/skills/`
  → plugin sync step are gate 4 (with init.sh deprecation).

## Gate 4 — Bridge + deprecate (terminal)

Completed interactively. The `specfuse` umbrella CLI (option a) landed in the
specfuse/specfuse repo: a PEP 420 namespace contributor (`specfuse.cli`, no
`specfuse/__init__.py`) that composes with the driver's `specfuse.loop`; console
script `specfuse` with `upgrade` (pip-upgrade + point at `/plugin update`) and `init`
(ensure driver + print bootstrap). Loop side: init.sh deprecation banner (v1.0;
removed v1.1), `scripts/sync-skills.sh` (canonical skills → plugin, addressing the
gate-3 drift defer), and README pip/plugin forward-path docs.

Surprise: the umbrella's `specfuse init` cannot fully scaffold a new repo from pip —
templates/rules still live in init.sh, not in package data. The bridge owns pip ↔
plugin; pip-native scaffold-data delivery is a follow-up feature.

Also: the CLI's pip `runner` was first bound as a default arg (`runner=subprocess.run`),
which `mock.patch` couldn't override (default captured at def-time) — a real pip call
fired in a test. Fixed by resolving the runner inside the function.

### Cost analysis
Interactive across gates 1–4; per-WU costs not tracked (only the abandoned gate-1
autonomous T02 attempt, ~$5.63, is in events.jsonl). The interactive path delivered
all four gates green where the per-WU loop dispatch could not pass gate 1 at all.

### What the loop did NOT verify (terminal)
- **Actual PyPI publish** of `specfuse-loop` and `specfuse` — operator configures the
  trusted publisher + pushes the `v*` tags; `release.yml` runs the publish.
- **Live marketplace install** — `/plugin marketplace add specfuse/specfuse` + install
  in a fresh Claude Code session (validator passes; live run is operator-side).
- **pip-native `specfuse init`** scaffolding (templates/rules as package data) —
  deferred to a follow-up feature; until then init.sh is the scaffold bootstrap.
- **Dogfood cutover** — this repo still uses `.claude/skills/` symlinks; retiring them
  for the published plugin is operator-side once the plugin is installed.

## Terminal verdict — verdict: met

The feature's goal — a PyPI-installable driver + a Claude Code plugin marketplace,
replacing the curl-bash/symlink install — is delivered and verified to the limit of
what the loop can verify: `specfuse.loop` package + console scripts (gate 1), tag-
triggered OIDC release pipeline + version-skew guard (gate 2), `specfuse/specfuse`
marketplace + plugin validated (gate 3), `specfuse` umbrella CLI + init.sh
deprecation + skill-sync (gate 4). The remaining steps are external/operator-owned
(PyPI publish, live plugin install) or an explicitly-scoped follow-up (pip-native
scaffolding). Recommend a follow-up feature: **scaffold-data in the pip package** so
`specfuse init` fully replaces init.sh (enabling its v1.1 deletion).
