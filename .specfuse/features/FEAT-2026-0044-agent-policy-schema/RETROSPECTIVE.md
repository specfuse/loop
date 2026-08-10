<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0044, agent-policy.yml schema + groom-backlog skill

**Correlation ID.** `FEAT-2026-0044/G1-CLOSE`. Single terminal gate, four
substantive work units, one close. Verdict recorded in this WU's frontmatter:
**`met_locally`** — every acceptance criterion below was re-verified by a fresh
command run in this session except three, listed in
[What the loop did NOT verify](#what-the-loop-did-not-verify), which is also the
`close-discipline.md` §2 follow-up record.

Two things about this feature are unusual and a reader will not infer them from
the diff: it was **drafted solo, with no operator interview**, and
**FEAT-2026-0048 was drafted against this schema before this schema existed**.
Both are audited below, in
[Solo-drafting decision audit](#solo-drafting-decision-audit) and
[Did the shipped schema diverge from what T01 declared?](#did-the-shipped-schema-diverge-from-what-t01-declared).

## Gate 1 — what shipped

- **T01 — the schema, the example, the validator.** `specfuse/loop/agent_policy.py`
  with `validate_agent_policy(path=None) -> list[str]`, module-level `frozenset`
  enums (`SEVERITY_VALUES`, `AUTOMERGE_VALUES`, `GATE_REVIEW_VALUES`), a
  `REQUIRED_TOP_LEVEL_FIELDS` tuple, per-section `_check_*` helpers and a
  `main() -> int` that exits `1` only when a finding starts with `ERROR: `.
  Shipped alongside `.specfuse/agent-policy.yml.example`, the thin shim
  `.specfuse/scripts/lint_agent_policy.py`, and the `agent-policy-example-lint`
  gate in `.specfuse/verification.yml`. It reuses `lint_monitoring.py`'s *shape*
  and imports nothing from it — `grep -n lint_monitoring specfuse/loop/agent_policy.py`
  returns two docstring lines and no import.
- **T02 — the reader and the queue-vs-roadmap check.** `load_policy(path=None) -> dict`
  (raising `FileNotFoundError` rather than returning defaults, so "no policy
  file" and "empty queue" stay distinguishable), a new public
  `lint_roadmap.roadmap_statuses(repo_root=None) -> dict` implemented over the
  existing `_parse_table_rows`, and `_check_queue_against_roadmap` applying the
  WARN/ERROR split. T02 also authored this repo's live
  `.specfuse/agent-policy.yml` and widened the CI gate to lint both the example
  and the live file.
- **T03 — the waiting dial, supplied.** `resolve_triage_auto(path=None) -> bool`,
  `True` only when `rules.triage.auto` is boolean `true`, `False` when the file
  or the key is absent. `plugins/specfuse/skills/triage-issues/SKILL.md` now
  tells the session to call it instead of asking the operator each run, and
  restates the settled `auto=True` semantics verbatim (non-`high` confidence is
  recorded as `question` and routed to `needs-human`, still marked, never
  skipped). `specfuse/loop/triage.py` was not the WU's to change.
- **T04 — `/groom-backlog`.** A propose-and-confirm skill in
  `plugins/specfuse/skills/groom-backlog/SKILL.md`, vendored to
  `.specfuse/skills/` and discovery-symlinked from `.claude/skills/`, with a
  markdown-contract test asserting its structure: the real API names, the
  queue-hygiene pass distinguishing `WARN: ` from `ERROR: `, the "What this
  skill does NOT do" section including the no-`--auto` rule, the one file it
  writes, empty-queue-is-valid, and the escalation-framing section.

## Oracles re-run fresh in this session

`close-discipline.md` §1. Every command below was executed in this close
session against the working tree; exit codes are read directly from the shell,
not inherited from any work unit's RESULT block. The full `code` gate set from
`.specfuse/verification.yml`, in declaration order:

| Gate | Command | Exit |
|---|---|---|
| `tests` | `python3 -m unittest discover -s tests -v -b` | **0** |
| `lint` | `ruff check specfuse .specfuse/scripts tests scripts` | **0** |
| `security` | `bandit -r specfuse .specfuse/scripts -ll` | **0** |
| `coverage` | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | **0** |
| `leak-scan` | `python3 .specfuse/scripts/leak_scan.py --all` | **0** |
| `agent-policy-example-lint` | `python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml` | **0** |
| `event-type-gate` | `python3 .specfuse/scripts/event_type_gate.py` | **0** |
| `roadmap-link-gate` | `python3 .specfuse/scripts/roadmap_link_gate.py` | **0** |
| `arm-sweep-gate` | `python3 .specfuse/scripts/arm_sweep_gate.py` | **0** |
| `monitoring-example-lint` | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | **0** |

Notable output rather than bare exits:

- `tests` — `Ran 2601 tests in 119.685s / OK (skipped=3)`. Re-run a second time
  after this close wrote its own artifacts (`RETROSPECTIVE.md`,
  `LEARNINGS-pending.md`, `CHANGELOG.md`, `.specfuse/roadmap.md`,
  `GATE-01-CRITERIA.md`), since several suites assert on exactly those files:
  `Ran 2601 tests in 98.517s / OK (skipped=3)`, exit 0 again. `lint`,
  `event-type-gate`, `roadmap-link-gate`, `arm-sweep-gate` and `leak-scan` were
  likewise re-run after the edits and stayed at exit 0. `coverage` was not
  re-run after them — the close added no Python.
- `coverage` — `TOTAL 8339 560 93%`, over the `--fail-under=90` floor.
  `specfuse/loop/agent_policy.py` itself reads `190 21 89%`; the gate is a
  package-wide floor, not a per-module one, so this is a pass, but it is the
  lowest-covered new module the feature shipped and worth a reader's eye.
- `leak-scan` — `gitleaks 8.30.1 / leak-scan: clean`.
- `event-type-gate` — `no validation errors across 56 events.jsonl file(s), 1348 event(s) checked`.
- `roadmap-link-gate` — `0 error(s), 5 warning(s)`. All five warnings are
  pre-existing `Detail cell is '—' but a detail section already exists` tidiness
  findings on other features — FEAT-2026-0011, 0047, 0049, 0050 and 0052 — and
  the gate deliberately does not fail on WARN. None of them names
  FEAT-2026-0044, and the count is unchanged by this close's roadmap edit.
- `arm-sweep-gate` — `evaluable=17 evaluated=17 could_not_evaluate=0`, no
  `not_evaluable` verdicts.

The `code` set holds six further gates — the bats operator-script suites
`leak-scan-hook`, `sync-scaffold-bats`, `sync-scaffold-symlinks-bats`,
`init-sh-shim-bats`, `init-skills-bats` and `hookspath-conflict-bats`. None is
named in this WU's criterion 1 and none was re-run here; see
[What the loop did NOT verify](#what-the-loop-did-not-verify), entry 4.

### `validate_agent_policy()` against both files

Criterion 2, run fresh in-process rather than through the shim, so the finding
list itself is observed and not just an exit code:

```
$ python3 -c "from specfuse.loop.agent_policy import validate_agent_policy; ..."
.specfuse/agent-policy.yml         -> NO FINDINGS   (ERROR findings: [])
.specfuse/agent-policy.yml.example -> NO FINDINGS   (ERROR findings: [])
```

Neither file returns an `ERROR: ` finding. Neither returns a `WARN: ` finding
either — the live queue (`FEAT-2026-0048`, `FEAT-2026-0047`, `FEAT-2026-0049`)
names three features that are all still `planned` in `roadmap.md`.

### Scoped oracles behind the per-criterion state

Recorded here because `GATE-01-CRITERIA.md` cites them per criterion:

| Command | Exit | Result |
|---|---|---|
| `python3 -m unittest tests.test_agent_policy_schema` | 0 | Ran 23 tests — OK |
| `python3 -m unittest tests.test_agent_policy_queue` | 0 | Ran 10 tests — OK |
| `python3 -m unittest tests.test_agent_policy_triage_dial` | 0 | Ran 4 tests — OK |
| `python3 -m unittest tests.test_groom_backlog_skill` | 0 | Ran 10 tests — OK |
| `python3 -m unittest tests.test_triage_apply` | 0 | Ran 7 tests — OK |
| `python3 -m unittest tests.test_skills_vendored_in_sync` | 0 | Ran 4 tests — OK |
| `python3 -m unittest tests.test_skill_discovery_links` | 0 | Ran 4 tests — OK |
| `python3 -c "from specfuse.loop.agent_policy import validate_agent_policy"` | 0 | — |
| `python3 -c "from specfuse.loop.agent_policy import load_policy; from specfuse.loop.lint_roadmap import roadmap_statuses"` | 0 | — |
| `python3 -c "from specfuse.loop.agent_policy import resolve_triage_auto"` | 0 | — |
| `python3 -c "roadmap_statuses()"` spot check | 0 | `FEAT-2026-0002 -> done`, `FEAT-2026-0011 -> blocked` |
| `diff -q plugins/…/groom-backlog/SKILL.md .specfuse/skills/groom-backlog/SKILL.md` | 0 | byte-identical |
| `diff -q plugins/…/triage-issues/SKILL.md .specfuse/skills/triage-issues/SKILL.md` | 0 | byte-identical |
| `readlink .claude/skills/groom-backlog` | 0 | `../../.specfuse/skills/groom-backlog` |

## The satisfiability claim, re-tested

`PLAN.md` § *Escalation-predicate satisfiability* claims the WARN/ERROR split
makes this gate satisfiable on a correct tree. Criterion 3 required re-testing
it rather than assuming it. Two purpose-built policy files were written outside
the repo (in `$TMPDIR`), identical to the shipped example except for one queue
entry, and each was run through the real gate command:

```
$ python3 .specfuse/scripts/lint_agent_policy.py $TMPDIR/pol_done.yml
WARN: queue: 'FEAT-2026-0002' is roadmap status 'done'
EXIT=0

$ python3 .specfuse/scripts/lint_agent_policy.py $TMPDIR/pol_ghost.yml
ERROR: queue: 'FEAT-2026-9999' has no row in roadmap.md
EXIT=1
```

Both halves behave exactly as `PLAN.md` claims: a queued feature going `done` —
which will happen to this repo's own queue as a matter of course — prints a
warning and **does not** fail CI, and a FEAT-ID with no roadmap row **does**.
The gate is satisfiable on a correct tree. This is the negative observation
`verification-discipline.md` §3 asks for: the rule was seen rejecting a
purpose-built bad input, not merely accepting a good one.

## Solo-drafting decision audit

This feature was drafted without an operator interview, on operator
instruction (2026-08-09). `PLAN.md` § *Assumed decisions* records seven
decisions a `/draft-feature` interview would have asked about. The operator's
veto checkpoint is this feature's PR, and that review is only as good as this
record, so each is marked **validated** (the implementation exercised it and it
held), **strained** (it held but cost something, or turned out to mean
something other than what the plan said), or **unexercised** (nothing in this
feature tested it either way).

1. **Single gate, single terminal `close`.** — **validated.** Four substantive
   work units, each passing on `attempt: 1` with `re_arm_count: 0`. No WU
   needed a gate boundary's worth of review to proceed, and the dependency
   chain (T01 → T02 → {T03, T04}) resolved without a re-plan. A second gate
   would have bought a review checkpoint over work that never went sideways.
2. **`autonomy_default: auto`.** — **strained.** `PLAN.md` predicted this was
   "close to a no-op on a single-gate feature — there is no next gate to arm".
   That was wrong about which mechanism the dial actually reaches. On a
   single-gate feature `auto` never auto-arms anything, but it *does* switch on
   FEAT-2026-0053/T09's staging invariant: a closing WU under `auto` may not
   touch `.specfuse/LEARNINGS.md`, and lessons stage to a feature-local
   `LEARNINGS-pending.md` instead. **This close is the first time that mechanism
   has ever fired in this repo** — no `LEARNINGS-pending.md` existed anywhere
   under `.specfuse/features/` before it. The collision is concrete: this WU's
   own acceptance criterion 6 reads "`.specfuse/LEARNINGS.md` gains at least one
   entry", which the driver's `assert_learnings_staged_under_auto` would refuse.
   See [Lessons](#lessons-promoted) for how that was resolved.
3. **Queue entries are FEAT-IDs only, not a heterogeneous work list.** —
   **validated.** `_FEAT_ID_RE` plus one `roadmap_statuses()` lookup per entry
   is the whole queue check; no consumer in T02, T03 or T04 had to disambiguate
   what kind of thing a queue entry was. `/groom-backlog` reads triaged issues
   as *candidates for the roadmap*, never as queue entries, which is exactly
   the separation the decision predicted.
4. **Queue drift severity split WARN/ERROR, not uniformly fatal.** —
   **validated, and re-tested this session** — see
   [The satisfiability claim, re-tested](#the-satisfiability-claim-re-tested).
   One refinement the plan did not state: `deferred` also produces no finding,
   alongside `planned`/`active`/`blocked`. `_check_queue_against_roadmap`'s
   docstring justifies it ("a legitimate parked slot, per the roadmap's own
   status legend") and T02's criterion 7 tested all four. That is a widening of
   the silent set relative to the roadmap row's prose, and it is the right
   call, but it is the operator's to veto.
5. **Validator returns `list[str]` and is a sibling of, not a caller into,
   `lint_monitoring.py`.** — **validated.** `agent_policy.py` imports
   `re`, `pathlib`, `._miniyaml` and `.lint_roadmap` only; the two references
   to `lint_monitoring` in the file are both docstring prose explaining the
   non-dependency. The shape transferred (frozenset enums, `REQUIRED_*` tuples,
   `_check_*` helpers, `main() -> int`) with no code shared.
6. **This repo bootstraps a real `.specfuse/agent-policy.yml`, and the CI gate
   points at it.** — **validated, and strengthened past the plan.** T02 pointed
   the gate at *both* the example and the live file rather than swapping one
   for the other, so the example cannot drift from the validator and the live
   file cannot drift from the roadmap. Both lint clean this session.
7. **`/groom-backlog` proposes and writes only on explicit accept; no `--auto`
   mode.** — **unexercised.** The skill ships, is vendored, is discovery-linked,
   and its structure is asserted by ten tests — but no one has run it. Nothing
   in this gate invokes it, deliberately: T04's body forbade any WU from
   subprocess-invoking it, because a skill whose whole contract is "a human
   accepts the proposal" cannot be exercised by a loop session. The propose-only
   posture is therefore a claim backed by the skill text and by the absence of
   an `--auto` code path, not by an observed run.

**Reading of the seven as a set.** Five held, one held with a correction the
operator should see (4's `deferred` widening), one turned out to mean something
the plan did not anticipate (2), and one is untested by construction (7). No
decision was contradicted by the implementation. The one that cost something —
decision 2 — cost it in this close, not in the build.

## Did the shipped schema diverge from what T01 declared?

**Yes, in one place, and it is a YAML-spelling requirement rather than a moved
or renamed field.** Named explicitly because FEAT-2026-0048's `T01` verifies the
shipped schema against what it assumed and is instructed to escalate on
divergence rather than adapt silently.

**The field: `rules.bugs.automerge`.** T01's WU body declared the schema with
the line written unquoted:

```yaml
    automerge: off              # off | on  — enforcement is FEAT-2026-0048's
```

The shipped example and the shipped live file both write it **quoted**:

```yaml
    automerge: "off"             # "off" | "on" — enforcement is FEAT-2026-0048's
```

This is not stylistic. The repo's `_miniyaml` parser rejects the unquoted form
outright — verified this session by copying the shipped example, unquoting that
one value, and running the validator over the copy:

```
ERROR: <copy>: could not parse as YAML: line 26: only lowercase `true`/`false`
accepted as booleans (got 'off')
```

So an unquoted `automerge: off` is not a lenient alternative spelling; it is a
hard parse failure that takes the whole file down with it.

**What this means for FEAT-2026-0048, precisely.** Its `T01` carries a
six-row *assumed surfaces* table. **All six rows hold as assumed**:
`specfuse/loop/agent_policy.py` exists; `load_policy(path=None) -> dict` returns
the parsed mapping; `validate_agent_policy(path=None) -> list[str]` returns
findings prefixed `ERROR: ` / `WARN: `; `rules.bugs.automerge` is `off` | `on`
defaulting to `off`; `rules.bugs.min_severity` is
`low`|`medium`|`high`|`critical`; `rules.bugs.preempt` is a bool. Read through
`load_policy`, the value of `rules.bugs.automerge` is the string `"off"` — which
is what `AUTOMERGE_VALUES` contains and what 0048's planned
`resolve_bug_automerge()` ("`True` only when `rules.bugs.automerge` is exactly
the string `"on"`") is already written against.

The one place 0048 will notice is textual: its `WU-90` criterion 1 reads "this
repo's `.specfuse/agent-policy.yml` still has `rules.bugs.automerge: off`", and
its `T01` criterion 9 asks for "a test asserts this explicitly". A test that
greps the raw file for the literal `automerge: off` **will not match**; a test
that reads the parsed value **will**. 0048 should assert the parsed value, and
its two new dials (`max_diff_lines`, `max_merges_per_day`) are plain ints and
need no such care.

Because every assumed surface holds and only the on-disk quoting differs, this
was recorded rather than escalated. If the operator reads it the other way —
that a divergence is a divergence and 0048's T01 should be re-drafted before it
runs — that is a one-line edit to 0048's `WU-90` criterion 1 and to its `T01`
criterion 9, and it is the operator's call to make at this PR.

**No other divergence.** Required top-level keys, all three enum sets, the
optional `rules.features.overrides` map, the `budgets` triple, the `escalation`
quad and the empty-queue-is-valid rule all match T01's declaration exactly.
One in-feature revision worth naming so it is not mistaken for drift: T01's
criterion 15 specified the `agent-policy-example-lint` gate command as the
example file only, and T02's criterion 10 deliberately widened it to both files
once the live file existed. That was planned in T02's body, not discovered.

## Consumer-visible contract changes

`close-discipline.md` §3. Four items, all additive; none removes or renames an
existing surface. Appended to `CHANGELOG.md`'s `Unreleased` section, traced to
`FEAT-2026-0044`.

1. **`.specfuse/agent-policy.yml`, a new configuration file and its schema.**
   Five required top-level keys (`version`, `queue`, `rules`, `budgets`,
   `escalation`); unknown top-level keys are an `ERROR: `, not ignored, so a
   typo in a dial name cannot read as a default. `version` must be `1`.
   `queue` is an ordered list of `FEAT-YYYY-NNNN` strings and **may be empty** —
   an empty queue is a meaningful declared state ("work bugs only, ask for
   priorities"), not a finding. `rules.bugs.automerge` and
   `rules.bugs.min_severity` take **quoted** string values. The file is
   optional: nothing in the loop requires it to exist, and every reader has a
   defined absent-file behaviour (`load_policy` raises `FileNotFoundError`,
   `resolve_triage_auto` returns `False`).
2. **`agent-policy-example-lint`, a new `code` gate in
   `.specfuse/verification.yml`.** It runs the validator over
   `.specfuse/agent-policy.yml.example` **and** `.specfuse/agent-policy.yml`.
   In this repo both exist. A downstream project that copies this gate wholesale
   without creating a live policy file will get `ERROR: … file does not exist`
   and a red gate — the second half of the command is this repo's dogfood, not a
   default every project should adopt unedited.
3. **`specfuse.loop.lint_roadmap.roadmap_statuses(repo_root=None) -> dict`, a
   new public function.** Maps every FEAT-ID in `roadmap.md` to its status
   string, including `done`, `abandoned` and `deferred` rows. Returns `{}` when
   `roadmap.md` is absent rather than raising. It is a thin public wrapper over
   the existing private `_parse_table_rows`, whose behaviour is unchanged; a
   consumer that had been reaching into the private helper should switch.
4. **`/triage-issues` changes where its `auto` dial comes from.** It previously
   left `auto` off unless the operator asked for it per run; it now calls
   `specfuse.loop.agent_policy.resolve_triage_auto()` and passes the result
   through. **The default is unchanged** — no policy file, or no
   `rules.triage.auto` key, still resolves to `False` — so a project that does
   nothing sees identical behaviour. What changes is that a project *can* now
   turn it on once, in a file, instead of per invocation, and that the operator
   is no longer prompted. `apply_triage`'s semantics are untouched: under
   `auto=True` a non-`high`-confidence decision is still recorded as `question`
   and routed to `needs-human`, still marked, never skipped. Also new and
   consumer-visible: **`/groom-backlog`**, a new skill in the published plugin,
   vendored into `.specfuse/skills/` and discovery-symlinked, so any project
   upgrading its scaffold gains a slash command. It proposes a queue and writes
   exactly one file, `.specfuse/agent-policy.yml`, only on explicit accept; it
   has no `--auto` mode by design.

**Human acknowledgment of this list has not been given** — see
[What the loop did NOT verify](#what-the-loop-did-not-verify), entry D1.

## Cost analysis

Every figure below is read from this feature's `events.jsonl`. Per-WU actuals
are the `task_completed` payload's `cumulative_cost_usd`, which folds in every
re-arm cycle; `attempts_lifetime` is quoted alongside so the reader can see
there were none to fold.

| Work unit | Planned | Actual (cumulative) | Delta | Attempts (lifetime) | Re-arms |
|---|---:|---:|---:|---:|---:|
| T01 — schema, example, validator | $4.00 | $1.227266 | **−$2.772734 (−69.3%)** | 1 | 0 |
| T02 — reader + queue drift | $3.50 | $1.593053 | **−$1.906947 (−54.5%)** | 1 | 0 |
| T03 — wire the triage dial | $2.50 | $0.949437 | **−$1.550563 (−62.0%)** | 1 | 0 |
| T04 — `/groom-backlog` skill | $4.00 | $0.784942 | **−$3.215058 (−80.4%)** | 1 | 0 |
| **Substantive subtotal** | **$14.00** | **$4.554698** | **−$9.445302 (−67.5%)** | 4 | 0 |
| G1-CLOSE — this unit | $5.00 | in flight (driver stamps it) | — | 1 recorded + this one | 0 |

- **Against the gate budget.** `GATE-01.md` sets `cost_budget_usd: 23.00`. The
  four substantive units consumed **$4.554698, or 19.8%** of it. Even a close
  that ran to its full $5.00 plan lands the gate near **$9.55, about 42%** of
  budget.
- **Against `PLAN.md`'s feature total.** `planned_cost_usd: 19.00`, which is
  exactly the sum of the five work units' plans ($14.00 + $5.00) — the plan and
  the graph agree, with the gate budget carrying $4.00 of separate headroom.
  Feature actual to date is **$4.554698, 24.0% of the $19.00 plan**, before this
  close's own cost is stamped.
- **One prior attempt cost nothing.** `G1-CLOSE` attempt 1 recorded
  `outcome: prep_halted`, `cost_usd: 0.0`, `duration_seconds: 0.0` — the driver
  refused it before dispatch because the WU declared `oracles: [recent-commits]`
  while `verification.yml` defines a `recent-commits` *gate inside* the
  `oracles` set, not a set by that name. It cost a human escalation and a
  one-line frontmatter fix (`oracles: [oracles]`), and zero dollars.

### Why all four substantive units came in over 50% under plan

**One cause, four instances: the estimates were priced for discovery that the
plan had already done.** Each of T01–T04 was drafted with its load-bearing
strings fixed in advance — the module path, the validator signature, the finding
prefixes, the dial's location in the schema, the exact function to call — and
each named the existing file to copy the shape from (`lint_monitoring.py` for
T01, `_parse_table_rows` for T02, `apply_triage`'s settled semantics for T03,
`/pick-feature` for T04). None of the four had to find anything. The variance is
therefore not a sign the units were cheap or thin: `agent_policy.py` is 358
lines and `tests/test_agent_policy_schema.py` alone is 252, and T01 — which
wrote most of the former and all of the latter — still came in at 31% of plan,
because the expensive part of a validator is deciding what the schema is, and
that had been decided at draft time.

T04's −80.4% is the largest and has a second contributor: a skill file plus a
markdown-contract test involves no design search at all once the section list is
fixed, and T04's body fixed it — eight of its eleven acceptance criteria name
the exact section the test must find. The honest reading is that **$4.00 was the
wrong number for T04, not that T04 under-delivered**; the same is true, less
sharply, of the other three.

**The actionable form of this** is that a solo-drafted plan that front-loads
every load-bearing string should price its implementation units *lower* than a
plan drafted from an interview, because the interview's discovery cost has
already been paid in the drafting. That is a candidate lesson, staged in
`LEARNINGS-pending.md`.

### Failure-class breakdown

(no non-passing attempts in scope)

Every substantive work unit in gate 1 passed on its first attempt with
`failure_class: null`. The one non-passing attempt in this feature's
`events.jsonl` — `G1-CLOSE` attempt 1, `prep_halted` — belongs to this work unit
and is excluded from its own breakdown by the same rule the driver applies; it
is described in [Cost analysis](#cost-analysis) instead.

## Documentation

`.specfuse/roadmap.md`'s FEAT-2026-0044 detail section carried one sentence that
no longer described what shipped: it said queue entries "must exist and be
`planned`/`active`/`blocked`", which predates the WARN/ERROR split
`PLAN.md` settled and is silent about `deferred`. The detail section now states
the delivered rule — absent row is an `ERROR: ` that fails the gate,
`done`/`abandoned` is a `WARN: ` that does not, and `deferred` is silent — and
names the four things the feature actually shipped. The row's status and the
detail section's status line both read `active` and agree; the terminal flip to
`done` is the driver's to make, gated on the verdict, and this close does not
write it.

## Lessons promoted

**Nothing generalizes into `.specfuse/LEARNINGS.md` from this close — not
because nothing was learned, but because this feature runs
`autonomy_default: auto`, and under `auto` a closing WU that touches
`.specfuse/LEARNINGS.md` fails `assert_learnings_staged_under_auto`
(reason `learnings_not_staged`).** No human read this gate before the close
dispatched, so a lesson written here would compound into every future feature's
planning context unreviewed. Two candidate lessons are staged in this feature's
`LEARNINGS-pending.md` for the operator to promote, narrow, or reject at PR
review.

This is the **first time the staging mechanism has fired in this repository**.
FEAT-2026-0053 built it and then correctly did not use it — that feature ran
`review`, and its retrospective says so explicitly, noting that "its first real
exercise belongs to the first `auto` feature". This is that feature. The
mechanism worked as designed; what it collided with is this WU's own acceptance
criterion 6, written as "`.specfuse/LEARNINGS.md` gains at least one entry, or
carries an explicit note that nothing generalized", which offers no third branch
for the `auto` case. The second branch is taken here, with the staging file
carrying the substance. That collision is itself one of the two staged lessons.

## Hedged-verdict follow-up record

Three entries, one per acceptance criterion this close could not settle. Each
gives the criterion verbatim, why it is unverifiable here, the exact condition
that would upgrade it, and its `kind:`. This section and
[What the loop did NOT verify](#what-the-loop-did-not-verify) describe the same
three items; this one carries the classification.

### D1 — Human acknowledgment of the consumer-visible contract-change list

- **Criterion, verbatim** (`close-discipline.md` §3): "The close enumerates
  every consumer-visible addition, removal, or rename the feature makes across
  ALL its producing WUs — API surface, generated models, published schemas, CLI
  flags, whatever contract consumers depend on — and **blocks on explicit human
  acknowledgment of the list**."
- **Why unverifiable here:** the enumeration exists and is complete (four items,
  above, and in `CHANGELOG.md`'s `Unreleased`), but an agent cannot supply the
  acknowledgment it is collecting. `operator-escalation.md` names writing the
  human's own justification for them as a failure the rule exists to prevent.
- **Re-run condition that would upgrade this:** the operator reads the four
  items at this feature's PR and acknowledges them — which for this feature is
  the same read that discharges the solo-drafting veto checkpoint, so it is one
  review, not two.
- **kind:** `acceptance-discharged`

### D2 — `specfuse/loop/triage.py` is unmodified by T03

- **Criterion, verbatim** (T03 acceptance criterion 8): "`specfuse/loop/triage.py`
  is **unmodified** by this WU — `git diff --stat` shows no change to it, and
  the existing `tests/test_triage_apply.py` passes untouched."
- **Why unverifiable here:** the criterion names `git diff --stat` as its
  oracle, and a work-unit session runs no `git` at all (`result-contract.md`
  rule 1, `never-touch.md` §3). The pre-dispatch `diff-stat` oracle capture is
  truncated to a byte budget and does not enumerate all 33 changed paths, so it
  cannot answer the question either. **The second half of the criterion was
  verified:** `python3 -m unittest tests.test_triage_apply` ran clean in this
  session (7 tests, OK), which is the behavioural proof that `apply_triage`'s
  semantics survived; only the diff-shaped half is open.
- **Re-run condition that would upgrade this:**
  `git diff --stat main -- specfuse/loop/triage.py` returning empty output, run
  by anyone with git access — the PR's own file list answers it at review.
- **kind:** `externally-verifiable-later`

### D3 — The red half of the four red-test-first criteria

- **Criterion, verbatim** (T01#1, and identically T02#1, T03#1, T04#1): "…exists
  and **fails on HEAD before this WU runs** (the module and the test file do not
  yet exist, which counts as red)."
- **Why unverifiable here:** the assertion is about a tree state that no longer
  exists. Re-running the named test today proves the *green* half and can never
  prove the red half, because the code the test needs is now present. Reaching
  the red state requires checking out each WU's parent commit, which is a `git`
  operation this session may not perform. All four named tests exist and pass —
  `tests.test_agent_policy_schema` (23 tests),
  `tests.test_agent_policy_queue` (10), `tests.test_agent_policy_triage_dial`
  (4), `tests.test_groom_backlog_skill` (10), all exit 0 — so the entries are
  recorded `pass` in `GATE-01-CRITERIA.md` on the strength of the half that is
  assertable.
- **Re-run condition that would upgrade this:** check out each work unit's
  parent commit and run the named test nodeid, expecting a failure — e.g.
  `git checkout <parent-of-T01-squash> && python3 -m unittest
  tests.test_agent_policy_schema.TestValidateAgentPolicy.test_shipped_example_validates_clean`.
  Cheap, but it needs git.
- **kind:** `externally-verifiable-later`

**Verdict ceiling.** Two of the three entries are
`externally-verifiable-later`, so by
`closing_requirements.verdict_ceiling_for_kinds` **rework exists**: a re-run in
an environment permitted to use git would settle D2 and D3, leaving D1, whose
discharge *is* the operator accepting the verdict. The operator therefore has a
real choice between accepting `met_locally` now at PR review and asking for the
two git-shaped checks first.

## What the loop did NOT verify

Four entries. The first three are the hedged-verdict follow-up record above,
restated here with where each actually gets checked; the fourth is a scope note
rather than an unmet criterion.

1. **Human acknowledgment of the consumer-visible contract-change list (D1).**
   *Where it actually gets checked:* the operator's read of this feature's PR —
   the same read that is this feature's solo-drafting veto checkpoint.
2. **`specfuse/loop/triage.py` unmodified, by diff (D2).** *Where it actually
   gets checked:* the PR's changed-files list, or `git diff --stat main --
   specfuse/loop/triage.py` run by anyone with git access. The behavioural half
   is already checked by `tests/test_triage_apply.py`, which runs in the `tests`
   gate on every CI run.
3. **The red half of the four red-test-first criteria (D3).** *Where it actually
   gets checked:* nowhere automatically, by construction — a red-test-first
   claim is verified once, by the producing session, at the moment it is true.
   The durable protection is that all four tests exist and are wired into the
   `tests` gate, so a regression that would have made them red again fails CI.
4. **Six `code` gates were not re-run in this close: `leak-scan-hook`,
   `sync-scaffold-bats`, `sync-scaffold-symlinks-bats`, `init-sh-shim-bats`,
   `init-skills-bats`, `hookspath-conflict-bats`.** These are the bats
   operator-script suites. This WU's criterion 1 enumerates the ten gates it
   requires and none of these is among them, and no work unit in this feature
   touched `init.sh`, `sync-scaffold.sh`, the pre-commit hook, or
   `install-hooks.sh`. Saying so explicitly because "the full `code` gate set"
   is a phrase that reads as *all of them*, and it was not all of them.
   *Where they actually get checked:* CI runs the whole set from
   `verification.yml` on the PR, `scripts/smoke-test.sh` derives its gate list
   from the same file, and the driver re-runs this WU's declared gate set at
   exit.

**No predecessor auto-close debt.** This feature has one gate and no
`<!-- specfuse:autoclose-debt -->` marker anywhere in its folder; nothing
auto-closed here and there is no deferred close to reconcile.
