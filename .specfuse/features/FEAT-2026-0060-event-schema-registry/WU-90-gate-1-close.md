---
id: FEAT-2026-0060/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
oracle_env: macos_local
model: opus
effort: high
gate_set: plannext
verdict: met
driver_version: 0.8.0
started_at: 2026-08-03T12:11:25.511275+00:00
duration_seconds: 859.787
cost_usd: 4.534763
input_tokens: 90
output_tokens: 44661
---

# Close gate 1 and the feature — retrospective, lessons, docs, terminal verdict

**Objective.** Close the feature in one session: re-run every oracle fresh, write
`RETROSPECTIVE.md`, promote generalizable lessons, update the roadmap, and record
a terminal verdict.

**Context.** Correlation ID `FEAT-2026-0060/G1-CLOSE`. Gate 1 is terminal, so
this is the whole closing ceremony — there is no `plan-next` and no gate 2.
`assert_gate_review_exists` does **not** apply; that guard is `plan-next`-only.

**Read `.specfuse/rules/close-discipline.md` §4 before writing anything.** The
driver's guards match literal strings and are checked *after* this WU runs, so a
mismatch costs a full re-dispatch rather than a re-arm. Run
`specfuse-lint --closing` before reporting `complete`.

**Do not add an acceptance criterion flipping `PLAN.md` status to `done`.** The
driver owns that flip via `fire_terminal_flips`, gated on the verdict.

## What is specific to this feature

**This close writes events through the code the feature just sanctioned.** Every
event this session causes the driver to emit now validates against the registry
T01 built. That makes the close a live end-to-end test rather than bookkeeping:
re-running the new gate over this feature's *own* `events.jsonl` — written during
this gate, including `attempt_outcome` and `auto_close_decision` — is the
strongest single piece of evidence the feature works. Do that explicitly.

**Two LEARNINGS entries need correcting, not just citing.**
`[FEAT-2026-0002/G1-CLOSE]` states that *"the orchestrator's schema rejects
driver-emitted events by design (the schema's `source` enum is the orchestrator
protocol)"*. The vendored schema has **no `source` enum**; that lesson describes a
version this repository no longer ships, and it is the reason the gap was read as
intentional for as long as it was. Record the correction. Separately,
`loop.py:704` cited the gap as *precedent* — T01 was required to fix that comment;
confirm it did.

**The seven-type list was a measurement with a short half-life.** Four of the
seven appeared after the roadmap row was filed naming three. Report what T01
actually derived versus the seven `PLAN.md` recorded, and treat any difference as
signal about how fast this drifts — that number is the argument for T02's guard
existing at all.

**Close obligations.**

1. **Oracles re-run fresh (§1).** Every oracle this feature's criteria name, run
   again here with full commands and exit codes read directly — never a producing
   WU's self-report.
2. **Hedged follow-up record (§2).** On any verdict short of `met`, a named record
   per unmet criterion: the criterion, why it could not be verified here, and the
   exact re-run condition that upgrades it to `met`.
3. **Consumer-visible contract changes (§3).** Enumerate every addition, removal,
   or rename across T01–T02, or write exactly `n/a — no consumer-visible contract
   change`. **The new `verification.yml` gate is the headline entry**: a
   downstream project upgrading the scaffold gains a gate that will fail if its
   driver emits a type this registry does not sanction. That is the intended
   behaviour and it is still a new way for someone else's build to go red.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in the feature directory and is non-empty.
2. A `## Cost analysis` section reconciles `planned_cost_usd` — $13.00 from
   `PLAN.md`, per-WU $4.50 / $3.50 / $5.00 — against actual spend computed from
   `events.jsonl`, with the delta named. Sum every field a work unit's lifetime is
   spread across, not only frontmatter `cost_usd`.
3. The gate's $18.00 `cost_budget_usd` is reconciled against actual gate spend and
   any overrun reported plainly.
4. A `## What the loop did NOT verify` section enumerates each acceptance
   criterion whose verification was deferred, with why and where it is actually
   verified. Write `(nothing — every acceptance criterion was verified in-loop)`
   if the list is empty; the explicit count must be visible either way.
5. Every oracle named by T01–T02 is re-run in this session with its full command
   and exit code recorded: the driver-types test suite, the drift-guard suite, the
   new `verification.yml` gate, and the full `code` gate set (`tests`, `lint`,
   `security`, `coverage --fail-under=90`, `leak-scan`).
6. The validator is re-run over **every** `.specfuse/features/*/events.jsonl`
   including **this feature's own**, and the total error count recorded. It must
   be zero. This feature's own log is the end-to-end evidence per the Context.
7. `git diff --exit-code specfuse/loop/data/schemas/event.schema.json` is re-run
   and confirmed clean — the vendored envelope must be untouched, which is the
   whole premise of the driver-local design.
8. The type list T01 derived is compared against `PLAN.md`'s seven, with any
   difference named and read as drift-rate evidence.
9. T02's drift guard is confirmed to **fail** on a synthetic unregistered type —
   re-run that check here rather than trusting T02's report, since a guard never
   observed failing is the exact thing this feature exists to prevent.
10. A consumer-visible contract-change enumeration is present per close obligation
    3, naming the new gate explicitly.
11. `LEARNINGS [FEAT-2026-0002/G1-CLOSE]`'s `source`-enum claim is corrected in
    `.specfuse/LEARNINGS.md`, and `loop.py:704`'s comment is confirmed updated by
    T01.
12. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
    `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`.
13. The roadmap detail section for FEAT-2026-0060 is updated to reflect what was
    actually built — including that it was **seven** types, not the three the
    section names.
14. This WU's **frontmatter** carries a `verdict:` field whose value is one of
    `met`, `met_locally`, `partially_met`, `not_met`.
15. If any work unit in this gate recorded a failed attempt, a literal
    `### Failure-class breakdown` heading is present with the classes named.
16. `specfuse-lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Source files owned by T01–T02 — this WU closes the gate, it does
not patch the work. `PLAN.md`'s `status` field. The vendored
`event.schema.json`. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set for closing WUs, plus the oracle re-runs
in criteria 5–7 and 9, which are this WU's real verification surface.
`specfuse-lint --closing` (criterion 16) is the in-session check for the driver's
`assert_*` guards.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
oracle named in criterion 5 cannot be re-run; criterion 6 finds a non-zero error
count, which means the registry is incomplete and the fix is a re-dispatch of T01
rather than an edit from this session; criterion 7 shows the vendored envelope was
modified, which means the feature took the approach it was explicitly designed to
avoid; criterion 9's guard does not fail on a synthetic type, meaning T02's guard
is cosmetic; or the consumer-visible contract-change list requires a human
acknowledgment that has not been given. Record a hedged verdict (`met_locally` /
`partially_met`) with the follow-up record from close obligation 2 rather than
claiming `met` for a criterion verified only by a producing WU's self-report.
