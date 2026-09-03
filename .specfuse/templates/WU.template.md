---
id: FEAT-YYYY-NNNN/T01     # /TNN substantive, /G<n>-CLOSE (etc.) closing
type: implementation       # implementation | human | retrospective | lessons | docs | plan-next | close | close-intermediate
status: pending            # draft | pending | ready | in_progress | in_review | done | blocked_human
attempts: 0
generated_surfaces: []     # OPTIONAL
# OPTIONAL, all commented out by default: `model`/`effort` overrides (absent =
# the type default), `planned_cost_usd`, `oracle_env`, `produces`.
---

<!--
One line per frontmatter field, including the optional `prep`, `oracles`,
`extra_gates`, `max_attempts`, `iterate_on_failure`, `produces`,
`produces_driver_helper`, `human_only`, `provenance` and `auto_close_disabled`
keys: `docs/methodology.md` §2, their one home. Do not restate them here;
dependencies live in PLAN.md's `depends_on` graph, not in frontmatter.

Closing shapes: `close` on a terminal gate folds RETRO+LESSONS+DOCS+verdict;
`close-intermediate` is its non-terminal twin and pairs with a `plan-next` WU.
The legacy four-WU sequence still parses and emits a lint WARN. Planning-WU
cost floors (`.specfuse/rules/planning-discipline.md` §5): $6.00 `plan-next`,
$5.00 `close`, $4.50 `close-intermediate`. Do NOT raise these to absorb a
second attempt: a closing-WU retry is a defect to diagnose, not a cost to
budget for.

DRIVER-OWNED FIELDS - written by the driver at dispatch and outcome time; authors
leave them absent: attempts, cost_usd, input_tokens, output_tokens,
duration_seconds, cumulative_*, re_arm_count, re_arm_history,
folded_through_re_arm, model, effort, gate_set, driver_version, started_at.
On every re-arm the driver folds the prior cycle's spend into the `cumulative_*`
lifetime accumulators unconditionally, including a re-arm
whose prior cycle cost nothing; `folded_through_re_arm` records what is folded.
-->

# <imperative title, e.g. "Add health-check endpoint">

Aim for 30-45 lines below: this is the entire prompt a cold, memoryless session
gets. The five bold sections are mandatory (the linter rejects a dispatchable
unit missing any); `Objective` is recommended, not enforced.

**Objective.** One sentence: what this unit produces.

**Context.** The correlation ID, what this is part of, and the specs/files that
ground it. Reference `.specfuse/rules/` and `/authoring-work-units` rather than
restating them; a restated rule drifts from its source.

**Acceptance criteria.** Two to five bullets, each pairing a statement of done
with the one command, grep, or test nodeid that judges it true or false. No
compound criteria. For an `implementation` unit introducing new behavior, one
bullet names a scoped test that fails on HEAD and passes after this unit's edits
(`/authoring-work-units` §12; write `Red-test exempt: <reason>` when carved out).

**Do not touch.** Only the deltas from `.specfuse/rules/never-touch.md`: the
sibling-WU files in this gate and the repo-specific paths this unit might brush
against. Generated dirs, secrets, `.git/` and "the driver owns all git" bind there.

**Verification.** The gate set the driver runs for this `type` (for `implementation`,
the `code` set in `.specfuse/verification.yml`) plus any unit-specific command,
including a symbol-existence check per new importable symbol (`/authoring-work-units` §9).

**Escalation triggers.** One or two conditions that stop the session with
`status: blocked` instead of pushing through: a spec ambiguity, a `never-touch.md`
boundary, a missing dependency, a required symbol still absent from the files you
edited. Blocked is a respectable outcome (`result-contract.md`).

<!-- Conditional sections, omitted unless they apply. A unit that introduces,
gates on, or flips a behavior flag adds a flag-scope table: every affected code
path, gated / not gated, one line of why (`planning-discipline.md` §3). A `close`
/ `close-intermediate` unit adds close obligations (`close-discipline.md` §§1-5 —
the verdict is binary; a `not_met` close writes `FOLLOW-UPS.md`), exits 0 on `specfuse lint --closing`, and sets `auto_close_disabled: true`. -->
