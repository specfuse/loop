---
feature_id: FEAT-2026-0085
title: Binary verdict — met or not_met, follow-ups become tracked issues, human steps become units
slug: binary-verdict
branch: feat/FEAT-2026-0085-binary-verdict
roadmap_goal: A terminal close records exactly met or not_met; a not_met close leaves one tracked follow-up per failed criterion; a criterion that needs a human becomes a unit the driver halts on before the close; and no auto-closed gate seeds unverified debt into the retrospective — measured as zero met_locally or partially_met verdicts and zero accept-hedged-close invocations on features closed after merge.
autonomy_default: review
status: planned
planned_cost_usd: 35.00
---

# Plan: Binary verdict

Across 273 features in 12 repositories, 48% of verdict-bearing features ended
`met_locally` or `partially_met`. 59 of those were later flipped to `met` by
`/accept-hedged-close`, almost always with nothing re-run. Of 101 hedged
features, 42 hedged because a criterion asked the loop to observe production,
14 because the discharging step lived in another repository, 16 because a human
had to sign or act, and 9 because the auto-closed gates had seeded every
criterion into "What the loop did NOT verify" as debt the terminal close could
not reconcile. Only about 13 carried information a hedge is for. No surveyed
external loop uses partial credit: every one records pass or fail per unit and
files a follow-up issue for what it could not finish.

This feature removes the two soft-success verdicts and everything built to
scaffold them, and replaces them with three honest channels: a `not_met` close
that files one tracked follow-up per failed criterion (T03), a `type: human`
work unit the driver halts on so a human step is recorded before the close
rather than hedged after it (T04), and an auto-close stub that states what the
driver's gates proved instead of listing every criterion as deferred (T02).
T01 changes the vocabulary and deletes the hedge machinery; T05 rewrites the
rule, removes the acceptance skill, and documents migration for the 42
standing hedged closes in the field.

**Sequenced after FEAT-2026-0084.** T05 edits `WU.template.md` and the
draft-feature skill after 0084/T02 and 0084/T03 reshape them, and the
single-gate shape here (five substantive units) relies on 0084/T04 raising the
proportionality threshold to 8. Do not arm until 0084 is merged and this
branch is rebased onto `main`.

## Scope boundary

**IN.** `VERDICT_VALUES`, the closing-requirement registry, the verdict guards
and lint messages, the auto-close stubs, a `FOLLOW-UPS.md` artifact and its
issue emission, the `human` work-unit type and its driver halt, the
close-discipline rule, the accept-hedged-close skill's removal, docs, and a
migration note.

**OUT, deliberately.**

- **A separate judge session that decides the verdict.** The close still
  writes the verdict here; moving that to a fresh evaluator is the next
  feature. This one makes the verdict binary so the judge has a binary to
  decide.
- **A feature-level oracle (`feature_oracle`).** Later feature.
- **Rewriting existing hedged closes.** Legacy `met_locally` / `partially_met`
  values stay readable on disk; the guards reject them only on a close
  dispatched from now on. Migration is a documented operator step, not a
  script.
- **The `narrow` / `broad` per-criterion oracle kinds** (`close-discipline.md`
  §5, `GATE-NN-CRITERIA.md`). Unrelated to hedging; they stay.
- **Removing `--recheck-verdict`.** It stays as the one out-of-band caller of
  `fire_terminal_flips`; it is how a migrated legacy close gets its flips.
- **Other repositories' scaffolds.** `specfuse upgrade` delivers the rule and
  the skill removal; their standing hedged features follow the migration note.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -n "VERDICT_VALUES" specfuse/loop/closing_requirements.py
  -> :27  the single spelling every guard imports. T01 narrows it there.

grep -rn "HEDGED_VERDICT_VALUES\|FOLLOW_UP_KIND\|verdict_ceiling_for_kinds" specfuse/ plugins/ tests/ | cut -d: -f1 | sort -u
  -> closing_requirements.py, loop.py (assert_hedged_followup_kinds_classified :5787),
     lint_closing.py (:253), accept-hedged-close/SKILL.md, 4 test files.
     This is the deletion set; nothing else consumes them.

grep -n "autoclose-debt\|DEFERRAL_HEADING" specfuse/loop/loop.py
  -> :3061 precreate seeds the heading; :4899 build_autoclose_debt_enumeration;
     :5026 write_stub_retrospective_terminal; :6308 assert_autoclose_debt_reconciled.
     T02 retires all four together.

grep -rn "def emit_issue_with_body" specfuse/
  -> 0 hits on this branch. FEAT-2026-0082/T01 (done, unmerged) adds it over
     escalation.py's _find_existing_issue / _correlation_marker. T03 calls it if
     present, otherwise adds it over the same helpers — the line 0052/T03 carries.

grep -rn "human_only" specfuse/loop/loop.py
  -> 0 hits. Only arm_eval.py reads it, as an arm-time veto. The driver has no
     notion of a unit a human performs; T04 adds one as a type, not a flag.

grep -n "^DISPATCHABLE" specfuse/loop/loop.py
  -> :326  {"pending", "ready"}. T04's type check sits beside it.
```

**Verdict: narrowing one constant, deleting one mechanism (hedge kinds and
ceiling), retiring one (auto-close debt), reusing one (the idempotent issue
emitter), building two small new ones (`FOLLOW-UPS.md` with its guard, and the
`human` unit type).**

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

T01 narrows what `assert_verdict_well_formed` accepts. **What does it report on
a close already in its final state?** Pass on `met` and `not_met`. It runs only
at outcome time on the close just dispatched, never on a `done` close, and
`lint_plan` validates `verdict` only on non-`done` statuses, so the 42 legacy
hedged closes across the corpus report zero. `recheck_terminal_verdict` reads a
legacy value, refuses the flips exactly as today, and its reason names the
migration note.

T03 adds `close-m` (a `not_met` close must carry `FOLLOW-UPS.md` with at least
one entry). It applies only when the verdict is `not_met`; no `done` close in
the corpus is re-checked. Zero.

T04 adds a lint ERROR for a `done` `human` unit without `evidence`. No `human`
unit exists yet; zero.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0085/T01
        file: WU-01-verdict-vocabulary.md
        depends_on: []
      - id: FEAT-2026-0085/T02
        file: WU-02-auto-close-stops-seeding-debt.md
        depends_on: [FEAT-2026-0085/T01]
      - id: FEAT-2026-0085/T03
        file: WU-03-followups-artifact-and-issues.md
        depends_on: [FEAT-2026-0085/T02]
      - id: FEAT-2026-0085/T04
        file: WU-04-human-work-unit-type.md
        depends_on: [FEAT-2026-0085/T03]
      - id: FEAT-2026-0085/T05
        file: WU-05-rule-skill-docs-migration.md
        depends_on: [FEAT-2026-0085/T04]
      # --- terminal gate: single close WU ---
      - id: FEAT-2026-0085/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0085/T01
          - FEAT-2026-0085/T02
          - FEAT-2026-0085/T03
          - FEAT-2026-0085/T04
          - FEAT-2026-0085/T05
```

## Notes

- **Single gate with five substantive units.** Legal once FEAT-2026-0084/T04
  raises the threshold to 8; that is one reason this feature is blocked by it.
- **The chain is serial** because every unit edits `loop.py` and four edit
  `closing_requirements.py`; the order avoids squash conflicts, not logical
  dependency. T04 could run in parallel with T02 and T03 on a driver that
  fans out.
- **Every unit touching `specfuse/loop/` halts the driver for a restart**
  (`driver_restart_required`). Expect five restarts; each re-probes the
  baseline.
- **Measurement baseline** for the close: `VERDICT_VALUES` has 4 members;
  `grep -rl "met_locally"` over `specfuse/ plugins/ docs/ .specfuse/rules .specfuse/templates tests/` names 38 files; 22 test files reference hedge machinery; standing hedged closes in this repository: run `grep -l "^verdict: met_locally\|^verdict: partially_met" .specfuse/features/*/WU-9*.md` at close and record the count.
- **What this feature does not fix, said once.** A close can still write `met`
  on a feature that is not wired end to end. That is the feature oracle's job,
  and it comes after the judge.
