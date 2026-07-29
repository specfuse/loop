---
id: FEAT-2026-0053/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 4.50
oracle_env: macos_local
auto_close_disabled: true
---

# Close gate 1 — retrospective, lessons, docs

**Objective.** Fold the retrospective, the lessons promotion, and the docs and
roadmap update into one session for gate 1. Non-terminal gate: `G1-PLAN` runs
next; this unit records no terminal verdict.

**Context.** Correlation ID `FEAT-2026-0053/G1-CLOSE-INTERMEDIATE`. Depends on
T01–T04.

**Read `.specfuse/rules/close-discipline.md` §4 before writing anything.** Its
guards match literally and are checked *after* this unit runs. The rows that
apply here: `assert_retrospective_exists`; `assert_retrospective_gate_section`
(heading matching `^#{1,3} Gate 1` — `## Gate 1`, not "Gate one");
`assert_learnings_appended_or_noop`; `assert_doc_or_roadmap_diff`; and
`assert_failure_class_breakdown_when_failures_present` (literal
`### Failure-class breakdown`, three hashes, only if a failed attempt occurred).
`assert_verdict_well_formed` does not apply — terminal verdicts belong to
`G3-CLOSE`.

**Close obligations.**

1. **Oracles re-run fresh (§1).** Every oracle T01–T04 name, run again here with
   full commands and exit codes read directly — never a producing unit's
   self-report.
2. **Consumer-visible contract changes (§3).** Enumerate every addition across
   T01–T04, or write exactly `n/a — no consumer-visible contract change`. Gate 1
   adds two new modules, three template-documented frontmatter fields, one new
   event type, and one new per-feature artifact (`PLAN.baseline.json`) — the
   list is additive but real; the event type and baseline file are
   consumer-visible to every downstream Specfuse project.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in the feature directory, is non-empty, and
   contains a heading matching `^#{1,3} Gate 1`.
2. A `## Cost analysis` section is present, reconciling `planned_cost_usd` —
   $23.50 for this gate, per-unit $2.50 / $3.00 / $4.50 / $3.00 / $4.50 /
   $6.00 — against actual spend read from `events.jsonl`, with the delta named.
3. A `## What the loop did NOT verify` section is present, enumerating each
   acceptance criterion whose verification was deferred, with why and where it
   is actually verified. Gate 1 was scoped fully in-loop — if the list is empty
   write `(nothing — every acceptance criterion was verified in-loop)`; if not,
   that is a finding about the gate cut worth stating plainly. More than 2
   entries or 30% of criteria requires flagging the sizing under
   `## What I'd change`.
4. Every oracle named by T01–T04 is re-run in this session with command and
   exit code recorded: `python3 -m unittest tests.test_plan_baseline -v`,
   `tests.test_lint_plan_contract_fields`, `tests.test_arm_eval`,
   `tests.test_arm_eval_wiring`, `tests.test_scaffold_data_in_sync`, and the
   two symbol-existence imports (`plan_baseline`, `arm_eval`).
5. A consumer-visible contract-change enumeration is present per close
   obligation 2.
6. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
   `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`.
7. The roadmap detail section for FEAT-2026-0053 reflects what gate 1 actually
   built.
8. If any work unit in this gate recorded a failed attempt, a literal
   `### Failure-class breakdown` heading is present with the classes named.

**Timing note.** The `arm_predicate_evaluated` event for THIS gate fires at the
`awaiting_review` flip — *after* this unit and `G1-PLAN` both finish. This unit
therefore cannot observe it; the human verifies the first live firing at the
arming checkpoint (see `GATE-01.md`'s arming discipline). Do not add a check
for it here — it would be unsatisfiable by construction.

**Do not touch.** Source files owned by T01–T04 — this unit closes the gate, it
does not patch the work. `PLAN.md`'s `status` field. Gate 2's WUs — `G1-PLAN`
drafts those. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set for closing units, plus the oracle
re-runs in criterion 4 and the event-trail check in criterion 5, which are this
unit's real verification surface.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
an oracle in criterion 4 cannot be re-run, or `events.jsonl` lacks the cost
data criterion 2 reconciles against.
