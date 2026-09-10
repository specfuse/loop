---
gate: 2
status: open
feature_oracle: "python3 -m unittest tests.test_spinout_brief_end_to_end -v -b"
---

# Gate 2 — a blocked_human escalation offers a re-plan

## Definition of done

After a work unit escalates with `blocked_human`, the operator-facing brief
presents re-planning the remaining gate as its default option, inside the
six-part framing `.specfuse/rules/operator-escalation.md` requires.

The `feature_oracle` above is the executable proof. It is **red today**:
`tests/test_spinout_brief_end_to_end.py` does not exist
(`python3 -m unittest tests.test_spinout_brief_end_to_end -v -b`, exit 1,
measured 2026-09-10 on `873e0ac`). It drives a real `loop.run()` to attempt
exhaustion — the same harness `tests/test_lazy_baseline_e2e.py` uses — and
asserts on what that run **prints and records**, never on a brief a test
composed itself. T06 is the tracer bullet that makes it runnable and green by
wiring the brief end to end; T07–T09 make each part correct.

Also required, as for every gate:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## The question gate 1 left open, now answered: **recommend, do not execute**

`GATE-01.md` deferred one decision to this draft — whether the brief's
re-plan option may **execute** the re-plan on the operator's yes, or only
recommend it and leave the flip manual. It is settled here as **recommend
only**. The brief names the re-scope it would make, names the command that
performs it, and changes nothing itself. Four pieces of gate-1 evidence
settle it, each cited so a reviewer can check the reasoning rather than the
conclusion:

1. **`RETROSPECTIVE.md` § "Did any unit in this gate re-plan?"** — zero
   `replan` events across the feature's whole record, and zero across every
   `.specfuse/features/*/events.jsonl` in the repo. The success rate of a
   re-planned unit is not low; it is **unmeasured, n=0**. Auto-executing a
   mechanism with no observed success rate is not a default, it is a guess
   with the operator's name on it.
2. **`RETROSPECTIVE.md` § "Deferred verification", the fourth bullet** — "the
   re-plan turn producing a genuinely better-scoped unit … Nothing in-loop
   can assert that a real planner's rewrite is *better*. Checked by operator
   judgment at the gate boundary on the first real re-plan." Operator
   judgment is the **only** oracle this feature has for rewrite quality. A
   yes given before the rewrite exists cannot be that judgment, so executing
   on it deletes the one check the feature ships with.
3. **`PLAN.md` § "Gate 1 was reverted once", defect 1** — the first
   implementation of the re-plan branch rewound the attempt counter and the
   unit loop stopped terminating; the hang masked two further defects and
   cost the entire first run of the gate (see `RETROSPECTIVE.md` § "Cost
   analysis": ~$16–18 to reach green, against $8.76 of surviving record).
   That is what an unattended re-plan loop does when it is wrong. Gate 1's
   fix bounds the blast radius to one unit's own attempt budget; a re-plan of
   the **remaining gate** would widen it again, unattended, on the strength
   of a yes typed before anything was written.
4. **`PLAN.md` § "Decisions taken at drafting" / § "Scope boundary"** —
   in-place re-scope was chosen over splitting because splitting mutates
   `gate.refs` mid-flight, and "deferred until re-plan has behaved on real
   spins." Re-planning the remaining gate *is* that mutation. Gate 1 produced
   no real spins, so the stated precondition for lifting the deferral was
   never met. Executing here would quietly overrule a deferral the plan made
   explicitly.

### What the probe added, and why it sharpens the answer rather than softening it

`G1-PLAN` ran the probe `GATE-01.md`'s escalation trigger asked for: a real
`loop.run()` over a synthetic feature whose unit fails every attempt
(`max_attempts: 3`, `verify` stubbed red). The re-plan trigger **fired** —
`RE-PLANNED …/T01 after attempt 2/3 — next dispatch uses a rewritten body`, a
`replan` event at `attempt: 2` — and the re-planned last attempt then failed
and the unit escalated `spinning_detected`. So a probe *can* produce a
re-plan, the escalation trigger's second clause is not met, and this gate is
drafted rather than blocked.

The probe's real finding is about ordering, and gate 2 is built on it:
`should_replan_instead_of_retry` fires at `attempt == max_attempts - 1` for
every eligible unit, so **by the time an operator ever reads this brief, the
driver has already re-planned that unit once and the re-planned attempt has
already failed.** The brief is not offering an untried remedy. It is
reporting that the automatic, unit-scoped re-plan was spent and did not work,
and asking whether to widen the same remedy to the rest of the gate. Offering
to execute that automatically — the same medicine at a larger dose, with the
one attempt that tested it already failed — is the weakest version of the
option, not the convenient one.

**What "recommend" must not degrade into.** Recommend-only is not "print
prose and let the operator hand-edit YAML." The brief must name the units it
would re-scope and the exact command that performs the flip, so the cost of
the manual step is one command, not an editing session. T07 owns that.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** No WU in this gate
  flips a default value or a severity: the brief is new output on a path that
  today prints one line, and no check changes level. T07 does change an
  operator-facing default — which option the brief presents first — and that
  is covered by the flag-scope table below rather than by a suite probe,
  because no existing test asserts on the exhaustion halt's stdout. The
  end-to-end probe that stands in for §4 is recorded in `GATE-02-REVIEW.md`
  § "The probe", with the driver's actual output pasted.
- **Flag-scope table (§3).** T07 introduces an operator-facing default and
  carries the table. Every `blocked_human` escalation reason in `loop.py` is
  enumerated there with a gated / not-gated verdict — the enumeration is
  measured (`grep -n '"reason": "' specfuse/loop/loop.py`), not recalled.
  Confirm at arming that the not-gated rows are the ones a reviewer agrees
  re-planning cannot help.
- **Escalation-predicate satisfiability (§2).** No check is raised to `ERROR`
  in this gate and no "zero issues" close predicate is asserted. The one
  zero-valued assertion — T07's negative observation that no status or
  attempt count changes when the brief prints — is a property of a code path
  that does nothing, and is satisfiable by construction.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted next gate and why, anything the retrospective got wrong. This is your record,
not the agent's — keep it honest.>
