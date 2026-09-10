---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_replan_end_to_end -v -b"
broad_run:
  tree: 010925acc191f352208acf03ad762b9d00247d62:06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:2c83bb610823e9b2aa803d43f8ef82b91d62b233:3e1ed273ab9179bbc8a1519961dcece15f51277e:5ff66b6e4d8a264f23709ea60706111a4c59ed11:764f3615ab36287de03ddb147c0182b4145e20fb:7b71e2d8d3d0d713385dc05863ba3d4f56f8bf8e:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:a26afd89f21eabb7487be4942de364c6a6c80a70:ba4e2ff68ff80b36054d003c5116bc9d9b3d3b1e:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  ran_at: 2026-09-10T20:19:52.393960+00:00
  ok: true
  failing: []
---

# Gate 1 — a unit that fails twice is re-planned, not re-run

## Definition of done

A work unit that has failed its second-to-last permitted attempt is re-planned
in place — a planning turn narrows its body, the driver reloads it and resets
its attempts — instead of being dispatched again with the identical prompt.
The gate's `events.jsonl` carries the `replan` event that
`gate_eval.evaluate_auto_close` already consumes as check 2.

The `feature_oracle` above is the executable proof. It is **red today**:
`tests/test_replan_end_to_end.py` does not exist. T01 is the tracer bullet
that makes it runnable and green by wiring the thinnest path end to end;
T02–T04 make each part correct.

Also required, as for every gate:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.
- The next gate's work units are drafted, and `GATE-02-REVIEW.md` is written.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## What this gate must not break

`detect_deterministic_refusal_repeat` (`loop.py:1399`) already escalates
*earlier* than any ceiling: a byte-identical guard refusal over a provably
untouched tree halts before the next session is dispatched. Re-plan fires
later and on a different signal. A unit that trips the refusal-repeat check
must still escalate there — re-plan must not convert a known-unfixable
refusal into a planning turn that cannot help either.

FEAT-2026-0103 rewrote this same retry path days before this gate was drafted:
a guard refusal now retains the working tree and dispatches a repair. A repair
attempt and a re-plan attempt are different things and the gate must keep them
distinguishable in the attempt record.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** No WU in this gate flips
  a default or a severity — the trigger is new behaviour behind a new decision
  point, and `MAX_ATTEMPTS` keeps its value. If gate 2's drafted WUs introduce
  one, the probe applies to them.
- **Flag-scope table (§3).** T02 introduces the decision that selects between
  "retry" and "re-plan". Confirm its flag-scope table names every path that
  reaches a retry today.
- **Escalation-predicate satisfiability (§2).** No check is raised to `ERROR`
  in this gate.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted next gate and why, anything the retrospective got wrong. This is your record,
not the agent's — keep it honest.>
