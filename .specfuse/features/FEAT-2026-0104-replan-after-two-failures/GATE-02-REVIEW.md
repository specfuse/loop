# Gate 2 review — read this before arming

Written by `FEAT-2026-0104/G1-PLAN`. This reviews the gate being **drafted**,
not the one being closed: gate 1's own account is `RETROSPECTIVE.md`.

## What gate 1 proved, and what it did not

Gate 1 built the re-plan trigger and shipped it green: a unit whose next
attempt would be its last is re-planned in place by a dispatched planning
session, the driver reloads it, the last attempt runs against the rewritten
body, and a `replan` event lands in the consumer `gate_eval` has waited for
since FEAT-2026-0018. Five units, five first-attempt passes.

What it did **not** prove is that any of that helps. No unit re-planned
during gate 1 — zero `replan` events in the feature's record and zero across
every `.specfuse/features/*/events.jsonl` in the repo. Every claim rests on
tests that stub the `claude -p` boundary. The feature is proven **runnable**,
not **useful**, and gate 2 is drafted on that footing.

## The probe

`GATE-01.md`'s escalation trigger required this session to either produce a
re-plan or halt. It produced one. A real `loop.run()` over a synthetic
single-unit feature (`max_attempts: 3`, `dispatch` stubbed to report
complete, `verify` stubbed red) printed:

```
   [16:30:44] attempt 1/3 … — fresh session
   FAIL attempt 1/3
   [16:30:44] attempt 2/3 … — fresh session
   RE-PLANNED FEAT-2026-8999/T01 after attempt 2/3 — next dispatch uses a rewritten body
   [16:30:44] attempt 3/3 … — fresh session
   FAIL attempt 3/3
   BLOCKED after 3 attempts — escalated (spinning_detected)
```

Event stream: `task_started, attempt_outcome, baseline_attribution,
attempt_outcome, baseline_attribution, replan, attempt_outcome,
baseline_attribution, human_escalation`, with the `replan` payload
`{"attempt": 2, "max_attempts": 3}`.

Three findings, all of which shaped the draft:

1. **The operator sees one line.** The `human_escalation` payload carries
   `reason`, `attempts` and `attempts_usage` — nothing readable. There is no
   brief on this path at all today, which is why gate 2's `feature_oracle` is
   red on a missing module rather than on a failing assertion.
2. **The automatic re-plan always precedes the brief.**
   `should_replan_instead_of_retry` fires at `attempt == max_attempts - 1`
   for every eligible unit, so any unit reaching `spinning_detected` has
   already been re-planned once and that re-planned attempt has already
   failed. The brief is reporting a spent remedy, not offering a fresh one.
   T06's part 1 and T07's option text are both written around this.
3. **The attempt-note record has a hole.** `persist_attempt_notes` writes one
   `work/<wu>/attempt-N.md` per buffered entry, and a re-planned attempt
   buffers twice under the same N; the transcript clobbers the failure
   evidence. Measured: `attempt-1.md` 757 bytes, `attempt-2.md` 59 bytes
   (transcript only), `attempt-3.md` 3491 bytes. T08 exists because of this.

Caveat, stated plainly: the probe stubs the model boundary. It proves the
trigger fires and the halt is reached; it says nothing about whether a real
planner's rewrite is any good.

## The decision this gate was told not to guess

Execute versus recommend is settled as **recommend only**, argued in
`GATE-02.md` § "The question gate 1 left open" against four named pieces of
gate-1 evidence: the zero re-plan count, the retrospective's own statement
that operator judgment is the only oracle for rewrite quality, the reverted
run's non-terminating re-plan loop, and `PLAN.md`'s existing deferral of
mid-flight `gate.refs` mutation "until re-plan has behaved on real spins."

Note the shape of the argument, because it matters at arming: three of the
four are *absence* evidence. Nothing measured says executing would be
harmful. What the record says is that nothing measured says it would be
safe, and the plan itself pre-committed to not lifting the deferral without
that measurement. If you disagree with reading absence that way, this is the
decision to overturn, and now is when to do it.

## What the drafted gate assumes

- That the six-part brief belongs on the **driver's** halt output and event
  payload, not on a filed GitHub issue. `emit_escalation` exists and files
  needs-human issues, but no `loop.py` escalation path calls it; wiring that
  in would be a larger change than this gate's definition of done asks for.
  If you want the brief on GitHub too, say so at arming — it is a fifth unit,
  not a widening of T06.
- That `escalation.validate_escalation_body` is an adequate oracle for "the
  six-part framing." It checks headings, two numbered options and the
  correlation marker. It cannot check that a part says anything useful; parts
  5 and 6 get their own assertions in T07 for that reason.
- That the scope of "a blocked_human escalation" is the four spin-out reasons
  in T07's flag-scope table, not all eleven. The gate's definition of done
  says "after a work unit escalates with `blocked_human`" without
  qualification, and the table narrows it. That narrowing is the draft's
  reading, not the plan's words.
- That `docs/methodology.md` is the right and only home for the operator-facing
  documentation (T09), reconciling with T05's paragraph rather than opening a
  third account.

## Push back on these before arming

1. **T08 is scope the gate's definition of done does not name.** It is a real
   defect, found by probe, on the brief's evidence path — and it is also the
   cheapest thing here to cut if you want gate 2 smaller. $1.50.
2. **The flag-scope table's *no* rows are judgement, not measurement.**
   `agent_reported_blocked` is the row most likely wrong: a session that
   named a boundary might well be a mis-sized unit. It is marked not-gated
   because its own `blocked_reason` is a better lead, which is an argument,
   not evidence.
3. **`format_human_unit_brief` will now be the odd one out.** It renders the
   six parts but carries no correlation marker, so it does not satisfy
   `validate_escalation_body` while the new brief will. Left alone
   deliberately — it belongs to FEAT-2026-0085 and this feature has no
   mandate over it — but the inconsistency is now visible and someone will
   file it.
4. **The estimate moved from $30.00 to $39.50** (`PLAN.md` § "The estimate
   was revised once"). Gate 1's plan left $5.74 for all of gate 2, which is
   less than a terminal `close`'s floor. If you want the original number
   held, gate 2 has to lose units, and T09 plus T08 is the only $3.00 that
   comes off without gutting the gate.
5. **Gate 1's under-spend is an artifact.** `RETROSPECTIVE.md` § "Cost
   analysis" shows the reverted first run's spend is unrecoverable from
   `events.jsonl`; the true cost of gate 1 was roughly $16–18, not the
   recorded $8.76. Do not arm gate 2 on the belief that this feature is
   running 40% under plan.

## Cross-repo contracts (`/authoring-work-units` §8)

| Value | Source | Checked |
|---|---|---|
| `ESCALATION_PART_HEADINGS` (the six part names) | `specfuse/loop/escalation.py:39` `_PART_HEADINGS`, re-exported at `loop.py:99` | yes — read at draft time |
| `validate_escalation_body` findings contract | `specfuse/loop/escalation.py:116` | yes — read at draft time |
| `<!-- specfuse:escalation id=… -->` marker | `specfuse/loop/escalation.py:_CORRELATION_MARKER_TEMPLATE` | yes — read at draft time |
| escalation `reason` vocabulary (11 values) | `grep -n '"reason": "' specfuse/loop/loop.py` | yes — enumerated at draft time |
| the command the brief names for the manual re-scope | `.specfuse/skills/` | **no — T07 must verify before reporting complete** |
