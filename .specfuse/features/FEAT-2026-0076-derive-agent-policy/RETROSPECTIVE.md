## Gate 1

Gate 1 asked whether a greenfield repository can be interviewed into a valid
policy file. What it decided: `propose_policy_defaults` proposes only what
evidence answers, every proposal it emits validates clean, and the skill's prose
describes that algorithm. What it did **not** decide is recorded under *What the
loop did NOT verify* below, in the words `PLAN.md` fixed in advance — a green
gate here is not evidence that an agent following the prose reproduces the
algorithm.

Four implementation WUs, four first-attempt passes, one hygiene WU inserted
mid-gate by operator review. Full `code` gate set re-run fresh in this close
session: 16 of 16 green.

### Oracles re-run fresh (`close-discipline.md` §1)

Every command below was executed in this close session with its exit code read
directly from the process; none is inherited from a producing WU's self-report.
The gate list is the full `code` set from `.specfuse/verification.yml`, in
declaration order, run from the repository root against the working tree as it
stands at this attempt.

| # | gate | command | exit |
|---|---|---|---|
| 1 | tests | `python3 -m unittest discover -s tests -v -b` | 0 |
| 2 | lint | `ruff check specfuse .specfuse/scripts tests scripts` | 0 |
| 3 | security | `bandit -r specfuse .specfuse/scripts -ll` | 0 |
| 4 | coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | 0 |
| 5 | leak-scan | `python3 .specfuse/scripts/leak_scan.py --all` | 0 |
| 6 | agent-policy-example-lint | `python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml` | 0 |
| 7 | event-type-gate | `python3 .specfuse/scripts/event_type_gate.py` | 0 |
| 8 | roadmap-link-gate | `python3 .specfuse/scripts/roadmap_link_gate.py` | 0 |
| 9 | arm-sweep-gate | `python3 .specfuse/scripts/arm_sweep_gate.py` | 0 |
| 10 | monitoring-example-lint | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | 0 |
| 11 | leak-scan-hook | `bats tests/leak_scan_hook.bats` | 0 |
| 12 | sync-scaffold-bats | `bats tests/sync_scaffold.bats` | 0 |
| 13 | sync-scaffold-symlinks-bats | `bats tests/sync_scaffold_symlinks.bats` | 0 |
| 14 | init-sh-shim-bats | `bats tests/init_sh_shim.bats` | 0 |
| 15 | init-skills-bats | `bats tests/init_skills_idempotent.bats` | 0 |
| 16 | hookspath-conflict-bats | `bats tests/hookspath_conflict.bats` | 0 |

`tests`: `Ran 2837 tests in 106.835s / OK (skipped=3)`. `coverage`: same 2837
tests, `TOTAL 9071 stmts / 603 miss / 93%`, over the gate's `--fail-under=90`.
`leak-scan`: `gitleaks 8.30.1 / leak-scan: clean`. `security`: the one
`# nosec B602` suppression at `specfuse/loop/loop.py:3206` is the pre-existing,
documented one; no new finding.

Four narrow oracles were additionally re-run for the per-criterion record in
`GATE-01-CRITERIA.md`, all exit 0:

| oracle | result |
|---|---|
| `python3 -m unittest tests.test_policy_proposals -v` | `Ran 21 tests / OK` |
| `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v` | `Ran 21 tests / OK` |
| `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v` | `Ran 20 tests / OK` |
| `python3 -c "from specfuse.loop.policy_proposals import propose_policy_defaults"` | symbol resolves |

**Environment note.** The gate set was run outside the session sandbox. Under
the sandbox, roughly a dozen tests that shell out to `git` over the network go
falsely red; the exit codes above are therefore the honest ones, and they are
the same environment (`oracle_env: macos_local`) the producing WUs ran in.

### `propose_policy_defaults` re-run fresh against every shipped fixture

Every fixture shape the shipped test suite constructs was rebuilt and
`propose_policy_defaults` re-run against it in this session — not asserted
through the tests, but called directly and its return value printed, so the
withheld keys are observed rather than inferred from a green test. The four
in-scope values are `max_tokens_per_run`, `max_items_per_day`, `test_paths`,
`max_open_prs`; "withheld" means the key is absent from the returned mapping
entirely, which is the module's designed way of saying *no evidence*.

| fixture | proposed | withheld | values |
|---|---|---|---|
| F1 empty repo (`.specfuse/` only) | — | all four | — |
| F2 `.specfuse/features/` present, no `events.jsonl` | — | all four | — |
| F3 `events.jsonl`, 2 passing implementation WUs | `max_tokens_per_run`, `max_items_per_day` | `test_paths`, `max_open_prs` | 900000, 1 |
| F4 events + `tests/` + gate command + ok runner | all four | — | 600000, 1, `['tests/']`, 3 |
| F5a history p90 $1.00 | both budget keys | `test_paths`, `max_open_prs` | 300000, 1 |
| F5b history p90 $50.00 | both budget keys | `test_paths`, `max_open_prs` | 15000000, 1 |
| F6 `tests/` tree + agreeing gate command | `test_paths` | the other three | `['tests/']` |
| F7 `spec/` tree + agreeing gate command | `test_paths` | the other three | `['spec/']` |
| F8 tree `tests/` vs gate `spec/` (disagreement) | `test_paths` | the other three | `['spec/', 'tests/']` |
| F9 no runner injected | — | all four | — |
| F10 runner raises `OSError` | — | all four | — |
| F11 runner returns unparseable output | — | all four | — |
| F12 runner reports 2 open PRs | `max_open_prs` | the other three | 4 |
| F13a repo beside a $999 decoy sibling | both budget keys | `test_paths`, `max_open_prs` | 600000, 1 |
| F13b identical repo, no sibling | both budget keys | `test_paths`, `max_open_prs` | 600000, 1 |
| F14a absolute `repo_root` | both budget keys | `test_paths`, `max_open_prs` | 900000, 1 |
| F14b relative `repo_root` | both budget keys | `test_paths`, `max_open_prs` | 900000, 1 |
| F14c `the-repo/./../the-repo` | both budget keys | `test_paths`, `max_open_prs` | 900000, 1 |
| F14d relative `repo_root`, no history | — | all four | — |
| F15 **this repository**, no runner | `max_tokens_per_run`, `max_items_per_day`, `test_paths` | `max_open_prs` | 873000, 28, `['tests/']` |
| F16 **this repository** + runner reporting 4 open PRs | all four | — | 873000, 28, `['tests/']`, 6 |

Three withholding behaviours are worth naming, because each is the difference
between an absent proposal and a confident wrong one:

- **F1/F2/F14d withhold for absence of data.** No history, no proposal — and
  F14d withholds through a *relative* path, which is exactly what T01 got wrong
  and T01H fixed.
- **F13a/F13b agree exactly** (600000 vs 600000): the $999 decoy sibling one
  directory over contributes nothing, so `events_stats.collect`'s workspace walk
  stays scoped to the repository actually being asked about.
- **F9/F10/F11 all withhold `max_open_prs`** — no runner, a raising runner, and
  a runner returning garbage are three different failures and all three produce
  *no proposal* rather than a plausible integer.

**Every proposal validates clean.** A policy file was built from this
repository's own proposals (F16, all four keys) and passed through
`validate_agent_policy`: `findings: []`, zero `ERROR: ` findings. The escalation
trigger "`propose_policy_defaults` emits a value `validate_agent_policy` rejects"
did not fire.

### The derivability count — `G1-PLAN`'s input for the provenance question

**3 of 4 on a realistic repository unaided; 4 of 4 with the `gh` runner the
skill's prose tells the operator to inject.** Run against this repository
(this repository's own root, 284 completed work units of real history):

| value | derived? | proposed | evidence class |
|---|---|---|---|
| `budgets.max_tokens_per_run` | yes | 873,000 | measured p90 cost over 214 passing implementation attempts, **converted** through an assumed 200,000 tokens/$ and 1.5x headroom |
| `budgets.max_items_per_day` | yes | 28 | 284 completed WUs total, **converted** through a 10%-of-volume heuristic (no per-day breakdown survives `collect()`) |
| `rules.bugs.test_paths` | yes | `['tests/']` | directly read: tree and `verification.yml` gate commands agree |
| `budgets.max_open_prs` | only with a runner | 3 unaided / count+2 with one | live `gh pr list`; withheld entirely when no runner is injected |

So **one value falls back to a shipped default** (`max_open_prs`, to the
example file's `3`) when the skill is run without a `gh` runner, and **two of
the three derived values are conversions, not measurements** — their evidence
strings disclose the conversion constant precisely because the number would
otherwise read as measured.

What this implies for the open question `PLAN.md` leaves to gate 2 — *how does
review tell an agent-chosen default from a deliberate operator choice?* Three
findings, offered as input, not as the decision:

1. **The "compare against the shipped `DEFAULT_*` constants" option is not
   implementable for three of the four keys.** `agent_policy.py` defines exactly
   three constants — `DEFAULT_MAX_DIFF_LINES`, `DEFAULT_MAX_MERGES_PER_DAY`,
   `DEFAULT_TEST_PATHS`. The three `budgets` keys are *required* fields with no
   constant at all; their only "shipped default" is the literal text of
   `.specfuse/agent-policy.yml.example`. A comparison mechanism built on the
   constants would silently cover one in-scope key.
2. **Where the comparison basis does exist, it is uninformative here.** This
   repository's live file carries `max_tokens_per_run: 2000000`,
   `max_items_per_day: 10`, `max_open_prs: 3` — byte-identical to the example
   file, i.e. every budget value in the repository that motivated this feature
   is the example's value, unedited. `rules.bugs.test_paths` is absent
   altogether, so review cannot distinguish "the operator chose `tests/`" from
   "nobody ever decided" without something the file does not currently record.
3. **The proposals disagree with the live values by enough that the distinction
   matters.** 873,000 vs 2,000,000 (2.3x) and 28 vs 10 (2.8x). If review's job
   is to surface a value worth revisiting, it will surface these two whichever
   mechanism gate 2 picks; the mechanism choice decides whether it can also tell
   the operator *why* the current value is what it is.

### What the loop did NOT verify

The deferral, verbatim from `PLAN.md` § *The oracle problem*:

> *an agent following `derive-agent-policy`'s prose, run against a repository
> whose policy file it has not seen, proposes the values
> `propose_policy_defaults` computes.*

**Re-run condition:** one operator invocation of `/derive-agent-policy` against
**this repository's own `.specfuse/agent-policy.yml`**. That run is also the
review the operator actually wants, so the deferral and the first real use are
one action.

Gate 1 cannot close this and never claimed it would. Every test in the gate
either exercises the algorithm (`tests/test_policy_proposals.py`, 21 tests) or
asserts on the prose (`tests/test_derive_agent_policy_skill.py`,
`tests/test_agent_policy_key_ownership.py`, structural literal matches); **none
composes them by having an agent execute the skill.** The precedent is
`[FEAT-2026-0069/G2-CLOSE]`: FEAT-2026-0039's gates were green and its skill
still emitted 30 components on its first real repo, because a passing fixture
and an agent-executed skill are different oracles. Reading "gate 1 green" as
"the skill works" would be that failure repeated.

A second, smaller thing the loop did not verify: **T01H#8's "unmodified" half.**
The criterion asks that T01's existing tests pass *unmodified*. This close
confirmed all 21 test methods are present and green, and that the 15 T01-era
`TestProposeDefaults` methods are intact by name — but a byte-level diff against
T01's version was out of reach, because a close WU runs no `git` commands. The
pass state recorded for that criterion rests on presence-and-green, not on a
diff.

### Consumer-visible contract changes

Three, all additive; nothing removed and nothing renamed.

1. **`specfuse.loop.policy_proposals`, a new importable module shipped in the
   wheel.** Public surface is one function:
   `propose_policy_defaults(repo_root=None, *, runner=None) -> dict`. Nothing
   previously occupied that import path. It returns a mapping of at most four
   keys — `max_tokens_per_run`, `max_items_per_day`, `test_paths`,
   `max_open_prs` — each value a `{"value", "evidence"}` mapping. **A key the
   repository carries no evidence for is absent from the mapping entirely**;
   the module never fills a gap with a shipped default dressed as a proposal,
   so a caller must handle absence rather than assume four keys. It consumes
   `events_stats.collect`, `gate_commands.iter_code_gates` and `agent_policy`'s
   validator without extending any of them, **does not write `queue:`**, and
   **performs no network call of its own** — `max_open_prs` is proposed only
   through an injected `runner(args, check=...)`, and is withheld when the
   runner is absent, raises, or returns unparseable output. `repo_root` is
   resolved before use, so a relative path, an absolute path, and a
   `./../`-containing path yield identical results (FEAT-2026-0076).
2. **`/derive-agent-policy`, a new skill in the published plugin**
   (`plugins/specfuse/skills/derive-agent-policy/`, `SKILL.md` + `PROMPT.md`),
   vendored into `.specfuse/skills/` and discovery-symlinked from
   `.claude/skills/` — so any project upgrading its scaffold gains a new slash
   command. It drafts the `rules`, `budgets` and `escalation` blocks of
   `.specfuse/agent-policy.yml` from `propose_policy_defaults` plus a batched
   operator interview, in staged per-block accepts, and **writes nothing before
   an explicit accept**. It **does not write `queue:`** (FEAT-2026-0076).
3. **`/groom-backlog` gains an explicit ownership boundary in its published
   text.** The skill's behaviour is unchanged — it still writes `queue:` and
   only `queue:` — but the file now *states* that it owns `queue:` and does not
   write `rules`, `budgets` or `escalation`, so the invariant is readable rather
   than remembered. The invariant across both skills is **one writer per key
   block**, and it is asserted by `tests/test_agent_policy_key_ownership.py`,
   which fails if either skill's text widens into the other's keys
   (FEAT-2026-0076).

These three items are appended to `CHANGELOG.md`'s `Unreleased` section under
`Added`, classified `added`, carrying this feature's ID.

### Cost analysis

Actuals read from `events.jsonl`'s `task_completed` payloads
(`cumulative_cost_usd`, which equals `cost_usd` for every WU here — `re_arm_count`
is 0 across the gate, so no re-arm cycle is hidden in the difference). Planned
figures from each WU's `planned_cost_usd` frontmatter.

| WU | planned | actual | delta | variance | attempts |
|---|---|---|---|---|---|
| T01 `policy_proposals` | $4.50 | $1.959089 | −$2.540911 | **−56.5%** | 1 |
| T01H `relative-repo-root` | $2.00 | $0.770011 | −$1.229989 | **−61.5%** | 1 |
| T02 `derive-agent-policy-skill` | $5.00 | $1.903363 | −$3.096637 | **−61.9%** | 1 |
| T03 `disjoint-key-ownership` | $2.00 | $2.544881 | +$0.544881 | +27.2% | 1 |
| **implementation subtotal** | **$13.50** | **$7.177344** | **−$6.322656** | **−46.8%** | 4 |
| G1-CLOSE-INTERMEDIATE | $4.50 | (this session; the driver stamps it at exit) | — | — | 1 |
| G1-PLAN | $6.00 | not started | — | — | 0 |
| **gate 1 planned total** | **$24.00** | **$7.177344 to date** | — | — | — |

**Against the budget.** `GATE-01.md` carries `cost_budget_usd: 29.00` and
`PLAN.md` carries `planned_cost_usd: 29.00`; both are the whole feature,
gate 1's six WUs ($24.00) plus gate 2's lone close placeholder ($5.00). Gate 1
has spent $7.18 of its $24.00, i.e. 30%, with the two closing WUs still to run.

**The $27.00 figure is stale, and this is the reconciliation that catches it.**
This WU's criterion 5 and `PLAN.md`'s *Notes* both name a $27.00 budget. That
was correct at drafting: 4.50 + 5.00 + 2.00 + 4.50 + 6.00 + 5.00 = $27.00. T01H
was inserted mid-gate at operator review and added $2.00, and `GATE-01.md`'s
`cost_budget_usd` and `PLAN.md`'s frontmatter were both updated to $29.00 while
the prose in `PLAN.md` § *Notes* was not. The live budget is **$29.00**; the
prose sentence naming $27.00 is a stale copy of a number that also lives in
frontmatter. Reported rather than edited — `PLAN.md` prose is not this close's
to rewrite, and `G1-PLAN` raises this figure again when it drafts gate 2's
substantive WUs.

**Three WUs over 50% variance, all underspend, one cause.** T01 (−56.5%), T01H
(−61.5%) and T02 (−61.9%) all came in at roughly 40% of estimate, and the
pattern is more informative than any of the three individually: every one passed
on its **first attempt**, and every estimate was priced with re-attempt headroom
that was never drawn. The drafting estimates were built for a gate whose work
was genuinely new (`propose_policy_defaults` had no existing mechanism to copy),
but the actual work turned out to be composition — `events_stats.collect` and
`gate_commands.iter_code_gates` already existed and were reused rather than
rebuilt, exactly as `PLAN.md`'s existing-mechanism table predicted, and T02 and
T03 had two sibling skills (`derive-verification`, `derive-monitoring`) to copy
the shape from. **The estimate priced the novelty of the goal; the spend
reflected the maturity of the parts.** A feature whose plan-time
existing-mechanism search returns "three mechanisms found and reused" should
expect its implementation WUs to land well under a from-scratch estimate. T03 is
the counter-example that confirms it: at +27.2% it is the only WU that went
over, and it is the only one whose work was neither reuse nor copy — writing a
disjoint-ownership invariant into two skills' prose and building a test that
fails if either widens.

T01H's $0.77 deserves one more sentence, because it is the cheap half of an
expensive lesson: the hygiene WU cost 11% of the gate's implementation spend and
fixed a defect that made every budget proposal silently disappear on a relative
path. Had operator review not caught it between T01 and T02, T02's prose would
have described an under-proposing algorithm and the cost would have been a T02
rewrite rather than a $0.77 insertion.

### Failure-class breakdown

(no non-passing attempts in scope)

Every one of the four implementation attempts recorded `outcome: passed` with
`failure_class: null` and `failure_signature: null` on attempt 1. The gate did
carry two halts — both `driver_staleness_detected` after T01 and T01H touched
`specfuse/loop/policy_proposals.py`, requiring a driver restart — but a
staleness halt is a driver-lifecycle event, not a failed attempt, and neither
consumed an attempt or produced a failure class.

The one real defect in this gate was found by **operator review, not by any
oracle**: T01 passed all twelve of its criteria while silently withholding both
budget proposals for any relative `repo_root`. That is recorded as a lesson
below rather than as a failure class, because no attempt failed — which is
precisely what makes it worth recording.

### Per-criterion state

`GATE-01-CRITERIA.md` carries all 42 criteria, each annotated in this attempt
with the oracle that re-proved it, `kind: narrow`, `state: pass`, and
`attempt: 1`. Every per-criterion oracle is a scoped module run or a symbol
import — a knowable scope, hence `narrow`. The gate-level oracle set (the 16
`code` gates above) is broad by construction and was re-run unconditionally this
attempt, per `close-discipline.md` §5; it is recorded here rather than
carried on any criterion.

`proved_at_sha` is deliberately left unrecorded on every entry: a close WU runs
no `git` command, so this session cannot read HEAD honestly, and a guessed sha
is worse than an absent one.

### Lessons promoted to `.specfuse/LEARNINGS.md`

Two, both from T01H's provenance:

- `[FEAT-2026-0076/G1-CLOSE-INTERMEDIATE/absence-needs-a-two-sided-test]` — when
  "propose nothing" is a designed outcome, absence-because-no-evidence and
  absence-because-the-lookup-failed are indistinguishable to every test that
  only asserts a key is missing.
- `[FEAT-2026-0076/G1-CLOSE-INTERMEDIATE/fixtures-that-share-an-incidental-property]`
  — twelve criteria passed because every fixture used an absolute tempdir; a
  fixture set that shares an unexamined property cannot fail on it.

## Gate 2

Gate 2 asked whether an **existing** policy file can be read, its values placed
next to what the evidence now suggests, and per-block corrections proposed
without clobbering what the operator already decided. What it decided:
`review_agent_policy` classifies all four in-scope keys against the shipped
baseline, carries the lossy direction's caveat inside the returned data, and
returns a per-key readout that is structurally incapable of re-emitting the
file; the skill's prose describes that algorithm and is fenced against
widening. What it did **not** decide is the same thing gate 1 could not decide,
recorded verbatim under *What the loop did NOT verify* — and the verdict is
hedged accordingly rather than reading a green gate as proof of the skill.

Three implementation WUs, one of them on a second attempt. Full `code` gate set
re-run fresh in this close session: 16 of 16 green.

### Oracles re-run fresh (`close-discipline.md` §1)

Every command below was executed in this close session, exit code read directly
from the process; none is inherited from a producing WU's self-report. The gate
list is the full `code` set from `.specfuse/verification.yml`, derived at run
time via `python3 -m specfuse.loop.gate_commands .specfuse/verification.yml`
(not transcribed), run from the repository root.

**The set was run twice, and both runs are 16/16 green**: once on the tree as
this close inherited it, and again after this close's own edits (this
retrospective, `GATE-02-CRITERIA.md`, `.specfuse/LEARNINGS.md`, `CHANGELOG.md`)
had landed — because a close that edits a changelog a test parses and a
learnings file a linter reads has changed the tree it just certified. The
figures quoted below are the second, post-edit run's. Prose in this file was
still being corrected after that second run; nothing in the `code` set reads
`RETROSPECTIVE.md`, and the surface that does —
`specfuse lint --closing` — was re-run last of all, after the final edit, exit
0 (`CLOSING-READY`).

| # | gate | command | exit |
|---|---|---|---|
| 1 | tests | `python3 -m unittest discover -s tests -v -b` | 0 |
| 2 | lint | `ruff check specfuse .specfuse/scripts tests scripts` | 0 |
| 3 | security | `bandit -r specfuse .specfuse/scripts -ll` | 0 |
| 4 | coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | 0 |
| 5 | leak-scan | `python3 .specfuse/scripts/leak_scan.py --all` | 0 |
| 6 | agent-policy-example-lint | `python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && … .specfuse/agent-policy.yml` | 0 |
| 7 | event-type-gate | `python3 .specfuse/scripts/event_type_gate.py` | 0 |
| 8 | roadmap-link-gate | `python3 .specfuse/scripts/roadmap_link_gate.py` | 0 |
| 9 | arm-sweep-gate | `python3 .specfuse/scripts/arm_sweep_gate.py` | 0 |
| 10 | monitoring-example-lint | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | 0 |
| 11 | leak-scan-hook | `bats tests/leak_scan_hook.bats` | 0 |
| 12 | sync-scaffold-bats | `bats tests/sync_scaffold.bats` | 0 |
| 13 | sync-scaffold-symlinks-bats | `bats tests/sync_scaffold_symlinks.bats` | 0 |
| 14 | init-sh-shim-bats | `bats tests/init_sh_shim.bats` | 0 |
| 15 | init-skills-bats | `bats tests/init_skills_idempotent.bats` | 0 |
| 16 | hookspath-conflict-bats | `bats tests/hookspath_conflict.bats` | 0 |

`tests`: `Ran 2861 tests in 120.493s / OK (skipped=3)`. Gate 1's close recorded
2837; the difference is **exactly 24**, and gate 2's three WUs contributed
exactly 24 test methods (12 in `tests/test_policy_review.py`, 8 in
`tests/test_derive_agent_policy_review_mode.py`, 4 in
`TestReviewModePreservation`). `coverage`: same 2861 tests,
`TOTAL 9145 stmts / 607 miss / 93%`, over the gate's `--fail-under=90`.
`lint`: `All checks passed!`. `security`: bandit's run summary reports 96
low-severity issues across the scanned tree and **0 medium, 0 high** — the
`-ll` threshold gates on medium-and-up, so nothing is reported and no `>> Issue`
block appears in the output. The eight `# nosec` suppressions in the scanned
tree (two `B602` and one `B604` in `specfuse/loop/loop.py`, one `B310` in
`specfuse/loop/notify.py`, four `B603` in `.specfuse/scripts/leak_scan.py`) are
all pre-existing; gate 2 added none. `leak-scan`: `gitleaks 8.30.1 /
leak-scan: clean`.

Six narrow oracles were additionally re-run for the per-criterion record in
`GATE-02-CRITERIA.md`, all exit 0:

| oracle | result |
|---|---|
| `python3 -m unittest tests.test_policy_review -v` (T04 c12) | `Ran 12 tests / OK` |
| `python3 -m unittest tests.test_policy_proposals -v` (T04 c12, "unmodified") | `Ran 21 tests / OK` |
| `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v` (T05 c9) | `Ran 29 tests / OK` |
| `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v` (T06 c8) | `Ran 32 tests / OK` |
| `python3 -m unittest tests.test_correlation_id_override -v` (T05's attempt-1 failure signature) | `Ran 11 tests / OK` |
| `python3 -c "from specfuse.loop.policy_review import review_agent_policy"` | symbol resolves |

Two structural checks for T05 c10 / T06 c7 (vendoring), run with `cmp`, not
inferred from the sync script's own output: `SKILL.md` and `PROMPT.md` are each
**byte-identical** between `plugins/specfuse/skills/derive-agent-policy/` and
`.specfuse/skills/derive-agent-policy/`, and `.claude/skills/derive-agent-policy`
is a live symlink to the vendored directory.

**Environment note.** As in gate 1, the gate set was run outside the session
sandbox; under the sandbox roughly a dozen tests that shell out to `git` over
the network go falsely red. The exit codes above are the honest ones and come
from the same environment (`oracle_env: macos_local`) the producing WUs ran in.

### `review_agent_policy` re-run fresh against a fixture per provenance class

Gate 1's close called `propose_policy_defaults` directly rather than asserting
it through the suite, and that is what made T01's silent withholding visible.
The same pattern is applied here to the thing gate 2 actually shipped: fixtures
were built in this session, `review_agent_policy` was **called directly**, and
its return value printed and read — not inferred from a green test. Every
fixture policy file carried a **populated `queue:`** (two FEAT-IDs) so the
disjoint-key claim is observed under the condition that would break it.

| fixture | `budgets.*` (3 keys) | `rules.bugs.test_paths` | caveat present? |
|---|---|---|---|
| C1 budgets byte-equal to the example, `test_paths` absent | `matches_baseline` ×3 | `absent_from_file` | on the 3 matching, not on the absent |
| C2 budgets tuned (873000 / 28 / 6), `test_paths: [tests/]` | `differs_from_baseline` ×3 | `matches_baseline` | on the matching one only |
| C3 as C1, `test_paths` absent from the file | `matches_baseline` ×3 | `absent_from_file` | as C1 |
| C4 no `agent-policy.yml.example` at all | `baseline_unavailable` ×3 | `matches_baseline` | on `test_paths` only |
| C4b example present but unparseable | `baseline_unavailable` ×3 | `matches_baseline` | on `test_paths` only |
| C5 key absent from the file **and** baseline unavailable | `baseline_unavailable` | — | none |
| R1 **this repository**, no runner | all three `matches_baseline` | `absent_from_file` | on the 3 matching |
| R2 **this repository** + runner reporting 4 open PRs | all three `matches_baseline` | `absent_from_file` | as R1 |

Five things the direct call showed that a green suite would not have:

- **`queue` appears nowhere in the returned structure** in any of the eight
  runs — checked as a substring over the JSON-serialised return value, with a
  populated `queue:` in the fixture. The returned mapping's top-level keys are
  exactly the four dotted in-scope keys, every run.
- **The caveat rides only on `matches_baseline`.** Present on every
  `matches_baseline` entry, absent on `differs_from_baseline`,
  `absent_from_file` and `baseline_unavailable`. A reader cannot pick up the
  hint without the disclaimer attached, which is the honesty condition
  `GATE-02-REVIEW.md` made the whole recommendation rest on.
- **C4/C4b degrade partially, not wholly.** With no example file — or an
  unparseable one — the three `budgets` keys go `baseline_unavailable` while
  `rules.bugs.test_paths` still classifies, because its baseline is
  `agent_policy.DEFAULT_TEST_PATHS` and needs no file. That is the
  union-of-two-sources decision paying off in the one case where it can be
  observed doing so.
- **C5 is the one place the four-state label is not a total partition, and it
  is worth naming plainly.** When a key is *both* absent from the file *and*
  has an unreadable baseline, `_classify` returns `baseline_unavailable` — the
  baseline check runs first — so the classification label alone does not
  distinguish that case from "present in the file, baseline unreadable". The
  entry as a whole still does: `current: {'present': False, 'value': None}`
  versus `current: {'present': True, …}`. T04's criterion 7 asks that the three
  absences produce *different observable results*, and they do; but the
  observable that separates them is the entry, not the classification string,
  and anything downstream that renders only the classification will collapse
  them. Recorded as a real limitation of the shipped shape rather than smoothed
  over.
- **R1's `max_items_per_day` proposal is 29, where gate 1 measured 28.** Same
  code, same repository, one gate of work later — the proposal moves with the
  history it is derived from, which is the intended behaviour and a useful
  reminder that a `converted` number is a snapshot, not a constant.

### Whether the chosen provenance mechanism held up (criterion 3)

**It held up, and the recommendation is to keep it. Three findings, then the
recommendation.**

**1. The shipped-baseline comparison covered all four in-scope keys in
practice — 4 of 4, not 1 of 4.** This was the whole reason `G1-PLAN` widened
shape 1 from "the `DEFAULT_*` constants" to "the shipped baseline", and the
direct runs confirm the widening was load-bearing rather than defensive:
`rules.bugs.test_paths` resolves through `agent_policy.DEFAULT_TEST_PATHS`, the
three `budgets` keys through `.specfuse/agent-policy.yml.example`, and every
entry records **which source answered**. Had the mechanism been built on the
constants alone, three of four keys — the three with the interesting deltas —
would have had no baseline at all.

**2. The lossy direction stayed disclosed at the output, not only in prose.**
The caveat is a field on the returned entry (`caveat`), not a sentence in
`SKILL.md` that a caller might not read, and it is attached to exactly the
class that needs it. The prose says the same thing in the same terms
(*"a hint, not a claim"*, and the asymmetry stated explicitly), so the
disclosure survives both consumption paths — a program reading the return value
and an agent reading the skill.

**3. Nothing in implementation argued for the provenance-recording shape.**
T04 shipped in one attempt at 29% of its estimate and needed no schema field to
answer criteria 3–8; no escalation trigger fired; `PLAN.md`'s scope boundary
was not approached, let alone crossed (see the next paragraph). The one thing
implementation *did* surface against the mechanism is the C5 precedence
collapse above, and that is a defect of the classification's *rendering*, not
of its *basis* — recording provenance in the file would not have fixed it.

**Recommendation: keep the shipped-baseline comparison; file the
provenance-recording shape as a successor feature, unchanged from
`GATE-02-REVIEW.md`'s recommendation, and with its doubt intact.** Gate 2 does
not resolve the strongest argument against it, which that review artifact
stated against itself: this repository's own file has no operator intent in it
to protect — R1 shows all three budget values still byte-identical to the
example and `test_paths` still absent — so the mechanism has not yet met the
hard case, a repository where someone *has* tuned their budgets. Gate 2's
fixtures construct that case (C2, all three `differs_from_baseline`) and the
mechanism handles it correctly, which is more than gate 1 could say; but a
fixture is not a tuned repository, and the reliable direction being the one
that matters there is a design claim this feature has still not tested on real
data.

**Scope boundary: not crossed.** The union of `files_touched` across all four
gate-2 attempts (T04, T05 ×2, T06 — the driver's own per-attempt observation of
the tree, recorded in `events.jsonl`, not an agent's self-report) is nine paths:
the three WU files, `events.jsonl`, `specfuse/loop/policy_review.py`, both
`SKILL.md`/`PROMPT.md` pairs, and three test files. **`specfuse/loop/agent_policy.py`
is not among them** — no key, no field, no validation rule added; `policy_review.py`
imports `agent_policy` and reads `DEFAULT_TEST_PATHS` and nothing else from it.
Neither is `.specfuse/agent-policy.yml` nor `.specfuse/agent-policy.yml.example`,
and the direct R1 run confirms the live file's three budget values are still
2000000 / 10 / 3 with `rules.bugs.test_paths` still absent, exactly as gate 1
measured them. The `agent-policy-example-lint` gate (which validates both files)
is green. `PLAN.md`'s scope boundary stands unwidened, and the criterion-3
failure this close exists to catch — a silently widened scope — did not occur.

### Whether the disjoint-key boundary survived (criterion 4)

**It survived, on both sides, and the fence gate 2 added is stronger than the
one gate 1 shipped.**

- **The code side (T04 criterion 9/10), observed directly.** `queue` appears
  nowhere in `review_agent_policy`'s return value across all eight runs above,
  with a populated `queue:` in every fixture. The function returns a per-key
  readout keyed by the four dotted in-scope keys and never a rendering of the
  input document, so clobbering is structurally impossible here rather than
  merely discouraged — the property T04's criterion 10 was written to make
  true.
- **The prose side (T06), re-run in this session.** `python3 -m unittest
  tests.test_agent_policy_key_ownership …` exits 0, `Ran 32 tests / OK`. The
  suite now carries `TestReviewModePreservation`'s four methods on top of
  T03's six. Two of them are the real fence:
  `test_review_mode_must_never_write_set_covers_every_unowned_key_block`
  derives the required disclaim set from the file's own stated ownership rather
  than a hardcoded list, so a new top-level key added later with no review-mode
  statement fails; and `test_review_mode_names_non_clobbering_consequence`
  refuses a vague "preserves intent" sentence by requiring the concrete
  consequence — a `budgets` correction returning two of three keys is a
  deletion.
- **The temptation the close named in advance did not materialise.** The close
  WU predicted that *a review skill is exactly the shape that would be tempted
  to write `queue:`*. It was not: review mode's prose names `queue`, `version`
  and `rules.triage` as must-never-write and names `/groom-backlog` as
  `queue`'s owner, and `/groom-backlog`'s own text (T03's, untouched by gate 2)
  still states the other half. The invariant is one writer per key block, and
  both halves are asserted.

### Failure-class breakdown

One non-passing attempt in scope across gate 2, and it is worth more than its
line in the table.

| WU | attempt | outcome | `failure_class` | `failure_signature` |
|---|---|---|---|---|
| T05 | 1 | failed | `tests` | `test_closing_sequence_ids_are_rejected_by_the_vendored_pattern_alone` |
| T05 | 2 | passed | — | — |
| T04, T06 | 1 | passed | — | — |

**The recorded signature names a test that has nothing to do with T05's
deliverable**, and the honest reading of that attempt is not the signature but
the `files_touched` list beside it. Attempt 1 touched exactly one path —
`tests/test_derive_agent_policy_review_mode.py` — and none of the three files
it was dispatched to write (`SKILL.md`, `PROMPT.md`, and their vendored
copies). It wrote its red test and stopped; with the prose it asserts on
unwritten, its own oracle was necessarily red regardless of anything else in
the suite. Attempt 2 touched all seven expected paths and passed.

**The signature's own test is green now and was re-run in this session**
(`python3 -m unittest tests.test_correlation_id_override -v`, `Ran 11 tests /
OK`), as is the full suite. `test_closing_sequence_ids_are_rejected_by_the_
vendored_pattern_alone` reads `specfuse/loop/data/schemas/event.schema.json`
straight off disk and asserts its `correlation_id` pattern does *not* match a
closing-sequence ID; that pattern is byte-equal to `.specfuse/schemas/
event.schema.json`'s today and is the narrow one the test expects, and no test
in the suite writes to either path (the two bats suites that write an
`event.schema.json` write into `$TESTDIR`). **Why it went red during that
attempt is not established**, and this close does not guess: no root cause was
reproduced, so none is recorded. What is recorded is that the attempt would
have failed on its own criteria anyway, that the failure did not recur, and
that the driver's own `failure_excerpt` carried the `NO VERDICT FOUND … may be
unrelated to the failure` note alongside the signature it stored.

**No re-arms.** `re_arm_count` is 0 for every WU in both gates, so no re-arm
cycle is hidden in any cumulative figure. Gate 2 also carried one
`driver_staleness_detected` halt after T04 touched `specfuse/loop/`, matching
gate 1's two — a driver-lifecycle event, not a failed attempt; it consumed no
attempt and produced no failure class.

### Per-criterion state

`GATE-02-CRITERIA.md` carries all 30 criteria — T04's 12, T05's 10, T06's 8 —
each annotated in this attempt with the oracle that re-proved it, `kind:
narrow`, `state: pass`, and `attempt: 1`. Every per-criterion oracle is a
scoped module run, a symbol import, a `cmp` byte-comparison, or a direct call
whose return value was read — all knowable scopes, hence `narrow`. The
gate-level oracle set (the 16 `code` gates above) is broad by construction and
was re-run unconditionally this attempt per `close-discipline.md` §5; it is
recorded here rather than carried on any criterion. The dispatch worklist
carried 0 criteria forward and required all 30 to be re-verified this attempt,
which is what happened.

`proved_at_sha` is deliberately left unrecorded on every entry, for the same
reason gate 1 gave: a close WU runs no `git` command, so this session cannot
read HEAD honestly, and a guessed sha is worse than an absent one.

**One qualification on three of those `pass` states**, stated rather than
buried: T04#1, T05#1 and T06#1 are red-test-first criteria — they assert a
named test *failed on HEAD before the WU ran*. This close re-verified that each
named test now exists and passes; it cannot re-observe the redness, because the
tree that was red no longer exists and a close WU runs no `git`. Those three
`pass` states therefore rest on the present half of the criterion plus the
producing WU's report of the absent half, and are the same posture gate 1's
criteria artifact took.

### What the loop did NOT verify

The deferral, verbatim from `PLAN.md` § *The oracle problem*, carried forward
from gate 1 unchanged and **not** closed by gate 2:

> *an agent following `derive-agent-policy`'s prose, run against a repository
> whose policy file it has not seen, proposes the values
> `propose_policy_defaults` computes.*

**Re-run condition:** one operator invocation of `/derive-agent-policy` against
**this repository's own `.specfuse/agent-policy.yml`**. That run is also the
review the operator actually wants — and, now that review mode exists, it is
also review mode's first real use, so the deferral and the first real use
remain one action.

Gate 2 did not test this and never claimed it would. Every test it added either
exercises the algorithm (`tests/test_policy_review.py`, 12 tests) or asserts on
the prose (`tests/test_derive_agent_policy_review_mode.py`,
`tests/test_agent_policy_key_ownership.py`, structural literal matches);
**none composes them by having an agent execute the skill.** Gate 2 added a
second reference implementation and more prose — it did not add an
agent-executing-prose oracle, and a green gate here must not be read as one.
This is the binding precedent `[FEAT-2026-0069/G2-CLOSE]` records: FEAT-2026-0039's
gates were green and its skill still emitted 30 components on its first real
repo. **The verdict below is hedged for exactly this reason.**

A second, smaller thing the loop did not verify, inherited in shape from gate
1's T01H#8: **the byte-level half of the "passes unmodified" criteria**. It is
narrower than gate 1's version, because `files_touched` closes most of it:

- **T05#9 (`tests/test_derive_agent_policy_skill.py`) and T04#12
  (`tests/test_policy_proposals.py`) are effectively closed.** Neither path
  appears in any gate-2 attempt's `files_touched`; the only attempts that
  touched them are T02's and T01/T01H's, in gate 1. Both suites were re-run
  green in this session. That is not a byte diff, but it is the driver's own
  observation of the tree at each attempt's end, and it says the files were not
  written to.
- **T06#6 (`tests/test_agent_policy_key_ownership.py`) genuinely remains
  half-verified.** T06 *did* edit that file — additively, by its own account —
  so `files_touched` cannot distinguish an appended class from a rewritten
  suite. What this close can say is that
  `test_t03_methods_present_and_pass_unmodified` asserts the T03-era method-name
  set is *exactly* the six original names and fails on any addition or removal,
  and that all thirty-two methods pass. Method **bodies** are not compared,
  because a close WU runs no `git` command.

The pass states recorded for these criteria therefore rest on presence,
name-set equality, absence from `files_touched`, and green — not on a byte
diff.

No predecessor auto-close debt markers exist in this feature
(`grep -rn "autoclose-debt"` over the feature directory returns nothing), so
there is none to reconcile here.

### Lessons promoted to `.specfuse/LEARNINGS.md`

Three, all from gate 2's own evidence:

- `[FEAT-2026-0076/G2-CLOSE/a-precedence-computed-summary-field-collapses-combinations]`
  — a single classification field computed by precedence cannot distinguish
  combinations of the conditions it ranks; assert on the whole entry.
- `[FEAT-2026-0076/G2-CLOSE/read-files-touched-before-trusting-failure-signature]`
  — a failed attempt's `failure_signature` says which oracle went red, not
  whether the WU did its work; `files_touched` against `produces:` says that.
- `[FEAT-2026-0076/G2-CLOSE/the-maturity-discount-applies-to-implementation-only]`
  — two gates of data: implementation WUs land near half their estimate when
  the existing-mechanism search returns reuse, while closing WUs do not.

## Consumer-visible contract changes

Gate 2 adds two, both additive; nothing removed and nothing renamed. (Gate 1's
three are enumerated under *Gate 1* above and are already in `CHANGELOG.md`'s
`Unreleased`; these two are appended there alongside them.)

1. **`specfuse.loop.policy_review`, a new importable module shipped in the
   wheel.** Public surface is one function:
   `review_agent_policy(repo_root=None, *, runner=None) -> dict`. Nothing
   previously occupied that import path. It returns a mapping keyed by exactly
   four dotted key names — `budgets.max_tokens_per_run`,
   `budgets.max_items_per_day`, `budgets.max_open_prs`, `rules.bugs.test_paths`
   — each entry carrying `current` (`{"present", "value"}`), `proposal`
   (`{"available"}`, plus `value` / `evidence` / `kind` when available, where
   `kind` is `measured` or `converted`), `baseline` (`{"available", "source"}`
   plus `value`, the `source` being either `agent_policy.DEFAULT_TEST_PATHS` or
   `agent-policy.yml.example`), `classification` (one of `matches_baseline`,
   `differs_from_baseline`, `absent_from_file`, `baseline_unavailable`), and
   `caveat` (a string on `matches_baseline`, `None` otherwise). **It returns a
   per-key readout and never a rendering of the input file**, so a caller
   cannot use it to rewrite `.specfuse/agent-policy.yml`. It **never reads,
   returns or reports `queue`**, does not extend `agent_policy`'s schema, and
   **performs no network call of its own** — `max_open_prs` evidence reaches it
   only through the injected `runner`, and a runner that raises still yields a
   full readout. Note the precedence in `classification`: when a key is both
   absent from the file and has an unreadable baseline, the value is
   `baseline_unavailable`; a consumer that needs the two apart must read
   `current["present"]` rather than the classification alone.
2. **`/derive-agent-policy` gains a review mode in the published skill**
   (`plugins/specfuse/skills/derive-agent-policy/`, `SKILL.md` + `PROMPT.md`,
   vendored into `.specfuse/skills/` and discovery-symlinked from
   `.claude/skills/`), so any project upgrading its scaffold gets the new
   behaviour on an existing slash command. The skill is now one skill with
   **two entry conditions**: an absent `.specfuse/agent-policy.yml` selects the
   bootstrap interview gate 1 shipped, an existing one selects review mode.
   Review mode calls `review_agent_policy`, presents current / proposal /
   baseline / classification per key, states the classification's asymmetry
   (differing from the baseline reliably means someone chose it; matching it
   does not reliably mean nobody did), distinguishes `measured` from
   `converted` proposals and names the assumption behind a converted one at the
   point the operator reads the number, and keeps the same **staged per-block
   accept** contract — `rules`, then `budgets`, then `escalation`, never one
   blanket yes. It **must never write `queue`, `version` or `rules.triage`**,
   and a correction it proposes for a block it does own **preserves every key
   the existing file already carries in that block** — a `budgets` correction
   returning two of three keys is a deletion, not a fix. `escalation` is
   outside `review_agent_policy`'s scope and falls back to the bootstrap ask
   (FEAT-2026-0076).

Both items are appended to `CHANGELOG.md`'s `Unreleased` section under `Added`,
classified `added`, carrying this feature's ID.

## Cost analysis

Actuals read from `events.jsonl`'s `task_completed` payloads
(`cumulative_cost_usd`). `re_arm_count` is 0 for every WU across both gates, so
no re-arm cycle is hidden in any figure; T05's cumulative is the sum of its two
attempts ($1.802767 + $1.174835). Planned figures from each WU's
`planned_cost_usd` frontmatter. This close's own spend is stamped by the driver
at exit and is therefore not in the table.

| WU | planned | actual | delta | variance | attempts |
|---|---|---|---|---|---|
| T01 `policy_proposals` | $4.50 | $1.959089 | −$2.540911 | **−56.5%** | 1 |
| T01H `relative-repo-root` | $2.00 | $0.770011 | −$1.229989 | **−61.5%** | 1 |
| T02 `derive-agent-policy-skill` | $5.00 | $1.903363 | −$3.096637 | **−61.9%** | 1 |
| T03 `disjoint-key-ownership` | $2.00 | $2.544881 | +$0.544881 | +27.2% | 1 |
| **gate 1 implementation subtotal** | **$13.50** | **$7.177344** | **−$6.322656** | **−46.8%** | 4 |
| G1-CLOSE-INTERMEDIATE | $4.50 | $7.302612 | +$2.802612 | **+62.3%** | 1 |
| G1-PLAN | $6.00 | $4.408823 | −$1.591177 | −26.5% | 1 |
| **gate 1 closing subtotal** | **$10.50** | **$11.711435** | **+$1.211435** | **+11.5%** | 2 |
| **gate 1 total** | **$24.00** | **$18.888779** | **−$5.111221** | **−21.3%** | 6 |
| T04 `policy_review` | $3.50 | $1.001152 | −$2.498848 | **−71.4%** | 1 |
| T05 `review-mode-prose` | $3.50 | $2.977602 | −$0.522398 | −14.9% | 2 |
| T06 `non-clobber-invariant` | $2.50 | $0.704898 | −$1.795102 | **−71.8%** | 1 |
| **gate 2 implementation subtotal** | **$9.50** | **$4.683652** | **−$4.816348** | **−50.7%** | 4 |
| G2-CLOSE (this session) | $5.00 | stamped by the driver at exit | — | — | 1 |
| **feature total** | **$38.50** | **$23.572431 to date** | — | **61.2% of plan** | — |

**Against the declared budgets.** `PLAN.md` carries `planned_cost_usd: 38.50`
and `GATE-02.md` carries `cost_budget_usd: 19.50`. Gate 2's three
implementation WUs spent **$4.68 of that $19.50 — 24%** — leaving $14.82 for
this close against its $5.00 estimate. The feature stands at **$23.57 of
$38.50, 61%**, with only this close unstamped — so the final total is not yet
knowable here, though it would take this close overrunning its $5.00 estimate
by roughly 3x for the feature to reach its plan. `PLAN.md`'s § *Notes* records
a drafting-time forecast of ~$37 for the whole feature and the drafted sum
landed at $38.50: **the forecast was accurate about the plan, and the plan was
pessimistic about the work** — two different kinds of estimate, and only the
second is off.

**Gate 1's pattern repeated, and two gates make it a trend — but a narrower
one than gate 1's close could see.** Gate 1's close reported implementation
spend at ~40% of estimate and named the cause: *the estimate priced the novelty
of the goal; the spend reflected the maturity of the parts.* Gate 2's
implementation came in at **49% of estimate (−50.7%)**, against gate 1's 53%
(−46.8%); across both gates the seven implementation WUs spent **$11.86 of
$23.00, 52%**. That is a trend, and `G1-PLAN` had already priced against it —
it deliberately set T04 below T01 ($3.50 vs $4.50) and T05 below T02 ($3.50 vs
$5.00) on exactly this reasoning, and gate 2 still came in half under the
reduced numbers. The discount is real and it is larger than one round of
correction absorbs.

**But it is a discount on implementation only, and gate 1's close could not
see that.** `G1-CLOSE-INTERMEDIATE` overran by **+62.3%** ($7.30 against
$4.50) — the feature's largest positive variance in both dollars and percent,
and its only material overrun — and it was reporting on itself from the inside
before the driver stamped it, so its own overrun is absent from its analysis. `G1-PLAN` came in at −26.5%. Closing
subtotal: **+11.5%**. So the honest statement of the pattern is not "this
feature runs under estimate" but: **composition work runs about half its
estimate; closing work does not, and the one closing WU that ran a full fresh
oracle sweep ran well over.** A planner applying the maturity discount to a
close WU on the strength of gate 1's sentence would underfund it. T03 (+27.2%)
is the same lesson inside the implementation set — the only gate-1 unit that
went over, and the only one whose work was neither reuse nor copy.

**T05's two attempts cost less than its single estimate.** $2.98 against
$3.50 — a failed attempt plus a successful one, still 15% under. The failed
attempt was $1.80 of that, and what it bought was a written test file that
attempt 2 kept. This is the cheap end of the re-attempt distribution and should
not be read as evidence that re-attempts are cheap: `planning-discipline.md`
§5's corollary (budget one re-attempt of the largest WU) is what made gate 2's
$19.50 comfortable, and it cost nothing to carry.

**One non-passing attempt across the feature**, T05's first — see § *Gate 2 →
Failure-class breakdown* above for why its recorded `failure_signature` is not
a diagnosis. Gate 1 had none.

## Hedged-verdict follow-up record

Verdict: **`met_locally`**. Every acceptance criterion that this loop can
decide was decided: gate 2's 30 were re-verified fresh in this session and are
recorded in `GATE-02-CRITERIA.md`; gate 1's 42 were verified and recorded by
`G1-CLOSE-INTERMEDIATE` in `GATE-01-CRITERIA.md` and are **not** re-verified
per-criterion here — what this close re-ran feature-wide is the full 16-gate
`code` set, fresh and unconditionally, which is the broad oracle covering both
gates' work. Two criteria-level claims could not be verified in-loop, and
neither is a failure of the work; both are recorded below with the exact
condition that would raise the verdict to `met`.

### The agent-executes-prose oracle (`PLAN.md` § *The oracle problem*)

- **criterion, verbatim:** *an agent following `derive-agent-policy`'s prose,
  run against a repository whose policy file it has not seen, proposes the
  values `propose_policy_defaults` computes.*
- **why it is unverifiable in this environment:** the loop's oracles are
  `unittest` runs and structural asserts over prose. Every test this feature
  ships either exercises the algorithm or asserts on the text; none composes
  them by having an agent execute the skill against an unseen tree, and a
  work-unit session cannot dispatch an agent to do so. A passing fixture and an
  agent-executed skill are different oracles — `[FEAT-2026-0069/G2-CLOSE]`.
- **re-run condition that would upgrade this to `met`:** one operator
  invocation of `/derive-agent-policy` against **this repository's own
  `.specfuse/agent-policy.yml`**, comparing what the agent proposes against
  `review_agent_policy`'s readout for the same four keys (recorded in § *`review_agent_policy`
  re-run fresh…* above as R1/R2, so the comparison target already exists). That
  run is also the first real use of review mode and the review the operator
  wants, so the deferral and the first real use are one action.
- **kind:** `externally-verifiable-later`

### The byte-level half of T06#6's "passes unmodified"

- **criterion, verbatim (T06#6):** *`tests/test_agent_policy_key_ownership.py`'s
  existing T03-era test methods are present and pass **unmodified**; this WU
  adds a class, it does not rewrite the suite.*
- **why it is unverifiable in this environment:** "unmodified" is a claim about
  a diff, and a close WU runs no `git` command (`result-contract.md` rule 1,
  `never-touch.md` §3). T06 legitimately edited this file, so — unlike T05#9
  and T04#12, whose paths appear in no gate-2 attempt's `files_touched` at all —
  the driver's per-attempt record cannot separate an appended class from a
  rewritten suite. This close verified everything short of the diff: all 32
  methods green in a scoped fresh run, and the T03-era method-name set asserted
  *exactly* equal to its original six names by
  `test_t03_methods_present_and_pass_unmodified`, which fails on any addition or
  removal. Method **bodies** are not compared.
- **re-run condition that would upgrade this to `met`:** a reviewer outside a
  close session runs `git diff <T03's commit> HEAD --
  tests/test_agent_policy_key_ownership.py` and observes the change is purely
  additive — one new class appended, no line inside `TestKeyOwnership` altered.
  That is one command and it belongs in the PR review, where the diff is already
  on screen.
- **kind:** `externally-verifiable-later`

**Verdict ceiling.** Both entries are `externally-verifiable-later`, so rework
exists: `met` is reachable, and the operator has a real choice between
accepting the hedge now and running the two named conditions first. Neither is
`inherent` and neither is `routed-finding` — nothing here is unknowable or
owned elsewhere.
