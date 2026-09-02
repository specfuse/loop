---
gate: 1
status: awaiting_review
cost_budget_usd: 30.00
baseline:
  sha: 7f7194e9d64fcb6efe1436c5eac02d9305c15690
  probed_at: 2026-09-02T11:43:13.132813+00:00
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: test_real_tree_is_clean_on_all_four_invariants
    - gate: coverage
      failure_class: coverage
      failure_signature: [07:45:37] bug-1 failed after 0s — RuntimeError: boom on bug-1
    - gate: roadmap-link-gate
      failure_class: other
      failure_signature: ERROR: roadmap.md:99: ref '#feat-2026-0084' in roadmap.md does not resolve — no anchor 'feat-2026-00
---

# Gate 1 — the dispatch context is lighter and unobservable criteria cannot be armed

## Definition of done

Stated as measurements, not as four units:

- `wc -w` over the rules `.claude/CLAUDE.md` includes reports at most 2,500
  words, and `operator-escalation.md` / `human-output.md` are no longer in that
  set (here and in the scaffold `scaffold.py` ships).
- `WU.template.md` is at most 70 lines and `authoring-work-units/SKILL.md` at
  most 200; a work unit rendered from the new template passes `lint_plan`, and
  `specfuse lint` still passes on every existing feature folder.
- `specfuse lint` reports ERROR on a `pending` work unit whose acceptance
  criterion reads "applied in prod" with no backticked check, reports nothing on
  the same criterion once the WU carries `oracle_env: github_actions_ci` or
  `human_only: true`, and the corpus sweep over this repository reports zero.
- A feature with 8 substantive units and one gate lints clean; the same feature
  with two gates gets a WARN; `docs/methodology.md` §6 says 8.

If all four units are `done` and any measurement above fails, this gate is not
done.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **T03 raises a check to ERROR.** PLAN.md answers §2: zero on a correct input,
  because `done` units are skipped and a correct criterion carries its check in
  backticks. Before arming, run `specfuse lint` over every feature folder with
  T03's rule applied locally and paste any ERROR into this file; an ERROR on an
  existing non-`done` unit means the phrase list or the skip rule is wrong.
- No flag is introduced or flipped; no flag-scope table applies.
- **The close is load-bearing** (it re-runs the four measurements) and carries
  `auto_close_disabled: true`.

## Reflection notes

<Written by the human at review time.>
