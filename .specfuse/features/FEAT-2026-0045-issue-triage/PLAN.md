---
feature_id: FEAT-2026-0045
title: issue-triage skill — categorize and route incoming GH issues (manual → auto dial)
slug: issue-triage
branch: feat/FEAT-2026-0045-issue-triage
roadmap_goal: Give every inbound GitHub issue exactly one lane — categorized, routed, and recorded in an authoritative body marker projected to a human-visible label — through a mechanism module that FEAT-2026-0048 can import and a thin interactive skill that owns the judgment.
autonomy_default: review
status: done
planned_cost_usd: 18.00
---

# Plan: issue-triage — mechanism in a module, judgment in a skill

Issues arrive from three places: the monitoring harvester, the orchestrator, and third
parties. Nothing categorizes them. `/attention` reads the `needs-human` queue and
`gh_features.list_features` reads `specfuse:feature`, but both consume labels that
somebody else already applied — no code in this repository decides what an untriaged
issue *is*.

FEAT-2026-0048 (autonomous bug pipeline) is blocked on this feature for a
**machine-readable** intake. That word decides the shape: a skill whose only artifact is
prose gives 0048 nothing to import.

## The constraint that shapes this feature

**`gh` does not work inside a dispatched `claude -p` session.** The symptom is an
invalid-token error from `gh auth status` and a TLS certificate failure from
`gh issue view`, while the same token succeeds from the operator's shell. The cause is
the command sandbox — corrected in `[FEAT-2026-0014/T01/gh-claudeP-broken]` by
FEAT-2026-0041/G1-CLOSE, after the original mis-diagnosis blamed the `gh` binary and its
ban cost two features.

So **no work unit in this feature may have "call live GitHub" as its oracle.** Every
module here takes an injectable runner and is tested over fixture issue JSON. This is
not a workaround; it is the convention the existing-mechanism search found already in
place at all five call sites.

## The seam: module = mechanism, agent = judgment

`triage.py` decides deterministically what counts as untriaged, what is already
structured (a harvester issue, recognised by the fingerprint marker `issues.py` already
owns), where a category routes, and how a decision is recorded. It does **not** classify
free-text third-party issues. That is the skill's judgment, and no unit test in this
feature will claim otherwise.

This is `[FEAT-2026-0024/G2-CLOSE]` applied at design time rather than discovered at
block time: split the deliverable at the unit-testable seam, and ship the part whose
true oracle is out of reach as an operator-deferred hedge rather than manufacturing
in-loop confidence for it.

## Existing-mechanism search (`.specfuse/rules/planning-discipline.md` §1)

```
grep -rn "gh issue list" --include=*.py specfuse/
  → 5 independent call sites:
      specfuse/monitor/issues.py:144        findings, by label + client-side marker
      specfuse/monitor/autofix_state.py:141 attempted fixes, same shape
      specfuse/loop/escalation.py:157       needs-human queue
      specfuse/loop/gh_features.py:28       specfuse:feature discovery
      specfuse/loop/labels.py:76            (comment only, no call)
  verdict: NO shared issue-listing client exists. Every site rolls its own with an
           INJECTABLE runner and filters client-side. Reusing that convention —
           not building a sixth ad-hoc shape, and not refactoring the five into a
           shared client, which is a different feature with its own blast radius.

grep -rn "triage" --include=*.py specfuse/ tests/
  → specfuse/loop/labels.py:57              LabelSpec(name="triage-question", ...)
    specfuse/loop/escalation.py:25          CATEGORY_LABELS member
    tests/test_escalation_contract.py:52    asserts it is a valid category
  verdict: the `triage-question` LABEL exists and is provisioned by FEAT-2026-0071.
           NO categorisation, routing, or scan mechanism exists. Building new,
           reusing the existing label for the question/unclear route.
```

**Verb check** (`[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/roadmap-row-verbs-are-claims]`).
The roadmap row's verbs were greppped, not assumed:

| Row's verb | Mechanism it names | Verdict |
|---|---|---|
| "queued for fix-bug" | headless `/fix-bug` | **exists** — `plugins/specfuse/skills/fix-bug/SKILL.md` §"Headless mode", closed outcome set `refused` / `could_not_proceed` / `completed`; `monitor/autofix_invoke.build_invocation` builds it |
| "recognizes harvester-created issues" | the finding marker | **exists** — `issues.py:60` `_MARKER_TEMPLATE`, private; T01 adds a narrow public predicate rather than re-typing the literal |
| "labeled" | label provisioning | **exists** — `LABEL_REGISTRY` + `provision_labels`, FEAT-2026-0071 |
| "behind an `auto` dial" | `agent-policy.yml` | **DOES NOT EXIST** — FEAT-2026-0044 is `planned` and unbuilt. Resolved below. |

## The decision the row left open: where the `auto` dial lives

The row says "headless mode behind an `auto` dial", but the file that owns every agent
dial is FEAT-2026-0044's `.specfuse/agent-policy.yml`, which does not exist.

**Chosen: the dial is an explicit argument at the headless entry point** —
`apply_triage(..., auto=False)`. No config file is read, no schema is declared, no lint
rule is added.

Rejected: building a minimal `agent-policy.yml` reader now. It takes 0044's core scope,
leaves 0044 shipping *against* a partial schema someone else authored, and declares a
surface nothing consumes — the drift shape FEAT-2026-0058 exists to prevent.

The `autofix` dial is **not** a transferable precedent: it is per-*component* in
`monitoring.yml`, and inbound issues are not components, so no existing file has a
legitimate claim on this dial. When 0044 lands it wires its policy file to a parameter
that already exists and is already tested.

## The decision the row under-specified: how a triaged issue is marked

**Chosen: both a body marker and a label, with the marker authoritative.**

The marker `<!-- specfuse:triage category={c} confidence={k} -->` is the source of truth
and the idempotency key. The category label is a *projection* of it for human visibility
in the GitHub UI — which is what makes the row's "leaves the rest labeled for human
triage" actually true.

Precedence is declared rather than left to chance: **if they disagree, the marker wins**,
and re-labelling is idempotent repair. This dissolves the usual two-writes-drift
objection, and it is not a new invention — `autofix_state.has_prior_attempt` already
locates an issue via the label listing and then *re-checks the body marker client-side
rather than trusting the listing*, precisely so a coincidental label match never reads
as a hit.

Write order follows from the precedence: **marker first, then best-effort label.** A
missing label is cosmetic and repairable; a missing marker means the issue is still
untriaged and will be retried.

**Registered is not provisioned** (`[FEAT-2026-0042/G2/registered-is-not-provisioned]`).
Four new labels enter `LABEL_REGISTRY`, and that rule requires naming which of the two
choices this feature makes for the code path that *uses* them: **tolerate absence.**
`apply_triage` records a failed label write in its report and never raises. A repository
that has not run `provision_labels` still gets correct triage; it just does not get the
colour swatch.

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

Not applicable. No check is raised to `ERROR`, no `WARNING` is made blocking, and no
"zero issues" close predicate is asserted. Nothing that validates today stops validating.

## Flag-scope table (§3)

Applicable, and **owned by T02**, which is the WU that introduces the `auto` behaviour
flag. The table lives in that WU rather than being restated here (one fact, one home).
The headline claim the arming review must check it against is: *"`auto` applies only
high-confidence categorisations and leaves the rest for human triage."*

## Runtime probe for a default/severity flip (§4)

Not applicable. No default value or severity is flipped. `auto` defaults to `False`,
which is the behaviour that exists today (there is no headless path at all), so the
default is not a change to anything.

## Scope boundary — explicitly OUT

- **Invoking `/fix-bug`, writing roadmap rows, or closing duplicates.** Triage produces a
  category, a route, and a record. Acting on the route is FEAT-2026-0048's job for bugs
  and the operator's for everything else. A triage skill that also fixes is two features.
- **`.specfuse/agent-policy.yml`, in any form.** FEAT-2026-0044 owns it. Reasoned above.
- **Refactoring the five `gh issue list` call sites into a shared client.** Real debt,
  different feature, much wider blast radius than this one.
- **Deterministic duplicate detection.** `duplicate` ships as a judgment-only category:
  the module gives it a marker and a route, and nothing more. Operator decision at draft
  time — cutting it entirely would leave the skill unable to express one of the most
  common triage outcomes, so it stays, named in the close's deferred list.
- **Re-triaging issues that already carry a marker.** Whether a *stale* triage should
  ever be revisited (the issue was edited since; confidence was `low`) is deliberately
  left open, exactly as FEAT-2026-0074's row leaves its re-diagnosis question open. v1
  is: marked means done.
- **Reusing GitHub's conventional `wontfix` label.** `triage:wontfix` is minted instead.
  The registry owns provisioning and must never `--force` over an operator's edited
  colour or description (FEAT-2026-0071's constraint), so adopting a label we did not
  create means drift we cannot repair.

## The trap that will otherwise be rediscovered

**The skill's documented vocabulary and the module's constants are two statements of one
contract, and prose drifts.** T03's oracle is a drift test binding them — which is worth
having, and is *not* proof that an agent following the prose triages correctly. That gap
is named here, in T03's body, and in the close, so the green does not read as "the skill
is proven" — the failure `[FEAT-2026-0069/G2-CLOSE]` records.

## Gates

```yaml
# Single terminal gate: 3 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0045/T01
        file: WU-01-triage-mechanism.md
        depends_on: []
      - id: FEAT-2026-0045/T02
        file: WU-02-apply-and-auto-dial.md
        depends_on: [FEAT-2026-0045/T01]
      - id: FEAT-2026-0045/T03
        file: WU-03-triage-issues-skill.md
        depends_on: [FEAT-2026-0045/T01, FEAT-2026-0045/T02]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0045/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0045/T01
          - FEAT-2026-0045/T02
          - FEAT-2026-0045/T03
```

## Expected verdict

**`met_locally`, not `met`.** Two acceptance surfaces are unreachable from inside a
dispatched session: triage against a live GitHub repository (the sandbox constraint
above), and "an agent following T03's prose reproduces the module's routing on an unseen
issue" (no test can assert this). Both are named in the close's hedged follow-up record
with a `kind:`, per `close-discipline.md` §2. Flagged at draft time so the verdict is a
plan, not a surprise.
