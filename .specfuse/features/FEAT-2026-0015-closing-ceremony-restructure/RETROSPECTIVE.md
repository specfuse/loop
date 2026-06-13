---
feature_id: FEAT-2026-0015
gate: 1
correlation_id: FEAT-2026-0015/G1-RETRO
---

# Gate 1 retrospective — Closing-ceremony restructure

## Per-WU analysis

### T01 — Add `close-intermediate` WU type and extend `close` to any terminal gate

**Status:** done | attempts: 1  
**Cost:** $0.418768 | Duration: 159.391s

**What worked.** Clean single-attempt execution. Agent added `close-intermediate` to all three driver dicts (`MODEL_BY_TYPE`, `EFFORT_BY_TYPE`, `GATES_FOR_TYPE`), wrote four targeted unit tests, and left all existing entries untouched. The helper-duplication trigger in AC3 (§10 grep check) executed correctly — agent confirmed exactly one definition site per dict. Symbol-existence check and full test suite passed without incident.

**What failed.** Nothing. No re-arms, no blocking.

**Rules/templates/boundaries.** No gaps surfaced. The "do not touch" boundary (exactly 2 files) was respected.

**Generalizes.** Additive-only dicts with explicit "add never modify" constraints and a pre-edit §10 grep check are a reliable guard against silent regressions in driver constants.

---

### T02 — Update `lint_plan.py` to accept new closing-WU shapes

**Status:** done | attempts: 1  
**Cost:** $1.163975 | Duration: 453.975s

**What worked.** Agent implemented the full closing-shape taxonomy: `NEW_INTERMEDIATE_SEQUENCE`, updated `_CLOSING_TYPES`, 2-WU non-terminal pass, 1-WU terminal pass for any-gate, legacy 4-WU warning, mixed-shape hard error. Existing `test_lint_close_wu.py` was correctly updated to drop the single-gate restriction. Helper-duplication §10 grep returned no duplicates outside `lint_plan.py` and tests.

**What failed — spec gap in T02.** T02 did NOT update `CORRELATION_ID_RE` to accept `G<n>-CLOSE-INTERMEDIATE` suffixes. The rule `.specfuse/rules/correlation-ids.md` (lines 130-132) explicitly requires updating the regex when adding a closing type, but T02's WU file did not include `CORRELATION_ID_RE` in its acceptance criteria. This was a spec omission, not an agent error: the agent touched `VALID_TYPES` and closing-shape logic as specified but had no AC pointing at the regex.

The gap was surface by T03's first attempt (see below). A hygiene WU (T02H) was drafted and inserted before T03 re-ran.

**Rules/templates/boundaries.** Gap identified: WU authoring for `lint_plan.py` changes must check `CORRELATION_ID_RE` as a coupling point whenever a new closing type is added. This is now documented in `correlation-ids.md` via T02H but the gap wasn't pre-empted by the T02 WU's escalation triggers or its "do not touch" commentary.

**Generalizes.** When a file has both a type registry (`VALID_TYPES`) and a separate regex (`CORRELATION_ID_RE`) that encode overlapping knowledge, a WU that updates one must also check the other — or the two diverge silently until a downstream WU surfaces it.

---

### T02H — Hygiene: extend correlation-ID grammar to include `CLOSE-INTERMEDIATE`

**Status:** done | attempts: 2  
**Cost:** $0.984542 | Duration: 383.343s  
*(T02H was unplanned at feature-draft time; inserted between T02 and T03 after T03's first escalation.)*

**What worked.** Agent updated `CORRELATION_ID_RE` with `CLOSE-INTERMEDIATE|CLOSE` ordering (longest-first, correct) and updated `correlation-ids.md` prose + regex example. Wrote three new tests plus a rejection test. All passed.

**What failed.** Two attempts logged. The first attempt produced a `files_changed_mismatch` (based on the WU's `attempts: 2` with no human escalation recorded). Driver retried; second attempt succeeded. The specific mismatch is not recorded in `events.jsonl` because T02H's first-attempt failure predated the events.jsonl preservation fix (see § What surprised us below).

**Rules/templates/boundaries.** No authoring gaps beyond the T02 spec omission already noted. The §10 helper-duplication trigger correctly identified `gate-status/SKILL.md` and `feature-conversion/SKILL.md` as out-of-scope surfaces that mention legacy closing IDs, recommending a follow-on hygiene WU.

---

### T03 — Update templates and `/draft-feature` skill to emit new closing shapes

**Status:** done | attempts: 3 (1 escalated + 2 fresh)  
**Cost (productive):** $1.532889 | Duration: 585.32s  
**Cost (diagnostic/wasted):** $0.950612 | Duration: 422.703s  
**Total T03 cost across all dispatches:** $2.483501

**What worked.** On the re-armed dispatch, agent correctly updated all four targets (`PLAN.template.md`, `WU.template.md`, `draft-feature/SKILL.md`, `tests/test_template_closing_shapes.py`). Template self-consistency (AC1/AC2 agreement) held. Lint ran clean against the updated template.

**What failed — first dispatch (escalated, agent-reported blocked).**
T03's first attempt surfaced the T02 `CORRELATION_ID_RE` gap (see T02 above). Agent correctly identified: `CORRELATION_ID_RE.match('FEAT-2026-0000/G1-CLOSE-INTERMEDIATE') → False` and escalated with `status: blocked`. This was proper behavior per result-contract.md §3: "Blocked is a valid, respectable outcome." The $0.950612 spend was not wasted — it produced the diagnostic evidence that drove the T02H insertion.

**What failed — second dispatch (files_changed_mismatch, attempt 1).**
After T02H landed, T03 re-armed unmodified. The second dispatch's first attempt exited `files_changed_mismatch` (4 unchanged paths logged in events.jsonl: `PLAN.template.md`, `WU.template.md`, `draft-feature/SKILL.md`, `tests/test_template_closing_shapes.py`). Agent made no file changes that attempt. Driver retried; second attempt in the same dispatch completed successfully.

The `files_changed_mismatch` on a re-armed WU after a hygiene insertion is a recurring pattern: agent may re-read stale cached state from the prior blocked session rather than the fresh post-T02H filesystem. No framework-level mitigation currently exists.

**Rules/templates/boundaries.** T03's escalation trigger #3 (§10 helper-duplication grep for closing-WU IDs across skills) ran and returned `gate-status/SKILL.md:81`, `feature-conversion/SKILL.md:90` as out-of-scope — correctly listed in RESULT block without silent edit. No rule gap beyond the T02H pre-condition surfaced above.

---

## Gate-level summary

| Metric | Value |
|--------|-------|
| Dispatch order | T01 → T02 → T02H (inserted) → T03 |
| WUs that spun | T02H (files_changed_mismatch on attempt 1); T03 (files_changed_mismatch on 2nd-dispatch attempt 1) |
| Human escalations | 1 — T03 first dispatch escalated with `agent_reported_blocked` |
| Re-arms | 1 — T03 re-armed unmodified after T02H landed |
| Hygiene WUs inserted | 1 — T02H, not in original plan |
| Planned WU count | 3 (T01, T02, T03) |
| Actual WU count | 4 (T01, T02, T02H, T03) |

**Total Gate 1 substantive cost (all attempts):**  
$0.418768 (T01) + $1.163975 (T02) + $0.984542 (T02H) + $2.483501 (T03 all dispatches) = **$5.050786**

---

## Cost analysis

| WU | Type | Effort | planned_cost_usd | actual_cost_usd | delta $ | delta % |
|----|------|--------|-----------------|-----------------|---------|---------|
| T01 | implementation | medium | $1.00 | $0.418768 | -$0.581 | **-58%** |
| T02 | implementation | medium | $1.00 | $1.163975 | +$0.164 | +16% |
| T02H | implementation (unplanned) | low | $0.50 ¹ | $0.984542 | +$0.485 | **+97%** |
| T03 | implementation | low | $0.50 | $1.532889 ² | +$1.033 | **+207%** |
| T03 (wasted) | — | — | — | $0.950612 | — | — |
| **Gate 1 substantive total** | | | **$3.00** ³ | **$5.050786** | **+$2.051** | **+68%** |

¹ T02H was unplanned; $0.50 planned cost added post-insertion to PLAN.md.  
² T03's `cost_usd` field captures only the productive dispatch (2 attempts, $1.532889). Wasted attempt shown separately.  
³ Planned total uses post-insertion T02H planned cost of $0.50.

**Variance rationale — T01 (-58%).**  
T01 was scoped as `effort: medium` and planned at $1.00. It completed in a single 159-second attempt with high cache-read efficiency (596K cache-read tokens vs 44K cache-creation tokens), suggesting the agent leveraged existing context very efficiently. The task was also additive-only (no existing logic to reason about, no edge-case handling required beyond the three dict entries and four unit tests). `medium` effort classification likely overestimates for pure-additive dict extension work; `low` with $0.50 would have been more accurate.

**Variance rationale — T02H (+97%).**  
T02H was planned at $0.50 (effort: low) but ran $0.984542 across two attempts. The regex change itself is low-complexity, but the surrounding verification surface is high: the agent needed to read `lint_plan.py`, `correlation-ids.md`, understand the alternation ordering gotcha (longest-first), write four targeted tests, and run the full test suite. Two attempts roughly doubled the expected cost. `low` effort was undersized; `medium` ($0.80–$1.00) would have been appropriate given the regex correctness surface and two-file touch with documentation.

**Variance rationale — T03 (+207% on productive cost alone).**  
T03's $0.50 planned cost was drastically undersized. The WU touched four files (two templates, one skill, one test file), required verifying template self-consistency against lint, and had a complex §10 helper-duplication check across the entire `.specfuse/` tree. Even without the wasted dispatch, two attempts at 585 seconds totaling $1.53 is 3× the plan. Adding the $0.95 diagnostic dispatch raises the real cost to $2.48 — nearly 5× planned. The `low` effort classification was wrong; `medium` ($0.80–$1.00) would still have undershot. The spec-gap escalation (T02H dependency not yet met) and subsequent re-arm are structural cost multipliers that planned-cost estimation must account for when a WU has unresolved upstream dependencies at draft time.

---

## What surprised us

**The dogfood inversion.** Gate 1's own closing ceremony uses the OLD 4-WU sequence (`G1-RETRO → G1-LESSONS → G1-DOCS → G1-PLAN`). This feature is simultaneously authoring the new closing contract AND closing its own first gate with the contract it is replacing. This is intentional — PLAN.md explicitly notes "last feature to pay full close tax on this branch" — but it creates an unusual meta-context: this retrospective documents a feature whose artifacts (templates, skill, lint rules) already assume the new shape, while the closing WUs executing it are using the old shape. Any operator reading this feature's closing WUs as exemplars will see the OLD pattern. The PLAN.md note and PLAN.template.md comment both call this out, but it is still easy to miss.

**Events.jsonl preservation gap.** T01's events were captured. T02's and T02H's events were NOT captured in `events.jsonl` — the file contains no `task_started` or `task_completed` entries for either. The commit `b431001 fix(loop): preserve events.jsonl across git reset --hard head_before` landed during this gate's execution, meaning T01 was dispatched before the fix and its events were written before the next `git reset --hard` clobbered them — except T01's events survived (perhaps the fix landed before T02). T02 and T02H events appear to have been lost to a `git reset --hard` after the fix was nominally applied, or the fix landed between T02H and T03. The practical consequence: this retrospective reconstructs T02 and T02H costs from WU frontmatter (`cost_usd`, `duration_seconds`), not from `events.jsonl`. The driver-level cost-capture is therefore the ground truth even when events.jsonl has gaps.

**T03's `files_changed_mismatch` after re-arm.** After T02H resolved the blocking condition, T03 re-armed with its WU file unmodified. The second dispatch's first attempt exited `files_changed_mismatch` with all four expected target files unchanged. This suggests the agent re-entered the session, read the WU file and codebase, but then failed to produce any file writes on its first attempt. A plausible cause: the re-armed session inherited cached tool-call state from the prior blocked session that prevented it from seeing T02H's changes as "new context requiring action." This is a known fragility in re-armed WUs after hygiene insertions — the agent may need an explicit cache-bust signal or a rewritten WU preamble to avoid this.

**Helper-duplication §10 worked as designed — and caught a real gap.** The `authoring-work-units §10` helper-duplication trigger (added after FEAT-2026-0013's ship-fail cycle) was explicitly required in all three T01-T03 escalation trigger sections. T01 ran it cleanly (no duplicates). T02 ran it and confirmed no production code outside `lint_plan.py` carried its own copy of the closing sequence. T03 ran it and returned two out-of-scope surfaces (`gate-status/SKILL.md:81`, `feature-conversion/SKILL.md:90`) that were correctly listed in the RESULT block without silent edit. No §10 violation triggered a `status: blocked` on these units, which means the guard is functioning as intended: surface duplication, escalate if it would cause a partial-update defect, otherwise document and defer. Gate 1 is §10's first real production test, and it passed.

However, the T02 spec omission (`CORRELATION_ID_RE` not updated) represents a case where §10 coverage was incomplete: the grep checked for `CLOSING_SEQUENCE|_CLOSING_TYPES` coupling but not for the regex coupling with the closing-type lexicon. The lesson is that §10 checks must be authored with the specific coupling points of the target file in mind, not just the obvious symbol names.

---

## Focus for Gate 2 plan-next WU

1. **Verify the `files_changed_mismatch` re-arm fragility** (T03 second dispatch, attempt 1) has a driver-level mitigation or documented workaround before G2 WUs that depend on G1 outputs are dispatched.
2. **Cost estimation calibration.** Gate 1's 68% gate-level overrun (and 207% on T03 alone) signals that `low` effort = $0.50 is systematically undersized for WUs touching multiple files with documentation coupling. G2 WU plans should use `medium` ($0.80–$1.00) as the floor for any WU touching more than one file.
3. **T02H class of gap.** Lint + regex coupling is a structural risk whenever `lint_plan.py` gains a new constant. G2's T04-T08 WUs should include explicit escalation triggers checking all coupled surfaces (VALID_TYPES ↔ CORRELATION_ID_RE ↔ correlation-ids.md) as a triple rather than independently.
4. **Events.jsonl coverage.** Confirm the `git reset --hard` preservation fix is solid across all G2 dispatch paths before dispatching T04.
