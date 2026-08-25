---
feature_id: FEAT-2026-0052
title: Baseline-delta ratchet, waiver, and tracking-issue emission
slug: baseline-delta-ratchet
branch: feat/FEAT-2026-0052-baseline-delta-ratchet
roadmap_goal: Give an operator facing a red baseline a third exit — proceed with the recorded failures held constant, every newly-introduced failure still blocking, and the waived debt filed as a tracked issue — instead of FEAT-2026-0051's only two, fix the repo-wide debt first or defer the feature.
autonomy_default: review
status: planned
planned_cost_usd: 25.00
---

# Plan: Baseline-delta ratchet, waiver, and tracking-issue emission

[FEAT-2026-0051](../FEAT-2026-0051-preflight-baseline-gate-probe/PLAN.md) stops
the bleeding: a `code` gate already red on the base tree halts at gate entry with
`preexisting_gate_failure`, having dispatched zero work units, and records the
failing set into the gate file's `baseline:` frontmatter. It shipped `met`, and
its halt message ends with a sentence this feature exists to delete:

> There is no way to proceed past this halt in this version. A waiver that lets a
> feature continue against a red baseline is future work tracked as
> FEAT-2026-0052; it does not exist yet.

The two exits 0051 offers — fix the debt on the integration branch, or defer the
feature — are both wrong when the debt is real, externally caused, and slow to
resolve: an unpatched transitive advisory with no upstream fix. The feature is
then held hostage by a failure it did not cause and cannot repair. The missing
third exit is "proceed, with everything the baseline already had held constant
and everything new still enforced."

Three additions on top of 0051's recorded baseline: the **ratchet** (a WU fails
only on failures beyond the baseline set), the **waiver** (an operator decision
that activates the ratchet for one gate, survives resume, and is durable on
disk), and **tracking-issue emission** (a waived baseline is always recorded on
GitHub, never silently accepted).

## Scope boundary

**IN.** The baseline-delta subtraction at the outcome layer; the
`--waive-baseline` flag and the `waiver:` gate-frontmatter block it writes; the
sha-and-set pinning that keeps a waiver from covering failures it never saw; the
`waived-baseline` label and the tracking issue filed against it; and the operator
message changes on both the halt path (offer the third exit) and the proceed path
(name the issue).

**OUT, deliberately.**

- **A per-gate mute.** Issue #234 rejected an `--ignore-security`-style flag
  because it also suppresses a genuine vulnerability a WU legitimately
  introduces. Subtracting a *recorded set* is not muting a gate: a new failure in
  a waived gate still fails. This distinction is the whole design, and D3 below
  is what enforces it.
- **Project-wide or cross-feature waivers.** A waiver is scoped to one gate of
  one feature at one sha. "Waive `dependency-audit` everywhere until upstream
  patches" is a different and much larger shape (it needs expiry, ownership, and
  a review cadence) and is not this feature.
- **Waiver expiry.** Deliberately absent in v1. The pinning in D3 already forces
  a re-decision whenever the failing set changes, which is the case expiry would
  mostly cover.
- **The `doc` and `plannext` gate sets.** 0051 probes only `code`, for the reason
  it recorded — those sets are driver-internal and have no externally-fed-oracle
  exposure. The ratchet inherits that boundary rather than widening it.
- **0051's `no_gate_marker` message defect** (its follow-up 1: render plain
  English when `_is_noninformative_signature()` is true). Real, but it is 0051's
  own follow-up on a line this feature does not otherwise touch; fixing it here
  would hide it inside an unrelated diff.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -rniE "ratchet|waiver|waive" specfuse/loop/ --include='*.py'
  -> 2 hits, both PROSE inside loop.py's halt message
     (lines 3876, 3970 — "the waiver ... does not exist yet")

grep -rn "emit_escalation" specfuse/
  -> specfuse/loop/escalation.py  (definition + helpers)
     specfuse/agent/run.py:293    (the only caller)

grep -rn "baseline" specfuse/loop/loop.py
  -> probe_baseline, read_gate_baseline, write_gate_baseline,
     gate_baseline_check, baseline_probe_enabled,
     format_preexisting_gate_failure, baseline_evidence_diffstat
     (all FEAT-2026-0051)

grep -rn "LABEL_REGISTRY|def provision_labels" specfuse/loop/*.py
  -> specfuse/loop/labels.py:31, :192
```

**Verdict, per piece — two of three reuse, one builds new.**

- **Ratchet: no existing mechanism, building new.** Nothing subtracts a recorded
  failure set from a live one. The nearest relative, `coverage --fail-under=90`
  in `.specfuse/verification.yml`, is a *static floor* rather than a delta
  against a measured baseline — the same rejection 0051 recorded for the same
  reason.
- **Tracking-issue emission: found `specfuse/loop/escalation.py`, reusing.** Its
  `emit_escalation` docstring states the property this feature needs:
  *"Idempotent: searches for an open issue carrying the ``needs-human`` label and
  this correlation ID's marker before creating; a second call for the same
  ``correlation_id`` returns the existing issue's identifier instead of filing a
  duplicate."* Also already handled there and not to be rebuilt: the
  assignee-omission fix (#1762), the non-raising `check=False` posture (#2170),
  and `CREATED_NUMBER_UNKNOWN` for a created-but-unparseable result. **Building
  a thin sibling rather than extending it** — see D4; the reason is the label,
  not the mechanics.
- **Label provisioning: found `specfuse/loop/labels.py`, reusing.**
  `provision_labels` creates every `LABEL_REGISTRY` label the repo is missing, so
  a new spec is a registry entry, not new code.
- **Comparability of the two failure sets: already built, free.**
  `parse_gate_failure_signature` produces `(failure_class, failure_signature)`
  for both a baseline entry and a live WU failure. FEAT-2026-0051/T01's WU said
  so explicitly — *"a baseline signature is directly comparable to a WU failure
  signature (which is what FEAT-2026-0052's ratchet will need)"*. The delta is a
  set comparison over an existing key, not a new parser.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature does not raise a severity — it *lowers* one, conditionally, which is
the mirror image and needs the same question answered in the opposite direction:

> **What does a WU report when the tree is in its intended final state and no
> waiver exists?**

**Byte-identical to today.** With no `waiver:` block present, the subtraction
never runs, `execute_unit_attempt` classifies exactly as it does now, and
`verify()` is untouched on every path. T01's acceptance carries a
no-waiver-present test asserting this directly.

And the question this feature's own risk actually turns on:

> **What does a waived WU report when it introduces a genuinely new failure?**

**It fails.** The waiver subtracts only the entries recorded in the baseline; a
failure whose `(gate, failure_class, failure_signature)` is not in that set is
untouched by the ratchet. This is the property that separates the design from
the mute #234 rejected, and it is T01's red test, not a claim in prose.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0052/T01
        file: WU-01-baseline-delta-ratchet.md
        depends_on: []
      - id: FEAT-2026-0052/T02
        file: WU-02-waiver-flag-persistence.md
        depends_on: [FEAT-2026-0052/T01]
      - id: FEAT-2026-0052/T03
        file: WU-03-tracking-issue-emission.md
        depends_on: [FEAT-2026-0052/T02]
      - id: FEAT-2026-0052/T04
        file: WU-04-operator-message.md
        depends_on: [FEAT-2026-0052/T03]
      # --- terminal gate: single close WU ---
      - id: FEAT-2026-0052/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0052/T01
          - FEAT-2026-0052/T02
          - FEAT-2026-0052/T03
          - FEAT-2026-0052/T04
```

## Notes

- **Single-gate feature** (4 substantive WUs ≤ 4): one terminal `close`, no
  `close-intermediate` and no `plan-next` — ceremony proportionality,
  `docs/methodology.md §6`. Same shape 0051 used.
- **The ratchet does not touch `verify()`.** It subtracts at
  `execute_unit_attempt` (`loop.py:4068`), where the driver already turns a gate
  report into `passed` / `failed` / `files_changed_mismatch`. `verify()`'s
  `(ok, report)` is every WU's exit oracle in every downstream project — the
  `[FEAT-2026-0019/G1]` hazard — and 0051/T01 was explicitly told to block rather
  than change it. Reversing that inside its own successor feature needs a
  stronger reason than convenience. The subtraction at the outcome layer also
  keeps the raw FAIL truthful in the report the agent reads and in
  `events.jsonl`, so a waived failure records as failed-and-waived rather than as
  a bare `PASS` that is indistinguishable from a real one a year later.
- **A waiver is pinned to the baseline it waives** (sha + the exact failing set).
  A failure appearing later is not covered and the gate halts again. Without the
  pin, a waiver granted for advisory X silently swallows advisory Y next week —
  which is the mute #234 rejected, wearing a different hat.
- **The tracking issue is not a `needs-human` escalation.** A waived baseline
  parks nothing; the run proceeds. Filing it under `needs-human` would put a
  running feature into `/attention`'s blocked-work inbox and misreport it as
  stalled. Hence a distinct `waived-baseline` label — see T03.
- **Self-hosting: this takes effect on the *next* driver invocation, not
  mid-run.** Python loads `loop.py` once at process start. 0051's PLAN predicted
  its own probe would run against its own remaining WUs; its retrospective proved
  that wrong and recorded the correction (*"Self-hosting notes should reason
  about process start, not file mtime"*). Stated here in the accurate — and
  smaller — form rather than repeating the error.
- **T02, T03 and T04 all edit the message site T01 touches**, so the chain is
  serialized rather than parallel. Same reason 0051 serialized T01→T02→T03, which
  produced no merge friction.
- **"Visible in the gate review" from the roadmap is unsatisfiable as literally
  written for a single-gate feature.** `_precreate_gate_review_stub`
  (`loop.py:3007`) no-ops when there is no next gate, so no `GATE-02-REVIEW.md`
  exists here. Resolved as three surfaces that do exist: the `waiver:` block in
  `GATE-01.md`, the proceed-path console message (T04), and the close record.
- Probe cost is **not** re-derived by this feature. 0051 measured it at 118.3s
  against this repo's `code` set, 92.6% of it `tests` + `coverage` running the
  same 1327 tests twice, 0s on resume, zero model tokens. Its retrospective asked
  that 0052 size the ratchet against that number rather than measure it again.
  The ratchet adds no gate runs at all — it compares two sets that already exist.
