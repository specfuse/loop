---
feature_id: FEAT-2026-0054
title: Close-ceremony skeleton + in-session closing lint
slug: close-ceremony-skeleton
branch: feat/FEAT-2026-0054-close-ceremony-skeleton
roadmap_goal: Make the closing-format guard class structurally near-impossible to fail — the driver pre-creates every artifact shape the closing guards assert on at dispatch time, and a new `specfuse-lint --closing` mode lets the close agent validate the full closing contract in-session before ending its attempt, so post-squash guard refusals stop burning full re-attempts.
autonomy_default: review
status: done
planned_cost_usd: 28.00
---

# Plan: close-ceremony skeleton + in-session closing lint

**Evidence base (portfolio review, 2026-07-30).** 28% of all closing-WU spend across 9 repos is
driver refusals. Measured classes: `closing_deliverable_missing` ~$42 across 15 attempts;
`assert_gate_review_exists` alone $53.11 across 15 refusals (issue #261, "the costliest guard in
the system"); FEAT-2026-0066's G3-CLOSE lost $6.20 to format guards before any verification ran.
The guards check literal artifact shape (headings, frontmatter fields, file names) **after** the
attempt — `assert_closing_deliverables` fires post-squash, `git reset --hard` discards the work,
and a $4–10 verification pass is re-bought over a missing heading. Close-WU prompts defend
against this with restated guard strings (~40% of WU-92/WU-93 body text in FEAT-2026-0066),
which is machine contract leaking into prose.

**The durable rule this feature mechanizes** ([FEAT-2026-0070/G1-CLOSE-INTERMEDIATE],
`.specfuse/LEARNINGS.md`): *when a contract is enforced at two moments, the earlier enforcer
must name the later one.* Today the closing contract has one enforcement moment (post-squash,
terminal) and zero earlier surfaces. This feature adds the earlier moments — skeleton at
dispatch, lint in-session — and makes all enforcement points read one shared requirement
registry so they cannot drift apart.

## Existing-mechanism search (planning-discipline.md §1)

Run at draft time (2026-07-30), against working-tree HEAD:

| Command | Verdict |
|---|---|
| `grep -n "CLOSING_ASSERTIONS_BY_TYPE\|assert_retrospective_exists\|assert_gate_review_exists" specfuse/loop/loop.py` | Guard functions exist (`loop.py:3926`, `:4232`, registry dict at `:4294`) — **refactor to read a shared registry, do not rebuild**. |
| `grep -n "write_stub_retrospective_terminal\|append_stub_retrospective_intermediate" specfuse/loop/loop.py` | Stub-skeleton writers exist for the auto-close path (`loop.py:3575` area) — **reuse and generalize for dispatched closes**. |
| `grep -n "specfuse-lint" pyproject.toml` | CLI entry exists (`specfuse-lint = "specfuse.loop.lint_plan:main"`) — **extend with a `--closing` mode, no new binary**. |

Verdict: every mechanism this feature needs has an existing home. The new artifact is the shared
requirement registry (T01); everything else is refactor, extension, or reuse.

## Scope boundary

**IN.** The closing-requirement registry; `specfuse-lint --closing`; skeleton pre-creation in
`dispatch()` for `close` / `close-intermediate` / `plan-next` WUs (including the
`GATE-{N+1}-REVIEW.md` stub that kills #261); rewriting `close-discipline.md` §4 and the
closing-WU template prose to reference the lint instead of restating guard strings.

**OUT.**
- Per-criterion DoD state / incremental re-close — FEAT-2026-0056.
- Executable oracle contract — FEAT-2026-0057.
- Arm-time produces/boundary lint — FEAT-2026-0055.
- Any change to `gate_eval.py` / the auto-close predicate (FEAT-2026-0018's surface).
- Any **new** guard. This feature makes existing guards unfailable-by-accident; it adds none.
- Migration of already-drafted features. The mechanism is dispatch-time, so in-flight features
  inherit it when their close dispatches; stale guard-restating prose in old WU bodies is inert
  (T04 records this explicitly in `close-discipline.md` and the feature-conversion skill).

## Escalation-predicate satisfiability

n/a — no check severity is raised, no "zero issues" predicate is asserted on any external
input. `--closing` findings are advisory in-session output for the closing agent; the blocking
enforcement (post-squash guards) exists today and is only refactored, never widened.

## Design constraints carried from LEARNINGS

- **Verdict lint window** ([FEAT-2026-0020], [FEAT-2026-0070]): `lint_plan` fails a dispatched
  close WU mid-flight on an invalid verdict value. The skeleton therefore never writes a
  placeholder `verdict:` value; it leaves the field absent and the `--closing` lint reports the
  absence as an actionable finding. `assert_verdict_well_formed` stays the outcome-time owner.
- **Idempotency against in-flight artifacts**: a partially-written `RETROSPECTIVE.md` (earlier
  gates' sections present) is appended to, never clobbered; an existing `GATE-{N+1}-REVIEW.md`
  is left alone. Skeleton pre-creation must be safe to run on every dispatch, including
  re-dispatch after a failed attempt.

## Gate shape (1 gate — ceremony proportionality, docs/methodology.md §6)

Four substantive WUs ≤ the threshold: single gate, single terminal `close`, no
close-intermediate, no plan-next.

## Gate graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0054/T01
        file: WU-01-closing-requirement-registry.md
        depends_on: []
      - id: FEAT-2026-0054/T02
        file: WU-02-lint-closing-mode.md
        depends_on: [FEAT-2026-0054/T01]
      - id: FEAT-2026-0054/T03
        file: WU-03-dispatch-skeleton-precreation.md
        depends_on: [FEAT-2026-0054/T01]
      - id: FEAT-2026-0054/T04
        file: WU-04-contract-surfacing.md
        depends_on: [FEAT-2026-0054/T02, FEAT-2026-0054/T03]
      - id: FEAT-2026-0054/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0054/T04]
```

## Notes

- Correlation IDs: `FEAT-2026-0054/TNN`; commit trailer `Feature: FEAT-2026-0054/TNN`.
- If T03 lands before G1-CLOSE dispatches, this feature's own close exercises the skeleton —
  the driver here runs from source. Treat that as a bonus observation for the retrospective,
  not an acceptance criterion.
- Success measure for the portfolio (recorded here for the retrospective, verified on the next
  generator feature, not in this repo): closing-format refusal classes
  (`closing_deliverable_missing` on format-only assertions, `assert_gate_review_exists`) at
  zero occurrences.
