# FEAT-2026-0116 — the failure signature names the failing test

One gate, four implementation units and this close. T01 built the walking
skeleton: `extract_failing_tests` (per-runner: unittest, pytest, Maven
surefire, vitest/jest, dotnet, dart, bats) and `signature_from_failing_tests`,
wired into `parse_gate_failure_signature` for class `tests`, with
`attempt_outcome` gaining `failing_tests`. T01H was hygiene inserted after
gate 1's own broad run failed the `security` gate (bandit B324 on the sha1
truncation tail) — `usedforsecurity=False`, nothing else. T02 made
`detect_spinning_signature_repeat` compare failing sets and put the last
attempt's class/signature/failing set on every spinning-family escalation
payload. T03 added `replay_with_failing_sets` and its `--failing-sets` CLI
flag, and documented the field in `docs/methodology.md` §2. All four are
`done`; T01 escalated once (a real red-before-green, not a spin) before
passing on attempt 2.

## Measurements

All commands were run fresh in this close session, from the working tree at
gate 1's head (`b43afd5`). Per the dispatch contract, this session did not run
the full suite, coverage, or any `tier: broad` gate; the driver's
once-per-gate broad run is cited below by log, not re-run. Two commands that
drive `loop.run()` end to end (`test_attempt_outcome_emission` /
`test_spinning_rearm_gate` / `test_deterministic_refusal_repeat` and
`test_replay_spin`'s sibling module `test_spinning_repeat_same_failing_set`)
first failed under this session's default sandbox with `cannot create a
directory under '/Users/christian/.claude/session-env' (Operation not
permitted)` — a known sandbox artifact for this repo's own dispatch-simulating
tests, not a defect — and were re-run unsandboxed, both green.

### feature_oracle: PASS

`python3 -m unittest tests.test_failure_signature_names_the_test -v -b` — 18
tests, `OK`, exit 0. Covers both halves the gate's definition of done names:
the #3414 Maven pair gets two different signatures, neither the bare
`Tests` run-level word, each naming its own test; and the full per-runner
extractor (unittest, pytest, surefire including the lowercase-package shape
`_SUREFIRE_FAILING_TEST_RE` used to reject, vitest/jest, dotnet, dart, bats)
plus the full-log fallback when a report's tail carries only the summary.

### replay_spin --failing-sets over this repository's corpus

`python3 -m specfuse.loop.replay_spin --failing-sets .specfuse/features`
(the CLI globs `*/events.jsonl` under the given directory):

```
FEAT-2026-0040-failure-artifact-harvester
  FEAT-2026-0040/T10  attempt 2  fired historically -> unclassified (no recognisable test id in excerpt)
FEAT-2026-0053-auto-mode
  FEAT-2026-0053/T07  attempt 2  fired historically -> unclassified (no recognisable test id in excerpt)
FEAT-2026-0060-event-schema-registry
  FEAT-2026-0060/T01  attempt 2  fired historically -> unclassified (no recognisable test id in excerpt)
FEAT-2026-0069-monitoring-check-targets
  FEAT-2026-0069/T03  attempt 3  fired historically -> unclassified (no recognisable test id in excerpt)
FEAT-2026-0100-separate-judge-session
  FEAT-2026-0100/T03  attempt 2  fired historically -> unclassified (no recognisable test id in excerpt)
FEAT-2026-0103-keep-diff-on-guard-refusal
  FEAT-2026-0103/T04H  attempt 2  fired historically -> unclassified (no recognisable test id in excerpt)
FEAT-2026-0113-triage-severity
  FEAT-2026-0113/T03  attempt 2  fired historically -> would_fire
  FEAT-2026-0113/T04  attempt 2  fired historically -> would_fire
FEAT-2026-0115-blocked-with-a-fix-unit-continues
  FEAT-2026-0115/T02  attempt 2  fired historically -> unclassified (no recognisable test id in excerpt)
```

Historical `spinning_signature_repeat` escalations across every feature in
this repository: **9** (cross-checked directly against `human_escalation`
events with that reason: 9). Of those, **2 would still fire** under the new
failing-set rule (`FEAT-2026-0113/T03`, `FEAT-2026-0113/T04` — both genuine
same-test repeats), and **7 the replay could not classify** — old events
whose `failure_excerpt` was persisted before this feature existed and is
capped at 500 bytes, per the replay's own printed caveat: the full gate log
behind an old event is gone, so an unclassified escalation may simply have
had its failing test id truncated out of the excerpt rather than genuinely
lacking one. **0 would_not_fire** in this corpus — every historical repeat
either still repeats under the new rule or could not be re-derived at all;
none is shown here to have been a false spin the new rule would have caught,
which bounds what this measurement can claim (see also T02's own escalation
below, which predates `failing_tests` entirely and is not in this corpus
scan).

**Per-criterion re-verification, this attempt (14 required, 0 carried
forward).** Every criterion with a runnable oracle was re-run fresh and
passes; `GATE-01-CRITERIA.md` records each command, its `kind` (all `narrow`)
and `b43afd5` as `proved_at_sha`. The three "fails on HEAD before this unit's
edits" criteria (T01#1, T02#1, T03#1) are left `unverified` by design — a
red-before claim is self-reported by the session that made it green and
cannot be re-proved after the fact; each producing WU's own `produces:` names
a test module that did not exist before it, which is the structural
substitute. Full command list:

| Criterion | Command | Result |
|---|---|---|
| T01#2, T01#3 | `python3 -m unittest tests.test_failure_signature_names_the_test -v -b` | 18 tests, OK |
| T01#4 | `python3 -m unittest tests.test_attempt_outcome_emission tests.test_attempt_outcome_contract tests.test_surefire_run_level_signature tests.test_failure_signature_fail_prefix tests.test_failure_signature_skips_log_noise tests.test_maven_failure_excerpt -v -b` | 78 tests, OK |
| T01H#1 | `bandit -r specfuse .specfuse/scripts -ll` | "No issues identified.", 0 High/Medium, exit 0 |
| T01H#2 | `python3 -m unittest tests.test_failure_signature_names_the_test tests.test_spinning_repeat_same_failing_set -v -b` | 24 tests, OK (unsandboxed — see note above) |
| T02#2, T02#3 | `python3 -m unittest tests.test_spinning_repeat_same_failing_set -v -b` | 6 tests, OK (unsandboxed) |
| T02#4 | `python3 -m unittest tests.test_attempt_outcome_emission tests.test_spinning_rearm_gate tests.test_deterministic_refusal_repeat tests.test_failure_signature_names_the_test -v -b` | 98 tests, OK (unsandboxed) |
| T03#2 | `python3 -m unittest tests.test_replay_spin_failing_sets -v -b` | 4 tests, OK |
| T03#3 | `grep -c "failing_tests" docs/methodology.md` then `python3 -m unittest tests.test_scaffold_data_in_sync -v -b` | `4`; 4 tests, OK |
| T03#4 | `python3 -m unittest tests.test_replay_spin -v -b` | 13 tests, OK (unsandboxed) |

**Driver broad run, cited and not re-run.** `GATE-01.md`'s `broad_run:` block
records `ran_at: 2026-09-26T18:21:27Z`, `ok: true`, `failing: []`, on the tree
this gate ends at (matches this session's `b43afd5` HEAD). This is the
**second** broad run of this gate — the first (`ran_at: …17:24:07Z`, cited in
`GATE-01.md`'s history before this session started) failed the `security`
gate on the B324 finding T01H fixed; `human_escalation` records that as
`reason: broad_run_gate_failure`, `gate: 1`, `failing_gates: [{"gate":
"security", ...}]`, correlation_id the feature itself (not a WU) — see
§ Cost analysis for why this is this gate's off-plan signal.

## Consumer-visible contract changes

Four additions/changes, nothing removed or renamed.

1. **added: `failing_tests` on the `attempt_outcome` event payload** (list of
   test ids, default `[]`) — additive.
2. **added: `failure_class`, `failure_signature`, `failing_tests` on the
   `spinning_detected` and `spinning_signature_repeat` escalation payloads** —
   previously null/absent on roughly a third of the spinning-family corpus
   (§ Measurements' replay).
3. **changed: `detect_spinning_signature_repeat`'s repeat definition.** When
   both attempts' `failing_tests` are non-empty, a repeat is now failing-set
   equality; the previous `(class, signature)` comparison is the fallback
   only when a set could not be extracted from either attempt. This narrows
   which attempt pairs a spinning-family escalation fires on — the intended
   effect, and satisfiable per PLAN.md's escalation-predicate check (a
   strict subset of today's firing set).
4. **added: `--failing-sets` CLI flag on `python3 -m specfuse.loop.replay_spin`.**

Appended to `CHANGELOG.md`'s `Unreleased` section under `FEAT-2026-0116`.

## Cost analysis

Off-plan signal for gate 1: `reflection_required(feature_dir, 1)` returns
`True` via `_gate_has_eventful_history` — a `human_escalation` whose
`correlation_id` is the **feature**, not a work unit (`reason:
broad_run_gate_failure`, `gate: 1`, the first broad run failing the
`security` gate on T01's B324 finding). That escalation is what inserted
T01H and reopened the gate; `evaluate_off_plan_signal`'s own `reasons` list is
otherwise empty (no blocked-human event, no replan, no budget overrun —
`gate_total_cost=5.730958` against `gate_budget=35.0`).

Reconciling each WU's `planned_cost_usd` against its `attempt_outcome` events
in `events.jsonl`:

| WU | Planned | Actual (all attempts) | Delta | Attempts |
|---|---|---|---|---|
| T01 | $6.00 | $0.427586 (attempt 1, failed) + $2.429417 (attempt 2, passed) = **$2.856976** | −$3.143 (−52.4%) | 2 |
| T01H | $1.50 | $0.161311 | −$1.339 (−89.2%) | 1 |
| T02 | $5.00 | $1.858836 | −$3.141 (−62.8%) | 1 |
| T03 | $3.00 | $0.853835 | −$2.146 (−71.5%) | 1 |
| **Implementation total** | **$15.50** | **$5.730958** | **−$9.769 (−63.0%)** | 5 |
| G1-CLOSE (this unit) | $5.00 | not yet in `events.jsonl` (this session) | — | — |

Implementation came in 63.0% under the sum of the four implementation WUs'
own `planned_cost_usd`. Note `PLAN.md`'s feature-level `planned_cost_usd:
19.00` predates T01H (drafted before gate 1's broad run inserted the hygiene
unit); the WU-level sum above ($15.50 implementation + $5.00 close =
$20.50) is the more granular and more current figure, and is what this
section reconciles against.

T01's one non-passing attempt was not a spin: attempt 1 failed on
`tests.test_failure_signature_names_the_test` not existing yet (the module
this same unit's own criterion 1 required to be red first), attempt 2 wrote
it and turned the oracle green. This is the expected shape of a walking-
skeleton unit's first attempt, not evidence of anything to fix.

### Failure-class breakdown

`close-f`'s own guard (`assert_failure_class_breakdown_when_failures_present`)
does not require this section here — see the lesson below for why — but the
underlying data is real and worth recording plainly:

| WU | Attempt | Outcome | Failure class / signature |
|---|---|---|---|
| T01 | 1 | failed | `tests` — `ERROR: test_failure_signature_names_the_test (unittest.loader._FailedTest…)` — the module did not exist yet |
| T01 | 2 | passed | — |
| T01H | 1 | passed | — |
| T02 | 1 | passed | — |
| T03 | 1 | passed | — |

One non-passing attempt in the whole gate, and it is the expected first
attempt of a red-then-green walking skeleton, not a repeated failure.

## What the loop did NOT verify

`PLAN.md`'s `## Post-merge checklist` names two items, both observable only
across repositories and over time — neither is checkable from this gate's own
run.

1. **Escalation-rate and repeat-accuracy tracking.** *Criterion:* over the
   next ten features closed in this repo and the generator, count
   `human_escalation` events with reason `spinning_signature_repeat` and, for
   each, whether the two attempts' `failing_tests` were equal (baseline: 7
   such escalations on driver >= 0.19, at least one on a progressing unit —
   #3414). *Reason not verified here:* this gate's own dispatch produced zero
   `spinning_signature_repeat` escalations (T01's one failure re-armed by
   passing its next attempt, not by exhausting the budget), so there is
   nothing of this shape to measure from this gate's own history; the
   corpus-wide replay above answers a related but different question (what
   the new rule would have done to *past* escalations, not what it does to
   *future* ones). *Where it actually gets checked:* filed as a
   `specfuse:post-merge` tracked issue at this close, per
   `close-discipline.md` §2; the next ten features' own `events.jsonl` files,
   read after they close.
2. **`None`-payload gap closure.** *Criterion:* count spinning-family
   escalations whose payload lacks `failure_signature` (baseline: 12 of 25).
   *Reason not verified here:* the corpus replay above operates only on
   `spinning_signature_repeat` reconstructed from `failure_excerpt`, which
   says nothing about whether a *future* dispatch's escalation payload
   carries `failure_signature` — that is a property of code paths this
   feature edits, observable only once those paths run on new escalations.
   *Where it actually gets checked:* the same tracked `specfuse:post-merge`
   issue; a future spinning-family escalation's own payload, read after this
   feature merges.

## Lessons

Staged to `LEARNINGS-pending.md` (this feature runs `autonomy_default: auto`,
so `.specfuse/LEARNINGS.md` is not touched directly, per `close-i`). One
entry: a recurrence of an already-promoted lesson
(`[FEAT-2026-0016/G3-CLOSE]`, `[FEAT-2026-0101/G1-CLOSE]`) about the
`_gate_number_from_wu_id` / `summarize_attempt_failure_classes` gate-scope
bug, confirmed again on this feature's own events and shown here to also
starve this close's pre-created RETROSPECTIVE.md skeleton, not only the
`close-f` guard the earlier write-ups named.

## Verdict

This section is advisory only. The judge writes the verdict the terminal
flips read, from § Measurements, `GATE-01.md`'s definition of done,
`GATE-01-CRITERIA.md`'s per-criterion state, and the gate's diff — this
section is withheld from it.

`verdict: met` on this reading. The gate's definition of done is that a
`tests`-class failure signature comes from the sorted set of failing test ids
per runner (never a run-level summary), that set rides on `attempt_outcome`
as `failing_tests`, the repeat detector compares sets so a changed set is
progress, and every spinning-family escalation payload carries the last
attempt's class, signature and failing set — `feature_oracle` proves this
fresh, this session, 18/18 green. All four implementation units are `done`,
every criterion with a runnable oracle re-verifies `pass` at `b43afd5`, and
the driver's own second broad run (after T01H's hygiene fix) is green. The
corpus replay is recorded as measured, not as proof the feature "worked" on
this gate's own history — this gate's own dispatch never produced a
`spinning_signature_repeat` escalation to test the new rule against directly
(§ What the loop did NOT verify).
