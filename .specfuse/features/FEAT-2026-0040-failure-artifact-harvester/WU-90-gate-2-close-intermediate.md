---
id: FEAT-2026-0040/G2-CLOSE-INTERMEDIATE
type: close-intermediate
status: draft
attempts: 0
planned_cost_usd: 4.50
oracle_env: macos_local
auto_close_disabled: true
---

# Close gate 2 — retrospective, lessons, docs, and an honest deferred list

**Objective.** Fold the retrospective, the lessons promotion, and the docs/roadmap
update into one session for gate 2. This is a non-terminal gate, so `G2-PLAN` runs
next and drafts gate 3; this unit records no terminal verdict.

**Context.** Correlation ID `FEAT-2026-0040/G2-CLOSE-INTERMEDIATE`. Depends on T04,
T05, T06, and T07. `auto_close_disabled: true` is set deliberately: this close carries
two obligations the auto-close predicate cannot discharge — a consumer-visible schema
change (T04's `dialect`) and gate 1's unenumerated auto-close debt — and
`close-discipline.md` requires a close carrying any such obligation to be load-bearing.

**Read `.specfuse/rules/close-discipline.md` §4 before writing anything.** Its guards
are matched literally and checked *after* this unit runs, so a mismatch costs a full
re-dispatch rather than a re-arm. The rows that apply here:
`assert_retrospective_exists`; `assert_retrospective_gate_section`, which requires a
heading matching `^#{1,3} Gate 2` — **`## Gate 2`, not "Gate two", not a bold line**;
`assert_learnings_appended_or_noop`; `assert_doc_or_roadmap_diff`; and
`assert_failure_class_breakdown_when_failures_present`, which wants a literal
`### Failure-class breakdown` heading with **three** hashes, only if this gate had a
failed attempt.

`assert_verdict_well_formed` does **not** apply — that guard is `close`-only, and a
terminal verdict for this feature belongs to `G3-CLOSE`.

**This gate's deferred list will not be empty, and pretending otherwise is the
failure.** `verification.yml` records that this repo "is a CLI tool with no deployable
components and will never carry a real monitoring.yml." Every adapter T05–T07 ship was
verified against a **stub transport**. A stub proves the adapter's shape, its
coordinate handling, its redaction boundary, and its fingerprint behaviour; it proves
nothing about the real Service Bus peek API, the real KQL result schema, or whether a
live workspace returns the columns the queries name. Those are verified only by an
operator run against the downstream .NET backend — the same oracle 0069 used to
discharge its follow-ups. Name that in `## What the loop did NOT verify` rather than
claiming what a stub proved.

Gate 1's deferred list was, by contrast, expected to be empty and was never
enumerated: gate 1 **auto-closed on-plan**, and `RETROSPECTIVE.md` carries the
`specfuse:autoclose-debt gate=1` marker recording that its 32 acceptance criteria went
unenumerated. That reconciliation is this unit's — the terminal close should inherit a
reconciled list, not the debt itself.

**Close obligations.**

1. **Oracles re-run fresh (§1).** Every oracle T04–T07 name, run again here with full
   commands and exit codes read directly — never a producing unit's self-report.
2. **Consumer-visible contract changes (§3).** T04 adds a **required-when-`cron`-present
   `dialect` field** to every heartbeat target. That is a consumer-visible schema
   change and, for any downstream project whose `monitoring.yml` already carries a
   cron-carrying heartbeat target, a **breaking** one: their config lints clean today
   and will not after upgrade. Enumerate it as breaking, with the migration a consumer
   performs, and block on explicit human acknowledgment. Do not write
   `n/a — no consumer-visible contract change` here; it would be false.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists in the feature directory, is non-empty, and contains a
   heading matching `^#{1,3} Gate 2`.
2. A `## Cost analysis` section reconciles this gate's `cost_budget_usd` and the
   per-unit `planned_cost_usd` figures against actual spend read from `events.jsonl`,
   with the delta named. Report the **as-drafted** figures as the honest ones; do not
   re-base the plan onto its own failure and then report the result as accuracy
   (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`).
3. A `## What the loop did NOT verify` section enumerates each acceptance criterion
   whose verification was deferred, with why and where it is actually verified. It
   must name, in these terms: that T05–T07's adapters were exercised **only against
   stub transports**, that no live Service Bus namespace or App Insights workspace was
   reached, and that the downstream .NET backend operator run is the oracle that
   discharges them.
4. The same section **reconciles gate 1's auto-close debt**: `RETROSPECTIVE.md`
   carries a `specfuse:autoclose-debt gate=1` marker for T01–T03's 32 criteria, which
   gate 1's auto-close never enumerated. Either enumerate what genuinely remains
   deferred from gate 1 or state, per criterion, that it was verified in-loop — gate 1
   was scoped so that list can legitimately be empty, and saying so explicitly is what
   turns the marker from debt into a reconciled record.
5. Every oracle named by T04–T07 is re-run in this session with its command and exit
   code recorded: `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example`,
   `tests.test_monitoring_cron_dialect`, `tests.test_monitoring_fenced_blocks`,
   `tests.test_derive_monitoring_discovery`, `tests.test_service_bus_dlq_adapter`,
   `tests.test_app_insights_adapters`, `tests.test_schedule_dialect`,
   `tests.test_heartbeat_adapter`, and the provider-leakage greps from T05 criterion 9,
   T06 criterion 10, and T07 criterion 11.
6. **The sweep is re-run, not inherited.** T04's tree-wide completeness assertion is
   executed fresh here and reports zero non-conforming instances **and** a non-zero
   collected count. A sweep that passes vacuously is the defect the criterion was
   written against, and only a fresh run distinguishes the two.
7. The provider-agnosticism claim is verified **as a property of the tree**, not only
   as a passing test: `grep -rniE "azure|appinsights|servicebus|kusto"
   specfuse/monitor/` reports matches **only** under `specfuse/monitor/providers/` or
   inside comments and docstrings elsewhere, and every match outside `providers/` is
   named in the retrospective.
8. Which sandbox each gate ran under is stated. Three of this repo's `code` gates are
   `bats` suites whose `setup` calls `mktemp -d`; under the session's default sandbox
   that returns `Operation not permitted` and all cases fail before an assertion runs.
   A close reporting a bare pass count would manufacture a regression
   (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`).
9. A consumer-visible contract-change enumeration is present per close obligation 2,
   with the `dialect` entry marked **breaking** and the consumer-side migration stated.
10. Generalizable lessons are appended to `.specfuse/LEARNINGS.md`, or
    `RETROSPECTIVE.md` contains the exact phrase `nothing generalizes`.
11. The roadmap detail section for FEAT-2026-0040 reflects what gate 2 actually built,
    and `docs/concepts/monitoring-schema.md` matches the validator's real behaviour —
    not the behaviour T04 intended.
12. If any work unit in this gate recorded a failed attempt, a literal
    `### Failure-class breakdown` heading is present with the classes named.

**Do not touch.** Source files owned by T04–T07 — this unit closes the gate, it does
not patch the work. If an oracle fails here, that is a finding to report, not a fix to
apply. `PLAN.md`'s `status` field. Gate 3's work units — `G2-PLAN` drafts those.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set for closing units, plus the oracle re-runs in
criterion 5, the fresh sweep in criterion 6, and the tree-wide grep in criterion 7,
which are this unit's real verification surface.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: an
oracle named in criterion 5 cannot be re-run; `events.jsonl` lacks the cost data
criterion 2 reconciles against; criterion 6's sweep reports a non-conforming instance,
which means the tree drifted after T04 and is a finding rather than a fix; criterion
7's grep finds a provider identifier in the core, which would mean gate 1's and gate
2's central claim is false; or the contract-change acknowledgment in obligation 2 has
not been given — a breaking schema change is exactly the case
`close-discipline.md` §3 blocks on rather than passes through.
