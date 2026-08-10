---
id: FEAT-2026-0076/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
oracle_env: macos_local
produces:
  - specfuse/loop/policy_review.py
  - tests/test_policy_review.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T16:09:36.452012+00:00
duration_seconds: 370.744
cost_usd: 1.001152
input_tokens: 846
output_tokens: 14847
---

# Read an existing policy file and classify each value against the shipped baseline

**Objective.** Ship `review_agent_policy` — a reference implementation that reads
an **existing** `.specfuse/agent-policy.yml` and returns, per in-scope key, the
current value, the evidence-backed proposal, the shipped baseline, and a
provenance classification that is explicitly a *hint*, never a claim.

**Context.** Correlation ID `FEAT-2026-0076/T04`. First substantive work unit of
gate 2. Depends on nothing inside gate 2; it composes
`specfuse/loop/policy_proposals.py`'s `propose_policy_defaults`, which gate 1
shipped (`FEAT-2026-0076/T01`, `T01H`).

Gate 1 bootstrapped a policy file from nothing. Gate 2 reviews one that already
exists — which needs an answer to the question `PLAN.md` § *Open question for
gate 2* deliberately left open, and which `GATE-02-REVIEW.md` answers with the
derivability count as its reason. **Read `GATE-02-REVIEW.md` § *The provenance
question* before starting.** Its decision is this WU's specification, and the
short form is:

> Provenance is computed by comparing the file's current value against the
> **shipped baseline** — `agent_policy.DEFAULT_*` where a constant exists, and
> `.specfuse/agent-policy.yml.example`'s literal value where one does not. No
> schema change. The comparison is **lossy in one direction** (an operator who
> deliberately chose a value equal to the baseline is indistinguishable from one
> who never chose), and this WU's job includes making that lossiness visible in
> the returned data rather than letting a downstream reader mistake the hint for
> a fact.

**Why the baseline is not just the `DEFAULT_*` constants.** Gate 1's
retrospective established that `agent_policy.py` defines exactly three constants
— `DEFAULT_MAX_DIFF_LINES`, `DEFAULT_MAX_MERGES_PER_DAY`, `DEFAULT_TEST_PATHS` —
and that **none of the three `budgets` keys has one**; they are required fields
whose only shipped value is the literal text of
`.specfuse/agent-policy.yml.example`. A comparison built on the constants alone
would silently cover one of the four in-scope keys and quietly say nothing about
the other three. The baseline is therefore the union of both sources, and which
source answered a given key must be recorded per key.

**The four in-scope keys**, unchanged from gate 1: `budgets.max_tokens_per_run`,
`budgets.max_items_per_day`, `budgets.max_open_prs`, `rules.bugs.test_paths`.

**Absence needs a two-sided test** —
`[FEAT-2026-0076/G1-CLOSE-INTERMEDIATE/absence-needs-a-two-sided-test]`, this
feature's own lesson, promoted to `.specfuse/LEARNINGS.md` by gate 1's close.
T01 passed twelve criteria while silently withholding both budget proposals on
any relative `repo_root`, because every fixture used an absolute tempdir and no
test could tell "no evidence exists" from "the lookup failed." This WU has three
distinct absences to keep apart — no current value in the file, no proposal from
evidence, no readable baseline — and criteria 6 and 7 exist to make each one
separately observable.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because neither
`specfuse/loop/policy_review.py` nor `tests/test_policy_review.py` exists.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_policy_review.py::TestReviewAgentPolicy::test_baseline_match_is_classified_and_caveated`
   exists and **fails on HEAD before this WU runs** (the module and the test file
   are both absent — either counts as red).
2. `specfuse/loop/policy_review.py` defines
   `review_agent_policy(repo_root=None, *, runner=None) -> dict`, importable as
   `from specfuse.loop.policy_review import review_agent_policy`.
3. For each of the four in-scope keys the returned entry carries the current
   value read from the target `.specfuse/agent-policy.yml`, the proposal
   `propose_policy_defaults` returns for it (or an explicit "no proposal"
   marker), the shipped baseline value, and **which source the baseline came
   from** — the `agent_policy.DEFAULT_*` constant or
   `.specfuse/agent-policy.yml.example`.
4. The provenance classification is one of exactly three states —
   value matches the shipped baseline, value differs from it, or the key is
   absent from the file — and a fourth state is returned when the baseline
   itself could not be read (criterion 7).
5. An entry classified as matching the shipped baseline carries a caveat string
   **in the returned data** stating that a deliberate operator choice equal to
   the baseline is indistinguishable from a value never chosen. A test asserts
   the caveat is present on that class and absent on the differs-from class, so
   a downstream reader cannot pick up the hint without the disclaimer attached.
6. **Each entry records how its proposal was obtained** — one of `measured`
   (read directly from repo state) or `converted` (computed through a disclosed
   assumption). Of the four in-scope keys, `rules.bugs.test_paths` is the only
   `measured` one; `max_tokens_per_run` converts cost at an assumed tokens-per-
   dollar rate, and `max_items_per_day` applies a volume heuristic to a total
   with no per-day breakdown behind it. A test asserts the classification per
   key, and asserts a `converted` entry carries the assumption in its evidence.

   Operator decision at the gate-2 arming review: a converted proposal must not
   be presented as though it were measured. A 2.3x delta resting on an assumed
   rate invites a correction the evidence does not actually support, and the
   distinction has to live in the returned data or T05's readout cannot show it.

7. A test asserts the three absences are distinguishable from one another: a key
   absent from the policy file, a key present in the file for which
   `propose_policy_defaults` returns no proposal, and a key whose baseline is
   unreadable each produce a **different** observable result — no two collapse
   to the same value.
8. When `.specfuse/agent-policy.yml.example` is absent or unparseable, every key
   whose baseline would have come from it is classified baseline-unavailable
   rather than compared against a guess, and a test constructs that fixture
   directly.
9. `review_agent_policy` never reads, returns, or reports the `queue` key, and a
   test asserts `queue` appears nowhere in the returned structure even when the
   fixture policy file carries a populated `queue:`.
10. The function returns a **per-key readout only** — it never returns or writes a
   whole-file document. A test asserts the return value contains no rendering of
   the input file, which is what makes clobbering structurally impossible in the
   reference implementation rather than merely discouraged in prose.
11. `review_agent_policy` performs **no network call of its own**; `max_open_prs`
    evidence reaches it only through the injected `runner`, exactly as
    `propose_policy_defaults` takes it. A test passes a runner that raises and
    asserts the call still returns a readout.
12. `python3 -m unittest tests.test_policy_review -v` exits zero after this WU's
    edits, and `python3 -m unittest tests.test_policy_proposals -v` still exits
    zero **unmodified** — this WU composes T01's module and must not change it.

**Do not touch.** `specfuse/loop/policy_proposals.py` — this WU consumes
`propose_policy_defaults`, it does not edit it, and criterion 11 is the proof.
`specfuse/loop/agent_policy.py` — the schema and its validation are out of this
feature's scope boundary (`PLAN.md` § *Scope boundary*); this WU **reads**
`DEFAULT_*` and adds no key, no field, and no validation rule.
`.specfuse/agent-policy.yml` and `.specfuse/agent-policy.yml.example` — this WU
reads both and writes neither; the live file's values are the operator's call,
not a work unit's. `plugins/specfuse/skills/derive-agent-policy/` — the prose is
T05's. `tests/test_policy_proposals.py`. Generated directories, secrets,
`.git/`. The driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`,
and the remaining entries in that set. Plus the scoped run in criterion 11 and
the symbol-existence check
`python3 -c "from specfuse.loop.policy_review import review_agent_policy"`
(`/authoring-work-units` §9).

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
answering criterion 3 or 4 turns out to require a new field in
`.specfuse/agent-policy.yml`'s schema — that is the scope boundary
`GATE-02-REVIEW.md` § *The provenance question* explicitly declines to cross, and
crossing it silently is the failure that section exists to prevent, so report it
and stop; or `.specfuse/agent-policy.yml.example` turns out not to be a reliable
baseline source for a key criterion 3 requires (name the key). If
`review_agent_policy` is absent from `specfuse/loop/policy_review.py` in the
files you edited, emit `status: blocked` — do not claim complete.
