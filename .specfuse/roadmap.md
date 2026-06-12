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

| Feature ID     | Title                                       | Status   | Folder |
|----------------|---------------------------------------------|----------|--------|
| FEAT-2026-0002 | Driver run-loop test coverage               | done     | `.specfuse/features/FEAT-2026-0002-driver-test-coverage/` |
| FEAT-2026-0003 | GitHub feature-pick for the loop            | done     | `.specfuse/features/FEAT-2026-0003-github-feature-pick/` |
| FEAT-2026-0004 | Single-driver working-tree lock             | done     | `.specfuse/features/FEAT-2026-0004-driver-lock/` |
| FEAT-2026-0005 | Combined close for single-gate features     | done     | `.specfuse/features/FEAT-2026-0005-combined-close/` |
| FEAT-2026-0006 | WU execution-time tracking                  | done     | `.specfuse/features/FEAT-2026-0006-wu-duration/` |
| FEAT-2026-0007 | Dispatch cost controls                      | done     | `.specfuse/features/FEAT-2026-0007-dispatch-cost-controls/` |
| FEAT-2026-0008 | Driver completeness-guard                   | done     | `.specfuse/features/FEAT-2026-0008-driver-completeness-guard/` |
| FEAT-2026-0010 | Roadmap restructure: add + archive          | planned  | `.specfuse/features/FEAT-2026-0010-roadmap-restructure/` |
| FEAT-2026-0011 | Scoring framework for roadmap features      | planned  | `.specfuse/features/FEAT-2026-0011-scoring-framework/` |
| FEAT-2026-0012 | Closing-WU deliverable guard                | planned  | — |
| FEAT-2026-0013 | CI integration_workspace cleanup race fix   | active   | `.specfuse/features/FEAT-2026-0013-ci-workspace-race-fix/` |
| FEAT-2026-0014 | GitHub Actions Node.js 20 deprecation bump  | done     | `.specfuse/features/FEAT-2026-0014-gha-node20-bump/` |

Status: `planned` → `active` → `done` (or `abandoned`).

## FEAT-2026-0002 — Driver run-loop test coverage

**Why.** This repo's own `code` coverage gate ships at `--fail-under=35`,
deliberately below the methodology's ≥ 90% default
(`.specfuse/verification.yml`). The gap is concentrated in the orchestration
paths of `loop.py`: `run()` (the attempt loop and gate-completion flow),
`squash_commit`, `log_event`, `find_feature`, `load_graph`, `load_wu`,
`require_git_ready`, the `dispatch` subprocess invocation, and the
`blocked_human` escalation flow end-to-end. The parse/decide/verify core is
already covered by the existing 27 unit tests.

**Goal.** Land integration tests that exercise the run-loop without
spawning a real `claude -p`, then raise this repo's `--fail-under` floor
toward 90. Specifically:

- `run()` happy path (a single passing WU lands a squashed commit and
  flips status to `done`).
- `run()` failed-then-passed path (attempt 1 fails verify, attempt 2
  passes; assert the failure note is written, the attempt counter is
  written to frontmatter, and only one squashed commit ends up on HEAD).
- `run()` agent-reported-blocked path (assert single attempt, `blocked_human`
  status, `human_escalation` event with `agent_reported_blocked` reason,
  `git reset --hard` ran).
- `run()` spinning-detection path (three failed verify cycles → `blocked_human`,
  `human_escalation` with `spinning detected` reason).
- `squash_commit` against a temp git repo: produces one commit with the
  correct trailer, folds away any commits the (stub) agent made.
- `log_event` round-trip: appends a single line of valid JSON with the
  expected fields.
- `find_feature` with zero/one/multiple actives.
- `require_git_ready` happy + missing-commits + non-repo (already covered
  manually after the original fix; promote to unit tests).

**Gate 1 (passed).** Single-gate feature, five substantive WUs:

- **T01** — `tests/test_loop_orchestration.py` raised `loop.py` from 87%
  to ≥ 95% by covering `squash_commit` soft-reset, `find_feature` 0/1/many,
  `require_git_ready`, dispatch error arms, lock contention, gate-budget
  halt, and `main()` argparse. Landed in 2 attempts (high effort).
- **T02** — `tests/test_validate_event.py` raised `validate-event.py` from
  0% to 97% by covering schema accept/reject and a real-event regression.
  First attempt blocked (AC 4 polarity error: the spec asserted the schema
  *accepts* a driver-emitted event, but the orchestrator's schema
  intentionally rejects `source: "driver"`); re-arm inverted the AC and
  added `jsonschema` to dev deps. Landed in 1 attempt post-re-arm.
- **T03** — `tests/test_lint_plan_errors.py` raised `lint_plan.py` from
  79% to 99% by covering the 11 named error arms + a regression on the
  bundled FEAT-2026-0001 fixture. First dispatch spun 3 attempts on a
  ruff F401 (`import sys` unused); re-arm added pre-flight lint discipline.
  Landed in 1 attempt post-re-arm.
- **T04** — `tests/test_miniyaml_negative.py` extended raised `_miniyaml.py`
  from 87% to 100% with escape-handling and indent-error fixtures. Landed
  in 1 attempt.
- **T05** — `.specfuse/verification.yml` and `scripts/smoke-test.sh`
  flipped from `--fail-under=70` to `--fail-under=90`; deviation comment
  removed. Landed in 1 attempt (45 s).

Post-gate coverage: TOTAL = **97%** (was 78% at feature start), with each
targeted module at or above its per-WU threshold (`loop.py` 97%,
`validate-event.py` 97%, `lint_plan.py` 99%, `_miniyaml.py` 100%). The
two-site `--fail-under` floor (`.specfuse/verification.yml` +
`scripts/smoke-test.sh`) reads `=90` and matches the methodology default.
GATE-01 status: `passed`.

**Status: done.** `roadmap_goal` met — this repo's coverage floor now
matches the methodology default (≥ 90%), with measured TOTAL at 97% and
no module under 90%. See `RETROSPECTIVE.md §Feature-arc verdict`.

## FEAT-2026-0003 — GitHub feature-pick for the loop

**Why.** Teach the loop to adopt a feature dispatched by the Specfuse
Orchestrator — so an orchestrator can hand a feature to a component repo's loop
and the loop grinds it through its gate cycle — in addition to today's
locally-authored `.specfuse/features/` flow. Full brief:
[`docs/handoff-github-feature-pick.md`](../docs/handoff-github-feature-pick.md).

**Gate 1 (passed).** The read path: extended the loop's correlation-ID grammar
to admit orchestrated `INIT-YYYY-NNNN/FNN[/TNN]` IDs alongside `FEAT-…`
component-local IDs (rule + linter + tests); added
`.specfuse/scripts/gh_features.py`, a discovery script that lists a target
repo's `specfuse:feature` issues as feature candidates (injectable `gh` runner
for fully offline unit testing). Both implementation WUs completed in one
attempt with no escalations. GATE-01 status: `passed`.

**Gate 2 (passed).** The write/adopt path: `.specfuse/scripts/adopt_feature.py`
scaffolds a dispatchable loop-feature folder from a picked `specfuse:feature`
issue — PLAN.md frontmatter (including `source_issue_url` and `initiative` when
present), GATE-01/02 files, WU-01 seeded verbatim from the raw issue body, and
gate-1 closing WUs 90–93 with generic placeholder bodies. `gh_features.py`
widened by one line to expose issue `body`. The `/adopt-feature` interactive
skill wraps the script as a pick-list-then-adopt flow. Both implementation WUs
completed in one attempt with no escalations. GATE-02 status: `passed`.

**Gate 3 (passed).** Report-back and smoke: `Backend` seam widened with three lifecycle
hooks (`on_feature_start`, `on_gate_passed`, `on_feature_complete`) and a `make_backend(feat_fm)`
factory (T05); `GitHubBackend(Backend)` label-transition backend in `gh_backend.py` using the
canonical `state:ready → state:in-progress → state:done` scheme, factory selects it when
`source_issue_url` is present in PLAN.md frontmatter (T06); live smoke of `INIT-2026-0001/F06`
(`RestoManagerApp/Backend#287`) run out-of-loop by human operator — discovery, adopt, and
report-back all PASS, `#287` fully restored post-smoke (T07). **Finding:** the adopted folder
failed `lint_plan.py` because orchestrator issue bodies use `## ATX` headings; the linter only
recognised `**bold**`/plain. Fix delivered in gate 4. GATE-03 status: `passed`.

**Gate 4 (passed).** ATX-heading linter fix: broadened `lint_plan.py`'s mandatory-section
detector to a union pattern (`^(?:#+\s*|\**)`) that accepts both Markdown ATX headings
(`## Context`) and the existing bold-preamble (`**Context.**`) form (T08). The adopted
`INIT-2026-0001-F06-…` folder now passes `lint_plan.py` exit-0, and existing bold-headed WU
bodies remain clean (regression guard). GATE-04 status: `passed`.

**Status: done.** All four gates passed. All four pipeline mechanisms — discover, adopt,
report-back, lint-clean grind — are proven live against `RestoManagerApp/Backend#287`. The
`roadmap_goal` is met. See `RETROSPECTIVE.md §Feature-arc retrospective` and
`SMOKE-INIT-2026-0001-F06.md`.

## FEAT-2026-0004 — Single-driver working-tree lock

**Why.** Two `loop.py` drivers sharing one working tree clobber each other: the
driver's per-WU `git reset --hard` and `git checkout -B` are tree-global, so any
interleaving corrupts WU state and mixes commits across units. Observed during the
FEAT-2026-0003 dogfood: a sandboxed `ps` falsely reported the first driver as dead,
a second was launched, and competing resets produced commits mixing multiple WUs'
work plus contradictory WU statuses. True parallelism across features uses separate
`git worktrees` — each worktree has its own working tree and therefore its own lock.

**Gate 1 (passed).** Advisory lock on the working tree: `loop.py`'s `run()` acquires
a non-blocking exclusive `fcntl.flock` on `.specfuse/.loop.lock` before any
git-mutating call; a contending driver exits non-zero with a clear stderr message and
touches no git or WU/GATE state; the lock auto-releases on process exit including
SIGKILL (no stale-lock cleanup path). `--dry-run` is exempt (no mutation; inspecting
while a real run is active must stay allowed). `init.sh` adds the targeted
`.specfuse/.loop.lock` gitignore line to every destination repo it sets up (idempotent,
without ignoring the rest of `.specfuse/`). Both this repo's `.gitignore` and every
`init.sh`-initialized repo ignore the lock file. Tests cover kernel-level exclusion
and release-on-close without spawning a real `claude -p`. All six acceptance criteria
met in one attempt ($0.89, ~5 min). GATE-01 status: `passed`.

**Status: active.** Single-gate feature; closing sequence in progress.

## FEAT-2026-0005 — Combined close for single-gate features

**Why.** The four closing ceremonies (retrospective → lessons → docs → plan-next)
cost four dispatches — including an Opus `plan-next` — even on a one-WU feature
where `plan-next` is terminal boilerplate with no next gate to forward-design.

**Gate 1 (passed).** A new `close` WU type collapses all four closing ceremonies
into one session, accepted by `lint_plan.py` and `loop.py` only for single-gate
features (multi-gate features keep the four-WU sequence, where forward-design
`plan-next` earns its cost). The linter enforces the single-gate constraint and
rejects `close` on any feature with two or more gates. `loop.py` maps `close` to
the `plannext` verification gate set (structural lint on the feature post-close),
and treats a passing `close` WU as completing the gate. `CORRELATION_ID_RE` gained
a `CLOSE` segment so `G1-CLOSE`-style correlation IDs pass validation. Three tests
cover: lint accepts single-gate close, rejects multi-gate close, and still passes
the four-WU sequence (regression). All acceptance criteria met in one attempt
($1.23, ~7 min). GATE-01 status: `passed`.

This feature itself closes with the four-WU sequence — the `close` type does not
exist when this feature's driver loads `loop.py`. FEAT-2026-0006 is the first
feature to use the new `close` WU.

**Status: done.** Single-gate feature. FEAT-2026-0006 is the first feature to use
the new `close` WU.

## FEAT-2026-0006 — WU execution-time tracking

**Why.** The loop already captured cost per WU; wall-clock execution time was missing.
Adding duration alongside cost gives operators a complete picture of WU weight (both
money and time) in `events.jsonl` and the WU frontmatter.

**Gate 1 (passed).** `loop.py` measures each attempt's wall-clock time with
`time.monotonic()` (start at dispatch, stop after verification) and records
`duration_seconds` per-attempt in `events.jsonl`'s `attempts_usage` list. Cumulative
`duration_seconds` (rounded to 3 decimals) is written to the WU's frontmatter at
outcome time (PASS / BLOCKED / SPINNING), independent of the `cost_tracking` setting.
`WU.template.md` documents the field as driver-owned. Tests cover per-attempt capture,
cumulative summing across a failed-then-passed sequence, frontmatter write, and
`cost_tracking: false` independence. All acceptance criteria met in one attempt (~$1.00,
~5 min). GATE-01 status: `passed`.

This feature is also the first live use of FEAT-2026-0005's `close` WU type —
closing in a single dispatch rather than the four-WU sequence. The combined close
ceremony worked correctly.

**Status: done.** `roadmap_goal` met — the loop records each work unit's wall-clock
execution time alongside the cost it already captures. See
`RETROSPECTIVE.md §Feature-arc retrospective`.

## FEAT-2026-0007 — Dispatch cost controls

**Why.** Per-WU dispatch cost was growing with no lever to control it. Three
mechanisms were missing: model-family aliasing (so WU specs don't pin model
versions), effort-tier control (so cheap work doesn't burn expensive thinking
budget), and a retry ladder that escalates compute rather than repeating the same
failed attempt.

**Gate 1 (closing).** Substantive delivery:

- **T01** — Model family aliases: `sonnet`/`opus`/`haiku` in WU frontmatter resolve
  at dispatch to the latest model in that family; full model IDs still accepted to
  pin a specific release.
- **T02** — `effort:` field (`low`/`medium`/`high`/`xhigh`/`max`) wired to
  `claude -p --effort`; default `medium` when field is absent. `WU.template.md`
  documents the field as author-controlled.
- **T03** — Tier-gated caveman preamble: `low`/`medium` effort WUs receive a
  terseness directive in the dispatched session; `high`+ do not.
- **T05** — Failure-note size cap: 200 lines / 8000 characters with head+tail
  truncation and a plain-ASCII truncation marker.

**T04 gap.** The retry escalation ladder (T04) was declared complete and driver
verification passed, but no production code was written. Required symbols
(`EFFORT_LADDER`, `effort_for_attempt`, `terseness_for_attempt`) are absent from
`loop.py`. The `code` gate passed because no new tests were registered and existing
tests make no assertion about absent functions. This failure mode is documented in
`RETROSPECTIVE.md`; two `[FEAT-2026-0007/G1-LESSONS]` entries in `LEARNINGS.md`
cover the completeness-guard and function-existence verification gaps. T04's
implementation was deferred to Gate 2 (T08H).

**Gate 2 (closing sequence in progress).** Substantive delivery:

- **T06** — Defaults-by-WU-type policy: `MODEL_BY_TYPE` and `EFFORT_BY_TYPE`
  tables in `loop.py` give every WU type a model and effort default; `model:` and
  `effort:` frontmatter fields become optional overrides rather than required
  fields. `lint_plan.py` updated to accept absent `model:`. `WU.template.md`
  frontmatter comments updated. Haiku guidance added to
  `.specfuse/skills/authoring-work-units/SKILL.md`. Landed in one attempt.
- **T07** — Per-gate cost budget: `cost_budget_usd` in `GATE-NN.md` sets a
  cumulative cost ceiling; `gate_budget_usd` / `gate_spent_usd` helpers in
  `loop.py`; halt-between-WUs semantics (current WU runs to terminal outcome,
  brake fires before the next dispatch — including closing-sequence WUs).
  `GATE.template.md` documents the field. Landed in one attempt.

**T08H / T08 gap.** T08H (re-land T04's retry-ladder code) and T08 (telemetry:
`resolved_model`, `cache_hit_rate`, `gate_summary`) both repeated T04's failure
mode: each session billed 0 input/output tokens, the driver committed only the WU
frontmatter status flip, and `status: done` advanced the dependency frontier
despite no symbols landing. After Gate 2: `EFFORT_LADDER`, `effort_for_attempt`,
`terseness_for_attempt`, `cache_hit_rate`, and `gate_summary` are absent from
`loop.py`. The retry escalation ladder and gate-level telemetry are undelivered.
Two `[FEAT-2026-0007/G2-LESSONS]` entries in `LEARNINGS.md` cover the 0-token
session gap and the limit of agent-side safeguards.

**Status: done.** Four `roadmap_goal` levers (model alias, effort tier, terseness,
per-gate budget) all landed and importable; type-default policy layered on top.
T04 retry ladder and T08 telemetry deferred — three reland attempts (T04, T08H, T08)
all silently no-op'd via the same 0-token-session failure path. The fix is
driver-side (refuse-commit on 0 tokens / empty diff / failed smoke-import), not
spec-side, so it belongs in a successor feature rather than a Gate 3. **Strongly
recommended next feature: FEAT-2026-0008 "Driver completeness-guard."** See
`RETROSPECTIVE.md §Feature-arc verdict` for the full terminal rationale and the
G4-LESSONS three-test analysis.

## FEAT-2026-0008 — Driver completeness-guard

**Why.** FEAT-2026-0007 shipped four cost-control levers but T04 / T08H / T08
all reported `status: done` while landing no production code (hollow passes,
each via a 0-token session that the driver committed because the WU
frontmatter status flip was the only staged change). Agent-side safeguards
(smoke-import AC, completeness escalation triggers) are bypassed when the
agent session crashes or produces 0 tokens. The fix is driver-side.

**Gate 1 (passed).** Three independent driver-side guards landed in one
attempt each, all wired into the attempt loop in `run()`:

- **T01** — Zero-token attempt guard: `is_zero_token_attempt(usage)` at
  `loop.py:711`, called at `loop.py:885` before RESULT-block parse. A
  session billing `input_tokens: 0` is treated as a failed attempt; three
  in a row escalate to `blocked_human` with `reason: "all_attempts_zero_token"`.
  `usage is None` (cost tracking disabled) does NOT trigger the guard.
- **T02** — `files_changed` diff guard: `verify_files_changed(result,
  head_before)` at `loop.py:622`, called at `loop.py:901` between
  `parse_result_block` and `squash_commit`. Any agent-claimed `files_changed`
  path that does not differ from HEAD fails the attempt before squash.
  Empty / absent `files_changed` opts out (pre-existing-WU compatibility).
- **T03** — WU-Verification smoke-import runner: `extract_smoke_imports` /
  `run_smoke_imports` at `loop.py:669` / `:684`, called at `loop.py:1110`-`:1112`
  between successful verify+squash and the status-flip-to-done. Conservative
  import-form regex only (no free-form `python3 -c` execution). A failing
  smoke check rolls back the squash via `git reset --hard <head_before>`
  and counts as a verification failure.

All three landed in one attempt each (T01 $2.61 / T02 $1.75 / T03 $1.66,
~17 min total). GATE-01 status: `passed`.

**Status: done.** `roadmap_goal` met — all three guards present in `loop.py`
AND wired into the attempt loop in `run()`. Per the FEAT-2026-0007 verdict's
mandatory recommendation, any one of the three would have caught T04/T08H/T08;
all three together close the gap structurally. The deferred FEAT-2026-0007
work (T04 retry escalation ladder, T08 telemetry) can now be relanded under
FEAT-2026-0009 — a third silent-no-op is structurally impossible. See
`RETROSPECTIVE.md §Feature-arc verdict` for the audit and the recursive
close-ceremony check.

## FEAT-2026-0010 — Roadmap restructure: add + archive

**Why.** The roadmap file currently mixes detail sections for every
feature — done, abandoned, planned, active — into one document. As
done features accumulate, `pick-feature` (and any other reader of the
roadmap) loads ~70% irrelevant context every invocation. The file has
also been edited entirely by hand; there is no skill to append a new
planned entry, and no mechanism to graduate detail sections out of the
hot file when work completes.

**Goal.** Land the structural changes that let the roadmap stay lean
without losing history:

- Split `.specfuse/roadmap.md` so detail sections cover only `planned`
  and `active` features; move `done` and `abandoned` detail sections
  to a new `.specfuse/roadmap-archive.md` (table rows stay in the
  main file with a link to the archive anchor).
- Migrate FEAT-2026-0003..0008's existing detail sections to the
  archive as the first dogfooding pass.
- Ship a `roadmap-add` skill: interactive append of a new planned
  row + detail section, auto-picking the next FEAT-YYYY-NNNN ID,
  honoring reserved IDs in repo history.
- Ship a `roadmap-archive` skill: given a FEAT-ID (or auto-detected
  done/abandoned rows with detail still inline), cut the detail
  section and append to the archive, leaving the table row intact.
- Hook the driver: when `loop.py` flips `PLAN.md` status to
  `complete`, suggest (or auto-fire) `roadmap-archive` for that
  feature. Manual-first cut; auto a follow-up if the manual flow is
  reliable.

**Benefits.** Reduce hot-path context for every roadmap reader.
Make adding a planned entry a one-command operation, removing the
friction that causes ad-hoc shorthand to leak into the table.
Preserve full history in a file that's never loaded on the hot
path. Foundation for FEAT-2026-0011, which adds new columns and
scoring data the table can't carry while it's still hand-edited.

**Verification.** `pick-feature` invoked against the restructured
roadmap loads strictly less context than today (measure: line count
of the file it reads). `roadmap-add` writes a row + detail section
that round-trips through the archive flow without losing data.
`roadmap-archive` is idempotent (running twice does not duplicate
the archive entry). Migration of 0003..0008 leaves the table
unchanged in shape; archive contains 6 detail sections matching
the originals byte-for-byte except for the new archive header.

**Status: planned.** Folder exists at
`.specfuse/features/FEAT-2026-0010-roadmap-restructure/` (PLAN.md,
GATE-01.md, GATE-02.md, 4 substantive WUs, 4 closing WUs). Land
before FEAT-2026-0011 (scoring needs the restructured table to
carry the new columns).

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

## FEAT-2026-0012 — Closing-WU deliverable guard

**Why.** FEAT-2026-0008 closed the hollow-pass surface for
`type: implementation` WUs via three driver-side guards (zero-token,
`files_changed` diff, smoke-import). Closing-sequence WUs
(`plan-next`, `close`, `retrospective`, `lessons`, `docs`) have the
same hollow-pass surface and none of the three FEAT-2026-0008 guards
catch them:

- Zero-token misses: the agent billed real tokens.
- `files_changed` diff guard misses: per FEAT-2026-0008/T02, empty or
  absent `files_changed` opts out, and closing WUs typically emit
  empty lists.
- Smoke-import misses: closing WUs produce prose deliverables, not
  importable symbols.

Observed live in an external (IaC) project's feature dogfood: a
terminal-gate `plan-next` WU billed `cost_usd: 0.90`,
`output_tokens: 4389`, emitted RESULT `status: complete`, and the
driver flipped `attempts: 1` / `status: done` while the agent had
never invoked `Write` / `Edit`: `GATE-NN-REVIEW.md` absent,
`PLAN.md status: active` unchanged, roadmap row unchanged. The
driver believed an honest RESULT block without confirmation.

Also encountered locally during FEAT-2026-0002/G1-CLOSE: the close
agent correctly flipped PLAN.md status, roadmap row, and wrote
RETROSPECTIVE.md — but only because the WU spec told it to. If the
agent had emitted PASS without writing, the driver would have
believed it and FEAT-2026-0002 would have closed hollow. The same
gap blocks reliable auto-progression of the roadmap row on feature
close (current behavior depends entirely on the close-agent
following the WU AC).

**Goal.** A driver-side guard, analogous in shape to FEAT-2026-0008's
three guards, that asserts type-keyed closing-deliverable existence
between successful verify+squash and the status-flip-to-done.
Type-keyed assertion table:

- `retrospective` → `<feature_dir>/RETROSPECTIVE.md` exists +
  size > N bytes (small floor, ~200).
- `lessons` → `git diff head_before -- .specfuse/LEARNINGS.md`
  shows ≥1 added line.
- `docs` → at least one file in `<feature_dir>` or
  `.specfuse/roadmap.md` shows a diff against `head_before`.
- `plan-next` → `<feature_dir>/GATE-<N>-REVIEW.md` exists +
  non-empty AND one of: (a) next gate's `work_units` non-empty
  in PLAN.md, (b) PLAN.md `status: done`, (c) roadmap row `done`.
- `close` → RETROSPECTIVE.md exists + non-empty AND LEARNINGS.md
  diff AND PLAN.md `status: done` AND roadmap row `done`.
- `implementation` → unchanged; FEAT-2026-0008's three guards
  already cover.

Failure rolls back via `git reset --hard head_before`, records an
`attempt_outcome` event with `outcome: "closing_deliverable_missing"`
naming the failed assertion, and counts as a verification failure
in the attempt loop — three in a row escalate to `blocked_human`.

**Verification.** New tests under `tests/test_loop_closing_guard.py`
covering negative case (agent emits PASS without writing the
type-keyed deliverable, guard fires, attempt fails) and positive
case (agent writes everything, guard passes). Recursive audit per
LEARNINGS [FEAT-2026-0008/G1-CLOSE]: the close ceremony for this
feature must run the new guard against itself — if any deliverable
is missing, the close WU emits `status: blocked`, not `complete`.

**Status: planned.** Independent of FEAT-2026-0010/0011. Detail the
first gate's WUs when ready to start. Single gate, one substantive
WU (`closing-deliverable-guard`) + `close` ceremony — mirrors
FEAT-2026-0008's shape.

## FEAT-2026-0013 — CI integration_workspace cleanup race fix

**Why.** The repo's CI suite intermittently fails with
`OSError: [Errno 39] Directory not empty: '/tmp/.../.git/objects'`
when `tests/test_driver_integration.py::integration_workspace`'s
`tempfile.TemporaryDirectory()` context manager exits and Python 3.12's
`shutil.rmtree` races against leftover file descriptors holding parts
of `.git/objects`. Three observed occurrences:

- 2026-06-10 push, `test_no_files_changed_in_result_block_runs_squash_as_today`
  — root cause was an unclosed `.specfuse/.loop.lock` fd; fixed by the
  `try/finally` close in `loop.py::run()` (commit `7abc809`).
- 2026-06-11 PR #7 first run,
  `test_cumulative_duration_written_to_frontmatter` — same OSError, but
  the prior fix doesn't touch the test that's failing now. A second
  unclosed handle (or git subprocess that hasn't exited yet) is still
  leaking inside `integration_workspace`.

A subsequent CI run on the same PR passed without code changes,
confirming the race is timing-dependent and not deterministic. CI
flakes erode the verification-as-oracle property even when each
individual failure has a reproducible root cause, and the team has
now spent two halt-and-investigate cycles on the same symptom shape.

**Goal.** Eliminate the race so the integration-test path is
deterministic on Python 3.12 CI runners.

Likely fix paths to evaluate:

- `tempfile.TemporaryDirectory(ignore_cleanup_errors=True)` in
  `integration_workspace` (Py 3.10+). Suppresses the symptom; doesn't
  fix the underlying leak.
- Audit `integration_workspace` for unclosed git subprocess handles
  and add explicit `subprocess.run` `check=True` + completion-wait at
  exit points. Fixes the root cause.
- Move `.specfuse/.loop.lock` open-then-flock pattern out of test
  paths that don't need it (the lock isn't load-bearing inside a
  TemporaryDirectory the test owns).

A single substantive WU per fix-path; recursive audit at close runs
the suite 50× in a loop and asserts zero flakes.

**Status: planned.** Independent of every other planned feature; can
run any time after FEAT-2026-0002 (which raised the floor that makes
the test-suite stability properties more visible).

## FEAT-2026-0014 — GitHub Actions Node.js 20 deprecation bump

**Why.** GitHub will force Node.js 20 actions to Node.js 24 on
2026-06-16; Node 20 removed from runners 2026-09-16. CI's
`actions/checkout@v4` and `actions/setup-python@v5` both emit the
deprecation warning today. Without action, the forced upgrade lands
during a normal CI run with no warning of which workflows will break
their action pinning behavior — exactly the failure mode this repo's
methodology is meant to surface before merge, not after.

**Goal.** Bump `.github/workflows/ci.yml` to action versions that
support Node 24 natively (currently: `actions/checkout@v5`,
`actions/setup-python@v6` — verify the major-version compatibility at
WU author time, not assume).

Single substantive WU: edit `ci.yml` action `uses:` lines; trigger a
CI run on the PR and confirm no deprecation warning fires; assert
both jobs still pass against the existing test suite.

**Status: done.** `roadmap_goal` met — `.github/workflows/ci.yml`
pins `actions/checkout@v6` and `actions/setup-python@v6`; no stale
`@v[0-5]` pins remain. Five days of deadline margin (closed
2026-06-11; forced upgrade 2026-06-16). T01 landed in 1 attempt
after a WU re-arm; the original ACs coupled the WU to the
operator's `gh` CLI auth state and burned 5 dispatches before the
re-arm dropped the host-coupled checks. See
`RETROSPECTIVE.md §Feature-arc verdict`.

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
