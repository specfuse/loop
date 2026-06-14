# Retrospective — FEAT-2026-0018 (auto-close predicate)

Intermediate retrospective written at gate-1 close. Terminal feature-arc
verdict belongs to G3-CLOSE.

## Gate 1 — `gate_eval.py` module + tests + backtest CLI

Gate 1 shipped the pure module (`.specfuse/scripts/gate_eval.py`),
its unit-test scaffold + 15 fixtures (`tests/test_gate_eval.py`,
`tests/fixtures/gate_eval/**`), and the CLI + calibration regression
(`tests/test_gate_eval_calibration.py`). Driver wiring stays out —
that is gate 2. No blocked_human escalations fired; no replan
events; all substantive WUs landed in ≤ 2 attempts.

### T01 — Standalone `gate_eval.py` module

- Attempts: 2 (first attempt 666 s, $1.56; second 674 s, $1.29).
- Blockers: first attempt did not satisfy AC8 symbol-existence
  check (likely missed one of the 10 required symbol grep matches);
  re-dispatch landed clean.
- Surprises: the second-attempt cost was nearly identical to the
  first despite a much smaller delta — cache-read amplification
  on the re-dispatch's full-spec reload (~1.87M cache-read tokens
  on attempt 2) makes a "small fix" attempt almost as expensive
  as a fresh one. Cost model that assumes attempt-2 << attempt-1
  is wrong on this codebase.

### T02 — Unit tests + ≥ 90% coverage

- Attempts: 1.
- Blockers: none.
- Surprises: 92,062 output tokens on a single dispatch — above the
  80k split-signal from `[FEAT-2026-0003/G2-LESSONS]`. The spec
  listed 15 named test classes + 12 distinct lintable fixture
  directories (each requiring its own PLAN.md + WU files +
  optional events.jsonl, all lint-clean against `lint_plan.py`).
  That is structurally test-scaffolding-at-scale, not standard
  "write the tests"; the planner's `implementation/high` $1.50
  default priced it as the latter. The single-attempt completion
  is to the agent's credit, not evidence the estimate was right.

### T03 — CLI + calibration regression

- Attempts: 1.
- Blockers: none.
- Surprises: 5.3M cache-read tokens on a single attempt. The
  calibration test scans 4 historical feature folders
  (FEAT-2026-0013/0014/0015/0017) into context for baseline
  pinning; each carries a non-trivial PLAN.md + WU graph +
  events.jsonl. Reading-history-as-fixture has a cache-amplified
  cost that the planner did not model.

## Cost analysis

Substantive WUs in scope (per T01 AC7, closing-WU types are
excluded from per-WU ratio checks; G1-CLOSE-INTERMEDIATE and
G1-PLAN are this WU and the next, with `cost_usd` not yet
recorded). Reference: predicate v1 criterion 3 (≤ 1.5×) and
criterion 4 (≤ 2×) from PLAN.md "Predicate v1".

| WU | planned_cost_usd | cost_usd | ratio | delta | criterion 3 (≤ 1.5×) | criterion 4 (≤ 2×) |
|----|------------------|----------|-------|-------|----------------------|---------------------|
| T01 | $1.80 | $2.85459 | 1.586× | +58.6% | FAIL | pass |
| T02 | $1.50 | $4.181495 | 2.788× | +178.8% | FAIL | FAIL |
| T03 | $0.80 | $2.471325 | 3.089× | +208.9% | FAIL | FAIL |
| **gate 1 sub-total (substantive)** | **$4.10** | **$9.50741** | **2.319×** | **+131.9%** | — | — |

Original gate budget (GATE-01.md): $8.00. Substantive spend
$9.50741 already exceeds the original budget by 18.8% **before**
this WU + G1-PLAN have run. Budget was raised mid-flight to
$14.00 in GATE-01.md frontmatter (annotated there) so the gate
remains evaluable under predicate-v1 criterion 6 once close-WU
costs land; the raise itself is acknowledged drift, captured
honestly in the GATE-01.md comment rather than backfilled to
look like the original plan.

Predicate-v1 self-evaluation against this gate's own data
(criterion 3 ≤ 1.5×, criterion 4 ≤ 2×): all three substantive
WUs trip criterion 3; T02 and T03 also trip criterion 4. Gate 1
would NOT auto-close under its own predicate. Meta-confirmation:
the predicate this feature ships correctly identifies this
gate as off-plan — close-intermediate ceremony was warranted.

### Variance > 50% rationale (all three substantive WUs)

Three independent WUs each overran ≥ 1.5×, and two exceeded 2×.
Treating these as three independent estimation misses
overconstrains the lesson: the systematic pattern is one cause
visible three times.

- **T01 (+58.6%).** Two attempts; second attempt's cost matches
  the first despite the much smaller delta because cache-reload
  on re-dispatch dominates the bill. Per-attempt costs are not
  independent and not roughly halving on a "small fix" retry.
- **T02 (+178.8%).** Single attempt, but 92k output tokens —
  above `[FEAT-2026-0003/G2-LESSONS]`'s 80k split-signal. Spec
  density (15 test classes + 12 lint-clean synthetic fixture
  directories) was priced at the standard `implementation/high`
  $1.50 default, which assumes "tests for the thing T01 ships,"
  not "test scaffolding at scale plus a fixture corpus." Wrong
  pricing model, not wrong execution.
- **T03 (+208.9%).** Calibration regression reads 4 historical
  feature folders as fixtures. 5.3M cache-read tokens is the
  signature of fixture-as-context, not fixture-as-checked-in
  test data. The planner priced T03 as "small CLI add" — the
  CLI alone would have hit ~$0.50; the calibration test's
  history-read drove the rest.

Shared cause: the planning model priced every WU by `effort`
band only (`implementation/high` → $1.80, `implementation/medium`
→ $0.80) without adjusting for spec density (named-classes
count, fixture count, history-folder reads). The estimates
were off by a factor proportional to the unmodeled inputs.

## Notes on docs/roadmap

Gate 1 ships an internal module with no operator-facing surface:
no skill changes, no docs/methodology updates, no roadmap row
edits required. The `assert_doc_or_roadmap_diff` close-guard is
satisfied by this RETROSPECTIVE.md write per FEAT-2026-0015/T07.

## Lessons promoted

One durable lesson appended to `.specfuse/LEARNINGS.md` under
this gate's tag — see entry tagged `[FEAT-2026-0018/G1-CLOSE-INTERMEDIATE]`.
