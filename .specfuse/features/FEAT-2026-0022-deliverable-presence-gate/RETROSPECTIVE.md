<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0022 Deliverable-presence gate

Single-gate feature, three independent driver-side guards plus one terminal
close. `roadmap_goal`: the driver refuses to commit an implementation WU as
`done` when a declared deliverable is absent or empty, or when the WU touched
zero files — closing the zero/partial-deliverable hollow-pass class
FEAT-2026-0008/0015 left open.

## Per-WU outcomes

All three substantive WUs passed on **attempt 1**, `outcome: passed`,
`agent_status: complete`, no failure class recorded (`events.jsonl`).

### T01 — `produces:` frontmatter field (`WU-01-produces-frontmatter-field.md`)
- **Attempts:** 1 (passed). Duration 415.99s, cost $2.27.
- **What worked:** Introduced the `WorkUnit.produces` field (parse + advisory
  lint WARN) and documented it in `WU.template.md`. `files_touched` shows the
  real deliverable set: `loop.py`, `lint_plan.py`, `WU.template.md`,
  `tests/test_produces_field.py` — not a status-flip-only diff. Red-test-first
  honored: `test_produces_field.py` exists (6 tests, all green).
- **What failed:** Nothing. Clean single-attempt pass.

### T03 — empty-files escalation (`WU-03-empty-files-escalation.md`)
- **Attempts:** 1 (passed). Duration 517.05s, cost $3.34 (most expensive WU).
- **What worked:** Added `assert_implementation_touched_files`; an
  implementation WU touching zero deliverable files records
  `no_deliverable_files` and blocks. `files_touched`: `loop.py`,
  `tests/test_empty_files_escalation.py`. Independent of T01 (depends only on
  `files_touched`), so ran second in the frontier without waiting on T02.
- **What failed:** Nothing. Highest spend — see Cost analysis.

### T02 — deliverable-presence gate (`WU-02-deliverable-presence-gate.md`)
- **Attempts:** 1 (passed). Duration 491.40s, cost $2.89.
- **What worked:** Added `assert_declared_deliverables` reading T01's
  `produces:` — each path must exist + be non-empty (`test -s`) before
  `complete` is accepted, else `deliverable_missing`. `files_touched`:
  `loop.py`, `tests/test_deliverable_presence_gate.py`. Correctly sequenced
  after T01 (its declared dependency).
- **What failed:** Nothing.

### G1-CLOSE — this ceremony (`WU-90-gate-1-close.md`)
- **Attempts:** 1. Wrote this retrospective, ran the recursive audit, appended
  LEARNINGS + the `produces:` rule to the authoring skill, reconciled roadmap +
  PLAN status, set `verdict: met`.

## Guard-helper existence audit

Run live this session (`grep`/`ls` against the working tree):

| Check | Command | Expected | Result |
|---|---|---|---|
| Presence gate helper | `grep -c "def assert_declared_deliverables" .specfuse/scripts/loop.py` | ≥1 | **1** ✓ |
| Empty-files helper | `grep -c "def assert_implementation_touched_files" .specfuse/scripts/loop.py` | ≥1 | **1** ✓ |
| `produces` field + parse | `grep -c "produces" .specfuse/scripts/loop.py` | ≥1 | **29** ✓ |
| T01 test | `ls tests/test_produces_field.py` | exists | exists ✓ |
| T02 test | `ls tests/test_deliverable_presence_gate.py` | exists | exists ✓ |
| T03 test | `ls tests/test_empty_files_escalation.py` | exists | exists ✓ |

**No hollow pass.** All three guard helpers exist in the driver and all three
test files exist on disk. None of T01/T02/T03 status-flipped without producing
the code they were contracted to add (corroborated by `files_touched` in each
WU's `attempt_outcome`).

## Live recursive validation

Existence is necessary, not sufficient — a guard that parses but never fires is
itself a hollow pass. This close ran the integration tests and confirmed both
the BLOCK path and the clean path:

- `python3 -m unittest tests.test_produces_field` → **Ran 6, OK**.
- `python3 -m unittest tests.test_deliverable_presence_gate` → **Ran 10, OK**.
  Asserts `deliverable_missing` is recorded and escalates to `blocked_human`
  after MAX_ATTEMPTS when a declared deliverable (e.g. `CODE_OF_CONDUCT.md` —
  the exact T12 partial-bundle shape) is absent or empty
  (`test_empty_deliverable_blocks`), AND that a satisfied deliverable does NOT
  record `deliverable_missing` (the negative path).
- `python3 -m unittest tests.test_empty_files_escalation` → **Ran 6, OK**.
  Asserts an implementation WU touching zero files records
  `no_deliverable_files` and blocks (the exact T16 zero-deliverable shape),
  and that the close WU is exempt from the empty-files rule.

The driver source backs the test assertions: `loop.py:2841`
(`closing_deliverable_missing`), `loop.py:2870` (`deliverable_missing`),
`loop.py:2895` (`no_deliverable_files`). The guards block, they do not merely
exist. (Mirrors the FEAT-2026-0008 "second live recursive validation" pattern.)

## Cost analysis

Planned (PLAN.md total **$7.00**, matching the sum of per-WU frontmatter:
T01 $1.50 + T02 $2.00 + T03 $1.50 + G1-CLOSE $2.00).

| WU | Planned | Actual | Delta |
|---|---|---|---|
| T01 | $1.50 | $2.27 | +$0.77 (+51%) |
| T02 | $2.00 | $2.89 | +$0.89 (+45%) |
| T03 | $1.50 | $3.34 | +$1.84 (+123%) |
| Substantive subtotal | $5.00 | **$8.50** | **+$3.50 (+70%)** |
| G1-CLOSE | $2.00 | (this session, not yet in events) | — |

**Delta named:** substantive spend overran by **+$3.50 (+70%)** against the
$5.00 substantive budget. Every WU overran; T03 worst (+123%). Driver was
`opus`/`effort: high` on all three by deliberate plan choice — PLAN.md notes
Sonnet 4.6 hollow-passes this guard-authoring shape, so the overrun bought the
clean single-attempt, zero-hollow-pass result the audit confirms. Reasonable
trade: $3.50 over budget vs. the cost of even one re-dispatch on a
correctness-path regression. Total feature spend will close near $8.50 +
close-WU cost (~$9–10), over the $7.00 plan but with no wasted attempts.

## What the loop did NOT verify

- **G1-CLOSE's own cost** — not yet in `events.jsonl` (this session is in
  flight). Verified post-squash by the driver; the close-WU planned $2.00 is
  the reconciliation anchor.
- **`git diff main..HEAD --stat`** — the WU context names it, but
  `result-contract.md` rule 1 forbids the session from running `git`. Used
  `files_touched` from each `attempt_outcome` event as the equivalent
  per-WU diff evidence instead. The driver owns git verification at squash.

Everything else — guard-helper existence (AC2), live block/clean firing (AC3),
test green-state — was verified in-loop this session. The list is 2 entries and
both are loop-sandbox/git-ownership limits, not deferred correctness checks; it
does not exceed the 30% threshold, so no single-gate sizing flag is warranted.

# Feature-arc verdict

**`roadmap_goal` MET.**

The driver now refuses to commit an implementation WU as `done` when a declared
deliverable is absent or empty (`assert_declared_deliverables` →
`deliverable_missing`), or when the WU touched zero deliverable files
(`assert_implementation_touched_files` → `no_deliverable_files`). Both shapes
are read from signals already produced (`produces:` declared at draft time;
`files_touched` per attempt). The Guard-helper existence audit confirms all
three helpers and all three test files are present; the Live recursive
validation confirms the guards fire and block (22 tests green across the three
files, both block and clean paths asserted), not merely exist.

This closes the zero-deliverable (T16) and partial-bundle (T12) hollow-pass
class documented in `[FEAT-2026-0020/G2/hollow-pass-presence-gates]`, extending
the no-code-written guard from `[FEAT-2026-0008/G1-CLOSE]`. No WU
hollow-passed the guards it added. `verdict: met` set on this WU's frontmatter.
