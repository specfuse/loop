---
feature_id: FEAT-2026-0015
gate: 1
correlation_id: FEAT-2026-0015/G1-PLAN
---

# Gate 1 review — Closing-ceremony restructure + hollow-pass guard

## What Gate 1 delivered

Gate 1 landed the MECHANICS for the new closing-WU taxonomy:

- **T01 (`loop.py`).** Added `close-intermediate` to `MODEL_BY_TYPE`
  (`opus`), `EFFORT_BY_TYPE` (`high`), and `GATES_FOR_TYPE`
  (`plannext`). Extended `close` semantics to any terminal gate
  (single- or multi-gate). Existing entries untouched.
- **T02 (`lint_plan.py`).** Added `NEW_INTERMEDIATE_SEQUENCE =
  ["close-intermediate", "plan-next"]`. Updated `_CLOSING_TYPES`
  to include `close-intermediate`. Per-gate shape check accepts:
  2-WU `close-intermediate → plan-next` (non-terminal), 1-WU
  `close` (terminal, any feature size), legacy 4-WU sequence
  (warn). Mixed-shape per-feature emits hard ERROR.
- **T02H (`correlation-ids.md`).** Extended `CORRELATION_ID_RE`
  with `CLOSE-INTERMEDIATE|CLOSE` (longest-first). Updated rule
  prose. Three new tests + one rejection test.
- **T03 (templates + skill).** Updated `PLAN.template.md`,
  `WU.template.md`, `/draft-feature` skill, and added
  `tests/test_template_closing_shapes.py` to assert templates
  lint-clean once rendered.

Closing-ceremony shape contract is now installed end-to-end at the
mechanics layer: drivers route, lint accepts the new shapes (warns
on legacy), correlation IDs validate, templates emit the new shape
by default. **NOT YET INSTALLED:** verdict gating, oracle env
parity, planned-cost capture, state-flip ownership, hollow-pass
guard for closing types.

## What Gate 2 MUST deliver

Per PLAN.md `roadmap_goal` and the roadmap detail's five subsections
(Verdict-state ↔ PLAN.md coupling / Oracle env-parity declaration /
Planned-cost capture / State-flip ownership consolidation / Subsumed
hollow-pass guard):

1. **Verdict coupling (T04).** New WU frontmatter field
   `verdict: met | met_locally | partially_met | not_met` on `close`
   / `close-intermediate` WUs. Driver-side: only `verdict: met`
   permits the terminal flips (PLAN done / gate passed / roadmap
   done). Other verdicts keep state in close-pending limbo; `not_met`
   emits `status: blocked`. Read at squash time, BEFORE the flip.
2. **Oracle env-parity (T05).** New WU frontmatter field
   `oracle_env: macos_local | linux_docker | github_actions_ci |
   <named>`. Lint warns when an AC mentions an oracle-like verb
   ("test loop", "audit", "run N times") and no `oracle_env`
   declared. Close ceremony refuses `verdict: met` if any
   load-bearing AC's `oracle_env` doesn't match goal env.
3. **State-flip consolidation (T06).** Move terminal flips
   (`GATE-NN.md status: awaiting_review → passed`, roadmap row
   `active → done`, `auto_archive_feature` invocation) out of
   `/wrap-feature` and into the `close` WU's driver-side
   post-verify flow, conditional on `verdict: met`. Shrink
   `/wrap-feature` to: read RETRO recap, push branch, open PR,
   merge advisory, next pick. No state flips.
4. **Hollow-pass guard (T07).** Type-keyed assertion table in
   `loop.py` extending FEAT-2026-0008's three implementation
   guards (zero-token, files_changed, smoke-import). One row each
   for `close`, `close-intermediate`, `plan-next`. Fired between
   successful verify+squash and the status-flip-to-done.
   `closing_deliverable_missing` outcome rolls back via
   `git reset --hard head_before`; counts as verification failure
   in the attempt loop.
5. **Planned-cost capture (T08).** WU frontmatter
   `planned_cost_usd: <float>` (already dogfooded informally in
   this feature; T08 formalizes). PLAN.md frontmatter
   `planned_cost_usd: <float>` (sum of WU plans, lint warns on
   mismatch > 10%). Required `## Cost analysis` section in the
   `close` WU's RETRO output (computed from `events.jsonl`).
6. **G2-CLOSE (new contract).** Single `type: close` WU exercising
   the full new contract: RETRO Gate 2 section, LEARNINGS append,
   docs/roadmap reconciled, feature-arc verdict, `## Cost
   analysis`, state-flips (per T06), and a recursive run of T07's
   hollow-pass guard against ITS OWN deliverables. Per
   `[FEAT-2026-0008/G1-CLOSE]` the guard MUST fire against the
   close itself.

## Verdict on scope

**Retain all six WUs (T04–T08 + G2-CLOSE). Do not defer.**

- Five substantive units (T04–T08) is at the upper edge of
  G1-LESSONS' "let work drive the WU count" guidance but NOT
  above. None is padding; each maps to a distinct subsection of
  the roadmap detail.
- Per `[FEAT-2026-0003/G4-LESSONS]` scope test: each unit
  completes in hours; each has contiguous proof (mechanics
  shipped in G1); the trigger is the roadmap's explicit five-
  topic enumeration. All three tests pass.
- G2-CLOSE is non-negotiable: PLAN.md `roadmap_goal` explicitly
  names "Recursive dogfood: this feature's own terminal close
  uses the new contract." Falling back to a 4-WU legacy close
  would invalidate the load-bearing test (per Escalation
  Trigger 3 of this very WU).
- Six WUs is within the gate-1 actual count of four substantive
  + four closing (with T02H), so capacity is precedented.

**No deferral.** Verdict coupling, oracle env-parity, state-flip
consolidation, and planned-cost capture are SEMANTICALLY
LINKED — splitting them across features would re-pay close
ceremonies on partial state. Hollow-pass guard MUST land here
because PLAN.md explicitly subsumes FEAT-2026-0012 and the
recursive dogfood requires it.

## Cross-repo contracts

Per `[FEAT-2026-0003/G3-LESSONS]` and authoring-work-units §8:
Gate 2 introduces load-bearing strings that will be referenced
across multiple files. Enumerate them here so the human can
verify before arming.

| Value | Source of truth | Notes |
|-------|-----------------|-------|
| `verdict` field name | this feature (T04 introduces) | Used in: close-WU frontmatter, `loop.py` verdict-gate check, `lint_plan.py` verdict-enum validation. Lock at T04 spec. |
| Allowed verdict values: `met`, `met_locally`, `partially_met`, `not_met` | this feature (T04) | Quote verbatim in T04, T07 (guard fires conditional on verdict), G2-CLOSE (must use one). |
| `oracle_env` field name | this feature (T05) | WU frontmatter + AC inline directive. Lock at T05. |
| Allowed `oracle_env` values: `macos_local`, `linux_docker`, `github_actions_ci`, plus operator-named string | this feature (T05) + LEARNINGS `[FEAT-2026-0013/G1-CLOSE]` | The fourth named-string form lets operators declare a CI image not yet standardized. |
| `closing_deliverable_missing` attempt-outcome event payload key | this feature (T07) | Parallel to FEAT-2026-0008's `files_changed_mismatch` / `smoke_import_failed`. Lock at T07; events.jsonl consumers (gate-status, retro WUs) read it. |
| `planned_cost_usd` frontmatter field name | this feature (T08), prior informal use in PLAN.md FEAT-2026-0015 | Lint warning text references it; close-WU `## Cost analysis` reads it. |
| `## Cost analysis` section heading (exact bytes) | this feature (T08) | G2-CLOSE writes this section into RETROSPECTIVE.md; T08's spec requires this exact heading. Per `[FEAT-2026-0010/G1]` foundation-WU string discipline. |
| `auto_archive_feature` function name | `.specfuse/scripts/loop.py` (already exists, T06 moves call-site) | T06 moves the invocation; no rename. |

These are all COMPONENT-LOCAL to this repo — no external
orchestrator surface, no GitHub-side vocabulary, no MCP
namespace. Verification is `grep` against the named source-of-
truth at arm time. No external-system probe required.

## Open questions for arm time

1. **T04 ↔ T07 timing.** T07's guard for `close` / `close-
   intermediate` includes "verdict field exists and is one of
   the allowed values." T07 depends on T04 (verdict lexicon
   must exist first). The dependency graph in PLAN.md must
   reflect this.
2. **T05 lint warning vs T07 hollow-pass guard interaction.**
   T05 emits LINT WARN on a missing `oracle_env`; T07's guard
   asserts the close-WU has run an env-parity check. These are
   distinct surfaces (lint = static, guard = post-verify) and
   should not be conflated.
3. **T06 wrap-feature regression test surface.** Moving flips
   out of `/wrap-feature` means existing wrap-feature
   integration tests (if any) need their assertions inverted.
   T06 spec must enumerate them per §10 helper-duplication.

## Block: lint contradicts the recursive-dogfood design

**Status — G1-PLAN attempt 2 (this session): emitting
`status: blocked`.**

PLAN.md (line 91–94) declares that THIS feature dogfoods both
closing shapes within the same feature:

- Gate 1 uses the LEGACY 4-WU sequence (G1-RETRO/LESSONS/DOCS/PLAN)
  — already executed and committed (commits `90e4a2d`, `00f97c2`,
  `f2d0b8c`).
- Gate 2 uses the NEW `type: close` contract — the load-bearing
  recursive dogfood.

T02 (`lint_plan.py`, commit `52a176a`) implemented AC #4
verbatim:

> "Mixed shapes within a single feature emit a hard ERROR:
> `ERROR: <feature_dir>: mixed closing-shape contracts across
> gates (gate N uses NEW, gate M uses LEGACY). Pick one contract
> per feature.`"

The mixed-shape check is correct per T02's spec but the T02 spec
contradicts PLAN.md's design intent. Concretely:

| Path forward | Outcome |
|--------------|---------|
| Populate `gates[1].work_units` with the NEW `close` shape (per AC2 + Escalation Trigger 3) | Lint ERROR — mixed-shape across gates |
| Populate `gates[1].work_units` with a LEGACY 4-WU sequence on Gate 2 | Lint OK but violates this WU's Escalation Trigger 3 ("falling back invalidates the load-bearing test") |
| Leave `gates[1].work_units` empty | AC2 of this WU unmet |

No path satisfies (this WU's AC2) ∧ (this WU's Trigger 3) ∧
(T02's mixed-shape ERROR). G1-PLAN's `Do not touch` forbids
modifying `lint_plan.py`, so the contradiction cannot be
resolved inside this WU's boundary.

### Recommended resolution path (operator decision)

Pick one. All three are small follow-on changes that need to
land BEFORE Gate 2 dispatch can proceed.

1. **Relax the cross-gate mixed-shape check** in `lint_plan.py`
   to a WARN (not ERROR). Rationale: the check was designed to
   prevent operator confusion, but the legitimate transition-
   feature pattern (this feature itself) needs the mixed shape
   exemption. A WARN preserves the signal without blocking.
   *Smallest diff; preserves T02 intent qualitatively.*
2. **Add a PLAN.md frontmatter flag** `transition_feature: true`
   that exempts the feature from the mixed-shape ERROR. More
   surgical but adds a new lint-recognized field.
3. **Drop the cross-gate mixed-shape check entirely.** Per
   `[FEAT-2026-0003/G4-LESSONS]` "let work drive the WU count" —
   the check is hypothetical operator-confusion prevention with
   no incident evidence behind it. Removing reverts T02 AC #4
   only. *Smallest implementation; biggest reversal of T02
   spec.*

Author's recommendation: **option 1** (WARN not ERROR). The
existing WARN on legacy 4-WU sequences is already the
documentation surface; layering "and you're mixing them" onto
the same WARN gives operators the same nudge without blocking
legitimate transition features.

Once one of these lands as a tiny hygiene WU (`T02H2`,
analogous to T02H for correlation-IDs), this WU's third attempt
can populate `gates[1].work_units` and complete cleanly.

### Drafted artifacts that survive across the reset

The following are on disk (untracked) and ready for the next
G1-PLAN attempt to wire into PLAN.md:

- `WU-04-verdict-coupling.md` (T04, status: draft)
- `WU-05-oracle-env-parity.md` (T05, status: draft)
- `WU-06-state-flip-consolidation.md` (T06, status: draft)
- `WU-07-hollow-pass-guard.md` (T07, status: draft)
- `WU-08-planned-cost-capture.md` (T08, status: draft)
- `WU-94-gate-2-close.md` (G2-CLOSE, status: draft, NEW
  `type: close` contract)
- This `GATE-01-REVIEW.md`

Proposed `gates[1].work_units` graph (for the post-fix attempt):

```yaml
- gate: 2
  file: GATE-02.md
  work_units:
    - id: FEAT-2026-0015/T04
      file: WU-04-verdict-coupling.md
      depends_on: []
    - id: FEAT-2026-0015/T05
      file: WU-05-oracle-env-parity.md
      depends_on:
        - FEAT-2026-0015/T04
    - id: FEAT-2026-0015/T06
      file: WU-06-state-flip-consolidation.md
      depends_on:
        - FEAT-2026-0015/T04
    - id: FEAT-2026-0015/T07
      file: WU-07-hollow-pass-guard.md
      depends_on:
        - FEAT-2026-0015/T04
    - id: FEAT-2026-0015/T08
      file: WU-08-planned-cost-capture.md
      depends_on: []
    - id: FEAT-2026-0015/G2-CLOSE
      file: WU-94-gate-2-close.md
      depends_on:
        - FEAT-2026-0015/T04
        - FEAT-2026-0015/T05
        - FEAT-2026-0015/T06
        - FEAT-2026-0015/T07
        - FEAT-2026-0015/T08
```

Six WUs total (five substantive + one new-contract close) —
within Escalation Trigger 1's "≤6 substantive" budget.
