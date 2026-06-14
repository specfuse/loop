# Gate-3 review — drafted by G2-PLAN

This document is the operator's pre-arm review for gate 3 of
`FEAT-2026-0018-auto-close-predicate`. Flip each gate-3 WU from
`status: draft` → `pending` only after working the Open verifications
+ Cross-repo contracts sections.

## Gate-2 summary

Gate 2 wired the gate-1 module into `loop.py` and added two operator
escape surfaces. Three substantive WUs landed in 2 attempts each:
**T04** (`maybe_auto_close_terminal`,
`write_stub_retrospective_terminal`, `mark_close_wu_auto_closed` —
terminal-gate path with the FEAT-2026-0017 invariant-guard
preservation), **T05** (`maybe_auto_close_intermediate`,
`append_stub_retrospective_intermediate` — intermediate-gate path,
option A: plan-next still dispatches), and **T06** (`--force-full-close
<feature-id>` CLI flag, `auto_close_disabled: true` PLAN.md frontmatter
override, `resolve_auto_close_override` precedence). No `blocked_human`
escalations; no `replan` events. Gate-2 budget was raised at arm time
from $9.00 → $16.00 anchored to gate-1's 2.14× actual ratio.

Gate-2 substantive spend: $9.04 actual vs $5.50 planned (1.64× over).
Driver of overrun: T04 and T06 both wired into multiple sites
(T04: stub-retro write + flips + close-WU frontmatter; T06: override at
both T04 and T05 call sites) but effort bands priced one-piece work.
T05 came in 1.21× (re-used T04's scaffolding), confirming the pattern
is site-count × effort-band misclassification, not estimation noise.

**Predicate self-check** (T03's CLI run on this feature, gate 2 — the
recursive-dogfood property continues to validate the deliverable):

```
FEAT-2026-0018  predicate=v1
  G02  auto=False
    reasons:
      - per_wu_cost_overrun: T04 actual=$4.10 planned=$2.50 ratio=1.64x
      - per_wu_cost_overrun: T06 actual=$2.29 planned=$0.80 ratio=2.86x
      - per_wu_hard_overrun: T06 actual=$2.29 planned=$0.80 ratio=2.86x
    metrics:
      gate_total_cost: $12.01
      gate_budget: $16.00
```

Meta-confirmation: the predicate this feature ships correctly
identifies gate 2 as off-plan; close-intermediate ceremony was
warranted; gate-2 budget (raised to $16) was not tripped (criterion 6
holds).

## Gate-3 substantive WUs

### T07 — Plan-next-draft lint extension + driver hook ($1.00, medium)

Adds `lint_plan_next_draft(feature_dir, just_closed_gate) → list[str]`
to `lint_plan.py` — a focused pass that walks the next-gate draft
cohort a `plan-next` WU just authored and surfaces the gaps the
general pass already detects, plus a few next-gate-specific ones
(empty section bodies, missing `planned_cost_usd`,
`produces_driver_helper` absence on driver-wiring drafts). Driver hook
in `loop.py`'s PASS branch fires after `assert_closing_deliverables` /
before `task_completed` for `wu.type == "plan-next"` — warn-only v1
per PLAN.md. CLI flag `--just-closed-gate N` exposes the pass for
ad-hoc use. Unit tests cover clean / missing-fields / driver-wiring-
without-PDH / terminal-gate-no-next-gate edge cases. Depends on no
other gate-3 WU (independent surface).

### T08 — /wrap-feature skill trim ($0.40, low)

Strips `wrap-feature/SKILL.md` Method §§ 2–3 (executive recap +
manual-verification step). The auto-close path stub RETROSPECTIVE.md
shape (`## Gate N — auto-closed (predicate=v1)` + 5-line YAML metrics)
has no `# Feature-arc verdict` section; the recap reads against shapes
auto-close features don't produce. Trim keeps push + PR + CI watch +
next-pick. New hard rule: `wrap-feature` MUST NOT assume RETROSPECTIVE
carries a feature-arc verdict. Version bump v0.2 → v0.3. No code
changes; pure skill-prose edit. Independent of T07.

### T09 — /migrate-to-auto-close skill ($1.20, medium)

New skill at `.specfuse/skills/migrate-to-auto-close/SKILL.md`. Scans
a Specfuse project's `.specfuse/features/`, identifies features whose
PLAN.md predates the auto-close path, runs `gate_eval.py backtest`
per feature, and surfaces a per-feature recommended action. Opt-in:
skill may write ONLY the `auto_close_disabled: true` frontmatter
field, and only after a per-feature y/n confirm. No multi-field
PLAN.md mutation; no auto-rewrites. Six hard rules + six method
steps. Independent of T07/T08.

### T10 — docs/methodology.md auto-close section + /draft-feature template tweak ($0.30, docs/low)

Appends a `### Deterministic auto-close path (FEAT-2026-0018)`
section to `docs/methodology.md` (around line 80, after existing
`close` / `close-intermediate` documentation). Quotes the seven-check
predicate from PLAN.md verbatim. Describes auto-close terminal,
auto-close intermediate (option A), override surfaces, and
predicate-version transparency. Lightly nudges
`/draft-feature/SKILL.md` to mention `evaluate_auto_close` in the
cost-table guidance. Depends on T09 (the skill T9 ships is one of
the surfaces methodology.md will reference).

## Open verifications

Operator should check / resolve each before flipping gate-3 WUs
from `draft` → `pending`.

1. **Gate-3 budget realism.** GATE-03.md declares
   `cost_budget_usd: 4.50`. Gate-1 ran at 2.32× plan; gate-2 ran at
   1.64× plan. Applying gate-2's lower ratio to gate-3's $2.90
   substantive plan → ~$4.76 substantive spend, plus `G3-CLOSE`
   $1.50 → ~$6.26 — already over the $4.50 budget. Two options:
   - **Recommended:** raise GATE-03.md `cost_budget_usd` to $8.00
     pre-arm, anchored to the same ratio gate-2 saw. Annotate the
     raise in GATE-03.md frontmatter (per the pattern used on
     GATE-02.md and GATE-01.md when those were raised mid-flight).
     This keeps criterion 6 evaluable and lets gate-3 either
     auto-close cleanly OR refuse with criterion-3/4 reasons only,
     not criterion-6 budget noise.
   - **Alternative:** leave $4.50, accept that criterion 6 will
     refuse auto-close on gate 3 (predicate will name budget +
     per-WU ratios as joint reasons). The recursive-dogfood
     property still holds; only the predicate's reason list grows.

2. **T07 driver-hook site precise location.** T07 specifies the
   hook lands in `loop.py`'s PASS branch between
   `assert_closing_deliverables` and `wu_events.append(
   "task_completed", ...)`. Confirmed at draft time: the PASS
   branch is at `loop.py:2110–2198`;
   `assert_closing_deliverables` call at ~line 2147 and
   `task_completed` append at ~line 2191. `loop.py` evolves;
   re-verify the line range when arming T07. Update T07's body
   if it has drifted.

3. **T07 reuse of `read_frontmatter` / `_miniyaml`.** T07's lint
   helpers must import the existing `read_frontmatter` (loop.py)
   and `_miniyaml` — they are the canonical PLAN.md / WU
   frontmatter readers. Confirm at arm time the import paths
   resolve from `.specfuse/scripts/lint_plan.py`'s module
   context (it already imports `_miniyaml` per `lint_plan.py:37`
   — verified).

4. **T08 trigger-phrase preservation.** The
   `wrap-feature/SKILL.md` `description:` field is the agent's
   discovery surface. If T08's tightened copy drops the trigger
   strings agents look for ("wrap-feature", "/wrap-feature",
   "wrap the feature"), the slash command stops working.
   T08 AC6 says preserve them; operator should re-read the
   final description copy at arm time and verify.

5. **T09 skill discovery via `.claude/skills/` symlink.** Per
   `.claude/CLAUDE.md`: "Skills under `.claude/skills/` are
   symlinks into `.specfuse/skills/` so Claude Code's discovery
   picks them up." Confirm at arm time:
   `test -L .claude/skills/migrate-to-auto-close ||
   ls -la .claude/skills/ | grep -q migrate-to-auto-close`. If
   the symlink isn't auto-maintained on new skills, T09 may
   need a manual step OR another skill (e.g.
   `update-config`) to wire it. Non-blocking for T09 itself.

6. **T10 docs/methodology.md insertion location.** T10's
   insertion target is "around line 80, after existing `close` /
   `close-intermediate` documentation." Confirmed at draft time
   that the `close` definition lives at lines 68–80 of
   methodology.md. If lines have shifted, T10's escalation
   trigger #2 covers it.

7. **T10 /draft-feature template tweak — locating cost-table
   guidance.** T10 says "search for `planned_cost_usd`" in
   `draft-feature/SKILL.md`. If the skill has been restructured
   and the cost-table guidance area no longer exists, T10's
   escalation trigger #3 fires. Pre-check at arm time:
   `grep -nq 'planned_cost_usd' .specfuse/skills/draft-feature/SKILL.md`.

8. **G3-CLOSE recursive-dogfood expectation.** Gate 3's WUs are
   relatively small + independent (T07/T08/T09 have no inter-
   dependencies; only T10 → T09). Best-case predicted ratio < 1.5×
   on each → predicate auto-closes gate 3 → THIS-WU dispatch
   skipped → stub RETROSPECTIVE.md written. Worst-case (T07's
   driver-wiring or T09's new skill goes 2+ attempts): predicate
   refuses → ceremony path → `G3-CLOSE` dispatches with full
   retrospective. EITHER OUTCOME is the recursive-dogfood
   evidence the PLAN.md § Notes asks for. Document which path
   fired in G3-CLOSE's `# Feature-arc verdict` section.

9. **Verdict requirement on terminal close.** Per
   FEAT-2026-0015/G2-CLOSE LEARNINGS,
   `verdict: met` (or `met_locally` / `partially_met` / `not_met`)
   MUST be written to `WU-90-gate-3-close.md` frontmatter.
   `fire_terminal_flips` reads it; absence silently bypasses the
   terminal-flip path. AC8 of G3-CLOSE names this; operator
   should verify the verdict-vs-deliverable mapping at gate close
   (not at arm time).

## Cross-repo contracts

Per `[FEAT-2026-0003/G3-LESSONS]`. For this gate, all surfaces are
internal to the loop's single repo; "cross-repo" reduces to
"cross-WU values invented at draft time that future code/tooling
will join on". Each row must be operator-checked before arming.

| Invented value | Authoritative source | Used in | Checked |
|---|---|---|---|
| function name `lint_plan_next_draft` | invented this gate; mirrors `lint_plan` naming | T07 AC1, AC6 | [ ] |
| CLI flag `--just-closed-gate <N>` on `lint_plan.py` | invented this gate; mirrors `--force-full-close` shape on `loop.py` (T06) | T07 AC3 | [ ] |
| event type `plan_next_draft_lint` | invented this gate; precedent: `auto_close_decision` from T04 (also invented) | T07 AC2 | [ ] |
| event field `blocking: bool` on lint-event payload | invented this gate; semantic: future v2 may flip to `true` | T07 AC2 | [ ] |
| skill name `migrate-to-auto-close` | invented this feature's PLAN.md "Scope OUT" | T09 AC1 | [ ] |
| skill triggers `"/migrate-to-auto-close"`, `"migrate to auto-close"`, `"audit auto-close eligibility"` | invented this gate | T09 AC1 (description) | [ ] |
| wrap-feature hard rule "Auto-close and full-ceremony features both supported" | invented this gate | T08 AC4 | [ ] |
| methodology.md heading `### Deterministic auto-close path (FEAT-2026-0018)` | invented this gate; mirrors existing methodology heading style | T10 AC1, AC6 | [ ] |
| methodology.md content — quoting PLAN.md's seven checks | source: PLAN.md § "Predicate v1" (this feature's own design) | T10 AC1 | [x] |
| `/draft-feature` template paragraph referencing `evaluate_auto_close` | source: gate_eval.py:292+ (the predicate's symbol surface) | T10 AC4 | [x] |
| G3-CLOSE verdict semantics (met / met_locally / partially_met / not_met) | source: FEAT-2026-0015/G2-CLOSE LEARNINGS + `VERDICT_VALUES` in loop.py | G3-CLOSE AC7 | [x] |

Each unchecked row is a value the arming operator should grep the
codebase + LEARNINGS for, to confirm no naming collision with an
existing convention. Three rows are pre-checked because their
sources are this feature's own already-shipped artifacts
(PLAN.md § Predicate v1, gate_eval.py, loop.py).

## Predicate-version note

This review is written against `predicate=v1`. Constants
(`PER_WU_COST_RATIO_CEILING = 1.5`, `PER_WU_HARD_OVERRUN_RATIO =
2.0`, `PLAN_NEXT_COST_RATIO_CEILING = 1.5`) are hardcoded in
`gate_eval.py`. The `predicate_version` string threads through every
`auto_close_decision` event T04/T05/T06 emit AND every
`plan_next_draft_lint` event T07 emits. Future predicate revisions
(v2+) remain auditable retroactively.

## Recursive-dogfood reminder

PLAN.md § Notes: "Gate 3 (lint + skill + docs) is the only realistic
self-test: if G3 goes on-plan, G3-CLOSE auto-fires, $0 close-WU
cost, and the close-WU bypass exercises itself end-to-end against
the terminal-flip path. Documented in G3-CLOSE's verdict regardless
of outcome."

Gates 1 and 2 each ran > 1.5× plan; the predicate this feature ships
correctly refused both. Gate 3's WUs are small and decoupled
(T07/T08/T09 mutually independent; only T10 depends on T09); the
best-case scenario is plausible. The G3-CLOSE WU body (drafted by
this G2-PLAN) carries AC3 instructing the agent to paste the
`gate_eval.py backtest --gate 3` output verbatim into the gate-3
retrospective — that is the single most load-bearing artifact this
close produces, regardless of which path fired.
