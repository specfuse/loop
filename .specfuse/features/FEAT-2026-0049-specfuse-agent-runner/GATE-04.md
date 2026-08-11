---
gate: 4
status: awaiting_review
cost_budget_usd: 29.50
baseline:
  sha: 3d62f18504cd3369c82359c933e02283935d6ada
  probed_at: 2026-08-11T11:02:35.858100+00:00
  failing: []
---

# Gate 4 — the agent advances features

## Definition of done

The agent reads the `queue:` top, advances that feature by invoking `specfuse
run` as a subprocess, classifies the driver's halt, escalates on
`awaiting_review` and switches to the next workable item, and parks blocked items
with an escalation. A drafting-needed queue top escalates rather than drafting —
async drafting is FEAT-2026-0050, explicitly out of scope here.

This is the terminal gate: its closing sequence is a single `close` work unit.

## Status

Drafted by gate 3's `plan-next` (`G3-PLAN`) on 2026-08-11 against the conductor
and the five providers as gates 1–3 actually shipped them. Three substantive work
units plus the terminal `close` — see `GATE-04-REVIEW.md` for the halt
classification decision, the three open questions, the four decisions taken at
draft time, and the cross-surface contract table.

The `close` WU's criteria were sharpened by the same unit and its `depends_on`
set to the three substantive units; it was drafted originally by `G1-PLAN`
against a guess at what this feature would build.

**Renumbered from gate 3 by `G2-PLAN` (2026-08-11).** The findings gate was
inserted ahead of this one — the sizing decision recorded in `GATE-02-REVIEW.md`
§ "The sizing decision" — which moved this gate and its terminal close from 3 to
4. Nothing else about this gate changed.

## Cost budget

`cost_budget_usd: 29.50` — the $23.00 sum of this gate's planned WU costs plus
one re-attempt of its largest work unit (T14, $6.50), per the
planning-discipline §5 padding rule. For calibration: gate 1 planned $29.50 and
spent $5.95, gate 2 planned $39.50 and spent $6.66, gate 3's substantive work
planned $20.50 and spent $4.94. `GATE-04-REVIEW.md` § "Gate 4's work units"
records why the estimates were corrected modestly rather than to the observed
median.

## What this gate deliberately does not prove

**No `specfuse-agent run` has ever executed against live repository state**, and
gate 4 does not change that. Every criterion in T12, T13 and T14 is met against
fixture feature folders and an injected runner, for a reason that is a safety
property rather than a limitation: a test that dispatched the real driver against
a real feature in this repository would run the loop inside the loop, and this
repository's own `queue:` names this very feature. What is provable here — the
classification, the ranking, the escalation shapes, the decline paths, the
subprocess invariant — is everything that does not require a live dispatch. The
terminal close must carry the remainder as an explicit deferral rather than let
"every work unit passed" read as "the agent advanced a feature".

## The constraint that must survive to here

The driver is invoked as a **subprocess**, never imported and called in-process.
Two live defects make in-process invocation wrong: #757 (a work unit that edits
the driver cannot take effect for anything the same process dispatches
afterwards) and #1040 (console scripts resolving `specfuse.loop` from
site-packages rather than the working tree). A gate-4 work unit that imports
`loop.run` has broken the feature's central design decision.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping this gate's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** **Checked by `G3-PLAN`:
  none of the three drafted WUs flips a default or a severity**, so no §4 runtime
  probe is required to arm this gate, and none was run. T13 reads the driver's
  exit codes and frontmatter and changes nothing about what a halt *is* — only
  about what the agent calls it, which is the distinction this bullet was written
  to test. The reasoning per WU, and the two changes that come closest —
  `rules.features.gate_review` and `rules.features.wip_limit` becoming
  load-bearing, and `specfuse-agent run` gaining the power to dispatch the gate
  driver — is recorded in `GATE-04-REVIEW.md` § "Default and severity check". If
  arming review answers OQ-1, OQ-2 or OQ-3 in a way that turns any of them into a
  real flip, that WU may not be armed on "mechanical, nothing design-open" and
  needs the local probe first.
- **Subprocess invariant.** Confirm no drafted WU imports `loop.run`. This is the
  one constraint that must survive from draft time to here; check it at arming,
  when the WUs actually exist, rather than trusting the prose above. Note it now
  survives an extra gate: it was drafted when this was gate 3. **As drafted it
  holds, and T13's criterion 2 makes it mechanical**: a structural test asserts
  `driver_invoke.py`'s source contains neither `loop.run` nor
  `import specfuse.loop.loop`, so the invariant is checked by the suite from here
  on rather than by a reviewer's memory.
- **Open questions.** `GATE-04-REVIEW.md`'s frontmatter carries a non-empty
  `open_questions:` list. Under `autonomy_default: auto` that parks the feature
  until it is answered — deliberately: all three are policy decisions the
  operator owns, and each changes one acceptance criterion. OQ-3 is the one worth
  reading first; it is the largest expansion of what an unattended run can do.
- **Scope check.** A drafting-needed queue top escalates. A drafted WU that
  attempts to draft a feature has taken on FEAT-2026-0050's scope and must not be
  armed. **As drafted this holds**: T14's criterion 5 asserts the injected runner
  receives no invocation containing `draft-feature`, and the drafting-needed path
  reaches no driver invocation at all.
- **Existing-mechanism check (§1).** Confirm each named function and constant
  still exists and still has the seams the WUs assume. The line references in the
  WU bodies and in `GATE-04-REVIEW.md`'s contract table are as of commit
  `7cb49da`.
