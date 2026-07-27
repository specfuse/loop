---
id: FEAT-2026-0046/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
verdict: met
oracle_env: macos_local
model: opus
effort: high
gate_set: plannext
driver_version: 0.5.0
started_at: 2026-07-27T21:41:17.723014+00:00
duration_seconds: 360.934
cost_usd: 3.131087
input_tokens: 2999
output_tokens: 25732
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Close the feature in one session: re-run every oracle fresh, write
`RETROSPECTIVE.md`, promote generalizable lessons, update the roadmap, and record a
terminal verdict.

**Context.** Correlation ID `FEAT-2026-0046/G1-CLOSE`. Gate 1 is terminal, so this is
the whole closing ceremony — there is no `plan-next` and no gate 2.

**Read `.specfuse/rules/close-discipline.md` §4 before writing anything.** It lists
the exact strings the driver's guards match literally, and they are checked *after*
this WU runs, so a mismatch costs a full re-dispatch rather than a re-arm. Across 158
closing work units, 28% of all closing-WU spend went to exactly that. The rows that
apply here: `assert_retrospective_exists`, `assert_cost_analysis_section_when_met`
(a `## Cost analysis` heading), `assert_verdict_well_formed` (a `verdict:` field in
this file's **frontmatter**, not the body),
`assert_failure_class_breakdown_when_failures_present` (a literal
`### Failure-class breakdown` heading, three hashes, only if the gate had a failed
attempt), `assert_learnings_appended_or_noop`, and `assert_doc_or_roadmap_diff`.

`assert_gate_review_exists` does **not** apply — that guard is `plan-next`-only, and
this terminal gate has no `plan-next`.

`auto_close_disabled: true` is set because this close's criteria include re-running
oracles and enumerating consumer-visible contract changes, which makes it
load-bearing: the auto-close predicate must not skip it.

**Do not add an acceptance criterion flipping `PLAN.md` status to `done`.** The driver
owns that flip — `fire_terminal_flips` writes it, gated on the verdict, on both the
dispatched and the agent-less path. An agent flip is redundant and reopens the
divergence that cost issue #49.

**Close obligations.**

1. **Oracles re-run fresh (§1).** Every oracle this feature's criteria name, run
   again here with full commands and exit codes read directly — never a producing
   WU's self-report.
2. **Hedged follow-up record (§2).** On `met_locally`, a named record per unmet
   criterion: the criterion, why it could not be verified here, and the exact re-run
   condition that upgrades it to `met`.
3. **Consumer-visible contract changes (§3).** Enumerate every addition, removal, or
   rename across T01–T04, or write exactly `n/a — no consumer-visible contract
   change`. This feature adds a new module, a new skill, and a new label vocabulary,
   so the list is expected to be non-empty.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in the feature directory and is non-empty.
2. A `## Cost analysis` section is present, reconciling `planned_cost_usd` — $17.00
   from `PLAN.md`, and the per-WU figures $2.50 / $3.50 / $4.00 / $2.00 / $5.00 —
   against actual spend read from `events.jsonl`, with the delta named.
3. A `## What the loop did NOT verify` section is present, enumerating each acceptance
   criterion whose verification was deferred, and for each: the criterion, why it was
   deferred, and where verification actually happens. **This section will not be
   empty.** No work unit in this gate touched a real GitHub issue — every `gh`
   interaction ran through an injected stub — so the real `gh` invocation behind
   `emit_escalation`, and `/attention`'s live `gh pr list` sweep, are both unverified
   here and must be named as operator post-merge steps. If the list exceeds 2 entries
   or 30% of the gate's criteria, flag the feature's single-gate sizing under
   `## What I'd change`.
4. Every oracle named by T01–T04 is re-run in this session with its full command and
   exit code recorded: `python3 -m pytest tests/test_escalation_contract.py -q`,
   `tests/test_escalation_emit.py`, `tests/test_attention_skill_structure.py`,
   `tests/test_attention_nonwriting_guard.py`, `tests/test_skills_vendored_in_sync.py`,
   the two symbol-existence imports, and T02's criterion-8 grep.
5. A consumer-visible contract-change enumeration is present per close obligation 3.
6. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
   `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`.
7. The roadmap detail section for FEAT-2026-0046 is updated to reflect what was
   actually built.
8. This WU's **frontmatter** carries a `verdict:` field whose value is one of `met`,
   `met_locally`, `partially_met`, `not_met`.
9. If any work unit in this gate recorded a failed attempt, a literal
   `### Failure-class breakdown` heading is present with the classes named.

**Do not touch.** Source files owned by T01–T04 — this WU closes the gate, it does not
patch the work. `PLAN.md`'s `status` field. Generated directories, secrets, `.git/`.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set for closing WUs, plus the oracle re-runs in
criterion 4 which are this WU's real verification surface. `assert_*` guards listed in
the Context are checked by the driver after this WU completes.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
oracle named in criterion 4 cannot be re-run in this session; `events.jsonl` lacks the
cost data criterion 2 reconciles against; or the consumer-visible contract-change list
requires a human acknowledgment that has not been given. Record a hedged verdict
(`met_locally`) with the follow-up record from close obligation 2 rather than claiming
`met` for a criterion verified only by a producing WU's self-report.
