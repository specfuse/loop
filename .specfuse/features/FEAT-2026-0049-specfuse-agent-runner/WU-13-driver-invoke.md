---
id: FEAT-2026-0049/T13
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.00
produces:
  - specfuse/agent/driver_invoke.py
  - tests/test_agent_driver_invoke.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.11.0
started_at: 2026-08-11T06:21:52.832062+00:00
duration_seconds: 734.653
cost_usd: 1.569455
input_tokens: 76
output_tokens: 23438
---

# T13 — `specfuse run` as a subprocess, and the closed set of halt classes

**Context.** `FEAT-2026-0049/T13`. This is the unit that carries the feature's
central design decision: the driver is invoked as a **subprocess**, never
imported and called in-process. `GATE-04.md` § "The constraint that must survive
to here" names the two live defects that make in-process invocation wrong —
#757 (a work unit that edits the driver cannot take effect for anything the same
process dispatches afterwards) and #1040 (console scripts resolving
`specfuse.loop` from site-packages rather than the working tree). Criterion 2
turns that constraint into something a test asserts rather than something a
reviewer remembers.

The unit ships nothing that decides *whether* to advance a feature — that is T12
and T14. It ships the invocation and the reading of what came back.

**What the driver already reports, and why no driver change is needed.** The
escalation trigger on `G3-PLAN` asked exactly this question, so the answer is
recorded rather than assumed. `specfuse.loop.loop.run` returns three exit codes,
and the code alone is ambiguous — `0` covers both "a gate advanced" and "the
feature is complete", `1` covers both "a work unit blocked" and "another driver
holds the lock". Every ambiguity resolves against state the agent can read
without any driver change:

| rc | Where it is returned | Disambiguated by |
|---|---|---|
| `0` | gate complete, awaiting review (`loop.py:7414`) | the gate's own `status` in `GATE-NN.md`, and `PLAN.md status` |
| `0` | all gates already `passed` (`loop.py:6096`) | `PLAN.md status` |
| `2` | the gate holds `draft` work units (`loop.py:6185`) | the exit code alone |
| `1` | a work unit blocked (`loop.py:7260`) | a `human_escalation` row appended to `events.jsonl` (`loop.py:6631, 6663, 7176, 7242`) |
| `1` | lock held (`:6109`), malformed `verification.yml` (`:6059`), bookkeeping commit rejected (`:7437`) | no `human_escalation` row; `stderr` carries the message |

So the classification below reads the exit code, the feature's gate and PLAN
frontmatter before and after the run, and the `events.jsonl` rows the run
appended. **Nothing here requires the driver to report something it does not
already report**, and no file under `specfuse/loop/` is edited.

**The driver command is a parameter, not a flag.** `build_invocation` defaults
to `("specfuse", "run")` per `GATE-04.md`, and takes the command as a keyword so
tests can inject one. No CLI flag is added — see `GATE-04-REVIEW.md` § "Decisions
taken here", D-1, which also records the consequence that matters in *this*
repository: `specfuse run` resolves `specfuse.loop` from the installed suite, not
from the working tree.

**Acceptance criteria.**

1. `tests/test_agent_driver_invoke.py::TestHaltClassification::test_awaiting_review_is_not_confused_with_feature_done`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Both states exit `0`, so this is the classification's load-bearing
   case. Run scoped:
   `python3 -m unittest tests.test_agent_driver_invoke.TestHaltClassification.test_awaiting_review_is_not_confused_with_feature_done`.
2. `specfuse/agent/driver_invoke.py` exposes
   `build_invocation(feature_id, *, command=("specfuse", "run"))` returning
   `["specfuse", "run", "--feature", <feature_id>]`, and the module **imports
   nothing from `specfuse.loop.loop`**. Two tests: one asserts the argv, and one
   structural test asserts the module's source contains neither `loop.run` nor
   `import specfuse.loop.loop` — the subprocess invariant, checked mechanically
   rather than trusted.
3. The same test passes after this WU's edits.
4. `classify_halt(...)` returns one of six exported constants —
   `HALT_ADVANCED`, `HALT_AWAITING_REVIEW`, `HALT_NOT_ARMED`, `HALT_BLOCKED`,
   `HALT_FEATURE_DONE`, `HALT_DRIVER_ERROR` — one test per row of this table,
   six tests:

   | rc | State after the run | Class |
   |---|---|---|
   | 0 | `PLAN.md status: done` | `HALT_FEATURE_DONE` |
   | 0 | every gate `passed` but PLAN not `done` | `HALT_AWAITING_REVIEW`, detail naming the withheld terminal flips |
   | 0 | the gate that was un-passed before the run is now `passed` | `HALT_ADVANCED` |
   | 0 | a gate reads `awaiting_review` | `HALT_AWAITING_REVIEW` |
   | 2 | any | `HALT_NOT_ARMED` |
   | 1 | the run appended a `human_escalation` row | `HALT_BLOCKED` |
   | 1 | it did not | `HALT_DRIVER_ERROR` |

   The all-gates-passed-but-PLAN-not-`done` row is `HALT_AWAITING_REVIEW` on
   purpose, not `HALT_FEATURE_DONE`: `loop.py:6089-6091` records that this
   combination means the terminal flips did not fire — a hedged verdict — and
   that the operator needs to see it rather than have it papered over.
5. `HALT_BLOCKED` carries the blocked work unit's id and the `reason` field from
   its `human_escalation` payload; `HALT_DRIVER_ERROR` carries the last lines of
   the subprocess's `stderr` rather than a guess. A test drives the lock-held
   message (`loop.py:6104-6108`) through as `stderr` and asserts it reaches the
   detail verbatim.
6. `advance_feature(runner, feature_id, *, features_root, command=...)` reads the
   feature's state and the `events.jsonl` line count before the call, issues
   **exactly one** subprocess through the injected runner, then reads both again
   and returns the classified halt. A test asserts the runner received exactly
   one argv and that it is `build_invocation`'s.
7. The module issues no `git` command, no `gh` command, and writes no file. A
   test asserts the injected runner sees only the driver invocation, and a
   structural test asserts the source contains no `"git"` and no `"gh"` literal.

**Do not touch.** `specfuse/loop/` entirely — the driver is invoked, never
imported and never edited; a needed change there is a plan change to escalate,
and it is also what `GATE-04.md`'s subprocess constraint forbids.
`specfuse/monitor/` entirely. `specfuse/agent/run.py`, `state.py`, `budget.py`,
`monitoring_read.py`, and every module under `specfuse/agent/providers/` — this
unit registers no provider and adds no CLI flag. `specfuse/agent/queue_read.py`
(T12's) — its readers are imported if useful, never edited. `WU-12`, `WU-14`, and
the modules they create. Any `.specfuse/features/` folder other than fixtures
this unit's tests create under a temporary directory — the tests must never
invoke a real driver against a real feature. The driver owns all git; this
session edits files only and runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol checks:
`python3 -c "from specfuse.agent.driver_invoke import build_invocation, classify_halt, advance_feature, HALT_ADVANCED, HALT_AWAITING_REVIEW, HALT_NOT_ARMED, HALT_BLOCKED, HALT_FEATURE_DONE, HALT_DRIVER_ERROR"`
and the subprocess-invariant grep:
`python3 -c "import pathlib,sys; s=pathlib.Path('specfuse/agent/driver_invoke.py').read_text(); sys.exit(0 if 'loop.run' not in s and 'specfuse.loop.loop' not in s else 1)"`.

**Escalation triggers.** If classifying any halt turns out to need a fact the
driver does not currently emit — a new exit code, a new event type, a machine
readable summary — **stop and name it precisely.** Changing the driver is outside
this feature's scope boundary (PLAN.md § "Scope boundary"), and it is a plan
change, not a gate-4 work unit; the table above is the evidence that it should
not be needed, so a case that escapes it is new information worth a block. If
running the real `specfuse run` binary from a test turns out to be the only way
to prove a row of criterion 4's table, stop rather than doing it: a test that
dispatches the driver against this repository would run the loop inside the loop.
If `build_invocation`'s default command cannot reach a driver at all in the test
environment, that is D-1's consequence surfacing, not a defect to work around —
report it rather than adding a fallback that imports the driver in-process.
