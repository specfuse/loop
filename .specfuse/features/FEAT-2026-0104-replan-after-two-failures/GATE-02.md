---
gate: 2
status: open
feature_oracle: "python3 -m unittest tests.test_spinout_brief_end_to_end -v -b"
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:2063b9c8685a76b5b0c2f876d054f6c8ebd235dd:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:3e1ed273ab9179bbc8a1519961dcece15f51277e:5ff66b6e4d8a264f23709ea60706111a4c59ed11:764f3615ab36287de03ddb147c0182b4145e20fb:78bc254baa9a8d1942140efcd1850b5c80a45539:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:8e3f37864133a66f9183cc23d6a11c5f9bfff755:97bcab1bc7244262cec901f46035f51dfdd07278:a32e8963721b36864c84ad7270d4b865fb7b2498:ba4e2ff68ff80b36054d003c5116bc9d9b3d3b1e:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  ran_at: 2026-09-11T17:17:10.538635+00:00
  ok: true
  failing: []
baseline:
  sha: b2f48f3f7a05a916e2decaf8a372552ea8a48065
  probed_at: 2026-09-11T16:29:54.858603+00:00
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:1f31411f88c46b16b536a083ef2eae1f0aaeff11:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:3e1ed273ab9179bbc8a1519961dcece15f51277e:5a010d5ade522ead755dae28d5c4a75cde10207e:5ff66b6e4d8a264f23709ea60706111a4c59ed11:764f3615ab36287de03ddb147c0182b4145e20fb:804e4be4b3a6a3eddf29cb2bcfae62a5fcdcd3fe:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:ba4e2ff68ff80b36054d003c5116bc9d9b3d3b1e:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d6c37c69e5921caafea5e01e5a7de243a8d0a7d6:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  entry_sha: b2f48f3f7a05a916e2decaf8a372552ea8a48065
  source: attributed:FEAT-2026-0104/T10
  failing: []
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
