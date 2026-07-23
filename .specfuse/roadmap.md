---
project: specfuse-loop
---

# Roadmap

The master plan for this repository's own work. Each feature lives in its
own folder under `.specfuse/features/` once started, with a `PLAN.md` (task
graph), `GATE-NN.md` files, and `WU-*.md` files. This roadmap owns *feature*
definitions and *feature* status; the PLAN owns the *graph*; GATE files own
*gate* status; WU files own *work-unit* status. One fact, one home — the
same split the Specfuse Orchestrator uses.

`FEAT-2026-0001` is reserved as the **bundled worked-example fixture** under
`.specfuse/features/FEAT-2026-0001-health-endpoint/`. It is not on this
repo's planned work; it ships as the self-demonstrating reference
installation a target project copies via `init.sh`.

| Feature ID     | Title                                       | Status   | Folder | Detail |
|----------------|---------------------------------------------|----------|--------|--------|
| FEAT-2026-0002 | Driver run-loop test coverage               | done     | `.specfuse/features/FEAT-2026-0002-driver-test-coverage/` | [→ archive](roadmap-archive.md#feat-2026-0002) |
| FEAT-2026-0003 | GitHub feature-pick for the loop            | done     | `.specfuse/features/FEAT-2026-0003-github-feature-pick/` | [→ archive](roadmap-archive.md#feat-2026-0003) |
| FEAT-2026-0004 | Single-driver working-tree lock             | done     | `.specfuse/features/FEAT-2026-0004-driver-lock/` | [→ archive](roadmap-archive.md#feat-2026-0004) |
| FEAT-2026-0005 | Combined close for single-gate features     | done     | `.specfuse/features/FEAT-2026-0005-combined-close/` | [→ archive](roadmap-archive.md#feat-2026-0005) |
| FEAT-2026-0006 | WU execution-time tracking                  | done     | `.specfuse/features/FEAT-2026-0006-wu-duration/` | [→ archive](roadmap-archive.md#feat-2026-0006) |
| FEAT-2026-0007 | Dispatch cost controls                      | done     | `.specfuse/features/FEAT-2026-0007-dispatch-cost-controls/` | [→ archive](roadmap-archive.md#feat-2026-0007) |
| FEAT-2026-0008 | Driver completeness-guard                   | done     | `.specfuse/features/FEAT-2026-0008-driver-completeness-guard/` | [→ archive](roadmap-archive.md#feat-2026-0008) |
| FEAT-2026-0010 | Roadmap restructure: add + archive          | done     | `.specfuse/features/FEAT-2026-0010-roadmap-restructure/` | [→ archive](roadmap-archive.md#feat-2026-0010) |
| FEAT-2026-0011 | Scoring framework for roadmap features      | blocked  | `.specfuse/features/FEAT-2026-0011-scoring-framework/` | — |
| FEAT-2026-0012 | Closing-WU deliverable guard (folded into 0015) | abandoned | — | [→ archive](roadmap-archive.md#feat-2026-0012) |
| FEAT-2026-0013 | CI integration_workspace cleanup race fix   | done     | `.specfuse/features/FEAT-2026-0013-ci-workspace-race-fix/` | [→ archive](roadmap-archive.md#feat-2026-0013) |
| FEAT-2026-0014 | GitHub Actions Node.js 20 deprecation bump  | done     | `.specfuse/features/FEAT-2026-0014-gha-node20-bump/` | [→ archive](roadmap-archive.md#feat-2026-0014) |
| FEAT-2026-0015 | Closing-ceremony restructure + hollow-pass guard | done     | `.specfuse/features/FEAT-2026-0015-closing-ceremony-restructure/` | [→ archive](roadmap-archive.md#feat-2026-0015) |
| FEAT-2026-0016 | Per-attempt outcome events + re-arm contract + audit trail | done     | `.specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/` | [→ archive](roadmap-archive.md#feat-2026-0016) |
| FEAT-2026-0017 | Close-WU wiring-race guard                  | done     | `.specfuse/features/FEAT-2026-0017-wiring-race-guard/` | [→ archive](roadmap-archive.md#feat-2026-0017) |
| FEAT-2026-0018 | Deterministic gate-close predicate + auto-close path | done     | `.specfuse/features/FEAT-2026-0018-auto-close-predicate/` | — |
| FEAT-2026-0019 | Distribution: PyPi-installable driver + Claude Code plugin marketplace | done | — | — |
| FEAT-2026-0020 | Public-readiness prep: secrets audit + OSS hygiene before visibility flip | done | `.specfuse/features/FEAT-2026-0020-public-readiness-prep/` | — |
| FEAT-2026-0021 | Ceremony proportionality + slim WU template | done | `.specfuse/features/FEAT-2026-0021-ceremony-proportionality/` | [→ archive](roadmap-archive.md#feat-2026-0021) |
| FEAT-2026-0022 | Deliverable-presence gate: machine-enforce per-WU `produces:` + empty-files escalation | done | `.specfuse/features/FEAT-2026-0022-deliverable-presence-gate/` | [→ archive](roadmap-archive.md#feat-2026-0022) |
| FEAT-2026-0023 | Lifecycle integration test + consolidate terminal-state ownership | done | `.specfuse/features/FEAT-2026-0023-lifecycle-integration-test/` | [→ archive](roadmap-archive.md#feat-2026-0023) |
| FEAT-2026-0024 | Hashed denylist + issue/PR-body leak guard | done | `.specfuse/features/FEAT-2026-0024-hashed-denylist-leak-guard/` | [→ archive](roadmap-archive.md#feat-2026-0024) |
| FEAT-2026-0025 | LEARNINGS curation + archival (bound planning-context growth) | done | — | [→ archive](roadmap-archive.md#feat-2026-0025) |
| FEAT-2026-0026 | Scaffold-data in the pip package: `specfuse init` replaces init.sh | done | — | [→ archive](roadmap-archive.md#feat-2026-0026) |
| FEAT-2026-0027 | Self-provisioning driver: auto-sync `.specfuse/` + plugin config on run | done | — | — |
| FEAT-2026-0028 | Umbrella CLI → scaffold-API wiring + docs in the pip seed | done | — | — |
| FEAT-2026-0029 | One-command Specfuse scaffold upgrade skill | done | — | [→ archive](roadmap-archive.md#feat-2026-0029) |
| FEAT-2026-0030 | Driver-side sanitization of agent-authored text before events.jsonl staging | done | — | [→ archive](roadmap-archive.md#feat-2026-0030) |
| FEAT-2026-0031 | Configurable integration branch | done | — | [→ archive](roadmap-archive.md#feat-2026-0031) |
| FEAT-2026-0032 | Non-WSL Windows execution (native driver + Git-Bash) | done | `.specfuse/features/FEAT-2026-0032-windows-native/` | [→ archive](roadmap-archive.md#feat-2026-0032) |
| FEAT-2026-0033 | Sub-repo component scoping: multiple components in one repo | deferred | — | — |
| FEAT-2026-0034 | Roadmap-table lint: enforce blocked features carry a resolvable Blocked-by link | planned | — | — |

Status: `planned` → `active` → `done` (or `abandoned`). `deferred` = parked
by choice pending an external decision/dependency; resumable (a human flips it
back to `active` when the blocker clears), distinct from `abandoned` (dead).
`blocked` = cannot proceed because a *named* dependency is unmet — an ADR
awaiting approval, or an upstream feature that must complete first. Resumable
like `deferred`, but where `deferred` is a voluntary park with no named blocker,
`blocked` always names its blocker so the roadmap shows what it waits on and
links to it.

A `blocked` feature's detail section carries a `**Blocked by.**` block — blank
line above it, one linked blocker per clause:

**Blocked by.** [ADR-0007: event-schema versioning](../docs/adr/0007-event-schema-versioning.md) — awaiting approval; [FEAT-2026-0011](#feat-2026-0011) — scoring data must land first.

Each blocker is a Markdown link: an ADR points at its `.md` file (kept under
`docs/adr/` by convention, so from `.specfuse/roadmap.md` the link is
`../docs/adr/…`); a feature dependency points at the blocking
feature's roadmap anchor (`#feat-yyyy-nnnn`). When every blocker clears, a human
flips `blocked` → `active` (or `planned`) and removes the `**Blocked by.**` block.

<a id="feat-2026-0011"></a>
## FEAT-2026-0011 — Scoring framework for roadmap features

**Why.** Today the roadmap has no scoring signal — `pick-feature`
ranks by recency and gut feel. Christian's "Feature Prioritization
Guidelines" methodology defines an objective formula
(`(WCI×CI) + (WBV×BV) + (WTF×TF) − (WCOI×COI) − (WR×R)`, normalized
to 0–100) that decouples stable per-feature criteria (objective,
data-backed) from time-varying weights (quarterly strategic
objectives). The methodology has been written down once; it needs
to land as a reusable Specfuse component so every repo (and
ultimately the orchestrator) inherits the same prioritization
discipline.

**Goal.** Land the scoring stack as a set of artifacts + skills.

Artifacts:

- `.specfuse/scoring-criteria.md` per repo, with stable definitions
  of what each criterion (CI/BV/TF/COI/R) MEANS for the project,
  including project-specific sub-criteria (e.g. specfuse-loop's
  CI = "methodology user impact: reduce operator interrupts,
  shorten WU spin time, lower per-feature cost"). Carries a
  `revision:` field and a `## Revision log` for audited evolution.
- `.specfuse/priorities/YYYY-QN.yml` per quarter, carrying the
  current period's strategic objective + the five weights. Latest
  file by name is active; history preserved by never overwriting.
- Per-feature scoring data lives in the roadmap detail section as
  a YAML block (not in the table row). Table row carries only
  `ID | Title | Status | Budget`. Score is rendered, never
  stored.
- `.specfuse/roadmap-ranked.md`, auto-regenerated, git-tracked, the
  always-current rendered view of priorities. Header includes the
  period, weights, and timestamp used to compute it.
- Audit lives in-detail as a `## Estimate revisions` subsection in
  each feature's roadmap entry, travels with the feature into the
  archive on completion.

Skills:

- `define-scoring-criteria` — bootstrap + `--revise` the per-repo
  criteria file. Reads CLAUDE.md, roadmap, LEARNINGS; asks "who are
  your customers", "what's strategic for this product", "what does
  drift risk mean here"; drafts the file, asks user to confirm.
- `set-priorities` — write the current quarter's weights file. On
  each call, snapshots the active period and starts a new one if
  the quarter rolled over.
- `roadmap-estimate` — fill CI/BV/TF/R + Budget bucket for a
  feature. Reads scoring-criteria.md as ground truth for the
  rubric. COI derived from Budget bucket via fixed mapping
  (`<$5 → 1, $5-25 → 4, $25-100 → 7, >$100 → 10`). Wires
  events.jsonl telemetry (actual cost / attempts / escalations
  across past features) as a grounding aid. For `active`
  features, `--reason` is mandatory; revision is appended to the
  feature's `## Estimate revisions` subsection.
- `roadmap-rank` — compute Feature Score per current weights
  using the methodology's formula + normalization. Two modes:
  stdout (interactive ranked view), or `--snapshot` (write
  `.specfuse/roadmap-ranked.md`). Active features and planned
  features ranked in separate sections.

Wiring:

- `pick-feature` updated to read `roadmap-ranked.md` (or call
  `roadmap-rank` if the snapshot is stale).
- `set-priorities` / `roadmap-estimate` / `roadmap-add` /
  `roadmap-archive` each call `roadmap-rank --snapshot` as their
  final step so the rendered ranking never goes stale.
- `init.sh` ships templates for `scoring-criteria.md` and a starter
  `priorities/<current-quarter>.yml`.
- Bootstrap specfuse-loop's OWN `scoring-criteria.md` and an
  initial `priorities/<current-quarter>.yml` as part of this
  feature (eats its own dog food).

**Benefits.** Objective prioritization across the backlog. Decoupled
"what does this feature offer" (stable) from "what are we chasing
this quarter" (time-varying). Reproducible scoring across repos and,
later, across the orchestrator's component repos. Audit trail when
estimates change. Foundation for the orchestrator to aggregate
features across component repos under one product-level weight set.

**Verification.** Compute Feature Scores for FEAT-2026-0010 and a
backfilled set of past features; manually validate the ranking
matches Christian's intuitive ordering for at least one historical
quarter. `roadmap-estimate` blocks re-rating `active` features
without `--reason`. `roadmap-rank --snapshot` regenerates a
deterministic file given the same inputs. `scoring-criteria.md`
revision flow lets a user change the rubric without losing prior
estimates' grounding (revision log captures the change).

**Blocked by.** [ADR-0002: ratify the roadmap feature-scoring model](../docs/adr/0002-ratify-roadmap-feature-scoring-model.md) — Proposed; the scoring formula + criteria schema must be accepted before the artifacts are built, or estimates captured under a later-changed rubric are invalidated.

**Status: blocked.** Design dependency ADR-0002 is unaccepted; build is held
until it lands. (FEAT-2026-0010, the earlier prerequisite, is `done`.) Clear with
`/block-feature FEAT-2026-0011 --unblock` once ADR-0002 is Accepted.

## Verdict-state ↔ PLAN.md coupling

Today the close ceremony flips PLAN.md `done` regardless of verdict
hedging. FEAT-2026-0013 v1 close emitted **"Met locally;
field-confirmation pending operator action"** AND flipped PLAN.md to
done — then CI failed and the operator had to reverse-flip 4 surfaces
to re-arm.

New rule (driver-enforced):

- Verdict **"Met"** → close MAY flip PLAN.md `done`, gate `passed`,
  roadmap row `done`.
- Verdict **"Met locally / field-pending"**, **"Partially met"**, or
  any qualified form → close MAY NOT flip PLAN.md done. PLAN.md
  stays `active`. Gate stays `awaiting_review`. RETROSPECTIVE
  records the hedge + the operator-side oracle that must run before
  the verdict can upgrade.
- Verdict **"Not met"** → close emits `status: blocked` per
  result-contract; no flips.

Implementation:

- Close WU spec requires a frontmatter field `verdict: met |
  met_locally | partially_met | not_met` written before the
  PLAN.md-flip step.
- Driver reads the field; only `verdict: met` permits the terminal
  flips. Other values keep state in close-pending limbo until
  operator confirms field-side oracle (typically via `/wrap-feature`
  step 4 or a dedicated `/confirm-verdict` skill, future).
- The recursive close audit (FEAT-2026-0008 pattern) runs on the
  guard itself: this feature's own close MUST exercise the verdict-
  coupling check.

## Oracle environment-parity declaration

LEARNINGS `[FEAT-2026-0013/G1-CLOSE/oracle-environment]` already
states the durable rule but does not enforce it. New WU contract:

- Every Acceptance Criterion that uses a verifying oracle (test loop,
  audit, lint, recursive-50× pattern, etc.) MUST declare the
  environment the oracle runs in: `oracle_env: macos_local |
  linux_docker | github_actions_ci | <named>`.
- Close ceremony refuses `verdict: met` if any load-bearing AC's
  declared `oracle_env` does not match the goal's target
  environment. FEAT-2026-0013's `roadmap_goal` named "Python 3.12 CI
  runners"; a macOS-local oracle would have been rejected at close
  time, forcing the Linux Docker probe before the verdict could
  upgrade.
- Lint check: `lint_plan.py` warns if a WU's ACs name an oracle
  without `oracle_env`. Failing lint blocks dispatch.

## Planned-cost capture + actual-vs-planned comparison

Today there is no convention for capturing a feature-level cost
estimate up front. `/wrap-feature` §2 plan-adherence read
acknowledges the gap ("Cost spent vs initial estimate if one was
recorded"). FEAT-2026-0011 plans a coarse Budget bucket for scoring,
but that's a prioritization input, not a close-time delta baseline.

Capture planned cost at TWO levels — WU and feature:

- **WU frontmatter** `planned_cost_usd: <float>` — per-WU operator
  estimate. THIS is the unit of learning: per-type/per-effort
  variance across features lets us calibrate the heuristic.
- **PLAN.md frontmatter** `planned_cost_usd: <float>` — feature-
  level estimate; SHOULD equal Σ of per-WU planned costs at
  activation time (lint warns on mismatch >10%). Operator
  declares the headline number explicitly so the feature-arc
  verdict can quote it.

Both fields are optional today (warn-only for new features),
mandatory once /draft-feature emits them by default.

Close-WU spec change (folds into the new `close` and
`close-intermediate` types):

- Required `## Cost analysis` section in RETROSPECTIVE.md (or its
  gate-section equivalent). For each WU in scope, quote
  `planned_cost_usd`, compute actual from events.jsonl (sum
  cost_usd across all this WU's attempts including re-arms via
  cumulative fields per FEAT-2026-0016), report delta %. Then
  aggregate to gate total. Then aggregate to feature total
  (terminal close only). Variance > 50% on any unit requires a
  one-paragraph rationale citing the cause (oracle env mismatch,
  scope discovery miss, re-arm cycle, etc.).
- Lint warnings when WU files or PLAN.md are missing
  `planned_cost_usd` for new features (grandfathered for in-flight).
  Same shape as the oracle-env-parity warning above.

**Future analysis path** (out of scope for 0015 — file as 0017
or fold into 0011 scoring):

- Aggregate per-WU `planned_cost_usd` vs actual across ALL
  features. Group by `(type, effort)` pair. Compute mean delta
  per group. Use as a self-calibrating heuristic in /draft-feature
  to seed future estimates. Closes the methodology learning loop.

Recursive dogfood: this feature's PLAN.md AND every WU file MUST
carry `planned_cost_usd` at activation/draft time; close ceremony
exercises the cost-analysis AC against itself.

## State-flip ownership consolidation

Today the closing surfaces are split between close ceremony and
`/wrap-feature`:

| Surface | Owner today | Owner after 0015 |
|---|---|---|
| PLAN.md status | close | close (per verdict-coupling above) |
| Terminal gate status | wrap-feature (cosmetic) | close |
| Roadmap row status | wrap-feature (manual flip) | close |
| Auto-archive call | wrap-feature (manual) OR driver's gate-is-None hook (chicken-and-egg) | close |

Live evidence: FEAT-2026-0010, 0013, 0014 all had `roadmap row = active`
after PLAN.md `done`. /wrap-feature step 1 surfaced the drift every
time. FEAT-2026-0010's auto-archive hook (T05) didn't fire on itself
because gate-is-None requires the gate cosmetic flip, which happens at
wrap. Move ALL terminal flips into close → drift becomes impossible
+ auto-archive fires cleanly on every feature including its own.

/wrap-feature shrinks to: read RETRO recap, push branch, open PR,
merge advisory, next pick. No state flips.

## Subsumed scope (from FEAT-2026-0012)

Hollow-pass guard against the NEW closing-WU taxonomy:

- **`close` (terminal-gate combined)** → guard asserts ALL of:
  RETROSPECTIVE.md exists + non-empty; LEARNINGS.md shows ≥1 added
  line (or explicit "nothing generalizes" note); some doc/roadmap
  file diff; PLAN.md flipped `done`; roadmap row flipped `done`.
- **`close-intermediate` (multi-gate non-terminal)** → guard asserts:
  RETROSPECTIVE.md section for this gate appended; LEARNINGS.md
  appended OR explicit-no-op acknowledged; doc surface diff if
  declared in spec.
- **`plan-next` (intermediate-gate, unchanged)** → guard asserts:
  GATE-(N+1)-REVIEW.md exists + non-empty; next gate's `work_units`
  drafted in PLAN.md OR PLAN.md `done` OR roadmap row `done`.
- **`implementation`** → unchanged; FEAT-2026-0008's three guards
  already cover.

Driver-side: in `loop.py::run()`, between successful verify+squash
and the status-flip-to-done, fire the type-keyed assertion. Failure
rolls back via `git reset --hard head_before`, records an
`attempt_outcome` event with `outcome: "closing_deliverable_missing"`
naming the failed assertion, counts as a verification failure in the
attempt loop (3-in-a-row → `blocked_human`).

Recursive close audit (per LEARNINGS `[FEAT-2026-0008/G1-CLOSE]`):
this feature's own close ceremony MUST run the new guard against
itself.

**Status: planned.** Single feature replacing 0012 and (originally
proposed) 0015. Detail the first gate's WUs when ready to start.
Likely shape: one substantive WU to ship the new WU types +
templates + lint, one substantive WU to ship the type-keyed guard
table + tests, then closing ceremony (using the new contract for
recursive dogfood).

## FEAT-2026-0019 — Distribution: PyPi-installable driver + Claude Code plugin marketplace

**Why.** Two distribution gaps, one feature.

1. **Driver + scaffold today** ship via `init.sh` copying
   `.specfuse/scripts/*.py` (`loop.py`, `lint_plan.py`, `_miniyaml.py`,
   `gate_eval.py`) into the consumer repo. Upgrade is `init.sh --upgrade`
   over HTTPS to GitHub. Versioning is "whatever was on `main` at copy
   time" — no `--version`, no compat check between the scaffold copy and
   any related tooling, no way for a consumer to pin to a known-good
   release. Bug fixes (e.g. specfuse/loop#35, the `_miniyaml` crash that
   left two WUs corrupted) require the operator to re-run the bash
   installer in each repo. CI environments can't `pip install specfuse`;
   they shell out to a curl-bash. Drift between the scaffold-copied driver
   and any package-published one is invisible.
2. **Claude assets** (skills, hooks, cavecrew subagents) currently
   distribute via a `.specfuse/skills/` symlink-into-`.claude/skills/`
   trick that the same `init.sh` performs. That doesn't scale to a second
   product (orchestrator), bypasses Claude Code's native plugin precedence
   and hot-reload, and forces every consumer through the bash installer.
   Plugin schema spike confirmed the native path supports hooks,
   subagents, hot reload, project-local override, and headless install —
   green light to migrate.

Both gaps share root cause: bash-installer ownership of state Claude Code
and Python already have first-class delivery channels for. Fix them in
one feature so the migration story is coherent.

**Goal — Part A: PyPi-installable driver.**

- Package name `specfuse` on PyPi. `pyproject.toml` at the repo root with
  `[project.scripts]` entries: `specfuse-loop = specfuse.loop:main` and
  `specfuse-lint = specfuse.lint_plan:main`. (A top-level `specfuse`
  console script gates `init` / `upgrade` / `plugin sync` per Part C.)
- Package layout: `specfuse/` (new top-level dir) ships `loop.py`,
  `lint_plan.py`, `_miniyaml.py`, `gate_eval.py`, plus a `templates/`
  data directory (PLAN / GATE / WU templates currently in
  `.specfuse/templates/`) and a `rules/` data dir (binding rules
  currently in `.specfuse/rules/`) loaded via `importlib.resources`.
  Imports inside the package switch from bare `import _miniyaml` to
  package-relative `from . import _miniyaml`.
- Driver path resolution: `loop.py` keeps its `SPECFUSE_DIR = Path(".specfuse")`
  convention for the per-repo state (features, LEARNINGS, verification.yml,
  roadmap.md) — only the script + template surfaces move into the
  pip package. State stays in the consumer repo; code stops being
  copied into it.
- `.specfuse/scripts/` becomes optional. Two supported configurations:
  - **Pip mode** (recommended): `pip install specfuse` puts
    `specfuse-loop` on PATH; consumer's `.specfuse/scripts/` is empty or
    absent. `specfuse-loop` is invoked directly.
  - **Vendored mode** (current shape, for environments without pip):
    `init.sh` continues copying scripts into `.specfuse/scripts/` for
    repos that need offline / sandboxed execution. The pip path is the
    default; vendored is the carve-out.
- Version compat. The driver carries a `DRIVER_VERSION` constant (already
  present, currently `0.2.0`). A new `MIN_SCAFFOLD_VERSION` field is added
  to the scaffold's `.specfuse/VERSION` (new file shipped by init).
  On startup, the driver compares; mismatch → fail-loud with the fix
  command (`specfuse upgrade <repo>`) in the error.
- CI publish path. GitHub Actions builds the wheel + sdist, runs the full
  test suite, then publishes to PyPi on a tag matching `v[0-9]+.*`.
  Trusted publishing (OIDC) preferred over API tokens.

**Goal — Part B: Claude Code plugin via marketplace.**

Package Specfuse Claude assets as a Claude Code plugin named `specfuse`,
published via marketplace at the `specfuse/specfuse` common repo. Skills
migrate to the `/specfuse:` namespace; caveman hooks move from user
`settings.json` into the plugin's `hooks.json`. `init.sh` ships a
deprecation banner in v1.0 and is deleted in v1.1. Core plugin
extraction (assets shared with orchestrator) deferred until orchestrator
lands.

**Goal — Part C: bridge command.**

Single `specfuse upgrade` CLI command on the pip-installed driver syncs
both surfaces: pulls the latest pip release of `specfuse`, runs the
scaffold's `init.sh --upgrade` equivalent in-process, and tells Claude
Code to `/plugin update specfuse@specfuse`. The bash `init.sh` is
retained for first-time bootstrap (it has to live somewhere before pip
is installed) but its body shrinks to "install pip package, hand off to
`specfuse init`".

**Benefits.**

- **Driver side.** Standard `pip install specfuse` / `pip install -U
  specfuse` upgrade story. Pinable in `requirements.txt` /
  `pyproject.toml` of the consumer repo. CI environments install via
  pip natively (no curl-bash). One source of truth for driver code —
  no drift between scaffold-copied and package-published versions.
  Version skew is detected at startup with a clear fix command, not
  silently masked.
- **Claude side.** Native marketplace install/update (`/plugin install
  specfuse@specfuse` + `/plugin update`), versioned plugin releases with
  hot reload (no session restart), preserved project-local skill
  overrides, offline install via vendored tree, single `specfuse upgrade`
  command bridges pip → plugin, foundation for multi-product
  distribution (orchestrator + future products reuse marketplace),
  elimination of symlink-tree maintenance.

**Risks tracked.**

- Wheel size growth from vendored plugin tree (mitigation: ship the
  plugin as a separate optional dep `specfuse[claude]`; default install
  is driver-only).
- CI dual-publish race (pypi tag + marketplace PR open simultaneously);
  publish sequencing in the release workflow.
- Migration of existing symlink installs — `specfuse init --migrate`
  detects the legacy layout, removes the symlink + scripts-copy, runs
  `pip install`, and posts a one-line summary of what changed.
- Namespace break for current `/arm-gate`-style invocations once skills
  move to `/specfuse:arm-gate`. Provide one release of aliases before
  removing.
- Bootstrap chicken-and-egg: `init.sh` cannot assume pip is present on
  the operator's machine. v1.0's `init.sh` either uses `python3 -m pip`
  with a fallback to "ask operator to install pip and re-run", or
  ships a self-contained `pipx`-style installer.
- Sandboxed / CI environments that can't reach PyPi: vendored mode
  (Part A) is the supported carve-out, not the default.

**Status: done.** Likely 3–4 gates: (1) repackage driver as pip
package + green test suite via `pip install -e .`; (2) GitHub Actions
publish path + first tagged release; (3) Claude Code plugin + marketplace
PR; (4) bridge command + deprecation of `init.sh` v1.0. Each gate
independently shippable.
## FEAT-2026-0020 — Public-readiness prep: secrets audit + OSS hygiene before visibility flip

**Why.** The `specfuse/loop` GitHub repo is currently private. The
FEAT-2026-0019 distribution plan ships a public PyPi wheel whose
contents are public source; that's coherent only if the GitHub repo
also goes public (no privacy is preserved by keeping it private once
the wheel is on PyPi, and Claude Code marketplace Part B of 0019 likely
requires public source anyway). The repo carries an Apache-2.0 license
already, so the legal posture is consistent — but the **hygiene posture
isn't.** A repo whose `main` history was written under a "this is
private" assumption can carry artifacts that shouldn't go public:
accidentally-committed credentials, personal email addresses + machine
paths embedded in commits, in-flight comments not meant for an external
audience, cross-pollinated content from other private repos, missing
contributor-onboarding files. Public-flip + first PyPi tag without
this audit ships a wheel with embarrassing or sensitive content into a
non-takedown-friendly channel.

This feature is the one-shot cleanup that makes `main` publishable, so
0019's first release lands on a public repo whose history is fit for
the audience.

**Goal.** Two gates. Gate 1 produces a green audit; gate 2 lands the
public-facing hygiene files + the visibility-flip checklist.

**Gate 1 — Audit.**

- **Secret scan across full git history** — `gitleaks` or `trufflehog`
  run against every commit on every reachable ref. Every match
  triaged: ignore (false positive), redact (rewrite history with
  `git-filter-repo` / BFG), or rotate (real credential leaked → rotate
  + redact). Acceptance: scan exits clean OR every match has a logged
  triage decision.
- **PR + issue content sweep** — read closed PRs and issues for
  references to internal hostnames, customer names, personal data,
  private-repo paths, or anything else only-makes-sense-internally.
  Triage same way. Recent IaC-agent issues (#23-#28, #35) reviewed
  separately because they're the freshest and most likely to mention
  consumer-side specifics.
- **In-repo personal references** — grep `main` for `/Users/`,
  `@gmail.com` / `@<personal-domain>`, credential filenames, internal
  Slack channel names, internal product code names. Anything found:
  redact in-place if on `main`, or rewrite history if older. Includes
  `.specfuse/LEARNINGS.md`, `CLAUDE.md`, and every commit message on
  `main` (commit-message rewrites require `git-filter-repo`).
- **Cross-pollination check** —
  `.specfuse/features/INIT-2026-0001-F06-conform-exampleEndpoint-to-validated-spec/`
  is filed under specfuse-loop's feature dir but looks like it leaked
  in from `example-org`. Confirm with `git log -- <path>`; if
  it doesn't belong, remove + commit + ensure no in-history secrets.
- **License-header sweep** — every `*.py` / `*.sh` / `*.md` source
  file under `.specfuse/scripts/`, `.specfuse/skills/`,
  `.specfuse/rules/`, `.specfuse/templates/` carries the Apache-2.0
  header. Spot checks already show most do; this is the mechanical
  confirm.
- **Audit report** — `.specfuse/features/FEAT-2026-0020-public-readiness-prep/AUDIT.md`
  enumerates every finding + triage decision + the fix commit hash
  (or "no action — false positive"). This file becomes the gate-1
  RETRO evidence + ships with the repo so the public-facing audit
  trail is honest.

**Gate 2 — Public hygiene + flip-readiness ceremony.**

- `README.md` polish — first-impression rewrite. 60-second pitch
  ("Specfuse Loop is a Specfuse-methodology dogfood: a Python
  driver + Claude Code skills that run features through gates with
  cost-bounded retries"). Quickstart: `pip install specfuse` (once
  0019 lands) or current `init.sh`. Link to the worked-example
  fixture in `.specfuse/features/FEAT-2026-0001-health-endpoint/`.
- `CONTRIBUTING.md` — how external contributors file issues, propose
  PRs, run tests (`python3 -m unittest discover -s tests -t .`), and
  the methodology-dogfood expectation: bug fixes via `/fix-bug`,
  features via `/draft-feature`.
- `SECURITY.md` — vulnerability reporting channel (GitHub Security
  Advisories preferred; email fallback).
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1, no modifications.
- `.github/ISSUE_TEMPLATE/` — three templates: bug report,
  feature request, methodology question. Match the shape of the
  IaC-agent issues (#23-#28) — they're a good worked example of
  what a good bug report looks like.
- `.github/pull_request_template.md` — summary + test-plan checklist,
  matching the shape of PRs #30 / #31 / #32 / #33 / #34 / #36 / #37
  (already converging on this form).
- `.github/dependabot.yml` — actions + pip ecosystems, weekly
  cadence.
- Branch-protection capture — document the current rules in
  `CONTRIBUTING.md`'s "How releases happen" section so a public
  forker can read what's expected.
- Release-tagging convention — `v0.x.0` semver for the loop driver;
  couples to 0019's PyPi tag scheme. Document in `CONTRIBUTING.md`.
- **Flip checklist** — `FLIP-CHECKLIST.md` in the feature folder
  enumerates every step + the owner + the rollback. Final WU is
  "operator runs the checklist" — the visibility flip itself happens
  outside the loop (it's a human decision on a GitHub UI), the loop
  just confirms readiness.

**Sequencing — must precede 0019's first PyPi tag.**

The PyPi wheel exposes source; if the source repo's history has
secrets, the wheel may reference them. Sequence:

1. 0020 ships → `main` is publishable.
2. Operator flips visibility to public (outside the loop).
3. 0019 ships → first PyPi tag + Claude Code marketplace publish.

A botched 0019 before 0020 means a tagged release with embarrassing
or sensitive content in a non-takedown-friendly channel. Don't.

**Scope OUT.**

- Marketing pages / website / docs site — separate work, not a
  flip-blocker.
- Renaming or rebranding — if the name needs a change, do it
  before 0020 starts.
- Anything from FEAT-2026-0019 (distribution surfaces) — that's its
  own feature.
- Closed-source private-index path (devpi / CodeArtifact). Out of
  scope because we're going public; if the public path is wrong,
  re-evaluate before 0020 starts, not inside it.

**Status: planned.** Two-gate feature, must precede 0019's first
public release. Likely shape: gate 1 = one substantive WU per audit
class (secret scan, PR sweep, personal-refs grep, cross-pollination,
license headers) + closing ceremony; gate 2 = one substantive WU per
hygiene-file class + the flip-checklist WU + closing ceremony.

## FEAT-2026-0027 — Self-provisioning driver: auto-sync `.specfuse/` + plugin config on run

**Why.** Even with FEAT-2026-0026, adopting/upgrading a project is still manual:
the user runs `specfuse init`/`upgrade` and separately installs the Claude plugin.
The leverage is to make a plain `specfuse-loop` run self-provision the project to the
installed driver's version — create the scaffold if absent, upgrade it if older
(never downgrade), and write the Claude plugin auto-provision config — so adoption is
"install specfuse globally, run it in any repo, done."

**Goal.** A version-gated auto-sync on driver run, plus diagnosis and onboarding.

- **Auto-sync decision tree** (on `specfuse-loop` run, comparing the installed
  scaffold version to `.specfuse/VERSION`): missing → auto-**create**; older with no
  local edits to versioned files → auto-**overlay** + stamp; older WITH local edits →
  **prompt / defer** to `specfuse upgrade` (never silently revert edits); equal →
  no-op (no diff noise); newer → **warn + refuse** (never downgrade; suggest
  `pipx upgrade specfuse-loop`). Never auto-commit — working-tree only, "review with
  git diff".
- **Local-edit detection** via a shipped-file hash manifest (new artifact) so the
  overlay can tell pristine versioned files from user-customized ones.
- **`.claude/settings.json` plugin config** — write/refresh `extraKnownMarketplaces`
  + `enabledPlugins` (merge-safe, preserving other keys) so Claude Code auto-installs
  `specfuse@specfuse` on trust. The driver writes config; Claude Code performs the
  install (it cannot run `/plugin` itself). Warn on plugin/driver version drift.
- **`specfuse doctor`** — read-only: driver version, scaffold version, plugin
  install/enable state, drift, recommended action. Diagnosis without mutation.
- **First-run prompt** — `specfuse-loop` in a bare repo offers to scaffold at the
  installed version. `--no-autosync` flag + `.specfuse/` config toggle for manual
  control; `specfuse upgrade` remains the explicit can-clobber path.

**Gate sketch.** G1 auto-sync engine (decision tree + hash-manifest detection +
toggles). G2 `.claude` plugin-config writing + version-drift warning. G3
`specfuse doctor` + first-run prompt.

**Legacy migration (added from FEAT-2026-0026's gate-3 review).** A repo scaffolded by
the old `init.sh` carries `.specfuse/scripts/` (vendored driver) and `.specfuse/skills/`
(relative symlinks) that the pip-native model replaces with the package + plugin.
FEAT-2026-0026's `specfuse upgrade` deliberately **leaves these intact** (deleting
user-adjacent dirs is a migration-semantics call). This feature owns the migration:
`specfuse init --migrate` (or an upgrade flag) that detects the legacy layout and prunes
the vendored `scripts/` + skill symlinks once the plugin is wired — opt-in, never silent.

**Benefits.** "Install once globally, run anywhere" adoption; projects converge to the
installed version automatically and safely; the never-downgrade rule protects projects
configured by a newer specfuse; the plugin provisions without manual `/plugin`
commands; legacy init.sh repos migrate cleanly to pip-native.

**Status: done.** Depends on FEAT-2026-0026 (needs package scaffold data +
in-process init/upgrade) and FEAT-2026-0028 (the umbrella CLI must call the scaffold
API before auto-sync can drive it). Also packaging/harness-coupled — expect interactive.

## FEAT-2026-0028 — Umbrella CLI → scaffold-API wiring + docs in the pip seed

**Why.** FEAT-2026-0026 shipped `specfuse.loop.scaffold` (`init_specfuse`,
`upgrade_specfuse`, `wire_claude`, `init`) and made `init.sh` a thin shim delegating to
`specfuse init`/`upgrade`. But the umbrella `specfuse` CLI's `init`/`upgrade` subcommands
still print curl-bash / pip-only guidance (FEAT-2026-0019's stubs) — they do **not** call
the new scaffold API. So `specfuse init`/`upgrade` and the init.sh shim do not actually
scaffold end-to-end yet. Surfaced as the required follow-up in FEAT-2026-0026's gate-3
review (the terminal gate auto-closed, so it was captured in PR #68, not the stub
retrospective). This **gates real adoption** — including the first external IaC project test.

Also: FEAT-2026-0026's package seed ships `templates/`, `rules/`, examples, `VERSION` —
but **no `docs/`**, whereas `init.sh` ships the methodology docs via `deploy_docs`. A
pip-scaffolded repo is missing `.specfuse/docs/`. Close the parity gap in the same feature.

**Goal.**
- Rewire `specfuse/specfuse` `cli.py`: `cmd_init` → `specfuse.loop.scaffold.init(target,
  ci_check=...)`; `cmd_upgrade` → `upgrade_specfuse(target)` then the pip-upgrade + plugin
  hint. Wire `--dry-run`. Verify against the real (no longer stub) API.
- Add `docs/` (methodology + concepts, the `deploy_docs` set) to the pip seed so
  `specfuse init`/`upgrade` lay down `.specfuse/docs/`; extend the drift guard.
- Release coordination: depends on a published `specfuse-loop` carrying `scaffold.py`
  (FEAT-2026-0026 merged → released), then a `specfuse` umbrella release.

**Benefits.** `specfuse init`/`upgrade` and the init.sh shim actually scaffold from pip
end-to-end — the last gap before `init.sh` can be deleted (v1.1) and before
FEAT-2026-0027's auto-sync has a working CLI to lean on. Unblocks the IaC adoption test.

**Status: done.** Depends on FEAT-2026-0026 (the scaffold API) being released to PyPI.
Cross-repo (loop seed/docs + umbrella `cli.py`) — expect interactive.

## FEAT-2026-0033 — Sub-repo component scoping: multiple components in one repo

**Why.** The loop assumes component == repo: `.specfuse/` is resolved as `Path(".specfuse")` relative to cwd (`specfuse/loop/loop.py:61-64`), gate commands run with no `cwd=` (`loop.py:1764`), there is one tree lock, one roadmap, and one verification surface per repo. Real projects put multiple shippable deliverables in one repo — a phone app and a kiosk/tablet app sharing generated Flutter libraries, delivered as separate store apps from the same git tree. Today the only way to model that is to flatten every deliverable into a single repo-root-scoped component, so a kiosk-only feature also runs the phone app's gates. Slow, not wrong — but it degrades as deliverables and gate runtimes grow, and it gives ownership/release-cadence-diverged deliverables no independent surface.

**Goal.** Let one repo host N components without splitting the git tree, keeping `.specfuse/` at repo root (one lock, one roadmap). Introduce an optional `component:` selector so a feature runs only the gates tagged to its component; unset selector = all gates, so existing single-component projects are unchanged.

**Sketch (subject to design gate).**
- `verification.yml`: optional per-gate `cwd:` (run command from a subdir) and optional `component:` tag on gate entries.
- Feature frontmatter: optional `component:` field; driver filters gates to matching `component:` (unset ⇒ run all — backward compatible).
- Widen the event `source` regex `component:<name>` (`shared/schemas/event.schema.json:65`) to admit `component:<repo>/<sub>` addressing, so sub-repo components are legible in the audit trail. Flag now so nothing hard-codes against the current bare-repo-name shape.
- Explicitly **rejected** approach: multiple `.specfuse/` dirs per repo — fights the single lock, the single roadmap, and `git rev-parse --show-toplevel` path math (`loop.py:904-935`) for little gain.

**Benefits.** Backward-compatible (new fields optional, selector defaults to all) ⇒ ships as an `init.sh --upgrade` propagation, not a migration. Removes the flatten tax for multi-deliverable repos. Orchestrator side gains an optional `components:` list per repo inventory + a `component:` narrower alongside `assigned_repo`, so the orchestrator can dispatch to a sub-repo component without breaking the existing `assigned_repo` contract.

**Trigger to promote (deferred → active).** One of: gate runtime on a multi-deliverable repo hurts enough to matter, or two deliverables in one repo genuinely diverge on owner / release cadence / CI. First live case in a downstream project: a kiosk/tablet app sharing one repo with its phone app, both consuming the same generated libraries. Until a trigger fires, the flatten approach is the sanctioned workaround.

**Status: deferred.** Parked pending a real trigger (above). Resumable — flip to `active` when a trigger fires; design gate first (the sketch is not yet a committed contract).

## FEAT-2026-0034 — Roadmap-table lint: enforce blocked features carry a resolvable Blocked-by link

**Why.** The `blocked` feature status (shipped in loop 0.3.24) is only meaningful if a blocked feature actually names its unmet dependency — an ADR or an upstream FEAT — and links to it. Nothing enforces that today: `lint_plan` validates feature dirs, PLAN frontmatter, and the gate/WU graph, not the roadmap-table prose. So a row can sit at `status: blocked` with no `**Blocked by.**` block at all (silently collapsing the deliberate `blocked`-vs-`deferred` distinction — `deferred` is the no-named-blocker park), or with a link that has rotted: an ADR path that moved, or a `#feat-yyyy-nnnn` anchor whose target was archived. The one enforcement gap left by the blocked-status work.

**Goal.** Add a roadmap-table lint pass (extend `lint_plan.py` or a sibling roadmap linter, wired into the same gate) that, for every row whose Status is `blocked`, checks its detail section carries a `**Blocked by.**` block with at least one link, and that each link resolves — an ADR file path exists on disk (or is a well-formed URL), and a feature-dependency link points at a live inline `<a id="feat-…">` anchor or a `roadmap-archive.md#…` target. Symmetrically WARN on a `**Blocked by.**` block attached to a non-`blocked` row (stale block left after an unblock).

**Benefits.** Makes `blocked` trustworthy: the roadmap cannot display `blocked` without stating, resolvably, what it waits on. Catches blocker link-rot at lint time instead of when a human clicks a dead link. Closes the enforcement gap the blocked-status feature deliberately deferred, keeping the machine-checkable invariants ahead of the prose conventions.

**Status: planned.**

## Notes

- Correlation IDs are allocated here, sequentially per year: `FEAT-YYYY-NNNN`.
  Work units take `FEAT-YYYY-NNNN/TNN` for substantive units,
  `FEAT-YYYY-NNNN/G<n>-(RETRO|LESSONS|DOCS|PLAN)` for the four-WU closing
  sequence, and `FEAT-YYYY-NNNN/G<n>-CLOSE` for the single-gate `close`
  alternative — see `.specfuse/rules/correlation-ids.md`.
- The feature folder name carries the full ID plus a slug, so it greps,
  sorts, and threads cleanly.
- **Read `.specfuse/LEARNINGS.md` before detailing a new feature.** It is
  the accumulated output of every gate's lessons step and exists to make
  the next plan better than the last.
