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

## Notes

- Correlation IDs are allocated here, sequentially per year: `FEAT-YYYY-NNNN`.
  Work units take `FEAT-YYYY-NNNN/TNN` for substantive units and
  `FEAT-YYYY-NNNN/G<n>-(RETRO|LESSONS|DOCS|PLAN)` for closing-sequence units
  — see `.specfuse/rules/correlation-ids.md`.
- The feature folder name carries the full ID plus a slug, so it greps,
  sorts, and threads cleanly.
- **Read `.specfuse/LEARNINGS.md` before detailing a new feature.** It is
  the accumulated output of every gate's lessons step and exists to make
  the next plan better than the last.
