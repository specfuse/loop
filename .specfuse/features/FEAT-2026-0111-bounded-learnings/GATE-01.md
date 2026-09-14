---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_binding_block_budget -v -b"
baseline:
  sha: b1268fa81ac577bb06cd1b107711cadcdf59e1f5
  probed_at: 2026-09-14T15:24:45.925491+00:00
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4acc6dfc5e8cece358c167d876515eba4a39a500:5ff66b6e4d8a264f23709ea60706111a4c59ed11:764f3615ab36287de03ddb147c0182b4145e20fb:77e8e3d3023099737fdfe4a1695c0edbbf639e45:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:9bd7bd3ea82793dad908b45e7abb4d4f81f91420:a00f17b4dea92727aa92f2478bef37348e132b4d:b37abd23368ec1eafe7ac27bb03aa41f66a8a5b2:ba4e2ff68ff80b36054d003c5116bc9d9b3d3b1e:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  entry_sha: b1268fa81ac577bb06cd1b107711cadcdf59e1f5
  source: attributed:FEAT-2026-0111/T05
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: "test_packaged_copy_is_byte_identical"
    - gate: coverage
      failure_class: other
      failure_signature: "no_gate_marker"
---

# Gate 1 — the distilled set reaches dispatch, inside an enforced budget

## Definition of done

`.specfuse/rules-local/learnings-distilled.md` is loaded by the binding block;
its content was accepted by a human rather than generated unattended; and the
whole block — distilled file included — is under 2,500 words and stays there
because a lint says so.

The `feature_oracle` is red today on both counts: the block is at 2,574 words
and no distilled file exists. T01 is the tracer bullet that makes it runnable;
T02–T04 make each part correct.

Also required, as for every gate:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## The blocking question this gate may not answer

Where the trim comes from is unknown. All three binding rules are contracts.
**T01 must report the trimmable headroom it found and block rather than trim a
binding contract to make room.** If the honest answer is that nothing can go,
this gate stops and a human decides whether to raise a cap set on measured
evidence — that is not a decision any unit here is authorized to make by
default.

## What this gate must not break

The binding block is what every dispatched session in every consuming project
reads. A change that pushes it further over budget, or that drops a rule an
implementation session depends on, is worse than shipping nothing. The
2,500-word figure exists because a 7,213-word block was measured being read
past (`scaffold.py:227`, FEAT-2026-0084/T01) — a larger block is not a
neutral trade, it is the failure mode.

`.specfuse/rules-local/` is documented as never touched by
`specfuse upgrade`. Anything this gate writes there must survive an upgrade,
and anything it writes to the scaffold's own block must not clobber a
consumer's `@` lines.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Escalation-predicate satisfiability (§2).** This gate makes a cap
  blocking, and the cap **fails on the current tree** (2,574 vs 2,500). PLAN.md
  answers §2 explicitly: the lint may not become blocking until the tree can
  pass it. Confirm at arming that T04 lands the allocation before, or with,
  the severity flip — never after.
- **Runtime probe for a default/severity flip (§4).** The flip above is a
  severity flip. Apply it locally and paste the failing set into
  `GATE-01-REVIEW.md` before arming anything that depends on it.
- **Flag-scope table (§3).** T04 introduces the budget that gates what loads.
  Confirm it names every `@`-referenced file and whether the budget covers it.

## Reflection notes

<Written by the human at review time.>
