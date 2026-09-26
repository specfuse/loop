# Retrospective — FEAT-2026-0117 gate 1 close

## Measurements

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e -v -b`
(run fresh, this session, outside the sandbox — the sandbox denies
`~/.claude/session-env`, which `loop.run()` needs to create for each
dispatched session; the same gotcha recorded for this repo's own test suite
elsewhere). Result:

```
test_carried_forward_and_reverify_partition_and_persist ... ok
test_carry_forward_narrow_greens_false_resets_everything ... ok

Ran 2 tests in 1.657s

OK
```

carried forward: 19 criteria, re-measured: 0

Per the re-verification worklist this dispatch was seeded with
(`GATE-01-CRITERIA.md`, all `kind: narrow` / `state: pass` with a recorded
`oracle` and `attempt`), all 19 recorded criteria across T01, T02, T02H,
T02H2, T03, and T04 carry forward from the prior close attempt un-reset — none
were invalidated, since no diff since their `proved_at_sha` touched a path
in their `covers:`. Zero required re-verification this attempt.

This close's own cost_usd beside the first close's: the first close attempt
(2026-09-26T19:38:15–19:48:06, `attempt_outcome` in `events.jsonl`) cost
**$1.597012**, ended `blocked` (missing `attempt_outcome` for T02H, since
resolved — see the re-arm reason in this WU's frontmatter). This attempt's
own `cost_usd` is stamped into this WU's frontmatter by the driver only once
the attempt completes, so it cannot be quoted here from inside the attempt
that is producing it; the number to diff against $1.597012 is whatever the
driver records for this attempt in `events.jsonl` / this WU's frontmatter
after this report.

`GATE-01.md`'s `broad_run` (run once, prior to this close's dispatch,
2026-09-26T19:38:15Z, tree list ending `...:e3b0de29b81a6c8e0abeacb3898519b98014b9ef`):
`ok: true`, `failing: []`.

## Cost analysis

Per-WU reconciliation, `planned_cost_usd` (each WU's own frontmatter, as
logged in its `task_completed` event) against actual spend summed from every
`attempt_outcome` in `events.jsonl` for that WU:

| WU | planned_cost_usd | attempts | actual cost_usd (sum) | delta |
| --- | ---: | --- | ---: | ---: |
| T01 | 6.00 | 1 (passed) | 5.130320 | -0.869680 (-14.5%) |
| T02 | 5.00 | 1 (passed) | 1.915640 | -3.084360 (-61.7%) |
| T02H | 1.50 | 1 (passed) | 0.180382 | -1.319618 (-88.0%) |
| T02H2 | 1.50 | 1 (passed) | 0.166122 | -1.333878 (-88.9%) |
| T03 | 3.00 | 1 (passed) | 1.706513 | -1.293487 (-43.1%) |
| T04 | 3.00 | 2 (1 failed, 1 passed) | 1.141285 (0.448614 + 0.692671) | -1.858715 (-62.0%) |
| **substantive total** | **20.00** | — | **10.240262** | **-9.759738 (-48.8%)** |
| G1-CLOSE (this gate's close) | 5.00 | 1 so far (blocked) + this attempt in progress | 1.597012 so far | not final — see `## Measurements` |

T04's two attempts are the one off-plan event driving this section: attempt 1
failed at gate entry (`preexisting_gate_failure`, `tests` + `coverage` both
red) — misattributed to T04 at first because T04's own session was the one
running when the gate-entry probe fired, but the failing signature
(`failures=32,` / `no_gate_marker`) was a stale-fixture condition already on
the tree before T04 touched anything documentation-only; the operator's
`arm_predicate_evaluated` at 19:15:44 shows every arming class `clean` once
re-armed, and attempt 2 passed clean at $0.692671. No WU ran over its planned
budget; every substantive WU landed under plan, and the close itself is still
mid-reconciliation (see above) rather than over budget — its first attempt
spent $1.597012 of a $5.00 plan before blocking on an honest data gap, not a
cost overrun.

### Failure-class breakdown

- **T04, attempt 1 — `tests` / `coverage` (class: `tests` / `other`,
  `preexisting_gate_failure`).** Gate-entry probe found the baseline red
  before T04's own diff landed anything; the driver halted per
  `docs/methodology.md`'s "do NOT assume it predates the feature" posture.
  Re-armed with no code change (the failure was upstream of T04's scope);
  attempt 2 passed.
- **G1-CLOSE, attempt 1 — `blocked_human` (class: `agent_reported_blocked`).**
  The close session correctly refused to write `## Cost analysis` when
  `events.jsonl` carried no `attempt_outcome` for `FEAT-2026-0117/T02H`, a
  `done` WU — this WU's own escalation trigger. Root cause: an operator
  `git checkout -- .` mid-run discarded T02H's uncommitted events. Recovery:
  reconstructed T02H's `task_started` / `attempt_outcome` / `task_completed`
  events from the WU's own driver-stamped frontmatter (`cost_usd: 0.180382`,
  `duration_seconds: 35.798`, etc.), each event's payload marked
  `"restored": "..."` rather than silently backfilled as if it had always
  been there. No cache-token counts were recoverable for that WU's restored
  events (frontmatter does not carry them); this reconciliation states that
  gap rather than fabricating a number.

## What the loop did NOT verify

Both items are `PLAN.md`'s `## Post-merge checklist`, unchanged by this
close — observable only across repositories and over time
(`close-discipline.md` §2), filed as `specfuse:post-merge` issues at close:

1. **Criterion:** "Over the next ten features closed in this repo and the
   generator, for every gate closed more than once: the second close's
   `cost_usd` against the first's (baseline: roughly equal), and the count
   of carried versus re-measured criteria from `## Measurements`."
   **Reason not verified here:** this close is itself the first live
   instance to measure — there is no ten-feature sample yet, and the
   comparison is cross-feature, not something one gate's close can observe
   about itself.
   **Where it actually gets checked:** a future methodology review
   (the successor to `reviews/2026-09-26-impact-assessment/`) sampling
   closed gates across this repo and the generator repo, the same way prior
   reviews measured hedge/re-run rates.
2. **Criterion:** "Any judge finding that names a carried criterion (a
   carried green that should have been re-measured)."
   **Reason not verified here:** a judge finding is produced by the judge
   session dispatched *after* this close passes, reading this
   `## Measurements` section and the gate diff — this close cannot observe
   its own future judge's output.
   **Where it actually gets checked:** the judge session for this gate
   (immediately following this close), and thereafter any future gate's
   judge session wherever `carried_from_attempt` entries are in its bundle.

## Consumer-visible contract changes

n/a — no consumer-visible contract change. This feature changes driver-
internal close/re-arm/criteria-carry behavior (`loop.py`, `criteria_state.py`,
`judge.py`, `closing_requirements.py`, `lint_closing.py`) and the rules/docs
describing it; it adds no CLI flag, published schema, or API surface a
consumer depends on. `verification.yml`'s `defaults.carry_forward_narrow_greens`
is a project-config default, not a consumer-facing contract.
