---
feature_id: FEAT-2026-0114
title: Amend `produces:` at the guard — a verified attempt renegotiates its declaration instead of spinning
slug: produces-amendable-at-the-guard
branch: feat/FEAT-2026-0114-produces-amendable-at-the-guard
roadmap_goal: An attempt that passed verification but did not touch a declared `produces:` path amends the declaration in its RESULT and passes, and an identical refusal never runs a third time.
autonomy_default: auto
status: planned
planned_cost_usd: 22.00
---

# Plan: Amend `produces:` at the guard

`produces:` is written at planning time, before anyone has seen the solution.
When the emergent solution lands somewhere else, the driver's
`resolve_produces_refusal` guard refuses the pass with `produces_not_in_diff`,
and the unit has no way to say "the plan named the wrong file". The 2026-09-26
impact assessment (`reviews/2026-09-26-impact-assessment/`, private) found this
to be the single largest mechanical spinner in the post-review corpus: five of
the six units since 2026-09-10 that failed three times with an identical
signature failed on this guard (FEAT-2026-0063/T02, 0153/T04, 0159/T02,
0173/T02, 0177/T02, 0185/T02 across two repositories). In every one, attempt 1
did real work that `verify()` passed; attempts 2 and 3 cost $0.2–0.6 and
changed nothing; the unit blocked; the operator edited `produces:` by hand; the
re-arm passed on the identical tree. The `produces_unchanged:` escape hatch
(#3282) was used in zero of nine repair attempts, because it covers a different
case — "the deliverable already holds" — and the retry note names the key
without showing its shape.

Two defects compound it. First, the `produces_not_in_diff` branch is the one
guard site that never appends to `refusal_history`, so the deterministic-refusal
short-circuit (#1415) cannot fire and the unit always runs to `max_attempts`.
Second, the repair note tells the session what to do but not how to write it.

This feature gives the RESULT block a second escape hatch, `produces_amended:`,
for the case the plan got wrong; makes the guard record its refusals so the
second identical one is the last; and puts both RESULT shapes verbatim in the
repair note. An amendment is recorded on the unit (`produces_dropped:`) and
shown to the judge, so a dropped deliverable that a criterion depended on is
visible evidence, not a silent edit.

**What this is not.** It is not a way to declare nothing. An amendment that
would leave an implementation unit with an empty `produces:` is refused with
today's summary, and `assert_implementation_touched_files` still applies. It is
not a change to `produces_unchanged:`, which keeps its meaning.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -n "produces_unchanged\|def resolve_produces_refusal\|def produces_justifications\|refusal_history\|def write_frontmatter_block\|_RETRY_CLASS_HINT" specfuse/loop/loop.py`
- **Verdict:** found `produces_justifications` / `resolve_produces_refusal` (#3282), `refusal_history` + `detect_deterministic_refusal_repeat` (#1415), `write_frontmatter_block` (used for `broad_run` and `baseline`); reusing all three, building the amendment path new.
- **Detail.** `resolve_produces_refusal(wu, touched, result_block)` returns
  `(remaining, accepted)` and already reads a list-of-dicts RESULT key; the
  amendment reader is its sibling with a second key. `refusal_history` is
  appended at five guard sites and read before dispatch; the produces site is
  the sixth and only omission. `write_frontmatter_block` splices a
  list-valued frontmatter key, which `set_wu` (scalar) cannot; `produces:`
  is list-valued so the rewrite goes through it.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero. No refusal is added or made stricter. One outcome is removed (a
  justified amendment passes where it used to refuse) and one arrives earlier
  (`deterministic_refusal_repeat` after two identical produces refusals instead
  of `spinning_detected` after three). With `verification.yml`
  `defaults: produces_amendable: false` the amendment key is ignored and the
  refusal text is today's; the `refusal_history` fix is unconditional.

## Assumptions taken by default (answers-supplied drafting, 2026-09-26)

- **Autonomy `auto`.** Single gate, driver-editing feature; the judge writes
  the terminal verdict from evidence, as on FEAT-2026-0103. `judge_editing`
  would veto a live arm anyway; there is no arm on a single gate.
- **Amendment shape: drop, not replace.** A RESULT may drop a declared path
  with a reason; it may not add one. The paths it actually changed are already
  in `files_changed`, and adding to `produces:` post hoc would let a session
  declare its own deliverable list. Reconsider if a real run shows the
  replacement case.
- **Kill switch in `verification.yml` `defaults:`**, the block
  `retain_on_guard_refusal` and `max_attempts` already read.

## Task graph

```yaml
# Single gate, single terminal close: 4 substantive WUs is under the ceremony
# proportionality threshold (docs/methodology.md §6).
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0114/T01
        file: WU-01-amendment-accepted-at-the-guard.md
        depends_on: []
      - id: FEAT-2026-0114/T02
        file: WU-02-repair-note-and-refusal-history.md
        depends_on: [FEAT-2026-0114/T01]
      - id: FEAT-2026-0114/T03
        file: WU-03-dropped-deliverables-reach-the-judge.md
        depends_on: [FEAT-2026-0114/T01]
      - id: FEAT-2026-0114/T04
        file: WU-04-document-the-contract.md
        depends_on: [FEAT-2026-0114/T02, FEAT-2026-0114/T03]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0114/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0114/T01, FEAT-2026-0114/T02, FEAT-2026-0114/T03, FEAT-2026-0114/T04]
```

## Scope boundary — explicitly OUT

- **Adding paths to `produces:` from a RESULT.** Drop only (assumption above).
- **`produces_unchanged:` semantics and its reader.** Untouched; the new key
  is read beside it.
- **Planning-time fixes.** A lint that warns when `produces:` names a file the
  unit's criteria never mention is a separate row; this feature fixes the
  runtime spin.
- **The other guard sites.** `deliverable_missing`, `no_deliverable_files`,
  `files_changed_mismatch` already record into `refusal_history`; nothing
  changes there.
- **No consumer repository is edited.** The generator and IaC runs are the
  evidence, not a surface.

## Post-merge checklist

Observable only across repositories and over time, so filed as a post-merge
observation rather than an acceptance criterion (`close-discipline.md` §2).

- [ ] Over the next ten features closed in this repo and the generator, count
      units with two or more consecutive `produces_not_in_diff` attempts
      (baseline: 6 in the 2026-09-10..26 window, 5 of them running to three)
      and the share that ended `blocked_human` on that class (baseline: all).
- [ ] Count `produces_amended` entries on passed events and, for each, whether
      the terminal close or judge cited the dropped path in a finding.

## Notes

- Dependencies live here, not in WU frontmatter.
- T02 and T03 are independent once T01 lands; serial only because dispatch is
  serial (FEAT-2026-0105).
