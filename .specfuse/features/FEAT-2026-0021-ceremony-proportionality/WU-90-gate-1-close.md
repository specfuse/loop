---
id: FEAT-2026-0021/G1-CLOSE
type: close
effort: high
status: done
attempts: 0
planned_cost_usd: 1.50
generated_surfaces: []
verdict: met
auto_close: true
auto_close_reasons: []
---

# Terminal close — ceremony proportionality + slim WU template

**Objective.** Run the single terminal close for FEAT-2026-0021: write
`RETROSPECTIVE.md`, promote durable lessons to `LEARNINGS.md`, reconcile docs
and the roadmap row, and write the terminal feature-arc verdict. This is the
dogfood: a ≤4-substantive-WU feature closing with a single terminal `close`,
exactly the shape T02 prescribes.

**Context.** Correlation ID `FEAT-2026-0021/G1-CLOSE`, terminal gate of
FEAT-2026-0021. Both substantive WUs (T01 slim template, T02 ceremony
proportionality) are documentation-only and must be `done` before this runs.
Collapse retrospective + lessons + docs + terminal verdict into this one
session (methodology §3 single-WU terminal `close`). Read `events.jsonl`, both
WU frontmatters (actual `cost_usd`), and `PLAN.md`'s planned-cost table to
build the cost analysis. Binding rules in `.specfuse/rules/` apply by
reference.

**Acceptance criteria.**

- `RETROSPECTIVE.md` exists in this feature folder and includes a
  `## Cost analysis` section reconciling `planned_cost_usd` (PLAN.md table +
  per-WU frontmatter) against actual spend (per-WU `cost_usd` /
  `events.jsonl`), with the delta named.
- `RETROSPECTIVE.md` includes a `## What the loop did NOT verify` section
  enumerating every acceptance criterion whose verification was deferred
  (e.g. real human-authoring ergonomics of the slimmed template; whether the
  ≤4 threshold is correctly calibrated — only future features can confirm).
  Write `(nothing — every acceptance criterion was verified in-loop)` if the
  list is empty so the count is explicit. If the list exceeds 2 entries or
  30% of criteria, flag the single-gate sizing under `## What I'd change`.
- `RETROSPECTIVE.md` records the **measurement baseline** verbatim for the
  follow-up feature to compare against: total $174 / 43% ceremony cost / $1.43
  avg implementation WU, over 14 features / 129 costed WUs. Name the metrics
  to re-measure on the next 2–3 features (ceremony %, impl $/WU,
  re-grounding token count) before any driver hardening.
- `RETROSPECTIVE.md` lists candidate **ceremony-execution** levers for the
  deferred follow-up feature: `close-intermediate` opus→sonnet, effort tiering
  on close WUs, trimming mandated retro structure, ceremony-content
  proportionality.
- `.specfuse/LEARNINGS.md` gains at least one durable, generalizable entry
  tagged `[FEAT-2026-0021/G1-CLOSE]` (e.g. the proportionality threshold; the
  "recon corrected the plan — two of four proposed changes were already in
  existing craft" lesson about inferring before inventing).
- Documentation reconciled: any doc that describes ceremony shape or the WU
  template surface reflects what T01/T02 changed.
- The roadmap row for FEAT-2026-0021 reflects terminal status per the
  close→roadmap reconciliation contract (methodology §; do not flip to a
  state the close ceremony does not own — match the precedent of recent
  terminal closes).
- A terminal feature-arc verdict (`met` / `partial` / `not met`) is written
  with one-line justification.

**Do not touch.** `.specfuse/scripts/loop.py` and other driver scripts (this
feature never changes them); other feature folders except the single roadmap
row; secrets; `.git/`. The driver owns git operations. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext`/close gate
(`python3 .specfuse/scripts/lint_plan.py <feature_dir>` clean) plus the
hollow-pass close guard (`assert_cost_analysis_section_when_met` and the
`## What the loop did NOT verify` section presence). Confirm
`RETROSPECTIVE.md` and the `LEARNINGS.md` append exist and are non-empty.

**Escalation triggers.** Emit `status: blocked` if either substantive WU is
not `done`; if the actual spend exceeds the $3.50 plan by > 2× (surface the
overrun rather than papering over it); or if reconciling the roadmap row would
require touching another active feature's section. Blocked is respectable —
`result-contract.md` rule 4.
