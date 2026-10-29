---
feature_id: FEAT-LOOP-2026-0205
title: Severity on the diagnosis, so findings can be prioritised
slug: diagnosis-severity
branch: feat/FEAT-LOOP-2026-0205-diagnosis-severity
roadmap_goal: Every diagnosed monitoring finding carries a severity the diagnosis judged from its evidence, shown as a label and used to spend the autofix daily cap on the most severe findings first, without findings ever entering the bug lane
autonomy_default: auto
status: done
planned_cost_usd: 13.00
---

# Plan: Severity on the diagnosis, so findings can be prioritised

Monitoring findings deliberately skip triage (`list_untriaged` flags them
`already_structured`; the triage provider skips them — FEAT-LOOP-2026-0049), because
their route to a fix is diagnose → autofix, gated on the diagnosis's `confidence`
and `fix_scope`. Routing works without a severity, but a queue of findings is flat:
nothing says which matters most, and autofix's daily cap (`autofix_state.DAILY_CAP`)
spends itself in arrival order. FEAT-LOOP-2026-0204 put the evidence a severity judgment
needs on the finding (endpoint and status, client abort or not, frequency,
instances, host liveness), so the diagnosis can now judge impact rather than guess.

## Decisions (2026-10-17)

The operator took the drafting recommendations ("take your recommendations"); each
is recorded so the reviewer sees which choices nobody made by hand.

1. **Vocabulary: the loop's existing one** (*recommendation*) —
   `agent_policy.SEVERITY_VALUES` (`low`, `medium`, `high`, `critical`), not a new
   scale. One vocabulary means a finding's label reads like any other issue's.
2. **Optional on the contract** (*recommendation*). `Diagnosis.severity` is
   optional; a diagnosis marker without it (every diagnosis posted before this
   feature) parses with `severity` absent, and an unknown value reads as absent
   rather than raising (`[FEAT-LOOP-2026-0113/G1-CLOSE-INTERMEDIATE]`: tolerance and
   fail-closed are one edit).
3. **Label: `severity:<value>`** (*recommendation*), the standard prefix
   (`agent_policy.SEVERITY_LABEL_PREFIX`), written by the findings-diagnose provider
   after it posts the diagnosis. A later diagnosis (#3487's re-diagnosis) replaces
   the previous severity label rather than adding a second one.
4. **Routing: ordering only** (*recommendation*). The findings-autofix provider
   advertises candidates most severe first (unknown last), so the daily cap is spent
   on the highest severities. Which findings are eligible is unchanged: the
   confidence threshold, `fix_scope` routing, one attempt per fingerprint and the
   cap itself stay exactly as they are.
5. **Findings never enter the bug lane** (*recommendation*). A severity label on a
   finding must not make the bug lane advertise it; a guard test pins that the bug
   lane still requires a triage `bug` category, which findings never get.
6. **One gate** (ceremony proportionality, `docs/methodology.md` §6): 4
   substantive units.
7. **Autonomy `auto`** (*recommendation*): no driver edits.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -rn "SEVERITY_VALUES\|SEVERITY_LABEL_PREFIX\|read_severity_label\|severity" specfuse/loop/agent_policy.py specfuse/loop/triage.py specfuse/monitor specfuse/agent/providers`
- **Verdict:** `found the severity vocabulary and label prefix, reusing; no severity on the diagnosis contract, building new`
- **If reusing:** `specfuse/loop/agent_policy.py:58` `SEVERITY_VALUES` and `:481`
  `SEVERITY_LABEL_PREFIX` — the vocabulary and the label spelling every other lane
  reads. Nothing here writes a second vocabulary or a second prefix.

## Escalation-predicate satisfiability (§2)

n/a — no severity flip of a validation rule; the field is new and optional.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-LOOP-2026-0205/T01
        file: WU-01-severity-walking-skeleton.md
        depends_on: []
      - id: FEAT-LOOP-2026-0205/T02
        file: WU-02-severity-rubric-prompt-and-skill.md
        depends_on: [FEAT-LOOP-2026-0205/T01]
      - id: FEAT-LOOP-2026-0205/T03
        file: WU-03-autofix-orders-by-severity.md
        depends_on: [FEAT-LOOP-2026-0205/T01]
      - id: FEAT-LOOP-2026-0205/T04
        file: WU-04-bug-lane-guard-and-docs.md
        depends_on: [FEAT-LOOP-2026-0205/T01]
      - id: FEAT-LOOP-2026-0205/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-LOOP-2026-0205/T01, FEAT-LOOP-2026-0205/T02, FEAT-LOOP-2026-0205/T03, FEAT-LOOP-2026-0205/T04]
```

## Scope boundary

**In:** the optional `severity` field on the diagnosis contract (render, parse,
headless analysis), the rubric the headless prompt and `/diagnose-issue` share, the
`severity:<value>` label, severity ordering of autofix candidates, the bug-lane
guard, docs and `docs/flows.html`.

**Out:** triaging findings through the human-issue triage path; any change to
autofix eligibility (threshold, `fix_scope`, attempts, cap size); severity-based
alerting or paging; per-component severity overrides in `monitoring.yml`.

## Post-merge checklist

- **One live diagnosis with a severity.** After release, diagnose one real finding on
  the first consumer (by hand or `diagnose: auto`) and confirm the marker carries a
  severity, the issue gets one `severity:` label, and a second diagnosis replaces it.
