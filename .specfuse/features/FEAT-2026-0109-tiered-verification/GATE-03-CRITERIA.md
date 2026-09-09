# Gate 3 — per-criterion close state

Per `close-discipline.md` §5. One entry per acceptance criterion of
`FEAT-2026-0109/G3-CLOSE`, recording the oracle that proved it, that oracle's
`kind` (`narrow` = knowable scope, may be carried forward; `broad` = no knowable
scope, re-runs every close attempt) and its `state`. Written by this close from
runs made in this session; nothing here is inferred by a reader, and nothing is
carried forward from a prior attempt — every entry below was re-run at
`attempt: 1` of the current arming.

### G3-CLOSE#1

- **criterion:** `RETROSPECTIVE.md` carries `## Gate 3` and a `## Measurements` table: for each bullet of `GATE-03.md`'s definition of done, the command run in this session and its exit status.
- **oracle:** `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` (structural: `close-a`, `close-c`, `close-e`) plus the seven-row table in `RETROSPECTIVE.md` § *Definition of done — one command per bullet*
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#2

- **criterion:** This gate's `feature_oracle` verdict recorded in `## Measurements` as a `### feature_oracle: PASS` / `FAIL` line (`close-discipline.md` §1; closing lint `close-n`).
- **oracle:** `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` → `close-n` satisfied; the underlying run is `python3 -m unittest tests.test_installed_copy_driver_e2e -q` → `OK`, exit 0
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#3

- **criterion:** `## Measurements` states gate 3's restart count against the predicted 1, the feature's total across all three gates, and whether this close session itself ran from a pinned build — with the evidence for the last.
- **oracle:** count of `driver_staleness_detected` with `halted: true` over `events.jsonl` (gate 3 → 1, feature → 8), and `ps -eo pid,ppid,etime,command` showing PID 1413 executing `.../specfuse-pins/18c1933ca3f437ad65e994ea6279e79cc69cc779/_run_pinned.py`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#4

- **criterion:** `## Measurements` restates, across all three gates, the counts gate 1 and gate 2 each deferred: `baseline_attribution` firings, attempts that genuinely narrowed, and broad runs that went red on narrow-passed work — each with what the number establishes and what it does not.
- **oracle:** event-type counts swept over all 71 `.specfuse/features/*/events.jsonl` (`baseline_attribution` → 1; `broad_run_result` → 7, of which 3 red), plus `resolve_narrow_test_selection` re-read from pin `4545ce57…` (narrowed attempts → 5)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#5

- **criterion:** `## Consumer-visible contract changes`: the reconciled enumeration across gates 1, 2 and 3, built from gate 1's and gate 2's staged lists rather than re-derived, with the matching `CHANGELOG.md` `Unreleased` entries carrying `FEAT-2026-0109`.
- **oracle:** `specfuse.loop.changelog.parse_changelog` over `CHANGELOG.md` → `Unreleased` carries `{'added': 12, 'changed': 6, 'fixed': 3}` traced to `FEAT-2026-0109` plus 2 `fixed` traced to `#3270` / `#3271` = 23, matching the 23-item enumeration; and `close-k` in `lint_plan.py --closing`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#6

- **criterion:** `## Cost analysis` reconciling `PLAN.md`'s `planned_cost_usd` and every WU's `planned_cost_usd` against `events.jsonl` across all three gates, naming the delta.
- **oracle:** sum of `attempt_outcome.cost_usd` over `events.jsonl` (22 attempts → $84.93671, plus $0.82575 judge) against the sum of `planned_cost_usd` across all 15 `WU-*.md` ($62.50) and `PLAN.md` ($26.00); corroborated by the plan lint's own `WARN: … delta 140%, threshold 10%`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#7

- **criterion:** `## What the loop did NOT verify`: criterion, reason, and where each actually gets checked.
- **oracle:** the section in `RETROSPECTIVE.md`, 9 entries, each naming criterion / reason / where-checked
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#8

- **criterion:** `## Lessons`: at most two entries.
- **oracle:** `grep -c "^[0-9]\. \*\*" ` over the `## Lessons` section of `RETROSPECTIVE.md` → 2
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#9

- **criterion:** Per-criterion state recorded per `close-discipline.md` §5 — each criterion's oracle, its `kind` (`narrow` / `broad`) and its `state`, written by this close and never inferred (closing lint `close-l`).
- **oracle:** this file, plus `python3 .specfuse/scripts/lint_plan.py <feature_dir> --closing` reporting no `close-l` finding and `python3 -m unittest tests.test_lint_closing_criteria -q` → `OK`, exit 0 over the whole real feature corpus
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#10

- **criterion:** Oracles re-run fresh, exit codes read directly in this session: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0; `specfuse lint` over every feature folder reports zero ERROR; the three gates' `feature_oracle` commands each report `OK`.
- **oracle:** `python3 -m unittest discover -s tests -q` → `Ran 3833 tests in 173.310s`, `OK (skipped=3)`, exit 0; `bash scripts/smoke-test.sh` → `smoke test: OK`, exit 0; `lint_plan.py` over all 77 feature folders → 0 ERROR, 0 non-zero exits; `tests.test_lazy_baseline_e2e` / `tests.test_tiered_verification_e2e` / `tests.test_installed_copy_driver_e2e` → `OK`, exit 0 each
- **kind:** `broad`
- **state:** `pass`
- **attempt:** `1`

### G3-CLOSE#11

- **criterion:** `specfuse lint --closing` passes before this unit reports `complete`.
- **oracle:** `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0109-tiered-verification --closing` → `CLOSING-READY`, exit 0
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
