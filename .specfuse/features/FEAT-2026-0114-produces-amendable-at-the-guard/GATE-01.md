---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_produces_amendment_e2e -v -b"
cost_budget_usd: 40.00
---

# Gate 1 — a verified attempt amends its `produces:` and passes; an identical refusal never runs a third time

## Definition of done

A work unit whose attempt passes verification but leaves a declared `produces:`
path untouched can drop that path from its declaration in the RESULT block with
a reason, and the attempt passes: the unit's `produces:` is rewritten without
it, the drop is recorded on the unit and on the passed event, and the judge
sees it. A refusal the RESULT does not answer is recorded like every other
guard refusal, so two identical ones end the unit as
`deterministic_refusal_repeat` and a third dispatch never happens. The repair
note shows both RESULT escape hatches verbatim.

The `feature_oracle` above is that claim, executable. It is **red on the tree
this gate starts from** (the module does not exist), and T01 — the walking
skeleton — is what makes it green. It drives `loop.run()` with a stubbed
dispatch: attempt 1 writes one of two declared deliverables and returns a RESULT
that drops the other under `produces_amended:` with a reason; the oracle asserts
the unit ends `done` on attempt 1, that `produces:` on disk lists only the
touched path, that `produces_dropped:` records the other with its reason, and
that the passed `attempt_outcome` carries `produces_amended`.

Also required for the gate to close:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are staged (feature-local `LEARNINGS-pending.md`).
- Documentation reflects what was actually built, in both the canonical
  `.specfuse/` files and their `specfuse/loop/data/` mirrors.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This is the feature's terminal gate, so its closing sequence is a single `close`
unit and the terminal verdict is written by a fresh judge session, not by the
close itself.

## The one site and the one switch

| surface | today | after this gate |
| --- | --- | --- |
| `resolve_produces_refusal` | reads `produces_unchanged:` only | also reads `produces_amended:`; a justified drop is accepted |
| `produces_not_in_diff` branch | never appends to `refusal_history` | appends, like the other five guard sites |
| repair note for that class | names `produces_unchanged:` | shows both keys' YAML verbatim |
| `verification.yml` `defaults.produces_amendable` | absent | `false` ignores the new key; absent means on |

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** T01 flips a default (a
  justified amendment passes where it refused). Before arming, run
  `python3 -m unittest tests.test_produces_justification tests.test_guard_repair_e2e tests.test_deliverable_presence_gate tests.test_deterministic_refusal_repeat -v -b`
  on the tree this gate starts from and paste the result here; T01's criterion
  4 names these as the modules that must keep passing unchanged.
- **Flag-scope table (§3).** The table above is it.
- **Escalation-predicate satisfiability (§2).** No check is raised; PLAN.md
  records zero.

## Reflection notes

<Written by the human at review time.>
