---
gate: 1
status: passed
cost_budget_usd: 26.00
baseline:
  sha: bb0a56ac7e7024982ec759ce267c922d62130a8b
  probed_at: 2026-08-10T06:22:16.139385+00:00
  failing: []
---

# Gate 1 — the bug lane runs end to end, and nothing merges unless every guardrail says so

## Definition of done

- The schema FEAT-2026-0044 shipped is verified against what this plan assumed,
  and the bug-lane dials exist on it.
- `evaluate_merge_guardrails` exists as a pure, fail-closed predicate over the
  six hardcoded guardrails, importing `arm_eval.JUDGE_PATHS` rather than
  restating it.
- The daily merge cap and the triaged-bug intake both read state that lives on
  GitHub, not on the runner's disk.
- Merge executes only when the dial is `on` **and** every guardrail passes;
  otherwise the PR is labeled with the reason and left open for a human.
- A refusal or failure from headless `/fix-bug` escalates via the
  FEAT-2026-0046 contract rather than dying silently.
- Every implementation work unit in this gate is `done`.
- The terminal close has run: retrospective, lessons, docs, and verdict.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

Single-gate feature (four substantive WUs, `docs/methodology.md` §6). No
`plan-next`, no next gate to arm.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Recorded for the reviewer, since this gate was armed at draft time:

- **Runtime probe (§4).** No WU flips a default value or an existing severity.
  The one dial this feature reads (`rules.bugs.automerge`) ships **default
  `off`** and stays `off` in this repo's own policy file for the whole feature —
  see PLAN.md § *Notes*. There is no default to probe against.
- **Flag-scope table (§3).** T04 gates behavior on `rules.bugs.automerge` and
  carries a flag-scope table naming every path that dial reaches, including the
  paths it deliberately does not.
- **Escalation-predicate satisfiability (§2).** Answered in PLAN.md. The
  predicate is per-PR, not per-tree, so it turns no CI gate red; and it fails
  closed on every unreadable input by construction.

## The risk this gate carries, stated plainly

T04 is the only work unit in either of tonight's two features that performs an
**irreversible outward action** — merging a pull request into the default
branch. Three things bound it, and a reviewer should check all three rather
than any one:

1. The dial ships `off` and this repo keeps it `off`. Nothing merges
   automatically as a result of this feature landing.
2. The predicate fails closed: any missing, malformed, or unreadable input
   yields "do not merge".
3. `JUDGE_PATHS` is imported, so a fix touching the driver, the rules, CI
   workflows, or the verification config can never auto-merge regardless of the
   dial.

## Reflection notes

<Written by the human at review time. This gate was drafted and armed without an
operator interview, on operator instruction (2026-08-09), and drafted against a
schema that did not exist yet — see PLAN.md § *Assumed decisions* and § *The
dependency that makes T01 exist*. If T01 reported a divergence, read its
escalation before anything else.>
