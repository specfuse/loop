## Gate 1 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 2.

- feature_id: FEAT-2026-0049
- predicate_version: v1
- gate_total_cost: $5.95
- gate_budget: $36.00
- reasons: [] (auto=True)

## What the loop did NOT verify (gate 1)

This gate auto-closed on-plan; the full close-intermediate ceremony did
not run, so the per-criterion deferred-verification list was **not**
enumerated. Any acceptance criterion whose verification is deferred
(loop-sandbox limit, cross-repo coordination, real-system access) is
unrecorded here. Gate 2's close MUST reconcile these
before the feature's terminal verdict — auto-close cannot enumerate them.

<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03,T04 criteria=27 predicate=v1 -->

- **FEAT-2026-0049/T01** (`WU-01-agent-lock.md`)
  - deferred: `tests/test_agent_lock.py::TestAgentLock::test_second_acquire_raises` exists
  - deferred: `specfuse/loop/_filelock.py` gains a filename parameter on `acquire_tree_lock`
  - deferred: The same test passes after this WU's edits.
  - deferred: A second `acquire_agent_lock` against the same directory raises
  - deferred: The agent lock and the driver lock are independent: holding
  - deferred: `.specfuse/.agent.lock` is gitignored, alongside the existing `.loop.lock`
- **FEAT-2026-0049/T02** (`WU-02-state-snapshot.md`)
  - deferred: `tests/test_agent_state.py::TestSnapshot::test_queue_read_from_policy` exists
  - deferred: `specfuse/agent/state.py` exposes one public function returning an immutable
  - deferred: The same test passes after this WU's edits.
  - deferred: A repository with no `.specfuse/agent-policy.yml` yields a snapshot with an
  - deferred: A `runner` that fails or returns unparseable output yields a snapshot with
  - deferred: The snapshot performs **no writes**: no issue comment, no label, no file. A
- **FEAT-2026-0049/T03** (`WU-03-budget-and-pause.md`)
  - deferred: `tests/test_agent_budget.py::TestRunBudget::test_cap_is_not_checked_mid_item`
  - deferred: `specfuse/agent/budget.py` exposes a `RunBudget` carrying the three caps and a
  - deferred: The same test passes after this WU's edits.
  - deferred: Each of the three caps independently stops the run: three tests, one per cap,
  - deferred: Absent caps mean unbounded: a `RunBudget` with none set never stops the run.
  - deferred: The PAUSE marker stops the loop at the next boundary and the run summary names
  - deferred: Every stop path yields a distinct, machine-readable stop reason. A run that
- **FEAT-2026-0049/T04** (`WU-04-conductor-loop.md`)
  - deferred: `tests/test_agent_run.py::TestDrainEmpty::test_drains_cleanly_with_no_providers`
  - deferred: `specfuse/agent/run.py` exposes the loop entry point and the action-provider
  - deferred: The same test passes after this WU's edits.
  - deferred: `pyproject.toml` gains `specfuse-agent = "specfuse.agent.run:main"` under
  - deferred: A second concurrently-running agent refuses to start, naming the lock holder's
  - deferred: The run summary names: items attempted, items completed, the stop reason from
  - deferred: With one or more test-double providers registered, the loop selects, executes
  - deferred: The loop performs no git mutation of its own. It invokes; it does not commit,

## Gate 2 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 3.

- feature_id: FEAT-2026-0049
- predicate_version: v1
- gate_total_cost: $6.66
- gate_budget: $45.50
- reasons: [] (auto=True)

## What the loop did NOT verify (gate 2)

This gate auto-closed on-plan; the full close-intermediate ceremony did
not run, so the per-criterion deferred-verification list was **not**
enumerated. Any acceptance criterion whose verification is deferred
(loop-sandbox limit, cross-repo coordination, real-system access) is
unrecorded here. Gate 3's close MUST reconcile these
before the feature's terminal verdict — auto-close cannot enumerate them.

<!-- specfuse:autoclose-debt gate=2 wus=T05,T06,T07,T08 criteria=30 predicate=v1 -->

- **FEAT-2026-0049/T05** (`WU-05-provider-seam.md`)
  - deferred: `tests/test_agent_seam.py::TestKindVocabulary::test_triage_item_is_selected_not_escalated`
  - deferred: `specfuse/agent/run.py` exposes `KIND_TRIAGE` and `KIND_ESCALATION_ANSWER`,
  - deferred: The same test passes after this WU's edits.
  - deferred: **Gate 1's ranking is unchanged.** With only bug- and feature-kind items
  - deferred: `ActionOutcome` carries a spend field defaulting to zero, and `run_agent`
  - deferred: `RunSummary` and the printed run summary name total reported spend alongside
  - deferred: `specfuse/agent/run.py` exposes `default_providers(...)` returning the
  - deferred: **An escalated outcome can reach the human inbox, not only stdout.**
  - deferred: **An escalation with no payload is reported as summary-only, in words.** When
- **FEAT-2026-0049/T06** (`WU-06-bugs-provider.md`)
  - deferred: `tests/test_agent_provider_bugs.py::TestBugsProvider::test_declined_outcome_escalates_without_second_issue`
  - deferred: `specfuse/agent/providers/bugs.py` implements T05's protocol over
  - deferred: The same test passes after this WU's edits.
  - deferred: `advertise` returns one `kind="bug"` item per open snapshot issue whose triage
  - deferred: `execute` maps `merged` to a completed outcome and `declined` / `refused` /
  - deferred: **No second escalation.** For `refused` / `could_not_proceed` the lane has
  - deferred: The provider is registered in `default_providers()` and the provider performs
- **FEAT-2026-0049/T07** (`WU-07-triage-provider.md`)
  - deferred: `tests/test_agent_provider_triage.py::TestTriageProvider::test_low_confidence_under_auto_becomes_question`
  - deferred: `specfuse/agent/providers/triage.py` implements T05's protocol over
  - deferred: The same test passes after this WU's edits.
  - deferred: The provider passes `auto=snapshot.triage_auto` to `apply_triage` and contains
  - deferred: A classifier result naming a category outside `triage.CATEGORIES` never
  - deferred: A row `list_untriaged` flags `already_structured` (a harvester finding) is not
  - deferred: The provider is registered in `default_providers()`, advertises
- **FEAT-2026-0049/T08** (`WU-08-answered-escalations.md`)
  - deferred: `tests/test_agent_provider_answers.py::TestAnsweredEscalations::test_numbered_reply_is_parsed_and_acknowledged`
  - deferred: `specfuse/agent/providers/answers.py` implements T05's protocol, advertising
  - deferred: The same test passes after this WU's edits.
  - deferred: The label name, the marker pattern, and the numbered-answers shape are read
  - deferred: An acknowledged answer produces exactly one `gh issue comment` naming the
  - deferred: An issue whose comments match no numbered option is left untouched — no
  - deferred: The provider is registered in `default_providers()` and performs no git

## Gate 3

Three substantive work units, three first-attempt passes, no re-arms, no
driver-refused attempts. This is the first gate whose deliverables cannot be
exercised against the repository that ships them, and the first gate of this
feature whose close was forced to run rather than auto-closing.

### Cost against `cost_budget_usd`

Read from `events.jsonl` (`attempt_outcome` / `task_completed` payloads) and WU
frontmatter, not estimated.

| WU | ID | attempts | planned | actual | duration | outcome |
|---|---|---|---|---|---|---|
| `WU-09-findings-seam.md` | T09 | 1 | $6.50 | **$1.42** | 632s | passed |
| `WU-10-findings-diagnose-provider.md` | T10 | 1 | $7.50 | **$1.76** | 676s | passed |
| `WU-11-findings-autofix-provider.md` | T11 | 1 | $6.50 | **$1.76** | 907s | passed |
| **substantive total** | | **3** | **$20.50** | **$4.94** | **2216s (37 min)** | |

`cost_budget_usd: 38.50`. The three substantive units consumed **$4.94, 12.8% of
the gate budget** and 24% of their own planned sum. Every unit ran `model: sonnet`
/ `effort: medium` at `re_arm_count: 0`.

The closing pair (`G3-CLOSE-INTERMEDIATE` $4.50, `G3-PLAN` $6.00) is not in the
table: this session is the first of them, and the driver writes a closing WU's
`attempt_outcome` row after the session ends. That is a row not yet written, not
a row lost — the escalation trigger about missing `events.jsonl` rows (#1024) did
**not** fire here. Every substantive work unit in gates 1, 2 and 3 has both its
`task_started` and its `attempt_outcome`/`task_completed` rows present.

For the feature so far: gate 1 spent $5.95 against $36.00, gate 2 spent $6.66
against $45.50, gate 3's substantive work spent $4.94 against $38.50. Three gates
in, budget has never been the binding constraint on this feature, and the
`planning-discipline.md` §5 padding has never been drawn on.

### What actually happened

- **T09 — the seam.** Added `KIND_FINDING_DIAGNOSE` and `KIND_FINDING_AUTOFIX` to
  `specfuse/agent/run.py`, placed both in `_select_next` (autofix at the bug tier
  honouring `rules.bugs.preempt`; diagnose at tier 3 with `KIND_TRIAGE` moved to
  sub-rank 1), created `specfuse/agent/monitoring_read.py` with its three readers
  (`load_monitoring_config`, `component_for_finding`, `component_diagnose_dial`),
  and added `--monitoring-config` to `main()`. Nine tests.
- **T10 — findings-diagnose.** `specfuse/agent/providers/findings_diagnose.py`
  plus `specfuse/agent/diagnose_invoke.py`, which delegates its whole parse to
  `diagnose_cli.render_headless` and holds no parsing of its own
  (`diagnose_invoke.py:89`). Seven tests.
- **T11 — findings-autofix.** `specfuse/agent/providers/findings_autofix.py` over
  `run_autofix`, passing `specfuse.monitor.autofix_invoke` as the `invoker`.
  Eleven tests, one per row of the outcome table.

The provider protocol took two more implementers without changing: `advertise` /
`execute` / `reconcile` still fit, and neither findings provider needed a fourth
verb. Five providers across two gates now implement the protocol T04 defined
before it had a single consumer — which is the evidence T04's escalation trigger
asked for and did not have at the time.

**Oracles re-run fresh in this session** (`close-discipline.md` §1), not inherited
from the producing WUs' self-reports:

- `python3 -m unittest discover -s tests -v -b` — **2992 tests, OK (1 skipped), exit 0**,
  109s. This is the feature-level re-run; it is not carried forward.
- The three gate-3 test modules scoped: 27 tests, OK.
- `ruff check specfuse .specfuse/scripts tests scripts` — All checks passed, exit 0.
- `specfuse lint .specfuse/features/FEAT-2026-0049-specfuse-agent-runner` — OK, exit 0.

### Four findings this gate produced

None is a defect in shipped behaviour; all four are things a reader would
otherwise assume wrongly.

1. **`reconcile` has still never done anything — now across five providers.**
   All five implement it as `return None` (`providers/findings_diagnose.py:180`,
   `providers/findings_autofix.py:225`, and the three from gate 2). Gate 2's
   review named gate 4's feature provider as the verb's last chance to earn its
   place. Gate 3 does not change that, and the sample is now large enough that
   "the protocol has three verbs" should be read as "two verbs and a hook nobody
   has needed."
2. **The spend ledger still counts zeros, and gate 3 added two more spenders.**
   No provider anywhere sets `ActionOutcome.spend`; every one takes the default
   of zero. `--max-tokens` is wired end to end and still cannot fire on real
   work. T11's escalation trigger was written to refuse reporting zero as if it
   were measured, and it did not need to fire — because no live run happened.
   This is unchanged from gate 2 and is now two gates old.
3. **The diagnose → autofix handoff is untested even against fixtures.**
   `GATE-03-REVIEW.md` recorded it as needing a live run on a repo with at least
   two findings. That understates it: no test drives both findings providers
   through `run_agent` in one run at all. The ranking premise the handoff rests
   on *is* tested (`test_full_kind_ordering_with_findings_inserted`), and T11's
   `advertise` does read comments live — but "a diagnosis posted at iteration 3
   is visible at iteration 4" has never been executed, in any environment. It is
   an argument, not a result.
4. **`test_default_providers_returns_empty_registry` is now green for a
   different reason than it was written for.** T05's criterion 7 said "the
   registry returns `()` in this unit"; the test asserts
   `tuple(default_providers()) == ()`. `default_providers()` today returns five
   providers when given a `repo` and `()` when not — so the test passes on the
   `repo=None` path while its name still reads as an emptiness invariant.
   Verified directly: `default_providers(repo='owner/repo', ...)` returns
   `AnsweredEscalationProvider, BugsProvider, TriageProvider,
   FindingsDiagnoseProvider, FindingsAutofixProvider`. Not a bug — the behaviour
   is correct and separately covered by each provider's
   `test_..._registers_..._provider`. It is a test whose name asserts more than
   its body does, which is the shape that reads as coverage while checking
   something else.

## What the loop did NOT verify (gate 3)

**The debts of gate 1 and gate 2 are reconciled below, in this section**, along
with gate 3's own. Gate 1 (T01–T04, 27 criteria) and gate 2 (T05–T08, 30
criteria) each auto-closed and each left a `specfuse:autoclose-debt` marker;
`WU-93` was drafted to reconcile gate 1's and auto-closed itself, so both were
still open when this close began. `G4-CLOSE` must name gate 1, gate 2 and gate 3
in its own deferral section — the guard reads only the **last** such section in
this file, so this one stops being the record the moment gate 4 writes its own.

Gate 3's ceiling is not gate 1's or gate 2's. Those gates' criteria were met
against this repo's live issues and its real `agent-policy.yml`. Gate 3's were
met against test doubles, because `.specfuse/verification.yml`'s
`monitoring-example-lint` gate says this repo "is a CLI tool with no deployable
components and will never carry a real monitoring.yml." No `monitoring.yml`
means no harvester run, which means no `monitoring-finding` issue has ever
existed here.

### Gate 3 — the criteria met only against fixtures

Per criterion, not as a blanket sentence. A criterion absent from this list was
met against the real thing and is not deferred. `kind:
externally-verifiable-later` for every entry: a real run in a monitoring-configured
repo is a nameable condition, not an inherent impossibility.

| Criterion | What stood in for the live surface | The live condition that would prove it |
|---|---|---|
| **T09#5** — `component_for_finding` resolves a finding issue's component | A body built by the real `specfuse.monitor.issues._render_body` inside the test (`tests/test_agent_findings_seam.py:194`) — the format is real, the issue is not | One `specfuse monitor run` against a repo with a real `monitoring.yml`, filing one real finding issue, then `component_for_finding` over that issue's body |
| **T09#5** — `load_monitoring_config` reads a config | A fixture config file written by the test; no operator-authored `monitoring.yml` has ever been parsed by this reader | Loading a real `.specfuse/monitoring.yml` from a monitoring-configured repo |
| **T09#6** — `--monitoring-config` defaults to `.specfuse/monitoring.yml` | The default is asserted as a value; the path has never resolved to a file that exists | One `specfuse-agent run` in a repo where that path exists, with the config actually loaded |
| **T10#2** — the provider composes `render_headless` over a headless analysis session | An injected `runner` returning canned analysis JSON. `render_headless` itself is the real function | One live `specfuse-agent run`, with a real headless session producing the analysis |
| **T10#5** — an unparseable analysis posts nothing | A purpose-built bad input (the negative observation is real and does prove the branch). What is unproven is the **rate** at which real sessions produce one | The same live run, with the `AnalysisParseError` escalation count read afterwards |
| **T10#6** — dial-off findings are not advertised | A fixture config's `diagnose:` value. No operator has ever set that dial for code that reads it — T10 is its first consumer | A repo whose `monitoring.yml` sets `diagnose: manual` on one component and `auto` on another, one run, advertisement counts read |
| **T11#2** — the provider reaches `run_autofix` with `autofix_invoke` as `invoker` | The invoker is passed but never called: no `/fix-bug` session has ever been launched down this path | A live run where `decide` returns `FIRE` for at least one finding |
| **T11#5** — each row of the outcome table | Fabricated `AutofixRunResult` values. Every branch is proven; `autofix.decide` itself is never exercised on real diagnosis text | The same live run, with `decide`'s reason distribution read from the run summary |
| **T11#6** — unresolvable components are not advertised | A fixture config missing the component | Same condition as T10#6 |
| **The diagnose → autofix handoff within one run** (finding 3 above; the premise under T09#4's ranking) | **Nothing.** No test drives both providers through `run_agent` together | A live run on a repo with at least two findings — or, cheaper and available now, one fixture-level test that registers both providers and asserts the iteration-4 visibility |

Criteria **T09#1–#4, T09#7, T10#1, T10#3, T10#4, T10#7, T11#1, T11#3, T11#4,
T11#7** were met against the real code paths and are not deferred: ranking,
symbol existence, the byte-identical render assertion, the no-writes assertions,
the structural "re-decides nothing" grep, and provider registration all execute
the shipped functions directly.

**Do not close this gap by inventing a `.specfuse/monitoring.yml` for this
repository.** It would make `monitoring-example-lint`'s stated reasoning false
and would be a fixture masquerading as a live surface, which is worse than an
honest deferral.

### Gate 1's auto-close debt — reconciled

Against the `specfuse:autoclose-debt` marker above (gate 1, T01–T04, 27
criteria). All 27 re-verified in this session against a fresh full-suite run.
The marker itself is left in place: it records that gate 1 auto-closed, which
remains true, and deleting it would erase the history rather than discharge it.
Per work unit, the oracle re-run and its result:

| WU | Criteria | Oracle re-run this attempt | Result |
|---|---|---|---|
| T01 | 1, 3, 4 | `tests.test_agent_lock.TestAgentLock.test_second_acquire_raises` | pass |
| T01 | 2 | `inspect.signature` → `acquire_tree_lock(specfuse_dir, lock_name='.loop.lock')`, `acquire_agent_lock(specfuse_dir)`; the `loop.py:6102` call site covered by the full suite | pass |
| T01 | 5 | `tests.test_agent_lock` `test_independent_of_driver_lock` | pass |
| T01 | 6 | `.gitignore:30` carries `.specfuse/.agent.lock` beside `.loop.lock` at `:29` | pass |
| T02 | 1, 3 | `tests.test_agent_state` `test_queue_read_from_policy` | pass |
| T02 | 2 | `state.gather_snapshot` is the one public entry point; `AgentSnapshot` is `frozen=True`; every read goes through the injected runner | pass |
| T02 | 4 | `test_missing_policy_yields_empty_queue_and_defaults` | pass |
| T02 | 5 | `test_failing_runner_yields_empty_section_with_reason`, `test_unparseable_runner_output_yields_empty_section_with_reason` | pass |
| T02 | 6 | `test_no_mutating_gh_subcommand_issued` | pass |
| T03 | 1, 3 | `tests.test_agent_budget` `test_cap_is_not_checked_mid_item` | pass |
| T03 | 2 | `RunBudget(*, clock, max_minutes=None, max_tokens=None, max_items=None, pause_marker=...)` — clock injected, three caps present | pass |
| T03 | 4 | `test_max_items_stops_next_item`, `test_max_minutes_stops_next_item`, `test_max_tokens_stops_next_item` | pass |
| T03 | 5 | `test_absent_caps_are_unbounded`, `test_max_items_zero_is_not_conflated_with_unset` | pass |
| T03 | 6 | `test_pause_marker_stops_at_next_boundary_with_distinct_reason` | pass |
| T03 | 7 | `test_stop_reasons_are_distinct`; `STOP_DRAINED` / `STOP_CAP` / `STOP_PAUSE` / `STOP_ERROR` all exported | pass |
| T04 | 1, 3 | `tests.test_agent_run` `test_drains_cleanly_with_no_providers` | pass |
| T04 | 2 | `run_agent`, `main`, `ActionProvider`, `ActionItem`, `ActionOutcome`, `RunSummary` all importable from `specfuse.agent.run` | pass |
| T04 | 4 | `pyproject.toml` `[project.scripts]` carries `specfuse-agent = "specfuse.agent.run:main"` alongside five others | pass |
| T04 | 5 | `test_second_agent_names_lock_path_not_traceback` | pass |
| T04 | 6 | `test_summary_reports_actual_elapsed_time_not_the_cap` | pass |
| T04 | 7 | `test_bug_preempts_feature_when_policy_says_so`, `test_queue_order_settles_features`, `test_provider_exception_escalates_and_run_continues` | pass |
| T04 | 8 | `test_loop_never_hands_its_runner_to_a_provider` | pass |

Module totals re-run this session: `test_agent_lock` 2, `test_agent_state` 7,
`test_agent_budget` 8, `test_agent_run` 7 — all OK.

### Gate 2's auto-close debt — reconciled

Against the `specfuse:autoclose-debt` marker above (gate 2, T05–T08, 30
criteria). All 30 re-verified the same way, and the marker is likewise left in
place as history.

| WU | Criteria | Oracle re-run this attempt | Result |
|---|---|---|---|
| T05 | 1, 3 | `tests.test_agent_seam` `test_triage_item_is_selected_not_escalated` | pass |
| T05 | 2 | `KIND_TRIAGE` / `KIND_ESCALATION_ANSWER` importable; ranking exercised by the same test | pass |
| T05 | 4 | `test_gate1_ranking_unchanged_bugs_preempt_false`, `..._true`, `test_unknown_kind_still_parked_with_escalation` | pass |
| T05 | 5, 6 | `test_reported_spend_reaches_budget_and_summary`, `test_no_spend_reported_leaves_total_zero` | pass |
| T05 | 7 | `test_default_providers_returns_empty_registry`, `test_run_agent_providers_default_is_empty_tuple` — **pass, but see finding 4 above**: the emptiness half of this criterion was true at T05 and is deliberately superseded by T06–T11 | pass, superseded |
| T05 | 8 | `test_escalated_outcome_with_payload_files_one_issue_not_two` | pass |
| T05 | 9 | `test_escalated_outcome_without_payload_is_summary_only` | pass |
| T06 | 1, 3 | `tests.test_agent_provider_bugs` `test_declined_outcome_escalates_without_second_issue` | pass |
| T06 | 2 | `providers/bugs.py` imports and calls `run_bug_lane` | pass |
| T06 | 4 | `test_advertise_returns_bug_item_for_triaged_bug`, `test_advertise_skips_non_bug_category`, `test_advertise_skips_untriaged_issue` | pass |
| T06 | 5 | `test_execute_maps_merged_to_completed`, `..._declined_to_escalated_with_reason`, `..._refused_to_escalated_with_detail`, `..._could_not_proceed_to_escalated_with_detail` | pass |
| T06 | 6 | `test_reconcile_issues_no_gh_call`, `test_lane_filed_outcomes_carry_no_escalation_payload` | pass |
| T06 | 7 | `test_default_providers_registers_bugs_provider`, `test_execute_passes_injected_runner_through_without_git_mutation` | pass |
| T07 | 1, 3 | `tests.test_agent_provider_triage` `test_low_confidence_under_auto_becomes_question` | pass |
| T07 | 2 | `providers/triage.py` + `triage_invoke.py` present, over `list_untriaged` / `apply_triage` | pass |
| T07 | 4 | the same criterion-1 test, asserted through the `gh issue edit` body | pass |
| T07 | 5 | `test_out_of_vocabulary_category_escalates_without_edit` | pass |
| T07 | 6 | `test_advertise_skips_already_structured_row` | pass |
| T07 | 7 | `test_default_providers_registers_triage_provider`, `test_execute_issues_no_git_mutation_of_its_own` | pass |
| T08 | 1, 3 | `tests.test_agent_provider_answers` `test_numbered_reply_is_parsed_and_acknowledged` | pass |
| T08 | 2 | `providers/answers.py` advertises `escalation-answer` for labelled+marked+answered issues | pass |
| T08 | 4 | label, marker and numbered-answers shape read from `specfuse.loop.escalation`'s own constants | pass |
| T08 | 5 | `test_needs_human_label_is_not_removed`, `test_second_pass_over_acknowledged_issue_writes_nothing`, plus the criterion-1 test | pass |
| T08 | 6 | `test_unmatched_comment_is_left_untouched_and_not_advertised` | pass |
| T08 | 7 | `test_default_providers_registers_answered_escalation_provider`, `test_execute_issues_no_git_mutation_or_issue_close` | pass |

Module totals re-run this session: `test_agent_seam` 11,
`test_agent_provider_bugs` 12, `test_agent_provider_triage` 6,
`test_agent_provider_answers` 6 — all OK.

### What this close could NOT reconcile, named individually

Two clauses recur across gates 1, 2 and 3 and are **not** re-provable in a
close session. Neither is an oracle that has gone missing — every named test
still exists under its original nodeid, so the escalation trigger about a
deleted or renamed oracle did not fire.

1. **"…and fails on HEAD before this WU runs."** The first acceptance criterion
   of every one of the eleven substantive work units (T01–T11) carries this
   red-before-green half. It was true when the producing session ran and is not
   re-provable now: the pre-WU tree state is gone from the working tree, and a
   closing session runs no `git` command by contract. What this close did
   re-prove is the other half — the test exists at the stated nodeid and is
   green. **Eleven criteria, half-reconciled**: T01#1, T02#1, T03#1, T04#1,
   T05#1, T06#1, T07#1, T08#1, T09#1, T10#1, T11#1.
2. **"No file under `specfuse/loop/` (or `specfuse/monitor/`) is edited."** This
   is a diff claim, and diffs need `git`. It appears in **T06#2, T07#2, T10#2
   and T11#2**. Four criteria, unreconcilable in this session by construction.
   They are not unverified in the loop as a whole — the driver's
   produces-vs-diff guard and each WU's `Do not touch` boundary cover them at
   squash time — but this close cannot be the one to assert them, and says so
   rather than marking them verified on a substitute.

`G4-CLOSE` inherits both lists. It runs under the same no-git contract, so it
will not be able to reconcile them either; the honest disposition at the
terminal verdict is to carry them as `kind: inherent` rather than to keep
deferring them to a close that structurally cannot discharge them.

## Lessons promoted

**Nothing generalizes into `.specfuse/LEARNINGS.md` from this close** — not
because nothing was learned, but because this feature runs
`autonomy_default: auto`, and under `auto` a closing WU whose diff touches
`.specfuse/LEARNINGS.md` fails `assert_learnings_staged_under_auto`. No human
read this gate before the close dispatched, so the four lessons this gate
produced are staged in `LEARNINGS-pending.md` in this feature folder for a human
to promote at PR review. That is the mechanism working, not an absence of
lessons.

