---
gate: 1
status: passed
cost_budget_usd: 21.00
baseline:
  sha: d6a7a6108c0f1a0700f31a6d83fb50f72ee2eaa4
  probed_at: 2026-08-04T14:03:16.071430+00:00
  failing: []
---

# Gate 1 — what changed, and will it break me, answerable from one document

## Definition of done

A `CHANGELOG.md` exists with an `Unreleased` section; both surfaces that ship work —
the close ceremony for features, `fix-bug` for bugs — append to it as work lands; and
cutting a version stamps `Unreleased` with the version, the date, and the umbrella
version that ships it, after which that section is immutable.

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.

This gate is **terminal**: the closing sequence is a single `close` WU.

## Cost budget

`cost_budget_usd: 21.00` — the $16.00 sum of WU estimates ($4.00 / $4.00 / $3.00 /
$5.00) plus one re-attempt of the largest ($5.00, the close), per the GATE template's
defensive padding while the closing-WU retry defect (#260) is open.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md` and
  load-bearing: 51 features are `done` and every prior bug PR predates this, so a
  lint demanding retrospective coverage is red on arrival. The check is scoped to work
  landing **after** this ships. No backfill.
- **Runtime probe for a default/severity flip (§4).** Not applicable: no default,
  threshold, or severity changes.
- **Flag-scope table (§3).** Not applicable: no behaviour flag introduced.

## The gap the roadmap row does not cover, and this gate does

The row says "the collection point", singular, and describes only the close ceremony.
**Bugs have no close ceremony** — `1 bug = 1 branch = 1 PR`, no feature folder, no §3
enumeration. Of the nine PRs merged 2026-08-03/04, **four were bugs**. A close-only
collector drops all of them and the document looks complete while being wrong about
half the release.

T02 therefore ships **two** collection points. A WU that implements only the close
side has built the thing the row described and not the thing the release needs.

## Known limits, recorded so the close does not misread them

**History is not backfilled, and the CHANGELOG will look thin at first.** Fifty-one
features and every prior bug PR stay undocumented, deliberately. The close must say
this plainly — an empty early document is a scope decision, not a claim that nothing
changed, and a reader who assumes otherwise has been misled by omission.

**Entry prose quality is not machine-checkable.** The lint asserts an entry exists, is
classified, and traces to a FEAT-ID or issue number. Whether the sentence is *useful*
is a human read. A close reporting "the CHANGELOG is verified" must not let a green
lint stand in for that.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
