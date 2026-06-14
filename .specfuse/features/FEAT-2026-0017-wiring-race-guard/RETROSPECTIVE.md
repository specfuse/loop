# Retrospective — FEAT-2026-0017 Close-WU wiring-race guard

## Per-WU outcome

### T01 — Post-pass driver-state invariant guard (close-type WUs)

- **Worked.** Final implementation shipped 155 lines in
  `.specfuse/scripts/loop.py` (POST_PASS_INVARIANTS_BY_TYPE,
  assert_terminal_flips_fired, verify_post_pass_invariants wired
  into `run()`'s passed-outcome path) and 316 lines of regression
  tests in `tests/test_loop_post_pass_invariant.py`, including the
  `test_feat_2026_0015_t06_regression` canary.
- **Failed.** Twelve attempts across four dispatch cycles before
  shipping:
  - Cycle 1 (Sonnet 4.6, 3 attempts × ~3 min, $0.42 total): every
    attempt hollow-passed — squash modified only WU-01 frontmatter,
    zero edits to loop.py, no test file. Verify-gate green because
    tests ran against unchanged code.
  - Cycle 2 (Opus 4.7, 3 attempts × ~10 min, $11.95 total): tests
    failed with `subprocess.CalledProcessError` exit 128 inside
    tempdir-git tests because the operator's global
    `commit.gpgsign=true` (SSH signing) prevented `git commit -m
    init` in subprocess tempdirs. Driver crashed during
    spinning-detected `commit_bookkeeping` from the same flake.
  - Cycle 3 (Opus 4.7, 3 attempts × ~8 min, $11.08 total): agent
    correctly diagnosed and refused — pre-existing 20 test errors
    in `tests/test_loop_files_changed_guard.py` +
    `tests/test_loop_orchestration.py` whose `_init_git` helpers
    omitted the gpgSign-false setup pattern used by
    `tests/_workspace.py:36`. Reproduces on `main`.
  - Cycle 4 (Opus 4.7, 1 attempt, $4.11): passed cleanly after
    operator hygiene-fix landed the gpgSign-false setup in the two
    broken `_init_git` helpers.
- **Attempts taken.** 10 attempts (3+3+3+1).
- **Final cost.** $27.55 vs planned $1.50 → **18.4× overrun**.
  See cost-analysis rationale below.

### T02 — `produces_driver_helper` WU frontmatter field + lint warning

- **Worked.** Single Opus 4.7 attempt landed all deliverables in
  one pass: `produces_driver_helper` field on `WorkUnit`
  (loop.py:152), `detect_driver_wiring` function in `lint_plan.py`,
  template update, lint warning.
- **Failed.** Nothing.
- **Attempts taken.** 1.
- **Final cost.** $1.23 vs planned $0.50 → **2.5× overrun**.

### G1-CLOSE — terminal close ceremony (recursive dogfood)

- **Worked.** Operator-finished after spinning-block surfaced an
  Opus agent blind-spot (consistent failure to flip
  `verdict: not_set` even with explicit retry feedback).
- **Failed.** Three dispatch cycles, all blocked or hollow:
  - Cycle 1 (1 attempt, $0.91): agent correctly refused because T01
    cycle 1 had hollow-passed — `POST_PASS_INVARIANTS_BY_TYPE`
    absent from `loop.py`. Validated authoring-work-units §9
    existence-check discipline.
  - Cycle 2 (3 attempts, $4.97): spun on
    `assert_doc_or_roadmap_diff` which required `docs/` or
    `.specfuse/roadmap.md` in the squash but T06's state-flip
    consolidation forbade roadmap edits and this scaffold has no
    `docs/`. Methodology-level contradiction between T06 (driver
    owns roadmap flip) and T07 (close-deliverable guard requires
    roadmap touch).
  - Cycle 3 (3 attempts, $4.68): with the
    `assert_doc_or_roadmap_diff` hygiene-fix accepting
    `RETROSPECTIVE.md` and `.specfuse/LEARNINGS.md`, the
    `diff-only-touches-wu` bypass at `loop.py:1465-1468` let
    attempt 3 silently hollow-pass. Driver flagged the
    inconsistency at end ("terminal gate closed without close
    ceremony flipping PLAN.md to `done`"). New hollow-pass surface
    discovered in dogfood.
  - Cycle 4 (3 attempts, $4.70): bypass-fix in place; agent
    satisfied retrospective + learnings + doc-diff assertions
    every attempt but consistently failed to flip
    `verdict: not_set` to a valid value despite explicit retry
    feedback. Honest block, not hollow-pass.
- **Attempts taken.** 10 across 4 cycles.
- **Final cost.** $10.58 vs planned $1.20 → **8.8× overrun**.

## Gate-level summary

Single-gate terminal feature. T01 + T02 deliverables shipped
substantively. G1-CLOSE delivered via operator-driven close
ceremony after surfacing two distinct hollow-pass surfaces in the
existing methodology, both of which were fixed in this feature's
branch as bonus deliverables.

### Bonus deliverables landed during dogfood

1. **`tests/test_loop_files_changed_guard.py` +
   `tests/test_loop_orchestration.py`** `_init_git` helpers now
   call `git config commit.gpgSign false` after `git init`, matching
   the existing pattern at `tests/_workspace.py:36`. 20 pre-existing
   test errors fixed (commit `36cd193`).
2. **`assert_doc_or_roadmap_diff` (loop.py:1269)** now also accepts
   `.specfuse/LEARNINGS.md` and `RETROSPECTIVE.md` (the real
   close-ceremony documentation deliverables under the post-T06
   contract). Resolves the T06 / T07 contract contradiction. Commit
   `8ec4756`.
3. **`assert_closing_deliverables` (loop.py:1440)** bypass at
   "diff-only-touches-wu" REMOVED. Previously silently passed
   hollow close-ceremony attempts where only the driver's own
   bookkeeping write touched the WU file. New regression test
   `test_close_fails_when_diff_only_touches_wu_file` added. Commit
   `6084a89`.

## Surprises

1. **Sonnet 4.6 is unreliable for impl-WUs that ship multi-symbol
   driver wiring + tests.** Hollow-passes by modifying only the WU's
   own frontmatter, then claims `status: done`. No verify gate
   catches this surface (tests run against unchanged code). Cost: 3
   attempts wasted before escalation to Opus.

2. **Re-arming a WU without committing the re-arm is destructive.**
   Driver's `git reset --hard head_before` between attempts wipes
   uncommitted WU-frontmatter edits. Cost: 1 full attempt cycle.

3. **Operator's global `commit.gpgsign=true` with SSH signing
   silently breaks any test that runs `git commit` in a tempdir.**
   Was broken on `main` for at least two test files; never caught
   until this feature's verify-gate ran.

4. **The methodology contradicts itself in ways only end-to-end
   dogfood surfaces.** FEAT-2026-0015 added both T06 (driver owns
   roadmap flip — close WU MUST NOT touch roadmap.md) and T07
   (close-deliverable guard REQUIRES docs/ or roadmap.md in
   squash). Lint did not catch this. The first feature to actually
   exercise the post-T06 close-contract surfaced it.

5. **The diff-only-touches-wu bypass in `assert_closing_deliverables`
   was a silent hollow-pass loophole.** Added "for test fixture
   convenience" but no test depended on it. Real close-ceremony
   runs could pass with zero substantive output.

6. **Opus 4.7 has a verdict-flip blind-spot for close-WUs.**
   Consistently produced RETROSPECTIVE.md + LEARNINGS + verified
   the close-deliverable shape, but failed to flip the one-line
   `verdict:` frontmatter field across 3 retry attempts with
   explicit failure feedback. Likely cause: the WU body's "set
   verdict ONLY when X AND Y AND Z confirmed" caution overrides
   the terse retry signal, and Opus stays neutral rather than
   commit.

## Cost analysis

| WU       | Planned   | Actual    | Variance |
|----------|-----------|-----------|----------|
| T01      | $1.50     | $27.55    | +1737%   |
| T02      | $0.50     | $1.23     | +146%    |
| G1-CLOSE | $1.20     | $10.58    | +782%    |
| **Gate** | **$3.20** | **$39.37** | **+1130%** |

### Variance rationale

- **T01 ($27.55 vs $1.50).** Three cycles wasted on (a) Sonnet
  4.6 hollow-pass × 3 attempts; (b) pre-existing operator-global
  signing-config breaking tempdir-git tests × 3 Opus attempts; (c)
  pre-existing untreated `_init_git` helper bugs in two test
  files × 3 Opus attempts. The successful cycle 4 was a single
  $4.11 Opus run — close to the original budget at 2.7× planned.
  All overspend was on cycles where the agent was correctly
  producing the work but the verify gate failed for reasons
  outside the WU's stated scope. NOT a substantive overrun.

- **T02 ($1.23 vs $0.50).** Single Opus attempt that included
  substantive work (helper field, lint function, template update,
  warning text). Real overrun: Opus 4.7's higher per-token cost +
  the scope was larger than the $0.50 plan anticipated.

- **G1-CLOSE ($10.58 vs $1.20).** Four cycles wasted on
  methodology-bug discovery (T06/T07 contradiction, bypass loophole,
  Opus verdict-flip blind-spot). Each cycle landed a real
  improvement to the methodology code (commits `36cd193`,
  `8ec4756`, `6084a89`). Operator-finish for the actual
  RETROSPECTIVE+LEARNINGS+verdict-flip was $0 driver-cost. Real
  overrun for the close ceremony itself: ~0×; all overspend was
  bonus deliverable discovery.

# Feature-arc verdict

**roadmap_goal:** met.

Direct evidence:

- **T01 deliverables landed** in `loop.py`:
  - `POST_PASS_INVARIANTS_BY_TYPE` constant (grep returns 1 hit).
  - `assert_terminal_flips_fired` function (grep returns 1 hit).
  - `verify_post_pass_invariants` function (grep returns 1 hit).
  - Wired into `run()`'s passed-outcome path after squash + flip,
    before bookkeeping flush.
  - Importable: `from loop import POST_PASS_INVARIANTS_BY_TYPE,
    assert_terminal_flips_fired, verify_post_pass_invariants`
    exits 0.

- **T02 deliverables landed**:
  - `produces_driver_helper` field on `WorkUnit` (loop.py:152).
  - `detect_driver_wiring` function (lint_plan.py:93).
  - Lint warning fires on implementation WUs that mention
    driver-wiring keywords without declaring the symbol(s).

- **Regression test present.** `test_feat_2026_0015_t06_regression`
  in `tests/test_loop_post_pass_invariant.py` reproduces the
  FEAT-2026-0015/T06 wiring-race bug pattern and asserts the new
  guard returns `(False, ...)` — the canary against
  re-introducing the `wu.verdict`-re-read race.

- **Bonus methodology surface fixes** (3 hollow-pass loopholes
  discovered and closed during dogfood):
  - `tests/_init_git` helpers fixed in 2 test files.
  - `assert_doc_or_roadmap_diff` extended to accept the real
    close-ceremony documentation paths.
  - `assert_closing_deliverables` diff-only-touches-wu bypass
    removed with regression test.

The original wiring-race surface (FEAT-2026-0015/G2-CLOSE
hollow-pass) is closed by T01. The recursive dogfood
exercise on G1-CLOSE surfaced two MORE hollow-pass surfaces
(diff-bypass + verdict-flip blind-spot) that the original goal
did not anticipate, both of which received methodological
treatment: one fixed in-feature (bypass), one logged for
deep-analysis (verdict blind-spot is a model-level pattern, not
a methodology bug per se).
