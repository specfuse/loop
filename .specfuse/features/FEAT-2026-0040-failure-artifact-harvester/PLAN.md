---
feature_id: FEAT-2026-0040
title: Failure-artifact harvester CLI — detect and report
slug: failure-artifact-harvester
branch: feat/FEAT-2026-0040-failure-artifact-harvester
roadmap_goal: Turn a component's functional failures — dead-lettered messages, error logs, 5xx traces, missed timer runs, invariant violations — into deduplicated GitHub issues within a polling cycle, deterministically and without an LLM, so autonomy level 1 is live end to end.
autonomy_default: review
status: done
planned_cost_usd: 70.00
---

# Plan: Failure-artifact harvester CLI

Detection must be deterministic, cheap, and LLM-free: enumerate discrete failure
artifacts and report them as deduplicated GitHub issues. Laser focus on component
misbehaviour — not metrics, not infrastructure. A poison message becomes one
evidence-rich issue within a polling cycle, deduplicated across thousands of
occurrences, feeding the existing triage loop.

This is the keystone of the monitoring initiative. [FEAT-2026-0038](../../roadmap.md),
[0041](../../roadmap.md), [0042](../../roadmap.md) and [0043](../../roadmap.md) are
all blocked on it. The contract it builds against is settled and machine-checkable:
[FEAT-2026-0039](../../roadmap.md) shipped the schema, [FEAT-2026-0069](../../roadmap.md)
added the `targets` enumeration axis, and both are `done` and released.

## The binding constraint, inherited and not negotiable

**Fingerprints must include the target key.** Enumeration runs over
`check["targets"]` when present and over the component otherwise, and a finding
derived from a target must fingerprint on that target's coordinates —
`subscription` + `function` for `dlq`, `name` for `heartbeat` — not only the
component name. `invariant` is the deliberate exception: 0069 *rejected* `targets`
there so that `fingerprint_by` remains its single enumeration key and this feature
is never handed two competing keys.

Without this, 20 DLQ targets collapse into one issue with every gate green, and the
per-subscription attribution 0069 paid two gates for is destroyed at the last step.
0069's terminal close restates it as its own closing obligation; it is this
feature's to honour. `T02` is where it lands.

## Decisions taken at drafting

**Telemetry resolves per component, through a seam** ([#262](https://github.com/specfuse/loop/issues/262)).
`environments.<name>.telemetry` is one binding per environment, so every component
in an environment resolves to the same sink. That is correct for the motivating
project and wrong in general — the operator's own words on the issue: *"for other
projects, each component may have a different App Insights instance."* The issue
names the cost precisely: *"If per-component bindings arrive after adapters exist,
the adapter interface changes rather than extends."*

So the adapter interface resolves telemetry **for a component**, through
`resolve_telemetry(component, environment)`, whose only implementation today reads
the environment binding. No schema change, no migration, no third consumer-visible
break in three releases — and when per-component bindings land they add a resolver
implementation rather than reshaping every adapter. Deliberately chosen over
changing the schema now, which was rejected as too expensive so soon after 0.6.0,
and over resolving from the environment directly, which is the shape #262 warns
about.

**The cron dialect is declared, never inferred.** A heartbeat check computing
"should this have fired?" cannot tell a 5-field expression (standard) from a
6-field one (seconds-first: Azure Functions NCRONTAB, which is what the motivating
project's timer triggers use). Inference by field count was considered and
**rejected by the operator**: it degrades silently exactly when a new dialect
arrives, which is the worst moment. Instead, heartbeat targets declare their
dialect explicitly and the validator enforces both the enum and the expression's
arity against it, so a mismatch is a validation error rather than a wrong verdict
at 3am.

This **widens a position 0069 recorded deliberately**: its T01 left target
coordinate *contents* opaque — `cron` and `timezone` unvalidated strings, exactly
as `invariant.query` is. Checking arity against a declared dialect crosses that
line knowingly. Migration is cheap because `derive-monitoring` generates these
targets from discovered trigger registrations and therefore already knows the
dialect. This lands in **gate 2**, not gate 1: it is schema work, the heartbeat
adapter is what consumes it, and keeping it out of gate 1 is what lets the artifact
model stay genuinely neutral.

**The GitHub issue surface gets its own gate.**
`[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]` is explicit that `gh` returns auth errors
inside `claude -p`, so a work unit touching the real issue surface produces **zero
in-loop evidence**, and mixing it with in-loop-verifiable work inflates a gate's
deferred list past the sizing threshold while conflating "deferred but post-state
verified" with "the loop never saw it." FEAT-2026-0046 hit this exactly. Gates 1
and 2 are therefore fully in-loop against stubbed transports and should close with
genuinely empty deferred lists; gate 3 owns the surface that cannot self-verify,
where a hedged close is expected rather than a sizing failure.

## Scope boundary

**IN.** The neutral artifact model and provider-adapter interface; fingerprinting
including the target key; redaction; the Azure adapter pair (Service Bus DLQ peek,
App Insights KQL); the cron-dialect contract; issue lifecycle with fingerprint
dedupe; the `specfuse-monitor run` CLI; local and GitHub Actions runner surfaces.
All environment access read-only.

**OUT, each with a home.** DLQ quarantine harvesting is
[FEAT-2026-0038](../../roadmap.md); root-cause diagnosis of findings is
[FEAT-2026-0041](../../roadmap.md); autofix is
[FEAT-2026-0042](../../roadmap.md); the in-cluster CronJob runner is
[FEAT-2026-0043](../../roadmap.md). Per-component *dials* beyond what the schema
already carries stay out — 0069 recorded that decision.

**OUT by deliberate design: quiet-based auto-close.** The roadmap's own words —
findings may be annotated "quiet for N runs — candidate for close", but humans
close. No exception.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

Two searches, two different verdicts.

**Issue lifecycle — `found, reusing`.**
- **Command:** `grep -n "^def \|marker" specfuse/loop/escalation.py`
- **Verdict:** FEAT-2026-0046 shipped `_correlation_marker`, `_find_existing_issue`
  (search by label plus an HTML-comment marker, then re-check `marker in body`),
  `_default_runner`, `_extract_issue_number`, and idempotent find-then-create. The
  harvester's issue lifecycle is the same shape with a fingerprint in place of a
  correlation ID. **Gate 3 reuses that machinery rather than building a parallel
  one**, and inherits its known weakness: 0046's own retrospective records that
  GitHub's search index does not reliably tokenise HTML-comment content, so a
  search returning nothing silently files a duplicate. Gate 3 must address that
  rather than adopt it unexamined.

**Redaction — `found, NOT reusable; building new`.**
- **Commands:** `grep -rn "def redact" specfuse/loop/*.py .specfuse/scripts/*.py`
  and `find specfuse/loop/data -name 'leak_*'`
- **Verdict:** `redact_leak_findings` exists at `loop.py:2097`, but it is
  marker-gated — it returns *text* unchanged unless the string `"leak-scan"`
  appears — and it redacts the quoted match inside a leak-scan FINDINGS block. On
  arbitrary artifact text (an exception message, a dead-lettered message body) it
  is a no-op. Wrong threat model.

  More decisively: the pattern source `leak_scan.py` exists **only** under
  `.specfuse/scripts/` and is absent from `specfuse/loop/data/`, because it is
  specfuse-internal tooling that deliberately does not ship to scaffolded projects
  (issue #55). **The harvester runs in consumer repositories, where that file does
  not exist.** Importing it would produce a harvester that works here and crashes
  everywhere else.

  So T03 builds its own, reusing one thing: the `<redacted:sha8>` convention, which
  keeps a stable hash so the same secret is correlatable across occurrences without
  the live value surviving. That property is exactly what a deduplicating harvester
  needs.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero — for every check this gate introduces.

Gate 1 introduces no severity flip and no blocking check over existing repository
state. Its assertions are over new modules only: the core carries no
provider-specific identifier, distinct targets produce distinct fingerprints, and a
planted secret does not survive the artifact boundary. Each reports zero on a
correct tree by construction, because the tree does not contain the modules until
this gate writes them. **Gate 2's validator change is a different matter** and must
answer this section again when `plan-next` drafts it: tightening heartbeat-target
validation is a severity flip, and the migrate-before-contract ordering
`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` established is mandatory there.

**Answered for gate 2** by `G1-PLAN`, in `GATE-02.md`'s arming section: `dialect` is
required only on a heartbeat target that *carries a `cron`*, so a correct tree — one
where every cron-carrying target declares a conforming dialect, which T04's migrate
step establishes before its contract step — reports **zero**. The predicate is
satisfiable, and the migrate criterion is a sweep rather than a sample precisely so
"zero on a correct input" is a fact rather than a hope.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0040/T01
        file: WU-01-artifact-model-adapter-protocol.md
        depends_on: []
      - id: FEAT-2026-0040/T02
        file: WU-02-fingerprinting.md
        depends_on: [FEAT-2026-0040/T01]
      - id: FEAT-2026-0040/T03
        file: WU-03-redaction.md
        depends_on: [FEAT-2026-0040/T01]
      # --- closing sequence: non-terminal gate ---
      - id: FEAT-2026-0040/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0040/T01
          - FEAT-2026-0040/T02
          - FEAT-2026-0040/T03
      - id: FEAT-2026-0040/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0040/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0040/T04
        file: WU-04-cron-dialect-contract.md
        depends_on: []
      - id: FEAT-2026-0040/T05
        file: WU-05-service-bus-dlq-peek-adapter.md
        depends_on: []
      - id: FEAT-2026-0040/T06
        file: WU-06-app-insights-telemetry-adapters.md
        depends_on: []
      - id: FEAT-2026-0040/T07
        file: WU-07-heartbeat-adapter-declared-dialect.md
        depends_on:
          - FEAT-2026-0040/T04
          - FEAT-2026-0040/T06
      # --- closing sequence: non-terminal gate ---
      - id: FEAT-2026-0040/G2-CLOSE-INTERMEDIATE
        file: WU-90-gate-2-close-intermediate.md
        depends_on:
          - FEAT-2026-0040/T04
          - FEAT-2026-0040/T05
          - FEAT-2026-0040/T06
          - FEAT-2026-0040/T07
      - id: FEAT-2026-0040/G2-PLAN
        file: WU-91-gate-2-plan-next.md
        depends_on: [FEAT-2026-0040/G2-CLOSE-INTERMEDIATE]
  - gate: 3
    file: GATE-03.md
    work_units:
      - id: FEAT-2026-0040/T08
        file: WU-08-queue-stalled-broker-adapter.md
        depends_on: []
      - id: FEAT-2026-0040/T09
        file: WU-09-fingerprint-keyed-issue-lifecycle.md
        depends_on: []
      - id: FEAT-2026-0040/T10
        file: WU-10-specfuse-monitor-run-cli.md
        depends_on:
          - FEAT-2026-0040/T08
          - FEAT-2026-0040/T09
      - id: FEAT-2026-0040/T11
        file: WU-11-runner-surfaces-local-and-actions.md
        depends_on: [FEAT-2026-0040/T10]
      # --- closing sequence: terminal gate ---
      - id: FEAT-2026-0040/G3-CLOSE
        file: WU-90-gate-3-close.md
        depends_on:
          - FEAT-2026-0040/T08
          - FEAT-2026-0040/T09
          - FEAT-2026-0040/T10
          - FEAT-2026-0040/T11
```

T02 and T03 both depend only on T01 and are independent of each other: fingerprints
and redaction are separate properties of the same artifact.

## Notes

- `planned_cost_usd` covers the **drafted** work only. Re-baselined by `G1-PLAN` from
  $25.00 (gate 1's five units plus gate 3's close placeholder) to **$52.00**, adding
  gate 2's six drafted units at $27.00; re-baselined again by `G2-PLAN` to **$70.00**,
  adding gate 3's four substantive units at $18.00 (`T08` $4.00, `T09` $5.00,
  `T10` $5.00, `T11` $4.00 — `G3-CLOSE`'s $5.00 was already in the $52.00 figure).
  Every gate is now drafted, so this figure does not rise again. The delta and its
  reasoning are in `GATE-03-REVIEW.md` §5.
- This repo cannot be the oracle for the adapters. `verification.yml` records that
  it "is a CLI tool with no deployable components and will never carry a real
  monitoring.yml." Proving the Service Bus and App Insights adapters needs an
  operator run against the downstream .NET backend — the same oracle 0069 used to
  discharge FU-1 and FU-3. Gate 2's close must name that explicitly rather than
  claiming what a stub proved.
- `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`: a gate's definition of done must be
  decidable **by that gate**. No gate here asserts a property of 0041, 0042, or the
  downstream project.
