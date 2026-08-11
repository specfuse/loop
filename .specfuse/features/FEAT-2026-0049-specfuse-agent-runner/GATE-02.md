---
gate: 2
status: open
cost_budget_usd: 45.50
---

# Gate 2 — the agent drains bugs, triage, and answered escalations

## Definition of done

The agent autonomously handles the cheap action classes and escalates what it
cannot: answered needs-human issues, parsed and acted on first; bug issues
through `run_bug_lane`; untriaged issues through `apply_triage` (honouring
`rules.triage.auto`). Underneath them, the seam all three need — the selector's
kind vocabulary, the provider registry reachable from the CLI, and a spend ledger
that makes `--max-tokens` enforce a real number rather than a counter that never
leaves zero.

This is the first gate in which the agent acts on a live repository. Every
provider consumes its shipped function unmodified; none of them changes a
default, a severity, or any predicate they call.

## Status

Drafted by gate 1's `plan-next` (`G1-PLAN`) on 2026-08-11 against the conductor
as gate 1 actually shipped it. Four substantive work units plus the two-WU
closing sequence — see `GATE-02-REVIEW.md` for what settled the shape.

**Sizing risk — resolved: split.** The findings classes (`diagnose_cli`,
`run_autofix`) moved out of this gate into their own, ahead of the features gate.
The evidence is in `GATE-02-REVIEW.md` § "The sizing decision"; the mechanical
insertion is `G2-PLAN`'s first acceptance criterion, since it moves the terminal
close to gate 4.

## Cost budget

`cost_budget_usd: 45.50` — the $37.50 sum of this gate's planned WU costs plus one
re-attempt of its largest work unit (T05, $8.00), per the planning-discipline §5
padding rule. For calibration: gate 1 planned $29.50 and spent $5.95.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping this gate's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** **Checked by `G1-PLAN`:
  none of the four drafted WUs flips a default or a severity**, so no §4 runtime
  probe is required to arm this gate. The reasoning, including the one change
  that came closest, is recorded in `GATE-02-REVIEW.md` § "Default and severity
  check". If arming review revises a WU into flipping one, that WU may not be
  armed on "mechanical, nothing design-open" and needs the local probe first.
- **Scope check.** PLAN.md's scope boundary forbids modifying any surface the
  agent drives. A drafted WU that needs to change `run_bug_lane`, `apply_triage`,
  or `escalation.py` is a plan change to escalate, not a WU to arm. Each drafted
  WU names its shipped function and its `Do not touch` section says so.
- **Existing-mechanism check (§1).** Confirm each named function still exists and
  still has the seams the WU assumes — these are consumed, not vendored, and they
  can move. The line references in the WU bodies are as of commit `eeaf09b`.
- **Open questions.** `GATE-02-REVIEW.md`'s frontmatter carries a non-empty
  `open_questions:` list. Under `autonomy_default: auto` that parks the feature
  until it is answered — deliberately: both entries are decisions the operator
  owns, not work the planner deferred.
