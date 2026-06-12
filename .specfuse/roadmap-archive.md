---
project: specfuse-loop
---

# Archived feature details

This file holds the detail sections for features whose status has reached `done`
or `abandoned`. The main roadmap table in `.specfuse/roadmap.md` keeps a row for
every feature (across all statuses) and links here via a `Detail` cell for
graduated entries. Features with status `planned` or `active` keep their detail
sections inline in `roadmap.md`.

## Conventions

- **Anchor format.** Each archived feature's detail section is preceded by an
  anchor on its own line:

  ```
  <a id="feat-yyyy-nnnn"></a>
  ```

  Replace `yyyy` and `nnnn` with the feature's four-digit year and zero-padded
  sequence number (e.g. `feat-2026-0003`). The anchor must appear on a line by
  itself, immediately above the `## FEAT-YYYY-NNNN —` heading.

- **Back-link form.** The corresponding `Detail` cell in the main roadmap table
  contains exactly:

  ```
  [→ archive](roadmap-archive.md#feat-yyyy-nnnn)
  ```

  with the same lower-case `feat-yyyy-nnnn` fragment. Both strings are
  machine-read by the `roadmap-archive` and `roadmap-add` skills — do not alter
  their shape.

- **Which features are archived.** Only features with status `done` or
  `abandoned` are archived here. Features with status `planned` or `active`
  keep their detail sections inline in `roadmap.md`.

- **Append order.** Sections are appended in the order they are archived (not
  necessarily numeric order). The placeholder comment below marks the insertion
  point; T02 (`roadmap-archive` skill) and T04 (migration) append after it.

<!-- Archived sections appended below -->

<a id="feat-2026-0003"></a>
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

<a id="feat-2026-0004"></a>
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

<a id="feat-2026-0005"></a>
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

<a id="feat-2026-0006"></a>
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

<a id="feat-2026-0007"></a>
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

<a id="feat-2026-0008"></a>
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
