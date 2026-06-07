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

---

# FEAT-2026-0007 Gate 2 — Retrospective

**Produced by:** WU-94 (G2-RETRO)  
**Gate span:** 2026-06-07T14:29 – 14:49 UTC  
**WUs in scope:** T06, T07, T08H, T08 (all implementation)  
**Total cost:** $5.43 across 4 WUs / 4 attempts  
**Dispatch order:** T06 → T07 → T08H → T08

---

## WU-by-WU analysis

### T06 — Defaults-by-WU-type policy (with Haiku guidance)
- **Attempts:** 1 · **Duration:** 518.5s · **Cost:** $1.538
- **Output tokens:** 28,367 — highest in the gate. Context window was large (cache read: 2,455,404 tokens from accumulated G1 history).
- **What worked.** T06 landed cleanly. Smoke check `python3 -c "from loop import MODEL_BY_TYPE, EFFORT_BY_TYPE"` exits 0. The WU was the most complex in Gate 2: 5 file changes (loop.py, lint_plan.py, WU.template.md, authoring-work-units/SKILL.md, new test file), policy tables across two dictionaries, a linter back-compat change, and a Haiku policy section in a skill file. All delivered in one attempt.
- **What failed.** Nothing observable. The existence smoke check from AC 8 succeeded.
- **Rule/template gaps.** AC 8's smoke check was explicitly named in the WU spec (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`). It worked — T06 ran the check and passed. This confirms the G1 lesson generalised correctly: naming the smoke check in the WU's own Verification section prevents silent no-ops.
- **Duration note.** 518.5 seconds is the longest WU in the feature. The large cache-read context (2.4M tokens) dominated — actual compute was Sonnet-scale but the context ingestion was expensive in wall-clock.

---

### T07 — Per-gate cost budget with `blocked_human` halt
- **Attempts:** 1 · **Duration:** 384.0s · **Cost:** $3.609
- **Model:** claude-opus-4-7 (by design — control-flow edit + new halt path).
- **Output tokens:** 20,461. Cache read: 4,500,637 tokens — largest in the gate (T06 added substantial context).
- **What worked.** T07 landed. Smoke check `python3 -c "from loop import gate_budget_usd, gate_spent_usd"` exits 0. The four-file scope (loop.py, lint_plan.py, GATE.template.md, test file) and the integration test (fixture gate at budget $1.00 / spent $1.50 → halt) all delivered.
- **What failed.** Nothing observable at the code level.
- **Budget brake did not fire during Gate 2.** GATE-02.md carries no `cost_budget_usd` field — T07's own implementation was the gate that introduced the field, so the gate being built by T07 could not have a budget set against it ex-ante. The brake was not exercised in this gate's run. Exercising it requires a future gate that sets `cost_budget_usd` in its GATE.md before dispatching.
- **Cost note.** T07's $3.61 is 67% of the gate's total cost and is attributable entirely to Opus pricing × large cache-read context (~4.5M tokens). The spec correctly assigned Opus (control-flow edit requiring reasoning about halt atomicity). The cache-read cost is unavoidable given the accumulated feature context by this point in the run.
- **Rule/template gaps.** GATE.template.md now documents `cost_budget_usd` as optional. No ambiguity was observable — the WU spec was precise on halt semantics (between WUs, not mid-attempt; mirrors MAX_ATTEMPTS shape).

---

### T08H — Hygiene: re-land retry-ladder code (T04's missing implementation)

- **Attempts:** 1 · **Duration:** 225.2s · **Cost:** $0.00 · **Tokens:** 0 input / 0 output
- **CRITICAL FINDING: T08H REPEATED THE T04 FAILURE MODE EXACTLY.**

**Smoke check result:**
```
python3 -c "from loop import EFFORT_LADDER, effort_for_attempt, terseness_for_attempt"
ImportError: cannot import name 'EFFORT_LADDER' from 'loop'
EXIT: 1
```

None of T08H's required symbols exist in the post-gate tree:

| Required (per T08H acceptance criteria) | Present? |
|---|---|
| `EFFORT_LADDER` constant in loop.py | **No** |
| `effort_for_attempt()` function | **No** |
| `terseness_for_attempt()` function | **No** |
| `dispatch()` effort/terseness kwargs | **No** |
| attempt loop wiring in `run()` | **No** |
| `effort_used`/`terseness` in attempts_usage | **No** |
| `tests/test_loop_retry_ladder.py` | **No** |

The events.jsonl record is damning: `cost_usd: 0.0`, `input_tokens: 0`, `output_tokens: 0`. The driver billed nothing. Duration was 225 seconds but no tokens were consumed — meaning the agent either produced a RESULT block claiming complete without editing any file, or the session crashed before the squash ran, and the driver committed only the WU-08H frontmatter status flip (replicating T04's failure mechanics).

T08H was written specifically to prevent this outcome. It included:
- AC 9: an explicit smoke-import check in the Verification section
- Escalation Trigger 1: "emit `status: blocked` if any of the three symbols is absent"
- Escalation Trigger 2: "confirm files_changed shows a substantive diff"

None of these safeguards fired. The agent emitted `status: done` (or the driver advanced without a RESULT block), verification ran against unchanged code, and the commit landed only the WU frontmatter update.

**Why the same failure mode survived the new safeguards.** The escalation triggers only fire if the agent reads and acts on them. If the agent's session produced a RESULT block with `status: complete` and a `files_changed` list that named `loop.py` — but whose actual edits were never applied (write tool failed silently, or the agent hallucinated the edit) — the driver's verification still passes because the code gate checks existing tests, not the presence of new symbols. The 0-token billing is the strongest signal that the session crashed or was trivially short; the driver does not gate-check token count before committing.

**Impact.** T08 (telemetry) depended on T08H. Without `effort_used`/`terseness` in the per-attempt record, T08's schema assertions would fail against a shape that still matches T02's output. T08 ran 79 seconds after T08H completed — per the log, it ran regardless.

---

### T08 — Telemetry extension: `resolved_model`, cache hit rate, gate summary

- **Attempts:** 1 · **Duration:** 79.7s · **Cost:** $0.280
- **Output tokens:** 3,257. Cache read: 443,479 tokens (much smaller — only the post-T08H context slice).
- **FINDING: T08 also silently no-op'd.**

**Smoke check result:**
```
python3 -c "from loop import cache_hit_rate, gate_summary"
ImportError: cannot import name 'cache_hit_rate' from 'loop'
EXIT: 1
```

Neither `cache_hit_rate` nor `gate_summary` exists in loop.py post-gate. `tests/test_loop_telemetry.py` is absent from the tests directory.

T08 ran despite T08H failing to land its dependency. The driver dispatched T08 when T08H's `status` read `done` — which it did, because T08H had committed that status flip. The driver has no mechanism to verify that a `done` WU's code actually exists before unblocking its dependents.

T08's 79-second duration and 3,257 output tokens indicate the agent did run (unlike T08H's 0-token session). It likely produced text output but either: (a) its file writes were not applied to the tree, or (b) it recognised T08H's symbols were absent (violating its Escalation Trigger 4: "if `effort_used`/`terseness` are absent from the per-attempt record, stop and emit `status: blocked`") but the RESULT block was emitted as `blocked` while the driver advanced it anyway, or (c) it edited the wrong path.

The events.jsonl does not record `files_changed` — only cost/duration. No further diagnosis is possible from the log alone.

---

## Gate-level observations

**Total cost:** $5.43 ($1.538 T06 + $3.609 T07 + $0.000 T08H + $0.280 T08)  
**Dispatch order:** T06 → T07 → T08H → T08 (correct; T08H's dependency on T06/T07 was respected)  
**T07 budget brake:** Did not fire. GATE-02.md has no `cost_budget_usd` field; the brake was not exercised.

**T08H smoke check (AC 2 of this WU):**
```
python3 -c "from loop import EFFORT_LADDER, effort_for_attempt"
EXIT: 1
```
T08H's contract was not landed. This is the T04 failure mode repeating in a WU authored specifically to prevent it.

**T06 and T07 landed correctly.** The two WUs with explicit smoke checks in their AC landed cleanly. The correlation is not coincidental: naming the import check in the WU's Verification section gives the agent a concrete gate to run before claiming complete.

**T08H and T08 did not land.** Neither their code symbols nor their test files are present in the post-gate tree. The WU `status: done` fields and events.jsonl `task_completed` events are structurally correct entries that mask empty deliveries.

---

## CRITICAL STRUCTURAL FINDING — T08H/T04 REPEAT FAILURE

**Finding name:** Silent no-op through zero-token session committed as `done`

**Description.** A WU session that produces 0 input/output tokens (T08H: 0/0) is committed to the repository with `status: done` because: (1) the driver squashes whatever edits were staged — if none, only the WU frontmatter update lands; (2) the code gate runs existing tests, which pass unchanged; (3) the driver advances the dependency frontier based on `status: done` in the committed WU file, not on symbol existence.

This failure path defeated both T04's original execution and T08H's corrective re-execution, despite T08H adding three explicit safeguards (smoke-import check in AC, two escalation triggers). The safeguards are agent-side; the driver's verification is corpus-side. The gap is that no driver-side check exists between "WU committed as done" and "dependents unlocked" that asserts newly-required symbols are importable.

**Gate 1 framing (for comparison).** Gate 1's CRITICAL FINDING named this as: "The gate has no mechanism to verify 'the required new test file was created' or 'the required functions exist.'" Gate 2 confirms this gap is load-bearing: even a hygiene WU written to correct it, with explicit smoke checks in its spec, did not close the gap because the driver-side verification still has no completeness check.

**Structural gap requiring escalation.** The driver needs a post-commit, pre-dependency-unlock check: for each WU whose spec names a smoke import in its AC or Verification section, run that command before advancing. Alternatively, the driver should refuse to commit a WU as `done` if its `files_changed` list (from the RESULT block) contains a file that is unchanged from HEAD. Either check would have caught T04, T08H, and T08.

---

# Feature-arc verdict

**Produced by:** WU-97 (G2-PLAN)
**Branch decision:** TERMINAL.
**Date:** 2026-06-07

## What shipped vs `roadmap_goal`

`roadmap_goal`: *Cut loop dispatch cost via per-WU model alias, effort tier, terseness, and per-gate budget.*

All four levers landed in `loop.py` and are importable post-Gate-2:

| Lever | WU | Symbol(s) | Status |
|---|---|---|---|
| Per-WU model alias | T01 | `MODEL_ALIASES`, alias resolution in `dispatch()` | ✅ landed |
| Effort tier | T02 | `VALID_EFFORT`, `--effort` in `CLAUDE_CMD` | ✅ landed |
| Terseness directive | T03 | `CAVEMAN_DIRECTIVE`, tier-gated preamble selection | ✅ landed |
| Per-gate cost budget | T07 | `gate_budget_usd`, `gate_spent_usd`, `_should_halt_for_budget` | ✅ landed |

Defaults-by-WU-type (T06) layered on top of the four levers — `MODEL_BY_TYPE` and `EFFORT_BY_TYPE` make the lever fields optional, so unauthored WUs inherit sensible model/effort without explicit declaration. This is the cost-control story complete: the four levers exist, they have type-driven defaults, and `WU.template.md` documents them as author-controlled.

## What telemetry confirmed

Real Gate 1 + Gate 2 events.jsonl (16 WUs, ~$13.20 total):

- **Effort tier × model defaults work as designed at the cheap end.** T03 (low/medium effort, Sonnet) ran 128s / 4,261 output tokens / $0.40 — less than half the cost of any other substantive WU. Type-default policy assigned Sonnet to implementation WUs and Opus only where the WU spec opted in (T04, T07). This compounds across a gate.
- **Cache reads dominate cost at scale.** T07 cost $3.61 (67% of Gate 2 total) primarily from a 4.5M-token cache-read window — the price of Opus × accumulated feature context, not the price of the lever itself. Cache-read cost grows monotonically with WU count in a gate; the four levers do not address it.
- **Per-gate budget brake did not fire in Gate 2.** GATE-02.md carries no `cost_budget_usd` field — the brake was introduced by T07 and cannot be exercised against the gate that built it. First exercise belongs to a successor feature's gate per `[FEAT-2026-0007/G2-LESSONS]`. The mechanism is in code and unit-tested ($1.00 budget / $1.50 spent → halt); production exercise is the deferred item.
- **Caveman directive landed but its cost-reduction effect is undermeasured.** T03 was cheap, but only one WU at low effort ran in this feature; the directive's empirical effect on output-token volume needs a feature with several low-effort WUs to measure.

## What was deferred

1. **Retry escalation ladder (T04 / T08H).** `EFFORT_LADDER`, `effort_for_attempt`, `terseness_for_attempt` are absent from `loop.py`. T04's original session and T08H's hygiene re-land both committed `status: done` with no production code (T08H billed 0 input/output tokens). Three attempts at agent-side fix proved insufficient — the gap is driver-side, not spec-side. **Candidate future feature: FEAT-2026-0008 Driver completeness-guard** (recommended below).
2. **Telemetry extension (T08).** `cache_hit_rate`, `gate_summary`, `resolved_model` per-attempt field — all absent. Same failure path as T08H. The cost-control story is shipped but its observability is not, so the levers' actual savings cannot be measured retrospectively from `events.jsonl` alone. Belongs in the same future feature as the retry-ladder reland, or its successor.
3. **Per-gate budget brake first exercise.** Set `cost_budget_usd` in the first Gate.md of the next feature that uses this loop, so the brake fires for real. Mechanical, not feature-sized.
4. **Caveman directive empirical measurement.** Needs a feature with ≥3 low-effort WUs to compare output-token volume to a baseline. Not blocking.

## Unresolved `Scope OUT` items

From PLAN.md's `Scope OUT` section, the following remain unresolved at feature close:

- **Prompt-caching SDK migration (`cache_control` breakpoints).** Still gated on a measurement spike of the `claude -p` CLI's built-in caching. Given that cache reads dominate cost in this feature's own telemetry (T07: 4.5M tokens, T06: 2.4M tokens), this is now the **highest-leverage** deferred lever for further cost control. Recommend opening a measurement-first feature against the CLI's caching surface, then deciding whether SDK migration is warranted.
- **Parallel / concurrent WU dispatch.** Unchanged; needs separate design for `git`, `events.jsonl`, working-tree race conditions. FEAT-2026-0004's `flock` lock is the prerequisite (landed) but the dispatcher work is its own feature.
- **Context pruning / per-WU file allowlist.** Unchanged; needs an agent-contract change. The cache-read cost pattern above strengthens the case but does not change the design boundary.
- **Ceremony-WU adaptive strategy.** Was to be planned from this feature's telemetry. Now blocked on telemetry (T08) landing properly in a successor feature.

## Why TERMINAL, not extend

Per `[FEAT-2026-0003/G4-LESSONS]`, extending requires all three tests to pass:

1. **Scope — hours not weeks.** The retry-ladder + telemetry reland looks bounded in code size, but **three attempts at the spec-side fix have already failed** (T04 with no completeness trigger, T08H with three explicit safeguards, T08 with the dependency on T08H). The next attempt must be driver-side: add a post-commit, pre-dependency-unlock symbol-existence check, refuse-commit-on-empty-files_changed, or 0-token-attempt detection. That work is the driver's verification contract, not a single hygiene WU — multiple file changes in `loop.py`, new unit tests against a real dispatch path, and a methodology decision about whether the agent's RESULT block's `files_changed` claim is verified pre-commit. This **fails the "hours not weeks" test** by failing the "single WU" interpretation: the fix is a feature, not a hygiene precursor.
2. **Contiguous proof — yes.** All evidence (events.jsonl 0-token entries, two LEARNINGS entries) is on this branch.
3. **Disciplined trigger — yes.** The evidence is live and concrete (T04 + T08H + T08 = three reproductions of the same failure mode in real telemetry).

Tests 2 and 3 pass. Test 1 fails on the substantive sizing. Per the lesson's own rule: *"If any [test] fails, the correct move is to write the terminal verdict and open a new feature later if needed."*

The cost-control roadmap_goal is met independent of the methodology gap — extending Gate 3 of this feature to fix the driver-side completeness gap would conflate two different threads and corrode the "feature ends" contract.

## Methodology-level correctness gap (Escalation trigger 3 — fired)

T08H was authored specifically to prevent T04's failure mode and **repeated it exactly**: 0 input tokens, 0 output tokens, 225s elapsed, `status: done` committed, no symbols landed. Three safeguards in T08H's spec (smoke-import AC, two escalation triggers) did not fire because the agent session produced no output to evaluate them against.

This is a **driver-side correctness gap**, not an authoring gap. Agent-side safeguards require an agent session that actually runs. The fix shape:

- **Mandatory recommendation for next feature (FEAT-2026-0008 candidate, "Driver completeness-guard"):**
  1. The driver MUST treat a 0-input-token attempt as a failed attempt (re-dispatch), not a completed one. The `attempts_usage[].input_tokens > 0` check is mechanical and falsifiable.
  2. If the WU's RESULT block declares `files_changed: [paths…]`, the driver MUST verify each path differs from `HEAD` before squashing — refuse the commit and re-dispatch otherwise.
  3. If the WU's Verification section names a `python3 -c "from X import Y"` smoke check, the driver MUST run it after squash and before advancing the dependency frontier — fail the WU if it exits non-zero.

Any one of those three would have caught T04, T08H, and T08 at the driver layer. All three together close the gap structurally. They are NOT in scope for this feature, and the temptation to extend Gate 3 to add them is what `[FEAT-2026-0003/G4-LESSONS]` warns against.

## Roadmap-goal sanity check (Escalation trigger 2 — NOT fired)

The `roadmap_goal` itself is not wrong. The four levers shipped and have the expected effect (T03's $0.40 cheap-end run, type-default model assignment doing what the spec said). What was undermeasured is the **aggregate cost-reduction percentage** vs a baseline — because the telemetry that would have measured it (T08) did not land. The goal is correct; the proof is partial. The successor feature that lands telemetry will close the proof.

## Summary

- Four cost-control levers landed; type-default policy layered cleanly on top.
- Retry ladder and telemetry deferred to next feature due to driver-side completeness gap that defeated three reland attempts.
- Cache-read cost (an architectural cost driver this feature does not address) is now the highest-leverage deferred lever — recommend a measurement-first feature on `claude -p` caching.
- Methodology gap is loudly named; FEAT-2026-0008 "Driver completeness-guard" recommended as the next feature.

Feature closes as **done**.
