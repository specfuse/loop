---
id: FEAT-2026-0016/T07
type: implementation
effort: medium
status: draft
attempts: 0
planned_cost_usd: 1.00
generated_surfaces: []
produces_driver_helper:
  - summarize_attempt_failure_classes
  - assert_failure_class_breakdown_when_failures_present
---

# Close-ceremony `## Cost analysis` — `### Failure-class breakdown` subsection

**Objective.** Extend the closing-deliverable contract so every
`RETROSPECTIVE.md`'s `## Cost analysis` section carries a
`### Failure-class breakdown` subsection sourced from
`events.jsonl`'s `attempt_outcome` events (T01-emitted): count of
non-passing attempts grouped by `failure_class`, dominant
`failure_signature` per class. Adds a driver helper that the
close agent invokes to render the breakdown, plus a new
close-guard assertion that fails the close WU when failures
exist in the gate's events but the subsection is missing.

**Context.** This is `FEAT-2026-0016/T07`. Consumer #4 of the
attempt_outcome data layer (after T04 spinning-detector hook, T05
`/gate-status` per-attempt surface, T06 `/unblock-wu` rationale).
Closes the gap between the structured per-attempt signal T01
writes and the human-readable retrospective the close agent
produces today.

Today's contract (PLAN.md `roadmap_goal` § "Closing-WU spec
change", documented in roadmap.md lines 207–221): close ceremony
authors a `## Cost analysis` section quoting per-WU planned vs
actual + delta %. The breakdown of WHY a WU's spend went over
plan ("two attempts on the same signature", "three different
failure classes") is not required and is therefore inconsistent
across feature retrospectives — observed in
`FEAT-2026-0018/RETROSPECTIVE.md` (gate-1 + gate-2 cost analyses
narrate cache-reload + token-output amplification but do not
enumerate which `failure_class` repeated). T01's
`attempt_outcome` events now make the enumeration cheap.

Cross-reference contracts shipped by gate 1:

- T01 — `attempt_outcome` payload carries `failure_class`,
  `failure_signature`, `outcome`, `attempt`, `cost_usd`,
  `duration_seconds` per attempt. PLAN.md "Event payload shape —
  `attempt_outcome` v1" is authoritative.
- FEAT-2026-0015/T07 — `assert_cost_analysis_section` /
  `assert_cost_analysis_section_when_met` close-guards live at
  `loop.py` lines ~1872+ and are wired into `CLOSE_GUARDS` (line
  ~1990). T07 adds a sibling guard alongside.

Reference binding rules: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`. Driver owns all git.

**§10 helper-duplication pre-flight.** Before authoring:

```bash
# Existing close-guard family and CLOSE_GUARDS registration
grep -nE '^def assert_cost_analysis|^def assert_retrospective|^def assert_terminal_flips' .specfuse/scripts/loop.py
grep -nE 'CLOSE_GUARDS|close_guards' .specfuse/scripts/loop.py

# Existing event-readers (do NOT duplicate)
grep -nE '^def .*(events|read_events|load_events|attempt_outcome)' .specfuse/scripts/loop.py | head -20

# Existing failure_class taxonomy (lock at v1)
grep -nE 'failure_class.*=|_GATE_CLASS_MAP' .specfuse/scripts/loop.py | head -10

# Confirm the close-guard ordering site so the new guard slots in correctly
grep -n 'assert_cost_analysis_section_when_met' .specfuse/scripts/loop.py
```

If a reader of events.jsonl already exists (per `read_events`
helper or similar), reuse it instead of authoring a second one.

**Acceptance criteria.**

1. **New helper — `summarize_attempt_failure_classes`.** Add
   `summarize_attempt_failure_classes(feature_dir: Path,
   gate_n: int | None = None) -> str` to `loop.py`. Reads
   `events.jsonl` in `feature_dir`. Filters to
   `event_type == "attempt_outcome"` records whose
   `payload.outcome != "passed"`. When `gate_n` is provided,
   further filters to events whose `correlation_id`'s WU belongs
   to gate `gate_n` (cross-reference PLAN.md's
   `gates[].work_units[].id`); when `None`, includes all gates.
   Returns a markdown block:

   ```text
   ### Failure-class breakdown

   | failure_class | non-passed attempts | dominant signature |
   |---------------|---------------------|--------------------|
   | tests | 3 | test_foo_bar |
   | lint | 1 | E501 line too long |
   | other | 1 | no_gate_marker |
   | **total** | **5** | — |
   ```

   "Dominant signature" = the `failure_signature` appearing most
   frequently within that class (ties broken by first-seen
   event-file order). When no non-passing attempts exist for the
   filter, returns the literal string
   `"### Failure-class breakdown\n\n(no non-passing attempts in scope)\n"`.
   Pure function — no side effects beyond reading the events
   file.

2. **New close-guard —
   `assert_failure_class_breakdown_when_failures_present`.** Add
   `assert_failure_class_breakdown_when_failures_present(wu,
   feature_dir, repo_root, head_before) -> tuple[bool, str]`
   to `loop.py`, alongside `assert_cost_analysis_section_when_met`.
   Behavior:
   - Read `RETROSPECTIVE.md`. If absent, return
     `(True, "")` (sibling guard `assert_retrospective_exists`
     catches that).
   - Determine the gate number from `wu.wu_id` (reuse
     `_gate_number_from_wu_id`).
   - Call `summarize_attempt_failure_classes(feature_dir,
     gate_n)`. If the helper reports zero non-passing attempts
     (the "(no non-passing attempts in scope)" sentinel), return
     `(True, "")` — nothing to summarize.
   - Otherwise, the retrospective must contain a literal
     `### Failure-class breakdown` heading anywhere in the file.
     Match with `re.search(r"^#{3} Failure-class breakdown\b",
     retro.read_text(), re.MULTILINE)`. On match: `(True, "")`.
     On miss: `(False,
     "assert_failure_class_breakdown_when_failures_present:
     <N> non-passing attempt(s) in gate <gate_n> but
     '### Failure-class breakdown' subsection absent from
     RETROSPECTIVE.md")` quoting the count.

3. **Wire into `CLOSE_GUARDS` immediately after
   `assert_cost_analysis_section_when_met`.** Insertion site is
   the same list (around `loop.py` line ~1990 today). Ordering
   matters: the new guard runs after the existing cost-analysis
   guards so its error message doesn't shadow the more
   foundational missing-section error. Verify with the AC8 grep
   check below.

4. **Close-guard applies to `close` AND `close-intermediate`
   types.** The guard family already runs on both close shapes
   (per FEAT-2026-0015/T07 contract). T07's new guard inherits
   that dispatch path — no separate wiring needed. Confirm the
   close-guard runner does not skip the new guard on either
   shape; if its dispatch list is per-type rather than shared,
   add the new guard to both lists.

5. **Legacy-event tolerance.** Features whose events.jsonl
   predate T01 (FEAT-2026-0015 and earlier) lack
   `attempt_outcome` records. The helper returns the
   "(no non-passing attempts in scope)" sentinel for such
   gates; the guard returns `(True, "")`. The breakdown
   subsection is REQUIRED only when attempt_outcome data with
   non-passing outcomes actually exists in the gate's scope. No
   backfill, no synthesis from `prior_attempts` notes — the
   feature explicitly defers backfill (PLAN.md "Scope OUT").

6. **Helper renders sorted output deterministically.** Rows in
   the rendered table are sorted by `non-passed attempts`
   descending, then by `failure_class` ascending for ties.
   Deterministic output makes the guard idempotent across
   regenerations and lets reviewers diff retrospectives without
   churn.

7. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. Helper present, single definition
   test "$(grep -cE '^def summarize_attempt_failure_classes\b' .specfuse/scripts/loop.py)" = "1"

   # b. Helper importable
   (cd .specfuse/scripts && python3 -c "from loop import summarize_attempt_failure_classes")

   # c. Guard present, single definition
   test "$(grep -cE '^def assert_failure_class_breakdown_when_failures_present\b' .specfuse/scripts/loop.py)" = "1"

   # d. Guard importable
   (cd .specfuse/scripts && python3 -c "from loop import assert_failure_class_breakdown_when_failures_present")

   # e. Guard wired into CLOSE_GUARDS after the cost-analysis-when-met guard
   python3 -c '
   import re, pathlib
   src = pathlib.Path(".specfuse/scripts/loop.py").read_text()
   block = re.search(r"CLOSE_GUARDS\s*=\s*\[(.*?)\]", src, re.DOTALL).group(1)
   names = re.findall(r"assert_\w+", block)
   assert "assert_cost_analysis_section_when_met" in names, "anchor missing"
   assert "assert_failure_class_breakdown_when_failures_present" in names, "new guard not wired"
   i = names.index("assert_cost_analysis_section_when_met")
   j = names.index("assert_failure_class_breakdown_when_failures_present")
   assert j > i, f"new guard at {j} must follow anchor at {i}"
   '

   # f. Working-tree diff touches loop.py
   { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | grep -qx '.specfuse/scripts/loop.py'
   ```

   Any check failing → `status: blocked` naming the failure.

**Do not touch.** Files this WU may edit:
- `.specfuse/scripts/loop.py` (two new top-level functions +
  one insertion into `CLOSE_GUARDS`)
- `tests/test_attempt_outcome_emission.py` (extend with the
  unit tests named under Verification)

No edits to: `gate_eval.py` (predicate v1 stays frozen; v2 is
explicitly out of scope per PLAN.md), `lint_plan.py`,
`validate-event.py`, T01's `emit_attempt_outcome` /
`parse_gate_failure_signature` surfaces, the
`assert_cost_analysis_section` / `assert_cost_analysis_section_when_met`
guards (reuse adjacency only), `RETROSPECTIVE.md` for any
feature (T08/T09/G3-CLOSE own their own writes here), skills,
secrets, `.git/`. Driver owns all git; edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in
`.specfuse/verification.yml` (tests, coverage ≥ 90%, zero
warnings, lint, security scan) + AC7 symbol-existence + import
checks. Add at least these unit tests to
`tests/test_attempt_outcome_emission.py`:

- `test_summarize_failure_classes_empty_when_all_passed` — fixture
  events.jsonl with only `outcome: passed` records; helper
  returns the "(no non-passing attempts in scope)" sentinel.
- `test_summarize_failure_classes_groups_by_class` — fixture with
  three `tests` failures (two signatures, one repeated) + one
  `lint` failure; helper output's table rows in deterministic
  order with the correct dominant-signature column.
- `test_summarize_failure_classes_filters_by_gate` — fixture
  with attempts under two different gates' WUs; helper called
  with `gate_n=2` excludes gate-1 attempts.
- `test_guard_passes_when_no_failures` — feature dir with only
  passing attempts; guard returns `(True, "")` even with no
  breakdown heading in RETROSPECTIVE.md.
- `test_guard_fails_when_failures_present_but_heading_absent` —
  feature dir with one non-passing attempt + RETROSPECTIVE.md
  lacking the heading; guard returns `(False, <error naming
  count>)`.
- `test_guard_passes_when_failures_present_and_heading_present` —
  same fixture but RETROSPECTIVE.md contains
  `### Failure-class breakdown`; guard returns `(True, "")`.

**Escalation triggers.**

1. **Completeness.** AC7 (a)/(c) returning anything other than
   `1`, or AC7 (b)/(d) raising `ImportError` → `status:
   blocked`. Helper or guard missing. Per
   `[FEAT-2026-0007/G1-LESSONS]`, frontmatter-flip-only is the
   documented hollow-pass shape — refuse it explicitly.
2. **Failure-class taxonomy drift.** If the §10 pre-flight
   surfaces a `failure_class` value emitted by T01 that is NOT in
   the v1 set (`tests | lint | security | coverage |
   symbol_existence | bandit | other | null`), name the drift
   and emit `status: blocked`. The taxonomy is locked at v1 in
   PLAN.md.
3. **Close-guard dispatch ambiguity.** If `CLOSE_GUARDS` is not
   the single registration site (e.g. close-intermediate and
   close types each maintain their own list), AC4's check that
   the new guard runs on both shapes is at risk. Document the
   topology and emit `status: blocked` rather than silently
   wiring into one shape only.
4. **Events.jsonl reader collision.** If the §10 pre-flight
   surfaces an existing event-reader helper with a different
   filter shape than this WU's helper needs (e.g. one that
   raises on malformed lines vs. one that skips them), reuse
   carefully and document the choice in the helper docstring;
   do not duplicate the reader.
