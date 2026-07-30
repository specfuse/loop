---
id: FEAT-2026-0054/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.00
oracle_env: macos_local
produces_driver_helper: "specfuse.loop.closing_requirements — CLOSING_REQUIREMENTS registry + requirement dataclass; CLOSING_ASSERTIONS_BY_TYPE guards refactored to read it"
produces:
  - specfuse/loop/closing_requirements.py
  - tests/test_closing_requirements.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.7.0
started_at: 2026-07-30T12:15:18.265773+00:00
duration_seconds: 799.689
cost_usd: 3.388021
input_tokens: 130
output_tokens: 40668
---

# Extract the closing-requirement registry — one contract, one home

**Objective.** A single machine-readable registry of every closing-artifact requirement, which
the existing post-squash guards read from — so a later lint mode (T02) and skeleton writer (T03)
cannot drift from what the guards actually check.

**Context.** Gate 1 of FEAT-2026-0054, no dependencies. Today the closing contract lives only
inside the `assert_*` function bodies registered in `CLOSING_ASSERTIONS_BY_TYPE`
(`specfuse/loop/loop.py:4294`; functions at `:3926`–`:4290` area). The durable rule this WU
serves: [FEAT-2026-0070/G1-CLOSE-INTERMEDIATE] in `.specfuse/LEARNINGS.md` — a contract
enforced at two moments needs one home both read. Binding rules:
`.specfuse/rules/result-contract.md`, `never-touch.md`, `correlation-ids.md`.

**Acceptance criteria.**

- `tests/test_closing_requirements.py::TestRegistryShape::test_registry_covers_all_registered_guards`
  **fails on HEAD** (module does not exist) before this WU runs.
- New module `specfuse/loop/closing_requirements.py` declares, per WU type (`close`,
  `close-intermediate`, `plan-next`), each requirement as data: required file (and how its name
  is derived, e.g. `GATE-{next_gate:02d}-REVIEW.md`), required heading with exact level (e.g.
  `## Cost analysis`, `### Failure-class breakdown`), required frontmatter field with allowed
  values (`verdict:` ∈ met / met_locally / partially_met / not_met), the condition under which
  it applies (always; when verdict=met; when gate had failed attempts; when autoclose-debt
  marker present), and the name of the post-squash guard that enforces it.
- Every function listed in `CLOSING_ASSERTIONS_BY_TYPE` (all types) derives its checked
  strings/paths from the registry — no literal heading, filename pattern, or verdict-value list
  remains inline in a guard body. Grep-checkable: `grep -n "Cost analysis\|Failure-class breakdown"
  specfuse/loop/loop.py` returns no matches inside guard functions after the refactor.
- Behavior equivalence proven: existing guard tests pass unchanged, and
  `TestRegistryEquivalence` exercises each guard through the registry on fixture feature dirs
  covering at least: missing retrospective, missing verdict, verdict=met without cost-analysis
  heading, failed-attempts gate without failure-class heading, plan-next without the
  next-gate review file.
- `POST_PASS_INVARIANTS_BY_TYPE` entries (`assert_autoclose_debt_reconciled`,
  `assert_terminal_flips_fired`) are **registered in the registry as post-pass phase entries**
  (so T02's lint can name them) but their function bodies are refactored only if zero-risk;
  otherwise they carry a registry pointer comment naming this exemption.
- Same-test-passes criterion: `tests/test_closing_requirements.py` passes in full after the
  WU's edits.

**Do not touch.** `specfuse/loop/lint_plan.py` (T02's surface); `dispatch()` and the stub-retro
writers (T03's surface); `specfuse/loop/data/**` and `plugins/**` (T04's surface); other
features' folders; `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml` (unittest discover, ruff,
bandit, coverage). Plus symbol check:
`python3 -c "from specfuse.loop.closing_requirements import CLOSING_REQUIREMENTS"`.

**Escalation triggers.** If any guard's checked strings cannot be derived from data without
changing what the guard accepts (behavior change), stop and emit `status: blocked` — this WU is
a pure refactor; equivalence is the contract. If `CLOSING_REQUIREMENTS` is absent from the
files you edited, emit `status: blocked` — do not claim complete.
