---
id: FEAT-2026-0076/T01H
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - specfuse/loop/policy_proposals.py
  - tests/test_policy_proposals.py
provenance: "Operator review between T01 and T02 found propose_policy_defaults silently withholding budget proposals for any relative repo_root; T02 is about to describe this algorithm in prose."
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T14:49:53.628261+00:00
duration_seconds: 761.32
cost_usd: 0.770011
input_tokens: 3572
output_tokens: 7853
---

# Withheld-for-no-evidence must mean no evidence, not an unresolved path

**Objective.** Make `propose_policy_defaults` behave identically for a relative
and an absolute `repo_root`, and make the token-conversion assumption visible in
the evidence string that carries it.

**Context.** Correlation ID `FEAT-2026-0076/T01H`. Hygiene unit inserted between
T01 and T02 at operator review. T02 must not describe an algorithm that
under-proposes.

**The defect, reproduced:**

```
propose_policy_defaults(".")          -> ['test_paths']
propose_policy_defaults("/abs/path")  -> ['max_items_per_day', 'max_tokens_per_run', 'test_paths']
```

T01 scopes `events_stats.collect` — which globs a workspace of *sibling
repositories* — down to this repo alone by building a temp directory holding one
symlink. That instinct is right and must be preserved: pointing `collect` at
`repo_root.parent` would read repositories this process has no business touching.
But `repo_root` is not resolved before `link.symlink_to(repo_root)`, so a
relative path produces a symlink whose target is relative to the scratch
directory and therefore dangles. `collect` reports zero work units and both
budget proposals are withheld.

**Why this is worse than an ordinary bug, and the reason it is worth a work unit
of its own.** This feature's design says a *withheld* proposal means "no evidence
exists — here is the shipped default, and it is a default." That statement is now
indistinguishable from "the code could not see the evidence." An operator running
the interview from the repository root is told there is no history to derive
budgets from, on a repository carrying **281 work units** of it, and accepts an
agent-chosen number. That is the precise outcome FEAT-2026-0076 exists to
prevent, produced by the feature itself.

It passed all twelve of T01's acceptance criteria because every fixture uses an
absolute temporary directory. Green tests, wrong on the real repository — the
`[FEAT-2026-0069/G2-CLOSE]` pattern reproducing inside the feature written to
respect it.

**Second, narrower obligation.** `events_stats.collect` aggregates `cost_usd`,
not raw token counts, so T01 introduced `_ASSUMED_TOKENS_PER_USD = 200_000` to
convert spend into a token budget. The constant is disclosed in a source comment,
which is not where the operator reads. This feature's contract is that **a
proposal carries the evidence it came from**; a proposal resting on an
undisclosed conversion violates that contract regardless of whether the number is
well chosen. Make the assumption appear in the `evidence` string. Do **not**
re-litigate the value of the constant — that is a judgment for the operator at
interview time, and changing it is out of scope here.

**Incremental edit to files T01 already delivered.** Both `produces` paths were
created by T01 and are declared here because this WU *modifies* them and the
in-diff gate should require that it does. Precisely:

- `specfuse/loop/policy_proposals.py` — resolve `repo_root` before building the
  scratch symlink, and extend the `max_tokens_per_run` evidence string to name
  the cost-to-token conversion assumption. No new function, no new proposed
  value, no change to `_ASSUMED_TOKENS_PER_USD`'s value.
- `tests/test_policy_proposals.py` — add the `TestRelativeRepoRoot` cases and the
  evidence-disclosure assertion. **No existing assertion is modified or
  weakened** (criterion 8).

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
relative-path case currently withholds proposals.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_policy_proposals.py::TestRelativeRepoRoot::test_relative_and_absolute_agree`
   exists and **fails on HEAD before this WU runs**.
2. `propose_policy_defaults` resolves `repo_root` before using it to build the
   scratch symlink, so a relative path, an absolute path, and a path containing
   `..` all produce the same proposals for the same repository. A test asserts
   all three agree.
3. **The sibling-repository scoping is preserved.** A test asserts that
   `events_stats.collect` is never handed `repo_root.parent` or any directory
   containing repositories other than this one — the symlink indirection stays,
   and this WU fixes only how its target is computed.
4. A test asserts that on a repository **with** events history, budget proposals
   are present when called with a relative path — the exact case that silently
   failed. Fixtures must exercise a relative path, not only absolute tempdirs,
   or this defect class returns.
5. **A withheld proposal means no evidence.** A test asserts that when
   `_collect_local_events` returns no usable data the reason is genuinely absent
   history — construct a repository with events and one without, and assert the
   withholding tracks the data rather than the path shape.
6. The `evidence` string for `max_tokens_per_run` names the cost-to-token
   conversion assumption and its value, so the operator can disagree with it at
   interview time. A test asserts the assumption appears in the evidence, not
   only in a source comment.
7. `_ASSUMED_TOKENS_PER_USD`'s value is **unchanged** by this WU — the
   disclosure is the fix here, not the number. A test asserts the constant still
   reads `200_000`, so a later change is a deliberate act with its own reason.
8. All of T01's existing tests pass **unmodified** — a test file may gain cases
   but no existing assertion is weakened. This is the proof the fix did not trade
   one behaviour for another.
9. `python3 -m unittest tests.test_policy_proposals -v` exits zero after this
   WU's edits.

**Do not touch.** `specfuse/loop/events_stats.py` — the scoping problem is
this module's to solve, not that one's; widening `collect` would change a
mechanism other callers depend on. `specfuse/loop/agent_policy.py`. The value of
`_ASSUMED_TOKENS_PER_USD` (criterion 7). The set of values in scope — this WU
fixes how existing proposals are computed and disclosed, and adds none.
`.specfuse/agent-policy.yml`. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped red/green run in criteria 1 and 9.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
resolving the path is not sufficient and the symlink indirection turns out to be
unworkable on this platform (report what fails — do **not** fall back to handing
`collect` a directory containing sibling repositories, which is the privacy
boundary T01 was right to draw); or if making the conversion assumption visible
would require a schema change, which `PLAN.md`'s scope boundary puts out. If
`tests/test_policy_proposals.py` does not gain a relative-path case, emit
`status: blocked` — do not claim complete.
