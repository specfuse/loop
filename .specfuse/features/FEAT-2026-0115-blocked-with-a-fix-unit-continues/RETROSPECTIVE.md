# FEAT-2026-0115 — a block that names its fix unit continues the gate

One gate, four implementation units, one terminal close. T01 built the walking
skeleton: `parse_blocked_next` / `insert_fix_unit` / `resolve_fix_unit_insertion`
and the `agent_reported_blocked` branch that inserts a validated draft instead
of escalating. T02 wired the arm predicate's stop classes and the two caps
(`drift_caps`, `max_fix_units_per_unit`) into that path. T03 made an inserted
unit read as off-plan for auto-close and worded the escalation brief for a
refused insertion. T04 documented `blocked_next:`, the `fix_unit_inserted`
event, and the two `defaults` keys, canonical and mirror. All four are `done`;
T02 and T04 each escalated once before re-arming and passing.

## Measurements

All commands were run fresh in this close session, from the working tree at
gate 1's head (`1c96fee`). The dispatch-time sandbox denies writes under
`~/.claude/session-env`, which `loop.run()` probes at start, so every command
that drives `loop.run()` (the `feature_oracle` and the T01–T03 test modules)
was re-run unsandboxed — this is a known sandbox artifact for this repo's own
tests, not a defect. Per the dispatch contract, this session did not run the
full suite, coverage, or any `tier: broad` gate; the driver's once-per-gate
broad run is cited below by log, not re-run.

### feature_oracle: PASS

`python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b` — 3 tests, `OK`,
exit 0 (`test_blocked_with_valid_blocked_next_inserts_and_continues`,
`test_blocked_with_blocked_next_under_review_autonomy_escalates`,
`test_blocked_without_blocked_next_escalates_unchanged`).

**Per-criterion re-verification, this attempt (16 required, 0 carried
forward).** Every criterion with a runnable oracle was re-run fresh and passes;
`GATE-01-CRITERIA.md` records each command, its `kind` (all `narrow` — every
oracle here is a scoped test module or a scoped grep) and `1c96fee` as
`proved_at_sha`. The four "fails on HEAD before this unit's edits" criteria
(T01#1, T02#1, T03#1) are left `unverified` by design — a red-before claim is
self-reported by the session that made it green and cannot be re-proved after
the fact; each producing WU's own `produces:` names a file that did not exist
before it, which is the structural substitute. Full command list:

| Criterion | Command | Result |
|---|---|---|
| T01#2, T01#3 | `python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b` | 3 tests, OK |
| T01#4 | `python3 .specfuse/scripts/event_type_gate.py` | `ok: no validation errors across 79 events.jsonl file(s), 2384 event(s) checked` |
| T01#4 | `python3 -m unittest tests.test_spinout_brief_end_to_end tests.test_replan_end_to_end tests.test_attempt_outcome_contract -v -b` | 7 tests, OK |
| T02#2, T02#3 | `python3 -m unittest tests.test_fix_unit_insertion_refused -v -b` | 5 tests, OK |
| T02#4 | `python3 -m unittest tests.test_fix_unit_insertion_e2e tests.test_arm_eval tests.test_lint_plan_next_draft -v -b` | 39 tests, OK |
| T03#2, T03#3 | `python3 -m unittest tests.test_fix_unit_insertion_bookkeeping -v -b` | 5 tests, OK |
| T03#4 | `python3 -m unittest tests.test_gate_eval tests.test_spinout_brief_end_to_end tests.test_spinout_brief_replan_option -v -b` | 56 tests, OK |
| T04#1 | `grep -c "blocked_next" .specfuse/rules/result-contract.md docs/methodology.md plugins/specfuse/skills/authoring-work-units/SKILL.md .specfuse/skills/authoring-work-units/SKILL.md` | `3`, `1`, `1`, `1` |
| T04#2 | `grep -n "fix_unit_insertion\|max_fix_units_per_unit" .specfuse/verification.yml.example docs/methodology.md` | 6 matches, exit 0 |
| T04#3 | `bash scripts/sync-scaffold.sh && python3 -m unittest tests.test_scaffold_data_in_sync -v -b` | sync produced no diff (already in sync); 4 tests, OK |
| T04#4 | `python3 .specfuse/scripts/leak_scan.py --all` | `leak-scan: clean`, exit 0 |
| Closing lint (checkout) | `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` | `CLOSING-READY` (close-h, close-i are post-pass notes), exit 0 |
| Closing lint (CLI form) | `specfuse lint --closing <feature_dir>` | `CLOSING-READY`, run by the **installed** pipx build, which warns it is not measuring the checkout — the row above is authoritative | 0 |

**Driver broad run, cited and not re-run.** `GATE-01.md`'s `broad_run:` block
records `ran_at: 2026-09-26T17:24:07Z`, `ok: true`, `failing: []`, on the tree
this gate ends at.

### Human escalations and fix-unit insertions in this gate's own run

`events.jsonl` carries two `human_escalation` events, both reason
`spinning_signature_repeat` (T02) and `spinning_detected` (T04) — neither is
`agent_reported_blocked`. No `fix_unit_inserted` event appears. So, per the
close's own acceptance criterion 2: **no unit reported blocked in this gate.**
The mechanism this feature builds was never exercised by its own gate — every
occasion a unit stopped, it stopped on the attempt-budget/spin path, not by
reporting `status: blocked` with `blocked_next:`. The feature's own
`feature_oracle` above is what proves the mechanism; this gate's own dispatch
history proves nothing about it either way.

## Consumer-visible contract changes

Three additions, nothing removed or renamed.

1. **added: an optional `blocked_next:` field in a `blocked` RESULT block**
   (`.specfuse/rules/result-contract.md`, T01/T04) — `{kind: fix_unit, file, id}`
   naming a drafted fix unit. Absent, behaviour is unchanged.
2. **added: the `fix_unit_inserted` driver event**
   (`specfuse/loop/data/schemas/driver-event.schema.json`, T01), emitted when a
   validated draft is inserted ahead of the blocked unit.
3. **added: two `verification.yml` `defaults` keys** — `fix_unit_insertion`
   (default `true`) and `max_fix_units_per_unit` (default `2`) (T01/T02/T04).
   A `verification.yml` declaring neither keeps today's behaviour.

Appended to `CHANGELOG.md`'s `Unreleased` section under `FEAT-2026-0115`.

## Cost analysis

Off-plan signal for gate 1 (`gate_eval.evaluate_off_plan_signal`, computed
fresh in this session):

```
reasons=['blocked_human_in_chain: T02 escalated 2026-09-26',
         'blocked_human_in_chain: T04 escalated 2026-09-26']
gate_total_cost=8.335696 (see note below), gate_budget=40.0
replan_events=[], fix_unit_inserted_events=[]
```

`reflection_required(feature_dir, 1)` returns `True`, so this section and the
failure-class breakdown are written in full.

**`gate_eval`'s `per_wu_cost` under-reports every re-armed unit — this is the
already-known lesson at `[FEAT-2026-0058/G1-CLOSE/attempts-lifetime-exceeding-attempts-marks-a-re-armed-unit]`, confirmed again here.**
Its `per_wu_cost` reads only the surviving cycle's `cumulative_cost_usd`
(T02: `$3.124199`, T04: `$0.388923`), which drops the cost of every attempt
made before the re-arm. Reconciling instead from every `attempt_outcome` row
per correlation ID, across arming cycles:

| WU | Planned | Actual (all attempts, all cycles) | `gate_eval`'s figure | Delta vs planned | Attempts |
|---|---|---|---|---|---|
| T01 | $7.00 | $3.486723 | $3.486723 | −$3.513 (−50.2%) | 1 |
| T02 | $5.00 | $0.430279 + $0.828388 + $3.124199 = **$4.382866** | $3.124199 (under-reports by $1.259) | −$0.617 (−12.3%) | 3 (2 pre-rearm, 1 post) |
| T03 | $3.00 | $1.335851 | $1.335851 | −$1.664 (−55.5%) | 1 |
| T04 | $3.00 | $0.811698 + $1.774042 + $0.191160 + $0.388923 = **$3.165824** | $0.388923 (under-reports by $2.777) | +$0.166 (+5.5%) | 4 (3 pre-rearm, 1 post) |
| **Implementation total** | **$18.00** | **$12.371263** | $5.339896 (under-reports by $7.031) | **−$5.629 (−31.3%)** | 9 |
| G1-CLOSE (this unit) | $5.00 | not yet in `events.jsonl` | — | — | — |

Implementation came in 31.3% under plan even after counting every escalated
attempt's real spend. T02 and T04 both escalated once (`spinning_signature_repeat`,
`spinning_detected`) and both passed on the first attempt of their re-armed
cycle; neither needed a second re-arm.

### Failure-class breakdown

| WU | Attempt | Outcome | Failure class / signature |
|---|---|---|---|
| T01 | 1 | passed | — |
| T02 | 1 | failed | `tests` — `ERROR: test_fix_unit_insertion_refused (unittest.loader._FailedTest…)` |
| T02 | 2 | failed | `tests` — same signature as attempt 1 |
| T02 | 1 (post-rearm) | passed | — |
| T03 | 1 | passed | — |
| T04 | 1 | failed | `tests` — `test_distilled_file_is_under_its_own_sub_budget` |
| T04 | 2 | files_changed_mismatch | `SKILL.md` |
| T04 | 3 | produces_not_in_diff | `SKILL.md` |
| T04 | 1 (post-rearm) | passed | — |

**T02's identical signature was a false spin, per the unit's own recorded
re-arm reason, not a genuine two-strikes-same-defect.** Both pre-rearm
attempts reported `status: blocked` with a real, in-scope reason (the unit's
original scope forbade the edits its own design needed); `re_arm_history`
records that the driver's RESULT parser read the block-scalar value as
`complete` instead of `blocked` (open defect `#3436`), so the escalation
classifier saw two identical `tests` failures and called it a spin. The unit
was re-scoped (write-then-evaluate) and the override was granted because the
escalated signature was the parse defect, not the unit's design. This is
recorded as a durable lesson below, not fixed here — fixing `#3436` is outside
this close's produces/do-not-touch boundary.

**T04's three attempts are the already-known canonical-vs-synced-copy trap
recurring.** `produces:` named `.specfuse/skills/authoring-work-units/SKILL.md`,
which `scripts/sync-scaffold.sh` overwrites from the canonical
`plugins/specfuse/skills/authoring-work-units/SKILL.md` on every run — and T04's
own criterion 3 required running that sync. Each attempt's edit to the synced
copy was silently reverted by the sync it was itself required to run, so
verification saw the file unchanged (`files_changed_mismatch`, then
`produces_not_in_diff`) after real work had been done. `re_arm_history` names
the drafting error directly and adds the canonical path to `produces:`, after
which attempt 1 of the new cycle passed. This is the exact shape already
promoted at `[FEAT-2026-0110/G1]` ("editing the derived copy would have been
silently reverted by the next sync") — a recurrence, not a new lesson; see
below.

## What the loop did NOT verify

`PLAN.md`'s `## Post-merge checklist` names two items, both observable only
across repositories and over time — neither is checkable from this gate's own
run.

1. **Escalation-rate and insertion-share tracking.** *Criterion:* over the
   next ten features closed in this repo and the generator, count
   `human_escalation` events with `reason: agent_reported_blocked` per feature
   against the driver >= 0.19 baseline (1.21/feature here, 3.26 in the
   generator), count `fix_unit_inserted` events, and the share of blocks that
   carried `blocked_next:`. *Reason not verified here:* this gate's own run
   produced zero `agent_reported_blocked` escalations and zero insertions (see
   § Measurements) — a sample of one gate, mostly unrelated escalation
   classes, cannot estimate a rate. *Where it actually gets checked:* filed as
   a `specfuse:post-merge` tracked issue at this close, per
   `close-discipline.md` §2; the next ten features' own `events.jsonl` files,
   read after they close.
2. **Whether an inserted unit's work holds up.** *Criterion:* for every
   insertion, whether the terminal close or judge later found the inserted
   unit's work wanting (a finding naming its id). *Reason not verified here:*
   no insertion has ever happened outside this feature's own tests — the
   mechanism this gate proves has not been exercised in production yet, and
   the tests' synthetic drafts are not evidence about a real drafted fix's
   quality. *Where it actually gets checked:* the same tracked
   `specfuse:post-merge` issue; a future gate's close or judge naming an
   inserted unit's id in a finding is the check.

## Lessons

Staged to `LEARNINGS-pending.md` (this feature runs `autonomy_default: auto`,
so `.specfuse/LEARNINGS.md` is not touched directly, per `close-i`). Two
entries: one new, one a recurrence of an existing promoted lesson recorded as
evidence that the lesson has not yet changed authoring practice, not restaged
as new text.

## Verdict

This section is advisory only. The judge writes the verdict the terminal
flips read, from § Measurements, `GATE-01.md`'s definition of done,
`GATE-01-CRITERIA.md`'s per-criterion state, and the gate's diff — this
section is withheld from it.

`verdict: met` on this reading. The gate's definition of done is that a
blocked RESULT naming a valid `blocked_next:` is inserted and the gate
continues with no `human_escalation`, while a draft the stop classes refuse,
a third insertion, or a `review`-autonomy feature still escalates as today —
`feature_oracle` proves both halves end to end, fresh, this session. All four
implementation units are `done`, every criterion with a runnable oracle
re-verifies `pass` at `1c96fee`, and the driver's own broad run is green. The
mechanism was never exercised on this gate's own dispatch history (§
Measurements), which is recorded as a scope limit, not a gap in the
`feature_oracle`'s coverage.
