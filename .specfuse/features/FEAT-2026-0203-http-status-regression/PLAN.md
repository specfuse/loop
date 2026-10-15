---
feature_id: FEAT-2026-0203
title: Deploy-correlated HTTP status regression check
slug: http-status-regression
branch: feat/FEAT-2026-0203-http-status-regression
roadmap_goal: A deployment that breaks auth, routing or content negotiation raises one finding per (component, status code, deployment), without continuous rate alerting
autonomy_default: auto
status: done
planned_cost_usd: 19.50
---

# Plan: Deploy-correlated HTTP status regression check

A deployment that breaks auth configuration, role or scope mapping, routing or
content negotiation produces a wave of 4xx responses, not 5xx, so `http-5xx` never
fires and the regression ships silently (#248). A continuous 4xx-rate alert would
cross the monitoring initiative's "no metrics" boundary, and FEAT-2026-0069 recorded
that `invariant` is not the sanctioned route to rate-based detection.

The operator's refinement on #248 resolves that tension: a server-fault 4xx spike
indicates a backend regression only when it starts soon after a component
deployment. Bounded to a window after each deployment, the check fires once per
deployment, with one finding per (component, status code, deployment). That is a
discrete, fingerprintable artifact, not a metric.

This feature ships a first-class `http-status-regression` check type, the Azure App
Insights adapter for it, `derive-monitoring` support, and — folded in at the
operator's decision on 2026-10-14 — #295's `stall_after` lint, because both need one
shared duration grammar (`window_after_deploy` and `stall_after` are the same kind of
value).

## Decisions (interview, 2026-10-14)

Taken at draft time. Items marked *operator* were answered explicitly; items marked
*recommendation* were taken under the operator's "take your recommendations for the
rest" and are recorded here so the arming reviewer can see which choices nobody made
by hand.

1. **Deploy signal: application version only, in v1** (*operator*). A deployment is
   the first `AppRequests` row for the component carrying a new `AppVersion`; the
   version string is the deployment's identity. It needs nothing beyond the
   `workspace_id` binding the provider already has. `deploy_signal.kind` exists in
   the schema so a CI-annotation or marker-query kind can be added later without a
   breaking change, but lint accepts only `app-version` now: permitting a value later
   breaks nobody, rejecting one after release does
   (`[FEAT-2026-0069/G2-CLOSE]`). The CI-annotation kind was rejected for v1 because
   App Insights annotations live on the App Insights resource, not in workspace
   tables — the coordinate switch #3468 avoided.
2. **Regression rule: share of requests, fixed thresholds** (*operator*). For each
   code in `codes`, compare its share of the component's requests in the window after
   the deployment with its share in an equal-length window immediately before. Fire
   when the after-share is at least **3×** the before-share **and** the code occurs
   at least **10** times in the after-window. Both numbers are documented constants
   in v1, not `monitoring.yml` fields — same asymmetry as decision 1. Share rather
   than raw count, because deployments cluster at low-traffic hours and a raw count
   reads a morning traffic ramp as a regression.
3. **Autonomy: `auto`** (*recommendation*). The terminal verdict is written by a
   fresh judge session from evidence only. Nothing here edits the loop driver, and an
   unreleased check type is cheap to correct.
4. **One gate, one terminal close** (*recommendation*). Five substantive units, under
   the ceremony-proportionality threshold (`docs/methodology.md` §6).
5. **One query per check, aggregates only** (*recommendation*, forced by a binding
   rule). `azure_app_insights.py`'s module contract and `security-boundaries.md`
   forbid folding a value returned by a telemetry query into a subsequent query. The
   deployment's first-seen time is such a value, so deployment detection and window
   counting happen in **one** KQL query; the adapter does the ratio arithmetic in
   Python over the returned aggregates. A two-query design is not a variant, it is a
   boundary violation.
6. **Evaluate a deployment only once its window has fully elapsed**
   (*recommendation*). Never on a partial window, so a deployment's verdict is
   computed once and does not change between harvester runs.
7. **A first deployment with no prior traffic** has a before-share of 0, so at least
   10 occurrences in the after-window fires (*recommendation*). A code absent before a
   rollout and present after it is the signal this check exists for.
8. **Re-sighting after a closed finding is accepted, not solved**
   (*recommendation*). `issues.record_finding` searches open issues only, so a spike
   re-observed after its issue is closed opens a new one. Decision 6 makes that rare
   (a deployment is evaluated in the run after its window closes); the residual is
   recorded at close, not engineered around here.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:**
  `grep -rniE "deploy|AppVersion|application_Version|rollout" specfuse/monitor specfuse/loop/lint_monitoring.py`,
  `grep -rnE "def parse_[a-z_]*(seconds|duration)|_DURATION_RE|stall_after" specfuse/monitor specfuse/loop/lint_monitoring.py`,
  and `grep -rnE "timespan|since=|window" specfuse/monitor/*.py specfuse/monitor/providers/*.py`
- **Verdict:** `found parse_stall_after_seconds, reusing/extending; no deployment concept and no time-window support exist, building new`
- **If reusing:** `specfuse/monitor/providers/azure_service_bus.py:149`,
  `parse_stall_after_seconds` — "Parse a `stall_after` value (`<integer><unit>`, unit
  in s/m/h/d)". T02 moves that grammar to one shared home both the adapter and the
  linter import, and `window_after_deploy` uses it too; nobody writes a second
  duration regex. The deployment hits are prose only ("unit of deployment"). The
  window hits are the harvester's watermark lookback (`cli.py:318`, never passed to an
  adapter) and the transport's `timespan=None` (`azure_app_insights.py:335`): no
  adapter today queries a bounded window, so T04 builds that inside its one query.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

T02 raises a malformed `stall_after` from "accepted, opaque" to a lint **error**.

- **What does the rule report on an input already in its intended final state?**
  Zero. Every `stall_after` shipped in this repository is `15m`
  (`.specfuse/monitoring.yml.example:175`, `specfuse/loop/data/monitoring.yml.example:175`,
  and the FEAT-2026-0069 review document), which conforms to the grammar. T02's
  criteria re-measure that over every shipped monitoring YAML, including the fenced
  blocks `tests/test_monitoring_fenced_blocks.py` validates, before the flip.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0203/T01
        file: WU-01-walking-skeleton.md
        depends_on: []
      - id: FEAT-2026-0203/T02
        file: WU-02-shared-duration-grammar.md
        depends_on: []
      - id: FEAT-2026-0203/T03
        file: WU-03-schema-and-lint.md
        depends_on: [FEAT-2026-0203/T01, FEAT-2026-0203/T02]
      - id: FEAT-2026-0203/T04
        file: WU-04-adapter-regression-rule.md
        depends_on: [FEAT-2026-0203/T01]
      - id: FEAT-2026-0203/T05
        file: WU-05-derive-monitoring-and-rule.md
        depends_on: [FEAT-2026-0203/T03, FEAT-2026-0203/T04]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-2026-0203/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0203/T01, FEAT-2026-0203/T02, FEAT-2026-0203/T03, FEAT-2026-0203/T04, FEAT-2026-0203/T05]
```

## Scope boundary

**In:** the `http-status-regression` check type (schema, lint, docs, both example
files); the App Insights adapter and its one query; CLI wiring of the new fields; the
shared duration grammar and #295's `stall_after` lint; `derive-monitoring` proposing
the check; the design-for-diagnosis rule on version stamping.

**Out:** the CI-annotation and marker-query deployment signals; configurable
thresholds; 5xx regressions (`http-5xx` owns those); providers other than Azure App
Insights; re-sighting after a closed finding (decision 8); any consumer's adoption,
including the first consumer, whose services do not stamp a version yet.

## Post-merge checklist

- **Live run against a real workspace.** Every in-loop oracle runs over a stub
  transport, and the query is checked against the workspace schema reference from
  #3471, not against Azure. Run the opt-in live check
  (`SPECFUSE_LIVE_TESTS=1 SPECFUSE_LIVE_WORKSPACE_ID=<id>`) once the new query is in
  its list, against a workspace whose component stamps `AppVersion`. No consumer does
  today, so this cannot be a pre-close human unit.
