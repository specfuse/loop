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
| FEAT-2026-0011 | Scoring framework for roadmap features      | planned  | `.specfuse/features/FEAT-2026-0011-scoring-framework/` | — |
| FEAT-2026-0012 | Closing-WU deliverable guard (folded into 0015) | abandoned | — | [→ archive](roadmap-archive.md#feat-2026-0012) |
| FEAT-2026-0013 | CI integration_workspace cleanup race fix   | done     | `.specfuse/features/FEAT-2026-0013-ci-workspace-race-fix/` | [→ archive](roadmap-archive.md#feat-2026-0013) |
| FEAT-2026-0014 | GitHub Actions Node.js 20 deprecation bump  | done     | `.specfuse/features/FEAT-2026-0014-gha-node20-bump/` | [→ archive](roadmap-archive.md#feat-2026-0014) |
| FEAT-2026-0015 | Closing-ceremony restructure + hollow-pass guard | done     | `.specfuse/features/FEAT-2026-0015-closing-ceremony-restructure/` | [→ archive](roadmap-archive.md#feat-2026-0015) |
| FEAT-2026-0016 | Re-arm contract + audit trail               | planned  | — | — |
| FEAT-2026-0017 | Close-WU wiring-race guard                  | active   | — | — |

Status: `planned` → `active` → `done` (or `abandoned`).


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

**Status: planned.** Depends on FEAT-2026-0010 landing first (table
shape needs to be ready to carry the new column shape).


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

## FEAT-2026-0016 — Re-arm contract + audit trail

**Why.** FEAT-2026-0013 burned $13.50 across 5 dispatches (v1, v2,
v3-attempt-1, v3-attempt-2, v3-attempt-3) before the fix held. Each
re-arm required the operator to manually compute cumulative
`historical_cost_usd`, `historical_duration_seconds`, etc., and write
them into WU frontmatter to preserve audit. The driver does NONE of
this; the `/unblock-wu` skill spec mentions the pattern but does not
automate it. /gate-status reports "this WU is blocked" but does NOT
surface "this WU has been re-armed 2 times". The audit signal for
re-arm history is invisible to every other skill.

Failure modes the gap surfaces:

- Operator under-estimates feature cost because each /unblock-wu
  resets `cost_usd: 0` and visible `attempts: 0`. FEAT-2026-0013's
  $13.50 was only visible by manually summing five events.jsonl
  blocks plus three commit messages.
- Re-arm rationale is captured in commit messages (FEAT-2026-0013
  history) but not in frontmatter — so /gate-status can't surface
  "this is re-arm 3; prior reasons: gh-auth, gpg-config, scope-miss".
- Methodology drift: the `historical_*` field naming was invented
  ad-hoc during 0013; no template, no lint, no driver awareness.

**Goal.** Standardize the re-arm contract end-to-end.

WU frontmatter additions:

- `re_arm_count: <int>` — number of times this WU has been re-armed
  from `blocked_human` (or `done` post-CI-fail) back to `pending`.
  Initialized 0; incremented by driver on next dispatch after an
  `/unblock-wu` write.
- `re_arm_history: [{timestamp, prior_status, prior_attempts,
  prior_cost_usd, prior_duration_seconds, reason}]` — append-only
  list. Operator (or /unblock-wu skill) writes one entry per
  re-arm.
- `cumulative_cost_usd`, `cumulative_duration_seconds`,
  `cumulative_input_tokens`, `cumulative_output_tokens` —
  cross-attempt sums INCLUDING all re-arms. Driver maintains;
  /unblock-wu does not touch.

Driver changes:

- On `/unblock-wu` re-arm write (detected: WU was `blocked_human`,
  now `pending` with `re_arm_count` incremented), driver fold prior
  attempt's `cost_usd` / `duration_seconds` into the cumulative
  fields BEFORE resetting `cost_usd: 0`.
- New event `re_arm_dispatched` written to `events.jsonl` carrying
  re-arm number + rationale.
- `task_started` event carries `re_arm_count` so dashboards can
  group attempts across re-arms.

Skill changes:

- `/unblock-wu` prompts for one-line re-arm rationale (already
  recommended in the skill spec; now MANDATORY). Writes the new
  `re_arm_history` entry.
- `/gate-status` surfaces "re-arm N (last reason: ...)" prominently
  on any WU with `re_arm_count > 0`.
- `/wrap-feature` executive recap (§3 plan-adherence) reads
  `re_arm_count` per WU instead of grep'ing events.jsonl.

**Scope OUT.**

- Changing the `/unblock-wu` decision vocabulary (re-arm /
  abandon / skip stays as-is).
- Driver auto-deciding when to abandon a WU after N re-arms
  (would be a separate retry-ceiling feature).
- Cross-feature cost rollup — that belongs to FEAT-2026-0011
  (scoring framework consumes per-feature cumulative cost).

**Verification.** Recursive: dogfood this feature's own close
ceremony exercises the new frontmatter fields. Tests cover the
driver's cumulative-fold logic, /unblock-wu's mandatory-rationale
prompt, and /gate-status's re-arm surfacing.

**Status: planned.** Independent of FEAT-2026-0015. Can land
in parallel. Probably small (one substantive WU for the driver
fold-logic, one for /unblock-wu + /gate-status updates, one for
WU template/lint changes).

## FEAT-2026-0017 — Close-WU wiring-race guard

**Why.** FEAT-2026-0015/T06 shipped `fire_terminal_flips` driver-side
+ wired it into the close path. Wiring looked correct on inspection
and on test (T06's own tests). The recursive dogfood (G2-CLOSE) ran
clean, wrote `verdict: met` to its WU frontmatter, and the driver
flipped PLAN.md to `done`. But the terminal gate stayed
`awaiting_review` and the roadmap row stayed `active`. Auto-archive
never fired.

Root cause: `wu.verdict` was populated by `load_wu` BEFORE dispatch
(value: `None`). Agent wrote `verdict: met` to the frontmatter DURING
dispatch. The driver's check at the close-path squash compared the
IN-MEMORY `wu.verdict` (still `None`) against the threshold. Check
returned False. `close_wu_for_terminal` stayed `None`.
`fire_terminal_flips` never invoked.

Race between WorkUnit-in-memory and agent's frontmatter write.

None of today's hollow-pass guards (FEAT-2026-0008's three +
FEAT-2026-0015/T07's four) catch this:

- Zero-token guard: T06 ran productively.
- `files_changed` guard: T06 listed `loop.py` + the test file; both
  changed.
- Smoke-import guard: `fire_terminal_flips` symbol existed +
  imported.
- Closing-deliverable guards (T07): T07 didn't model wiring-race —
  it asserts on file existence and content shape post-pass, not on
  driver-state invariants that should fire as a CONSEQUENCE of the
  WU's effect.

**Goal.** Add a new guard category for **post-pass invariants**: a
WU passes verify + smoke + files_changed, but the LIVE side effect
it was supposed to produce in the driver / fs DIDN'T happen.

Type-keyed post-pass invariant table (extends T07):

- **`close` (type)** — after squash, the driver must observe one of:
  (a) terminal gate → `passed`, roadmap row → `done`, auto-archive
  trail (when `verdict: met`); (b) PLAN.md stays `active` (when
  verdict is hedged). If neither holds and `verdict: met` is in the
  WU's post-squash frontmatter, hollow-pass: emit
  `attempt_outcome: post_pass_invariant_failed` naming the missing
  side effect, reset, re-attempt within budget.
- **`implementation` WUs that target driver code** — when a WU
  declares `produces_driver_helper: <symbol>` in frontmatter, the
  driver verifies the helper is INVOKED from the right call path
  via grep, not just defined. Symbol-existence alone is the
  hollow-pass surface FEAT-2026-0007/T04 already lost on; T06 lost
  on a more subtle variant (helper invoked from path that's never
  reached due to stale in-memory state).

**Scope IN.**

- Driver-side post-pass invariant check, type-keyed.
- New WU frontmatter field `produces_driver_helper: <symbol>` or
  similar, optional, with lint warning when an `implementation`
  WU's body claims to wire something into the driver but doesn't
  declare the symbol.
- Tests cover: T06's exact failure mode reproduced as a
  regression test; positive case where flips fire cleanly.

**Scope OUT.**

- Re-architecting WorkUnit-in-memory ↔ frontmatter sync. T06's
  fix (re-read frontmatter post-squash) is sufficient for the
  verdict path; broader sync is unwarranted.
- Wiring-race detection beyond the close path — only `close` WUs
  exhibit the load-time-vs-dispatch-time gap because they're the
  only ones whose driver behavior depends on agent-written
  frontmatter.

**Verification.** Recursive: this feature's own G1-CLOSE (single-
gate, new contract) MUST exercise the new guard. Regression test
reproduces FEAT-2026-0015/T06 G2-CLOSE bug pattern.

**Status: planned.** Single gate, ~2 substantive WUs (driver guard
table + frontmatter field + lint) + 1-WU close. Estimated $3-5.


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
