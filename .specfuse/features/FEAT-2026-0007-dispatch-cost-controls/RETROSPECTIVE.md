# FEAT-2026-0007 Gate 1 — Retrospective

**Produced by:** WU-90 (G1-RETRO)  
**Gate span:** 2026-06-07T13:25 – 13:42 UTC  
**WUs in scope:** T01, T02, T03, T04, T05 (all implementation)  
**Total cost:** $3.81 across 5 WUs / 5 attempts  
**Dispatch order:** T01 → T05 → T02 → T03 → T04

---

## WU-by-WU analysis

### T01 — Accept model family alias
- **Attempts:** 1 · **Duration:** 216s · **Cost:** $0.746
- **What worked.** Spec was precise: explicit allowed set (not a regex), explicit no-expansion policy, exact file list. Agent landed all 4 files (loop.py, lint_plan.py, WU.template.md, new test). Commit also bootstrapped the full feature folder structure (PLAN.md, all WU files, GATE-01/02.md) — standard first-WU pattern.
- **What failed.** Nothing observable.
- **Missing/ambiguous in WU.** Nothing — the escalation trigger (don't introduce broader lint validation) was the right guardrail for this scope.

---

### T05 — Cap failure-note size
- **Attempts:** 1 · **Duration:** 186s · **Cost:** $0.590
- **What worked.** Driver correctly identified T05 as dependency-free and dispatched it second rather than last. Spec was self-contained: exact function signature, 200-line / 8000-char limits, head+tail split, plain-ASCII marker constraint, exact file count (2). All delivered.
- **What failed.** Nothing observable.
- **Missing/ambiguous in WU.** The acceptance criteria required "both the first and last lines of the input appear in the output" in the test (criterion 3b) — a concrete behavioral check. This level of specificity helped; it left the agent no room to write a test that just checks string length.

---

### T02 — Add effort field and wire `--effort`
- **Attempts:** 1 · **Duration:** 238s · **Cost:** $0.818
- **Cache read:** 1,553,336 tokens — highest in the gate (T01 + T05 context accumulated).
- **What worked.** Spec enumerated the exact valid set, the `ValueError` message requirement, the CLAUDE_CMD extension format, and the lint-plan narrowing. Agent delivered all 4 files and both tests (positive and negative).
- **What failed.** Nothing observable.
- **Missing/ambiguous in WU.** The WU didn't address WU files with no YAML block at all (bare body, no frontmatter). The agent used `fm.get("effort", "medium")` which is safe given the existing `load_wu` contract, but the spec could have stated "YAML-absent files use the dataclass default" explicitly. Low severity; current behavior is correct by inference from T01's pattern.

---

### T03 — Tier-gated caveman preamble
- **Attempts:** 1 · **Duration:** 128s · **Cost:** $0.401
- **Fastest and cheapest WU in the gate.** Output was 4,261 tokens — less than half of any other WU. Scope was tightly bounded: one new constant, one preamble-selection branch, one sentence in WU.template.md, one test.
- **What worked.** Spec named the constant (`CAVEMAN_DIRECTIVE`), the exact condition (`wu.effort in {"low", "medium"}`), the must-not-alter list (RESULT block format, code blocks, quoted errors), and the escalation trigger (mass-fail on existing verbatim preamble assertions). Agent landed all 3 files cleanly.
- **What failed.** Nothing observable.
- **Missing/ambiguous in WU.** Spec referred to the caveman directive as a "multi-line string" but didn't specify the directive's content, only its behavioral constraints (no narration, no end-of-turn summary, etc.). The agent authored the directive body with discretion — which was intentional, but means T04's "caveman-lite" variant had to infer what "softer" meant from T03's output rather than from T03's spec.

---

### T04 — Retry escalation ladder for effort and terseness
- **Attempts:** 1 · **Duration:** 224s · **Cost:** $1.261
- **Model:** claude-opus-4-7 (by design — control-flow edit + signature change simultaneously)
- **Output tokens:** 12,451 — highest in the gate; Opus reasons verbosely.
- **CRITICAL FINDING: Implementation not delivered.**

The WU frontmatter shows `status: done`, and the events.jsonl records `task_completed`. The driver ran verification and passed it. But none of the required code changes exist in the repository:

| Required (per acceptance criteria) | Present? |
|---|---|
| `EFFORT_LADDER` constant in loop.py | No |
| `effort_for_attempt()` function | No |
| `terseness_for_attempt()` function | No |
| `dispatch()` `effort`/`terseness` kwargs | No |
| Attempt loop calling both helpers | No |
| `effort_used`/`terseness` in `attempts_usage` | No |
| `tests/test_loop_retry_ladder.py` | No |

The only files that changed in T04's commit are `WU-04-retry-ladder.md` (frontmatter update) and `events.jsonl` (task event).

**Why verification passed despite no code.** The `code` gate runs `python3 -m unittest discover -s tests -v`. When T04 wrote no test file, no new tests were registered. The existing tests — which don't assert `effort_for_attempt` exists — all passed. The gate has no mechanism to verify "the required new test file was created" or "the required functions exist." The driver's verification is a conformance check on existing artifacts, not a completeness check on acceptance criteria.

**Root cause (most likely).** The agent produced a RESULT block with `status: complete`, the driver squashed its edits (which were only the WU status flip), verification passed on the unchanged code, and the driver committed. The agent either hallucinated completion without editing loop.py, or its loop.py writes were discarded in the reset before the squash. The events log does not record agent file writes — only outcomes — so the exact failure mode is unobservable from this log.

**Impact.** Retry attempts currently run with the same effort and the same (or no) terseness directive on every attempt. The escalation behavior FEAT-2026-0007 was built for does not exist at runtime. Gate 2 work that assumes T04 landed (T08 telemetry) will be building on absent infrastructure.

**Rule missing from WU spec.** The WU acceptance criteria listed the required functions but did not include a verification step asserting the functions are importable (e.g., `python3 -c "from loop import effort_for_attempt"`). Adding a fast smoke-import check to the acceptance criteria's own `Verification` section would have caught this before the driver committed.

---

## Gate-level observations

**Dispatch order was correct.** T05 ran second (before T02/T03/T04) because the driver correctly identified it as dependency-free. All other units ran in dependency order (T01 → T02 → T03 → T04). Scheduling was not a failure mode.

**Cache hit rate was high throughout.** Cache reads ranged from 691k (T03, smallest context window) to 1.5M tokens (T02, post-T01+T05). This kept cost low on T01–T03. T04's Opus pricing explains its 3× cost delta despite similar duration.

**No retry in the gate.** Every WU completed in 1 attempt. The retry ladder itself was never exercised — which means the T04 implementation gap is consequential only when a WU fails and retries occur. That situation is not tested.

**Template gap exposed.** `WU.template.md` documents `effort:` field and the caveman directive sentence (per T02/T03) but has no section guiding the author on specifying smoke-import or function-existence checks in `Verification`. The WU spec's Verification section tends to defer to "run the `code` gate" without naming what within the gate would fail if the function is absent.

**Escalation trigger on T04 was well-placed but didn't fire.** The T04 spec said "stop if changing `dispatch()`'s signature breaks T02 or T03 tests." This would catch a wrong change. It had no mirror trigger: "stop if your changes are missing from the staged diff." The driver could add an agent pre-flight check that reads its own RESULT block's `files_changed` list and verifies those files differ from HEAD before committing.
