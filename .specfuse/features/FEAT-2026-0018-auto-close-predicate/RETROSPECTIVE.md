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

## Gate 2 — driver wiring + force-full-close + auto_close_disabled override

Gate 2 wired the gate-1 module into `loop.py`. Three substantive WUs:
T04 (terminal-gate path — `maybe_auto_close_terminal`,
`write_stub_retrospective_terminal`, `mark_close_wu_auto_closed`),
T05 (intermediate-gate path option A —
`maybe_auto_close_intermediate`,
`append_stub_retrospective_intermediate`), and T06 (operator escapes
— `--force-full-close <feature-id>` CLI flag and `auto_close_disabled:
true` PLAN.md frontmatter override — `resolve_auto_close_override`).
All three landed in 2 attempts. No blocked_human escalations; no
replan events. Gate-2 budget was raised at arm time from $9.00 →
$16.00 anchored to the gate-1 actual ratio (2.14×) applied to a
gate-2 plan dominated by two `xhigh` driver-wiring WUs.

### T04 — Terminal-gate wiring

- Attempts: 2 (first 710 s, $2.39; second 781 s, $1.71).
- Blockers: first attempt did not satisfy the AC8 symbol-existence
  check (one of the three required `produces_driver_helper` symbols
  did not resolve, or its call-site lacked the named helper); the
  re-dispatch landed clean.
- Surprises: T04 ships 3 driver helpers
  (`maybe_auto_close_terminal`, `write_stub_retrospective_terminal`,
  `mark_close_wu_auto_closed`) plus the FEAT-2026-0017 invariant-guard
  interaction (stub-retro write must happen BEFORE
  `fire_terminal_flips`, after which `assert_terminal_flips_fired`
  must still pass). That ordering invariant was the highest-density
  acceptance criterion in the gate and added a meaningful slice of
  the cycle's spend.

### T05 — Intermediate-gate wiring (option A)

- Attempts: 2 (first 613 s, $1.68; second 428 s, $0.98).
- Blockers: first attempt's AC8 symbol check or test gate did not
  pass; re-dispatch landed clean. Attempt-2 cost was 58% of
  attempt-1 (closer to a true delta than T01's near-parity in
  gate 1) — the second wiring site had a leaner spec footprint
  on re-dispatch.
- Surprises: cheapest of the three. Re-using T04's predicate-call
  site + stub-frontmatter helper + event-emission pattern paid off
  exactly as the WU's "depends_on: T04" rationale predicted; the
  second wiring site is materially cheaper than the first when the
  shared scaffolding already exists.

### T06 — `--force-full-close` flag + `auto_close_disabled` override

- Attempts: 2 (first 488 s, $1.34; second 395 s, $0.95).
- Blockers: first attempt did not satisfy a verifier — most likely
  the AC8 symbol-existence check on `resolve_auto_close_override`,
  or the integration assertion that BOTH wiring sites (T04 and T05)
  honour the override. Re-dispatch landed clean.
- Surprises: 2.86× plan on a `medium` effort band — the largest
  ratio of gate 2. T06 was planned as a small CLI add ($0.80) but
  hooked into two pre-existing wiring sites, added a frontmatter
  field with PLAN.md-mutation semantics, and shipped tests for both
  override paths plus the precedence ordering (CLI flag vs
  frontmatter vs default). Multi-site touch + lint cleanliness on
  the override + tests is structurally a `high` effort, not
  `medium`. Same shape as T02 in gate 1 (effort band priced single-
  site work; AC implied multi-site shipping).

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
| T04 | $2.50 | $4.096069 | 1.638× | +63.8% | FAIL | pass |
| T05 | $2.20 | $2.653762 | 1.206× | +20.6% | pass | pass |
| T06 | $0.80 | $2.286465 | 2.858× | +185.8% | FAIL | FAIL |
| **gate 2 sub-total (substantive)** | **$5.50** | **$9.036296** | **1.643×** | **+64.3%** | — | — |

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

Original gate-2 budget was $9.00; raised to $16.00 at arm time
anchored to gate-1's actual ratio (2.14× of original $4.10 plan).
Substantive gate-2 spend $9.04 is 56.5% of the raised budget; the
$16.00 ceiling was correctly sized — gate 2 came in under the
adjusted budget despite T06's 2.86× WU-level miss. Predicate-v1
self-evaluation against gate-2 data (criterion 3 ≤ 1.5×, criterion
4 ≤ 2×, criterion 6 ≤ budget): T04 trips criterion 3; T06 trips
criteria 3 and 4; criterion 6 holds. Gate 2 would NOT auto-close
under its own predicate. Meta-confirmation: the predicate this
feature ships correctly identifies gate 2 as off-plan —
close-intermediate ceremony was warranted.

### Variance > 50% rationale — gate 1 (all three substantive WUs)

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

### Variance > 50% rationale — gate 2 (T04 and T06; T05 within band)

T05 came in 1.21× plan and needs no rationale. T04 and T06 both
miss, and the pattern is structural — not estimation noise on three
independent estimates, but two instances of one cause.

- **T04 (+63.8%).** Two attempts. Three driver helpers shipped
  (`maybe_auto_close_terminal`, `write_stub_retrospective_terminal`,
  `mark_close_wu_auto_closed`) plus the FEAT-2026-0017 ordering
  invariant — stub-retro write must happen BEFORE
  `fire_terminal_flips`, AND `assert_terminal_flips_fired` must
  still observe true terminal flips on the auto-close path. The
  `xhigh` effort band ($2.50) captures the wiring footprint, but
  not the invariant-interaction surface. The re-dispatch landed
  the AC-driven fix; attempt-2 cost ($1.71) was a meaningful
  fraction of attempt-1 ($2.39), confirming the gate-1 finding
  that re-dispatch is not "fix-delta" cost.
- **T06 (+185.8%).** Two attempts. Priced as `implementation/
  medium` ($0.80) — "small CLI add" shape. Actually shipped: CLI
  flag, frontmatter override, integration into BOTH wiring sites
  T04 and T05 introduced, precedence ordering between the two
  override paths, and tests for each. Same misclassification
  shape as gate 1's T02 (single-site pricing of multi-site work).
  T06 would have been priced correctly at `implementation/high`
  with an explicit per-wiring-site surcharge.

Shared cause across T04 and T06: the planner saw "one feature
WU" and priced one piece of wiring. Both WUs actually wired into
multiple sites (T04: stub-retro write + flips + auto_close
frontmatter on close WU; T06: override at both T04 and T05
sites). Effort bands do not see site count. T05 was on-band
precisely because its wiring re-used T04's scaffolding — a single
new site backed by an already-paid-for foundation.

## Notes on docs/roadmap

Gate 1 ships an internal module with no operator-facing surface:
no skill changes, no docs/methodology updates, no roadmap row
edits required. The `assert_doc_or_roadmap_diff` close-guard is
satisfied by this RETROSPECTIVE.md write per FEAT-2026-0015/T07.

Gate 2 wired the gate-1 module into `loop.py` and added two
operator-facing surfaces (`--force-full-close <feature-id>` and
the `auto_close_disabled: true` PLAN.md frontmatter override).
Operator-facing docs for these surfaces belong to gate 3's docs
WU (T10 in PLAN.md). For this WU, the `assert_doc_or_roadmap_diff`
close-guard is satisfied by this RETROSPECTIVE.md write per
FEAT-2026-0015/T07.

## Lessons promoted

One durable lesson per gate appended to `.specfuse/LEARNINGS.md`
under each gate's tag — see entries tagged
`[FEAT-2026-0018/G1-CLOSE-INTERMEDIATE]` and
`[FEAT-2026-0018/G2-CLOSE-INTERMEDIATE]`.
