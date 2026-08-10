---
feature_id: FEAT-2026-0048
title: Autonomous bug pipeline — triage → fix → PR with auto-merge dial and hardcoded guardrails
slug: autonomous-bug-pipeline
branch: feat/FEAT-2026-0048-autonomous-bug-pipeline
roadmap_goal: Run the full bug lane headlessly — triaged bug issue or diagnosed finding to headless fix-bug to PR, and on CI green merge behind a default-off dial that opens the gate without ever removing the guardrails.
autonomy_default: auto
status: planned
planned_cost_usd: 21.00
---

# Plan: Autonomous bug pipeline

The agent's core autonomy promise: bugs handled end to end. Small test-first
diffs are cheap to revert, so the risk asymmetry favors autonomy for bugs
specifically — unlike features, where gate review stays human. This feature
supersedes FEAT-2026-0042's "human merge is the permanent floor" with "default
floor **plus** a dial", and the dial **opens the gate; it never removes the
fence**.

Drafted **solo, without an operator interview**, on operator instruction
(2026-08-09), and drafted **before FEAT-2026-0044 shipped the schema it builds
on**. Both are recorded in § *Assumed decisions*, and T01 exists specifically to
catch the second one going wrong.

## Scope boundary

**IN.** The bug-lane dials on `agent-policy.yml`; a pure guardrail predicate for
merge eligibility; durable (non-disk) merge-cap state; triaged bug issues as a
lane intake alongside diagnosed findings; merge execution behind the dial; and
escalation on refusal via the FEAT-2026-0046 contract.

**OUT — the scheduler.** Nothing here decides *when* the lane runs.
FEAT-2026-0049 owns invocation; this feature ships functions and a CLI entry
point it can call.

**OUT — features.** Gate review stays human. This lane is bugs only, and the
`features.gate_review` dial FEAT-2026-0044 ships is untouched here.

**OUT — re-designing `/fix-bug`.** Its headless mode, its `refused` /
`could_not_proceed` / `completed` outcomes, and every one of its refusal
criteria shipped in FEAT-2026-0042. This feature consumes them. **No refusal
path is weakened or removed** — that sentence is already in the skill and stays
true.

**OUT — the notify webhook.** FEAT-2026-0047 owns outbound notification.
Escalations here are GitHub issues per FEAT-2026-0046; the webhook is a later
consumer of the same issues.

## Assumed decisions (drafted without an interview — operator veto at PR review)

1. **Single gate, single terminal `close`.** Four substantive WUs, at the
   ceremony-proportionality threshold (`docs/methodology.md` §6). Also avoids an
   unattended `plan-next` drafting a second gate overnight.
2. **The guardrail predicate is pure and fails closed.** It reads no files and
   performs no I/O; every input is passed in, and *any* failure to evaluate any
   input returns "do not merge". This copies `autofix.decide` exactly, including
   its docstring promise — *"Any failure to evaluate an input returns DECLINE."*
   A guardrail that throws on malformed input is a guardrail that a malformed
   input walks through.
3. **The merge cap's state lives on GitHub, never on disk.** Per
   `[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/ephemeral-runner-state-fails-open]`:
   the runner is a GitHub Actions container today and an AKS CronJob tomorrow,
   so a disk-backed counter never reaches its cap, silently, while still reading
   as a rate limiter in review. `autofix_state.py` already solved this with
   issue-body markers and a re-derived count; this feature copies that shape.
4. **Never-auto-merge paths are `arm_eval.JUDGE_PATHS`, imported not retyped.**
   That tuple (`.specfuse/verification.yml`, `.specfuse/hooks/`,
   `.specfuse/rules/`, `.github/workflows/`, `specfuse/loop/`, `pyproject.toml`)
   is this repo's already-ratified answer to "what must a human look at",
   shipped by FEAT-2026-0053. A second hand-written list would drift from it,
   and the drift would be invisible. A bug fix touching any of them can still be
   *authored* by the lane; it just never auto-merges.
5. **Test-first evidence is checked structurally, not semantically.** The
   guardrail asserts the PR's diff adds at least one test file and that CI ran
   green — it does not attempt to judge whether the test is a *good* test. A
   semantic judgment here would be a model-authored approval, and
   FEAT-2026-0053's organizing principle binds: *model-authored signals may only
   veto; only mechanical facts and human-authored constants may approve.*
6. **Guardrail failure labels the PR and leaves it open for a human.** It does
   not close the PR, and it does not retry. The work is still valuable — a
   green, ready-to-merge PR is the dial-off outcome anyway.
7. **`bug_automerge` reads from `rules.bugs.automerge`**, the key FEAT-2026-0044
   ships, rather than a new top-level dial. The roadmap row for 0044 already
   names `automerge` inside its `bugs:` class-rule block; adding a second home
   would split one fact across two keys.

## The dependency that makes T01 exist

This feature was drafted before FEAT-2026-0044 was built, so every schema
reference below is an **assumption about a file that did not exist at drafting
time**. That is exactly the shape
`[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/roadmap-row-verbs-are-claims]` warns
about, and the mitigation is mechanical rather than hopeful: **T01's first job
is to verify the shipped schema against what this plan assumed and escalate on
divergence**, before any other WU builds on it.

Assumed, and to be verified by T01:

| Assumed surface | Assumed shape |
|---|---|
| `specfuse/loop/agent_policy.py` | module exists |
| `load_policy(path=None) -> dict` | returns the parsed mapping |
| `validate_agent_policy(path=None) -> list[str]` | findings prefixed `ERROR: ` / `WARN: ` |
| `rules.bugs.automerge` | `off` \| `on`, default `off` |
| `rules.bugs.min_severity` | `low` \| `medium` \| `high` \| `critical` |
| `rules.bugs.preempt` | bool |

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  - `grep -n "^def \|^class \|^[A-Z_]\+ = " specfuse/monitor/autofix.py specfuse/monitor/autofix_state.py specfuse/monitor/autofix_invoke.py specfuse/monitor/autofix_run.py`
  - `grep -rn "JUDGE_EDIT\|judge_edit\|decision_class_paths" specfuse/loop/*.py`
  - `grep -n "refus\|large\|complex\|promot" .specfuse/skills/fix-bug/SKILL.md`
  - `grep -n "^def \|^class " specfuse/loop/escalation.py specfuse/loop/triage.py`
- **Verdict:** `found five existing mechanisms, reusing all five — this feature is assembly plus one genuinely new predicate.`

| Surface this feature needs | Existing mechanism | Verdict |
|---|---|---|
| Decision predicate shape (decide/decline + reason constants + injected state reader) | `monitor/autofix.py::decide(...) -> AutofixDecision`, `CONFIDENCE_THRESHOLD`, `REASON_*` | **copy the shape** — T02 |
| Durable, non-disk rate-limit state | `monitor/autofix_state.py::daily_cap_reached`, `has_prior_attempt`, `record_attempt`, `GitHubAutofixState`, marker templates | **copy the shape and the marker convention** — T03 |
| Headless `/fix-bug` invocation + outcome classification | `monitor/autofix_invoke.py::build_invocation`, `classify_outcome`, `OUTCOMES` | **call directly** — T04 |
| End-to-end finding → fix orchestration | `monitor/autofix_run.py::run_autofix`, `_apply_failed_label` | **extend, do not fork** — T03/T04 |
| Never-auto-merge path set | `loop/arm_eval.py::JUDGE_PATHS` | **import** — T02 |
| Escalation issue contract | `loop/escalation.py::emit_escalation`, `render_escalation_body` | **call directly** — T04 |
| Triage state on an issue | `loop/triage.py::parse_marker`, `CATEGORIES`, `route_for` | **call directly** — T03 |

**Genuinely new:** only `evaluate_merge_guardrails` — the merge-eligibility
predicate. Everything else in this feature is wiring between mechanisms that
already shipped.

**Roadmap-row verb check** (`[FEAT-2026-0045/G1-CLOSE/verb-check-table-earns-its-cost]`):

| Verb from the row | Mechanism it assumes | Backed? |
|---|---|---|
| "headless `/fix-bug`" | a non-interactive fix-bug entry point | **yes** — headless mode + outcome table shipped in FEAT-2026-0042; the skill documents it |
| "its large/complex refusal escalates" | fix-bug refusal criteria reaching an escalation | **yes** — `refused` outcome exists; `emit_escalation` exists |
| "on CI green, merge" | a readable CI conclusion per PR | **partly** — `gh pr checks` is the mechanism; **no wrapper exists in this repo**, so T04 builds the thinnest one. Recorded as the one row not already backed. |
| "behind `bug_automerge: off\|on`" | the dial's config home | **assumed** — FEAT-2026-0044 ships it; this is precisely what T01 verifies |
| "a daily auto-merge cap" | durable cross-invocation counter | **yes** — `autofix_state` pattern, and see assumed decision 3 |

5 verbs, 3 fully backed, 1 partly (T04 owns the gap, scoped), 1 assumed-and-verified-by-T01.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature raises no existing check to `ERROR` and flips no severity. It adds
a **new** predicate whose default answer is "do not merge".

- **What does the predicate report on an input already in its intended final
  state?** For the *repository*: nothing — it runs per-PR, not over the tree, so
  there is no "correct tree" for it to fire on, and no CI gate goes red because
  of it. For a *PR* in its intended final state (test-first diff, CI green,
  under the size cap, no `JUDGE_PATHS` touched, traced to a triaged issue,
  under the daily cap): **merge-eligible**, with every guardrail satisfied.
- The inverse is the one that matters and is deliberate: on **any** missing or
  unreadable input, the answer is **not** merge-eligible. Fails closed.

## Task graph

```yaml
# Single terminal gate: 4 substantive WUs, at the ceremony-proportionality
# threshold (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0048/T01
        file: WU-01-verify-policy-schema-and-bug-dials.md
        depends_on: []
      - id: FEAT-2026-0048/T02
        file: WU-02-merge-guardrail-predicate.md
        depends_on: [FEAT-2026-0048/T01]
      - id: FEAT-2026-0048/T03
        file: WU-03-lane-state-intake-and-merge-cap.md
        depends_on: [FEAT-2026-0048/T02]
      - id: FEAT-2026-0048/T04
        file: WU-04-merge-execution-and-escalation.md
        depends_on: [FEAT-2026-0048/T03]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0048/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0048/T01
          - FEAT-2026-0048/T02
          - FEAT-2026-0048/T03
          - FEAT-2026-0048/T04
```

Strictly serial, unusually for this repo, and deliberately: T01 establishes that
the schema this plan assumed is the schema that shipped; T02 is the predicate;
T03 supplies the state the predicate reads; T04 is the only unit that performs
an irreversible action, and it must be last so every guardrail exists before
anything can merge.

## Notes

- **The dogfood boundary.** This repo's `.specfuse/agent-policy.yml` keeps
  `rules.bugs.automerge: off` throughout. This feature builds the dial; it does
  not turn it on. Flipping it on is an operator decision on a separate commit,
  after reading the guardrails.
- **`prep`/`oracles` are not used here.** The guardrail predicate is pure and
  unit-testable with injected fakes, so no pre-dispatch environment capture is
  needed.
- Every WU that touches GitHub does so through an injected `runner` callable,
  matching `triage.py` and `autofix_run.py`, so tests never reach the network.
