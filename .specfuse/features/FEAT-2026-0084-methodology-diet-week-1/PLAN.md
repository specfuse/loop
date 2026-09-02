---
feature_id: FEAT-2026-0084
title: Methodology diet, week 1 — prune rules, shrink work units, lint unobservable criteria, single gate to 8
slug: methodology-diet-week-1
branch: feat/FEAT-2026-0084-methodology-diet-week-1
roadmap_goal: The next three features drafted after merge carry work units of 45 lines or fewer, every acceptance criterion names a check the loop can run, features of up to 8 substantive units draft as one gate, and every dispatch loads at most 2,500 words of binding rules.
autonomy_default: review
status: planned
planned_cost_usd: 24.00
---

# Plan: Methodology diet, week 1

A review of 273 features across 12 repositories (2026-09-01) found that 48% of
features with a verdict end hedged, that the hedge rate rose as ceremony
accreted (generator repo: 4 of 18 hedged in its earliest quartile, 15 of 18 in
its latest), and that 72 of 101 hedges trace to acceptance criteria asking the
loop to observe something it cannot reach — production, another repository, a
human signature. Every dispatch also carries roughly 50K tokens of fixed
context, 7,213 words of which are the seven rules included through
`.claude/CLAUDE.md`; a typical work unit body is 94 lines against a 199-line
template and a 571-line authoring skill.

This feature is the first week of the proposed correction: the four changes that
need no driver behaviour change. It prunes the included rules to a ceiling
(T01), shrinks the work-unit template and authoring skill (T02), adds a lint that
refuses acceptance criteria the loop cannot observe (T03), and raises the
single-gate threshold from 4 to 8 substantive units (T04). The binary verdict,
the separate judge, verification tiers, keep-diff retries, parallel dispatch, and
the retrospective replacement are later features.

## Scope boundary

**IN.** The seven `@`-included rules and the include block that ships them;
`WU.template.md`; `authoring-work-units/SKILL.md`; one new `lint_plan` ERROR/WARN
rule plus one draft-feature interview question; the proportionality threshold
and one new `lint_plan` WARN.

**OUT, deliberately.**

- Removing `met_locally` / `partially_met`, the follow-up `kind:` taxonomy, or
  `/accept-hedged-close`. That is the binary-verdict feature.
- Making `autonomy_default: auto` or auto-arm the default. Auto-close seeds every
  criterion of an auto-closed gate into "What the loop did NOT verify" as debt
  the terminal close must reconcile (FEAT-2026-0050's retrospective lists 19);
  that is a hedge generator and must be fixed with the verdict change, not
  before it.
- Any change to `verify()`, the gate sets, the baseline probe, the attempt
  reset, or dispatch ordering in `loop.py`.
- Converting existing feature folders or existing work units to the new shape.
  The lint must keep accepting the 327 existing bodies as they are.
- `close-discipline.md` and `planning-discipline.md`. They are not in the
  dispatch include set; they are the next feature's subject.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -n "oracle_env" specfuse/loop/lint_plan.py
  -> :1648  WARN when the AC section mentions oracle verbs and the WU lacks oracle_env.
     Adjacent heuristic over the same section; T03 reuses its slicer
     (_slice_ac_section, :161) and its WARN plumbing, adds a sibling rule.

grep -n "arm-sweep-gate" .specfuse/verification.yml
  -> :80  the corpus-wide lint sweep already runs as a driver gate. T03's rule
     joins it by living inside lint_plan; no new gate.

grep -rn "proportional" specfuse/loop/lint_plan.py
  -> 0 hits. No lint enforces the single-gate threshold today; T04 adds a WARN.

grep -rn "≤ 4" docs/methodology.md .specfuse/skills/draft-feature/SKILL.md
  -> docs/methodology.md:346-369 (the one home), draft-feature/SKILL.md:190 (reference).

grep -n "_RULES_BLOCK" specfuse/loop/scaffold.py
  -> :226  the include block is generated from one constant; T01 edits it there.
```

**Verdict: extending three existing mechanisms (the AC slicer and its WARN
plumbing, the arm sweep gate, the scaffold include block), building one small new
one (the observability rule) and one WARN.**

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

T03 adds an ERROR-level rule. **What does the rule report on an input already in
its intended final state?** Zero. The rule fires only on a bullet in the
acceptance-criteria section that both matches an unobservable phrase and carries
no backticked command, path, or test id; a criterion in its intended final state
names its check in backticks. The rule skips `done` work units, so the existing
corpus (whose hedged features carry exactly such criteria) reports zero, and
T03's acceptance requires the sweep to prove it before the rule ships at ERROR.
Escape hatches for a criterion that is honestly unobservable here: `oracle_env`
naming a non-local environment, or `human_only: true`.

T04's rule is WARN-only; no predicate to satisfy.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0084/T01
        file: WU-01-prune-included-rules.md
        depends_on: []
      - id: FEAT-2026-0084/T02
        file: WU-02-shrink-wu-template-and-authoring-skill.md
        depends_on: []
      - id: FEAT-2026-0084/T03
        file: WU-03-lint-ac-observable.md
        depends_on: []
      - id: FEAT-2026-0084/T04
        file: WU-04-single-gate-threshold-8.md
        depends_on: [FEAT-2026-0084/T03]
      # --- terminal gate: single close WU ---
      - id: FEAT-2026-0084/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0084/T01
          - FEAT-2026-0084/T02
          - FEAT-2026-0084/T03
          - FEAT-2026-0084/T04
```

## Notes

- **Single-gate feature** (4 substantive WUs): one terminal `close`, no
  `close-intermediate`, no `plan-next` (`docs/methodology.md` §6).
- **This feature's work units are written in the shape T02 prescribes**: five
  bold sections, about 40 lines, no restated rules. If they cannot be executed
  from that shape, T02's ceiling is wrong and the close must say so.
- **Canonical locations.** Skills are edited under `plugins/specfuse/skills/`
  and synced to `.specfuse/skills/` (`scripts/sync-scaffold.sh`,
  `tests/test_skills_vendored_in_sync.py`). Rules, templates and docs are edited
  under `.specfuse/` and `docs/` and synced to `specfuse/loop/data/`
  (`tests/test_scaffold_data_in_sync.py`). Every WU here runs the sync script
  before reporting.
- **T04 depends on T03** only because both edit `draft-feature/SKILL.md` and
  `lint_plan.py`; serialising them avoids a squash conflict, not a logical
  dependency.
- **Measurement baseline** for the close: included rules 889 lines / 7,213
  words; `WU.template.md` 199 lines; `authoring-work-units/SKILL.md` 571 lines;
  threshold 4; `lint_plan` rules that mention observability: 0.
