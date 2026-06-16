---
id: FEAT-2026-0021/T01
type: implementation
effort: low
status: done
attempts: 1
planned_cost_usd: 1.00
generated_surfaces: []
duration_seconds: 158.802
cost_usd: 0.343998
input_tokens: 8
output_tokens: 3826
---

# Slim the WU template's frontmatter notes; nudge acceptance criteria toward assertions

**Objective.** Shrink the authored surface of `.specfuse/templates/WU.template.md`
by folding driver-owned/audit-only frontmatter-field docs into one collapsed
note, and add a one-line nudge toward assertion-shaped, machine-checkable
acceptance criteria. Documentation-only; no executable code changes.

**Context.** Part of FEAT-2026-0021 (ceremony proportionality + slim WU
template), correlation ID `FEAT-2026-0021/T01`. See this feature's `PLAN.md`
for the why. `WU.template.md` today carries ~141 lines of frontmatter notes,
most of which document fields the **driver** writes at outcome time — an
author authoring a WU never sets them. That volume is loaded as context every
time the template grounds a drafting session, and it buries the handful of
fields an author actually fills. This WU collapses the driver-owned docs
without deleting any field or changing any contract. Binding rules in
`.specfuse/rules/` and the per-WU craft in
`.specfuse/skills/authoring-work-units/SKILL.md` apply by reference.
**Red-test exempt:** documentation/template-only WU — introduces no
executable behavior (see `/authoring-work-units` §12 carve-out).

**Acceptance criteria.**

- `.specfuse/templates/WU.template.md` contains exactly one collapsed note
  block, marked with the literal string `driver-owned`, that enumerates the
  fields the driver writes at outcome time: `attempts`, `cost_usd`,
  `input_tokens`, `output_tokens`, `duration_seconds`, `cumulative_cost_usd`,
  `cumulative_duration_seconds`, `cumulative_input_tokens`,
  `cumulative_output_tokens`, `re_arm_count`, `re_arm_history`. Verify:
  `grep -c "driver-owned" .specfuse/templates/WU.template.md` returns ≥ 1.
- The previous per-field standalone note paragraphs for those driver-owned
  fields are removed (their content lives only in the collapsed block). Verify
  the notes region shrank by at least 35 lines: the file is meaningfully
  shorter than its pre-WU length (record both counts in the RESULT block).
- The author-set optional fields remain documented (one concise line each):
  `planned_cost_usd`, `oracle_env`, `produces_driver_helper`,
  `generated_surfaces`, `model`, `effort`. Verify each token still appears:
  `for f in planned_cost_usd oracle_env produces_driver_helper generated_surfaces model effort; do grep -q "$f" .specfuse/templates/WU.template.md || echo "MISSING $f"; done` prints nothing.
- The five mandatory body sections (`Context`, `Acceptance criteria`,
  `Do not touch`, `Verification`, `Escalation triggers`) and the recommended
  `Objective` line are unchanged in the template body.
- The acceptance-criteria guidance in the template body gains one sentence
  encouraging **assertion-shaped, machine-checkable** criteria (each AC
  phrased so a single grep/command/test can judge it true or false). Verify:
  `grep -iq "assertion" .specfuse/templates/WU.template.md`.

**Do not touch.** Any driver or linter script under `.specfuse/scripts/`
(no frontmatter field is renamed or removed — only its documentation is
reorganized); any other feature folder; `.git/`. The driver owns all git
operations — edit files only. Edit only
`.specfuse/templates/WU.template.md`. See `.specfuse/rules/never-touch.md`
for the full forbidden-path list.

**Verification.** This is a documentation WU; the `doc` gate
(`artifact-changed`) plus the grep assertions above are the real oracle
(LEARNINGS[134-141]: a markdown-only WU otherwise gets a vacuous code-gate
pass). Additionally run, and require to pass:
- `python3 -m unittest discover -s tests` — confirms no existing test pins
  template text that this WU moved.
- `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0001-health-endpoint`
  exits 0 — confirms the slimmed template did not break the linter's view of
  a real feature.

**Escalation triggers.** Emit `status: blocked` rather than pushing through
if: any driver-owned field listed above is *also* an author-set field in
practice (the collapse would hide a value an author must provide); a test
greps removed template prose and cannot be satisfied without changing test
intent; or collapsing a field's doc would orphan a contract referenced by
`methodology.md` or `authoring-work-units` (leave a forwarding reference
instead and report). Blocked is a respectable outcome —
`result-contract.md` rule 4.
