---
id: FEAT-2026-0103/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - specfuse/loop/data/verification.yml.example
  - docs/methodology.md
  - tests/test_retain_on_guard_refusal_docs.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.18.0
started_at: 2026-09-10T02:26:25.037380+00:00
duration_seconds: 96.677
cost_usd: 0.591725
input_tokens: 44
output_tokens: 8862
---

# The retain-and-repair contract is documented where operators read

**Objective.** An operator adopting the next release can find, in the shipped
example and the methodology, what happens after a guard refusal, how to turn
it off, and how it interacts with spinning detection.

**Context.** FEAT-2026-0103/T04, after T02 and T03. `specfuse/loop/data/verification.yml.example`
documents every `verification.yml` key with a commented block; add
`defaults: retain_on_guard_refusal` beside `max_attempts` with the four sites
and the default. `docs/methodology.md` § "Per-attempt outcome events" is the one
home for outcome semantics (`tests/test_attempt_outcome_contract.py` reads it):
state that `files_changed_mismatch`, `produces_not_in_diff` and the two
`guard_refusal` outcomes now retain the tree (`tree_retained: true` in `extras`)
and that a `passed` outcome may carry `auto_repaired_files_changed`. State the
spinning interplay in one paragraph: `detect_deterministic_refusal_repeat`
escalates on an identical summary with an identical touched set (#1415), and a
retained tree that the repair attempt leaves untouched produces exactly that, so
a session that ignores the brief still escalates after two refusals rather than
running to the attempt ceiling. §12 red-test exemption: pure documentation; the
test below is a consistency check, not a behaviour test.

**Acceptance criteria.**

1. `tests/test_retain_on_guard_refusal_docs.py` asserts the example file
   contains `retain_on_guard_refusal` under a `defaults:` block with a comment
   naming all four outcomes, and that `docs/methodology.md`'s per-attempt
   outcome section mentions `tree_retained` and `auto_repaired_files_changed`;
   it fails on HEAD and passes after.
2. `python3 -m unittest tests.test_attempt_outcome_contract -v` exits 0 after
   the edit (the section's shape is unchanged; only prose is added).
3. `grep -n "retain_on_guard_refusal" specfuse/loop/data/verification.yml.example docs/methodology.md` returns at least one hit in each.

**Do not touch.** The driver source under `specfuse/loop/` (this unit is
prose only); `.specfuse/rules/`;
`.specfuse/verification.yml`; `CHANGELOG.md` (the close collects the entry).

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Stop with `status: blocked` if the methodology's
per-attempt section cannot take the added prose without breaking
`tests/test_attempt_outcome_contract.py`'s extractor (name the assertion).
