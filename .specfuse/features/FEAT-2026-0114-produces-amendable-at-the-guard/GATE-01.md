---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_produces_amendment_e2e -v -b"
cost_budget_usd: 40.00
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:19e6172a5f8ed4e64796dcbec75a5c167dfaa326:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:432d3887cc279ecdd3887cf10cca56aaf178a2d5:4acc6dfc5e8cece358c167d876515eba4a39a500:5a7eaa51c3d1b12fd724e173fb4a170d8ffc2a22:5ff66b6e4d8a264f23709ea60706111a4c59ed11:7236c0b74a800bb48cc28ab6dc46543c53a4dc90:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d664745f3d8e8d366a9f5029d78452efa5fda16f:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:e978847f0b944383345d25b542b3a49c2578b685
  ran_at: 2026-09-26T15:55:13.587483+00:00
  ok: true
  failing: []
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
