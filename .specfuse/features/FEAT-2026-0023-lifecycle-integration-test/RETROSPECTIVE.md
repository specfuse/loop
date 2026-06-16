<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0023 (Lifecycle integration test + consolidate terminal-state ownership)

Single terminal gate, three substantive WUs (T01, T03, T02) + one combined
`close` ceremony (G1-CLOSE). The feature closes the **class** of close/branch
seam bugs (#47/#48/#49), not the three instances.

## Per-WU outcomes

### T01 — Consolidate terminal-state ownership (`WU-01-consolidate-terminal-flips.md`)
- **Attempts:** 1, `passed`. Cost $3.36, 424s (events.jsonl
  `attempt_outcome`, 2026-06-16T15:52:17Z).
- **What worked:** First-attempt pass. `fire_terminal_flips` (loop.py:1595) is
  now the single driver-side owner of every terminal flip — gate→passed,
  roadmap row→done, **PLAN.md status→done** (loop.py:1718), and
  `auto_archive_feature`. Both close paths reach it; the agent-less auto-close
  path now flips PLAN for free, closing #49. The PLAN flip is gated on
  `verdict_permits_terminal_flips` and re-reads the verdict from disk so the
  auto-close path (which writes `verdict=met` to the WU file but leaves
  in-memory `wu.verdict` None) is handled identically. Red-test-first:
  `tests/test_terminal_flip_ownership.py` reproduces #49 against the pre-T01
  driver.
- **What failed:** Nothing in-loop.

### T03 — Harden the branch seam (`WU-03-branch-seam-hardening.md`)
- **Attempts:** 1, `passed` (WU frontmatter `status: done`, `attempts: 1`).
- **Observability gap (flagged):** `events.jsonl` contains **no** T03
  `task_started`/`attempt_outcome`/`task_completed` records — only T01 and T02
  are logged, despite T03 being committed (`f5d9263`) and its WU marked done.
  Its per-attempt cost/duration therefore cannot be cited from the event log.
  The deliverable is nonetheless verified independently by green tests
  (`tests/test_ensure_feature_branch.py`, present, 8.2 KB).
- **What worked:** `ensure_feature_branch` (loop.py:~684) now surfaces git's
  stderr, carries the `/pick-feature` roadmap+PLAN flips onto the new branch,
  and detects a stale/divergent branch. Fixes #48.

### T02 — End-to-end lifecycle integration test (`WU-02-lifecycle-integration-test.md`)
- **Attempts:** 1, `passed`. Cost $4.30, 585s (events.jsonl
  `attempt_outcome`, 2026-06-16T16:22:36Z).
- **What worked:** First-attempt pass. The harness drives `loop.run()` against
  a real git tmp repo, stubbing **only** the agent boundary; every other moving
  part (`ensure_feature_branch`, the auto-close predicate
  `evaluate_auto_close`, `fire_terminal_flips`, `auto_archive_feature`) is the
  real driver. It asserts the terminal invariant on BOTH the dispatched-close
  and the agent-less auto-close path, plus the branch seam and the row-only
  archive anchor (#47). This is the layer that would have caught all three bugs.
- **What failed:** Nothing in-loop.

### G1-CLOSE — this ceremony (`WU-90-gate-1-close.md`)
- **Attempts:** 1 (in progress). Audit ran clean; verdict `met` (below).

## Terminal-ownership audit

The recursive responsibility: confirm the consolidation actually unified
terminal-flip ownership and the lifecycle test exercises real seams.

- `grep -c "def fire_terminal_flips" .specfuse/scripts/loop.py` → **1**. The
  single definition is at **loop.py:1595**; it writes `PLAN.md status: done`
  at **loop.py:1718** (`write_frontmatter_field(plan_path, "status", "done")`),
  gated on `verdict_permits_terminal_flips(disk_verdict)`.
- **No SECOND site writes `PLAN.md status: done`.** The only other PLAN-status
  writes are semantically distinct, not competing terminal owners:
  - loop.py:2670 writes `status: complete` (the all-gates-already-passed
    entry marker, a different status, not `done`).
  - loop.py:3097 writes `status: active` (the hedged-verdict **revert** path —
    undoes a `done`, does not create one).
  The consolidation goal holds: exactly one writer flips PLAN→done.
- `ls tests/test_terminal_flip_ownership.py tests/test_ensure_feature_branch.py
  tests/test_lifecycle_integration.py` → **all three present** (8.2 KB / 8.2 KB
  / 21.1 KB).
- **Lifecycle test is not hollow.** Its module docstring states it stubs ONLY
  the agent boundary and exercises the REAL `fire_terminal_flips` /
  `auto_archive_feature` / `ensure_feature_branch` / auto-close predicate (not
  re-implementations) — escalation-trigger guard built in. Inspected
  assertions confirm it checks `PLAN.md status: done`, gate `passed`, roadmap
  row `done`, the `auto_close_decision(auto=True)` event, and the branch seam.
- **Tests run green:** `python -m unittest tests.test_terminal_flip_ownership
  tests.test_ensure_feature_branch tests.test_lifecycle_integration` →
  `Ran 14 tests` … `OK`.

No absence found. Not a hollow pass.

## Cost analysis

Planned (PLAN.md `planned_cost_usd: 8.50`) = sum of per-WU planned: T01 $2.00 +
T02 $3.00 + T03 $1.50 + G1-CLOSE $2.00 = **$8.50**.

| WU | Planned | Actual | Delta |
|----|---------|--------|-------|
| T01 | $2.00 | $3.36 | +$1.36 (+68%) |
| T02 | $3.00 | $4.30 | +$1.30 (+43%) |
| T03 | $1.50 | — (no events) | unknown |
| G1-CLOSE | $2.00 | — (in progress) | unknown |

Known actual: T01 + T02 = **$7.67** vs $5.00 planned → **+$2.67 (+53%)** on the
two WUs the event log records. T03 and this close WU are not yet reconcilable
from `events.jsonl` (T03 events absent — see T03 observability gap above; close
cost lands post-session). Both logged WUs ran ~50% over their per-WU estimate —
consistent with the PLAN note that these are intricate `opus`/`effort: high`
driver-correctness changes, so the overrun is in-character, not anomalous.

## What the loop did NOT verify

(nothing — every acceptance criterion was verified in-loop: the audit greps,
the `ls` presence checks, and the 14-test green run all executed in-session.)

Caveat (not an unverified acceptance criterion): T03's per-attempt cost/duration
could not be **cited from `events.jsonl`** because its records are missing from
the log. T03's *deliverable* is still verified — by green
`test_ensure_feature_branch.py` — so no acceptance criterion is unverified; only
the audit trail for that WU is incomplete.

## What I'd change

- **Single-gate sizing was correct.** Zero entries in "What the loop did NOT
  verify" (well under the >2 / >30% flag threshold). Three substantive WUs +
  one combined close was the right ceremony weight per the size rule.
- **Fix the missing-T03-events gap.** A WU committed and marked `done` with no
  `events.jsonl` record is an observability bug — it breaks cost reconciliation
  and the learnings-suggest clustering that reads `attempt_outcome`. Worth a
  follow-up driver bug: assert every committed WU has a matching
  `task_completed` event before advancing the frontier.

# Feature-arc verdict

`roadmap_goal` — "one driver-side owner for every terminal flip
(PLAN+GATE+roadmap+archive) called by both close paths, a hardened branch seam,
and an end-to-end lifecycle integration test that would have caught all three
bugs (#47/#48/#49)" — is **met**.

Evidence (AC 2 audit): `fire_terminal_flips` is the single owner (count=1,
loop.py:1595) and now flips PLAN→done (loop.py:1718) on both close paths with no
competing writer; the branch seam is hardened (T03, `test_ensure_feature_branch.py`);
the end-to-end lifecycle test exercises the real seams on both close paths and
the row-only archive (`test_lifecycle_integration.py`); all 14 tests across the
three suites pass. The lifecycle test is the layer that would have caught
#47/#48/#49 before a live run.

`verdict: met`. The driver reads this post-squash and fires the terminal flips
(gate→passed, roadmap row→done, PLAN.md→done, auto-archive). The roadmap row is
correctly still `active` at the moment this WU runs — the driver flips it
post-squash; this is the normal path, not a conflicting/raced `done`.
