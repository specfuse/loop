---
id: FEAT-2026-0048/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
oracle_env: macos_local
produces:
  - specfuse/loop/bug_lane.py
  - tests/test_bug_lane_guardrails.py
produces_driver_helper: evaluate_merge_guardrails
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T05:03:44.606906+00:00
duration_seconds: 642.74
cost_usd: 1.038923
input_tokens: 46
output_tokens: 12688
---

# The merge-eligibility predicate — pure, fail-closed, six hardcoded guardrails

**Objective.** Create `specfuse/loop/bug_lane.py` exposing
`evaluate_merge_guardrails(...) -> MergeDecision`: a pure predicate that answers
"may this PR auto-merge" and answers **no** on any doubt.

**Context.** Correlation ID `FEAT-2026-0048/T02`. Depends on
`FEAT-2026-0048/T01`, which verified the policy schema and added
`bug_lane_limits()`.

This is the only genuinely new mechanism in this feature; everything else is
wiring between shipped ones.

**Copy the shape of `specfuse/monitor/autofix.py`.** Read it before writing. It
is the working precedent: module-level reason constants, a frozen decision
dataclass, an injected state-reader `Protocol` so the predicate performs no I/O,
and — the sentence that matters most — its docstring promise, *"Any failure to
evaluate an input returns DECLINE."* **Do not import from it**; the two
predicates answer different questions over different inputs.

**Fail closed. This is the whole design.** A guardrail that raises on malformed
input is a guardrail that malformed input walks straight through. Every
unreadable, missing, wrong-typed, or ambiguous input yields "do not merge" with
a reason — never an exception, never a default-permit.

**The six guardrails**, all required, all `and`-ed. The roadmap row names them
and this WU implements exactly them, adding none:

1. **Test-first evidence** — the PR's changed-file list includes at least one
   path under `tests/`. Structural only: this does **not** judge whether the
   test is a good test. A semantic judgment would be a model-authored
   *approval*, and FEAT-2026-0053's organizing principle binds — *model-authored
   signals may only veto; only mechanical facts and human-authored constants may
   approve.*
2. **CI green** — the passed-in CI conclusion is exactly `"success"`. Any other
   value, including `"pending"`, `None`, and the empty string, declines.
3. **Diff size cap** — total changed lines ≤ `max_diff_lines` from
   `bug_lane_limits()`.
4. **No never-touch paths** — no changed path is under any entry of
   `arm_eval.JUDGE_PATHS`. **Import that tuple; do not retype it.** It is this
   repo's ratified "a human must look at this" set (FEAT-2026-0053), and a
   second hand-written copy would drift invisibly. Match on path prefix, and
   treat the bare-filename entry (`pyproject.toml`) as a whole-file match, the
   same approximation `arm_eval` documents.
5. **Traced to a triaged issue or diagnosed finding** — the passed-in
   provenance is a non-empty issue reference of one of the two accepted kinds.
   An untraceable PR never auto-merges.
6. **Daily cap** — the injected state reader reports the rolling-24h merge count
   below `max_merges_per_day`. T03 owns the storage; this WU owns only the
   `Protocol` and the call.

**Every declined guardrail returns its own reason constant**, so the label T04
applies names the actual cause rather than a generic refusal.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
module does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_bug_lane_guardrails.py::TestEvaluateMergeGuardrails::test_all_guardrails_pass_is_eligible`
   exists and **fails on HEAD before this WU runs**.
2. `specfuse/loop/bug_lane.py` defines a frozen `MergeDecision` dataclass with
   at least `eligible: bool` and `reason: str`.
3. Module-level reason constants exist, one per guardrail plus one for
   unreadable input, following `autofix.py`'s `REASON_*` naming — including
   `REASON_ELIGIBLE` for the pass case.
4. `evaluate_merge_guardrails` is **pure**: it opens no file, spawns no process,
   and makes no network call. A test asserts this by calling it with only
   in-memory arguments and a fake state reader.
5. A `Protocol` for the merge-cap state reader is defined in this module,
   mirroring `autofix.RateLimitStateReader`. T03 implements it.
6. Each of the six guardrails has a test proving it **alone** declines, with the
   other five satisfied, and that the returned `reason` is that guardrail's own
   constant.
7. A test proves all six satisfied returns `eligible=True` with
   `REASON_ELIGIBLE`.
8. **Fail-closed tests:** `None`, a wrong-typed value, and a missing key for
   *each* input each return `eligible=False` rather than raising. A test asserts
   `evaluate_merge_guardrails` never propagates an exception for any malformed
   input in the covered set.
9. `JUDGE_PATHS` is **imported** from `specfuse.loop.arm_eval`, not redefined. A
   test asserts the imported object is the same tuple — `bug_lane.JUDGE_PATHS is
   arm_eval.JUDGE_PATHS` — so a future edit to `arm_eval` cannot leave this
   predicate behind.
10. A test asserts a changed path under each entry of `JUDGE_PATHS` declines,
    iterating the tuple rather than hardcoding its members, so the test cannot
    go stale when the tuple grows.
11. A test asserts CI conclusions `"pending"`, `"failure"`, `""`, and `None`
    each decline, and only `"success"` passes that guardrail.
12. `python3 -m unittest tests.test_bug_lane_guardrails -v` exits zero after
    this WU's edits.
13. `python3 -c "from specfuse.loop.bug_lane import evaluate_merge_guardrails, MergeDecision"`
    exits zero.

**Do not touch.** `specfuse/loop/arm_eval.py` — import `JUDGE_PATHS`, never
edit it; if the tuple seems wrong for this use, report it rather than changing a
set FEAT-2026-0053 ratified. `specfuse/monitor/autofix.py` — read for shape, do
not edit or import. Anything that performs a merge — T04 owns execution and this
WU must remain incapable of it. `.specfuse/roadmap.md`. Generated directories,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped red/green run in criteria 1 and 12 and the symbol check in 13.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`arm_eval.JUDGE_PATHS` does not exist or is not a module-level tuple of path
prefixes (the plan's §1 search says it is at `specfuse/loop/arm_eval.py:54` —
if that has changed, report it); or a guardrail cannot be evaluated
mechanically and would require a judgment call about code quality, which is
explicitly out of this predicate's remit. If `specfuse/loop/bug_lane.py` is
absent from the files you edited, emit `status: blocked` — do not claim
complete.
