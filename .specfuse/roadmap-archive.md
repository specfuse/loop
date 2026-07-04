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
<a id="feat-2026-0025"></a>
## FEAT-2026-0025 — LEARNINGS curation + archival (bound planning-context growth)

**Why.** `.specfuse/LEARNINGS.md` is append-only and loaded **whole** into
planning context by `/draft-feature`, `/pick-feature`, `plan-next`, and
`/authoring-work-units`. After ~20 features it is already ~86 entries / ~24k
tokens (~4 entries/feature, growing unbounded). The driver enforces appends
(`assert_learnings_appended_or_noop`) but nothing prunes: there is no
archival/compaction counterpart the way `roadmap.md` has `roadmap-archive.md` +
`auto_archive_feature`, and `learnings-suggest` only ADDS candidates. Left
unchecked this inflates every planning session's context cost and dilutes signal
as superseded/duplicate rules accumulate. Surfaced reviewing FEAT-2026-0024
(whose `LEARNINGS.template.md` split already separated portable methodology
wisdom from this repo's feature-specific history).

**Goal.** A curation/archival mechanism that bounds the planning-loaded LEARNINGS
to the active, durable set: (1) a `LEARNINGS-archive.md` + a curation step that
moves feature-specific or obsolete entries out of the planning-loaded file
(mirroring `auto_archive_feature`); (2) promotion of broadly-applicable rules
into the binding `.specfuse/rules/*.md` (curated, small, always-loaded), leaving
LEARNINGS as a staging area; (3) a `/learnings-curate` skill — the
read/compaction counterpart to `learnings-suggest` — that merges duplicates,
retires superseded entries, and flags promotion candidates for the operator;
(4) later, indexed retrieval so consumers load only the relevant slice instead
of the whole file.

**Benefits.** Planning-context cost stays bounded as the repo scales to hundreds
of features. Higher signal — a curated durable set beats append-only sprawl when
the planner (human or agent) is hunting the rule that applies. Durable rules
graduate into binding contracts. Portable methodology wisdom stays cleanly
separated from feature-specific history. Closes the missing half of the
methodology's feedback loop: today it can only grow, never compact.

**Status: planned.**

<a id="feat-2026-0030"></a>
## FEAT-2026-0030 — Driver-side sanitization of agent-authored text before events.jsonl staging

**Why.** The loop driver writes agent-authored free-text (blocked reasons,
failure notes) into `events.jsonl`, then stages and commits that audit trail. When
the text happens to contain a token the repo's structural leak-scan flags — e.g. an
absolute home-directory path (a `~`-expanded checkout location) the agent mentioned
while explaining where it searched — the pre-commit hook rejects the bookkeeping commit and the gate halts
mid-run. Observed live on FEAT-2026-0029/T01 (driver 0.3.6): the agent's
`blocked_reason` quoted a local checkout path, tripping `user-path` findings on
`events.jsonl` lines 29-30. This is the same failure family as the now-closed #76
(which redacted the leak hook's *own* FINDINGS text) and #73 (the general form),
but a distinct, still-uncovered source: **agent-authored** note text, not
hook-captured FINDINGS. #76's fix does not cover it.

**Goal.** A single driver-side sanitization pass applied to *all* agent-authored
strings before they are written into `events.jsonl` (or at minimum before the
bookkeeping commit is staged): redact absolute home-directory prefixes (the
`~`-expanded macOS and Linux forms) and any other token the structural leak-scan
flags, to a placeholder,
preserving the audit signal without re-embedding the trigger. Retires the residual
per-token allowlist band-aids and closes the systemic self-poison class for note
text, not just captured-FINDINGS text.

**Benefits.** Bookkeeping commits stop halting the gate on benign local paths that
leak into agent prose; the audit trail still records *that* and *why* a WU blocked;
one sanitization chokepoint replaces scattered redaction. Removes a recurring
operator-recovery chore (manual redact-and-commit) from real runs. Small, driver-
local (`loop.py`), test-backed (feed a note containing a user path → assert the
staged events.jsonl passes `leak_scan.py --staged`).

**Status: planned.**

<a id="feat-2026-0029"></a>
## FEAT-2026-0029 — One-command Specfuse scaffold upgrade skill

**Why.** Upgrading a project's Specfuse scaffold today means a human hand-runs
`specfuse upgrade` then repeats the same git choreography every time — branch off
origin/main, run the upgrade, commit, push, open a PR, merge. It's repetitive,
easy to get wrong (upgrading a dirty tree, branching off a stale local main), and
there's no single entrypoint.

**Goal.** A Claude Code skill that performs a scaffold upgrade end-to-end on a
target project: (1) dry-run mode reports what the upgrade would change without
writing; (2) live mode opens a chore branch off the latest origin/main, runs
`specfuse upgrade`, commits, pushes, opens a PR, and merges on green.

**Benefits.** One command replaces a multi-step manual ritual; always branches off
fresh origin/main (no stale-base bugs); dry-run preview before any write. The
merge step is gated on BOTH CI-green AND a clean post-upgrade health report — if
the upgrade flags conformance FAILs, the skill halts before merge and hands off to
`/feature-conversion` rather than landing a broken scaffold. It wraps the existing
`specfuse upgrade [--dry-run]` CLI, so it adds orchestration only, not new upgrade
logic.

**Status: planned.**

<a id="feat-2026-0026"></a>
## FEAT-2026-0026 — Scaffold-data in the pip package: `specfuse init` replaces init.sh

**Why.** FEAT-2026-0019 shipped the pip driver (`specfuse-loop`), the `specfuse`
umbrella CLI, and the Claude Code plugin — but `specfuse init` cannot yet scaffold a
new repo from pip alone: the scaffold data (`templates/`, `rules/`,
`verification.yml.example`, `roadmap.template.md`, `LEARNINGS.template.md`) still lives
in the loop repo and ships only via the bash `init.sh`. So `init.sh` remains the
bootstrap and carries a v1.0 deprecation banner it cannot yet honor — v1.1 cannot
delete it until pip-native scaffolding exists. Surfaced in FEAT-2026-0019's gate-4
retrospective (terminal verdict's recommended follow-up).

**Goal.** Ship the scaffold data inside the `specfuse-loop` (or `specfuse`) package and
have `specfuse init <repo>` lay down a target's `.specfuse/` from package resources,
fully replacing `init.sh`.

- Package the templates/rules/examples as package data, loaded via
  `importlib.resources` (no reliance on a source checkout).
- `specfuse init` writes `.specfuse/` (templates, rules, verification.yml seed,
  roadmap + LEARNINGS seeds, `.specfuse/VERSION` stamp) and wires `.claude/` — the
  `init.sh` behavior, in-process and pip-delivered.
- `specfuse upgrade` overlays the versioned scaffold from the installed package
  version (the `--upgrade` path), so upgrades follow `pip install -U`.
- Delete `init.sh` (v1.1) once parity is proven; keep a thin curl-bash bootstrap only
  for the no-pip first-touch case if still needed.

**Benefits.** `init.sh`'s deprecation becomes real (v1.1 deletion unblocked). One
delivery channel (pip) for both code and scaffold; offline/sandboxed installs work
from the wheel; version-skew between scaffold and driver collapses to the package
version. Closes the last gap between FEAT-2026-0019's vision and what shipped.

**Gate sketch (drafted at /draft-feature time).**
- G1 — package the scaffold seed (templates, rules, examples, roadmap/LEARNINGS
  templates, gitignore lines, VERSION) + a resource-loading API via
  `importlib.resources`. Decision: `specfuse-loop` owns the data; the umbrella CLI
  calls into it.
- G2 — `specfuse init <repo>` writes a fresh `.specfuse/` (+ `.gitignore`, VERSION
  stamp, `.claude` wiring) from package resources — parity with `init.sh` INIT.
- G3 — `specfuse upgrade <repo>` overlays versioned files (parity with `--upgrade`:
  preserve user-authored, prune internal, stamp); deprecate then delete `init.sh`
  (v1.1).

**Status: active.** Depends on FEAT-2026-0019 (the package + CLI it extends).
Packaging/harness-coupled — per LEARNINGS `[FEAT-2026-0019/G1]`, expect to run this
interactively (atomic), not per-WU loop dispatch.

<a id="feat-2026-0024"></a>
## FEAT-2026-0024 — Hashed denylist + issue/PR-body leak guard

**Why.** Closes the two leak-guard surface gaps FEAT-2026-0020's review
surfaced (GitHub issues #45, #46), both rooted in LEARNINGS
`[FEAT-2026-0020/G2/leak-guard-surface-asymmetry]`. (1) `leak_scan.py`'s
denylist (`leak_denylist.txt`) is gitignored — committing the literals to a
public repo would re-leak them — so in CI the `--all` gate enforces gitleaks
secrets only, NOT org-name re-introduction. (2) The pre-commit hook scans git
commits only; GitHub issue/PR titles, bodies, and comments are a separate
public surface it can't see — exactly where the FEAT-2026-0020 leaks landed.

**Goal.** Two gates. Gate 1 (#45): a committed, salted-SHA-256 hashed denylist
(`leak_denylist.hashes`) that CI loads, giving `scan_repo`/`--all` org-name
coverage without exposing the literals; a `leak_scan.py --hash-denylist`
generator keeps it in sync with the gitignored plaintext. Gate 2 (#46): a
GitHub Action triggered on `issues` + `pull_request` (open/edit) that runs the
scanner + hashed denylist over titles/bodies/comments and fails/comments on a
hit.

**Shape.** Hashing can't substring-match, so the chosen design normalizes each
literal (lowercase, strip non-alphanumeric) and matches via a char-sliding
window at a committed distinct-length set — preserving the plaintext denylist's
substring fidelity (`acmewidget` ⊂ `AcmeWidgetApp`) while leaking only a
handful of small integers, never content. Honest caveat: low-entropy names + a
public salt = obfuscation, not secrecy; the guard catches accidental
re-introduction. Gate-1 substantive WUs are `opus`/`high`, red-test-first
(leak-guard correctness path). `autonomy: review` halts at the gate boundary.

**Scope OUT.** Expunging GitHub edit-history (GitHub retains body revisions —
the Action stops new leaks only; documented limitation). Replacing the plaintext
denylist (stays as local-convenience source). Hashing the pre-commit `--staged`
surface (plaintext present locally). `act`/Docker Action emulation in-loop
(gate-2 live trigger is operator-verified post-merge). Cost levers.

**Status: planned.** Two gates, both independently shippable; gate 2 consumes
gate 1's committed hashed denylist. `planned_cost_usd: 11.50` covers the five
WUs that exist now; `plan-next` revises when gate 2's Action WUs are drafted.

<a id="feat-2026-0023"></a>
## FEAT-2026-0023 — Lifecycle integration test + consolidate terminal-state ownership

**Why.** Three driver bugs surfaced in a single session (2026-06-16), all of
the same shape — **seam bugs at handoffs between subsystems**, none catchable
by the existing 749 unit tests because unit tests stub the handoffs:

- **#47** (fixed in #47) — `/draft-feature` emits a roadmap row only;
  `auto_archive_feature` assumed an inline detail section, so an auto-closed
  drafted feature halted on `archive_anchor_missing`.
- **#48** — `ensure_feature_branch` crashes with a raw traceback when a dirty
  working tree (the `/pick-feature` status flips) or a stale pre-existing
  branch blocks the checkout.
- **#49** — terminal **auto-close** leaves `PLAN.md status: active`: the normal
  close path relies on the close WU's *agent* to flip PLAN.md, and the
  auto-close path runs no agent while `fire_terminal_flips` never touches
  PLAN.md.

Root pattern: the methodology's machinery (auto-close predicate 0018,
draft-feature skill, archive automation 0010) grew faster than its integration
coverage, and the gaps only execute at real feature boundaries — rare events
that the first true end-to-end **autonomous** runs (`autonomy: auto` / predicate
close) finally exercised without a human silently papering over each seam.

**Goal.** Close the class, not the three instances.

1. **End-to-end lifecycle integration test.** A test harness that drives a
   synthetic feature through the full lifecycle in one run — draft → pick →
   loop dispatch → terminal close (BOTH the dispatched-close and the
   auto-close-predicate paths) → archive → wrap-ready — and asserts the
   terminal invariant holds: `PLAN.md=done`, `GATE=passed`, roadmap row `done`,
   archive anchor present, RETROSPECTIVE present. Parameterized over close path
   (normal vs auto-close) and feature shape (single-gate vs multi-gate;
   row-only vs detail-section). This is the layer that would have caught all
   three bugs before they hit a live run.

2. **Consolidate terminal-state ownership.** Today the PLAN/GATE/roadmap/archive
   flips are scattered across the close WU's agent, `fire_terminal_flips`, and
   `auto_archive_feature` — #49 exists precisely because one flip lived in the
   agent for one path and nowhere for the other. Make a single driver-side
   function the authoritative owner of every terminal flip (PLAN.md included),
   called identically by both close paths, idempotent, with the hedged-verdict
   revert kept consistent. Subsumes the #49 fix.

3. **Harden the branch seam (#48).** `ensure_feature_branch` surfaces git's
   stderr instead of a traceback, carries expected `/pick-feature` flips onto
   the new branch, and detects a stale/divergent existing branch. May fold in
   here or ship as the standalone #48 bug fix — decide at draft time.

**Scope OUT.** New lifecycle *features* (this adds test + refactor coverage of
the existing lifecycle, not new behavior). Rewriting the auto-close predicate
itself (0018 stands). The per-bug hotfixes that are cheaper as standalone bug
branches (#48 especially) if they're needed before this feature is pulled.

**Status: planned.** Likely single gate: WU per lifecycle-path test +
terminal-ownership consolidation WU + closing ceremony. Pull before the next
feature that exercises an untested close-path combination.

<a id="feat-2026-0021"></a>
## FEAT-2026-0021 — Ceremony proportionality + slim WU template

_No inline detail section was recorded for this feature; stub written at archive time._

<a id="feat-2026-0022"></a>
## FEAT-2026-0022 — Deliverable-presence gate: machine-enforce per-WU `produces:` + empty-files escalation

**Goal.** The driver refuses to commit an implementation WU as `done` when a
declared deliverable is absent or empty, or when the WU touched zero files —
closing the zero/partial-deliverable hollow-pass class FEAT-2026-0008/0015 left
open. Filed from GitHub issue #41 and LEARNINGS
`[FEAT-2026-0020/G2/hollow-pass-presence-gates]` (T16 passed `done` touching
zero files at ~$1.48; T12 created `SECURITY.md` but not the bundled
`CODE_OF_CONDUCT.md`).

**Shape.** Single terminal gate, three driver-side guards + `close`, mirroring
FEAT-2026-0008. T01 adds the `produces:` WU frontmatter field (parse +
`WorkUnit.produces` + advisory lint WARN). T02 (`assert_declared_deliverables`)
blocks a `complete` whose declared `produces:` path is absent or empty. T03
(`assert_implementation_touched_files`) blocks an `implementation` WU whose
attempt touched zero deliverable files, independent of `produces:`.

**Scope OUT.** Symbol-level presence (`grep -q`), retrofitting `produces:` onto
existing WUs, broadening the verification contract, cost levers.


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
(`example-org/example-app#287`) run out-of-loop by human operator — discovery, adopt, and
report-back all PASS, `#287` fully restored post-smoke (T07). **Finding:** the adopted folder
failed `lint_plan.py` because orchestrator issue bodies use `## ATX` headings; the linter only
recognised `**bold**`/plain. Fix delivered in gate 4. GATE-03 status: `passed`.

**Gate 4 (passed).** ATX-heading linter fix: broadened `lint_plan.py`'s mandatory-section
detector to a union pattern (`^(?:#+\s*|\**)`) that accepts both Markdown ATX headings
(`## Context`) and the existing bold-preamble (`**Context.**`) form (T08). The adopted
`INIT-2026-0001-F06-…` folder now passes `lint_plan.py` exit-0, and existing bold-headed WU
bodies remain clean (regression guard). GATE-04 status: `passed`.

**Status: done.** All four gates passed. All four pipeline mechanisms — discover, adopt,
report-back, lint-clean grind — are proven live against `example-org/example-app#287`. The
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

<a id="feat-2026-0010"></a>
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

**Status: active. Gate 1 (passed).** Gate 1 shipped: `roadmap-archive.md` created, `Detail` column added to the table, `roadmap-archive` skill shipped, `roadmap-add` skill shipped, FEAT-2026-0003..0008 detail sections migrated to the archive. Main roadmap shed 223 lines (647 → 424); archive grew to 275 lines. **Gate 2 (passed).** Driver auto-archive hook shipped: `loop.py` now calls `auto_archive_feature` after flipping `PLAN.md` status to `complete`, automatically archiving the feature's roadmap detail section on feature close. Tests cover happy path, idempotency, and refusal. 1 WU (T05), 2 attempts, $2.05.

<a id="feat-2026-0002"></a>
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

<a id="feat-2026-0013"></a>
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

**Gate 1 (passed).** T01 audited `integration_workspace` and applied
two coupled fixes in one attempt (362.795 s, $0.327): (a) `git -c
gc.auto=0` on every `git` invocation inside the fixture body, killing
gc.autoDetach's post-parent-exit background-subprocess class; (b) a
`git -C <root> rev-parse HEAD` sync barrier in a `finally:` block
after the `yield root` line, forcing index-lock flush and pending
writer release before `TemporaryDirectory` teardown. `subprocess.run`
calls inside the fixture use `check=True` with completion-wait;
fixture remains a `@contextmanager` yielding `Path` (no API break).
50× local audit at T01 close: 50/50 clean. GATE-01 status: `passed`.

**Status: done.** `roadmap_goal` met — the close-session 50×
recursive audit, post-T01-squash on HEAD `2a9e2aa`, shows 50/50
unittest exits 0 with no `OSError: Directory not empty`, no
`FAILED`, no `ERROR`. `tail -1 | sort | uniq -c` returned one
distinct line across 50 runs (driver stdout from an inner
integration test, not unittest's verdict — see RETROSPECTIVE.md
"Reading the output"); exit-code count confirmed PASS:50 FAIL:0.
The race is eliminated locally; CI on a Py 3.12 runner is the
field test (next PR run). Two `[FEAT-2026-0013/G1-CLOSE]` entries
landed in LEARNINGS.md covering the gc.auto=0 + sync-barrier rule
and the `tail -1` oracle fragility. See `RETROSPECTIVE.md
§Feature-arc verdict`.

<a id="feat-2026-0014"></a>
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

<a id="feat-2026-0012"></a>
## FEAT-2026-0012 — Closing-WU deliverable guard

**Status: abandoned 2026-06-13 — folded into FEAT-2026-0015.** Scope
preserved here for audit; implementation moved into 0015 to avoid
building guards against a 4-WU taxonomy that 0015 then collapses.
See FEAT-2026-0015 detail section's `## Subsumed scope` for the
hollow-pass guard work this feature originally proposed.

---

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

<a id="feat-2026-0015"></a>
## FEAT-2026-0015 — Closing-ceremony restructure + hollow-pass guard

**Subsumes FEAT-2026-0012** (filed 2026-06-12, abandoned 2026-06-13
when this feature was scoped). 0012 proposed a driver-side closing-WU
deliverable guard against the 4-WU taxonomy. That investment would be
partially obsoleted by this feature's collapse of the taxonomy from
4 WU types to 2-3. Building the guard against the NEW taxonomy from
day 1 is cheaper end-to-end. The hollow-pass guard work is folded
into this feature's `## Subsumed scope` section below.

**Why.** The current 4-WU closing sequence (`retrospective → lessons →
docs → plan-next`) consistently consumes ~50% of feature cost despite
the inner three WUs (RETRO, LESSONS, DOCS) being summary+append work
on overlapping context. Live evidence from FEAT-2026-0010:

- Gate 1 close: $3.17 of $6.15 (52%); cache-creation across 4 WUs
  ≈ 209k tokens (each fresh session re-bootstraps the same context).
- Gate 2 close: $2.23 of $4.28 (52%); same shape.
- LESSONS WUs frequently produce 0-1 entries; DOCS WUs often produce
  empty diffs or `files_changed_mismatch` on the same file the close
  ceremony already touched.

The single-gate `close` alternative (FEAT-2026-0005) proved a combined
session works for terminal-of-single-gate: $0.83 on FEAT-2026-0014;
$1.84 on FEAT-2026-0013 v3-a3. Multi-gate features have no equivalent
shortcut today; their terminal gate also pays the full 4-WU tax even
though no `plan-next` is needed (terminal = nothing to plan).

**Goal.** Restructure the closing contract to two patterns:

- **Terminal gate (any feature, single- or multi-gate)**: single
  combined `close` WU. Folds retrospective + lessons + docs +
  feature-arc verdict into one session. Extends FEAT-2026-0005's
  pattern from single-gate-only to any-feature-terminal-gate.
- **Intermediate gate (multi-gate only)**: 2-WU close.
  `close-intermediate` (new type) folds RETRO + LESSONS + DOCS into
  one session; `plan-next` remains separate as today (high-stakes,
  opus, drafts next gate's WUs against fresh context).

Per-feature estimated savings: $1.50-3.00 + ~100k cache-creation
tokens per closed gate. Wall-time: 4 sessions → 2 per intermediate
gate, 4 → 1 per terminal gate.

**Scope.**

- New `close-intermediate` WU type in `loop.py` (`MODEL_BY_TYPE` +
  `EFFORT_BY_TYPE` + `GATES_FOR_TYPE` + verification routing).
- Update `.specfuse/templates/WU.template.md` and PLAN.md template to
  use 2-WU intermediate and 1-WU terminal patterns by default.
- Update `lint_plan.py` to accept the new shapes; reject the old
  4-WU sequence as deprecated (with a grandfather window for
  in-flight features so this PR doesn't break existing branches).
- Update `.specfuse/skills/authoring-work-units/SKILL.md` to document
  the new contract.
- Update `/draft-feature` skill to emit the new patterns.
- The `close-intermediate` WU type's prompt must demand explicit
  subsections: `## RETROSPECTIVE`, `## LEARNINGS to promote`,
  `## Docs reconciled` — the audit trail per-step the old per-WU
  sequence provided implicitly.

**Scope OUT.**

- Backfilling already-closed features (their 4-WU history stays as
  precedent).
- Changing `plan-next`'s shape — keep its dedicated session.
- Single-gate's existing `close` alternative — already correct
  shape; just rename `close-terminal` for clarity or leave as-is.

**Verification.** A dogfood feature (FEAT-2026-0016 or this feature
itself) closed under the new contract shows: (a) terminal-gate cost
≤ $1 (matches G1-CLOSE precedent); (b) intermediate-gate close cost
≤ $1 (close-intermediate, no plan-next); (c) lint accepts the new
shapes and rejects the old (modulo grandfather). `tests/test_lint_*`
updated.


<a id="feat-2026-0017"></a>

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
FEAT-2026-0015/T07's four) caught this:

- Zero-token guard: T06 ran productively.
- `files_changed` guard: T06 listed `loop.py` + the test file; both
  changed.
- Smoke-import guard: `fire_terminal_flips` symbol existed +
  imported.
- Closing-deliverable guards (T07): T07 didn't model wiring-race —
  it asserts on file existence and content shape post-pass, not on
  driver-state invariants that should fire as a CONSEQUENCE of the
  WU's effect.

**Delivered.** Driver-side post-pass invariant check, type-keyed.
For close-type WUs with `verdict: met`, asserts terminal gate
`passed`, roadmap row `done`, archive anchor present. On failure:
reset, attempt_outcome event, retry within budget. T02 added the
`produces_driver_helper` WU frontmatter field + lint warning for
implementation-WUs whose body claims driver-wiring without
declaring the symbol(s) produced. Recursive dogfood: G1-CLOSE was
intended to exercise the new guard against itself.

**Bonus deliverables surfaced by dogfood.** Three pre-existing
hollow-pass / methodology surfaces were also closed in this
feature's branch:

- `tests/test_loop_files_changed_guard.py` +
  `tests/test_loop_orchestration.py` `_init_git` helpers now run
  `git config commit.gpgSign false` after `git init`, matching the
  pattern at `tests/_workspace.py:36`. 20 pre-existing test errors
  (operator-global SSH signing + tempdir-git incompatibility)
  fixed.
- `assert_doc_or_roadmap_diff` (loop.py) now also accepts
  `.specfuse/LEARNINGS.md` and `RETROSPECTIVE.md` — resolves the
  T06 (driver owns roadmap flip) ↔ T07 (close-deliverable guard
  requires roadmap.md or docs/) contract contradiction surfaced
  by the post-T06 close-contract.
- `assert_closing_deliverables` diff-only-touches-wu bypass
  removed. Previously silently passed hollow close-ceremony
  attempts where only the driver's bookkeeping write touched the
  WU file. New regression test
  `test_close_fails_when_diff_only_touches_wu_file`.

**Verdict.** `met` — original wiring-race surface closed by T01;
three bonus hollow-pass surfaces also closed; Opus 4.7
verdict-flip blind-spot logged for deep-analysis. Full RETROSPECTIVE
+ cost analysis in
`.specfuse/features/FEAT-2026-0017-wiring-race-guard/RETROSPECTIVE.md`.
Actual cost $39.37 vs planned $3.20 — 12.3× overrun, all on
dogfood-surfaced bug discovery cycles where the agent worked
correctly but verify-gates failed for reasons outside WU scope.

<a id="feat-2026-0016"></a>
## FEAT-2026-0016 — Per-attempt outcome events + re-arm contract + audit trail

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
