---
feature_id: FEAT-2026-0042
title: Autofix wiring — headless fix-bug from diagnosed findings behind a per-component dial
slug: autofix-wiring
branch: feat/FEAT-2026-0042-autofix-wiring
roadmap_goal: Make the per-component `autofix` dial do something — fire headless fix-bug on a diagnosed finding only when the diagnosis is confident and its fix_scope is small, route large/external findings to a human, and bound the whole thing with one-run-per-fingerprint, a daily cap, and a failure label.
autonomy_default: review
status: active
planned_cost_usd: 27.00
---

# Plan: Autofix wiring — headless `fix-bug` from diagnosed findings

Detection shipped in FEAT-2026-0040. Diagnosis shipped in FEAT-2026-0041. The
remaining step to a self-healing repository is launching the existing bug-fix
workflow from a diagnosed finding — guarded, because a wrong diagnosis can produce
a confidently-wrong PR, and an incident storm can flood a repository with them.

## The safety floor is not this feature's to choose

The roadmap row assigns auto-merge to
[FEAT-2026-0048](../../roadmap.md#feat-2026-0048), which is `blocked`. So the worst
outcome this feature can produce is **an unwanted pull request on a branch** —
cheap to close, nothing lands on a protected branch, no code reaches production.

That is a constraint, not a decision. No work unit in this feature may merge a pull
request, enable auto-merge, or push to a protected branch, and no later gate may
widen it. If a gate believes it needs to, that is an escalation to the operator and
almost certainly means the work belongs in 0048.

## What already exists, and what is actually missing

The dial is **already declared, already validated, and completely inert.**

```
.specfuse/monitoring.yml.example:66   autofix — whether a diagnosed finding may
                                      trigger an automated fix. one of "off" | "on"
                                      (quoted; bare `off` is not valid YAML here)
lint_monitoring.py:60                 "autofix" is in REQUIRED_COMPONENT_FIELDS
lint_monitoring.py:198                its value is validated against AUTOFIX_VALUES
```

No runtime code reads it. Every component in the example ships `autofix: "off"`.
FEAT-2026-0039/0069 built the schema and the validator; this feature builds the
consumer. `specfuse/monitor/diagnosis.py:15` already anticipates it — its docstring
says the bounded-float `confidence` exists because "FEAT-2026-0042 gates on a
threshold."

So this feature does not invent a dial, a config surface, or a vocabulary. It makes
an existing declared contract do the thing it was declared for.

## Existing-mechanism search (`.specfuse/rules/planning-discipline.md` §1)

```
Command: grep -rn "autofix" specfuse/ | grep -v /data/
         grep -nE "_MARKER_TEMPLATE|_QUIET_MARKER|_parse_meta" specfuse/monitor/issues.py
         grep -niE "headless|claude -p|interactive" .specfuse/skills/fix-bug/SKILL.md

Verdict: the DIAL exists and is validated; NO consumer reads it. The decision layer,
         the rate-limit state, and the invocation path do not exist.

Reuse:   issues.py owns the GitHub-as-state pattern this feature follows —
         `_MARKER_TEMPLATE` (fingerprint), `_META_TEMPLATE` (occurrences, last_seen),
         `_QUIET_MARKER`, and `_parse_meta` reading them back out of an issue body.
         Autofix attempt state is the same shape and must not invent a second one.

         labels.py (FEAT-2026-0071) owns LABEL_REGISTRY. The failure label is
         registered there, not hardcoded at a call site — FEAT-2026-0040 shipped a
         label its own code queried and 0071's registry did not declare, and
         `gh issue create` rejected every finding until it was made by hand (#300).

Gap:     `.specfuse/skills/fix-bug/SKILL.md` is titled "(interactive)". It has
         refusal paths that propose /draft-feature and carries the
         operator-escalation framing that halts for a human. There is NO headless
         mode to invoke. T03 builds one; the roadmap row assumed it existed.
```

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

Two criteria classes on this feature could be authored unsatisfiably, and the gate
split is the answer to the first.

Nothing in gate 1 fires anything. Every gate-1 work unit is a pure decision
layer, a state reader/writer, or a mode that is not yet invoked. That is deliberate:
it makes every gate-1 acceptance criterion satisfiable with unit tests and no side
effects, and it means a human reads gate 1's output before anything can act. The
firing wiring and its live end-to-end run are gate 2's, drafted by `G1-PLAN` and
armed by a human.

**Fix-quality is not verifiable here.** No test asserts that an automated fix is
*correct* — the same inherent limit FEAT-2026-0041 recorded for diagnosis quality.
Criteria here assert the *decision* is right (fires only when it should) and the
*mechanism* works (a run produces a PR). A criterion of the form "the autofix
produces a correct patch" would be unsatisfiable and must not be written.

## Runtime probe for a default/severity flip (§4)

Not applicable in gate 1. No default changes: `autofix: "off"` remains the shipped
default for every component and this feature does not flip one. Gate 2 introduces
firing behaviour behind that dial; `G1-PLAN` must re-answer §4 for gate 2 rather
than inherit this answer.

## Flag-scope table (§3)

Not applicable. No new behaviour flag is introduced — `autofix` already exists in the
schema. This feature adds its consumer.

## Scope boundary — explicitly OUT

- **Auto-merge, and any write to a protected branch.** FEAT-2026-0048 owns it. See
  the safety floor above. This is the hardest boundary in the feature.
- **The `diagnose: auto` trigger.** FEAT-2026-0074 owns it. This feature acts on a
  finding that already carries a diagnosis; it does not decide when to diagnose.
- **Per-component confidence tuning.** The confidence threshold is a hardcoded
  constant, per FEAT-2026-0053's precedent for arm-predicate stop classes: a safety
  threshold that lives in a config file can be tuned into uselessness by the person
  it is meant to stop. `autofix: on|off` is per-component; *how confident is
  confident enough* is not.
- **Changing what `fix-bug` does.** T03 adds a headless *mode*; it does not alter
  the bug-fix workflow, its refusal criteria, or the 1-bug-1-branch-1-PR contract.
- **Fix correctness.** Inherent, per §2.

## Two traps that will otherwise be rediscovered mid-attempt

**Local state cannot work here.** The harvester's runners are ephemeral — 0040 ships
a GitHub Actions runner and FEAT-2026-0043 will add an AKS CronJob. A state file on
disk is gone by the next invocation, so "one fix run per fingerprint" would fire once
per *run* and the daily cap would never bind. It would fail **silently**, which is
the worst shape: the guardrail reads as present. State lives on the GitHub issue.

**`fix-bug` halts for humans by design.** Driving the interactive skill and hoping
its halts resolve is not an option — a halt in a headless session has no one to
answer it. T03's headless mode must map every interactive halt to an explicit
recorded outcome. Its refusal paths then become a *second* guardrail behind T01's
predicate rather than a hang.

## Gates

```yaml
# Two gates. The split is the safety property: gate 1 ships the decision layer,
# the state, and a headless mode — none of which can fire anything. A human reads
# gate 1 and arms gate 2, which adds the firing wiring and its live end-to-end run.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0042/T01
        file: WU-01-autofix-predicate.md
        depends_on: []
      - id: FEAT-2026-0042/T02
        file: WU-02-github-state-and-label.md
        depends_on: []
      - id: FEAT-2026-0042/T03
        file: WU-03-fix-bug-headless-mode.md
        depends_on: []
      # --- closing sequence: non-terminal gate ---
      - id: FEAT-2026-0042/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0042/T01
          - FEAT-2026-0042/T02
          - FEAT-2026-0042/T03
      - id: FEAT-2026-0042/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on:
          - FEAT-2026-0042/G1-CLOSE-INTERMEDIATE
  - gate: 2
    file: GATE-02.md
    work_units:
      # Substantive WUs are drafted by G1-PLAN and inserted BEFORE this close.
      # The terminal close is pre-declared so the linter reads gate 2 as terminal.
      - id: FEAT-2026-0042/G2-CLOSE
        file: WU-92-gate-2-close.md
        depends_on: []
```
