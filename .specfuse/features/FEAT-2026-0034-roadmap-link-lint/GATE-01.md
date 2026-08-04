---
gate: 1
status: open
cost_budget_usd: 17.50
baseline:
  sha: 84122a67ee2130ad63be3edd04f12bd21a0a0d81
  probed_at: 2026-08-04T03:37:37.770296+00:00
  failing: []
---

# Gate 1 — the four rot shapes fail a check instead of a reader

## Definition of done

`roadmap.md` and `roadmap-archive.md` are read as one link graph and checked against
four invariants — blocked-by presence and resolution, ref resolution in both
directions, anchor adjacency, and cross-file ID uniqueness — wired into
`verification.yml` and exiting 0 on this tree.

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.

This gate is **terminal**: the closing sequence is a single `close` WU.

## Cost budget

`cost_budget_usd: 17.50` — the $12.50 sum of WU estimates ($4.00 / $3.50 / $5.00) plus
one re-attempt of the largest ($5.00, the close), per the GATE template's defensive
padding while the closing-WU retry defect (#260) is open. The close sits at the
`planning-discipline.md` §5 floor.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`, and it was
  load-bearing: the four invariants were checked by hand *before* drafting, two live
  violations were found, and they are repaired in a commit ahead of this feature. The
  gate's "exits 0 on this tree" criterion is therefore satisfiable on arrival rather
  than red on day one.
- **Runtime probe for a default/severity flip (§4).** Not applicable: no default,
  threshold, or severity changes. A new check is added; nothing that passes today
  begins failing except through the new gate's own findings.
- **Flag-scope table (§3).** Not applicable: no behaviour flag introduced.

## Known limits, recorded so the close does not misread them

**This gate lints; it does not repair.** `auto_archive_feature` produces shapes 3 and
4 on every archive run and is deliberately not fixed here — the roadmap row is
explicit that a failing check on the next archive *is* the durable fix. A close that
reports the archiver defect as outstanding work of this feature has misread the scope;
one that omits it entirely has hidden the reason the lint exists.

**ADR approval state is not checked.** A `**Blocked by.**` ADR link is validated for
existence, not for whether the ADR was accepted. FEAT-2026-0011 has sat `blocked` on an
unapproved ADR-0002 all week and will still pass this lint. That is correct and should
be stated rather than left to look like an oversight.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
