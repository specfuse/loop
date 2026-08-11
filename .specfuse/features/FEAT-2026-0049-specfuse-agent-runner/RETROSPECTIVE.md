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

### The headline: selection is proven against live state; execution is not

**This headline moved during the re-arm of this close, and the move is the
point.** The first pass of this close said the feature had *never* been
exercised against live repository state. That is no longer true, and it is also
not yet true that the feature has been shown to work. The precise state:

- **Selection — proven against live state.** A read-only probe run in this
  session built a real `AgentSnapshot` of this repository (36 open issues, 1
  open PR, 63 feature folders, 0 unreadable), called `advertise()` on all six
  registered providers, and asked `_select_next` what it would choose. All six
  advertised without raising — answered-escalations 0, bugs 10, features 1,
  triage 8, findings-diagnose 0, findings-autofix 0, 19 items — and the
  selector returned `("execute", BugsProvider, bug-1413)`, which is correct
  under this repository's `rules.bugs.preempt: true`. Command, output and
  caveats are in § "What this close proved against live state".
- **Execution — still unproven. No item was executed.** The probe stopped at
  the selection boundary by construction: nothing was dispatched, no driver was
  invoked, no `gh` write was issued, nothing was committed. So
  `provider.execute()`, `advance_feature`, every halt classification and every
  escalation path remain proven only against fixture feature folders and an
  injected runner. **No `specfuse-agent run` has executed against live
  repository state at any point in gates 1, 2, 3 or 4**, and that sentence is
  still the one an operator should read before deciding this feature works.

**On the execution half this is "not proven", not "disproven"** — nothing
observed across four gates suggests `execute` is broken. The distinction matters
because the two readings lead to opposite next actions: "disproven" would mean
fix something, "not proven" means run it once, under caps, and read the result.
**On the selection half the earlier phrasing was too generous**, and the re-arm
is the correction: something *was* broken there, nobody had looked, and the
first look found it.

**One thing the re-arm did disprove, and it is the reason the re-arm exists.**
Between the two passes of this close, issue #1746 was found and fixed
(`21fdb40`): `state.read_feature_summaries` called `.is_dir()` on its argument
while `FeatureProvider`'s no-argument fallback was the *string*
`".specfuse/features"`, so the **default invocation** — a bare
`specfuse-agent run` with no `--features-root` — raised `AttributeError` from
inside `FeatureProvider.advertise`. `_select_next` iterates every provider's
`advertise` with no per-provider guard, so that one type error ended the entire
run, taking the healthy bug, triage and findings providers down with it. The
shipped default path was broken and every test injected a fixture `Path`, so
nothing caught it. It is fixed, the reader now normalises at the boundary, and
`tests/test_agent_default_features_root.py` (8 tests) exercises the default
rather than a supplied value. The probe above is the first evidence that the
fixed path holds outside a fixture.

Two standing findings belong in the same headline, because both are properties
of the shipped code rather than of the test environment:

1. **`reconcile` was called by six providers across four gates and did nothing
   every time.** Every implementation is `return None` —
   `providers/answers.py:219`, `bugs.py:128`, `triage.py:173`,
   `findings_diagnose.py:180`, `findings_autofix.py:225`, `feature.py:334`.
   All six re-verified in this session. The call site is real (`run.py:332`,
   executed for every item), so this is
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
inherited from a producing WU's self-report **and nothing inherited from this
close's own previous pass**. That last clause is the reason the re-arm was
worth its cost: the tree moved by one commit (`21fdb40`, the #1746 fix) after
the first pass recorded its evidence, and `--recheck-verdict` re-reads the
verdict field rather than re-verifying anything. Every row below was observed in
*this* session.

| Command | Result |
|---|---|
| `bash scripts/smoke-test.sh` (the full `code` gate set, all 16 gates derived from `.specfuse/verification.yml`) | **exit 0** — `smoke test: OK` |
| ↳ `tests` gate: `python3 -m unittest discover -s tests -v -b` | **3054 tests, OK (skipped=1)**, 119.5s |
| ↳ `lint` gate: `ruff check specfuse .specfuse/scripts tests scripts` | `All checks passed!` |
| ↳ `security` gate: `bandit -r specfuse .specfuse/scripts -ll` | `No issues identified.` (0 medium, 0 high; 0 `#nosec` lines skipped) |
| ↳ `coverage` gate: `coverage run --source=specfuse … && coverage report --fail-under=90` | `TOTAL 10289 673 93%` — above the 90% floor |
| ↳ the remaining 12 gates (leak-scan, agent-policy-example-lint, event-type, roadmap-link, arm-sweep, monitoring-example-lint, and the six `bats` suites) | all green; `roadmap-link-gate` printed the same 3 non-failing WARNs as the previous pass |
| `python3 -m unittest tests.test_agent_queue_read -b` | **exit 0**, 19 tests, OK |
| `python3 -m unittest tests.test_agent_driver_invoke -b` | **exit 0**, 16 tests, OK |
| `python3 -m unittest tests.test_agent_provider_feature -b` | **exit 0**, 19 tests, OK |
| `python3 -m unittest tests.test_agent_default_features_root -b` (the #1746 regression module, new since the previous pass) | **exit 0**, 8 tests, OK |

The three gate-4 modules together: **54 tests, OK**; with the #1746 regression
module, **62**. The suite total moved 3046 → **3054**, and the eight new tests
are exactly that module — the only test-surface change between the two passes.
The full-suite run is the feature-level re-run and is **not** carried forward to
any future close attempt.

All 22 of `GATE-04-CRITERIA.md`'s entries are `kind: narrow` — a scoped nodeid,
a symbol-existence import, or a structural assert — and all 22 are recorded
`state: pass` at `attempt: 1`, where they were individually re-run. This attempt
carried them forward rather than re-running them per criterion, which is what
`narrow` means and what the re-verification worklist directed (22 carried, 0
requiring re-verification). They are not stale on that account: every one of the
22 scoped oracles is a subset of a module this session did re-run in full —
`tests.test_agent_queue_read`, `tests.test_agent_driver_invoke`,
`tests.test_agent_provider_feature`, 54 tests, all OK — so no carried-forward
green rests on a module that went unexercised here.

**No gate-4 criterion carries a `broad` oracle**, which is a statement about
this gate rather than an omission: no acceptance criterion here names the full
suite as its proof. The full suite still ran, as the feature-level oracle above,
and `close-discipline.md` §5 is explicit that the feature-level re-run is never
carried forward — it re-ran on this attempt too.

### What this close proved against live state

**Selection, end to end, against this repository. Not execution.** Two probes,
both run in this session, both read-only. The second is new at the re-arm and is
the larger of the two.

**Probe 1 — T12's readers, pointed at this repository's own files:**

```
resolve_wip_limit('.specfuse/agent-policy.yml')                     -> 1
resolve_gate_review('.specfuse/agent-policy.yml', 'FEAT-2026-0049') -> 'human'
read_feature_summaries('.specfuse/features')                        -> 63 summaries, 0 unreadable
classify_queue_entry('FEAT-2026-0049', …)                           -> workable
select_workable(('FEAT-2026-0049',), …, wip_limit=1)                -> (('FEAT-2026-0049',), ())
```

So `rules.features.wip_limit` and `rules.features.gate_review` — validated by
`agent_policy.py` since FEAT-2026-0044 and read by no shipped code until T12 —
have now been read from an operator-authored policy file, and the classifier has
been run over 63 real feature folders rather than fixtures.

**Probe 2 — the whole selection path, all six providers, one real snapshot.**
`gather_snapshot` with the shipped default runner against `specfuse/loop`, then
`advertise()` on every provider `default_providers(repo=…)` returns, then
`_select_next`. Observed:

```
providers: AnsweredEscalationProvider BugsProvider FeatureProvider
           TriageProvider FindingsDiagnoseProvider FindingsAutofixProvider
snapshot:  queue=('FEAT-2026-0049',)  issues=36 (no error)  prs=1 (no error)
           features=63  features_errors={}
advertise: AnsweredEscalationProvider 0
           BugsProvider              10   (bug-1413 the highest-ranked)
           FeatureProvider            1   (feature-FEAT-2026-0049-g4, queue_key=FEAT-2026-0049)
           TriageProvider             8   (triage-1746 first)
           FindingsDiagnoseProvider   0
           FindingsAutofixProvider    0
                                     19 items, no provider raised
rules.bugs.preempt: True
_select_next -> ("execute", BugsProvider, bug-1413)
```

Three things this establishes that no fixture test did:

1. **The bare-invocation path works.** `default_providers` was built with no
   `features_root`, which is exactly what `main()` constructs when
   `--features-root` is omitted — the path that raised `AttributeError` before
   `21fdb40`. Every provider advertised.
2. **The snapshot's `gh` reads work against a real repository.** 36 issues and 1
   PR came back with `issues_error`/`prs_error` both `None`; the bug and triage
   providers turned that into 10 and 8 real items keyed to live issue numbers.
3. **Ranking is right, and it does not favour this feature.** `_select_next`
   chose a bug, not the feature — correct under `rules.bugs.preempt: true`, and
   worth stating because it changes what a live trial would exercise: with ten
   open bug items ahead of it, `FeatureProvider.execute` is eleventh in line in
   *this* repository. Group D's re-run condition is sharpened accordingly below.

**What neither probe touched: `execute`.** No `provider.execute()` was called,
no driver was invoked, no write or mutating `gh` call was issued, nothing was
committed. This is selection evidence only, and stating it as anything more
would be the overstatement the re-arm brief warned against. It also observes
rather than argues the hazard `GATE-04-REVIEW.md` § "Risks to weigh before
arming" named: the live queue top is this feature, so a real run here — once the
bug lane drained — would invoke the driver on the feature it is being built
inside.

### Findings this gate produced

Five. One is a defect in gate 4's shipped behaviour that has since been fixed
(#1746), two are corrections to the record, one is a driver defect this close
can see and is forbidden to fix, and one is a lesson about this close's own
first pass.

0. **Gate 4 did ship a defect, and it was in the default invocation: #1746.**
   Recorded here as a finding rather than repaired, per this WU's escalation
   trigger — the fix landed on the branch as `21fdb40` between this close's two
   passes and is not this session's work. `FeatureProvider.__init__` falls back
   to the string `".specfuse/features"` when `features_root` is `None`, and
   `state.read_feature_summaries` called `.is_dir()` on whatever it was handed;
   the shipped default therefore raised `AttributeError: 'str' object has no
   attribute 'is_dir'` from inside `advertise`. Blast radius beyond the one
   provider: `_select_next` (`run.py:192`) iterates `provider.advertise` with no
   per-provider `try`, so one provider's type error propagated out of selection
   and ended the entire run — the bug, triage and findings providers were all
   working and all lost. **The reason no test caught it is a fixture pattern
   worth naming**: every one of gate 4's 54 tests passes `features_root=` a
   `Path` built in a temp directory, so the shipped default was the one input
   never supplied. The fix normalises at the boundary
   (`features_root = Path(features_root)`), and
   `tests/test_agent_default_features_root.py` — 8 tests — deliberately
   exercises the *default* rather than a supplied value, including a
   `default_providers()`-wide advertise sweep and a `_select_next` survival
   test. **Second-order finding, not fixed and not in this close's scope:** the
   un-guarded `advertise` loop in `_select_next` is still un-guarded. #1746 was
   fixed at the reader; a future provider that raises for a different reason
   will still take the whole run down with it. `run_agent` has a per-provider
   guard around `execute()` and none around `advertise()`.

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
4. **This close's own first pass ran a live probe and still missed #1746,
   because the probe called the leaf functions and not the entry path.** The
   first pass proved `resolve_wip_limit`, `resolve_gate_review`,
   `read_feature_summaries`, `classify_queue_entry` and `select_workable`
   against this repository — and separately proved that
   `default_providers(repo=…)` *constructs* six providers. It never called
   `advertise()` on any of them. #1746 lives precisely in the gap between
   construction and advertise, so a live probe that looked thorough was blind to
   the one live defect present in the tree it was probing. The second pass's
   probe closed that gap by driving the same path `main()` drives. Recorded as a
   finding rather than as an apology: it is a repeatable mistake, and it is the
   substance of one of the lessons staged below.

## Cost analysis

Every figure recomputed from `events.jsonl` `attempt_outcome` payloads in this
session — none estimated, and none carried over from this close's previous
pass, which read a file that did not yet contain its own row. No row was
missing: the escalation trigger about `events.jsonl` rows lost between a squash
and the next bookkeeping commit (#1024) did **not** fire, and every work unit in
all four gates has both its `task_started` and its
`attempt_outcome`/`task_completed` rows present.

| Gate | Planned (sum of WU `planned_cost_usd`) | Actual | `cost_budget_usd` | Actual as % of budget |
|---|---|---|---|---|
| 1 | $29.50 | **$13.19** | $36.00 | 36.6% |
| 2 | $39.50 | **$14.94** | $45.50 | 32.8% |
| 3 | $31.00 | **$23.73** | $38.50 | 61.6% |
| 4 | $23.00 | **$14.30** | $29.50 | 48.5% |
| **feature** | **$123.00** | **$66.16** | **$149.50** | **44.3%** |

**Gate 4's number moved at the re-arm, and it moved a conclusion with it.** The
previous pass could not see its own cost — the driver writes a closing WU's
`attempt_outcome` row after the session ends — so it reported gate 4 at $4.47
and *predicted* it would "land near $9.47". The row now exists:
`FEAT-2026-0049/G4-CLOSE`, attempt 1, **$9.83**, 857.9s, passed. That is **1.97×
its $5.00 estimate and the most expensive single work unit in the feature** —
more than any implementation unit, more than any `plan-next`. Gate 4's actual is
therefore $14.30, not $4.47, and the feature's is $66.16, not $56.33. This
session's own cost is likewise not yet written and is not in any figure above;
at the same $9.83 the gate would land near $24.13 against its $29.50 budget,
still inside it but no longer comfortably.

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
cost **$0.00**. The five that actually ran cost **$44.14 — 66.7% of the
feature's entire $66.16 spend** — and every one of them overran its estimate, in
the opposite direction to every substantive unit:

| Closing WU | planned | actual | delta |
|---|---|---|---|
| `G1-PLAN` | $6.00 | $7.24 | **+21%** |
| `G2-PLAN` | $6.00 | $8.28 | **+38%** |
| `G3-CLOSE-INTERMEDIATE` | $4.50 | $7.02 | **+56%** |
| `G3-PLAN` | $6.00 | $11.77 | **+96%** |
| `G4-CLOSE` (pass 1; this re-arm not yet costed) | $5.00 | $9.83 | **+97%** |

All five ran `model: opus` / `effort: high`; all fourteen substantive units ran
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

**The re-arm is a third cost shape §5 does not model, and it should be named
rather than folded in.** It is not a retry — the first pass passed — and it is
not a first attempt. It is a *deliberate re-run bought to refresh evidence that
a subsequent commit made stale*, and it costs roughly a full close. Whether it
was worth ~$10 is a judgement the operator can now make on the record: it moved
one headline claim, added the whole-selection-path live probe, corrected gate
4's cost by $9.83, and surfaced a second-order finding about the un-guarded
`advertise` loop. The general lesson is smaller and cheaper than the price paid:
a close's evidence has an implicit "as of commit X", and nothing in the artifact
records which X.

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
driver-refused attempt, and — re-checked this session against the same file —
still no failed closing attempt: `G4-CLOSE` passed on attempt 1 and this
session's re-arm was an operator decision, not a retry after failure. Counting
it as a failure would misreport the one number this table exists to carry.

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
7. **The bare `specfuse-agent run` was broken on this branch and is fixed
   (#1746) — added to the enumeration at the re-arm, and it is the item a
   consumer most needs.** Items 1–6 were pre-populated by
   `GATE-04-REVIEW.md` from what the feature's WUs were drafted to build; this
   one landed as a bug fix on the branch (`21fdb40`) after that enumeration was
   written, and so appears in no gate document. It is consumer-visible in the
   strongest sense: without it the command's **default invocation** — no
   `--features-root` — raised `AttributeError: 'str' object has no attribute
   'is_dir'` and ended the whole run, including the five providers that were
   working. Two surfaces changed. `specfuse.agent.state.read_feature_summaries`
   now normalises its `features_root` argument, so it accepts a `str` or a
   `Path` and returns `((), {})` for an absent directory instead of raising —
   this is a public name as of T12 and the widening is a compatible one.
   `specfuse-agent run` with no flags now completes selection rather than
   crashing. Everything shipped in items 1–6 was, in practice, reachable only by
   passing `--features-root` until this landed.

## Hedged-verdict follow-up record

The terminal verdict is `met_locally`, **decided afresh in this session and not
inherited from this close's previous pass.** Every acceptance criterion of all
fourteen substantive work units is met and re-verified; what is unproven is the
feature-level claim that the command does its job when actually run. Per
`close-discipline.md` §2, one entry per criterion below, each with the condition
that would upgrade it.

**Why not `met`, on the new evidence.** The re-arm added real live-state
evidence — selection works end to end against this repository, and the default
invocation that was broken now holds. It did not add execution evidence, and
`met` is a claim that the feature was *shown to work*. AC7's escalation trigger
is explicit that `met` alongside "no `specfuse-agent run` has ever executed
against live state" is the combination to stop at. It still applies.

**Why not `partially_met`.** No criterion is unmet at the level it was written.
All 22 gate-4 criteria pass, and the one defect this feature shipped (#1746) was
found and fixed on the branch rather than left standing.

**Why the re-arm did not move the verdict, stated plainly so the operator is not
misled by the extra evidence.** The gap between `met_locally` and `met` was
never "does selection work" — it was "does an item execute." That gap is
untouched. What moved is confidence *within* `met_locally`: the hedge is now
better characterised, one real defect fewer sits behind it, and Group D's re-run
condition is sharper.

Four groups, and the `kind`s of the first three were decided by the closes that
met them rather than re-decided here. Because at least one entry is
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

**Still open, and carried forward at the re-arm.** The re-arm's read-only probe
is not this group's re-run condition, which names one real `specfuse-agent run`.
A probe that stops before `execute()` cannot discharge criteria about what
`execute()` does.

All 22 entries in `GATE-04-CRITERIA.md`, less the live-state subset recorded in
§ "What this close proved against live state" — which the re-arm *enlarged*:
beyond T12's readers and classifier, the whole selection path (`gather_snapshot`
→ six `advertise()` calls → `_select_next`) has now run against this
repository's real issues, PRs, policy file and 63 real feature folders. The
remainder — every halt classification in T13, every row of T14's halt→outcome
table, and every escalation path — was met against fixture feature folders under
a temporary directory and a runner that returns canned exit codes, stdout and
stderr.

- **why unverifiable here:** deliberately, and as a safety property rather than
  a limitation. A test that dispatched the real driver against a real feature
  in this repository would run the loop inside the loop, and this repository's
  own `queue:` top is this very feature. `GATE-04.md` § "What this gate
  deliberately does not prove" records the decision; T13's and T14's escalation
  triggers forbid working around it.
- **re-run condition (sharpened by the probe, and the sharpening matters):** one
  `specfuse-agent run` against a repository whose `queue:` top is a feature
  other than this one — under `--max-items 1` and a `--max-minutes` cap, which
  is what makes the trial cheap and bounded. **Add one condition the previous
  pass could not have known to add:** the trial repository must have **no
  higher-ranked bug work**, or `rules.bugs.preempt` must be `false`. The probe
  showed `_select_next` choosing `BugsProvider` over `FeatureProvider` on this
  repository's real state — correct behaviour, and it means a `--max-items 1`
  run here would spend its single item on a bug and exercise none of this
  group's criteria. A run that never reaches the feature provider is not the
  re-run condition however faithfully it is executed. With that condition met,
  one run exercises the console script, the lock, the caps, the snapshot, the
  ranking, the subprocess invocation, at least one halt classification and its
  escalation path, all at once.
- **kind:** `externally-verifiable-later`

## Lessons promoted (gate 4)

Same mechanism as gate 3's, unchanged: under `autonomy_default: auto` a closing
WU whose diff touches `.specfuse/LEARNINGS.md` fails
`assert_learnings_staged_under_auto`, so this gate's lessons are appended to
`LEARNINGS-pending.md` in this feature folder for a human to promote at PR
review. Gate 3's four are left in place, the first pass's three are left in
place, and the re-arm appends two more — the file now holds **nine**. This is
staging, not "nothing generalizes": the lessons do generalize, and the staging
file is where the mechanism puts them.

The re-arm's two are both about evidence rather than about the agent runner, and
both were paid for in this feature:

1. **A test suite that injects a fixture path for a parameter with a shipped
   default never exercises the default.** Every one of gate 4's 54 tests passed
   `features_root=<tmp Path>`; the string fallback that `main()` actually uses
   was the one input never supplied, and it crashed the whole run (#1746).
2. **A live probe that calls a module's leaf functions is not evidence about the
   entry path that calls them.** This close's first pass probed five readers and
   a constructor against live state, looked thorough, and was blind to a defect
   sitting between the constructor and the first method call.

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
of the full suite (**3054 tests, OK**, this session) and observed no regression
in any of them.

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

1. **Every gate-4 criterion less the live-state subset was met against fixtures
   and an injected runner** — Group D above,
   `kind: externally-verifiable-later`. Twenty-two criteria, all `pass`, none of
   them evidence that the command *executes* an item when run. The re-arm
   enlarged the live-state subset from T12's readers to the whole selection path
   — `gather_snapshot` → six `advertise()` calls → `_select_next`, against this
   repository's real state — but stopped there by construction. **Selection:
   verified against live state. Execution: not verified anywhere but a
   fixture.** That sentence is the whole of what this gate can honestly claim.
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
7. **`_select_next` still calls every provider's `advertise()` with no
   per-provider guard — added at the re-arm and not fixed here.** #1746 was
   fixed at the reader that raised, not at the loop that let one provider's
   exception end the run. `run_agent` wraps `provider.execute()` in a
   `try/except` that parks the item and continues (`run.py:325-326`); the
   `advertise` loop inside `_select_next` (`run.py:212`) and the
   `provider.reconcile()` call (`run.py:332`) have no equivalent. So the
   *shape* of the #1746 failure — one provider taking down five healthy ones —
   is still reachable by any future `advertise` that raises for any other
   reason. This close records it and does not repair it: it is a change to
   T04's gate-1 surface, outside this WU's bounds, and it wants a bug with its
   own branch and its own test.
8. **The `--max-tokens` and `reconcile` deferrals above are now four gates old
   and were not advanced by the re-arm.** Named again rather than dropped: a
   deferral that survives a re-arm unchanged is still a deferral, and the
   re-arm's extra evidence touched neither.

