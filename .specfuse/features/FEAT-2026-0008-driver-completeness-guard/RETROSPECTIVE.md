# Retrospective — FEAT-2026-0008 Driver completeness-guard

Single-gate feature. Three independent substantive WUs (T01/T02/T03) plus
this `G1-CLOSE` ceremony. The whole point of the feature was to close the
hollow-pass gap that swallowed FEAT-2026-0007/T04, T08H, and T08 — so the
retrospective leads with the diagnostic audit (AC 2), then per-WU notes.

## Guard-helper existence audit

Recursive check: did the guards this feature was built to add actually
land?

| Check | Result | Source of truth |
|---|---|---|
| `grep -c "def is_zero_token_attempt" .specfuse/scripts/loop.py` | `1` | `loop.py:711` |
| `grep -c "def verify_files_changed" .specfuse/scripts/loop.py` | `1` | `loop.py:622` |
| `grep -c "def extract_smoke_imports" .specfuse/scripts/loop.py` | `1` | `loop.py:669` |
| `grep -c "def run_smoke_imports" .specfuse/scripts/loop.py` | `1` | `loop.py:684` |
| `ls tests/test_loop_zero_token_guard.py` | present | `tests/` |
| `ls tests/test_loop_files_changed_guard.py` | present | `tests/` |
| `ls tests/test_loop_smoke_runner.py` | present | `tests/` |

All four helpers exist AND are wired into the attempt loop in `run()`:

- `loop.py:885` — `is_zero_token_attempt(usage)` called immediately after
  `dispatch()` returns, before RESULT-block parse (T01 AC 2).
- `loop.py:901` — `verify_files_changed(parsed, head_before)` called
  between RESULT-block parse and `squash_commit` (T02 AC 3).
- `loop.py:1110`-`loop.py:1112` — `extract_smoke_imports(wu.body)` then
  `run_smoke_imports(...)` called between successful verify+squash and the
  `set_wu(wu, "status", DONE)` flip (T03 AC 3).

**Audit verdict: PASS.** No hollow pass detected. The feature did not
recursively reproduce the failure it was built to fix.

## Per-WU notes

Evidence cited from `.specfuse/features/FEAT-2026-0008-driver-completeness-guard/events.jsonl`.

### T01 — Zero-token attempt guard

- **Attempts:** 1. Cost $2.61, duration 392 s, input_tokens 46,
  output_tokens 19735 (events.jsonl line 2 `task_completed`).
- **What worked.** Helper `is_zero_token_attempt(usage)` landed at
  `loop.py:711` with the exact contract the WU specified (returns `False`
  for `None` to preserve cost-tracking-off behavior, `False` for missing
  key, `True` only when `input_tokens == 0`). Wiring at `loop.py:885`
  fires before the RESULT-block parse — exactly the placement T01 AC 2
  named.
- **What failed.** Nothing. One-attempt clean.
- **Rule/template/boundary gap.** None. The WU's escalation triggers
  (completeness, cost-tracking-disabled regression, spinning-path overlap)
  bounded the work cleanly.

### T02 — `files_changed` diff guard

- **Attempts:** 1. Cost $1.75, duration 337 s, input_tokens 22,
  output_tokens 21351 (events.jsonl line 4 `task_completed`).
- **What worked.** `verify_files_changed(result, head_before)` at
  `loop.py:622` returns the list of agent-claimed paths that don't differ
  from HEAD; wiring at `loop.py:901` runs between `parse_result_block`
  and `squash_commit`, which is the exact sequencing T02 AC 3 demanded.
  Critically: it runs **before** `git add -A`, so the working-tree diff
  against `head_before` is meaningful (escalation trigger 3 averted).
- **What failed.** Nothing. One-attempt clean.
- **Rule/template/boundary gap.** None. Empty `files_changed` correctly
  opts out (AC 4) — pre-existing WU compatibility preserved.

### T03 — WU-Verification smoke-import runner

- **Attempts:** 1. Cost $1.66, duration 324 s, input_tokens 1256,
  output_tokens 22030 (events.jsonl line 6 `task_completed`).
- **What worked.** Both helpers landed: `extract_smoke_imports` at
  `loop.py:669` (conservative regex, import-form only) and
  `run_smoke_imports` at `loop.py:684`. Wiring at `loop.py:1110`-`:1112`
  places the smoke step between a successful `squash_commit` and the
  status-flip-to-done, with rollback to `head_before` on failure.
- **What failed.** Nothing. One-attempt clean. Notable: this WU has the
  highest `input_tokens` (1256) of the three, consistent with the broader
  surface (regex + subprocess + rollback sequencing).
- **Rule/template/boundary gap.** None. The conservative regex (escalation
  trigger 2) held: free-form `python3 -c` is not executed, only the
  import form.

## Cross-WU observations

- **Three for three, one attempt each, no escalations.** $6.01 total
  feature cost, ~17 min total dispatch time. The three guards landed in
  the order T01 → T02 → T03 (independent in the graph, sequenced by
  driver dispatch order). No spinning, no `blocked_human`, no failure
  notes threaded between attempts.
- **The independent-WU design paid off.** PLAN.md's `Task graph` declared
  T01/T02/T03 with `depends_on: []` for all three; this let them dispatch
  back-to-back without inter-WU coordination. Each guard touches a
  different point in the dispatch / squash / advance pipeline (parse
  boundary, pre-squash, post-squash) and the no-shared-state design kept
  the WU specs orthogonal.
- **The completeness escalation triggers (per
  `[FEAT-2026-0007/G1-LESSONS]`) were the agent-side guard that closed
  the gap before this feature's driver-side guard exists.** Each WU
  carried a "If [function_name] is absent from your edits, emit
  `status: blocked`" trigger. None fired — the work was actually
  produced. With the driver-side guards now landed, this agent-side
  belt-and-suspenders is no longer load-bearing for future features but
  remains documented in LEARNINGS as defense-in-depth.
- **No rule/template/boundary gaps surfaced.** Each WU's body was the
  spec the agent needed; no clarifying questions, no ambiguous
  requirements observed in retrospect.

## Lessons promotion

One generalizable lesson appended to root `.specfuse/LEARNINGS.md` tagged
`FEAT-2026-0008/G1-CLOSE`: the close-ceremony recursive audit pattern.
See LEARNINGS for the entry. Other observations in this retrospective
are feature-specific and stay here.

# Feature-arc verdict

**`roadmap_goal` met.**

The goal — *"The driver refuses to commit a WU as `done` when the
dispatched session produced no real work, so hollow passes (status-flip-
only commits) cannot land"* — is structurally achieved by the union of
the three guards landed in Gate 1:

1. **Zero-token guard** (`is_zero_token_attempt`, `loop.py:711`, wired at
   `:885`) catches the exact failure path that swallowed FEAT-2026-0007/
   T04, T08H, T08: a session billing `input_tokens: 0` cannot produce
   real edits, so it's treated as a failed attempt before its RESULT
   block is even parsed.
2. **`files_changed` diff guard** (`verify_files_changed`, `loop.py:622`,
   wired at `:901`) catches the broader failure mode where an agent
   *does* run but produces no real diff — the RESULT block's claim is
   verified against the working tree before squash.
3. **Smoke-import runner** (`extract_smoke_imports` + `run_smoke_imports`,
   `loop.py:669`/`:684`, wired at `:1110`-`:1112`) catches the partial
   case where files change but the named symbols don't actually import —
   the WU-declared smoke check is *executed*, not assumed.

Per the FEAT-2026-0007 verdict's mandatory recommendation, **any one** of
the three would have caught T04/T08H/T08; **all three together** close
the gap structurally. AC 2's audit confirms all three are present in
`loop.py` AND wired into the attempt loop in `run()`.

**No hollow pass detected.** The recursive failure mode this close
ceremony was instrumented to detect (T01/T02/T03 hollow-passing despite
the guards) did not occur. Each WU billed positive tokens, produced real
diffs, and exercised its named symbols in tests.

**Recovery action:** none required. The deferred FEAT-2026-0007 work
(T04 retry escalation ladder, T08 telemetry) can now be relanded under
the planned **FEAT-2026-0009** with the guards in place — the third
silent-no-op is now structurally impossible.
