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
| FEAT-2026-0002 | Driver run-loop test coverage               | planned  | —      |
| FEAT-2026-0003 | GitHub feature-pick for the loop            | done     | `.specfuse/features/FEAT-2026-0003-github-feature-pick/` |
| FEAT-2026-0004 | Single-driver working-tree lock             | done     | `.specfuse/features/FEAT-2026-0004-driver-lock/` |
| FEAT-2026-0005 | Combined close for single-gate features     | done     | `.specfuse/features/FEAT-2026-0005-combined-close/` |
| FEAT-2026-0006 | WU execution-time tracking                  | done     | `.specfuse/features/FEAT-2026-0006-wu-duration/` |
| FEAT-2026-0007 | Dispatch cost controls                      | done     | `.specfuse/features/FEAT-2026-0007-dispatch-cost-controls/` |
| FEAT-2026-0008 | Driver completeness-guard                   | active   | `.specfuse/features/FEAT-2026-0008-driver-completeness-guard/` |

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

**Verification.** When this feature's last gate passes, raise
`.specfuse/verification.yml`'s coverage `--fail-under` to a number matching
the new measured floor (target ≥ 80; if the integration tests don't reach
80 alone, scope the feature to add what's needed). Update the comment in
the YAML to remove the deviation note once the floor is at or above the
methodology default.

**Status: planned.** Detail the first gate's WUs when ready to start; the
roadmap entry stays one row until then.

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
`source_issue_url` is present in PLAN.md frontmatter (T06); live smoke of `example-feature`
(`example-org/example-app#287`) run out-of-loop by human operator — discovery, adopt, and
report-back all PASS, `#287` fully restored post-smoke (T07). **Finding:** the adopted folder
failed `lint_plan.py` because orchestrator issue bodies use `## ATX` headings; the linter only
recognised `**bold**`/plain. Fix delivered in gate 4. GATE-03 status: `passed`.

**Gate 4 (passed).** ATX-heading linter fix: broadened `lint_plan.py`'s mandatory-section
detector to a union pattern (`^(?:#+\s*|\**)`) that accepts both Markdown ATX headings
(`## Context`) and the existing bold-preamble (`**Context.**`) form (T08). The adopted
`example-feature-…` folder now passes `lint_plan.py` exit-0, and existing bold-headed WU
bodies remain clean (regression guard). GATE-04 status: `passed`.

**Status: done.** All four gates passed. All four pipeline mechanisms — discover, adopt,
report-back, lint-clean grind — are proven live against `example-org/example-app#287`. The
`roadmap_goal` is met. See `RETROSPECTIVE.md §Feature-arc retrospective` and
`SMOKE-example-feature.md`.

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
