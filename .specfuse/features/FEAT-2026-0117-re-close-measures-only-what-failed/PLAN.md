---
feature_id: FEAT-2026-0117
title: A re-close measures only what failed — narrow greens survive a re-arm unless the tree they proved changed
slug: re-close-measures-only-what-failed
branch: feat/FEAT-2026-0117-re-close-measures-only-what-failed
roadmap_goal: The second close of a gate re-measures its broad oracles, the feature oracle and the criteria that failed or whose covered paths changed, and inherits every other narrow green, so a judge-lowered or hygiene-driven re-close costs a fraction of the first.
autonomy_default: auto
status: active
planned_cost_usd: 22.00
---

# Plan: a re-close measures only what failed

Close cost per feature doubled after the review's changes landed — median $6 to
$14, mean $11 to $17 — and the reason is not the judge ($0.46 per close) but the
re-runs: 64% of post-review features close a gate twice or more, 39% three or
more times, and every re-close re-measures every criterion
(`reviews/2026-09-26-impact-assessment/`, private). FEAT-2026-0104's gate 2
closed four times and spent $31.47 closing against $17 building (#3313). With
implementation spend flat, this is the largest remaining ceremony line item.

The rule already permits inheritance. `close-discipline.md` §1 and §5 say a
`narrow` criterion's recorded green in `GATE-NN-CRITERIA.md` is carried forward
on a re-close; only `broad` oracles and the `feature_oracle` re-run every time.
The artifact exists too: the driver seeds `GATE-NN-CRITERIA.md` before every
close dispatch, the close writes `oracle`, `kind`, `state`, `proved_at_sha` and
`attempt` per entry, and `build_reverification_worklist` partitions entries into
"carried forward" and "re-verify" for the next prompt. What breaks the chain is
the re-arm: `/unblock-wu` resets the close to `attempts: 0`, and the skeleton
step's #3279 fix then resets every entry whose `attempt` exceeds the current
one back to `unverified`, wiping the greens the rule says to keep. The
worklist never checks `proved_at_sha` against the tree either, so even with
the reset removed a green could outlive a change to the thing it measured.

This feature keeps narrow greens across a re-arm, invalidates a green when
the gate diff since `proved_at_sha` touches a path the criterion covers,
records what was carried and what was re-measured on the close, and shows the
judge the same. Broad oracles and the `feature_oracle` keep re-running.

**What this is not.** It does not cache the `feature_oracle` or a broad gate
result across closes; §1 binds those to every attempt and this feature leaves
the rule as it is.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -n "def build_reverification_worklist\|def _precreate_criteria_state_stub\|def format_reverification_worklist\|proved_at_sha\|def resolve_gate_start_sha\|def capture_gate_diff" specfuse/loop/loop.py specfuse/loop/criteria_state.py specfuse/loop/judge.py; grep -n "attempt" specfuse/loop/lint_closing.py | grep -i broad`
- **Verdict:** found the artifact, its writer, its worklist and the gate diff helper; reusing all of them, adding the invalidation rule and removing the re-arm reset for narrow greens.
- **Detail.** `build_reverification_worklist` carries an entry only when
  `kind == narrow`, `state == pass`, `oracle` and `attempt` are set; it takes
  `current_attempt` and never uses it, and never compares `proved_at_sha` to
  the tree. `_precreate_criteria_state_stub` resets entries with
  `attempt > current` (#3279) regardless of kind. `lint_closing`'s close-l
  requires a `broad` pass to carry the current attempt — narrow entries have
  no such constraint, so a carried narrow green is already lint-legal.
  `capture_gate_diff(start_sha)` gives the judge its diff and can give the
  invalidation rule its touched paths.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero. No refusal is added. A first close is unchanged. A re-close either
  carries a green (fewer oracle runs) or re-measures it (today). With
  `verification.yml` `defaults: carry_forward_narrow_greens: false` every
  re-close behaves as today.

## Assumptions taken by default (answers-supplied drafting, 2026-09-26)

- **Autonomy `auto`.** Single gate; the judge writes the terminal verdict.
- **Covered paths = the criterion's unit `produces:` plus the oracle command's
  test module path**, recorded on the entry as `covers:` by the driver at seed
  time (not by the close, which should not decide its own inheritance). A
  criterion with no derivable `covers:` is never carried.
- **Invalidation is by path, not by content hash.** A diff touching a covered
  path invalidates; a diff elsewhere does not. Simpler than a hash of the
  covered files and honest about what the loop can know.

## Task graph

```yaml
# Single gate, single terminal close: 4 substantive WUs is under the ceremony
# proportionality threshold (docs/methodology.md §6).
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0117/T01
        file: WU-01-narrow-greens-survive-the-re-arm.md
        depends_on: []
      - id: FEAT-2026-0117/T02
        file: WU-02-a-green-is-invalidated-by-its-covered-paths.md
        depends_on: [FEAT-2026-0117/T01]
      # hygiene (gate 1 entry probe, 2026-09-26): T02's covers tests leaked
      # their cwd into the suite; T02H adds the cwd guard.
      - id: FEAT-2026-0117/T02H
        file: WU-02H-tests-restore-the-working-directory.md
        depends_on: [FEAT-2026-0117/T02]
      - id: FEAT-2026-0117/T03
        file: WU-03-carried-and-re-measured-on-the-close-and-the-judge.md
        depends_on: [FEAT-2026-0117/T01]
      - id: FEAT-2026-0117/T04
        file: WU-04-document-the-contract.md
        depends_on: [FEAT-2026-0117/T02, FEAT-2026-0117/T02H, FEAT-2026-0117/T03]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0117/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0117/T01, FEAT-2026-0117/T02, FEAT-2026-0117/T02H, FEAT-2026-0117/T03, FEAT-2026-0117/T04]
```

## Scope boundary — explicitly OUT

- **Caching the `feature_oracle` or broad gates across closes.** §1 binds them
  to every attempt; changing that is a rule change, not this row.
- **Automatic re-arm after a judge lowering.** The human still re-arms; this
  feature makes the re-arm cheap. (An auto re-arm behind a hygiene unit is
  FEAT-2026-0115's shape applied to closes — a later row if the numbers ask.)
- **`close-intermediate`.** Same artifact, same worklist; the units name both
  types where the code is shared, but the oracle exercises the terminal
  `close`.
- **No consumer repository is edited.**

## Post-merge checklist

Observable only across repositories and over time (`close-discipline.md` §2).

- [ ] Over the next ten features closed in this repo and the generator, for
      every gate closed more than once: the second close's `cost_usd` against
      the first's (baseline: roughly equal), and the count of carried versus
      re-measured criteria from `## Measurements`.
- [ ] Any judge finding that names a carried criterion (a carried green that
      should have been re-measured).

## Notes

- Dependencies live here, not in WU frontmatter.
- T02 and T03 are independent once T01 lands.
