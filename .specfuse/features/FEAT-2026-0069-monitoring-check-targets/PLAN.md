---
feature_id: FEAT-2026-0069
title: monitoring.yml check targets + queue-stalled check type
slug: monitoring-check-targets
branch: feat/FEAT-2026-0069-monitoring-check-targets
roadmap_goal: Separate the two axes `monitoring.yml` conflates — component as the unit of deployment and attribution, check target as the unit of failure-artifact enumeration — so a single deployable carrying N queue subscriptions and M schedules can express per-subscription DLQ attribution and per-schedule heartbeat, and so FEAT-2026-0040's adapter interface is built against a contract that already answers "do I enumerate per component or per target."
autonomy_default: review
status: active
planned_cost_usd: 34.00
---

# Plan: monitoring.yml check targets + queue-stalled check type

FEAT-2026-0039 shipped the `monitoring.yml` schema so that FEAT-2026-0040 could be
built against a machine-checkable contract rather than a prose one. The first real-repo
run of `/derive-monitoring` (0039 gate 2's FU-1, against a downstream .NET backend: one
HTTP API plus one functions host carrying 20 queue-topic subscriptions and 10 timer
triggers) found that the contract is wrong in a way a fixture could not have shown —
and found it, as intended, *before* adapters exist. This feature fixes it.

The defect is a conflated axis. `component` is currently asked to be two things at
once: the unit of deployment and attribution (role name, trust dials, redeploy
boundary) **and** the unit of failure-artifact enumeration (what findings are counted
per). Those coincide only when a deployable carries exactly one trigger. On the
observed host they diverge 30-to-2: one `dlq` check covers 20 unrelated subscriptions
with no per-subscription attribution, and one `heartbeat` covers 10 timers, so a single
silent timer among ten is invisible to any config this schema can express.

Making each trigger its own component does not fix it, and the reason is decisive
rather than stylistic: `cloud_RoleName` is **per-process**. All 30 triggers run in one
host reporting one role name, so 30 components would each carry an `error-logs` /
`heartbeat` check that is literally the same query — 30 duplicate findings per
exception — and the design-for-diagnosis property "per-component role name matches
`monitoring.yml` `name`" becomes unsatisfiable by construction. The dials are
deployment-level trust (`autofix: on` means "an agent may fix this and redeploy it",
which is granted to a deployable, not to a queue), and generated triggers churn, so 30
hand-maintained component blocks would drift on every new trigger.

So: **component stays the deployment and attribution unit; checks gain an optional
`targets` list that is the enumeration unit.** A DLQ is not a component — it is a queue
belonging to a subscription that a function inside a component consumes. A timer is not
a component — it is a schedule.

## Scope boundary

**IN — gate 1.** The `targets` axis in the schema and its structural validation
(`specfuse/loop/lint_monitoring.py`), the migration of every shipped surface that
carries a YAML example, the contract flip that makes a target-less `dlq` a finding, and
the `queue-stalled` check type (issue #247) which poses the identical
adapter-enumeration question for a broker coordinate.

**IN — gate 2.** Re-keying component discovery so it keys on *deployment* evidence
(Helm chart, compose service, Dockerfile) and treats trigger registrations as evidence
of a component's **type** rather than as components themselves, plus the fixture whose
single deployable contains N triggers — the shape 0039's gate-2 fixture structurally
could not catch, because its stack had one trigger per deployable.

**OUT — owned by FEAT-2026-0040.** Fingerprinting. This is not optional politeness:
**0040's fingerprint model must include the target key**, or 20 DLQs collapse into one
issue and the attribution this feature pays for is lost at the last step. Recorded here
as a binding constraint on 0040; implemented nowhere in this feature.

**OUT — recorded decisions, deliberately not built.** Three of them, each with its
reason, so a later gate does not relitigate:

- **Per-target dials.** "Autofix this one subscription but not that one" multiplies the
  trust surface and nothing observed motivates it. Dials stay per-component until
  something does.
- **The `environments` × `components` cross-product.** `environments` and `components`
  are independent top-level lists, so the schema asserts every component exists in
  every environment. A project with dev / pre-prod / prod where some component ships
  only to prod cannot say so. Acknowledged as a known limitation; worth settling before
  0040 hardens the adapter contract, but it is a different axis from this one and
  bundling it would double the blast radius of a breaking change.
- **Deployment-regression detection on 4xx status codes (issue #248).** Expressible
  today via `invariant`, which would erode the discrete-artifact model by precedent
  rather than by decision. Verdict: the no-metrics boundary holds; `invariant` is not
  the sanctioned route to rate-based detection. Left as a filed scope question.

**OUT — shipping separately as a bug fix.** Issue #246 (`_ENV_VAR_NAME_RE` rejects the
`Section__Key` env-var spelling). One regex plus tests, and it touches the same file
this feature rewrites — so it lands **before** this feature starts, on its own
`fix/issue-246-*` branch. Reversed order would rebase a bug branch onto a substantially
changed validator, which a dispatched WU cannot resolve.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -rniE "targets|target_key|enumerat" specfuse .specfuse/scripts docs/concepts
    -> 0 real hits (every hit is a Python `enumerate()` builtin)
grep -rniE "schema_version|apiVersion|^version:" .specfuse/monitoring.yml.example \
    .specfuse/verification.yml specfuse/loop/lint_monitoring.py
    -> 0 hits (no schema version marker exists anywhere)
grep -rn "fingerprint_by" specfuse docs .specfuse
    -> the precedent, see below
```

**Verdict: no existing mechanism, building new — but one pattern is reused, not
rebuilt.** `fingerprint_by` on `invariant` checks is already exactly this shape: a
per-check keying field that the validator requires structurally and never interprets,
consumed downstream by 0040's fingerprint model (`lint_monitoring.py:214`,
`docs/concepts/monitoring-schema.md:84`). `targets` is its generalization, not a new
concept. A WU must not invent a parallel mechanism.

Two further findings from the pre-flight, both load-bearing on the gate cut:

- **`_miniyaml` needs no changes.** Probed at draft time against the exact nesting this
  feature introduces — a list-of-mappings under a key of a list item, including a
  quoted cron expression — and it parses correctly. No parser WU, and no WU should
  budget for one. This matters because `_miniyaml` is load-bearing for PLAN, GATE, WU,
  and `verification.yml` in every downstream project.
- **Two hard test couplings constrain WU shape** (enumerated per §10; see the Notes).

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature flips a permissive schema position to a blocking one: a target-less `dlq`
check validates clean today and becomes a finding at T03. So the question applies.

**What does the rule report on an input already in its intended final state? Zero — but
only because T02 runs before T03.** That ordering is the whole design of gate 1 and is
not a convenience:

- The shipped `.specfuse/monitoring.yml.example` currently carries a target-less `dlq`
  check, and this repo's own `monitoring-example-lint` gate validates that file. Flip
  the validator first and the gate is red on a correct tree — an unsatisfiable
  predicate, and per FEAT-2026-0051's preflight baseline probe a red base gate halts
  before any WU dispatches at all.
- The same applies to `tests/test_monitoring_fenced_blocks.py`, which extracts every
  ```yaml block from five declared surfaces and runs each through the validator.

Hence expand → migrate → contract: T01 accepts `targets` and requires them nowhere
(purely additive, everything stays green), T02 migrates every shipped surface to carry
them, T03 flips the requirement once nothing target-less remains. Each intermediate
state is green, which is the property the driver needs since it squashes every WU with
all gates required to pass.

**No live consumer needs migrating.** Confirmed with the operator at drafting: the only
`monitoring.yml` ever drafted against this schema is the FU-1 output, and it is
uncommitted. So there is no migration WU — but T03's finding message must still name
the fix inline, because there is no migration document for an operator to fall back on.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0069/T01
        file: WU-01-check-targets-validator.md
        depends_on: []
      - id: FEAT-2026-0069/T02
        file: WU-02-migrate-shipped-surfaces.md
        depends_on: [FEAT-2026-0069/T01]
      # Hygiene WU inserted after T03 blocked on `spinning_signature_repeat`:
      # T02's ACs tested "add a component with targets" rather than "migrate
      # every surface", so three pre-existing target-less `dlq` checks survived
      # and T03's contract flip inherited a non-conforming tree. T03H fixes
      # those and adds the tree-wide criterion T02 lacked. See its Context for
      # the escalation event.
      - id: FEAT-2026-0069/T03H
        file: WU-03H-dlq-targets-in-remaining-surfaces.md
        depends_on: [FEAT-2026-0069/T02]
      - id: FEAT-2026-0069/T03
        file: WU-03-dlq-targets-required.md
        depends_on: [FEAT-2026-0069/T03H]
      - id: FEAT-2026-0069/T04
        file: WU-04-queue-stalled-check-type.md
        depends_on: [FEAT-2026-0069/T03]
      # --- non-terminal gate: close-intermediate then plan-next ---
      - id: FEAT-2026-0069/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0069/T01
          - FEAT-2026-0069/T02
          - FEAT-2026-0069/T03H
          - FEAT-2026-0069/T03
          - FEAT-2026-0069/T04
      - id: FEAT-2026-0069/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]

  - gate: 2
    file: GATE-02.md
    work_units:
      # Drafted by G1-PLAN against the shape gate 1 actually emitted, not the
      # shape the sketch predicted. All four ship `status: draft` (unarmed);
      # the human flips them at the gate-1 review-and-arm checkpoint after
      # reading GATE-02-REVIEW.md.
      #
      # T05 is independent of the re-key: it decides the `invariant` x
      # `targets` fall-through gate 1 shipped by accident and corrects the
      # stale `_check_targets` docstring, both routed here by gate 1's
      # retrospective. T06 -> T07 -> T08 is a strict chain: keying, then the
      # N-trigger fixture that proves the keying, then the prose that
      # describes it.
      - id: FEAT-2026-0069/T05
        file: WU-05-invariant-targets-position.md
        depends_on: []
      - id: FEAT-2026-0069/T06
        file: WU-06-rekey-discovery-on-deployment-evidence.md
        depends_on: []
      - id: FEAT-2026-0069/T07
        file: WU-07-n-trigger-fixture-and-target-generation.md
        depends_on: [FEAT-2026-0069/T06]
      - id: FEAT-2026-0069/T08
        file: WU-08-skill-method-prose.md
        depends_on: [FEAT-2026-0069/T07]
      # --- terminal gate: single close, no plan-next ---
      - id: FEAT-2026-0069/G2-CLOSE
        file: WU-92-gate-2-close.md
        depends_on:
          - FEAT-2026-0069/T05
          - FEAT-2026-0069/T06
          - FEAT-2026-0069/T07
          - FEAT-2026-0069/T08
```

## Gate 2 sketch (for `plan-next`, not binding)

Gate 1's `plan-next` refines this against the shape gate 1 actually emits. Definition
of done: `/derive-monitoring`, run against a repo whose single deployable carries N
triggers, emits **1 component with N targets** — not N components.

- **Re-key `discover_components`.** Today an evidence matcher keyed on trigger
  attributes returns one component per trigger; on the observed host that is 30
  components where the correct answer is 2. The right key is *deployment* evidence
  (Helm chart, compose service, Dockerfile) with trigger registrations demoted to
  evidence of a component's `type`. This is a change to the `patterns` table contract,
  not just to a pattern table — treat it as such.
- **A fixture whose one deployable carries N triggers.** The common shape for any
  functions host, worker pool, or consumer group. 0039's Stack A fixture has one
  trigger per deployable and therefore could not express the bug; that is why this
  fixture is a deliverable and not an afterthought.
- **Mechanical target-list generation.** The issue reports all target coordinates as
  extractable without asking the operator anything — subscription names from the
  trigger attribute, function names from the `[Function(nameof(...))]` form, cron and
  IANA timezone from named constants on the timer classes — so discovery can generate
  the lists and regenerate them as triggers are added. **This claim is confirmed only
  against a repo outside this tree.** Gate 2 must not treat a fixture it authors as
  evidence for it; see the close obligation.
- **Skill method prose.** `derive-monitoring`'s Step 1 and Step 4 currently describe
  component discovery with no target concept. Canonical copy in
  `plugins/specfuse/skills/`, propagated by `scripts/sync-scaffold.sh`.

## Notes

- **Multi-gate (8 planned substantive WUs > 4)** — full ceremony per
  `docs/methodology.md §6`. Gate 1 is non-terminal (`close-intermediate` +
  `plan-next`); gate 2 pre-declares its terminal `close`.
- **§10 pre-flight: two hard test couplings, both dictating WU shape.** Enumerated at
  draft time so no WU rediscovers them at dispatch cost:
  1. `tests/test_monitoring_example.py:59` asserts the shipped example exercises
     **every** member of `CHECK_TYPES`, and `:94` asserts the docs table documents
     every member. Adding `queue-stalled` to the enum turns both red instantly — so
     T04 ships enum + example block + docs row atomically and cannot be split.
  2. `suggest_checks()` (`tests/test_derive_monitoring_discovery.py:102`) emits a
     target-less `{"type": "dlq", "harvest_mode": "peek"}`; `render_monitoring_yml()`
     renders each check's own keys at one indent level; `TestDiscoveredConfigPassesLint`
     (`:332`) runs that render through `validate_monitoring` and asserts zero findings.
     T03's contract flip turns that test red, and the renderer cannot emit a nested
     list-of-mappings at all. So T03 carries the **minimal** reference-impl change (a
     neutral `subscriptions` field on the record, one target per known subscription,
     nested rendering) while the actual re-keying stays in gate 2. This is a real
     cross-gate coupling, deliberately bounded rather than overlooked.
- **The axis distinction is the thing to protect.** Two coordinates per DLQ target are
  deliberate: `subscription` is what the harvester queries, `function` is what a human
  diagnoses by. A WU that collapses them to one has broken the feature's point even if
  every gate passes.
- **`error-logs` and `http-5xx` stay target-less by construction**, and the validator
  rejects targets on them. They are role-name keyed and therefore genuinely
  component-scoped; permitting targets there would reintroduce the duplicate-findings
  problem this feature exists to remove.
- **Neutrality is a blocking constraint, not a preference.** `subscription`, `function`,
  `cron`, `timezone`, and whatever names the `queue-stalled` threshold must be as
  vendor-neutral as `dlq` already is. T01 and T04 escalate rather than special-case one
  provider, because that boundary is what makes 0040's adapter interface possible.
- **Secrets posture is unchanged and still structural.** Every example uses obvious
  placeholders (`acme-*`, `Etc/UTC`); credentials remain environment-variable names
  only. `.specfuse/rules/security-boundaries.md` and the `leak-scan` gate both bite on
  this surface, and `leak-scan`'s pre-commit form is stricter than its CI form.
- **Cost note.** `planned_cost_usd` totals $34: gate 1 at $21 (T01 $3.00, T02 $2.50,
  T03 $3.00, T04 $2.50, two planning WUs at the $5.00 floor from
  `planning-discipline.md` §5), gate 2 sketched at ~$13.
- **Expected lint WARN until gate 1 closes.** `lint_plan.py` compares this
  feature-level $34 against the sum of *existing* WU `planned_cost_usd` values ($26 —
  gate 1's $21 plus the `G2-CLOSE` placeholder's $5) and warns at a 24% delta. The gap is structural, not an estimating error: gate 2's
  substantive WUs do not exist until `G1-PLAN` drafts them, and the sum converges once
  it does. The figure is left honest rather than trimmed to silence the warning,
  because the terminal close reconciles actual spend against it and an understated plan
  would make gate 2's real cost read as an overrun. 0039 carried the same warning for
  the same reason.
- **The convergence prediction above was wrong, and is left standing rather than
  rewritten.** `G1-PLAN` drafted gate 2's four substantive WUs at $12.00, taking the WU
  sum from $28.00 to $40.00 — so the delta did not close, it crossed zero and reopened
  on the other side (now ~18% *over* the $34.00 feature figure). Neither number is
  adjusted here: `WU-91`'s AC9 requires the discrepancy be reported rather than
  silently reconciled, and the reasoning is in `GATE-02-REVIEW.md` § *Cost
  reconciliation*. The short version is that $34.00 was drafted before gate 1 revealed
  a mid-gate hygiene WU, a four-attempt WU, and a two-attempt close — all real spend the
  original figure had no way to carry. The terminal close reconciles actuals against
  both figures.
</content>
</invoke>
