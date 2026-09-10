---
id: FEAT-2026-0104/T05
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - docs/methodology.md
  - .specfuse/verification.yml.example
  - .specfuse/skills/authoring-work-units/SKILL.md
model: sonnet
effort: medium
gate_set: code
driver_version: 0.19.0
started_at: 2026-09-10T20:00:31.903770+00:00
duration_seconds: 956.096
cost_usd: 0.777467
input_tokens: 78
output_tokens: 9330
---

# Document when a unit re-plans and what an operator sees

**Objective.** Record the re-plan trigger where the surfaces that shape
behaviour are actually read: the methodology, the example verification config,
and the authoring guidance for unit sizing.

**Context.** FEAT-2026-0104/T05. `docs/methodology.md:187` already documents
the `replan` event from the consumer's side ("no `replan` event in
`events.jsonl` for this gate's WUs") as an auto-close condition. Until this
feature that sentence described something nothing could produce. It now needs
the other half: what causes a replan, and what a reader should conclude when a
gate did not auto-close because of one.

**Acceptance criteria.**

- `docs/methodology.md` states the trigger in terms of the ceiling, not a
  hard count of two, and names the `iterate_on_failure` exemption; the
  existing auto-close sentence at §2 is reconciled rather than duplicated.
- `.specfuse/verification.yml.example` documents any key this feature added,
  in the same shape as its neighbours, or states that none was added.
- `/authoring-work-units`' sizing rule gains a pointer noting that a unit
  which re-plans was mis-sized at authoring time — the re-plan is a recovery,
  not a workflow to design units around.
- `python3 .specfuse/scripts/leak_scan.py --all` exits 0 over the edited
  prose: no real paths, org names or home directories.

**Do not touch.** Driver code — every behaviour this unit describes is already
built by T01–T04 and this unit changes none of it. `.specfuse/LEARNINGS.md`,
which the closing sequence owns. The sibling WU files in this gate.

**Verification.** Narrow tier for `docs`: the `code` gates minus `tier: broad`,
plus `python3 .specfuse/scripts/leak_scan.py --all` and
`grep -n "replan" docs/methodology.md` to confirm both halves are present.

**Escalation triggers.** Stop with `status: blocked` if what T01–T04 actually
built contradicts what this plan says they would — documenting the plan's
intent over the tree's behaviour is how a doc becomes a lie.
