---
id: FEAT-YYYY-NNNN/T01    # FEAT-YYYY-NNNN/TNN for substantive, /G<n>-(RETRO|LESSONS|DOCS|PLAN|CLOSE|CLOSE-INTERMEDIATE) for closing
type: implementation       # implementation | retrospective | lessons | docs | plan-next | close | close-intermediate
# model: <override>        # optional — defaults per MODEL_BY_TYPE[type] in loop.py; aliases: sonnet | opus | haiku
# effort: <override>       # optional — defaults per EFFORT_BY_TYPE[type] in loop.py; low | medium | high | xhigh | max
status: pending            # draft | pending | ready | in_progress | in_review | done | blocked_human
attempts: 0
# planned_cost_usd: 0.00   # OPTIONAL — estimated USD cost at draft time; see roadmap_goal § Planned-cost capture
generated_surfaces: []     # OPTIONAL — paths to generated files this unit's acceptance depends on
# oracle_env: macos_local  # OPTIONAL — environment where this WU's verifying oracle runs; see frontmatter notes
---

<!--
Frontmatter notes (single-repo):

AUTHOR-SET FIELDS — fill or override these at draft/arm time:
- `id` — task-level correlation ID. Pattern in `.specfuse/rules/correlation-ids.md`. Driver and
  linter both read this; must match the PLAN.md graph entry.
- `type` — drives which gate set the driver runs (`implementation` → `code`; `retrospective` /
  `lessons` / `docs` → `doc`; `plan-next` / `close` → `plannext`). Closing shapes: `close`
  (terminal gate, collapses RETRO+LESSONS+DOCS+verdict), `close-intermediate` (non-terminal,
  pair with a `plan-next` WU). Legacy four-WU sequence accepted but emits WARN.
- `status` — lifecycle position. Authors set `pending`; driver writes `in_progress`, `done`,
  `blocked_human`. `draft` = unarmed (next gate's WUs); flip to `pending` to arm.
- `model` — OPTIONAL. Claude model alias (`sonnet` | `opus` | `haiku`) or full model ID to pin
  a release. Absent → type-keyed default in `loop.py`.
- `effort` — OPTIONAL. Thinking budget for `claude -p`. Levels: `low` | `medium` | `high` |
  `xhigh` | `max`. Absent → type-keyed default. `low`/`medium` add a terseness directive.
- `planned_cost_usd` — OPTIONAL. Estimated USD at draft time. Compared against actual in close
  WU's cost analysis. Lint WARN when absent on active/draft WUs (non-blocking).
- `generated_surfaces` — OPTIONAL. Paths to generated files this unit's acceptance depends on.
- `oracle_env` — OPTIONAL. Environment the verifying oracle runs in: `macos_local`,
  `linux_docker`, `github_actions_ci`, or an operator-named string. Lint WARN when AC mentions
  oracle-like verbs but this field is absent.
- `produces_driver_helper` — OPTIONAL. Symbol(s) this WU adds or modifies in the driver
  (`loop.py`, `lint_plan.py`, adjacent scripts). Lint WARN when body mentions driver-wiring
  keywords but field is absent. See FEAT-2026-0017.
- `produces` — OPTIONAL. File path(s) this WU must produce; machine-enforced by the driver's
  presence gate (FEAT-2026-0022). Lint WARN when absent on `implementation` WUs.

DRIVER-OWNED FIELDS — the driver writes these at outcome time; authors leave them absent:
<!-- driver-owned: attempts, cost_usd, input_tokens, output_tokens, duration_seconds,
     cumulative_cost_usd, cumulative_duration_seconds, cumulative_input_tokens,
     cumulative_output_tokens, re_arm_count, re_arm_history -->
<!-- Full field semantics in docs/methodology.md §2 and events.jsonl outcome payloads. -->

Dependencies live in PLAN.md's `gates[].work_units[].depends_on` graph, not
here — see `docs/methodology.md` §2 (one fact, one home).
-->

# <imperative title, e.g. "Add health-check endpoint">

This whole body below the frontmatter is what a fresh `claude -p` session receives.
Write it so a session with no memory can execute it from this file alone. The five
sections below are mandatory — the linter rejects a dispatchable WU that is missing
any. An optional `Objective` line above them is recommended but not enforced.

**Objective.** One sentence: what this unit produces.

**Context.** What this is part of, the correlation ID, and the specs/files that
ground it. Enough for a cold session to orient. Reference the binding rules in
`.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`) and the verification skill rather
than restating them.

**Acceptance criteria.** Explicit, testable statements of done. Prefer assertion-shaped,
machine-checkable criteria — each AC phrased so a single grep, command, or test can
judge it true or false. Avoid compound criteria ("X and also Y"); split them so a single
failure attributes to a single line. For `implementation` WUs that introduce new behavior,
the first criterion names a scoped test (`tests/<path>::<test_name>` or runner-equivalent
nodeid) that **fails on HEAD before this WU runs**, and a later criterion asserts the
same test **passes after the WU's edits**. The red→green proof is the loop's
cheapest hollow-pass guard; see `/authoring-work-units` §12 for the contract and
the carve-outs (refactor, migration, pure-data → explicit `Red-test exempt:
<reason>` line in the WU body).

**Do not touch.** Generated directories (`_generated/`, `gen-src/`, or the repo's
declared equivalent), files owned by other work units in this gate, secrets,
`.git/`. The driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md` for the full list.

**Verification.** The gates that must pass. For `implementation` units these are
the `code` gates in `.specfuse/verification.yml` (tests, coverage ≥ 90%, zero
warnings, lint, security scan). Name anything unit-specific in addition — including
explicit symbol-existence checks for any new functions or constants this WU
introduces (e.g. `python3 -c "from module import new_function"`). The code gate
passes when no tests assert a symbol exists and cannot detect its absence; these
checks fill that gap. See `.specfuse/skills/verification/SKILL.md` for how to run
and interpret them.

**Escalation triggers.** Conditions under which you stop and emit `status: blocked`
in the RESULT block rather than pushing through (spec ambiguity, a required
modification of generated code, a missing dependency, a credential the unit
should not be reading). For `implementation` units introducing new symbols, include
a completeness trigger: "If [required_function / required_file] is absent from the
files you edited, emit `status: blocked` — do not claim complete." Blocked is a
respectable outcome — `result-contract.md` rule 4.
