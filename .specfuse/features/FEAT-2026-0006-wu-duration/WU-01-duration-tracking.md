---
id: FEAT-2026-0006/T01
type: implementation
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.996561
input_tokens: 32
output_tokens: 14843
---

# Capture per-WU execution time alongside cost

**Objective.** Record each work unit's wall-clock execution time — per-attempt in
`events.jsonl` and cumulative on the WU's frontmatter — using the same plumbing
that already records cost.

**Context.** This is `FEAT-2026-0006/T01`. `loop.py`'s `run()` already tracks
cost per WU: each attempt's usage is appended to `attempts_usage` (flushed to
`events.jsonl`), and a `cum_usage` dict is summed and written to the WU
frontmatter at outcome time via `write_cost_to_wu` (fields `cost_usd`,
`input_tokens`, `output_tokens`). Duration rides the same path with
`time.monotonic()` (stdlib). Grounding: the attempt loop in `run()`,
`execute_unit_attempt`, `write_cost_to_wu`, and the `attempts_usage`/`cum_usage`
accumulators. Reference the binding rules under `.specfuse/rules/`; honor
`result-contract.md`, `never-touch.md`. The driver owns all git.

**Acceptance criteria.**
1. Each attempt's **whole-attempt** wall-clock (dispatch + verify) is measured
   with `time.monotonic()` and recorded as `duration_seconds` on that attempt's
   `attempts_usage` entry in `events.jsonl`.
2. A cumulative `duration_seconds` (summed across the WU's attempts) is written to
   the WU's frontmatter at outcome time (PASS / BLOCKED / SPINNING), alongside
   `cost_usd`, rounded to 3 decimals.
3. Duration is captured **even when `cost_tracking` is `false`** — it does not
   depend on the `claude -p` JSON usage block.
4. `WU.template.md`'s frontmatter notes document `duration_seconds` as a
   driver-owned field (like the cost fields).
5. Tests in `tests/` assert: a single attempt records a `duration_seconds`;
   cumulative duration sums across a failed-then-passed sequence; the cumulative
   value is written to frontmatter. Use the existing stubbed-dispatch test
   pattern — no real `claude -p`.

**Do not touch.** The `Backend` seam / `make_backend`, the working-tree lock
helper, the `close`-type machinery, `lint_plan.py`, `gh_features.py`,
`adopt_feature.py`, `gh_backend.py`, the verification gate *commands*, binding
rules, secrets, `.git/`. The driver owns git — edit files only. Files this WU
changes: `.specfuse/scripts/loop.py`, `.specfuse/templates/WU.template.md`, and a
test file under `tests/`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests,
ruff, bandit, coverage ≥ floor). Run them in order. `time` is stdlib — no new
dependency.

**Escalation triggers.** If folding duration into `execute_unit_attempt`'s return
value breaks the existing cost-tracking tests' contract, stop and emit
`status: blocked` naming the conflict rather than reshaping the signature
silently. Measure with `time.monotonic()` (monotonic clock), never wall-clock
`time.time()`, so the duration is unaffected by clock adjustments.
</content>
