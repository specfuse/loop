---
gate: 1
status: passed
baseline:
  sha: dd81f062ae8df97f52bc3fe166fdff6c5ad09013
  probed_at: 2026-07-26T17:47:28.864419+00:00
  failing: []
---

# Gate 1 — the schema expresses per-target enumeration, and the validator enforces which check types may carry it

## Definition of done

- `monitoring.yml` can express per-subscription DLQ attribution and per-schedule
  heartbeat: a check carries an optional `targets` list, and each target carries the
  coordinates its check type needs.
- The validator enforces the axis distinction — `dlq` and `queue-stalled` **must** carry
  targets, `heartbeat` **may**, `error-logs` and `http-5xx` **must not**.
- Every shipped surface carrying a YAML example has been migrated, so the repo's own
  `monitoring-example-lint` gate and `tests/test_monitoring_fenced_blocks.py` are green
  against the new contract rather than the old one.
- `queue-stalled` exists as a check type, so a wedged consumer is no longer invisible to
  every check the schema can express (issue #247).
- FEAT-2026-0040's adapter interface has a machine-checkable answer to "do I enumerate
  per component or per target."
- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`), generalizable lessons are
  promoted to `.specfuse/LEARNINGS.md`, and docs plus roadmap status reflect what was
  actually built.
- Gate 2's work units are drafted, and `GATE-01-REVIEW.md` is written.

**What this gate deliberately does NOT prove.** `/derive-monitoring` still emits N
components for a deployable carrying N triggers. The schema will be able to express the
right answer before discovery is able to produce it. That is gate 2, and gate 1's close
must state it plainly rather than let the schema's correctness read as the feature's
completion.

The closing sequence (`close-intermediate` → `plan-next`) is part of every non-terminal
gate and is enforced by the linter. The driver runs the gate unattended, then stops here
for human review-and-arm: read the review artifact, accept or edit the drafted
next-gate work units, flip the accepted ones to `pending`, set this gate's status to
`passed`, and re-run.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** Gate 2 re-keys
  `discover_components`, which changes what the discovery reference implementation
  returns for existing fixtures. That is a behavioral default change, so it may **not**
  be armed on "mechanical, nothing design-open." Apply the re-key locally, run
  `python3 -m unittest discover -s tests -v` — the full oracle, not a subset — and paste
  the failure list into `GATE-01-REVIEW.md`. That list becomes the WU's enumerated test
  surface.
- **Escalation-predicate satisfiability (§2).** If any gate 2 WU asserts a "zero
  findings" predicate over a fixture it also authors, confirm the predicate is
  satisfiable on a correct input before arming — and confirm the fixture is not being
  used as evidence for the extractability claim it cannot support.
- **Flag-scope table (§3).** No behavior flag is expected in gate 2. If one appears,
  it needs the table.

## Reflection notes

**Armed 2026-07-26.** All four gate-2 drafts (`T05`–`T08`) accepted unmodified. The
review artifact was unusually good: the §4 runtime probe was genuinely run — twice, full
1473-test oracle, reverted, with the residual diffed — and its enumerated failure list is
pasted verbatim into `T06` so that WU does not rediscover its own breakage attempt by
attempt. §3's §10 enumeration accounts for every hit, including two symbols beyond the
required minimum (`_STACK_B_*`, `validate_monitoring`).

**What the probe found that the plan did not.** Two of gate 1's provider-neutrality
boundary tests pass on an *empty* component list — `len([]) == len([])` — so they were
satisfiable by a discovery function returning nothing. That is a pre-existing gate-1
defect, not something the re-key introduces. `T06` AC6 fixes it as a rider; kept there
rather than split into a hygiene WU because it is two assertions in a file `T06` already
edits.

**What I checked rather than took on faith.** The review's cost section reported
`G1-PLAN`'s own cost as unavailable — true when it was written, mid-session. It is in
`events.jsonl` now: **$16.44 across 2 attempts against a $5.00 estimate**. That makes
gate 1's actual **$38.39**, which already exceeds `PLAN.md`'s **$34.00 for the whole
feature** before gate 2 dispatches anything. I also verified `T05`'s flip is satisfiable
(`invariant` is absent from `_TARGETLESS_CHECK_TYPES`, and no shipped surface puts
`targets` on an `invariant` check) — the review argued the position well but never ran
that check.

**The overrun is not an estimating failure and should not be recorded as one.** Gate 1's
substantive WUs came in at $11.94 against $11.00 — +8.6%, four of five *under*. The two
closing WUs came in at $26.45 against $10.00, +165%. The entire gap is
`planning-discipline.md` §5's flat $5.00 planning floor, which FEAT-2026-0049 already
showed was low ($15.65 for its `plan-next`) and which was recorded as *provenance for*
the floor rather than as a reason to move it. Third feature to pay for it. Filed as issue
#260 and captured as
`[FEAT-2026-0069/GATE-1-ARM]` in `.specfuse/LEARNINGS.md` with both datasets and proposed
replacements ($12.00 `plan-next`, $8.00 `close`/`close-intermediate`), and `G2-CLOSE`
gained AC3 — a mandatory `## Planning-floor revision` section — so the lesson has to
produce an action rather than another observation.

**Open questions.** Accepted the review's recommendation on 1, 2, 3, 5, 6, 7. On 4 I
agreed with the *decision* (leave `PLAN.md` at $34.00; do not re-baseline a plan onto its
own overrun) but not with leaving it there — hence AC3 above.

**Housekeeping.** Sixteen files in this folder carried a stray `</content>` line, and
`PLAN.md` also a `</invoke>`. Mine: tool-call closing tags that leaked into `PLAN.md`
when I first wrote it, which every agent then copied from the files it read as templates.
Stripped before arming so gate 2's outputs do not inherit it.

**Deferred, not dropped.** `GATE-01-REVIEW.md` records that the driver's
`assert_gate_review_exists` computes `GATE-{N+1:02d}-REVIEW.md` while `WU.template.md`
and the gate template both promise `GATE-{N}-REVIEW.md`. Three features have now failed
an attempt on it (0026, 0027, this one). That is a scaffold bug, filed as issue #261 rather
than worked around again here.
