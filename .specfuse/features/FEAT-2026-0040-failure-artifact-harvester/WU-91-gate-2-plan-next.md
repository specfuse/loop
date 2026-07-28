---
id: FEAT-2026-0040/G2-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
model: opus
effort: high
gate_set: plannext
---

# Draft gate 3 — the issue lifecycle, the CLI, and the runner surfaces

**Objective.** Draft gate 3's substantive work units into `PLAN.md`, and write
`GATE-03-REVIEW.md` for the human review-and-arm checkpoint.

**Context.** Correlation ID `FEAT-2026-0040/G2-PLAN`. Depends on
`G2-CLOSE-INTERMEDIATE`, whose retrospective and lessons are this unit's primary input
— gate 3 is drafted from what gate 2 actually learned, not from what gate 2 predicted.

**The review artifact is named for the gate being armed, not the gate being closed.**
`assert_gate_review_exists` requires **`GATE-03-REVIEW.md`**. `close-discipline.md` §4
records this as the single most expensive guard in the system — $53.11 of measured
waste across 15 refusals — because the intuitive name is wrong. A gate-2 `plan-next`
writes `GATE-03-REVIEW.md`.

**What gate 3 is for**, per `PLAN.md`: the fingerprint-keyed GitHub issue lifecycle,
the `specfuse-monitor run` CLI that drives the adapters through a polling cycle, and
the local plus GitHub Actions runner surfaces.

**Three things gate 3 must carry, and they are known now.**

1. **`escalation.py` is reused, not reimplemented — and its known weakness is
   addressed rather than inherited.** FEAT-2026-0046 shipped `_correlation_marker`,
   `_find_existing_issue`, `_default_runner`, `_extract_issue_number`, and idempotent
   find-then-create; the harvester's lifecycle is the same shape with a fingerprint in
   place of a correlation ID. 0046's own retrospective records that GitHub's search
   index does not reliably tokenise HTML-comment content, so a search returning nothing
   silently files a duplicate on every retry. That is the one property a deduplicating
   harvester cannot afford to get wrong. A drafted WU must own it explicitly.
2. **This gate's central surface produces zero in-loop evidence.**
   `[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]` records that `gh` returns auth errors
   inside `claude -p`. Gate 3 was isolated at feature-drafting time for exactly this
   reason. Each such unit must be either designated out-of-loop with an operator-journal
   artifact as its verification proxy, or scoped to a stubbed runner with the real
   invocation named as a **deferred** criterion. A hedged verdict here is the expected
   outcome; an unhedged one claimed on stub evidence is not.
3. **Quiet-based auto-close stays out.** The roadmap's own words: findings may be
   annotated "quiet for N runs — candidate for close", but humans close. No exception,
   and a drafted WU that reintroduces it is out of scope rather than a nice extra.

**And the terminal close is gate 3's, so its placeholder must be rewritten.**
`WU-90-gate-3-close.md` is a `status: draft` placeholder written at feature-drafting
time; its body says so and asks whoever arms gate 3 to rewrite it against what gate 3
actually contains. Two things it must gain: an instruction to reconcile the
`specfuse:autoclose-debt` marker by naming **`gate 1`** literally in
`## What the loop did NOT verify` — `assert_autoclose_debt_reconciled` matches that
string — and an accurate `depends_on` list once gate 3's substantive units exist.

**`queue-stalled` gets its adapter in gate 3 — an operator decision taken at gate 2's
arming, recorded in `GATE-02-REVIEW.md` §6.1.** Gate 2 was kept as the adapter-*shape*
gate, so the check type 0069 added for a wedged consumer was deliberately left out of
`T05`. It is not an oversight and must not be rediscovered as one. It reads a **broker**
coordinate — queue depth and age-of-oldest — not a telemetry one, so it extends `T05`'s
`BrokerAdapter` rather than the telemetry adapters, and the threshold's units are
currently opaque in the schema. Draft it here, alongside the CLI.

**Acceptance criteria.**

1. `GATE-03-REVIEW.md` exists in the feature directory and is non-empty. The filename
   is literal — named for the gate being armed.
2. `PLAN.md`'s gate 3 `work_units` list contains at least one entry at `status: draft`
   **before** the `FEAT-2026-0040/G3-CLOSE` entry, which remains the terminal entry.
3. Every drafted gate-3 WU file exists, is `status: draft`, and carries the five
   mandatory body sections.
4. A drafted WU covers the fingerprint-keyed issue lifecycle against
   `escalation.py`'s existing machinery, and its body names the 0046 duplicate-filing
   weakness and how the WU addresses it.
5. A drafted WU covers the `specfuse-monitor run` CLI, and one covers the local and
   GitHub Actions runner surfaces.
5a. A drafted WU covers the `queue-stalled` adapter, extending `T05`'s
   `BrokerAdapter` rather than the telemetry adapters, per the operator decision
   recorded in `GATE-02-REVIEW.md` §6.1. Its body states that the check reads broker
   coordinates (queue depth, age-of-oldest) and names the threshold-units gap in the
   schema as something to settle or explicitly defer — not to leave implicit.
6. Each drafted WU whose verification depends on the real `gh` surface is explicitly
   marked as producing no in-loop evidence, with either an operator-journal proxy or a
   stubbed-runner scope plus a named deferred criterion.
7. `WU-90-gate-3-close.md` is rewritten against gate 3's actual contents, its
   `depends_on` updated, and its body instructs naming `gate 1` in
   `## What the loop did NOT verify` for the auto-close-debt reconciliation.
8. `GATE-03-REVIEW.md` records the arming-discipline assessment for gate 3:
   `planning-discipline.md` §2, §3, and §4 each either answered or marked not
   applicable **with the reason**, not silently omitted.
9. Every drafted WU carries a `planned_cost_usd`, and `GATE-03.md` carries a
   `cost_budget_usd` equal to their sum plus one re-attempt of the largest.
10. `PLAN.md`'s `planned_cost_usd` is re-baselined to include gate 3's drafted units,
    and the delta against the previous figure is stated in `GATE-03-REVIEW.md`.
11. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0040-failure-artifact-harvester`
    exits zero.

**Do not touch.** Source files owned by T01–T07. `RETROSPECTIVE.md` — the previous
unit wrote it; this one reads it. `PLAN.md`'s `status` field: the driver owns the
terminal flip. Gates 1 and 2 — closed. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set, plus criterion 11's lint run over the whole
feature folder. Drafted WUs are prose: their quality is checked by the human at the
arming checkpoint, which is what `GATE-03-REVIEW.md` exists to support — criteria 4–8
are the structural floor, not a substitute for that review.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: gate
2's retrospective reports a finding that invalidates the drafted gate-3 shape — for
example that the artifact stream the adapters produce cannot key an issue without a
field no WU shipped; `escalation.py`'s machinery cannot be reused without a change to
its public shape, which is a cross-feature contract question and not this unit's to
settle; or gate 3 cannot be drafted such that any unit produces in-loop evidence,
which would mean the gate boundary itself was drawn wrong and is worth reporting
before a human arms it.
