# Follow-ups — FEAT-LOOP-2026-0251

### An early refusal records a different outcome from the late order for one input

**Criterion (verbatim).** "A surviving skip, or an early refusal whose outcome or failure
class differs from the late one for the same input: record `not_met` with a follow-up."

**Evidence.** A probe drove `loop.run()` with a unit declaring `src/rule.py`, an attempt
writing only `docs/notes.md`, a RESULT listing both under `files_changed`, and green gates.
With `fail_fast_deliverables: true` the first `attempt_outcome` is `produces_not_in_diff`
(class `produces_not_in_diff`, 0 verify calls). With `false` it is `files_changed_mismatch`
(class `files_changed_mismatch`, 1 verify call). The control with a plain RESULT gives
`produces_not_in_diff` both ways. `tests/test_files_changed_auto_repair.py`,
`test_untouched_deliverable_still_refuses`, had its expected outcome changed to match.

**What happened, in plain terms.** The attempt is refused both ways. Only the name of the
refusal, and so the retry advice, differs. `PLAN.md` says the feature does not change what
is refused, only when, and that `files_changed_mismatch` stays where it is. It does not say
which refusal wins when both apply. The close cannot settle that.

**Options.**

1. Accept the new precedence and state it in the definition of done and the docs. For: no
   code change; no gate run is paid; the retry note names the missing deliverable. Against:
   the RESULT's false `files_changed` claim is not reported on that attempt.
2. Skip the early refusal when the RESULT's `files_changed` would trip the mismatch guard.
   For: outcomes match the old order. Against: code and tests change, and those attempts pay
   for a full gate run again.

**Recommendation.** Option 1.

**Re-run condition.** Either `GATE-01.md` and the close unit state that a deliverable
refusal takes precedence over `files_changed_mismatch`, or case A records the same outcome
and failure class with the key `true` and `false`, asserted by a test.

### Clause 6 does not hold literally for two pre-existing tests

**Criterion (verbatim).** "**Nothing else changes.** Every existing test of the three
guards passes unchanged, apart from assertions on the order of `verify` and the guard, which
are updated and named in the close."

**Evidence.** A `diff` of `tests/` against a snapshot of public `main` shows two edits that
are not about order. `test_deterministic_refusal_repeat` moved a source-text anchor to
`if not deliv_ok:`, because the emit call moved into a shared helper.
`test_produces_shape` changed two filters from `directory` to
`assert_declared_deliverables`, because the new lint WARN contains "directory". All ten
changed modules pass (68 tests, exit 0). Neither edit removes an assertion.

**Options.**

1. Widen the clause to allow edits forced by a refactor or by new lint wording. For: matches
   what was built, with no code change. Against: the clause is relaxed after the fact.
2. Restore both tests unchanged. For: the clause holds as written. Against: the WARN must be
   reworded and the driver's emit call moved back to each call site, which duplicates code
   the gate's arming discipline says to share.

**Recommendation.** Option 1.

**Re-run condition.** `GATE-01.md` clause 6 covers these two kinds of edit, or both test
files match their pre-feature text and pass.
