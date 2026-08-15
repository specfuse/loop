---
id: FEAT-2026-0076/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.50
oracle_env: macos_local
produces:
  - specfuse/loop/policy_proposals.py
  - tests/test_policy_proposals.py
produces_driver_helper: propose_policy_defaults
model: sonnet
effort: medium
gate_set: code
driver_version: 0.10.0
started_at: 2026-08-10T14:28:34.578334+00:00
duration_seconds: 825.259
cost_usd: 1.959089
input_tokens: 95
output_tokens: 30438
---

# Propose agent-policy values from repository evidence

**Objective.** Create `specfuse/loop/policy_proposals.py` exposing
`propose_policy_defaults(repo_root=None, *, runner=None) -> dict`: for each
derivable `agent-policy.yml` value, a proposal carrying **the value and the
evidence it came from** — or no proposal at all where the evidence is absent.

**Context.** Correlation ID `FEAT-2026-0076/T01`. Foundation WU: T02's skill
prose must describe this algorithm, so the shape fixed here is what the prose
quotes.

**Why the evidence travels with the value, not just the number.** This feature
exists because `agent-policy.yml` is full of values an agent chose and never
explained. A proposal of `2000000` is the same opaque thing again. *"Proposed
2000000 — your last 30 runs peaked at 1.4M output tokens"* is a conversation the
operator can disagree with. The evidence string is the deliverable as much as the
number is.

**Proposing nothing is a first-class outcome.** On a repository with no
`events.jsonl`, the honest answer is not a plausible-looking budget — it is *no
proposal*, so the interview presents the shipped default and says plainly that it
is a default. A confident wrong proposal is worse than an absent one, because the
operator has no way to tell it was invented. This is the same failure shape as
`[FEAT-2026-0039]`, where a skill emitted 30 components with total confidence.

**Reuse, do not rebuild.** Read these first:

- `specfuse/loop/events_stats.py` — `collect(roots) -> dict` aggregates
  `events.jsonl` across feature folders. The source for token and item budgets.
- `specfuse/loop/gate_commands.py` — `iter_code_gates(...)` / `code_gate_names(...)`
  read `verification.yml`'s `code` set. A gate command like
  `python3 -m unittest discover -s tests` names the test directory; that is
  evidence for `test_paths`, alongside the directory tree itself.
- `specfuse/loop/agent_policy.py` — `DEFAULT_MAX_DIFF_LINES`,
  `DEFAULT_MAX_MERGES_PER_DAY`, `DEFAULT_TEST_PATHS`, and
  `validate_agent_policy`. **Consume these; do not extend the schema** (PLAN.md
  § *Scope boundary*).

**Values in scope.** Propose only what evidence can answer:
`budgets.max_tokens_per_run`, `budgets.max_items_per_day`,
`budgets.max_open_prs`, and `rules.bugs.test_paths`. Everything else in the file
(`gate_review`, `wip_limit`, `preempt`, `min_severity`, `automerge`, the whole
`escalation` block) is operator judgment with no repo evidence behind it —
those are the interview's *questions*, not its proposals, and this module must
not invent them.

**`queue:` is out of scope entirely** — `/groom-backlog` owns it (PLAN.md
decision 2).

**No network except through the injected runner.** `max_open_prs` needs the
repo's open-PR count; take a `runner` callable exactly as `triage.py` and
`bug_lane_state.py` do, so tests never reach GitHub. An absent or failing runner
yields no proposal for that value, not a guess.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because the
module does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_policy_proposals.py::TestProposeDefaults::test_empty_repo_proposes_nothing`
   exists and **fails on HEAD before this WU runs** (the module does not exist).
2. `specfuse/loop/policy_proposals.py` defines
   `propose_policy_defaults(repo_root: str | Path | None = None, *, runner=None) -> dict`.
3. Each proposal is a mapping carrying at least the proposed `value` and a
   non-empty `evidence` string naming where it came from. A test asserts no
   proposal is returned with an empty or missing `evidence`.
4. A repository with **no** `events.jsonl` anywhere returns **no** proposal for
   `max_tokens_per_run` or `max_items_per_day` — not a default dressed as a
   proposal. A test asserts the keys are absent from the result.
5. A repository **with** `events.jsonl` fixtures returns a proposal for both,
   derived via `events_stats.collect` rather than a re-implementation. A test
   asserts the proposed value is a function of the fixture data (change the
   fixture, the proposal changes).
6. `test_paths` is proposed from evidence in both directions: a fixture whose
   tests live in `tests/` proposes `["tests/"]`; a fixture whose tests live in
   `spec/` with a matching gate command proposes `["spec/"]`. A test covers both.
7. A repository where the tree and the gate commands **disagree** about the test
   layout proposes the union and says so in the `evidence` string, rather than
   silently picking one. A test covers the disagreement case.
8. `max_open_prs` is proposed only when the injected `runner` returns a usable
   count; an absent runner, a failing runner, and unparseable output each yield
   **no** proposal for it and do not raise. A test covers all three.
9. **Every proposed value validates clean.** A test builds a policy file from
   the proposals plus the shipped defaults for everything else, runs
   `validate_agent_policy` against it, and asserts zero `ERROR: ` findings. A
   proposer that emits what its own validator rejects is the feature failing at
   its purpose.
10. The module performs no network call and opens no file outside `repo_root` —
    a test exercises the whole surface with fixtures and a fake runner.
11. `python3 -m unittest tests.test_policy_proposals -v` exits zero after this
    WU's edits.
12. `python3 -c "from specfuse.loop.policy_proposals import propose_policy_defaults"`
    exits zero.

**Do not touch.** `specfuse/loop/agent_policy.py` — consume its constants and
validator, do not extend the schema; a new dial belongs to the feature that
introduces it. `specfuse/loop/events_stats.py` and `gate_commands.py` — call
them, do not modify them. `.specfuse/agent-policy.yml` — this WU proposes
values, it never writes the live file. The `queue:` key in any form. Generated
directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `agent-policy-example-lint`.
Plus the scoped red/green run in criteria 1 and 11 and the symbol check in 12.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`events_stats.collect` does not expose per-run token or cost data usable for a
budget proposal (report its actual shape rather than inventing a second
aggregator); `gate_commands` cannot be read without executing a gate command
(this module must never run one); or a value in scope turns out to need a schema
change to propose, which PLAN.md's scope boundary puts out of this feature. If
`specfuse/loop/policy_proposals.py` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
