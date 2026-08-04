---
gate: 2
status: open
cost_budget_usd: 29.50
---

# Gate 2 — the dial goes live, verified end to end

## Definition of done

Drafted by `FEAT-2026-0042/G1-PLAN` at gate 1's close, after reading gate 1's
`RETROSPECTIVE.md`. The intended shape recorded here at draft time survived that
read: nothing in the retrospective invalidated it, and the two work units it
sketched became three because the invocation surface and the wiring that uses it are
separately testable and separately reviewable.

Given a diagnosed finding on a component whose `autofix` dial is `"on"`, the system
can actually attempt a fix — the predicate fires, the attempt is durably recorded,
a headless `fix-bug` session launches, its outcome comes back through a closed
three-value set, and a failure is labelled — and that path has been exercised once
against a real repository, end to end, with every object it created cleaned up.

- Every implementation work unit in this gate is `done`:
  - **`T04`** — `specfuse/monitor/autofix_invoke.py`: builds the headless `fix-bug`
    invocation and classifies its result into T03's closed outcome set. Builds and
    classifies only; runs nothing.
  - **`T05`** — `specfuse/monitor/autofix_run.py`: the firing wiring. Reads the
    finding's diagnosis, calls T01's `decide`, records the attempt through T02's
    state **before** invoking, fires through T04, and labels the outcome. Carries the
    §3 flag-scope table. Its own entry point; deliberately not wired into the
    harvest cycle.
  - **`T06`** — the live end-to-end run: a scratch issue naming
    `FEAT-2026-0042/T06`, a trivial bug planted in a throwaway clone, a real fired
    run, a real branch and pull request, and cleanup in the same session. The only
    work unit in this feature carrying `unsandboxed: true`.
- The terminal close `G2-CLOSE` is `done`, carrying the feature's retrospective,
  lessons, documentation reconciliation, consumer-visible contract list, and terminal
  verdict.
- `GATE-02-REVIEW.md` exists and carries an explicit `open_questions` list.

**This gate is terminal.** Its closing shape is a single `close` work unit.

## The safety floor — carried forward, not re-decidable here

Auto-merge belongs to [FEAT-2026-0048](../../roadmap.md#feat-2026-0048) and is
**impossible in this feature**. No work unit in this gate may merge a pull request,
enable auto-merge, or push to a protected branch. The ceiling is an unwanted PR on a
branch. A drafted WU that widens this is an escalation to the operator, not a
judgement call for `G1-PLAN`.

That paragraph is restated verbatim in `WU-04-headless-fix-invoker.md`,
`WU-05-autofix-firing-wiring.md`, and `WU-06-live-end-to-end-run.md`, because a
constraint a session has to infer from a linked document is a constraint a session
can miss. T04 additionally requires the prohibition to be **literal text in the
prompt** the headless session reads, and T05's criterion 7 and T06's criterion 7 are
where it is mechanically checked rather than asserted.

## Arming discipline — re-answered by `G1-PLAN`, not inherited

Gate 1's answers to the `planning-discipline.md` checks do not carry into this gate.
All three were re-answered at drafting time; the evidence lives in
`GATE-02-REVIEW.md`.

- **§4 runtime probe** — run, and it found one real failure. Summary below.
- **§2 satisfiability** — re-answered per criterion against a real repository.
- **§3 flag-scope table** — newly applicable; `FEAT-2026-0042/T05` carries it.

**§4 runtime probe: run, and it found something.** Gate 1 answered "not applicable"
because nothing fired and no default changed. That answer does not carry. The probe
was run at drafting time — the `autofix` dial flipped to `"on"` in
`.specfuse/monitoring.yml.example`, the full oracle run (`python3 -m unittest
discover -s tests`, 2106 tests, not a subset), and the failure list recorded.
**One real failure**, absent from the identical baseline run:
`test_scaffold_data_in_sync.TestScaffoldDataInSync.test_package_data_matches_canonical`.
The command, the raw output, the reading, and what it changed about the drafts are in
`GATE-02-REVIEW.md`. The flip was reverted; the shipped default is `"off"` and the
probe left no diff.

**§2 satisfiability: re-answered against a real repository.** Gate 1 was satisfiable
by construction because nothing fired. Gate 2's criteria meet a real repository, so
each was checked against what a dispatched session can actually verify — including
that `gh` works only unsandboxed
(`LEARNINGS [FEAT-2026-0014/T01/gh-claudeP-broken]`, corrected 2026-08-03 by
`FEAT-2026-0041/G1-CLOSE`). The per-criterion answers are in `GATE-02-REVIEW.md`.
The one criterion that is **not** satisfiable by construction is T06's criterion 7
(a pull request exists), because it depends on the fired run reaching `completed`;
that is stated as such in the draft and routed to an escalation trigger rather than
hidden.

**§3 flag-scope table: now applicable.** `PLAN.md` recorded §3 as not applicable
because gate 1 adds no consumer for the `autofix` flag. Gate 2 adds the first one, so
`FEAT-2026-0042/T05` carries the table, and the arming read should check this gate's
headline claim ("the dial goes live") against it — in particular the row stating that
`specfuse-monitor run` is **not** wired to fire.

## Known limits, recorded so the close does not misread them

**Fix correctness is not verified by this gate and cannot be.** The same inherent
limit gate 1 recorded, and the same one `FEAT-2026-0041` recorded for diagnosis
quality. Every criterion in this gate asserts the *decision* is right or the
*mechanism* is sound; none asserts a generated patch is correct. A criterion of the
form "the automated fix produces a correct patch" is unsatisfiable and must not be
written. It belongs in the close's `## What the loop did NOT verify` as **inherent**,
not as a gap for a later feature to close with more tests.

**One live run is one live run.** T06 exercises the firing path once, against a
planted trivial bug, on one operator's machine. It is not evidence about behaviour on
an ephemeral runner, against a real finding, or under concurrency. The close should
say so rather than let a green gate read as production readiness.

**`refused` is a pass, not a failure.** `fix-bug`'s refusal paths are a second
guardrail behind T01's predicate, and gate 1's retrospective says so explicitly. If
T06's fired run returns `refused`, the mechanism claim holds and the pull-request
claim does not — the draft routes that to an honest block and a hedged verdict, not
to a re-planted easier bug.

## Cost budget

`cost_budget_usd: 29.50` — the **$21.50** sum of this gate's work-unit estimates
($4.00 T04 + $4.50 T05 + $8.00 T06 + $5.00 `G2-CLOSE`) plus one re-attempt of the
largest ($8.00, T06), per the defensive padding `planning-discipline.md` §5 and the
GATE template prescribe while the closing-WU retry defect (#260) is open. `G2-CLOSE`
sits at the §5 `close` floor of $5.00.

T06 at $8.00 is the estimate to watch and the one least anchored in this repo's
history: it is the only work unit here that launches a nested headless session and
waits for it, and gate 1's own calibration ran the other way — implementation work
landed at 48% of estimate across T01–T03. The number is deliberately not the median
of anything, because nothing comparable has been measured.

## Reflection notes

<Written by the human at review time.>
