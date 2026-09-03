# The Specfuse gate-cycle methodology

This document is the canonical definition of the gate cycle: the shared
vocabulary and contracts that the Specfuse Loop and the Specfuse Orchestrator
both implement. It is written to be implementation-agnostic — the loop runs it
single-repo with a driver script; the orchestrator runs it multi-repo with
agents and a polling loop — but the *concepts* defined here mean the same thing
on both surfaces.

> **Authoring note.** While the gate cycle is being proven, the loop is its
> near-term author: the loop runs real features first, and what it learns
> revises these contracts before they are folded into the orchestrator's frozen
> baselines. See [`concepts/architecture-addendum-gates-and-iterative-planning.md`](concepts/architecture-addendum-gates-and-iterative-planning.md)
> for how the cycle maps onto the orchestrator's state machine and agent roles.

---

## 1. The unit hierarchy

- **Roadmap** — the master index of features for a repository/project, with each
  feature's status (`planned → active → done`/`abandoned`). A feature may also be
  parked in one of two states — `blocked` or `deferred`. Nothing is
  loop-dispatchable in either, so the driver skips them (like `abandoned`), but
  both stay resumable: a human flips the feature back to `active` when the
  obstacle clears. Both are distinct from `abandoned` (dead) and `done`
  (complete).
  - `blocked` — cannot proceed because a **named** dependency is unmet: an ADR
    awaiting approval, or an upstream `FEAT-YYYY-NNNN` that must complete first.
    A blocked feature always names and links its blocker, so the roadmap shows
    the dependency at a glance. Only `planned` or `active` may be blocked.
  - `deferred` — a *voluntary* park with no named blocker, pending an external
    decision or dependency. The absence of a named blocker is the entire
    difference from `blocked`.
- **Feature** — a spec-driven *or directly-authored* unit of value, identified by
  a correlation ID `FEAT-YYYY-NNNN`. A feature owns an ordered list of gates.
- **Gate** — a milestone partition of a feature: an ordered batch of substantive
  work units followed by a mandatory closing sequence and a human review-and-arm
  checkpoint. Gates are numbered within a feature.
- **Work unit (WU)** — a single, self-contained unit of work identified by a
  task-level correlation ID `FEAT-YYYY-NNNN/TNN` for substantive units,
  `FEAT-YYYY-NNNN/TNNH[N…]` for hygiene units that precede a target substantive
  unit, `FEAT-YYYY-NNNN/G<n>-(RETRO|LESSONS|DOCS|PLAN)` for the legacy four-WU
  closing sequence, `FEAT-YYYY-NNNN/G<n>-CLOSE-INTERMEDIATE` +
  `FEAT-YYYY-NNNN/G<n>-PLAN` for the two-WU intermediate closing (non-terminal
  gates), or `FEAT-YYYY-NNNN/G<n>-CLOSE` for the single-WU terminal close.
  A WU is crafted to be completed in one focused agent session.
  It carries its own prompt and is the contract between the planner and the
  executor.

The correlation ID threads the entire lifecycle — it appears in the feature
folder name, the WU file, every event-log entry, the branch, the commit trailer
(`Feature: FEAT-YYYY-NNNN/TNN`), and (in the orchestrator) the GitHub issue.

## 2. Ownership — one fact, one home

- The **PLAN** owns the *shape*: gate order, which WUs belong to each gate, and
  the dependency edges between them.
- The **GATE** owns the *gate*: its status, its definition of done, and the
  human's reflection notes.
- The **WU** owns *itself*: its type, model, status, attempts, and prompt body.

Dependencies live in the PLAN, not in WU frontmatter: a dispatched session never
needs to know its own dependencies — they are satisfied by the time the unit is
handed to it. Dependency edges are scheduling metadata, and scheduling belongs to
the driver/PM, not to the executing session.

### 2.1 WU frontmatter fields — the one home

`WU.template.md` carries the shape; the semantics live here, one line per field,
so a drafting agent reads a 70-line template instead of 120 lines of field notes
it mostly does not need. Author-set unless marked driver-owned.

- `id` — task-level correlation ID; must match the PLAN.md graph entry. Pattern:
  `.specfuse/rules/correlation-ids.md`.
- `type` — one of the eight in §3; selects the gate set the driver runs
  (`implementation` → `code`; `retrospective`/`lessons`/`docs` → `doc`;
  `plan-next`/`close`/`close-intermediate` → `plannext`).
- `status` — lifecycle position. Authors write `draft` (unarmed) or `pending`
  (armed); the driver writes `in_progress`, `in_review`, `done`, `blocked_human`.
- `model` — OPTIONAL. Family alias (`sonnet`/`opus`/`haiku`) or a full
  `claude-*` ID to pin a release. Absent → the type default in `MODEL_BY_TYPE`.
- `effort` — OPTIONAL. `low`|`medium`|`high`|`xhigh`|`max` thinking budget.
  Absent → the type default; `low`/`medium` add a terseness directive.
- `planned_cost_usd` — OPTIONAL estimate at draft time, compared against actual
  in the close. Floors for planning WUs: `.specfuse/rules/planning-discipline.md` §5.
- `generated_surfaces` — OPTIONAL. Generated files this unit's acceptance depends on.
- `oracle_env` — OPTIONAL. Where the verifying oracle runs: `macos_local`,
  `linux_docker`, `github_actions_ci`, or an operator-named string.
- `produces` — OPTIONAL. Path(s) or glob(s) this unit must yield; the driver's
  presence gate refuses `complete` when one is missing or empty.
- `produces_driver_helper` — OPTIONAL. Symbol(s) this unit adds to the driver.
  Lint WARNs when the body mentions driver wiring and the field is absent.
- `prep` — OPTIONAL. A `verification.yml` set run **before dispatch**, fail-fast:
  the first non-zero exit halts dispatch, no session runs.
- `oracles` — OPTIONAL. A `verification.yml` set run before dispatch, capture-all;
  its output is injected into the session prompt as real repo state.
- `extra_gates` — OPTIONAL. A `verification.yml` set unioned onto the
  type-selected gate set **at exit**, ANDed into the same pass/fail verdict.
- `max_attempts` — OPTIONAL. Attempt ceiling for this unit, overriding the
  project default and the built-in 3. Below 1, non-integer, or `true` is an error.
- `iterate_on_failure` — OPTIONAL, default false. Opt in only when the oracle is
  a convergent whole-tree validator emitting a `FINDINGS: <n>` line: an attempt
  that lowers findings keeps its tree, one that does not is rolled back, and two
  non-improving attempts escalate `convergence_plateau`.
- `auto_close_disabled` — OPTIONAL. Set `true` on a load-bearing close so the
  auto-close predicate cannot skip it (`.specfuse/rules/close-discipline.md`).
- `human_only` — OPTIONAL, veto-only: the planner's self-flag on a draft it knows
  needs a human. Never grants autonomy, only subtracts it.
- `provenance` — OPTIONAL, veto-only: a string citing the retrospective item or
  `events.jsonl` event that motivated a unit added beyond the plan baseline.
- `open_questions` — lives in `GATE-{N+1}-REVIEW.md` frontmatter, not here. A
  required explicit list; `[]` means nothing blocks, and a **missing field is not
  an empty list** — it parks the feature under `auto`.
- Driver-owned, written at dispatch and outcome time (authors leave them absent):
  `attempts`, `cost_usd`, `input_tokens`, `output_tokens`, `duration_seconds`,
  `cumulative_*`, `re_arm_count`, `re_arm_history`, `folded_through_re_arm`,
  `model`/`effort` as resolved, `gate_set`, `driver_version`, `started_at`.

## 3. Work unit types

Nine types share one state machine; type affects only who handles the unit and
what its prompt contains.

Substantive:
- `implementation` — code.
- `qa_authoring` / `qa_execution` / `qa_curation` — test-plan authoring,
  execution, and regression-suite curation.

Performed by a person (FEAT-2026-0085):
- `human` — a step no agent can take: reply on an issue, sign something, click
  through a console, run something interactively. The driver never dispatches
  it; when it is ready the driver prints the operator brief and halts. The
  operator performs the step and marks it `done` with `evidence:`
  (`/unblock-wu <WU-ID> --done --evidence "<what you did>"`), and the run
  resumes; a `done` `human` unit with no `evidence` is a lint ERROR. It has no
  model and no gate set, and needs only Objective, Context, and Acceptance
  criteria. Place it *before* the close that depends on it, so the human step
  is recorded as work rather than softened into the verdict afterwards.

Closing sequence — every gate ends with **one** of three forms:

*Two-WU intermediate* (non-terminal gates — preferred over the legacy four-WU sequence):
- `close-intermediate` — folds retrospective, lessons, and docs into one session:
  writes `RETROSPECTIVE.md`, promotes lessons to `LEARNINGS.md`, and reconciles
  documentation. Paired with the `plan-next` unit that follows.
- `plan-next` — drafts the next gate and writes the human review summary.

*Single-WU terminal* (terminal gate of any feature):
- `close` — collapses all four ceremonies into one session: writes
  `RETROSPECTIVE.md`, promotes lessons to `LEARNINGS.md`, reconciles docs and
  roadmap, and writes the terminal feature-arc verdict. `lint_plan.py` rejects
  this type on any non-terminal gate.

*Legacy four-WU sequence* (accepted by lint but emits WARN; use two-WU or single-WU forms instead):
- `retrospective` — feature-local raw observations for the gate.
- `lessons` — promotes the *generalizable* subset of the retrospective into the
  cross-feature `LEARNINGS.md`.
- `docs` — reconciles documentation and roadmap status with what was built.
- `plan-next` — drafts the next gate and writes the human review summary.

### Deterministic auto-close path (FEAT-2026-0018)

The driver evaluates a deterministic predicate (`gate_eval.py`, predicate=v1) at
every gate boundary — intermediate and terminal — before dispatching any close WU.
The predicate exists to eliminate the human `/arm-gate` round-trip and the
hollow-pass / wiring-race brittleness class on fully on-plan gates; the full close
ceremony (retrospective, lessons, docs) remains valuable precisely when things go
off-plan, and the predicate routes each gate to the right path without AI judgment.
For the full design rationale see `PLAN.md` for FEAT-2026-0018.

**Predicate v1 — a gate auto-closes iff ALL hold:**

1. **No blocked_human in attempt chain** — no WU in this gate has `blocked_human`
   in its lifecycle events (`events.jsonl`) for this run. Re-arm history from
   FEAT-2026-0016, if present, is also inspected — any prior `blocked_human`
   cycle disables auto.
2. **No replan** — no `replan` event in `events.jsonl` for this gate's WUs.
3. **Per-WU cost ≤ 1.5× planned** — every substantive WU's `cost_usd` ≤
   `planned_cost_usd × 1.5`. If `planned_cost_usd` absent: skip this check for
   that WU (graceful degrade — emits a warning reason in the decision but doesn't
   disable auto).
4. **No WU > 2× planned** — even one substantive WU exceeding plan by > 2×
   disables auto regardless of others. Catches estimation drift like
   FEAT-2026-0015/G1-PLAN (3.8× over).
5. **Plan-next ≤ 1.5× planned** — the `plan-next` type WU is held to the same
   1.5× ceiling, enforced separately so plan-next overrun is a visible reason
   in the decision.
6. **Gate total ≤ `cost_budget_usd`** — if `GATE-NN.md` declares a budget, sum
   of all WU `cost_usd` in the gate must be ≤ budget. Absent budget: skip.
7. **No test/lint/security failures in attempt notes** — every substantive WU's
   final attempt's `attempt_outcome` must be `passed`. Earlier attempts may have
   failed (already governed by check 1 if blocked), but the FINAL outcome on
   each WU must be clean.

**Auto-close terminal** — when the predicate fires on a terminal gate, the driver
writes a stub `RETROSPECTIVE.md`, marks the close WU `status: done` with
`auto_close: true` frontmatter, and fires `fire_terminal_flips` directly. The
close WU's dispatch is skipped. The FEAT-2026-0017 invariant guard
(`assert_terminal_flips_fired`) still runs — the driver calls it after the stub
is written, so the guard exercises the same path regardless of ceremony form.

**Auto-close intermediate (option A)** — on a non-terminal gate that auto-closes,
the `close-intermediate` WU dispatch is skipped (no retrospective session, no
lessons promotion), but `plan-next` still dispatches to author the next gate's
draft work units. The human review-and-arm checkpoint therefore still fires;
auto-close only eliminates the reflective overhead, not the forward-design step.

**Override surfaces** — two escape hatches exist. Pass `--force-full-close
<feature-id>` on the CLI to bypass the predicate for a single gate and run the
full close ceremony regardless of predicate outcome. Alternatively, set
`auto_close_disabled: true` in a feature's `PLAN.md` frontmatter to disable
auto-close permanently for that feature (e.g., for features that are inherently
exploratory and expect off-plan behavior). For a single **substantive close**
— a `close` (or `close-intermediate`) WU whose acceptance criteria assert on the
source tree, reconcile prior gates, or observe runtime behaviour rather than
just writing the retrospective stub — set `auto_close_disabled: true` in **that
WU's** frontmatter. The predicate keys on the implementation WUs' cost and
plan-conformance and cannot see what a close verifies, so a substantive close
must be marked must-run or its verification is silently skipped (#189).

**The verdict is binary** (FEAT-2026-0085) — a close records `met` or
`not_met`, and nothing in between. Across 273 features in 12 repositories, 48%
of verdict-bearing closes ended on one of the two soft-success verdicts this
release retired, and 59 of those were later flipped to `met` by an acceptance
skill with nothing re-run: the hedge had become a polite synonym for "unknown".
A `not_met` close leaves every terminal surface un-flipped (gate
`awaiting_review`, roadmap row `active`, PLAN.md `active`) and must write
`FOLLOW-UPS.md` in the feature folder — one `### `-headed entry per failed
criterion, carrying the criterion verbatim, the evidence (the command run and
its exit code or output line), and the re-run condition that would satisfy it.
`close-m` refuses a `not_met` close whose `FOLLOW-UPS.md` is absent or empty,
pre-squash and via `specfuse lint --closing`.

**What a hedge used to carry now has three honest channels.** Of 101 hedged
features, 42 hedged because a criterion asked the loop to observe production,
16 because a human had to sign or act, and 9 because auto-closed gates had
seeded every criterion into the retrospective as debt the terminal close could
not reconcile. So: a criterion that needs a person is a `type: human` work unit
placed before the close; a criterion that can only be observed in production is
a `## Post-merge checklist` line in `PLAN.md`, never an acceptance criterion;
and work that simply did not get done is `not_met` plus a follow-up entry. See
`.specfuse/rules/close-discipline.md` §2 for the close-time obligations.

**Unfinished work becomes tracked issues, not prose.** After a `not_met`
close's squash, `file_followup_issues` files one GitHub issue per
`FOLLOW-UPS.md` entry under `specfuse:follow-up`, carrying the entry body
verbatim and idempotent per entry; on a `met` close it files the optional
`## Post-merge checklist` section as one `specfuse:post-merge` issue. `gh`
absent or failing leaves `FOLLOW-UPS.md` itself as the record — the driver
never deletes or rewrites it — and emits one `followups_recorded` event naming
the `filed` and `unfiled` counts.

**Re-firing the flips out of band** (FEAT-2026-0070) — `fire_terminal_flips`
runs at close-WU-*outcome* time and the driver never re-dispatches a `done`
close WU, so a verdict corrected after the fact needs an entry point.
`specfuse run --recheck-verdict <FEATURE_ID>` re-reads the terminal close WU's
verdict from disk and fires the flips if it now permits them, without
re-dispatching the WU. It **does not write terminal state itself** — it routes
through the one owner. It is a no-op (exit `0`, printing why) when the feature
is already `done` or the verdict on disk does not permit the flips. This is
also the path a migrated legacy close takes; see
[Migrating a hedged close](#migrating-a-hedged-close).

**The row flips from any non-`done` status** (FEAT-2026-0070) — the terminal
roadmap-row flip previously fired only on `active → done`, so an `autonomy: auto`
feature that self-dispatched from a `planned` row stayed `planned` through a
correct close and escalated `roadmap_row_not_done`. Any non-`done` row now flips.

**Terminal state has exactly one writer.** `fire_terminal_flips` in
`specfuse/loop/loop.py` owns the gate → `passed`, roadmap row → `done`, PLAN.md →
`done`, and auto-archive transitions. Every close path — dispatched, auto-closed,
and out-of-band re-check — calls that one function; no skill and no agent writes
those surfaces. Issue #49 exists because two paths once diverged, and
`[FEAT-2026-0023/G1-CLOSE]` is the rule that came out of it: do **not** add a "flip
PLAN.md to done" acceptance criterion to a close WU, and do not let a skill
hand-edit a terminal surface — if a new path needs the flip, give the driver an
entry point and call it.

**Predicate-version transparency** — every `auto_close_decision` event in
`events.jsonl` carries a `predicate_version` field (e.g., `predicate_version:
v1`). Future revisions to the predicate constants increment this version, so
the audit trail for any gate boundary remains interpretable retroactively even
after v2+ revisions ship.

### Per-attempt outcome events (FEAT-2026-0016)

Every dispatched attempt emits exactly one `attempt_outcome` event to
`events.jsonl`. The payload carries a standardized set of fields:
`outcome`, `failure_class`, `failure_signature`, `failure_excerpt`,
`cost_usd`, `duration_seconds`, `attempt`, and `re_arm_count`. For
the field-by-field schema see
`.specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/PLAN.md`
§ "Event payload shape — `attempt_outcome` v1". The full payload is
not restated here (one fact, one home).

`outcome` taxonomy, as `loop.py` actually emits it — thirteen values,
bound to the emitter by `tests/test_attempt_outcome_contract.py`:

| outcome | meaning |
|---|---|
| `passed` | verify + all driver-side guards clean |
| `failed` | a verification gate failed |
| `blocked` | the agent reported `status: blocked` |
| `prep_halted` | a declared `prep`/`oracles` set halted before dispatch — no session spawned (FEAT-2026-0057/T04) |
| `zero_token_skip` | the session produced no tokens; nothing ran |
| `files_changed_mismatch` | RESULT declared paths that show no diff |
| `closing_deliverable_missing` | a closing-WU guard refused (see `close-discipline.md` §4) |
| `deliverable_missing` | a declared `produces:` path is absent |
| `no_deliverable_files` | the squash names only the WU file / events |
| `produces_not_in_diff` | `produces:` path exists but is not in the squash |
| `squash_commit_failed` | `git commit` for the squash was rejected |
| `smoke_import_failed` | a declared smoke-import line failed post-squash |
| `learnings_not_staged` | a closing WU under `autonomy_default: auto` touched `.specfuse/LEARNINGS.md` directly instead of staging to `LEARNINGS-pending.md` (FEAT-2026-0053/T09) |

Extending it is a breaking change for every consumer below and requires a
deliberate versioning decision — **and an update here in the same commit.**
Five of the values above shipped without that step, and the drift was
found only when someone mined the corpus (#270).

`failure_class` taxonomy is **locked at v1**: `tests | lint |
security | coverage | symbol_existence | bandit | other | null`.
`failure_class: other` is the explicit catch-all for paths not yet
classified; `null` means the outcome was `passed` (no failure).

**Where the diagnostic lives depends on the outcome.** This is the part that
misleads readers of the "standardized set" above: `failure_class` /
`failure_excerpt` are not populated on every non-`passed` outcome, and a
consumer that queries only those concludes the record is empty when it is not.

| outcome | carries its reason in |
|---|---|
| `failed`, `files_changed_mismatch`, `produces_not_in_diff` | `failure_class` + `failure_signature` + `failure_excerpt` |
| `blocked` | **`agent_blocked_reason`** (plus a sibling `human_escalation` event) |
| `prep_halted` | **`halt_class`** + **`summary`** (plus a sibling `human_escalation` event) |
| `closing_deliverable_missing`, `no_deliverable_files`, `deliverable_missing`, `squash_commit_failed`, `learnings_not_staged` | **`summary`** |
| `files_changed_mismatch` (pre-0.3.23) | **`unchanged_paths`** only — `failure_*` was added by #182 |
| `zero_token_skip` | nothing, correctly — no attempt ran |

**Read every field in that table before concluding a record is undiagnosable.**
A cross-repo audit reported three separate "missing diagnostic" findings that
were all query errors against this contract, none of which existed (#270).

Consumers that read `attempt_outcome` events (the auto-close
predicate, `/gate-status`, the spinning-detector hook, close-ceremony
cost analysis) treat the `outcome` and `failure_class` values as an
enum — new values are a breaking change.

### Re-arm WU frontmatter additions (FEAT-2026-0016)

When a WU is re-armed from `blocked_human` back to `pending`, six
cumulative audit fields track cross-attempt state:
`re_arm_count`, `re_arm_history`, `cumulative_cost_usd`,
`cumulative_duration_seconds`, `cumulative_input_tokens`,
`cumulative_output_tokens`. For the field-level spec (initialization
values, write ownership, append semantics) see
`.specfuse/templates/WU.template.md` frontmatter notes. The driver
maintains the cumulative fields; `/unblock-wu` writes `re_arm_history`
entries; `/gate-status` surfaces `re_arm_count` prominently on any WU
where it is > 0.

## 4. The five-section work-unit contract

Every dispatchable WU prompt has these five mandatory sections (a sixth,
`Objective`, is recommended but not enforced):

- **Context** — what this is part of, the correlation ID, the grounding specs/files.
- **Acceptance criteria** — explicit, machine-checkable statements of done.
- **Do not touch** — generated dirs, other units' files, secrets, branch
  protection, `.git/`.
- **Verification** — the exact gate commands that must pass.
- **Escalation triggers** — conditions under which to stop and report `blocked`
  rather than push through.

This is the same five-section contract as the orchestrator's work-unit issue
body (architecture §8). Pattern enforcement (TDD order, a required structure)
belongs in the WU prompt and the shared rules, **not** in finer WU granularity.

## 5. Verification is the exit oracle

The executing session's self-report is **advisory**. The driver (loop) or the
branch-protection gate (orchestrator) re-runs the unit's verification and *that*
decides done. For `implementation` units the gates mirror branch protection:
tests pass, coverage ≥ threshold, zero warnings, lint clean, security scan clean.
A unit that passes its own checks but would fail the real gate has done the wrong
thing. Keep the loop's `verification.yml` `code` set in lock-step with branch
protection wherever both exist.

### 5.1 Operator scripts are software, not docs

A unit that ships an **executable artifact for human operators** — a committed
`.sh` script, an installer helper, a runbook whose body is a sequence an operator
copy-pastes — is not exercised by a default `code` gate set: no unit test, no
syntax check, nothing that catches the quirks shell ships with on a fresh
workstation. The unit passes on "the file exists with these sections" and the
operator finds the bugs against real systems, post-merge.

Such a unit's acceptance criteria must include all three, each phrased so a gate
can check it mechanically:

1. **`shellcheck <script>` produces zero warnings**, or every
   `# shellcheck disable=SCxxxx` carries an inline justification naming the reason.
2. **`bash -n <script>` parses clean** — catches typos and unterminated
   constructs a shellcheck pass skips when it cannot parse.
3. **At least one bats-core test against the happy path**, with every external
   command (`az`, `kubectl`, `curl`, `gh`, `terraform`, …) replaced by a
   PATH-shimmed stub. The stubs assert the call shape; the test asserts exit code
   and observable output. The happy path alone catches the lifecycle bugs
   (trap-revoke ordering, `set -e` silent abort, premature exit); error-branch
   coverage is a bonus, not a requirement.

Name the corresponding gate command in the unit's Verification section — usually
a `code` gate entry like `bash -n scripts/<name>.sh && shellcheck
scripts/<name>.sh && bats tests/<name>.bats`. If `verification.yml` declares no
bats gate yet, adding one is the hygiene precursor.

The rule fires on the presence of a committed executable, not on the unit's type:
a markdown-only runbook, a Terraform module, a Helm chart, or a config file is
out of scope.

> **Provenance.** An Argo CD session shipped two ~500-LoC bootstrap scripts as
> docs artifacts; post-merge the operator spent ~3.5hr over 10 patches on
> portability (`${VAR,,}` does not work on stock macOS bash 3.2), lifecycle
> (trap-revoke fired before the revoke was needed, a KV read aborted silently
> under `set -e`), and surface (`az ad sp create` raced with re-runs).
> `shellcheck` flags the portability issue statically; one bats happy-path test
> with `az` stubbed catches the rest. ~15min per script at authoring time.

## 6. The gate cycle

For each gate, in order:

1. **Plan.** The current gate's WUs are detailed (the first gate by the human/PM
   at feature planning; every later gate by the prior gate's `plan-next`).
2. **Execute.** The driver/PM walks the gate's ready WUs (dependencies met),
   dispatches each as a **fresh** session, verifies, and commits one squashed
   commit per unit. A failed gate is retried with a fresh session carrying the
   failure evidence, up to three attempts (the spinning threshold), then
   escalated for human attention.
3. **Close.** The closing sequence runs as the gate's last units. Three forms:
   - **Two-WU intermediate** (non-terminal gate): `close-intermediate` (folds
     retrospective + lessons + docs into one session) then `plan-next` (drafts the
     next gate and writes the human review summary).
   - **Single-WU terminal** (terminal gate): a single `close` WU collapses all
     four ceremonies; no forward-design `plan-next` is needed when there is no
     next gate.
   - **Legacy four-WU** (emits WARN): `retrospective → lessons → docs →
     plan-next` in fixed order.
4. **Review and arm.** The cycle stops for the human, who reviews the next gate's
   draft (guided by the review summary), edits or accepts it, arms the accepted
   units, and signals approval. Then the cycle repeats for the next gate.

The final gate has no next gate to plan; `plan-next` instead signals feature
completion.

### Ceremony proportionality

Closing ceremony cost should scale with feature size. A feature whose
**planned substantive** WU count (types `implementation`, `qa_authoring`,
`qa_execution`, `qa_curation`) is **≤ 8** drafts as a **single gate** with
a **single terminal `close` WU** — no `close-intermediate`, no `plan-next`.
This is the proportional shape: small features do not pay multi-WU closing
overhead sized for large ones.

**Planned count is the key.** The threshold is evaluated against the WUs
declared at planning time, not the WUs that actually ran. A feature whose
scope is revised mid-execution is an off-plan feature by definition.

**Off-plan safety net.** The decision rule is authoring-layer only. A
single-gate feature whose gate goes off-plan (blocked WU, replan event,
cost overrun) still receives the full close ceremony via the `gate_eval`
auto-close predicate (§3 "Deterministic auto-close path"): the predicate
disables auto-close and the driver dispatches the closing WU as a normal
reflective session. Ceremony proportionality trades reflection only on
features that stay small **and** on-plan. The `gate_eval.py` predicate is
the safety net; this rule does not replace it.

The canonical threshold is **8** (stated here, in `docs/methodology.md`;
referenced, not re-defined, in `.specfuse/skills/draft-feature/SKILL.md`).

### Fresh context per dispatch

Each WU is executed by a new session. All durable state lives in the PLAN, the
GATE/WU files, git history, the event log, and per-unit failure notes — never in
a context window. This is the Ralph property, kept at work-unit granularity
because units are sized to land in one pass.

## 7. plan-next and the review summary

`plan-next` is forward design — the one act in the cycle that is not synthesis
against a log — and takes the strongest model. It reads the gate retrospective
and the cross-feature `LEARNINGS.md`, drafts the next gate's WUs, and may revise
*not-yet-reached* gates (split/merge/re-scope), surfacing any such change loudly
in the review summary. It never touches a gate already passed.

It **drafts but never arms.** Arming — accepting the drafted units so they
execute — is the human's act (or, under automatic mode, a mechanically-gated
auto-arm; see §9). This preserves the highest-leverage human checkpoint: catching
a misframed gate before it becomes merged code.

The review summary is weighted toward **doubt**, not completeness: decisions and
their rationale, an explicit "if you check only three things, check these" list,
a roadmap-anchor check (with a loud flag if the goal itself seems to be drifting),
and open questions — each mapped to the draft WU it affects. The summary is
advisory and owns no state.

## 8. LEARNINGS — the cross-feature feedback loop

`LEARNINGS.md` is an append-only, cross-feature log of durable, reusable rules
distilled by each gate's `lessons` unit. It is read at planning time so each
plan is better than the last. Feature-specific observations stay in that
feature's `RETROSPECTIVE.md`; only rules that would change how a *future* WU is
written or executed graduate to `LEARNINGS.md`. This is the human-scale analogue
of the Ralph loop feeding errors back into the prompt.

## 9. Autonomy

Three levels — `auto`, `review`, `supervised` — set once as a feature default
in `PLAN.md` frontmatter (`autonomy_default`). No consumer reads a per-gate
autonomy field: the per-gate, tightening-only override described in earlier
drafts of this section is designed but **unbuilt**. Likewise `review` and
`supervised` are, today, the same behavior — every consumer branches only on
`== "auto"`; the three-way distinction is a name, not yet a mechanism.

At every gate close the driver evaluates `evaluate_arm_predicate` (see
`specfuse/loop/arm_eval.py`) and emits its verdict as an `arm_predicate_evaluated`
event, regardless of autonomy level. Under `review` and `supervised` that
verdict is recorded and nothing acts on it — the gate always halts
`awaiting_review` for a human. Under `auto`, the verdict is acted on at exactly
one flip site in `loop.py`: if the predicate's `would_arm` is `True`, the same
bookkeeping commit that would otherwise just mark the gate `awaiting_review`
instead also flips every next-gate WU `draft` -> `pending` and the just-closed
gate `awaiting_review` -> `passed`, logging a `gate_auto_armed` event. If
`would_arm` is `False`, `auto` takes the same halt-for-human path as the other
two levels — nothing in the predicate distinguishes an `auto` feature from a
`review` one except whether the verdict is consulted.

The predicate itself is eight named stop classes (`budget_projection`,
`judge_editing`, `decision_class_paths`, `retroactive_edits`, `drift_caps`,
`missing_provenance`, `open_questions_human_only`, `plan_next_lint`), each
returning `fired` / `clean` / `not_evaluable`; `would_arm` is `True` only if
none fired. Three of the eight — `missing_provenance`, `open_questions_human_only`,
`plan_next_lint` — are veto channels fed by model-authored output; the rest
are mechanical counters, path checks, and hardcoded caps. The full per-class
meaning is T11's stop-class reference, not restated here.

Escalation overrides autonomy by control flow, not by a checked condition: the
two escalation flip sites (`blocked_human` after `MAX_ATTEMPTS`, and the
dry-run/blocked early returns) return before the arm branch in `loop.py` is
ever reached, so an escalated gate cannot be armed regardless of
`autonomy_default` — there is no autonomy check to forget. Given that, the
human checkpoints on an `auto` feature are exactly: any escalation during the
gate, the PR review, and the merge. Auto-arm advances a feature toward the
*next* gate's execution; it never auto-merges — the merge gate stays human
until the QA loop is trusted.

An auto-arm is exactly one commit. Before that commit is written, the driver
tags the pre-arm `HEAD` as `pre-arm/<feature-id>/gate-<N>`, so an arm crash
leaves the repository in exactly one of two recoverable states — armed, or not
armed — never a partial third. See `docs/dev/auto-arm-recovery.md` for the
recovery procedure; that concept lives here, the procedure lives there.

An `auto` feature also produces two artifacts a `review` feature does not:
`FEATURE-REVIEW.md` (the closing-gate review a human would otherwise have
written by hand) and `LEARNINGS-pending.md` (staged LEARNINGS entries held for
human promotion instead of landing directly). See T12's migration guide for
when and how these get created.

## 10. The two execution surfaces

| Concern        | Loop (single-repo)                  | Orchestrator (multi-repo)              |
|----------------|-------------------------------------|----------------------------------------|
| State backend  | WU / GATE file frontmatter          | GitHub issue labels + feature registry |
| Dispatch       | driver shells out (`claude -p`)     | inbox files + polling loop             |
| Branch / merge | one branch, squash per WU            | branch + PR per task, merge watcher    |
| Spec front-end | optional; task graph authored directly | spec-first (specs agent + codegen)  |

Everything above those rows — the unit hierarchy, ownership split, WU contract,
verification-as-oracle, the gate cycle, plan-next, LEARNINGS, and autonomy — is
shared and means the same thing on both surfaces.

## Migrating a hedged close

FEAT-2026-0085 retired the two soft-success verdicts, `met_locally` and
`partially_met`. They stay **readable**: 42 closes across the corpus are
`status: done` carrying one, `load_wu` and `recheck_terminal_verdict` parse
them rather than crash, and `lint_plan` validates `verdict` only on a non-`done`
close — so a standing hedged close reports no new error and needs no urgent
action. They are not **writable**: `assert_verdict_well_formed` rejects them on
any close dispatched from now on, and `recheck_terminal_verdict` refuses the
terminal flips on one, naming this section in the refusal.

`/accept-hedged-close` no longer exists. There is no path that softens a verdict
to get past `/wrap-feature`'s refusal; migrate the close instead.

Pick one of two routes per standing hedged close. Find them with:

```bash
grep -l "^verdict: met_locally\|^verdict: partially_met" .specfuse/features/*/WU-9*.md
```

**Route A — discharge, then record `met`.** Use this when the old follow-up
record's re-run condition is reachable today, or when it was an
`acceptance-discharged` entry that a signature was always going to settle. Run
the re-run condition and read the exit code. If it passes, edit the close WU's
`verdict:` to `met`, then:

```bash
specfuse run --recheck-verdict <FEATURE_ID>
```

That re-reads the verdict from disk and fires the terminal flips through their
one owner — gate `passed`, roadmap row `done`, PLAN.md `done`, auto-archive.
It never writes those surfaces itself, and it does not re-dispatch the close.

**Route B — record `not_met` and track what is left.** Use this when the work is
genuinely unfinished. Edit the close WU's `verdict:` to `not_met`, then write
`FOLLOW-UPS.md` in the feature folder from the old `## Hedged-verdict follow-up
record` — one `### `-headed entry per unmet criterion, carrying the criterion
verbatim, the evidence, and the re-run condition. Then re-arm the unit that
failed (`/unblock-wu <WU-ID>`) so the loop can finish it, or leave the close
`not_met` and let the driver file the follow-up issues on its next pass.

Translating the old `kind:` values, which no longer exist:

| Old `kind:` | Where it goes now |
|---|---|
| `acceptance-discharged` | a `type: human` unit placed before the close (route A after it is `done` with `evidence:`) |
| `externally-verifiable-later` | a `## Post-merge checklist` line in `PLAN.md` if it needs production; otherwise a `FOLLOW-UPS.md` entry |
| `routed-finding` | already tracked elsewhere — link that issue from the `FOLLOW-UPS.md` entry |
| `inherent` | not assertable, ever: it was never a legitimate acceptance criterion. Delete it from the criteria and say so in the retrospective |

**Do not rewrite the history.** Existing `RETROSPECTIVE.md` files keep their
`## Hedged-verdict follow-up record` sections as written — they are the record
of what was true at the time. Migration edits the close WU's `verdict:` and adds
`FOLLOW-UPS.md`; it does not revise past retrospectives.
