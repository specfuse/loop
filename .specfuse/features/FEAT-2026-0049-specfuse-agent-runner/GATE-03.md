---
gate: 3
status: awaiting_review
cost_budget_usd: 38.50
baseline:
  sha: b5b72d3a827bd7f31b2efc628e1706445dfea752
  probed_at: 2026-08-11T04:10:24.117876+00:00
  failing: []
---

# Gate 3 — the agent diagnoses and autofixes findings

## Definition of done

The agent handles the two findings action classes over the monitoring surface,
both composed from shipped functions consumed unmodified:

- **findings-diagnose.** An open `monitoring-finding` issue that carries no
  diagnosis comment is analysed by a headless session, rendered through
  `specfuse.monitor.diagnose_cli.render_headless`, and posted as exactly one
  comment. `diagnose_cli` renders; it neither produces the analysis nor posts
  the result, so the provider supplies both halves.
- **findings-autofix.** A diagnosed finding issue is run through
  `specfuse.monitor.autofix_run.run_autofix`, which decides, records, fires, and
  labels. The provider's job is to reach that call with a valid
  `(monitoring_config, component)` pair and to translate the result into an
  outcome the conductor records — never to re-decide what `autofix.decide`
  already decided.

Underneath them, the seam both need: two more item kinds with a ranking the
selector can place, the monitoring-config reader that resolves a finding issue to
its component and dial, and the CLI surface that tells the agent where the
monitoring config lives.

## What this gate deliberately does not prove

**Nothing in this gate can be exercised against this repository end to end**, and
that is the reason it is its own gate rather than part of gate 2.
`.specfuse/verification.yml`'s `monitoring-example-lint` gate says why in its own
words: *"this repo is a CLI tool with no deployable components and will never
carry a real monitoring.yml."* No `monitoring.yml` means no harvester, which
means no `monitoring-finding` issue has ever been filed here, which means both
providers advertise an empty list against this repo's live state — correctly.

What **is** provable here, and what the work units are written to prove, is every
behaviour that does not need a live component: the composition, the parse and
render path, the decline paths, the idempotence, the escalations, and the
selector's ranking. The verification shape is the one
`tests/test_autofix_run.py` already established for `run_autofix` itself —
injected `runner`, fixture config — which is the same oracle the shipped function
is held to. `GATE-03-REVIEW.md` § "What cannot be proven here, precisely" names
what that leaves open and the exact condition that would close it.

## Status

Drafted by gate 2's `plan-next` (`G2-PLAN`) on 2026-08-11 against the conductor
and the four providers as gate 2 actually shipped them. Three substantive work
units plus the two-WU closing sequence — see `GATE-03-REVIEW.md` for the ranking
decision, the two open questions, and the cross-surface contract table.

This gate is **non-terminal**: gate 4 (the features gate) is the terminal one, so
this gate closes with `close-intermediate` + `plan-next`, and `G3-PLAN` drafts
gate 4's substantive work units.

## Cost budget

`cost_budget_usd: 38.50` — the $31.00 sum of this gate's planned WU costs plus one
re-attempt of its largest work unit (T10, $7.50), per the planning-discipline §5
padding rule. For calibration: gate 1 planned $29.50 and spent $5.95; gate 2
planned $39.50 and spent $6.66.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping this gate's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** **Checked by `G2-PLAN`:
  none of the three drafted WUs flips a default or a severity**, so no §4 runtime
  probe is required to arm this gate. The reasoning, including the two changes
  that come closest — findings-autofix reusing `rules.bugs.preempt`, and the
  `diagnose:` dial becoming load-bearing for the first time — is recorded in
  `GATE-03-REVIEW.md` § "Default and severity check". If arming review answers
  OQ-1 or OQ-2 in a way that turns either into a real flip, that WU may not be
  armed on "mechanical, nothing design-open" and needs the local probe first.
- **Open questions.** `GATE-03-REVIEW.md`'s frontmatter carries a non-empty
  `open_questions:` list. Under `autonomy_default: auto` that parks the feature
  until it is answered — deliberately: both entries are policy decisions the
  operator owns, and each changes one acceptance criterion.
- **Scope check.** PLAN.md's scope boundary forbids modifying any surface the
  agent drives. A drafted WU that needs to change `diagnose_cli.py`,
  `autofix_run.py`, `autofix.py`, or `autofix_state.py` is a plan change to
  escalate, not a WU to arm. Each drafted WU names its shipped function and its
  `Do not touch` section says so.
- **Existing-mechanism check (§1).** Confirm each named function still exists and
  still has the seams the WU assumes. The line references in the WU bodies are as
  of commit `8ee9fbc`.
- **The arm predicate will not clear this gate on its own, and that is expected.**
  `arm_eval`'s drift-cap and budget-projection classes have been fired since gate
  2 was drafted: `PLAN.baseline.json` snapshots 7 work units totalling $34.50, and
  every WU drafted after baselining counts as added. Gate 2 was armed by hand
  through `/arm-gate` for the same reason. Read this as "the predicate is doing
  its job on a feature that was baselined before two of its four gates were
  planned", not as a new signal about gate 3.
