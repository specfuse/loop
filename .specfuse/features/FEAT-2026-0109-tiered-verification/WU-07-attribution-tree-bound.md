---
id: FEAT-2026-0109/T07
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.50
oracle_env: macos_local
produces:
  - .specfuse/features/FEAT-2026-0109-tiered-verification/GATE-01.md
  - .specfuse/features/FEAT-2026-0109-tiered-verification/PLAN.md
  - specfuse/loop/loop.py
  - tests/test_lazy_baseline_e2e.py
model: sonnet
effort: medium
gate_set: code
---

# Say the bound the mechanism actually holds, and test the case that has none

**Objective.** Correct "attribution runs at most once per gate" to the bound
`gate_baseline_check`'s dedup really holds — **at most once per tree state per
gate** — everywhere it is claimed, and add the test for the differing-tree case
that exists nowhere today.

**Context.** FEAT-2026-0109/T07; read `PLAN.md`, `GATE-01.md`, and
`RETROSPECTIVE.md` § "What the loop did NOT verify" item 4, which raised this
gap and deferred the decision to gate 2's `plan-next`. That decision has been
made and is recorded in `GATE-02-REVIEW.md` § "The differing-sha gap": **the
wording moves, not the mechanism.** Do not re-open it — implement it.

The gap, precisely. `GATE-01.md`'s definition of done claims "Attribution runs
at most once per gate. A second failing unit does not re-probe if the gate
already has a fresh attribution record for this tree." The implementation is
`attribute_failure_to_baseline` delegating to `gate_baseline_check`
(`loop.py:4681`), whose dedup compares the recorded `baseline.tree` against
`_current_tree_hash()`, falling back to `baseline.sha == head_sha` for a legacy
record with no `tree`. So the real guarantee is one probe **per tree state**.
Two units failing at different shas, separated by a landed unit that changed
tracked content under `specfuse/` or `tests/`, legitimately re-probe.
`AttributionDedup.test_attribution_runs_at_most_once_per_gate` covers the
same-tree case only.

This matters now because gate 2's per-attempt narrowing makes multi-unit
failure within one gate more likely — the exact condition under which the two
readings diverge.

**Why the wording moves and not the mechanism**, so the reasoning survives with
the change: a baseline record is a measurement *of a tree*. Reusing it across a
landed change would answer "did this failure pre-exist?" against a tree that no
longer exists, which is the mis-attribution T01 exists to prevent. Holding the
stronger bound would need new per-gate state outside `gate_baseline_check` and
would make attribution wrong in exactly the case gate 2 makes more common. The
full argument is in `GATE-02-REVIEW.md`.

**The three surfaces carrying the overclaim.** All three say the same wrong
thing and all three move together:

1. `GATE-01.md`'s third definition-of-done bullet.
2. `attribute_failure_to_baseline`'s docstring (`loop.py:4720`), "which is what
   bounds attribution to at most once per gate".
3. `PLAN.md` § Notes, "Bounded to one dispatch per gate because the retroactive
   probe fires on the first failure" — the same defect stated about dispatches.

Correct the claim in each and, in `GATE-01.md`, leave a one-line note naming
this unit as the correction, so the gate reads as amended rather than as
retrospectively rewritten. **`GATE-01.md`'s `baseline:` frontmatter block is
not yours** — the prose bullet is the only thing that changes there. Gate 1's
`RETROSPECTIVE.md` already states the bound correctly and must not be touched.

**The test constraint that will otherwise be discovered by failing.**
`_current_tree_hash()` (`loop.py:4527`) shells out to `git ls-tree HEAD` in the
process's working directory and drops the `.specfuse` entry, so the existing
`AttributionDedup` test — which uses a bare `TemporaryDirectory` for the gate
file — is really reading *this repo's* tree, identical across both calls. To
vary the tree you need a real temporary git repository with two commits that
change tracked content outside `.specfuse/`, entered for the duration of the
test. Build one; monkeypatching `_current_tree_hash` to return two different
strings tests the mock, not the bound, and would be a hollow pass on the one
case this unit exists to cover.

**Acceptance criteria.**

- `tests/test_lazy_baseline_e2e.py::AttributionDedup::test_attribution_reprobes_when_the_tree_moved` fails on HEAD and passes after: in a real temporary git repository, two calls to `attribute_failure_to_baseline` at **different** head shas with a tracked-content commit between them run `probe_baseline` **twice**, both return `freshly_probed=True`, and the persisted record's `source` names the **second** unit. This is the case that has no test today.
- `::test_attribution_dedups_across_a_bookkeeping_commit`: two calls at different head shas whose commit touched only `.specfuse/` run `probe_baseline` **once** — different sha, same tree, still deduped. This is the boundary that makes the first test a real distinction rather than "any second call re-probes".
- The existing `::test_attribution_runs_at_most_once_per_gate` still passes unchanged, or is renamed to name the tree bound with its assertions untouched.
- `grep -n "at most once per gate" .specfuse/features/FEAT-2026-0109-tiered-verification/GATE-01.md specfuse/loop/loop.py .specfuse/features/FEAT-2026-0109-tiered-verification/PLAN.md` returns no match; the replacement wording names the tree state in each of the three places.
- `GATE-01.md` carries a one-line note attributing the correction to `FEAT-2026-0109/T07`, and a diff of `GATE-01.md` shows no change to its `baseline:` block or its `feature_oracle`.
- `python3 -m unittest tests.test_lazy_baseline_e2e -q` reports `OK` — gate 1's own `feature_oracle` still green.
- `python3 -m unittest discover -s tests -q` reports `OK`.
- `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0109-tiered-verification` exits 0.

**Do not touch.** The dedup logic in `gate_baseline_check`, `probe_baseline`,
`write_gate_baseline` or `attribute_failure_to_baseline` — this unit changes
words and adds tests, and a behavioural edit here is the escalation below, not
the fix; `GATE-01.md`'s `baseline:` block and `feature_oracle`; gate 1's WU
files and `RETROSPECTIVE.md`; `PLAN.md`'s task graph and frontmatter (the
§ Notes sentence is the only edit there); T04/T05/T06's surfaces;
`.specfuse/rules/`, `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if making the differing-tree
case testable requires changing `_current_tree_hash`, `gate_baseline_check` or
the record shape — the decision recorded in `GATE-02-REVIEW.md` was explicitly
that the mechanism does **not** move, so a behavioural change here contradicts
it and is an operator's call. Also block if a real temporary git repository
cannot be constructed in this suite's harness, rather than falling back to
monkeypatching the tree hash.
