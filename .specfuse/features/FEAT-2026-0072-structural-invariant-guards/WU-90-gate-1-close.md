---
id: FEAT-2026-0072/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
verdict: met_locally
model: opus
effort: high
gate_set: plannext
driver_version: 0.5.0
started_at: 2026-07-28T15:24:41.454793+00:00
duration_seconds: 615.176
cost_usd: 5.182915
input_tokens: 97
output_tokens: 38677
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Close the feature in one session: re-run every oracle fresh, write
`RETROSPECTIVE.md`, promote generalizable lessons, update the roadmap, and record
a terminal verdict.

**Context.** Correlation ID `FEAT-2026-0072/G1-CLOSE`. Gate 1 is terminal, so this
is the whole closing ceremony — there is no `plan-next` and no gate 2.

**Read `.specfuse/rules/close-discipline.md` §4 before writing anything.** It
lists the exact strings the driver's guards match literally, checked *after* this
WU runs, so a mismatch costs a full re-dispatch rather than a re-arm. Across 158
closing work units, 28% of all closing-WU spend went to exactly that. The rows
that apply: `assert_retrospective_exists`,
`assert_cost_analysis_section_when_met` (a `## Cost analysis` heading),
`assert_verdict_well_formed` (a `verdict:` field in this file's **frontmatter**,
not the body), `assert_failure_class_breakdown_when_failures_present` (a literal
`### Failure-class breakdown` heading, three hashes, only if the gate had a
failed attempt), `assert_learnings_appended_or_noop`, and
`assert_doc_or_roadmap_diff`.

`assert_gate_review_exists` does **not** apply — that guard is `plan-next`-only,
and this terminal gate has no `plan-next`.

**Do not add an acceptance criterion flipping `PLAN.md` status to `done`.** The
driver owns that flip via `fire_terminal_flips`, gated on the verdict. An agent
flip is redundant and reopens the divergence that cost issue #49.

**One thing to check that is specific to this feature.** This feature adds a
`lint_plan` check that a `done` feature's gates are all `passed`. When
`fire_terminal_flips` closes *this* feature, its own gate flips to `passed` — so
the new check must not fire on the feature that introduced it. Verify that
explicitly rather than assuming.

**Close obligations.**

1. **Oracles re-run fresh (§1).** Every oracle this feature's criteria name, run
   again here with full commands and exit codes read directly — never a producing
   WU's self-report.
2. **Hedged follow-up record (§2).** On `met_locally`, a named record per unmet
   criterion: the criterion, why it could not be verified here, and the exact
   re-run condition that upgrades it to `met`.
3. **Consumer-visible contract changes (§3).** Enumerate every addition, removal,
   or rename across T01–T03, or write exactly `n/a — no consumer-visible contract
   change`. **A new blocking `lint_plan` error is the headline entry** — a
   downstream project whose tree has a done feature with an unclosed gate will
   start failing its plan-lint gate on upgrade. Say so plainly.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in the feature directory and is non-empty.
2. A `## Cost analysis` section is present, reconciling `planned_cost_usd` —
   $14.00 from `PLAN.md`, and the per-WU figures $2.50 / $3.00 / $3.50 / $5.00 —
   against actual spend read from `events.jsonl`, with the delta named.
3. A `## What the loop did NOT verify` section is present, enumerating each
   acceptance criterion whose verification was deferred, with why and where it is
   actually verified. Write
   `(nothing — every acceptance criterion was verified in-loop)` if the list is
   empty; the explicit count must be visible either way. If the list exceeds 2
   entries or 30% of the gate's criteria, flag the feature's single-gate sizing
   under `## What I'd change`.
4. Every oracle named by T01–T03 is re-run in this session with its full command
   and exit code recorded: `python3 -m pytest tests/test_skill_discovery_links.py -q`,
   `tests/test_done_feature_gates.py`, `tests/test_bats_suites_gated.py`,
   `bats tests/sync_scaffold_symlinks.bats`, `bats tests/sync_scaffold.bats`,
   `shellcheck scripts/sync-scaffold.sh`, `bash -n scripts/sync-scaffold.sh`, and
   T03's criterion-11 tree-wide `lint_plan` sweep.
5. A consumer-visible contract-change enumeration is present per close obligation
   3, naming the new blocking `lint_plan` error explicitly.
6. The new done-feature gate check is confirmed **not** to fire on this feature
   itself once its own gate is flipped to `passed`.
7. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
   `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`.
8. The roadmap detail section for FEAT-2026-0072 is updated to reflect what was
   actually built, and issues #284 and #287 are named as resolved by it.
9. This WU's **frontmatter** carries a `verdict:` field whose value is one of
   `met`, `met_locally`, `partially_met`, `not_met`.
10. If any work unit in this gate recorded a failed attempt, a literal
    `### Failure-class breakdown` heading is present with the classes named.

**Do not touch.** Source files owned by T01–T03 — this WU closes the gate, it does
not patch the work. `PLAN.md`'s `status` field. The gate files of FEAT-2026-0007,
-0008, and -0036 — T03 owns those. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set for closing WUs, plus the oracle re-runs
in criterion 4 which are this WU's real verification surface. The `assert_*`
guards listed in the Context are checked by the driver after this WU completes.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
oracle named in criterion 4 cannot be re-run; the new check fires on this feature
itself (criterion 6), which would mean the check or the flip ordering is wrong;
`events.jsonl` lacks the cost data criterion 2 reconciles against; or the
consumer-visible contract-change list requires a human acknowledgment that has not
been given. Record a hedged verdict (`met_locally`) with the follow-up record from
close obligation 2 rather than claiming `met` for a criterion verified only by a
producing WU's self-report.
