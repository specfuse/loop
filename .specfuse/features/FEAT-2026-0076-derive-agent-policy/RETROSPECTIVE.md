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
