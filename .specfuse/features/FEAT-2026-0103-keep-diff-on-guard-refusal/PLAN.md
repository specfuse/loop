---
feature_id: FEAT-2026-0103
title: Keep the diff on guard refusals — repair, do not restart
slug: keep-diff-on-guard-refusal
branch: feat/FEAT-2026-0103-keep-diff-on-guard-refusal
roadmap_goal: When a bookkeeping guard refuses an attempt, the working tree is kept and the next attempt repairs it with the guard's exact complaint in hand, instead of re-authoring from scratch.
autonomy_default: auto
status: active
planned_cost_usd: 23.00
---

# Plan: Keep the diff on guard refusals — repair, do not restart

Four driver-side bookkeeping guards run after a unit's squash and before its
`done` flip: `assert_declared_deliverables` (`deliverable_missing`),
`assert_implementation_touched_files` (`no_deliverable_files`),
`resolve_produces_refusal` (`produces_not_in_diff`) and `verify_files_changed`
(`files_changed_mismatch`). Each is right to refuse — they exist because agents
declare work they did not do (`[FEAT-2026-0013/G1-CLOSE]`). But every refusal
today is followed by `reset_preserving_events(head_before)`: the squash is
thrown away, and the next attempt starts from the base tree with a truncated
note about work it can no longer see. Across the 2026-09-01 review's corpus
that is 323 attempts, roughly $830 and 42 hours, spent re-authoring work the
guard had only asked to be *declared* correctly (`reviews/…/hedge-taxonomy.md`,
private). On this repo alone, FEAT-2026-0084/T01 paid $10.28 over two refusals
before a third attempt cleared the guard by inventing an edit.

This feature keeps the tree. A guard refusal uncommits the squash and leaves
the working tree exactly as the attempt left it; the next attempt is dispatched
with the guard's exact complaint, told the tree is retained, and asked to
repair — fix the declaration, or make the missing deliverable — not to start
over. The one clerical case that needs no session at all (a RESULT block naming
an untouched path that is not a deliverable) is repaired by the driver and the
attempt proceeds as passed.

**What this is not.** It is not convergent iteration for test failures. #2650
retains a tree only when a validator emits a `FINDINGS:` metric that improved,
because a broken tree nobody has measured is not worth keeping. A guard
refusal is different in kind: the complaint is exact, the work is verified
(`verify()` passed before every one of these guards), and what is missing is
bookkeeping. Test-gate failures keep today's reset unless the unit opts into
`iterate_on_failure`.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -n "iterate_on_failure\|retained\|def capture_working_tree_diff\|def apply_diff\|def reset_preserving_events\|produces_unchanged" specfuse/loop/loop.py`
- **Verdict:** found convergent iteration (#2650) and the `produces_unchanged`
  justification (#3282); reusing both, building the guard-refusal retain path new.
- **Detail.** `decide_convergence_action`'s docstring: "``retain`` — The tree
  improved (or is the first measurement). Keep it and let the next attempt
  continue in place." That path already proves the driver can leave a tree in
  place between attempts and tell the next session so
  (`synthesize_retry_directive(retained=True)`: "telling a session its work
  'was DISCARDED' when the tree is still there makes it re-author from
  scratch"). It does not cover guard refusals: it is gated on
  `wu.iterate_on_failure` and on a `FINDINGS:` metric, and the four guard
  sites `continue` the attempt loop before it is reached. This feature reuses
  `capture_working_tree_diff` for the note and the `retained` directive for
  the prompt, and adds the uncommit-keep-tree step the guard sites lack.
  `resolve_produces_refusal` (0.17.0, #3282) already lets a RESULT justify an
  unchanged `produces:` path; T03's auto-repair is the complement for paths
  that are *not* deliverables, and does not touch that path.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero. No guard is added and none is made stricter: every refusal that fires
  after this feature fired before it. What changes is what happens *after* a
  refusal (retain instead of reset) and one case that no longer refuses at all
  (T03). The retain path is off when `verification.yml` sets
  `defaults: retain_on_guard_refusal: false`, and off is byte-identical to
  today.

## Task graph

```yaml
# Single gate, single terminal close: 4 substantive WUs is under the ceremony
# proportionality threshold (docs/methodology.md §6).
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0103/T01
        file: WU-01-retain-tree-after-refusal.md
        depends_on: []
      - id: FEAT-2026-0103/T02
        file: WU-02-repair-turn-lead.md
        depends_on: [FEAT-2026-0103/T01]
      - id: FEAT-2026-0103/T03
        file: WU-03-clerical-auto-repair.md
        depends_on: [FEAT-2026-0103/T01]
      - id: FEAT-2026-0103/T04
        file: WU-04-document-the-contract.md
        depends_on: [FEAT-2026-0103/T02, FEAT-2026-0103/T03]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0103/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0103/T01, FEAT-2026-0103/T02, FEAT-2026-0103/T03, FEAT-2026-0103/T04]
```

## Scope boundary — explicitly OUT

- **Test-gate failures.** A failed `tests`/`lint`/`coverage` gate still resets
  the tree unless the unit declares `iterate_on_failure` (#2650). Retaining a
  failing tree without a metric is the design that mechanism rejected.
- **`iterate_on_failure` stays opt-in.** The roadmap row said "defaults on";
  what this feature turns on by default is retention *after guard refusals*,
  with its own kill switch. The convergent metric contract is untouched.
- **Parallel dispatch (FEAT-2026-0105) and re-planning after two failures
  (FEAT-2026-0104).** Both interact with retained trees; both are their own rows.
- **The `learnings_not_staged` close guard.** Closing units are dispatched at
  opus effort high; retaining their tree is cheap to add but the shape is
  different (the refusal is about a staging file, not the deliverable) and no
  measurement motivates it. Left on today's reset.
- **No consumer repository is edited.** The generator's FEAT-2026-0167 numbers
  in #3293 are context, not a surface.

## Post-merge checklist

Observable only across repositories and over time, so filed as a post-merge
observation rather than an acceptance criterion (`close-discipline.md` §2).

- [ ] Over the next five features closed in this repo and the generator, count
      `attempt_outcome` events with `failure_class` in `guard_refusal`,
      `files_changed_mismatch`, `produces_not_in_diff` and sum their
      `cost_usd`; record the share of feature spend against the review's
      baseline (10% of spend, 323 attempts corpus-wide) and the mean number of
      attempts a refused unit needed to pass (baseline: a refusal restarted the
      unit; target: one repair attempt).
- [ ] Confirm on one real refusal in the generator that the retained tree
      survived the driver's own bookkeeping commit and the repair attempt's
      squash carried both the original work and the repair.

## Notes

- Dependencies live here, not in WU frontmatter.
- T02 and T03 are independent once T01 lands; they are serial today because
  dispatch is serial (FEAT-2026-0105), not because either needs the other.
