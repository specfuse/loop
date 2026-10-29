---
id: FEAT-2026-0246/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces:
  - tests/test_terminal_judge_editing_end_to_end.py
  - tests/test_arm_eval_terminal.py
  - specfuse/loop/arm_eval.py
  - specfuse/loop/loop.py
  - specfuse/loop/data/schemas/driver-event.schema.json
model: sonnet
effort: high
gate_set: code
oracle_env: macos_local
produces_driver_helper:
  - stop_for_terminal_judge_edit
driver_version: 0.30.0
started_at: 2026-10-29T11:56:33.750899+00:00
duration_seconds: 184.655
cost_usd: 1.071005
input_tokens: 58
output_tokens: 19157
---

# T01 — walking skeleton: a terminal judge edit halts before the close

**Objective.** The thinnest path end to end. A pure check reports which done
substantive units of the terminal gate declare a judge-surface path, and the driver
halts before the terminal close when it fires. This makes the oracle module exist and
turns Definition-of-done clauses 1 and 2 green; it does not build acknowledgement
(T02) or cover every autonomy level and close path (T03).

**Context.** `FEAT-2026-0246/T01`, the walking skeleton and the only unit permitted to
stub. Write `tests/test_terminal_judge_editing_end_to_end.py` **first**, driving the
real driver with only the agent stubbed, in the style of
`tests/test_lifecycle_integration.py`. Classes:

- `FiresOnSingleGateJudgeEdit` — a single-gate fixture feature, `autonomy_default:
  auto`, whose one implementation unit is done and declares `produces:
  [specfuse/loop/arm_eval.py]`: the run halts, the close unit is `blocked_human`, a
  `human_escalation` event has reason `judge_editing_terminal` and names the unit and
  path, the close agent was never dispatched, and the gate, roadmap row and `PLAN.md`
  are unchanged.
- `CleanFeatureClosesUnchanged` — the same fixture with `produces: [docs/x.md]`:
  the close runs and the terminal flips fire as on HEAD (the positive control's
  pair).
- `AcknowledgedStopProceeds`, `NewPathRefires` —
  `unittest.skip("owned by FEAT-2026-0246/T02")`.
- `EveryAutonomyLevelStops`, `AutoClosePathStops`, `BriefHasSixParts` —
  `unittest.skip("owned by FEAT-2026-0246/T03")`.
- `DocsNoLongerRecommendReview` — `unittest.skip("owned by FEAT-2026-0246/T04")`.

`arm_eval.py`: add `evaluate_terminal_judge_editing(feature_dir, gate_number) ->
ClassVerdict`. Pure: reads `PLAN.md` and the gate's unit files only. A unit counts
when its type is not in `gate_eval.NON_SUBSTANTIVE_TYPES` and its status is `done`;
it hits on each `produces:` path for which `_matches_judge_path` is true and on a
non-empty `produces_driver_helper`, with the same reason wording as class 2 (`"<id>
produces <path>"`). `fired` with the hits joined, else `clean`. Do not add it to
`CLASS_NAMES` — it is not a successor-arm class, and `would_arm` must not change.
Note that `arm_eval.py` must not import `loop.py`; importing the `gate_eval` constant
is allowed.

`loop.py`: immediately before the terminal auto-close branch (`maybe_auto_close_terminal`)
and the dispatched-close path for `wu.type == "close" and gate is gates[-1]`, call the
check once, through one new helper `stop_for_terminal_judge_edit` so both branches
share a single seat. On `fired`: set the close unit `blocked_human` through `backend.set_wu`,
emit `human_escalation` with reason `judge_editing_terminal` and the hit list, commit
bookkeeping, and halt the gate the way other per-unit escalations do. Stubbable here,
and only here: the brief text (T03 writes it — a one-line message is enough) and the
acknowledgement read (T02). On every terminal gate, `fired` or `clean`, emit
`terminal_judge_editing_evaluated` with the verdict, registered in
`driver-event.schema.json`.

**Acceptance criteria.**

1. `tests/test_terminal_judge_editing_end_to_end.py::FiresOnSingleGateJudgeEdit` fails
   on HEAD (no such check) and passes after; `::CleanFeatureClosesUnchanged` passes
   after; every other oracle class is skipped, each naming its owner.
2. `tests/test_arm_eval_terminal.py` covers: a judge-module path fires; a universal
   path (`.github/workflows/ci.yml`) fires; `specfuse/loop/data/docs/x.md` is clean
   (`JUDGE_DATA_PREFIXES` excludes `data/docs/`); a non-empty `produces_driver_helper`
   fires; a `close`-type unit producing a judge path is ignored; a `pending` or
   `abandoned` unit is ignored; a multi-gate fixture checks only the last gate's
   units.
3. `python3 -m unittest tests.test_arm_eval tests.test_arm_eval_wiring
   tests.test_lifecycle_integration -b` still passes — `evaluate_arm_predicate`,
   `CLASS_NAMES` and `would_arm` are unchanged.
4. A schema check accepts the new `terminal_judge_editing_evaluated` event (the
   existing driver-event schema test, or a new case in it).

**Do not touch.** `fire_terminal_flips`, `maybe_auto_close_terminal` and
`evaluate_auto_close` bodies (they are preceded, not modified). `JUDGE_PATHS` and
`_UNIVERSAL_JUDGE_PATHS` contents. Docs (T04).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_arm_eval tests.test_arm_eval_wiring tests.test_lifecycle_integration -b`.

**Escalation triggers.** If the terminal close is reached on a code path other than
the two named above (for example a resume that skips the in-loop branch), stop and
escalate with that path named — a third entry point means the stop needs a different
seat, which is a design decision.
