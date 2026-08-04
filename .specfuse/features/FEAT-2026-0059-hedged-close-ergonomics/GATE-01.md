---
gate: 1
status: passed
cost_budget_usd: 19.50
baseline:
  sha: 305c857d283e7b787400bd1ad864aca13617e4d4
  probed_at: 2026-08-04T12:14:58.565075+00:00
  failing: []
---

# Gate 1 — a hedged close answers "why not `met`" before it is asked

## Definition of done

Every follow-up entry a hedged close writes carries a `kind:`, a lint refuses a
hedged close without one, and `/accept-hedged-close` leads with the verdict ceiling
the classification implies rather than a wall of quotes — with routed findings
prompted onto a tracking surface instead of dying in prose.

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.

This gate is **terminal**: the closing sequence is a single `close` WU.

## Cost budget

`cost_budget_usd: 19.50` — the $14.50 sum of WU estimates ($3.50 / $3.50 / $2.50 /
$5.00) plus one re-attempt of the largest ($5.00, the close), per the GATE template's
defensive padding while the closing-WU retry defect (#260) is open. The close sits at
the `planning-discipline.md` §5 floor.

Estimates are set below this repo's historical drafting habit deliberately.
Implementation work units have come in well under estimate across the last four
features (FEAT-2026-0034 landed $2.21 and $1.17 against $4.00 and $3.50), while
closing WUs overshoot — the split #260 tracks. Padding the implementation side
further would make the gate budget a number nobody trusts.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`, and it is
  load-bearing: two hedged records already exist without `kind:`, so a corpus-wide
  lint would be red on arrival and unfixable without rewriting closed features. The
  check is scoped to the close being linted. Confirmed before drafting.
- **Runtime probe for a default/severity flip (§4).** Not applicable: no default,
  threshold, or severity changes. A required field is added to a record that is
  currently unlinted, so nothing passing today begins failing.
- **Flag-scope table (§3).** Not applicable: no behaviour flag is introduced.

## The one thing this gate must not do

**The skill must not infer `kind` from prose.** The close WU writes it, because the
close has the context — it knows why a criterion went unmet, having just tried to
meet it. A skill inferring the classification from wording would be confidently wrong
on exactly the ambiguous entries where the operator most needs it right, and its
guess would carry the authority of the tool rather than the uncertainty of a
heuristic. If T02 or T03 finds itself pattern-matching entry text to decide a kind,
that is an escalation, not a clever fallback.

## Known limits, recorded so the close does not misread them

**The two existing hedged records stay unclassified.** FEAT-2026-0041's and
FEAT-2026-0042's retrospectives predate `kind:` and are deliberately not migrated —
they are records of what those closes knew at the time. A close that reports them as
outstanding migration work has misread the scope.

**Nothing here changes when a hedge happens.** `verdict_permits_terminal_flips` is
untouched. If this gate's output makes hedging *feel* different, that is ergonomics,
not semantics, and the close should say so.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
