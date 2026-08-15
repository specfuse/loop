---
id: FEAT-2026-0048/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - tests/test_bug_lane_policy_contract.py
produces_driver_helper: resolve_bug_automerge, bug_lane_limits
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T04:54:50.101122+00:00
duration_seconds: 312.051
cost_usd: 0.805799
input_tokens: 30
output_tokens: 9457
---

# Verify the shipped policy schema against this plan's assumptions, then add the bug-lane dials

**Objective.** Assert that `specfuse/loop/agent_policy.py` shipped the surfaces
this feature assumed, escalate if it did not, and — only once verified — add
`resolve_bug_automerge()` and `bug_lane_limits()` plus the two new dials the
merge guardrails need.

**Context.** Correlation ID `FEAT-2026-0048/T01`. First WU of a strictly serial
gate.

**This WU exists because this feature was planned against a file that did not
exist.** FEAT-2026-0048 was drafted the same evening as FEAT-2026-0044 and
before it ran, so every schema reference in `PLAN.md` is an assumption. That is
the `[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/roadmap-row-verbs-are-claims]` shape,
and this unit is its mechanical mitigation: **verify first, build second,
escalate on divergence rather than adapting silently.**

Adapting silently is the failure mode to avoid. If `rules.bugs.automerge` turns
out to live somewhere else, or `load_policy` has a different signature, the
right response is `status: blocked` with the divergence named — not a quiet
rewrite of this feature's assumptions, because `PLAN.md`, T02, T03, and T04 all
encode the same ones and would then disagree with reality in three more places.

**Assumed surfaces to verify** (from `PLAN.md` § *The dependency that makes T01
exist*), quoted verbatim:

| Assumed surface | Assumed shape |
|---|---|
| `specfuse/loop/agent_policy.py` | module exists |
| `load_policy(path=None) -> dict` | returns the parsed mapping |
| `validate_agent_policy(path=None) -> list[str]` | findings prefixed `ERROR: ` / `WARN: ` |
| `rules.bugs.automerge` | `off` \| `on`, default `off` |
| `rules.bugs.min_severity` | `low` \| `medium` \| `high` \| `critical` |
| `rules.bugs.preempt` | bool |

**The two dials to add**, both under the existing `rules.bugs` block so the
class rules stay in one place:

```yaml
rules:
  bugs:
    max_diff_lines: 150       # int > 0 — merge-eligibility size cap
    max_merges_per_day: 3     # int > 0 — rolling 24h auto-merge cap
```

Defaults are deliberately conservative: a bug fix larger than 150 changed lines
is not the "small, cheap to revert" shape this lane's risk argument rests on,
and three merges a day bounds a bad night.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because
`resolve_bug_automerge` does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_bug_lane_policy_contract.py::TestPolicyContract::test_resolve_bug_automerge_defaults_off`
   exists and **fails on HEAD before this WU runs**.
2. A test asserts every row of the assumed-surfaces table above: the module
   imports, `load_policy` and `validate_agent_policy` are callable with the
   documented signatures, and the shipped
   `.specfuse/agent-policy.yml.example` carries `rules.bugs.automerge`,
   `rules.bugs.min_severity`, and `rules.bugs.preempt`.
3. If any row of that table does not hold, this WU emits `status: blocked`
   naming the divergent surface and its actual shape — it does **not** adapt.
4. `specfuse/loop/agent_policy.py` gains
   `resolve_bug_automerge(path: str | Path | None = None) -> bool`, returning
   `True` only when `rules.bugs.automerge` is exactly the string `"on"`.
5. `resolve_bug_automerge` returns `False` when the policy file is absent, when
   the key is absent, and when the value is anything other than `"on"` —
   including the boolean `True`, which is not the declared spelling. A test
   covers all four.
6. `specfuse/loop/agent_policy.py` gains
   `bug_lane_limits(path: str | Path | None = None) -> dict` returning
   `{"max_diff_lines": int, "max_merges_per_day": int}`, with the documented
   defaults (`150`, `3`) when the file or the keys are absent.
7. `validate_agent_policy` accepts and validates `max_diff_lines` and
   `max_merges_per_day` — each must be an `int > 0`, else an `ERROR: ` finding
   naming the key. A test covers a zero, a negative, and a string.
8. `.specfuse/agent-policy.yml.example` documents both new dials with their
   permitted values, and `validate_agent_policy` returns `[]` against it.
9. This repo's live `.specfuse/agent-policy.yml` keeps
   `rules.bugs.automerge: off`. A test asserts this explicitly — the feature
   builds the dial and must not turn it on.
10. `python3 -m unittest tests.test_bug_lane_policy_contract -v` exits zero
    after this WU's edits.
11. `python3 -c "from specfuse.loop.agent_policy import resolve_bug_automerge, bug_lane_limits"`
    exits zero.

**Do not touch.** `specfuse/loop/triage.py`. `specfuse/monitor/autofix*.py` —
T03 and T04 own the lane. `specfuse/loop/arm_eval.py` — T02 imports from it and
nothing in this feature modifies it. `.specfuse/roadmap.md`. Generated
directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, and the
`agent-policy-example-lint` gate FEAT-2026-0044 added. Plus the scoped red/green
run in criteria 1 and 10 and the symbol check in criterion 11.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
**any row of the assumed-surfaces table does not hold** — this is the WU's
primary job, not an edge case, and a divergence must reach the operator because
`PLAN.md`, T02, T03, and T04 all encode the same assumptions; or
`specfuse/loop/agent_policy.py` does not exist at all, meaning FEAT-2026-0044
did not land and this feature was dispatched out of order. If
`resolve_bug_automerge` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
