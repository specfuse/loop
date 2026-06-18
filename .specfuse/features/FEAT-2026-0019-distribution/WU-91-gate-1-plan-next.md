---
id: FEAT-2026-0019/G1-PLAN
type: plan-next
effort: high
status: done
attempts: 0
planned_cost_usd: 2.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 plan-next — draft gate 2's (Publish) work units

**Objective.** Author gate 2's substantive WU files (CI build + OIDC trusted
publishing + first tagged release + version-skew check), wire them into `PLAN.md`'s
gate-2 `work_units` graph with real `depends_on` edges, generate gate 2's closing
sequence (`G2-CLOSE-INTERMEDIATE` + `G2-PLAN`, since gate 2 is non-terminal), and write
`GATE-01-REVIEW.md`.

**Context.** This is `FEAT-2026-0019/G1-PLAN`, following G1-CLOSE-INTERMEDIATE. It
drafts gate 2 from gate 1's retrospective + the `PLAN.md` forward-arc note. Gate 1
delivered the pip-installable `specfuse.loop` package; gate 2 publishes it. Read the
roadmap detail for FEAT-2026-0019 (Goal — Part A's CI publish path and version-compat
bullets) as the spec ground. `plan-next` takes the strongest model and is forward
design — see `docs/methodology.md` §7.

Gate 2's expected scope (refine against the retrospective; re-scope loudly if needed):

- **Wheel + sdist build in CI** — GitHub Actions job building both, running the full
  test suite against the built artifact (not just the source tree).
- **OIDC trusted publishing** — publish to PyPI on a tag matching `v[0-9]+.*`; trusted
  publishing (OIDC) preferred over API tokens. Sequence the publish so a tag triggers
  build → test → publish.
- **Version-skew check** — `DRIVER_VERSION` (already in the driver) vs a new
  `.specfuse/VERSION` carrying `MIN_SCAFFOLD_VERSION`, compared at startup;
  mismatch → fail-loud with the fix command. (Deferred here from gate 1.)

**Acceptance criteria.**

1. **Gate 2 WU files authored** under the feature folder (e.g.
   `WU-04-*.md`, `WU-05-*.md`, …) — each a dispatchable WU with all five mandatory
   sections, `status: draft` (unarmed), and a `planned_cost_usd`. Per-WU craft per
   `/authoring-work-units`; implementation WUs that add behavior carry a red-test (or
   an explicit §12 exemption).
2. **`PLAN.md` gate-2 graph updated** — real `id`/`file`/`depends_on` for each gate-2
   WU, plus the 2-WU closing sequence `G2-CLOSE-INTERMEDIATE` (depends on all gate-2
   substantive WUs) and `G2-PLAN` (depends on `G2-CLOSE-INTERMEDIATE`). Gate 4's
   terminal `G4-CLOSE` scaffold is left intact.
3. **`GATE-01-REVIEW.md` written** — weighted toward doubt: the decisions and their
   rationale, an explicit "if you check only three things, check these" list, a
   roadmap-anchor check against `roadmap_goal` (flag loudly if the goal seems to be
   drifting), and open questions, each mapped to the draft WU it affects.
4. **Lint clean** — `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0019-distribution`
   passes (the drafted WUs satisfy the five-section contract).
5. **No arming** — gate 2's WUs stay `draft`; arming is the human's act at review.

**Do not touch.** Gate 1's WUs and `GATE-01.md` status (the driver owns gate flips);
already-passed work; `specfuse/loop/` code; secrets; `.git/`. This WU drafts gate 2
only — it does not detail gates 3–4 (their prior gate's plan-next does that).

**Verification.** `plannext` gate set (the linter, AC4) + AC1–AC3 existence checks. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If gate 1's retrospective implies the `roadmap_goal` or the
gate arc should change (e.g. OIDC trusted publishing isn't viable for this org, or the
offline-vendored deferral must pull forward into gate 2), surface it loudly in
`GATE-01-REVIEW.md` and emit `status: blocked` if it blocks a coherent gate-2 draft.
Do not silently re-scope a not-yet-reached gate without flagging it.
