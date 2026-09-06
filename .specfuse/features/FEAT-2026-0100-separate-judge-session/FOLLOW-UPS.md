# Follow-ups

Filed by FEAT-2026-0100/G1-CLOSE for gate 1, one entry per failed criterion.

### `specfuse lint` over every feature folder reports zero ERROR

**Criterion, verbatim** (`WU-90-gate-1-close.md`, and `GATE-01.md` § Definition
of done bullet 7): *"`specfuse lint` reports ERROR on a `pending` close WU whose
body says `verdict: met`, and zero ERROR over every existing feature folder."*
The first half holds; the second does not.

**Evidence.** A sweep of `python3 -m specfuse.loop.lint_plan <dir>` over all 74
folders under `.specfuse/features/` holding a `PLAN.md`, run in this session:
**1 folder exits non-zero, 1 `ERROR:` line**. The line:

```
ERROR: .specfuse/features/FEAT-2026-0082-async-drafting-wiring/WU-90-gate-1-close.md: close WU body names a predecided verdict: 'the verdict is' — the judge writes the verdict in its own session; see PLAN.md § Escalation-predicate satisfiability.
```

The rule is correct and the input is genuinely bad. `FEAT-2026-0082`'s close WU
is `status: pending`, `attempts: 0` (the feature is `status: planned` and has
never been dispatched), and its body line 50 reads *"leg is missing, the answer
is **no**, and the verdict is hedged"* — a pre-decided verdict, in a shape
(`hedged`) that FEAT-2026-0085 retired. `PLAN.md` § Escalation-predicate
satisfiability asserted this close was `done` and therefore skipped; it is not.
The condition predates this gate: `git show
303f1d7:.specfuse/features/FEAT-2026-0082-async-drafting-wiring/WU-90-gate-1-close.md`
— T05's own commit — carries the same `status: pending` and the same sentence,
so the sweep would have failed on the tree T05 reported `done` on, against T05's
own fourth acceptance criterion and its `blocked` escalation trigger.

**Re-run condition.** Rewrite `FEAT-2026-0082`'s close WU body so it names what
to measure and not what to conclude — a whole-body review by whoever arms 0082,
not a phrase swap, because the same body also still describes a retired hedged
verdict. Then the sweep over all folders under `.specfuse/features/` reports
zero `ERROR` and this criterion is satisfied. Do not widen the rule's skip set.

### The judge's gate diff resolves to a re-probed baseline, not to gate entry

**Criterion, verbatim** (`GATE-01.md` § Definition of done bullet 1, in part): a
judge dispatch *"whose prompt contains the gate's definition of done, the
`GATE-NN-CRITERIA.md` entries, **the gate's diff**, and the close's
`## Measurements` section."* Demonstrated on a fixture; not true of the dispatch
this gate will actually make.

**Evidence.** `resolve_gate_start_sha` prefers `GATE-NN.md`'s `baseline.sha`,
documented as the commit *"the driver wrote at gate entry, before any unit was
dispatched."* On a gate that halts, the baseline probe re-runs on resume and
overwrites it. `GATE-01.md` carries `baseline.sha:
7f50a473b99f0483eb71a390bea995cf1a6af689`, `probed_at:
2026-09-06T13:26:04Z` — ten hours after T01 started and after three
`driver_staleness_detected` halts. Measured in this session:

- `git diff --stat 7f50a47..HEAD` — the range the judge gets — **1 file changed,
  2 insertions(+), 2 deletions(-)**, and the file is `GATE-01.md` itself.
- `git diff --stat 64dde90..HEAD` (merge-base with `main`) — the gate's real
  footprint — **34 files changed, 3677 insertions(+), 10 deletions(-)**.

Every feature that takes a driver-restart halt gets the degraded bundle; this
one predicted five such halts in `PLAN.md` § Notes and took three. The fixtures
could not surface it because `_write_feature` writes a baseline once and never
re-probes it.

**Re-run condition.** Either stop the baseline re-probe from overwriting a
gate's original entry sha (keep the first-probed value, or record the re-probe
alongside it), or make `resolve_gate_start_sha` prefer the earliest recorded
gate-entry sha over the latest probe. Satisfied when, on a gate that has taken
at least one `driver_staleness_detected` halt, the range `judge_close` reports
in the `judged` event's `diff_base` covers every commit the gate's units landed
— verifiable by comparing that range's `--stat` against the merge-base range on
a fixture gate whose baseline has been re-probed mid-gate.

### The judge's prompt is not excluded from the close's `## Retrospective` prose

**Criterion, verbatim** (`GATE-01.md` § Definition of done bullet 1, in part): a
judge dispatch whose prompt *"does not contain the close's `## Verdict` or
`## Retrospective` prose."* True of `## Verdict`; false of `## Retrospective`
whenever that section has subheadings, which is the shape every recent close in
this repository uses.

**Evidence.** `strip_forbidden_sections` opens a redacted run at a heading whose
first word is `verdict` or `retrospective` and closes it at the next heading of
*any* level — so a `###` child re-opens the stream exactly as a `##` sibling
does. Measured in this session by calling
`specfuse.loop.judge.strip_forbidden_sections` on this feature's
`RETROSPECTIVE.md` rendered as a `+`-prefixed diff hunk, the form in which it
reaches `build_judge_bundle` via `capture_gate_diff`, and counting surviving
non-blank lines per section:

- `## Verdict`, no subheadings: **0% of its non-blank lines survive** —
  correctly stripped.
- `## Retrospective`, with `###` subsections: **100% survive** — every line
  carried into the prompt.

Proportions rather than line counts because the close's own retrospective is
both the input to this measurement and a file the close edits; the counts move,
the proportions do not.

The prompt then instructs the judge *"Do not open `RETROSPECTIVE.md`. Its
closing sections carry the other session's own opinion of its work; reading them
is how a judge stops being one"* — while having already supplied those sections.
`TestJudgePromptEvidence` does not catch it: its fixture retrospective's
`## Verdict` has no subheadings, so the one section it asserts on is the one
shape the defect does not reach. `test_redaction_stops_at_the_next_ordinary_heading`
pins the sibling-`##` behaviour, which is correct and should stay.

**Re-run condition.** Make a redacted run end only at a heading of the *same or
shallower* level than the one that opened it (and at the existing diff
file/hunk boundaries), so `###` children of a forbidden `##` section stay
redacted while a following `##` sibling still ends it. Satisfied when
`strip_forbidden_sections` over a `## Retrospective` section carrying `###`
subsections leaves 0 of its non-blank lines, in both plain and `+`-prefixed diff
form, while the existing sibling-heading test still passes — and when
`TestJudgePromptEvidence`'s fixture retrospective is given a `###` subsection
under each forbidden heading so the assertion covers the shape real closes write.
