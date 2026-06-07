# Retrospective — FEAT-2026-0006 (WU execution-time tracking)

Gate 1, single-gate feature. Closed with the combined `close` WU type — first live
use of FEAT-2026-0005's output.

## WU breakdown

### FEAT-2026-0006/T01 — Capture per-WU execution time alongside cost

| Field | Value |
|---|---|
| Attempts | 1 |
| Cost | $0.9966 |
| Outcome | done |

**What worked.** Riding the existing cost-plumbing pattern (`cum_usage` accumulator,
`write_cost_to_wu`, `attempts_usage` list) made duration a natural add-on.
`time.monotonic()` is stdlib — no new dependency. Tests followed the existing
stubbed-dispatch pattern (`StubBackend`, mock subprocess) without requiring new
infrastructure. The three-file scope bound (loop.py, WU.template.md,
tests/test_duration_tracking.py) matched the actual diff exactly.

**What failed.** Nothing — first attempt, no escalation.

**Bootstrap observation.** T01 implements the timing mechanism that would record its
own execution time, but the driver dispatching T01 runs old loop.py (before T01's
commit lands). Therefore T01's `task_completed` event in `events.jsonl` has no
`duration_seconds` in `attempts_usage`, and T01's frontmatter has no
`duration_seconds` field. This is expected — the bootstrap gap is structural, not a
bug. The first WU timed by the new mechanism is G1-CLOSE (dispatched after T01's
commit is applied).

**Missing or ambiguous rules/templates.** None — the spec was precise, the escalation
trigger was explicit, and the Do-not-touch scope was clearly bounded with a named file
count.

---

### FEAT-2026-0006/G1-CLOSE — Combined closing ceremony

| Field | Value |
|---|---|
| Attempts | 1 |
| Type | close (first live use) |
| Outcome | done |

**What worked.** The `close` WU type is structurally sound. A single session handles
RETROSPECTIVE.md, LEARNINGS.md generalizability evaluation, roadmap/docs
reconciliation, and the feature-arc verdict without scope pressure. Collapsing four
dispatches into one is justified for single-gate features.

**Did the close ceremony work?** Yes. The four obligations (RETROSPECTIVE.md,
LEARNINGS.md, docs/roadmap, feature-arc verdict) mapped cleanly to one session. No
structural ambiguity was encountered; the WU spec's escalation conditions did not fire.

**What was missing.** No example RETROSPECTIVE.md exists in the fixture feature
(FEAT-2026-0001-health-endpoint). The agent inferred structure from the four-WU
closing sequence's known outputs. A short example in the fixture would reduce
first-attempt guesswork for future single-gate features using `close`. This is
feature-specific noise — not a blocking gap, but an improvement opportunity for the
fixture.

---

## Feature-arc retrospective — FEAT-2026-0006

**Roadmap goal:** "The loop records each work unit's wall-clock execution time
alongside the cost it already captures."

**Verdict: MET.**

Evidence from T01:

- `loop.py` measures each attempt's wall-clock time with `time.monotonic()` (start
  at dispatch, stop after verification) and writes `duration_seconds` into that
  attempt's `attempts_usage` entry in `events.jsonl`.
- Cumulative `duration_seconds` (rounded to 3 decimals) is written to the WU's
  frontmatter at outcome time (PASS / BLOCKED / SPINNING) via `write_cost_to_wu`,
  alongside `cost_usd`.
- Duration capture is independent of `cost_tracking` — it runs even when
  `cost_tracking: false`. Verified by `tests/test_duration_tracking.py::TestDurationTrackingCostDisabled`.
- `WU.template.md` documents `duration_seconds` as a driver-owned frontmatter field,
  noting that per-attempt duration appears in `events.jsonl`'s `attempts_usage` list
  alongside cost/token fields.
- Tests assert all three behaviors: per-attempt capture, cumulative summing across a
  failed-then-passed sequence, and frontmatter write.

PLAN.md's task graph is unchanged — single gate, no gate 2 was planned or added.
