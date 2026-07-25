---
feature_id: FEAT-2026-0051
title: Pre-flight baseline gate probe + preexisting_gate_failure halt
slug: preflight-baseline-gate-probe
branch: feat/FEAT-2026-0051-preflight-baseline-gate-probe
roadmap_goal: Probe the gate set once at gate entry so a gate already red on the base tree halts with preexisting_gate_failure having dispatched zero work units, instead of every WU inheriting the red gate as its exit oracle and spinning its full attempt budget against a failure no WU caused.
autonomy_default: review
status: done
planned_cost_usd: 21.00
---

# Plan: Pre-flight baseline gate probe

A `code`-set gate that is already red on the feature's base tree becomes every
work unit's exit oracle. Each WU then spins to `spinning_signature_repeat` /
`spinning_detected` against a failure it did not cause and — for a WU whose
footprint is a zero-dependency file or a config-only change — could not possibly
fix. A live downstream run burned roughly $8 across two WUs this way, on a
dependency-audit advisory published after the base tree was last green, with the
lockfile byte-identical to the integration branch.

This is the time-varying-oracle failure mode LEARNINGS already records
(`[FEAT-2026-0007/G1-CLOSE]`: never make a tool's own report the acceptance
oracle). Dependency audits are the canonical case — their verdict changes when
an advisory database updates, with no code change — but it generalizes to any
externally-fed gate: a linter release adding a rule, a compiler version bump, a
license scanner, an environment-flaky test.

The fix is a brake, not a mute: run the gate set **once** at gate entry, before
the first WU is dispatched. If it is already red, halt. One gate-set run
replaces a full attempt budget burned per WU.

## Scope boundary

**IN.** The probe, the `preexisting_gate_failure` pre-dispatch halt, the
baseline record in the gate file, the re-probe policy, the kill-switch, and the
plain-English escalation message with its base-vs-head evidence payload.

**OUT — deferred to FEAT-2026-0052.** The baseline-delta ratchet (a WU failing
only on failures *beyond* the recorded baseline), the waiver that lets a feature
proceed against a red baseline, and tracking-issue emission via `gh`. Split
deliberately: the ratchet rewrites the pass/fail semantics of `verify()`, which
is the driver's own exit oracle for every WU in every downstream project — the
`[FEAT-2026-0019/G1]` hazard — and the `gh` surface produces zero in-loop
evidence per `[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]`. Landing the brake first
means 0052 gets designed against real baseline data instead of blind.

**Consequence to state plainly, not paper over:** v1 has no "proceed anyway"
path. An operator facing a red baseline can fix the debt on the integration
branch or defer the feature. The escalation message says exactly that.

**The kill-switch is not the mute flag the issue rejected.** Issue #234
explicitly rules out a per-gate `--ignore-security`-style mute, because it would
also suppress a genuine vulnerability a WU legitimately introduces.
`--no-baseline-probe` disables the **probe**, returning the driver to its
current behavior. It weakens no gate and suppresses no verdict. Recorded here so
a later reader does not delete it as the thing #234 forbade.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -rn "baseline" specfuse/loop/*.py          -> 0 hits
grep -rniE "ratchet|delta" specfuse/loop/*.py   -> lint_plan.py cost-delta WARN only
```

**Verdict: no existing mechanism, building new.** Nothing in the driver probes,
records, or compares a pre-existing failure set. The nearest relatives were read
and rejected as the wrong shape:

- `coverage --fail-under=90` (`.specfuse/verification.yml`) is a *static floor*,
  not a delta against a measured baseline.
- `lint_plan.py`'s cost-delta WARN (`lint_plan.py:326`) compares planned against
  summed WU costs — unrelated surface, borrowed vocabulary only.
- `detect_spinning_signature_repeat` (`loop.py:709`) reacts *after* attempts are
  spent. That is the cost this feature exists to avoid paying.

**Reused, not rebuilt:** `verify()` (`loop.py:2314`) already runs a named gate
set and returns `(ok, report)`; the probe calls it unchanged. The pre-dispatch
halt reuses the per-gate budget brake's exact mechanics
(`loop.py:4157-4178` — `set_gate(awaiting_review)` → `human_escalation` event →
`commit_bookkeeping` → `return 1`).

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This adds a new blocking halt, so the question applies: **what does the probe
report on a tree already in its intended final state?**

**Zero.** On a green base tree the probe's failing set is empty, no halt fires,
and dispatch proceeds byte-identically to today. The predicate is satisfiable —
it fires only on a genuinely red base tree, which is the condition it is built to
detect. Verified in T01's acceptance by a green-baseline test asserting the
dispatch path is entered normally.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0051/T01
        file: WU-01-baseline-probe-halt.md
        depends_on: []
      - id: FEAT-2026-0051/T02
        file: WU-02-baseline-persistence-killswitch.md
        depends_on: [FEAT-2026-0051/T01]
      - id: FEAT-2026-0051/T03
        file: WU-03-escalation-message-evidence.md
        depends_on: [FEAT-2026-0051/T02]
      # --- terminal gate: single close WU ---
      - id: FEAT-2026-0051/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0051/T01, FEAT-2026-0051/T02, FEAT-2026-0051/T03]
```

## Notes

- Single-gate feature (3 substantive WUs ≤ 4): one terminal `close`, no
  intermediate ceremony — proportionality (`docs/methodology.md §6`).
- **Self-hosting hazard.** `loop.py` runs from repo source, so from T01 onward
  the driver dispatching this feature's own remaining WUs executes the probe
  code T01 just wrote. This repo's gates are green, so the probe should pass and
  cost one extra gate-set run per gate entry. If it misfires, the recovery is
  `--no-baseline-probe` (T02) — which is part of why the kill-switch is in scope
  rather than deferred.
- T02 and T03 both edit the escalation site T01 creates; the dependency chain
  serializes that shared edit (the FEAT-2026-0037 T01→T02 precedent).
- The probe measures the **`code`** set specifically — the set `implementation`
  WUs are gated on. The `doc` and `plannext` sets are driver-internal and have no
  externally-fed-oracle exposure; not probed, deliberately.
- The probe fires at **every** gate's entry, not only gate 1: an advisory
  database updating between gate 1 and gate 2 is the exact failure mode. Once per
  gate is still far below once per WU.
