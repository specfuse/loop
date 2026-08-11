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

## Gate 4 — the agent advances features

Three substantive work units, three first-attempt passes, no re-arms, no
driver-refused attempts. The terminal gate, and the one where the thing being
driven is the same machinery doing the driving.

### The headline: this feature has never been run

**No `specfuse-agent run` has executed against live repository state at any
point in gates 1, 2, 3 or 4.** Every behaviour this feature ships is proven by
test against injected runners and fixture feature folders. The command exists,
it is installed as a console script, its six providers register, and its whole
selection-and-stopping machinery is covered by 3046 passing tests — and nobody
has ever typed it and watched what happened.

**This is "not proven", not "disproven".** Nothing observed in four gates
suggests the runner is broken. No test has failed for a reason that implicates
live behaviour, no design assumption has been contradicted, and the one live
surface a close *can* reach without dispatching anything was reached in this
session and behaved exactly as its tests said it would (see § "What this close
proved against live state"). The distinction matters because the two readings
lead to opposite next actions: "disproven" would mean fix something, and
"not proven" means run it once, under caps, and read the result.

Two standing findings belong in the same headline, because both are properties
of the shipped code rather than of the test environment:

1. **`reconcile` was called by six providers across four gates and did nothing
   every time.** Every implementation is `return None` —
   `providers/answers.py:219`, `bugs.py:128`, `triage.py:173`,
   `findings_diagnose.py:180`, `findings_autofix.py:225`, `feature.py:334`.
   The call site is real (`run.py:332`, executed for every item), so this is
   not "untested"; it is "tested, called, and empty." Gate 2's review named the
   feature provider as the verb's last chance to earn its place. It did not
   take it, and that was a decision recorded in advance
   (`GATE-04-REVIEW.md` § "The `reconcile` verdict"), not an oversight. A
   future feature should either delete the verb or name the case that needs it;
   after four gates the honest reading of the protocol is "two verbs and a hook
   nobody has needed."
2. **`--max-tokens` is wired end to end and every provider still reports
   `spend=0`.** `ActionOutcome.spend` defaults to `0` (`run.py:125`) and
   `budget.record_tokens(outcome.spend)` runs on every item (`run.py:333`), so
   the ledger is live and the number flowing through it is always zero — no
   provider anywhere assigns `spend`. The cap therefore cannot fire on real
   work. Gate 4 adds the most expensive spender of the six: `advance_feature`
   launches a full driver run. Unlike the earlier five it has a plausible spend
   source — the driver writes cost into WU frontmatter via `write_cost_to_wu` —
   but reading it was never drafted, and reporting a measured zero when nothing
   was measured is exactly what T11's escalation trigger refused to do.

### What actually happened

- **T12 — the workability classifier.** `specfuse/agent/queue_read.py` with
  five disposition constants, `classify_queue_entry` in a stated precedence
  order (`UNREADABLE` first, because an unparseable folder is
  indistinguishable from an absent one by `feature_id` alone), `select_workable`
  with `DONE` entries consuming no `wip_limit` slot, and the two
  `rules.features` readers. Promoted `state._read_features` to
  `read_feature_summaries` with the old name retained as an alias. Nineteen
  tests.
- **T13 — the subprocess seam.** `specfuse/agent/driver_invoke.py`:
  `build_invocation`, six halt classes, `advance_feature`. The subprocess
  invariant is now mechanical rather than remembered — a structural test
  asserts the module's source contains neither `loop.run` nor
  `specfuse.loop.loop`. Sixteen tests.
- **T14 — the feature provider.** `specfuse/agent/providers/feature.py` over
  T12 and T13, registered in `default_providers()`. Nineteen tests, including
  one per row of the halt→outcome table. The two escalation categories
  `escalation.py` declared and nothing had ever used — `drafting-needed` and
  `gate-review` — got their first consumer.

`default_providers(repo='owner/repo')` now returns six providers, verified
directly in this session: `AnsweredEscalationProvider`, `BugsProvider`,
`FeatureProvider`, `TriageProvider`, `FindingsDiagnoseProvider`,
`FindingsAutofixProvider`.

### Oracles re-run fresh in this session

Per `close-discipline.md` §1 — run here, exit codes read directly, nothing
inherited from a producing WU's self-report.

| Command | Result |
|---|---|
| `bash scripts/smoke-test.sh` (the full `code` gate set, all 16 gates derived from `.specfuse/verification.yml`) | **exit 0** — `smoke test: OK` |
| ↳ `tests` gate: `python3 -m unittest discover -s tests -v -b` | **3046 tests, OK (skipped=1)**, 116.5s |
| ↳ `lint` gate: `ruff check specfuse .specfuse/scripts tests scripts` | `All checks passed!` |
| ↳ `security` gate: `bandit -r specfuse .specfuse/scripts -ll` | `No issues identified.` (0 medium, 0 high) |
| ↳ `coverage` gate: `coverage run --source=specfuse … && coverage report --fail-under=90` | `TOTAL 10288 676 93%` — above the 90% floor |
| ↳ the remaining 12 gates (leak-scan, event-type, roadmap-link, arm-sweep, monitoring-example-lint, and the six `bats` suites) | all green; `roadmap-link-gate` printed 3 non-failing WARNs |
| `python3 -m unittest tests.test_agent_queue_read -b` | **exit 0**, 19 tests, OK |
| `python3 -m unittest tests.test_agent_driver_invoke -b` | **exit 0**, 16 tests, OK |
| `python3 -m unittest tests.test_agent_provider_feature -b` | **exit 0**, 19 tests, OK |

The three gate-4 modules together: **54 tests, OK**. The full-suite run is the
feature-level re-run and is **not** carried forward to any future close attempt.

Every one of `GATE-04-CRITERIA.md`'s 22 entries was additionally re-run under
its own scoped oracle this attempt, all `state: pass`. All 22 are `kind: narrow`
— a scoped nodeid, a symbol-existence import, or a structural assert. **No
gate-4 criterion carries a `broad` oracle**, which is a statement about this
gate rather than an omission: no acceptance criterion here names the full suite
as its proof. The full suite still ran, as the feature-level oracle above; it
just is not what any single criterion rests on.

### What this close proved against live state

Small, but real, and worth separating from the fixtures. T12's readers were
pointed at this repository's own files in this session — not at a fixture:

```
resolve_wip_limit('.specfuse/agent-policy.yml')                 -> 1
resolve_gate_review('.specfuse/agent-policy.yml', 'FEAT-2026-0049') -> 'human'
read_feature_summaries(Path('.specfuse/features'))              -> 63 summaries, 0 unreadable
classify_queue_entry('FEAT-2026-0049', …)                       -> workable
select_workable(['FEAT-2026-0049'], …, wip_limit=1)             -> (('FEAT-2026-0049',), ())
```

So `rules.features.wip_limit` and `rules.features.gate_review` — validated by
`agent_policy.py` since FEAT-2026-0044 and read by no shipped code until T12 —
have now been read from an operator-authored policy file, and the classifier has
been run over 63 real feature folders rather than fixtures. This is read-only:
no `gh` call, no write, no driver invocation. It is also the exact hazard
`GATE-04-REVIEW.md` § "Risks to weigh before arming" named — the live queue top
is this feature — observed rather than argued: a real `specfuse-agent run` here
would classify `FEAT-2026-0049` as workable and invoke the driver on the feature
it is being built inside.

### Findings this gate produced

None is a defect in gate 4's shipped behaviour. Two are corrections to the
record, one is a driver defect this close can see and is forbidden to fix.

1. **"Every substantive work unit was a first-attempt pass" is false, and it is
   written in three places.** `PLAN.md` § "A note on `planned_cost_usd`",
   `GATE-04-REVIEW.md` § "On the estimates", and `GATE-03-REVIEW.md` all say
   eleven substantive units, every one a first-attempt pass. **T06 failed its
   first attempt** — `events.jsonl` records `attempt: 1, outcome: failed,
   failure_class: tests, cost_usd: 0.703116`, then `attempt: 2, outcome:
   passed`; `WU-06-bugs-provider.md` frontmatter reads `attempts: 2`. Fourteen
   substantive units, thirteen first-attempt passes, one re-arm. The claim was
   used as evidence for a cost-estimating decision ("eleven observations is a
   distribution, not an outlier"), so it is not cosmetic — though the
   correction does not change the decision, since thirteen of fourteen is still
   a distribution. Not fixed here: those are gate 1–3 planning artifacts and a
   close records rather than revises.
2. **The failure-class breakdown guard cannot see a substantive work unit's
   failure.** `summarize_attempt_failure_classes(feature_dir, gate_n, …)`
   resolves an event's gate through `_gate_number_from_wu_id`
   (`loop.py:4976`), which matches `^G(\d+)-` on the ID's last segment. A
   substantive ID (`FEAT-2026-0049/T06`) has no such prefix, so it returns
   `None` and the event is filtered out of **every** gate-scoped summary.
   Observed directly: the gate-scoped call returns `(no non-passing attempts in
   scope)` for gates 1, 2, 3 and 4, while the unscoped call over the same file
   returns a table with one row — `tests | 1 |
   test_default_providers_returns_empty_registry`. So `close-f`
   (`assert_failure_class_breakdown_when_failures_present`), which is gate-
   scoped, can only ever fire on a *closing* WU's own failed attempt. A
   substantive WU's failure is structurally invisible to it. **This is a driver
   defect, not a gate-4 defect, and this close does not fix it** — a closing
   unit records; the fix is a bug with its own branch. The breakdown below is
   therefore written from the unscoped read, which is the true one.
3. **T06's one failure was on the test gate 3's close later flagged as
   misnamed.** Its `failure_signature` is
   `test_default_providers_returns_empty_registry` — the same test gate 3's
   retrospective finding 4 recorded as "green for a different reason than it
   was written for". The two observations are one story: a test asserting an
   emptiness invariant that later WUs deliberately superseded cost one failed
   attempt ($0.70) while it was being superseded, and then went on reading as
   coverage afterwards. The lesson gate 3 staged about superseded criteria has
   a price attached to it after all.

## Cost analysis

Every figure read from `events.jsonl` `attempt_outcome` / `task_completed`
payloads and from WU frontmatter — none estimated. No row was missing: the
escalation trigger about `events.jsonl` rows lost between a squash and the next
bookkeeping commit (#1024) did **not** fire, and every substantive work unit in
all four gates has both its `task_started` and its
`attempt_outcome`/`task_completed` rows present.

| Gate | Planned (sum of WU `planned_cost_usd`) | Actual | `cost_budget_usd` | Actual as % of budget |
|---|---|---|---|---|
| 1 | $29.50 | **$13.19** | $36.00 | 36.6% |
| 2 | $39.50 | **$14.94** | $45.50 | 32.8% |
| 3 | $31.00 | **$23.73** | $38.50 | 61.6% |
| 4 | $23.00 | **$4.47** | $29.50 | 15.2% |
| **feature** | **$123.00** | **$56.33** | **$149.50** | **37.7%** |

Gate 4's actual excludes this closing session: the driver writes a closing WU's
`attempt_outcome` row after the session ends, so that row is not yet written —
not lost. At its $5.00 plan the gate would land near $9.47 against $29.50.

### The distribution that matters, per work unit

| WU | ID | attempts | planned | actual | duration | outcome |
|---|---|---|---|---|---|---|
| `WU-12-queue-workability.md` | T12 | 1 | $5.50 | **$0.72** | 334s | passed |
| `WU-13-driver-invoke.md` | T13 | 1 | $6.00 | **$1.57** | 735s | passed |
| `WU-14-feature-provider.md` | T14 | 1 | $6.50 | **$2.18** | 786s | passed |
| **gate-4 substantive** | | **3** | **$18.00** | **$4.47** | **1855s (31 min)** | |

Across all four gates: **fourteen substantive work units planned $86.50 and
spent $22.03 — 25.5% of plan.** Every one ran `model: sonnet` / `effort:
medium`; thirteen passed first attempt, T06 took two.

**The closing units are where the money went, and that is the one real cost
finding of this feature.** Seven closing units were planned at $36.50. Two
(gate 1's and gate 2's close-intermediates) auto-closed at `attempts: 0` and
cost **$0.00**. One is this session. The four that actually ran cost
**$34.30 — 60.9% of the feature's entire $56.33 spend** — and every one of them
overran its estimate, in the opposite direction to every substantive unit:

| Closing WU | planned | actual | delta |
|---|---|---|---|
| `G1-PLAN` | $6.00 | $7.24 | **+21%** |
| `G2-PLAN` | $6.00 | $8.28 | **+38%** |
| `G3-CLOSE-INTERMEDIATE` | $4.50 | $7.02 | **+56%** |
| `G3-PLAN` | $6.00 | $11.77 | **+96%** |

All four ran `model: opus` / `effort: high`; all fourteen substantive units ran
`sonnet` / `medium`. That is most of the explanation, and it is a deliberate
setting rather than a surprise — but it means the feature's cost model is
inverted from the one the estimates assume. `planning-discipline.md` §5 sizes a
gate's padding off *the largest substantive estimate* and treats a closing-WU
retry as a defect to diagnose rather than a cost to budget for. On this feature
the substantive units came in at a quarter of plan while the closing units came
in at up to double, and the padding was never drawn on because the substantive
underrun absorbed it. Budget was never the binding constraint here — but if it
ever becomes one, the estimates are wrong at the closing units, not at the
implementation units.

Gate 3's $23.73 stands out for the same reason and no other: it is the only
gate whose close was forced to run *and* whose `plan-next` had four gates of
accumulated context to reconcile.

### Failure-class breakdown

Read unscoped across all four gates, for the reason recorded in finding 2
above: the gate-scoped read is structurally blind to a substantive work unit's
failure, and gate-scoped it would print `(no non-passing attempts in scope)`
for every gate — which would be true of what it can see and false of what
happened.

| failure_class | non-passed attempts | dominant signature |
|---------------|---------------------|--------------------|
| tests | 1 | test_default_providers_returns_empty_registry |
| **total** | **1** | — |

One non-passing attempt in 21 work units across four gates: T06, attempt 1,
$0.70, recovered on attempt 2. No `blocked` outcome, no `spinning_detected`, no
driver-refused attempt, and no re-arm requiring a human anywhere in the feature.

## Consumer-visible contract changes

Enumerated per `close-discipline.md` §3. This is **not** an `n/a` close — the
feature adds a new command and changes what an existing one does. Each item is
appended to `CHANGELOG.md`'s `Unreleased` section under this feature's ID.

1. **`specfuse-agent`, a new console script** —
   `specfuse-agent = "specfuse.agent.run:main"` in `pyproject.toml`
   `[project.scripts]`, taking the shipped entry points from five to six. It is
   the operator-launched conductor: it takes `.specfuse/.agent.lock` (its own,
   distinct from the driver's `.specfuse/.loop.lock`), reads repo state, and
   runs select→execute→reconcile to drain.
2. **Seven new CLI flags on that command**, all optional with safe defaults:
   `--repo` (OWNER/NAME), `--policy` (path to `agent-policy.yml`),
   `--features-root` (path to `.specfuse/features`), `--monitoring-config`
   (defaults to `.specfuse/monitoring.yml`), and the three caps `--max-minutes`,
   `--max-tokens`, `--max-items`, each defaulting to `None` meaning unbounded.
   Two things about the caps a consumer will otherwise assume wrongly: they are
   checked **at item boundaries only**, so a cap can overshoot by the duration
   of one running item and never interrupts work in progress (D3); and
   `--max-items` counts **advertised items, which for a feature means gates,
   not features** — one feature advancing four gates consumes four items, so
   `--max-items 3` yields one feature, not three.
3. **`--max-tokens` is enforceable in principle and inert in practice.** The
   ledger is wired end to end, and every provider reports `spend=0`, so the cap
   cannot currently fire on real work. Stated here rather than in the
   retrospective alone because a consumer reading the flag list would otherwise
   expect it to bound cost.
4. **A behaviour change to `default_providers()` — an unattended
   `specfuse-agent run` now dispatches the loop driver.** This is a change to
   what an existing command does, not an addition, and it is the largest
   blast-radius change the feature makes. Before gate 4, the command could file
   bug PRs, triage issues, answer escalations, post diagnoses and fire
   autofixes. After it, the same command reads `queue:` from
   `.specfuse/agent-policy.yml` and invokes `specfuse run` on the top workable
   feature — which commits. There is **no opt-in flag**: the provider is
   registered like the other five. That was decided as OQ-3 in
   `GATE-04-REVIEW.md` on the grounds that the approved roadmap goal funds
   exactly this behaviour, and it was decided **by the agent, overnight, with
   the operator asleep**, under a standing authorization to arm unattended. The
   review recommends the operator review this one decision specifically before
   merge, and this close repeats that recommendation.
5. **Two previously inert policy dials become load-bearing.**
   `rules.features.wip_limit` (int ≥ 1, default 1) now caps how many distinct
   features one run advances, in `queue:` order, with already-`done` entries
   consuming no slot. `rules.features.gate_review` (`human` | `auto`, default
   `human`, with a per-feature `overrides` map) now decides what an
   `awaiting_review` halt does: `human` files a `gate-review` needs-human
   issue, `auto` records the halt in the run summary and files nothing. Both
   have been validated by `agent_policy.py` since FEAT-2026-0044 and read by no
   shipped code until now — so an operator who set them expecting no effect
   will now get one. Absent keys and malformed values resolve to the
   conservative defaults rather than raising.
6. **Two escalation categories reach GitHub for the first time.**
   `drafting-needed` and `gate-review` have been declared in
   `escalation.py`'s `CATEGORY_LABELS` and used by nothing; the feature
   provider is their first consumer, so repositories will begin seeing
   needs-human issues carrying those labels. No category was minted and the
   registry is unchanged.

## Hedged-verdict follow-up record

The terminal verdict is `met_locally`. Every acceptance criterion of all
fourteen substantive work units is met and re-verified; what is unproven is the
feature-level claim that the command does its job when actually run. Per
`close-discipline.md` §2, one entry per criterion below, each with the condition
that would upgrade it.

Three groups, and their `kind`s were decided by the closes that met them rather
than re-decided here. Because at least one entry is
`externally-verifiable-later`, `verdict_ceiling_for_kinds` reads **rework
exists**: a real re-run condition is nameable, so the operator has a genuine
choice between accepting the hedge now and waiting for one live run.

### Group A — gate 3's ten criteria met only against fixtures

Enumerated individually with their live conditions in § "Gate 3 — the criteria
met only against fixtures" above, which this entry carries forward verbatim
rather than restating: T09#5 (`component_for_finding`), T09#5
(`load_monitoring_config`), T09#6 (`--monitoring-config`'s default path), T10#2,
T10#5, T10#6, T11#2, T11#5, T11#6, and the diagnose→autofix handoff within one
run. Ten criteria.

- **why unverifiable here:** this repository has no `.specfuse/monitoring.yml`
  and never will — `.specfuse/verification.yml`'s `monitoring-example-lint`
  gate records that it is a CLI tool with no deployable components — so no
  harvester run has ever happened and no `monitoring-finding` issue has ever
  existed here. Inventing one would be a fixture masquerading as a live
  surface.
- **re-run condition:** one `specfuse monitor run` followed by one
  `specfuse-agent run` in a repository with a real `monitoring.yml` and at
  least two findings, one with `diagnose: auto` and one with `diagnose:
  manual`. The single cheapest partial upgrade, available in this repo today
  and not done: a fixture-level test registering both findings providers and
  asserting the iteration-4 visibility of a diagnosis posted at iteration 3.
- **kind:** `externally-verifiable-later`

### Group B — the fourteen red-before-green halves

T01#1, T02#1, T03#1, T04#1, T05#1, T06#1, T07#1, T08#1, T09#1, T10#1, T11#1,
T12#1, T13#1, T14#1. Gate 4 inherits the same criterion shape gates 1–3 used,
so the eleven gate-3's close named are now fourteen.

- **the criterion, verbatim (T12#1's, representative of all fourteen):**
  "`tests/test_agent_queue_read.py::TestQueueWorkability::test_queue_entry_without_a_feature_folder_needs_drafting`
  exists and **fails on HEAD before this WU runs** (the file does not yet
  exist)."
- **why unverifiable here:** the green-after half re-runs in milliseconds and
  did, this session, for all fourteen. The red-before half asserts a tree state
  that no longer exists and would need `git` to reconstruct; a closing session
  runs no `git` command by contract.
- **re-run condition:** none. No future close can discharge this either, for
  the same structural reason. It was true when each producing session ran and
  the driver's produces-vs-diff guard covered it at squash time; this close
  will not mark it verified on a substitute.
- **kind:** `inherent`

### Group C — the four no-file-under-`specfuse/loop/`-was-edited diff claims

T06#2, T07#2, T10#2, T11#2.

- **the criterion, verbatim (T06#2's shape):** "No file under `specfuse/loop/`
  (or `specfuse/monitor/`) is edited."
- **why unverifiable here:** it is a diff claim, and diffs need `git`.
- **re-run condition:** none, in a close session, by construction. Not
  unverified in the loop as a whole — the driver's produces-vs-diff guard and
  each WU's `Do not touch` boundary cover it at squash time — but this close
  cannot be the one to assert it.
- **kind:** `inherent`

### Group D — gate 4's own criteria, met against fixtures and an injected runner

All 22 entries in `GATE-04-CRITERIA.md`, less the live-state subset recorded in
§ "What this close proved against live state" (T12's readers and classifier,
which this session ran against this repository's real `agent-policy.yml` and its
63 real feature folders). The remainder — every halt classification in T13, and
every row of T14's halt→outcome table — was met against fixture feature folders
under a temporary directory and a runner that returns canned exit codes,
stdout and stderr.

- **why unverifiable here:** deliberately, and as a safety property rather than
  a limitation. A test that dispatched the real driver against a real feature
  in this repository would run the loop inside the loop, and this repository's
  own `queue:` top is this very feature. `GATE-04.md` § "What this gate
  deliberately does not prove" records the decision; T13's and T14's escalation
  triggers forbid working around it.
- **re-run condition:** one `specfuse-agent run` against a repository whose
  `queue:` top is a feature other than this one — under `--max-items 1` and a
  `--max-minutes` cap, which is what makes the trial cheap and bounded. That
  single run would exercise the console script, the lock, the caps, the
  snapshot, the ranking, the subprocess invocation, at least one halt
  classification and its escalation path, all at once.
- **kind:** `externally-verifiable-later`

## Lessons promoted (gate 4)

Same mechanism as gate 3's, unchanged: under `autonomy_default: auto` a closing
WU whose diff touches `.specfuse/LEARNINGS.md` fails
`assert_learnings_staged_under_auto`, so this gate's lessons are appended to
`LEARNINGS-pending.md` in this feature folder for a human to promote at PR
review. Gate 3's four are left in place and three more are appended — the file
now holds seven. This is staging, not "nothing generalizes": the lessons below
do generalize, and the staging file is where the mechanism puts them.

## What the loop did NOT verify

**This section supersedes gate 3's.** The guard reads only the last
`What the loop did NOT verify` heading in this file, so from the moment this one
is written it is the record — which is why every earlier gate's deferrals are
carried into it here rather than left behind in a section that is no longer
read. Named explicitly and by number: **gate 1**, **gate 2**, **gate 3**, and
**gate 4**.

### gate 1 — auto-close debt, reconciled

`<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03,T04 criteria=27 -->` is
still open as a marker and stays that way: it records that gate 1 auto-closed,
which remains true, and deleting it would erase history rather than discharge
it. **All 27 criteria are reconciled, and were reconciled by gate 3's close**
against a fresh full-suite run; that per-WU table — oracle re-run and result for
T01#1–#6, T02#1–#6, T03#1–#7 and T04#1–#8, 27 rows, all `pass` — is in §
"Gate 1's auto-close debt — reconciled" above and is carried forward here with
its evidence rather than redone. This close re-ran the same four modules as part
of the full suite (3046 tests, OK) and observed no regression in any of them.

One qualification, carried not created: T01#1, T02#1, T03#1 and T04#1 are
reconciled on their green-after half only. Their red-before-green half is Group
B above, `kind: inherent`.

### gate 2 — auto-close debt, reconciled

`<!-- specfuse:autoclose-debt gate=2 wus=T05,T06,T07,T08 criteria=30 -->` —
same disposition, same reason, marker likewise left standing. **All 30 criteria
are reconciled**, by gate 3's close, in the per-WU table in § "Gate 2's
auto-close debt — reconciled" above: T05#1–#9, T06#1–#7, T07#1–#7, T08#1–#7, all
`pass`. Carried forward with its evidence.

Two qualifications, both carried:

- T05#7's emptiness half is recorded `pass, superseded` — the test is green
  because `default_providers()` returns `()` on the `repo=None` path, not
  because the registry is empty. It returns **six** providers when given a
  `repo`, verified again this session. Not a defect; a test whose name asserts
  more than its body does.
- T06#1, T07#1, T08#1 are reconciled on their green half only (Group B);
  T06#2 and T07#2 are Group C, `kind: inherent`.

### gate 3 — no marker, and still named

Gate 3 left no `specfuse:autoclose-debt` marker: its close ran rather than
auto-closing. It is named here anyway because its own deferral section stopped
being the record the moment this one was written, which that close said in
writing. Its ten fixture-only criteria are Group A above,
`kind: externally-verifiable-later`, each with the live condition it already
named; T09#1, T10#1 and T11#1 are Group B and T10#2, T11#2 are Group C. Criteria
T09#2–#4, T09#7, T10#3, T10#4, T10#7, T11#3, T11#4 and T11#7 were met against
the real code paths and are **not** deferred.

Gate 3's own instruction to this close was to stop deferring Groups B and C and
carry them as `kind: inherent`. Done.

### gate 4 — its own deferrals

1. **Every gate-4 criterion less T12's live-state subset was met against
   fixtures and an injected runner** — Group D above,
   `kind: externally-verifiable-later`. Twenty-two criteria, all `pass`, none
   of them evidence that the command works when run.
2. **`reconcile` has never done anything, across six providers and four
   gates.** Verified, not assumed: all six return `None`, and the call site
   executes. Recorded as a finding for a future feature to act on, not as
   something this close can discharge.
3. **`spend` is zero everywhere, so `--max-tokens` has never bounded
   anything.** Same posture: the wiring is verified, the number is structurally
   zero, and no live run exists to measure the real one.
4. **The snapshot is not a snapshot, and this close says so plainly rather than
   deferring it again.** `run_agent` gathers one `AgentSnapshot` before the
   loop and passes that same value to `advertise()` on every iteration, but
   four of six providers now re-read live state inside `advertise` — and the
   feature provider is the first that must, because its own `execute` is what
   changed the state it re-reads. The name describes an intent the code no
   longer has. Fixing it means changing T02's gate-1 surface, which is out of
   this feature's bounds.
5. **No live-state evidence exists for any halt class.** `classify_halt`'s six
   classes were derived from the driver's shipped source and proven against
   fixture feature folders; no real `specfuse run` halt has ever been passed
   through them. If a seventh halt shape exists in practice, nothing here would
   have found it.
6. **The two things this close observed but must not fix**: the
   first-attempt-pass claim contradicted by T06's `events.jsonl` rows, and the
   gate-scoped failure-class summary that is structurally blind to substantive
   work units (`_gate_number_from_wu_id` returns `None` for a `TNN` ID). The
   first is stale prose in gate 1–3 planning artifacts; the second is a driver
   defect that needs a bug with its own branch. Both are findings above, and
   both are carried by the verdict rather than repaired here.

