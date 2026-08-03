---
gate: 1
status: awaiting_review
cost_budget_usd: 23.50
baseline:
  sha: 26290fb0200643b6cb33a5f89e59544c8c6be566
  probed_at: 2026-08-03T19:58:42.808561+00:00
  failing: []
---

# Gate 1 — a finding can be diagnosed, in one format, from either entry point

## Definition of done

A harvester finding can be turned into a structured diagnosis comment — root cause,
evidence trail, candidate fix, and machine-readable `confidence` and `fix_scope` —
rendered by a module that owns the format, produced identically from the interactive
and headless entry points, with the `gh` round-trip verified against a real repository
rather than a stub.

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.

This gate is **terminal**: the closing sequence is a single `close` WU, not
`close-intermediate` + `plan-next`. There is no next gate to draft.

## Cost budget

`cost_budget_usd: 23.50` — the $18.50 sum of WU estimates ($4.00 / $3.50 / $3.00 /
$3.00 / $5.00) plus one re-attempt of the largest WU ($5.00, the close), per the
defensive padding the GATE template prescribes while the closing-WU retry defect
(#260) is open. The close sits at the `planning-discipline.md` §5 floor of $5.00.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate's WUs are armed at draft time (`status: pending`), so the discipline below
applies to this drafting rather than to a later arm:

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`, and it is
  load-bearing twice here: no criterion asserts a diagnosis is *correct* (unsatisfiable
  in-loop), and only T04 may invoke `gh` (satisfiable only unsandboxed). Confirmed
  before drafting.
- **Runtime probe for a default/severity flip (§4).** Not applicable: no default,
  threshold, or severity changes. Additive module, skill, and entry point.
- **Flag-scope table (§3).** Not applicable: no behaviour flag introduced.
  `unsandboxed: true` on T04 is an existing driver field.

## The sandbox escape, scoped deliberately

T04 is the only work unit carrying `unsandboxed: true`. That is not an accident of
convenience — it confines the escape to the single unit that needs it, so the blast
radius of running without the sandbox is one work unit rather than the gate.

**No other work unit may write a `gh` acceptance criterion.** A sandboxed `gh` call
fails with an invalid-token or TLS-certificate error that reads like a broken feature
rather than a sandbox artifact, and that misreading has already cost this project two
features (see `PLAN.md`). If a WU other than T04 appears to need `gh`, that is an
escalation, not a flag to copy.

## Known limits, recorded so the close does not misread them

**Diagnosis quality is not verified by this gate and cannot be.** Every test here
asserts format, contract, and round-trip fidelity. A green gate means the comment is
well-formed and the fields parse — it does **not** mean the root cause is right. The
close must state this in `## What the loop did NOT verify` rather than let passing
format tests read as verified diagnosis quality. This is the feature's central
limitation and it is inherent, not a drafting gap.

**A hard-killed T04 attempt may orphan a scratch issue.** Cleanup is an explicit
acceptance criterion and the scratch issue carries an identifying marker, but a
process killed between create and close leaves one open. If the close finds one,
report it rather than quietly deleting it.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
