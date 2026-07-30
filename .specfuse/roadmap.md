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
| FEAT-2026-0034 | Roadmap link-integrity lint: resolvable Blocked-by links, anchor adjacency, cross-file ID uniqueness | planned | — | [→ detail](#feat-2026-0034) |
| FEAT-2026-0035 | Guided draft-feature interview: one decision at a time, pros/cons + recommendation | done | — | — |
| FEAT-2026-0036 | Pin ruff's lint ruleset explicitly; lift the <0.16 version pin | done | `.specfuse/features/FEAT-2026-0036-adopt-ruff-016/` | — |
| FEAT-2026-0037 | Evaluate adopting ruff 0.16's expanded default ruleset (opt-in the valuable families) | done | `.specfuse/features/FEAT-2026-0037-ruff-correctness-rules/` | [→ archive](roadmap-archive.md#feat-2026-0037) |
| FEAT-2026-0038 | DLQ quarantine harvest mode (per-component) | blocked | — | — |
| FEAT-2026-0039 | Monitoring schema + derive-monitoring skill (discovery, diagnosability audit, bootstrap) | done | `.specfuse/features/FEAT-2026-0039-monitoring-schema/` | [→ detail](#feat-2026-0039) |
| FEAT-2026-0040 | Failure-artifact harvester CLI (detect + report; local and gh-actions runners) | done | `.specfuse/features/FEAT-2026-0040-failure-artifact-harvester/` | [→ archive](roadmap-archive.md#feat-2026-0040) |
| FEAT-2026-0041 | diagnose-issue skill: root-cause diagnosis of harvester findings (manual + headless) | blocked | — | — |
| FEAT-2026-0042 | Autofix wiring: headless fix-bug from diagnosed findings behind per-component dial | blocked | — | — |
| FEAT-2026-0043 | In-cluster monitor runner: AKS CronJob surface for the harvester | blocked | — | — |
| FEAT-2026-0044 | agent-policy.yml schema + groom-backlog skill (priority queue, rules, dials) | planned | — | — |
| FEAT-2026-0045 | issue-triage skill: categorize and route incoming GH issues (manual → auto dial) | planned | — | — |
| FEAT-2026-0046 | Escalation contract: needs-human issues (assigned, structured) + /attention inbox skill | done | — | [→ archive](roadmap-archive.md#feat-2026-0046) |
| FEAT-2026-0047 | Notify webhook (pluggable provider) + heartbeat-silence self-alert | blocked | — | — |
| FEAT-2026-0048 | Autonomous bug pipeline: triage → fix → PR with auto-merge dial + hardcoded guardrails | blocked | — | — |
| FEAT-2026-0049 | specfuse-agent runner: run-to-drain queue execution with lock, caps, pause-and-switch | blocked | — | — |
| FEAT-2026-0050 | Async feature-drafting interview via question issues | blocked | — | — |
| FEAT-2026-0051 | Pre-flight baseline gate probe + preexisting_gate_failure halt | done | `.specfuse/features/FEAT-2026-0051-preflight-baseline-gate-probe/` | [→ archive](roadmap-archive.md#feat-2026-0051) |
| FEAT-2026-0052 | Baseline-delta ratchet, waiver, and tracking-issue emission | planned | — | — |
| FEAT-2026-0053 | Autonomous feature mode (auto gate-arming with mechanical stop conditions) | active | `.specfuse/features/FEAT-2026-0053-auto-mode/` | [→ detail](#feat-2026-0053) |
| FEAT-2026-0054 | Close-ceremony skeleton + in-session closing lint | done | — | [→ archive](roadmap-archive.md#feat-2026-0054) |
| FEAT-2026-0055 | Arm-time WU contract lint: produces satisfiability + boundary consistency | done | `.specfuse/features/FEAT-2026-0055-arm-time-wu-contract-lint/` | [→ archive](roadmap-archive.md#feat-2026-0055) |
| FEAT-2026-0056 | Per-criterion DoD state + incremental re-close | planned | — | — |
| FEAT-2026-0057 | Executable oracle contract for gates: scripted verification + environment prep | planned | — | — |
| FEAT-2026-0058 | Feature decision registry + override lint | planned | — | — |
| FEAT-2026-0059 | Hedged-close ergonomics: classified follow-ups, verdict-ceiling headline, routed-finding tracking | planned | — | — |
| FEAT-2026-0069 | monitoring.yml check targets + queue-stalled check type | done | `.specfuse/features/FEAT-2026-0069-monitoring-check-targets/` | [→ detail](#feat-2026-0069) |
| FEAT-2026-0070 | Terminal-flip contract — hedged-verdict acceptance, row-status breadth, auto-close debt | done | `.specfuse/features/FEAT-2026-0070-terminal-flip-contract/` | [→ archive](roadmap-archive.md#feat-2026-0070) |
| FEAT-2026-0071 | Label registry + provisioning on init/upgrade (best-effort, never fatal) | done | `.specfuse/features/FEAT-2026-0071-label-provisioning/` | [→ archive](roadmap-archive.md#feat-2026-0071) |
| FEAT-2026-0072 | Structural-invariant guards: declared surfaces that nothing asserts on | done | `.specfuse/features/FEAT-2026-0072-structural-invariant-guards/` | [→ archive](roadmap-archive.md#feat-2026-0072) |
| FEAT-2026-0060 | Driver-local event schema registry: sanction the three unsanctioned event types | planned | — | [→ detail](#feat-2026-0060) |

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

<a id="feat-2026-0034"></a>
## FEAT-2026-0034 — Roadmap link-integrity lint: resolvable Blocked-by links, anchor adjacency, cross-file ID uniqueness

**Why.** The `blocked` feature status (shipped in loop 0.3.24) is only meaningful if a blocked feature actually names its unmet dependency — an ADR or an upstream FEAT — and links to it. Nothing enforces that today: `lint_plan` validates feature dirs, PLAN frontmatter, and the gate/WU graph, not the roadmap-table prose. So a row can sit at `status: blocked` with no `**Blocked by.**` block at all (silently collapsing the deliberate `blocked`-vs-`deferred` distinction — `deferred` is the no-named-blocker park), or with a link that has rotted: an ADR path that moved, or a `#feat-yyyy-nnnn` anchor whose target was archived.

A 2026-07-30 manual audit of `roadmap.md` + `roadmap-archive.md` found four distinct rot shapes and 19 instances, only some of which a resolution-only check would catch. (1) **Unresolvable refs** — 10 prose links to archived features still using the bare `#feat-…` form after the section moved to `roadmap-archive.md`, plus 5 in the archive pointing the other way at sections that live in `roadmap.md`; the rot is bidirectional, so a one-file linter misses half of it. (2) **Missing anchors** — `blocked` rows 0041 and 0047 whose Detail cells linked to sections that never carried an `<a id>`. (3) **Misattached anchors** — the anchor above the 0053 section read `feat-2026-0069`, so 0053's Detail cell was dead *and* 0069's ref silently landed on the wrong feature. (4) **Duplicate IDs across files** — `/roadmap-archive` dragged the preceding live feature's anchor along with each section it moved, leaving `feat-2026-0041` and `feat-2026-0047` defined in *both* files; those refs resolved cleanly to the wrong section, which is strictly worse than a dead link because nothing visibly breaks. Shapes 3 and 4 are the archiver misfiring on every run, so they recur until linted.

**Goal.** A roadmap link-integrity lint pass (extend `lint_plan.py` or a sibling roadmap linter, wired into the same gate) reading `roadmap.md` and `roadmap-archive.md` as one link graph, checking four invariants. **Blocked-by presence and resolution** — every `blocked` row's detail section carries a `**Blocked by.**` block with at least one link; each link resolves (ADR path exists on disk or is a well-formed URL; a feature link points at a live `<a id="feat-…">` anchor in either file). Symmetrically WARN on a `**Blocked by.**` block attached to a non-`blocked` row. **Ref resolution, both directions** — every `#feat-…` ref in either file resolves against the anchor set of the file it names, with a bare `#…` resolving same-file; an ERROR names the correct cross-file form as the fix, since the mechanical repair is a prefix rewrite. **Anchor adjacency** — every `<a id="feat-YYYY-NNNN">` is immediately followed (blank lines allowed) by a `## FEAT-YYYY-NNNN` heading whose ID matches; an anchor followed by a different feature's heading, or by another anchor, is an ERROR. This is the check that catches shape 3 and the archiver's stray-anchor output. **Cross-file ID uniqueness** — no `feat-…` ID is defined in both files, and none twice within a file. Round out with a WARN for a row whose Detail cell is `—` while a detail section for that ID exists (the reverse of link rot: a live section nothing points at).

**Benefits.** Makes `blocked` trustworthy: the roadmap cannot display `blocked` without stating, resolvably, what it waits on. Catches all four rot shapes at lint time rather than when a human clicks a dead link — or worse, follows a resolvable link to the wrong feature and reasons from it. Adjacency and uniqueness turn `/roadmap-archive`'s stray-anchor defect from a silent recurring corruption into a failing check the next archive run trips immediately, which is the durable fix; repairing the current instances by hand is not. Keeps the machine-checkable invariants ahead of the prose conventions.

**Status: planned.**

## FEAT-2026-0035 — Guided draft-feature interview: one decision at a time, pros/cons + recommendation

**Why.** `draft-feature` Step 3 asks a **single batched round** of hat questions — a wall of questions that suits an expert who already knows every answer but overwhelms the newcomers the methodology most needs to onboard, and it hands the driver weakly-validated answers (a batch is skimmed, not deliberated). Onboarding friction and driver alignment both suffer. The improvement: walk the user through the framing decisions **one at a time**, and for each *decision* question present the options with prose pros/cons and a recommendation so they choose well — the shape `/pick-feature` already uses, extended per-question.

**Goal.** Rewrite Step 3 into an **adaptive guided interview**, no mode toggle:
- Ask one question per turn; the count is **evidence-gated** (the existing "infer first, ask last" rule already auto-scales it — a well-evidenced feature yields few questions, a vague one many), so experts aren't forced through filler and novices aren't dumped a wall.
- Distinguish two question kinds: **elicitation** (only the user knows — roadmap_goal, who's the user, scope-out) asked open; **decision** (skill can enumerate — autonomy level, additive-vs-replacement, gate count, single-vs-multi-gate, red-test strategy) presented as options + **prose** pros/cons + a recommendation + the user's pick. **Never a table.**
- Mid-interview escape hatch: the user can say "take your recommendations for the rest" to fast-forward — an in-flow expert exit, not an up-front choice.

**Benefits.** Lowers onboarding friction and teaches the methodology as it asks; every answer is validated before the next builds on it, so the resulting PLAN aligns the driver better; auto-scaling keeps it cheap for experts on well-understood features. Reuses the proven `/pick-feature` decision-presentation shape, so the craft is consistent across skills.

**Status: done.** Shipped in draft-feature v0.2 (#228).

## FEAT-2026-0036 — Pin ruff's lint ruleset explicitly; lift the <0.16 version pin

**Why.** CI's lint gate broke on ruff 0.16 with ~300 findings on code clean for months. Investigation (this feature) reframed the original premise: they were **not** 300 real errors, and not import-ordering. ruff 0.16 **changed its implicit default `select`** from the classic `E4,E7,E9,F` to a large opinionated set (B/SIM/PLW/RUF/I/…). The repo's `[tool.ruff]` config selected nothing, so it inherited 0.16's new default overnight — the gate expanded purely from a version bump, no code involved. The emergency `ruff>=0.6,<0.16` pin froze the version to dodge it.

**What was done.** Pin the ruleset **explicitly** and version-independently — `[tool.ruff.lint] select = ["E4","E7","E9","F"]`, the classic default the repo was always clean under — then lift the version pin (`ruff>=0.6`). Under ruff 0.16 with the explicit select the gate is clean (`All checks passed!`) and the full suite is unchanged (1295 OK). **No source code changed** — the original "fix ~300 errors across the test files" plan was based on a false premise and was abandoned; the real fix is two lines of config. Executed directly after a loop run on the flawed plan blocked (see LEARNINGS: the run surfaced a hollow-pass and a gate/tool-version-skew lesson).

**Benefits.** The gate is now immune to ruff redefining its defaults again — the intent is written down, not inherited. The version pin is gone, so ruff tracks current. Deliberately adopting 0.16's broader rule families (many are genuinely good) is decoupled into its own opt-in decision (see FEAT-2026-0037) rather than being forced by a bump.

**Status: done.** Config-only fix (`pyproject.toml` explicit select + version unpin); no code change.

## FEAT-2026-0038 — DLQ quarantine harvest mode (per-component)

**Why.** Peek-only DLQ harvesting (monitoring v1) leaves messages in the DLQ: TTL can expire evidence, DLQ depth loses signal value, and replay-after-fix stays manual. Quarantine mode (receive + archive to blob storage) preserves evidence durably and makes replay mechanical, enabling autonomy level 4 (replay-verify-close).

**Goal.** Add a per-component `harvest_mode: peek|quarantine` flag to monitoring.yml; quarantine mode receives DLQ messages, archives full message (body + properties) to a per-env blob container with crash-safe receive-archive ordering, and links the artifact from the GH finding issue. Fingerprint and finding schema unchanged from peek mode.

**Benefits.** DLQ depth becomes a true live signal; failure evidence survives TTL; replay-after-fix becomes mechanical, unlocking self-healing level 4.

**Blocked by.** [FEAT-2026-0040](roadmap-archive.md#feat-2026-0040) — extends the harvester's peek-mode DLQ adapter

**Status: blocked.**

<a id="feat-2026-0039"></a>
## FEAT-2026-0039 — Monitoring schema + derive-monitoring skill (discovery, diagnosability audit, bootstrap)

**Why.** Specfuse-configured repos should be self-healing: every deployable component (web API, message worker, timer worker) proactively watched for functional failures — DLQ messages, error logs, 5xx, missed timer runs, broken business invariants — with findings reported as GitHub issues that feed the existing triage loop (fix-bug or roadmap). The foundation is a declarative `.specfuse/monitoring.yml` (the post-deploy counterpart of `verification.yml`) and a skill that derives it from repo evidence, because hand-authoring per-component checks and auditing diagnosability is mechanical work the repo itself can mostly answer.

**Goal.** Ship (a) the monitoring.yml schema + example: `environments`, `components` with per-component trust dials (`runner: local|gh-actions|in-cluster`, `diagnose: manual|auto`, `autofix: off|on`), check types `dlq` (harvest_mode peek|quarantine), `error-logs`, `http-5xx`, `heartbeat`, and custom `invariant` (user KQL + `fingerprint_by`); (b) a design-for-diagnosis rule (correlation IDs, structured logging, cloud_RoleName per component, DLQ error-context capture); (c) the `derive-monitoring` skill mirroring derive-verification's posture (evidence first, ask only what code cannot answer, draft never auto-write) that discovers components, interviews for invariants and environment coordinates, audits each component against the design-for-diagnosis rule with gap findings, and drafts monitoring.yml + runner bootstrap files (GH Actions workflow, gitignored `monitoring.local.yml` example, read-only secrets checklist) with staged per-file accepts. Provider-agnostic by design, exactly as verification.yml is language-agnostic: check types are neutral concepts, environments carry typed provider bindings (`telemetry.provider`, `broker.provider`), and adapters normalize into a neutral artifact model (OTel semantic conventions; `trace_id` as the correlation spine). Azure adapters ship first: Service Bus + App Insights (operation_Id maps to the spine).

**Benefits.** Turnkey bootstrap: interview ends, user reviews drafted files, first local `--dry-run` is minutes away. The diagnosability audit ensures components are born diagnosable — the property that lets a repo-resident agent outperform external monitoring at root-cause. Schema decided up front keeps the harvester (FEAT-2026-0040) and later autonomy stages purely additive.

**Scope narrowed at drafting (see the feature's `PLAN.md`).** Deliverable (c)'s
GitHub Actions runner workflow moved to [FEAT-2026-0040](roadmap-archive.md#feat-2026-0040): that
workflow invokes the harvester CLI, which does not exist until 0040, and shipping a
template whose entry point is a nonexistent binary is the `[FEAT-2026-0029/G1-CLOSE]`
failure verbatim. The local-runner bootstrap artifacts still ship here. Added at
drafting: a committed structural validator for the schema, so 0040 inherits a
machine-checkable contract rather than prose.

**Status: done.**

<a id="feat-2026-0041"></a>
## FEAT-2026-0041 — diagnose-issue skill: root-cause diagnosis of harvester findings (manual + headless)

**Why.** A harvester finding carries the artifacts; the unique value of a repo-resident agent is joining them with source code to name the root cause ("DLQ message failed because OrderMapper.cs:142 throws on null DiscountCode") — the thing external monitoring can never do. Diagnosis must earn trust interactively before running unattended.

**Goal.** A `/diagnose-issue NN` skill: pulls artifact section + correlation-ID-linked telemetry from the finding issue, reads the component source, and posts a structured diagnosis comment — root cause, evidence trail, candidate fix, plus machine-readable `confidence` and `fix_scope: small|large|external` fields (the gate FEAT-2026-0042 consumes). Identical comment format from both entry points: interactive first, headless (`claude -p`) second, auto-triggered by the harvester on new fingerprints only for components with `diagnose: auto` (one diagnosis per fingerprint, not per occurrence). Redaction rules apply to diagnosis prose.

**Benefits.** Autonomy level 2: issues arrive pre-diagnosed for opted-in components, at bounded token cost (dedupe caps spend). The per-component manual-to-auto dial lets diagnosis quality be proven with a human watching before automation, component by component.

**Blocked by.** [FEAT-2026-0040](roadmap-archive.md#feat-2026-0040) — harvester findings/issue contract must exist

**Status: blocked.**

## FEAT-2026-0042 — Autofix wiring: headless fix-bug from diagnosed findings behind per-component dial

**Why.** With detection (FEAT-2026-0040) and diagnosis (FEAT-2026-0041) in place, the remaining step to a self-healing repo is launching the existing fix-bug skill (1 bug = 1 branch = 1 PR, test-first) from a diagnosed finding — guarded, because a wrong diagnosis can produce a confidently-wrong PR and an incident storm can flood the repo.

**Goal.** Per-component `autofix: on|off` (default off). Auto-fire headless `/fix-bug NN` only when the diagnosis self-reports confident + `fix_scope: small`; `large`/`external` findings route to human triage or roadmap promotion instead. One fix run per fingerprint, daily auto-fix cap, and an "auto-fix attempted, failed" label so refusals and failures surface instead of dying silently. Human merge on a protected branch is the default floor; auto-merge is governed by the agent-level dial and hardcoded guardrails defined in FEAT-2026-0048 (supersession recorded 2026-07-25 — small test-first bug diffs are cheap to revert, so bugs may graduate to auto-merge; features never do here).

**Benefits.** Autonomy level 3: wake up to a ready test-first PR for known-small failures, on components that earned the dial. Guardrails (confidence gate, caps, failure labels) keep bad diagnoses and storms from eroding trust in the pipeline.

**Blocked by.** [FEAT-2026-0041](#feat-2026-0041) — diagnosis confidence/fix_scope fields gate autofix

**Status: blocked.**

## FEAT-2026-0043 — In-cluster monitor runner: AKS CronJob surface for the harvester

**Why.** The harvester CLI is host-agnostic by design (FEAT-2026-0040 ships local + gh-actions surfaces), but orgs whose policy forbids external runners touching environments — or who want workload identity instead of exported secrets and tighter schedules than GH Actions cron honors — need an in-cluster surface.

**Goal.** Container image build for the harvester CLI, a CronJob manifest template, Azure workload-identity setup docs (read-only Service Bus Listen + App Insights access, GH token for issue writes), and derive-monitoring drafting support for `runner: in-cluster` components. Same CLI, same monitoring.yml, same issue contract — only the launch surface differs.

**Benefits.** Completes the per-component runner matrix (local for tuning, gh-actions for turnkey, in-cluster for perimeter-bound orgs); schedules honored tightly; credentials never leave Azure.

**Blocked by.** [FEAT-2026-0040](roadmap-archive.md#feat-2026-0040) — packages the harvester CLI

**Status: blocked.**

<a id="feat-2026-0044"></a>
## FEAT-2026-0044 — agent-policy.yml schema + groom-backlog skill (priority queue, rules, dials)

**Why.** The specfuse-agent (FEAT-2026-0049) must know the operator's priorities ahead of time: priority is policy, not intelligence — the agent selects work *within* a declared policy and escalates ties, never guesses intent. That policy needs one auditable, versioned surface, plus a periodic ritual that keeps it fed as the backlog evolves.

**Goal.** Ship (a) the `.specfuse/agent-policy.yml` schema + example: ordered `queue:` of FEAT-IDs (validated against the roadmap every agent run — entries must exist and be `planned`/`active`/`blocked`; drift escalates, never guessed around), class rules (`bugs: {preempt, min_severity, automerge}`, `features: {gate_review: human|auto per-feature override, wip_limit}`), budgets (`max_tokens_per_run`, `max_open_prs`, daily caps), and escalation config (webhook, `assignee`, quiet hours, SLA); (b) the `/groom-backlog` skill: reads roadmap planned set, open triaged issues, blocked chains, LEARNINGS, and the current queue; surfaces queue-hygiene findings (done entries to remove, blocked-upstream reorders, triaged feature-class issues not yet on the roadmap) and per-candidate trade-offs in the pick-feature style; proposes a new ordered queue and writes agent-policy.yml only on explicit accept. Empty queue = agent works bugs only and asks for priorities.

**Benefits.** The operator's role shifts from per-decision operator to policy-setter: one file review changes agent behavior; a ten-minute periodic grooming session keeps the agent autonomous between check-ins. Every autonomy dial decided across the monitoring and agent initiatives gets its declared home.

**Status: planned.**

<a id="feat-2026-0045"></a>
## FEAT-2026-0045 — issue-triage skill: categorize and route incoming GH issues (manual → auto dial)

**Why.** Issues arrive from the monitoring harvester, the orchestrator, and third parties. Before anything can be fixed or planned, each needs categorizing (bug / feature request / question / duplicate / won't-fix) and routing (fix-bug, roadmap-add candidate, needs-human, close). Today that triage is implicit human work; the agent needs it as an explicit, dial-controlled step — and it is useful standalone long before the agent exists.

**Goal.** A `/triage-issues` skill: scans untriaged issues (no triage label), proposes per-issue category + route with a one-paragraph rationale — bug → labeled and queued for fix-bug (severity assessed against the fix-bug small-scope contract; large/risky proposes feature promotion instead), feature → proposed roadmap-add draft, duplicate → linked and proposed close, question/unclear → needs-human. Interactive propose-and-confirm first; headless mode behind an `auto` dial applies only high-confidence categorizations and leaves the rest labeled for human triage. Fingerprint-aware: recognizes harvester-created issues (already structured) and skips re-categorizing them.

**Benefits.** Every inbound issue lands in exactly one lane with an audit trail; the agent's bug pipeline (FEAT-2026-0048) gets a clean, machine-readable intake; the human only sees the issues that genuinely need judgment.

**Status: planned.**

<a id="feat-2026-0047"></a>
## FEAT-2026-0047 — Notify webhook (pluggable provider) + heartbeat-silence self-alert

**Why.** Escalations must push, not wait to be pulled — the vision explicitly requires the agent to reach out (Discord/Teams/Slack). Notify-only keeps it trivial: answers belong in the GH escalation issue (FEAT-2026-0046), so no bot hosting, no reply parsing in chat, no provider lock-in. And a silent agent is itself a failure mode: a stalled or dead agent must announce itself.

**Goal.** A webhook notifier in agent-policy.yml (`escalation.webhook`): on new/re-pinged needs-human issues, post a one-liner + link to the configured channel; provider = any incoming-webhook URL (Discord/Slack/Teams payload adapters, provider swap = URL change). SLA handling: unanswered escalation past the configured window re-pings once, then the item is parked and the queue continues. Heartbeat-silence self-alert: the agent records a last-run timestamp (repo-derivable); a scheduled check (or /attention on open) flags "agent has not run in M hours" — and where a schedule exists, fires the same webhook.

**Benefits.** The operator hears about blockers within minutes wherever they live, answers where the audit trail lives, and can trust that agent silence is itself alarmed — monitoring the monitor at near-zero build cost.

**Blocked by.** [FEAT-2026-0046](roadmap-archive.md#feat-2026-0046) — notifies escalation-contract items; contract must exist first

**Status: blocked.**

<a id="feat-2026-0048"></a>
## FEAT-2026-0048 — Autonomous bug pipeline: triage → fix → PR with auto-merge dial + hardcoded guardrails

**Why.** The agent's core autonomy promise: bugs handled end-to-end. Small test-first diffs are cheap to revert, so the risk asymmetry favors autonomy for bugs specifically — unlike features, where gate reviews stay human (per-feature `gate_review` dial, default human). This feature supersedes FEAT-2026-0042's "human merge is the permanent floor" with "default floor + dial", recorded there.

**Goal.** Orchestrate the full bug lane headlessly: triaged bug issue (FEAT-2026-0045) or diagnosed monitoring finding (FEAT-2026-0041) → headless `/fix-bug` (1 bug = 1 branch = 1 PR, test-first; its large/complex refusal escalates to needs-human or feature promotion) → PR → on CI green, merge behind `bug_automerge: off|on` (default off). Even at `on`, merge requires ALL hardcoded guardrails: test-first evidence in the diff, full verification gates green in CI, diff under a configured size cap, zero touches to never-touch paths, the fix traced to a triaged issue or diagnosed finding, and a daily auto-merge cap. Any guardrail failure → PR waits for human with the reason labeled. Fix failures and refusals escalate via the FEAT-2026-0046 contract instead of dying silently.

**Benefits.** Autonomy where reversal is cheap: wake up to fixed-and-merged small bugs (dial on) or ready-to-merge green PRs (dial off), with the fence permanently in place either way — the dial opens the gate, never removes the guardrails.

**Blocked by.** [FEAT-2026-0045](#feat-2026-0045) — needs machine-readable triage intake; [FEAT-2026-0046](roadmap-archive.md#feat-2026-0046) — refusals and guardrail failures escalate through the contract

**Status: blocked.**

<a id="feat-2026-0049"></a>
## FEAT-2026-0049 — specfuse-agent runner: run-to-drain queue execution with lock, caps, pause-and-switch

**Why.** The capstone: a script that drives the whole lifecycle of a specfuse-configured repo — monitoring findings, issue triage, bug fixing, prioritized feature advancement — as a thin conductor over the existing loop driver and skills (none of which it modifies), escalating whatever it cannot handle. The operator controls when and how long it runs, and therefore what it costs.

**Goal.** `specfuse-agent run` — operator-launched, run-to-drain: acquire a lock file (PID + heartbeat timestamp, stale-lock detection, exactly one agent per repo); loop — read repo state (issues, PRs, roadmap, agent-policy.yml, feature folders: the entire agent memory, per the derivable-from-GH-or-safely-losable principle — no agent database), pick the highest-value action under policy (bugs preempt per rules; queue top for features; parse answered needs-human issues first), execute via the existing skill/driver surfaces, reconcile — until the queue is drained or a cap hits (`--max-minutes`, `--max-tokens`, `--max-items`). Feature execution respects gate checkpoints: driver halts `awaiting_review` → escalate per contract and switch to the next workable item (pause = stop and pick different work; feature folders already persist all state). Blocked items park with an escalation; drafting-needed queue tops escalate (drafting stays human in v1). Kill switch: a PAUSE marker checked each iteration. Cron or event triggers later invoke the same script unchanged.

**Benefits.** One command turns the repo self-healing for exactly as long as the operator allows: value delivered per invocation, cost bounded by flags, every human touchpoint flowing through one escalation queue, and every safety property (locks, caps, checkpoints, guardrails) enforced by construction rather than agent judgment.

**Blocked by.** [FEAT-2026-0044](#feat-2026-0044) — policy file is the agent's contract; [FEAT-2026-0046](roadmap-archive.md#feat-2026-0046) — escalation queue; [FEAT-2026-0047](#feat-2026-0047) — outbound notification; [FEAT-2026-0048](#feat-2026-0048) — the autonomous bug lane

**Status: blocked.**

<a id="feat-2026-0050"></a>
## FEAT-2026-0050 — Async feature-drafting interview via question issues

**Why.** In agent v1, an undrafted queue-top feature escalates and waits for an interactive /draft-feature session — correct sequencing (planning is where human judgment adds most), but it becomes the throughput bottleneck once the agent outpaces operator session availability. The interview itself can move async without surrendering drafting quality.

**Goal.** Agent-preparable drafting: for a drafting-needed queue top, the agent studies the roadmap entry, LEARNINGS, exemplars, and the codebase, then posts the draft-feature interview as a needs-human question issue — batched questions in the established format (elicitation open; decisions with prose pros/cons + recommendation), at most two rounds. From the answers it drafts the feature folder, logging explicit assumptions for anything unanswered; gate-1 review remains human per the `gate_review` dial. Falls back to plain escalation when answers are too thin to draft responsibly.

**Benefits.** Drafting progresses on the operator's schedule (answer questions from anywhere, agent does the assembly) while planning judgment and the gate-1 checkpoint stay human — the last throughput bottleneck relieved without repeating the assumption-built-plan failure mode.

**Blocked by.** [FEAT-2026-0049](#feat-2026-0049) — an agent capability; the runner and its escalation loop must exist

**Status: blocked.**

<a id="feat-2026-0052"></a>
## FEAT-2026-0052 — Baseline-delta ratchet, waiver, and tracking-issue emission

**Why.** [FEAT-2026-0051](roadmap-archive.md#feat-2026-0051) stops the bleeding — a gate already red on the base tree halts before any work unit is dispatched — but leaves the operator only two exits: fix the repo-wide debt first, or defer the feature. Neither is right when the debt is real, externally-caused, and slow to resolve (an unpatched transitive advisory with no upstream fix yet), because the feature is then held hostage by a failure it did not cause and cannot repair. The missing third exit is "proceed, with everything the baseline already had held constant and everything new still enforced."

**Goal.** Three additions on top of 0051's recorded baseline. First, the **baseline-delta ratchet**: during a gate, a WU fails only on failures beyond the recorded baseline set, so pre-existing debt stops blocking while anything a WU newly introduces still fails normally — the same shape as the coverage floor, and deliberately chosen over a per-gate mute, which would also hide a genuine vulnerability a WU legitimately introduces. Second, the **waiver**: an operator-set flag that activates the ratchet for a gate, survives driver resume, and is visible in the gate review — turning 0051's halt into a decision point rather than a dead end. Third, **tracking-issue emission**: the escalation carries a fully-formed issue body plus the `gh issue create` command, auto-creating the issue only when `gh auth status` passes and printing the command for the operator otherwise, so a waived baseline is always tracked rather than silently accepted.

**Benefits.** A feature blocked on externally-caused debt can proceed without anyone weakening a gate: the debt is held constant, tracked in an issue, and visible in the gate review, while every newly-introduced failure still fails. Designed against real baseline records produced by 0051 rather than speculatively, and sequenced after it so the oracle-semantics change lands behind a shipped, proven brake.

**Status: planned.**

<a id="feat-2026-0053"></a>
## FEAT-2026-0053 — Autonomous feature mode (auto gate-arming with mechanical stop conditions)

**Why.** The methodology's autonomy field (`auto` / `review` / `supervised`) is written to PLAN.md frontmatter and never read — zero consumers — so every feature stops at every gate boundary exactly like a `review` feature, and a four-gate feature costs four human touches regardless of how routine its gates are. Operator history across features shows those gate reviews are near-universal rubber-stamps whose accepted changes are additive (new work units at gate check, occasionally a new gate), so the per-gate checkpoint spends latency without buying review value; the operator's real read happens at PR review, and merge is always human.

**Goal.** Implement `auto` end-to-end: the driver arms drafted gates and accepts plan-next's additive plan adjustments on its own, stopping only on mechanical conditions. Stop classes: (1) projected budget breach — spent plus planned-remaining exceeds 2× the feature budget; (2) objective-at-risk proxies — hedged close verdict (stays human, unchanged), remaining-work count failing to shrink across two consecutive gate closes, attempt-per-WU trend decay; (3) plan-drift caps — cumulative added WUs above 50% of the original skeleton (counted in planned dollars as well as units), a second added gate, any retroactive edit to passed gates, any addition lacking machine-readable provenance citing the retrospective item or failure event that triggered it; (4) judge-editing — any draft touching verification config, test thresholds, CI workflows, hooks, or the driver itself; (5) decision-class registry hits — human-authored path/keyword registry covering public API shape, schema or data migrations, security posture, dependency additions; (6) model self-flagged must-be-human decisions (self-flags may only subtract autonomy, never grant it). Supporting mechanics: budget projection over the existing per-attempt cost capture in events.jsonl and the per-gate budget brake, tag-before-arm revert points, per-gate doubt summaries accumulated into a FEATURE-REVIEW.md surfaced in the PR body, LEARNINGS entries staged to a pending file promoted at PR review, and a shadow mode that logs would-have-armed / would-have-stopped verdicts on attended features before the dial goes live. Dial read from per-feature frontmatter; policy-file layering may tighten later, never loosen.

**Benefits.** A four-gate feature drops from four human touches to one (the PR review, now fed by the accumulated doubt summaries); unattended runs progress overnight with blast radius bounded by construction — caps, revert tags, and hard floors on judge-editing and retroactive edits — rather than by judgment; shadow-mode telemetry replaces guesswork when tuning stop thresholds; and the declared-but-dead autonomy field finally does what the methodology has promised since it was specified.

**Gate 1 — shipped, and it changes no arming behavior anywhere.** Four substantive work units `done`. `specfuse/loop/plan_baseline.py` writes an immutable `PLAN.baseline.json` snapshot of a feature's as-activated plan graph at first dispatch — write-once by construction, because a refreshable baseline is a drift detector that can be gamed by drifting. `specfuse/loop/arm_eval.py` is the predicate: pure, side-effect-free, mirroring `gate_eval.py`'s shape without sharing its code, returning a per-class verdict (fired / clean / not_evaluable, each with a reason) across seven classes — budget projection, judge-editing, decision-class paths, retroactive edits, drift caps, missing provenance, and open-questions/human-only — plus an overall `would_arm`. The three machine-readable plan-next contract fields (`open_questions`, `human_only`, `provenance`) are documented in both `WU.template.md` copies and covered by **warn-only** lint; the flip to blocking under `auto` is gate 2's, and it is a severity flip needing its own satisfiability answer and runtime probe. Wiring is passive: the driver evaluates and appends one `arm_predicate_evaluated` event at every `awaiting_review` flip, and its control flow after the append is verdict-independent — a predicate exception degrades to an `evaluation_error` payload rather than crashing a gate close. **The organizing principle held.** Only the two veto classes carry model-authored input, and both can only subtract; every approval input is a counter, a path, or a hardcoded constant. Substantive spend **$8.35 against $13.00 drafted (−35.8%)** — three first-attempt passes at roughly 45–48% of estimate, the third consecutive feature to under-run implementation by about a third (issue #260, no per-feature response). The one blocked attempt cost **$1.22**: T04 stopped on discovering that the per-type event-schema registry and the envelope `event_type` enum are both unowned by this repo, which is now **[FEAT-2026-0060](#feat-2026-0060)**; the operator narrowed T04's criteria to follow the existing `gate_reached` / `attempt_outcome` precedent rather than answer the registry question inside a shadow-mode work unit.

**Consumer-visible additions from gate 1, all additive.** Two new modules; three template-documented frontmatter fields; the new `arm_predicate_evaluated` event type on `events.jsonl` (deliberately outside the envelope enum and the per-type registry, matching existing driver-local precedent); and the new per-feature `PLAN.baseline.json` artifact, committed by the driver, which every Specfuse project on a driver at or past 0.7.1 will start seeing appear in its feature folders. Nothing was removed or renamed. Full enumeration and the deferred-verification list are in the feature's `RETROSPECTIVE.md`.

**Gate 1 deliberately did not prove** that either wired call site fires, and the reason generalizes: a work unit that wires new code into the driver cannot be verified by the driver run that wired it — `loop.py` is imported once at process start, so mid-run edits are dead code for the rest of that invocation. `PLAN.baseline.json` existed in **0 of 43** feature directories at close time. Two consequences the arming checkpoint must handle. First, `GATE-01.md`'s first-firing check reads an absent `arm_predicate_evaluated` event as proof the wiring claim is false; on this gate it is more likely a stale process, so **disambiguate before escalating** — did a driver launched after the wiring commit close the gate? Second, this feature's own baseline will be captured at the *next* invocation, from a PLAN.md that by then already contains gate 2's drafted work units, so the "as-activated" graph it records is the post-drift graph. **Gate 2 must not treat this feature's own baseline as evidence that drift detection works.** Relatedly, a close-time sweep of the predicate over all 43 real feature directories returned `would_arm: False` with every class `not_evaluable: no_baseline` on 43 of 43 — the designed fail-closed path confirmed on real input, and the approval path still unproven outside fixtures.

**Status: active.** Gate 1 closed; gate 2 (live arming behind the dial, atomic arm transaction with tag-before-arm, lint warns flipping to blocking under `auto`, FEATURE-REVIEW.md accumulation, LEARNINGS staging) is drafted by `G1-PLAN` and armed by the human. This feature itself runs `autonomy_default: review` — per `[FEAT-2026-0007/G2-LESSONS]`, an enforcement mechanism cannot be exercised by the gate that builds it, so the first live `auto` ride belongs to a successor feature.

## FEAT-2026-0056 — Per-criterion DoD state + incremental re-close

**Why.** A close returning `not_met` triggers fix WUs and a re-dispatched close that re-verifies the entire DoD from scratch. FEAT-2026-0066 ran G2-CLOSE 3 times and G3-CLOSE across 5 attempts — $48.50 of close spend, each pass re-running the full 2200-test suite, full regen, and the real-SQL-Server scenario matrix, including criteria already proven green on prior attempts. Close attempts are the costliest attempt type portfolio-wide ($4.2 avg vs $3.5 implementation) and 4 of the 10 most expensive WUs are closes.

**Goal.** GATE files carry the DoD as a per-criterion checklist; each close attempt records per-criterion pass/fail state. A re-dispatched close re-verifies only failed and newly-added criteria plus a regression check scoped to the diff landed since the last close attempt. Terminal closes keep a full-walk option (flag or default) for the final pass, so end-to-end freshness is still available where it matters.

**Benefits.** Roughly halves close cost on multi-attempt gates — the dominant close-cost mechanic in the two most expensive features ($157.75 and $140.30). A cheaper `not_met` keeps closes honest: the incentive pressure toward optimistic `met` verdicts drops when finding a defect no longer re-prices the whole ceremony.

**Status: planned.**

## FEAT-2026-0057 — Executable oracle contract for gates: scripted verification + environment prep

**Why.** FEAT-2026-0066's closes hand-drove the same verification stack at least four times — consumer clone sync, regen, `dotnet build`, six real-SQL-Server scenarios, full generator suite — from prose instructions, at $8–12 per pass. A consumer clone that had drifted stale cost one entire close cycle: the environment-prep step (`git reset --hard origin/main` before a Hard Rule #2 proof) lived in agent memory and LEARNINGS prose, not in anything enforced. Deterministic work re-derived by a frontier model every attempt is the single biggest recurring close cost in generator-class repos.

**Goal.** `verification.yml` / GATE frontmatter gains named, ordered oracle commands, including environment-prep steps, per gate or per criterion (composing with FEAT-2026-0056's per-criterion state). The driver — or the close agent as a mandatory first action — executes them deterministically and captures output; the close agent's job narrows to interpreting results, judging the DoD, and writing the ledger. Target-project harness scripts (e.g. the generator's SQL Server scenario matrix) stay in the target repo; the loop ships the contract, dispatch, and capture.

**Benefits.** Close attempts become script-run plus interpretation — cheaper, reproducible, and viable on a smaller model tier; environment-freshness lessons become enforced steps instead of prose that each new close may or may not recall; verification evidence gains a consistent, machine-captured form across features.

**Status: planned.**

## FEAT-2026-0058 — Feature decision registry + override lint

**Why.** FEAT-2026-0066 hit three drift defects from decisions transcribed as prose between PLAN, GATE, and WU files: a four-row operator contract table transcribed as three rows (the dropped 404 row shipped as a defect and cost a gate), a false premise propagated into three files (T11 had to repair all three), and an ADR silently overriding a ratified operator decision — surfaced two gates later as a close blocker. The WU itself noted "there is no override registry in `.specfuse/` today". Vigilant prose is the only current defense against all three shapes.

**Goal.** A per-feature `DECISIONS.md` registry: decision ID, statement, owner, status (`ratified` / `overridden-pending-signoff` / `superseded`), and provenance link. PLAN/GATE/WU artifacts reference decisions by ID instead of restating them. `specfuse-lint` blocks arming a gate whose artifacts contradict the registry or carry an override lacking an operator sign-off mark; the close ceremony's contract-change enumeration reads from the registry rather than re-deriving it.

**Benefits.** Transcription drift and silent overrides become lintable instead of vigilance-dependent; multi-gate features keep one canonical decision surface that survives re-arms and reopens; operator review checkpoints get a single place to confirm or veto overrides instead of hunting them in prose diffs.

**Status: planned.**

## FEAT-2026-0059 — Hedged-close ergonomics: classified follow-ups, verdict-ceiling headline, routed-finding tracking

**Why.** First live run of `/accept-hedged-close` (FEAT-2026-0054, 2026-07-30) showed the operator-facing gap: the skill quotes the raw D-entry follow-up record and demands a one-line reason, but never answers the operator's actual questions — *why couldn't this close `met`, and what kind of reason is expected?* On 0054 the answer was derivable but buried: two entries were unclosable in-repo by construction (an operator-signature entry and a future-rate-in-other-repos entry) and two were findings routed to other owners — meaning `met_locally` was the structural ceiling and no rework alternative existed. The operator had to reverse-engineer that from four verbose entries. Routed findings also currently survive only as retrospective prose, with no tracking surface.

**Goal.** (1) `close-discipline.md` §2's hedged-verdict record gains a required `kind:` per entry — `acceptance-discharged` / `externally-verifiable-later` / `routed-finding` — written by the close WU, which has the context. (2) `/accept-hedged-close` reads the classification and leads with a verdict-ceiling headline ("no in-repo rework can raise this verdict" vs "rework exists: <what>"), states the explicit alternative (accept now vs stay hedged until the named upgrade conditions, then recheck), and scaffolds the reason prompt from the classification while still requiring the operator's own words (`operator-escalation.md`'s never-author rule intact). (3) At acceptance, each `routed-finding` entry prompts for a tracking surface — existing issue/roadmap row, or offer `/roadmap-add` / `gh issue create` — so accepted follow-ups land in a queue instead of dying in prose.

**Benefits.** The operator's accept/rework decision becomes a choice between two named options instead of a blank-line prompt after a wall of quotes; acceptance reasons get sharper because the skill names what is being accepted; routed findings stop leaking; the classification lives in the §2 contract (one home) so the skill re-derives nothing.

**Status: planned.**

<a id="feat-2026-0069"></a>
## FEAT-2026-0069 — monitoring.yml check targets + queue-stalled check type

**Why.** The first real-repo run of `/derive-monitoring` ([FEAT-2026-0039](#feat-2026-0039) gate 2's FU-1, against a downstream .NET backend with one HTTP API plus one functions host carrying 20 queue-topic subscriptions and 10 timer triggers) found that `monitoring.yml` conflates two axes. `component` is asked to be both the unit of deployment and attribution (role name, trust dials, redeploy boundary) *and* the unit of failure-artifact enumeration (what findings are counted per). Those coincide only when a deployable carries exactly one trigger. On the observed host they diverge 30-to-2: one `dlq` check covers 20 unrelated subscriptions with no per-subscription attribution, and one `heartbeat` covers 10 timers, so a single silent timer among ten is invisible to any config the schema can express. Making each trigger its own component does not fix it — `cloud_RoleName` is per-process, so 30 components would each carry the same `error-logs`/`heartbeat` query (30 duplicate findings per exception) and the design-for-diagnosis property "per-component role name matches `monitoring.yml` `name`" becomes unsatisfiable by construction. This is exactly the class of gap 0039 shipped a schema early in order to surface, and it must be settled before [FEAT-2026-0040](roadmap-archive.md#feat-2026-0040) builds adapters against the contract.

**Goal.** Separate the axes. Component stays the deployment and attribution unit; checks gain a `targets` list that is the enumeration unit — `dlq` targets carry `subscription` (what the harvester queries) plus `function` (what a human diagnoses by), `heartbeat` targets carry a name plus optional cron and IANA timezone, and `error-logs`/`http-5xx` reject targets because they are role-name keyed and genuinely component-scoped. Gate 1 lands the schema, the structural validation, the migration of every shipped YAML surface, the contract flip that makes `targets` required on `dlq`, and the `queue-stalled` check type (issue #247 — a wedged consumer produces no dead-lettered message, no missed heartbeat, and no error log, and `invariant` cannot see it because queue depth is a broker coordinate a telemetry query cannot reach). Gate 2 re-keys component discovery onto *deployment* evidence (Helm chart, compose service, Dockerfile) with trigger registrations demoted to evidence of a component's type, adds the fixture whose single deployable carries N triggers, and generates target lists mechanically.

**Benefits.** Per-subscription DLQ attribution and per-schedule heartbeat become expressible, so a dead-lettered message on one of 20 subscriptions is a distinct finding rather than one undifferentiated bucket. FEAT-2026-0040's adapter interface gets a machine-checkable answer to "do I enumerate per component or per target" before any adapter exists. And the sequencing keeps its promise from 0039: the schema absorbs the correction, so the harvester stays purely additive.

**Ordering.** Issue #246 (`_ENV_VAR_NAME_RE` rejects the `Section__Key` env-var spelling) lands **first**, as a standalone bug fix — it touches the same validator this feature rewrites, and the reverse order would rebase a bug branch onto a substantially changed file.

**Scope boundary — recorded decisions, deliberately not built.** Per-target dials (multiplies the trust surface; nothing observed motivates it — dials stay per-component). The `environments` × `components` cross-product, where the schema asserts every component exists in every environment (acknowledged limitation; a different axis, and bundling it would double the blast radius of a breaking change). Issue #248, deployment-regression detection on 4xx codes (verdict: the no-metrics boundary holds; `invariant` is not the sanctioned route to rate-based detection). And fingerprinting stays 0040's — but **0040's fingerprint model must include the target key**, or 20 DLQ targets collapse into one issue and the attribution this feature pays for is lost at the last step.

**Gate 1 — shipped.** Five work units `done` (one, `T03H`, inserted mid-gate). Checks carry a `targets[]` list; the validator enforces the axis per check type — **required** on `dlq` and `queue-stalled`, optional on `heartbeat` and `invariant`, **rejected** on `error-logs` and `http-5xx`. `queue-stalled` joined the check-type enum (issue #247), taking `CHECK_TYPES` from five to six. Every shipped YAML surface was migrated (both `monitoring.yml.example` copies, both `monitoring.overrides.yml.example` copies, both `derive-monitoring/SKILL.md` copies) before the contract flipped, so each intermediate state stayed green — expand → migrate → contract, ordered that way because a flip-first ordering is unsatisfiable under the preflight baseline probe. Substantive spend **$11.94** against $11.00 as drafted (+8.6%); the whole overrun is one WU's three wasted attempts, traced to a migrate criterion scoped to a sample rather than a sweep. **The `targets`-required flip on `dlq` is a breaking schema change** — no live consumer needs migrating (the only config drafted against this schema is uncommitted), and the validator's finding message names the fix inline. Full enumeration and the deferred-verification list are in the feature's `RETROSPECTIVE.md`.

**Gate 1 deliberately did not prove** that `/derive-monitoring` emits 1 component with N targets for a deployable carrying N triggers. The schema can now express the right answer; discovery still cannot produce it — `discover_components` keys on trigger attributes and returns one component per trigger. That is gate 2, along with the fixture whose single deployable carries N triggers and the claim (confirmed only against a repo outside this tree) that every target coordinate is mechanically extractable.

**Gate 2 — shipped.** Four work units `done`, each on its first attempt, no escalations, **$4.43 against $12.00 planned**. `discover_components` is re-keyed onto *deployment* evidence: a component exists because a deployment artifact names it within a `scope_prefix`, and a trigger registration is evidence of that deployable's type and the source of its target list — never a component in its own right. `http_serving` and `message_consuming` are now derived from matched triggers instead of hand-declared, and the emitted record carries `subscriptions` and `schedules`. `suggest_checks` fans `schedules` into per-schedule `heartbeat` targets, closing the last half of the motivating defect — a single silent timer among several is now expressible. A third fixture stack (one deployable, **3** subscriptions and **2** schedules) makes the definition of done a test: `TestOneDeployableManyTriggers` asserts one component, 3 `dlq` targets, 2 `heartbeat` targets, and zero validator findings on the rendered YAML. The `derive-monitoring` skill's Step 1, Seams table, and `PROMPT.md` were rewritten to match, canonical copy first and propagated by `scripts/sync-scaffold.sh`. `invariant`'s accidental permissive `targets` fall-through became a decision — **rejected**, because `fingerprint_by` is already that check type's enumeration key and permitting both would hand FEAT-2026-0040's fingerprint model two competing keys.

**Outcome: the defect is fixed.** `/derive-monitoring` run against a repo whose single deployable carries N triggers now emits **1 component with N targets**, not N components — the 30-to-2 divergence that motivated the feature. Per-subscription DLQ attribution and per-schedule heartbeat are expressible in the schema, enforced by the validator, and produced by discovery.

**Issue #245 — resolved by this feature.** *"`monitoring.yml`: component is the wrong axis for per-subscription DLQ and per-schedule heartbeat — checks need targets."* Both axes are now separate: `component` stays the unit of deployment and attribution, `targets` is the unit of failure-artifact enumeration. Close #245 on merge, with one carry-over noted below.

**Issue #247 — resolved by this feature** (gate 1, `T04`). *"add a `queue-stalled` check type — a wedged consumer is invisible to `dlq`, `heartbeat`, and `invariant` alike."* `queue-stalled` is in `CHECK_TYPES`, carries `targets` **required from birth**, and is exercised by the shipped example and the docs table. Close #247 on merge.

**Carry-over from #245, and it is the one thing that can silently undo this feature.** The issue's claim that every target coordinate is *mechanically extractable from real code* is confirmed only against a repo outside this tree; a fixture authored inside gate 2 is evidence the algorithm fans a trigger table into a target list, not evidence that real repositories are shaped that way. Verifying it needs **one post-merge operator run of `/derive-monitoring` against a real repo whose single deployable carries ≥3 subscriptions and ≥2 schedules** — the same operator step FEAT-2026-0039 recorded for its own skill. That one run also discharges the second deferral (that the *skill*, executed end-to-end by an agent, reproduces what the reference implementation is tested to do). Both are enumerated with exact re-run conditions in the feature's `RETROSPECTIVE.md` § *Hedged follow-up record*.

**Costs, honestly.** Feature actual **$42.82** against `PLAN.md`'s as-drafted **$34.00** (+25.9%), excluding the terminal close. The plan was never re-baselined, deliberately. The variance does not blend: all nine implementation WUs came in **$16.37 against $25.00 (−34.5%)**, while the two gate-1 closing WUs came in **$26.45 against $10.00 (+164.5%)** — a floor `planning-discipline.md` §5 supplied, not a judgement any author made. Third feature to pay for it; tracked as **issue #260** with the two concrete file targets (§5 itself and `WU.template.md`'s comment quoting it) named in the retrospective's `## Planning-floor revision`. Gate 1's one real defect — a migrate criterion scoped to a sample rather than a sweep — cost $5.26.

**Note for [FEAT-2026-0040](roadmap-archive.md#feat-2026-0040), restated.** **Fingerprints must include the target key.** Enumeration runs over `check["targets"]` when present and over the component otherwise, and a finding derived from a target must fingerprint on that target's coordinates (`subscription` + `function` for `dlq`, `name` for `heartbeat`) — not only the component name. `invariant` is the deliberate exception: `targets` is rejected there, so 0040 reads `fingerprint_by` for `invariant` and `targets` for everything else. Without this, 20 DLQ targets collapse into one issue with every gate green, and the attribution this feature paid two gates for is lost at the last step.

**Status: done.** Terminal close ran with verdict `met_locally`; the consumer-visible contract-change list (15 items across both gates; items 1, 3, and 11 breaking, including the `patterns` table contract) was acknowledged by the operator at the terminal review checkpoint, and FU-1 and FU-3 were then discharged post-close by running `/derive-monitoring` against the downstream .NET backend that originated the feature — **33 trigger registrations resolved to 2 components**, every target coordinate extracted mechanically, drafted config validating clean. Verdict upgraded to `met`. FU-2 stays open by design: it asserts about FEAT-2026-0040's adapter interface and is 0040's acceptance criterion, not this feature's.

<a id="feat-2026-0060"></a>
## FEAT-2026-0060 — Driver-local event schema registry: sanction the three unsanctioned event types

**Why.** The loop driver emits `gate_reached` and `attempt_outcome` on every run, and FEAT-2026-0053/T04 adds `arm_predicate_evaluated`. None of the three appear in the envelope `event_type` enum in `specfuse/loop/data/schemas/event.schema.json` (a closed 28-entry list this repo does not own), and none have a per-type payload schema — `PER_TYPE_SCHEMA_DIR` holds four schemas, all core-orchestrator types vendored from another repo. The gap is invisible today only because the driver's emit path (`build_event` / `flush_events` in `loop.py`) never invokes the validator: `validate_event.py` is a standalone CLI. So every driver-emitted event is unvalidated in practice, and anyone who does run `validate_event.py` over a real `events.jsonl` gets failures on the driver's own output. FEAT-2026-0053/T04 blocked on discovering this and was unblocked by narrowing its scope, deliberately deferring the question rather than answering it inside a shadow-mode WU.

**Goal.** Decide and implement where driver-local event schemas live, then bring all three types into conformance so `validate_event.py` passes over a real driver-produced `events.jsonl`. Two candidate shapes, to be chosen as part of this feature: (a) extend the vendored registry and envelope enum in the core repo, keeping one registry — correct but cross-repo; or (b) sanction an explicitly-named loop-local schema tier, with manifest entries in the scaffold sync script and its orphan-file test, leaving the core enum alone. Also decide whether emit-time validation should be wired into `build_event` / `flush_events`, or whether `validate_event.py` stays a CI/manual check — an unvalidated emit path is what let three types drift unnoticed.

**Benefits.** The driver's own event stream becomes machine-checkable, which every downstream consumer (`gate-status`, `learnings-suggest`, the harvester, FEAT-2026-0053's shadow telemetry) implicitly assumes today. Removes a standing trap where a WU touching events discovers the gap mid-attempt and blocks, as T04 did at a cost of one wasted 210-second attempt.

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
