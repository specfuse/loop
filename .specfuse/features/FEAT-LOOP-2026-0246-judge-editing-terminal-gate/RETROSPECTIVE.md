# Retrospective — FEAT-LOOP-2026-0246 gate 1 close

First and only close of gate 1 (single-gate feature, PLAN decision 7). Six implementation
units (T01–T06); this session re-measured the oracles fresh and wrote the close
deliverables.

## Measurements

All commands were run in this session from the repository root with the project venv,
exit codes read directly. HEAD was `4d501615eb0e284b3a953ee90cbf90a4b7541767` with this
close's own working-tree edits (`CHANGELOG.md`, this file, `LEARNINGS-pending.md`,
`GATE-01-CRITERIA.md`, the `verdict` field of `WU-90-gate-1-close.md`) uncommitted. This
session may not run git commits; the tree state is HEAD plus those edits.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_terminal_judge_editing_end_to_end -v -b`
(exit 0): `Ran 11 tests` / `OK`, every class running, none skipped:

```
PatchRestoresOriginals              1
FiresOnSingleGateJudgeEdit          1
CleanFeatureClosesUnchanged         1
AcknowledgedStopProceeds            1
NewPathRefires                      1
EveryAutonomyLevelStops             1
AutoClosePathStops                  2
BriefHasSixParts                    1
BriefShowsThePasteReadyAcknowledgement  1
DocsNoLongerRecommendReview         1
```

### No surviving skip

`grep -nE 'unittest\.skip|@skip|skipTest' tests/test_terminal_judge_editing_end_to_end.py`
prints nothing (exit 1). `grep -n skip` on the module reports one line, line 14, inside
the module docstring ("T01 owns the firing and clean-control classes; the other classes
are skipped"). It is prose: T01 created the module with the T02, T03 and T04 classes
skipped by owner name, and each owner removed its own. The verbose run above lists no
`skipped` marker for any of the eleven tests.

### The self-halt fired (close criterion 1)

`events.jsonl` (34 events), read directly:

| time (UTC) | correlation_id | event | what it shows |
| --- | --- | --- | --- |
| 12:37:49 | `FEAT-LOOP-2026-0246` | `terminal_judge_editing_evaluated` | `status: fired`, 11 hits across T01, T02 and T03 |
| 12:37:49 | `FEAT-LOOP-2026-0246/G1-CLOSE` | `human_escalation` | `reason: judge_editing_terminal`, `gate: 1`; `hits` include `FEAT-LOOP-2026-0246/T01 produces specfuse/loop/arm_eval.py` and `FEAT-LOOP-2026-0246/T01 produces specfuse/loop/loop.py`, plus `specfuse/loop/lint_plan.py`, the event schema and three `produces_driver_helper` declarations |
| 12:50:49 | `FEAT-LOOP-2026-0246` | `terminal_judge_editing_evaluated` | `status: clean`, "acknowledged by operator" for the five keys |
| 12:50:49 | `FEAT-LOOP-2026-0246` | `terminal_judge_editing_acknowledged` | `close_unit: FEAT-LOOP-2026-0246/G1-CLOSE`; `reason: "Reviewed the diff; additive stop, no existing guard weakened"` |

Both events are present, in that order, and the close unit's `started_at`
(12:50:49.76) follows the acknowledgement event (12:50:49.68). Criterion 1 is met.
The acknowledged `paths` are the five keys the brief printed
(`produces_driver_helper`, `specfuse/loop/arm_eval.py`,
`specfuse/loop/data/schemas/driver-event.schema.json`, `specfuse/loop/lint_plan.py`,
`specfuse/loop/loop.py`).

### Broad run (driver's, not re-run here)

The full `code` gate set is the driver's, once per gate. `events.jsonl` records four
`broad_run_result` events: 12:11:28 and 12:26:57 `ok: false` (see Failure-class
breakdown), then 12:37:49 and 12:50:49 `ok: true`, `failing: []`. The last one is on
the tree recorded in `GATE-01.md`'s `broad_run:` block.

### Per-criterion oracles (20 criteria, `GATE-01-CRITERIA.md`)

carried forward: 0 criteria, re-measured: 20

All twenty were `unverified` on entry. Each was run in this session as its own command
by one script; each now records its oracle command, `kind: narrow`, `state: pass`
and `proved_at_sha` `4d501615eb0e284b3a953ee90cbf90a4b7541767`, all exit 0.

| criterion | oracle |
| --- | --- |
| T01#1 | `unittest …FiresOnSingleGateJudgeEdit …CleanFeatureClosesUnchanged` |
| T01#2, T02#2, T06#1 | `unittest tests.test_arm_eval_terminal` (`Ran 27 tests` together with the lint and docs modules) |
| T01#3 | `unittest tests.test_arm_eval tests.test_arm_eval_wiring tests.test_lifecycle_integration` (`Ran 36 tests`) |
| T01#4 | `.specfuse/scripts/event_type_gate.py` (`ok: no validation errors across 86 events.jsonl file(s), 2663 event(s) checked`, which includes this feature's two new event types) and `unittest tests.test_driver_event_registry_covers_emitters` |
| T02#1 | `unittest …AcknowledgedStopProceeds …NewPathRefires` |
| T02#3 | `unittest tests.test_lint_judge_edit_acknowledged` |
| T02#4 | `.specfuse/scripts/lint_plan.py <feature dir>`: `OK — … structurally valid` (plus a WARN: PLAN `planned_cost_usd` 17.00 vs 19.00 of WU costs, because T05 and T06 were added after the baseline) |
| T03#1 | `unittest …EveryAutonomyLevelStops …AutoClosePathStops …BriefHasSixParts` |
| T03#2 | `grep -rln judge_editing_terminal specfuse --include=*.py` lists `loop.py` and `lint_plan.py`. `loop.py` has the halt-table row (4188), the brief renderer and its dispatch (4215, 4330) and the constant (4568); `lint_plan.py` has it only in a docstring (1391) naming the halt the field clears. No second renderer |
| T03#3 | `unittest tests.test_lifecycle_integration` |
| T04#1 | `unittest tests.test_judge_editing_terminal_docs …DocsNoLongerRecommendReview` |
| T04#2 | the three `cmp` pairs, exit 0 each |
| T04#3 | `grep -rn "the only checkpoint the change gets" docs plugins .specfuse/skills specfuse/loop/data` prints nothing, exit 1 |
| T05#1 | `unittest …PatchRestoresOriginals` |
| T05#2 | `unittest …EveryAutonomyLevelStops tests.test_verify_empty_gate_set tests.test_timeout_kill_portable tests.test_tiered_verification_e2e` (`Ran 15 tests`, one process) |
| T05#3 | the feature oracle, and the no-skip grep above |
| T06#2 | `unittest …BriefShowsThePasteReadyAcknowledgement` |
| T06#3 | the feature oracle with `tests.test_lifecycle_integration` |

The "fails on HEAD / fails before the change" halves of T01#1, T02#1–#3, T03#1, T04#1,
T05#1–#2 and T06#1–#2 are properties of the tree before each unit and cannot be
re-observed from here; each unit's own attempt recorded its red run (T06's, in
`PROGRESS.md`: "4 new tests errored"). This close re-ran only the green halves.

Also run: `tests.test_changelog_schema tests.test_changelog_append_only
tests.test_changelog_collection` (`Ran 38 tests`, OK) after the `CHANGELOG.md` edit;
`ruff check specfuse .specfuse/scripts tests scripts` (`All checks passed!`);
`tests.test_driver_event_registry_covers_emitters tests.test_event_gate_full_envelope`
(`Ran 6 tests`, OK). The close's `gate_set` is `plannext` (the `plan-lint` gate); the
`code` gates are the driver's broad run.

### Definition of done, clause by clause

| clause | proven by | result |
| --- | --- | --- |
| 1. a done substantive unit declaring a `JUDGE_PATHS` path (or a non-empty `produces_driver_helper`) halts before the close: close `blocked_human`, `human_escalation` `judge_editing_terminal` naming each unit and path, no terminal flip | `FiresOnSingleGateJudgeEdit.test_halts_before_the_close`; `tests.test_arm_eval_terminal` (judge-module path, universal path, driver-helper hit, `close`-type unit ignored, `pending` and `abandoned` ignored, last gate only); and this feature's own close, which fired on the real driver at 12:37:49 | proven |
| 2. no such unit: closes exactly as on HEAD | `CleanFeatureClosesUnchanged.test_closes_as_on_head`, the positive control to clause 1's fixture; `AutoClosePathStops.test_positive_control_without_judge_path_auto_closes` | proven |
| 3. an acknowledgement covering every hit, unit back at `pending`: re-run proceeds and emits the event with the reason; a hit outside it re-fires | `AcknowledgedStopProceeds.test_rerun_dispatches_close_and_records_reason`; `NewPathRefires.test_added_judge_path_halts_naming_only_the_new_path`; `tests.test_arm_eval_terminal` (full coverage clean, partial coverage fires naming only the uncovered, literal `produces_driver_helper` entry, no event on a feature with no hits); `tests.test_lint_judge_edit_acknowledged` (the field's shape, each bad case beside the valid one); and this feature's own 12:50:49 acknowledgement | proven |
| 4. clauses 1 and 3 hold under `auto`, `review` and `supervised`, on an auto-close-eligible gate and on a dispatched close | `EveryAutonomyLevelStops.test_each_level_halts_without_a_terminal_flip`; `AutoClosePathStops.test_halts_before_any_auto_close_decision` | proven for the halt at all three levels and on the auto-close path. The acknowledged re-run (clause 3) is exercised in `AcknowledgedStopProceeds` at one autonomy level; this feature's own acknowledgement ran under `auto`. See "What the loop did NOT verify" |
| 5. the brief has the six parts and states the clearing steps; no doc copy recommends `review` for a terminal-gate judge edit | `BriefHasSixParts.test_message_is_the_six_part_brief`; `BriefShowsThePasteReadyAcknowledgement.test_driver_helper_hit_names_the_literal_entry`; `DocsNoLongerRecommendReview.test_docs_name_the_terminal_stop_not_review`; `tests.test_judge_editing_terminal_docs`; the three `cmp` pairs; the "only checkpoint" grep | proven. The one remaining `review` mention (`docs/methodology.md`, "Tighten to `review` when the judge cannot do its job…") is about a judge that cannot grade the criteria, not about a judge edit; the sentence before it says `review` adds no terminal checkpoint |

## Cost analysis

Reconciled from `events.jsonl` `attempt_outcome` events and each unit's
`planned_cost_usd`. `PLAN.md` plans 17.00 (the baseline: T01–T04 at 12.00 plus the 5.00
close); T05 and T06 were added later at 1.00 each, so the unit plans sum to 19.00
(`lint_plan` WARNs on that 12% difference). `GATE-01.md` sets `cost_budget_usd: 20.00`.

| unit | planned (USD) | actual (USD) | attempts (outcomes) | duration (s) |
| --- | --- | --- | --- | --- |
| T01 | 4.00 | 1.0710 | 1 (passed) | 184.7 |
| T02 | 3.00 | 0.4040 | 1 (passed) | 115.9 |
| T03 | 3.00 | 0.5214 | 1 (passed) | 154.8 |
| T04 | 2.00 | 0.2902 | 1 (passed) | 117.9 |
| T05 | 1.00 | 0.1337 | 1 (passed) | 45.3 |
| T06 | 1.00 | not recorded | 1, run in the operator's session, not dispatched | — |
| T01–T06 | 14.00 | 2.4203 | 5 recorded | 618.5 |
| G1-CLOSE (this attempt) | 5.00 | not yet recorded | 1 | — |
| **recorded total** | 19.00 | **2.4203** | 5 recorded | 618.5 |

The five recorded attempts spent $2.42 (17.3% of the $14.00 planned for them, 12.1% of
`cost_budget_usd`). T06 has no `attempt_outcome` or `task_completed` event: it was
done by the operator in their own session after the halt ("fix it here",
`PROGRESS.md`), so its spend sits outside `events.jsonl` and is not estimated here.
This close's own attempt is written when the driver ends it, so it is not reconciled
and the total excludes it. The two failed broad runs and the one halt cost no
`attempt_outcome` spend (the broad run is the driver's, with no model session); the
arm predicate reads "projected spend $7.29 within 2.0x baseline planned total $17.00
(cap $34.00)".

**What the self-halt cost in operator wait.** The stop fired at 12:37:49 UTC. The
operator's acknowledgement commit is 12:45:48 and the driver re-ran at 12:50:49. That
is **7 min 59 s from halt to acknowledgement and 13 min 0 s from halt to the close being
dispatched**. Of the 13 minutes, about 6 min (12:37:49 to 12:43:47, the T06 commit)
was the operator finding that the brief's "write the paths" instruction would not
clear the two `produces_driver_helper` hits and fixing it, and 5 min was the driver's
own re-run (a new build pin at 12:45:51, then the broad run to 12:50:49). The stop's
dollar cost was $0.00 in driver spend. The wait was the point of the feature, and the
T06 share of it was a defect in the first brief (see below), not a cost of the stop.

### Failure-class breakdown

| class | unit / event | count | cost (USD) | what it was |
| --- | --- | --- | --- | --- |
| `tests` (`failures=14`) + `other` (`no_gate_marker`, `coverage`) | broad run 12:11:28 and again 12:26:57 | 2 | not charged to a unit | `EveryAutonomyLevelStops` calls `_stub_agent()` once per autonomy level and `_Base.tearDown` restored `self._patches` in forward order, so the last `setattr` left `loop.verify` stubbed for the rest of the suite and 14 tests in `test_verify_empty_gate_set`, `test_tiered_verification_e2e` and `test_timeout_kill_portable` failed. Each failure was `awaiting_review`; the second was the same signature after a re-run. Operator diagnosis, T05 (the patch helper restores the driver it found), third broad run green |
| `judge_editing_terminal` halt | G1-CLOSE 12:37:49 | 1 | $0.00 | expected (PLAN decision 8). The brief told the operator to list "the paths" but two of the eleven hits were `produces_driver_helper` declarations covered only by the literal key `produces_driver_helper`; an operator listing file paths would have re-fired the stop. Found by the operator, fixed by T06 |

The patch-restore leak is the "broad-run: pollution before sandbox" shape already in
the notes: tests that pass alone and fail in the full suite point at a leaked
monkeypatch first. No unit's narrow tier could see it, because every failing module sat
outside every unit's `produces:`.

## Consumer-visible contract changes

Enumerated across T01–T06 for acknowledgment; each is in `CHANGELOG.md` `Unreleased`
(`Added` ×1, `Changed` ×1, FEAT-LOOP-2026-0246).

- **Added — the `judge_editing_terminal` halt.** A terminal gate whose done substantive
  unit declares a `JUDGE_PATHS` path or a non-empty `produces_driver_helper` blocks its
  close unit and emits a `human_escalation` with reason `judge_editing_terminal` before
  the close is dispatched or auto-closed, at every `autonomy_default`.
- **Added — the `judge_edit_acknowledged: {paths, reason}` close-unit field**, the
  operator's way to clear it (write it, run `/unblock-wu`), and `specfuse lint`
  validation of the field (ERROR on a missing or empty `reason`, empty or non-list
  `paths`, or the field on a non-close unit).
- **Added — two driver event types** in `driver-event.schema.json`:
  `terminal_judge_editing_evaluated` and `terminal_judge_editing_acknowledged`.
- **Changed — for every consumer project:** a feature whose terminal gate declares
  `.specfuse/verification.yml`, `.specfuse/hooks/`, `.specfuse/rules/`,
  `.github/workflows/` or `pyproject.toml` in a unit's `produces:` now halts once before
  its close. The driver's own module and data entries of `JUDGE_PATHS` do not match in a
  consumer repository. This corrects the roadmap entry's earlier claim that projects
  without the driver source are unaffected (PLAN decision 5).
- **Changed — wording.** `/draft-feature`, `docs/methodology.md` and
  `docs/concepts/autonomy-stop-classes.md` (and their `data/` and `plugins/` copies) no
  longer recommend `review` as the safeguard for a terminal-gate judge edit.

Awaiting human acknowledgment of this list, per `close-discipline.md` §3.

## What the loop did NOT verify

1. **No real consumer-repo halt on a universal judge path.** Every observation of the
   five universal entries is a fixture repository built inside a test (the
   `.github/workflows/ci.yml` case in `tests.test_arm_eval_terminal`; the end-to-end
   module's fixtures use driver-module paths). The only real-driver halt is this feature's own,
   and it fired on driver-module paths. Nothing here shows that a consumer's real
   `.github/workflows/` or `.specfuse/verification.yml` edit halts, that the brief
   renders cleanly with its paths, or that its operator can clear it. Where checked:
   `PLAN.md`'s post-merge checklist, "One consumer-repo halt", after a loop release
   containing this feature: run one feature in a consumer repository whose terminal gate
   edits `.github/workflows/` or `.specfuse/verification.yml`, confirm the halt names
   the unit and path, and that `judge_edit_acknowledged` plus `/unblock-wu` lets the
   close run.
2. **Declared, not actual, paths.** The check reads each done unit's `produces:` and
   `produces_driver_helper`. A unit that edits a judge surface it did not declare is not
   caught, and nothing in this feature measures how often that happens (PLAN "Known
   limits"). Checking the gate's real diff was out of scope. Where checked: the judge,
   which is given the gate's diff, and the PR review; a future feature would have to
   add a diff-based check, and none is planned.
3. **`pyproject.toml` matches whole-file.** A dependency bump in a consumer project fires
   the stop. This is the arm class's v1 approximation, inherited (PLAN decision 5) and
   stated in the changelog; nothing measures the false-positive rate. Where checked: the
   first consumer to hit it.
4. **The acknowledged re-run was observed at one autonomy level.** The halt is proven at
   `auto`, `review` and `supervised`, on both close paths. `AcknowledgedStopProceeds` and
   this feature's own re-run both ran under `auto`. `arm_eval.py` does not read
   `autonomy_default` (`grep -n autonomy specfuse/loop/arm_eval.py` prints nothing), but no test shows the acknowledged path clearing under the other
   two. Where checked: the consumer-repo post-merge run, if that repository is not on
   `auto`.
5. **The operator-side steps are tested as file edits, not as `/unblock-wu`.** The tests
   write the field and set the close unit to `pending`, which is what `/unblock-wu` does
   ("the test writes the field and flips the close unit to `pending`"). The skill itself
   was run for real once, by the operator, at this feature's own close. Where checked: the
   post-merge run.
6. **The "fails on HEAD" halves of the red-first criteria** were recorded by each unit's
   attempt, not re-observed here (see Measurements).

## Documentation pass

`docs/methodology.md` §9, `docs/concepts/autonomy-stop-classes.md` §2 and
`/draft-feature` (`plugins/` and `.specfuse/` copies) were read against the shipped code:
each states that the stop applies at every autonomy level, is cleared by
`judge_edit_acknowledged` plus `/unblock-wu`, reaches consumer projects through the
universal entries, and reads declared paths only. `grep -rn "the only checkpoint the
change gets" docs plugins .specfuse/skills specfuse/loop/data` prints nothing, and the
three `cmp` pairs are identical, so the `data/` and `plugins/` copies match. No copy
still recommends `review` for a terminal-gate judge edit. The `review` mentions that
remain say it adds no terminal checkpoint, or concern a judge that cannot grade the
criteria.

## Retrospective

**What went well.** The dogfood worked as designed. The stop fired on this feature's own
close with the right hits at the right moment (before the close, $0.00), the brief let
the operator find the problem in it, and the acknowledgement cleared the next run with
the reason recorded. Every "closes unchanged" assertion has a firing control beside it
(`CleanFeatureClosesUnchanged` against `FiresOnSingleGateJudgeEdit`, the auto-close
positive control, the full/partial coverage pair). Five recorded attempts spent 17.3% of
plan, with no failed unit attempt.

**What didn't.** Two things, both caught by a person rather than the loop's own tests.
First, the oracle's own patch helper leaked a stub, which red the broad run twice and
cost two operator interventions before T05 fixed the restore order; the unit-level
narrow tier could not see it. Second, the first brief told the operator to list "the
paths" while the driver-helper hits needed a literal key, so a faithful operator would
have re-fired the stop; the operator found it from the gate-status review, and T06 did
the fix outside the loop's accounting, so its cost is unrecorded. PLAN decision 8's
expectation held, and criterion 1 exists because of it.

**Lessons.** Staged in `LEARNINGS-pending.md` (`autonomy_default: auto`, so this close
may not append to `.specfuse/LEARNINGS.md`): a test helper that patches module globals
per call must restore them in reverse order or from a saved original, and an operator
instruction in a halt brief must be checked by following it literally.

**Open follow-ups (not blockers).** The post-merge checklist item (`specfuse:post-merge`,
filed at close); a diff-based check for undeclared judge edits; a measured
false-positive rate for the whole-file `pyproject.toml` match.
