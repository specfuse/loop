---
id: FEAT-2026-0070/G2-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
auto_close_disabled: true
---

# Gate 2 close — terminal close for FEAT-2026-0070

**Objective.** Close the feature: retrospective, lessons, docs, and the terminal
feature-arc verdict, in one session.

**Context.** This is `FEAT-2026-0070/G2-CLOSE`, the terminal close. Scaffolded at
feature-drafting time so `lint_plan.py` read gate 2 as the non-empty terminal gate; gate 1's
`G1-PLAN` has since drafted gate 2's four substantive WUs above this entry, set this WU's
real `depends_on`, and added AC11–AC12 below. `GATE-02-REVIEW.md` is the arming record.

Gate 2's definition of done, from `GATE-02.md`: an auto-closed gate leaves a concrete
deferred-verification worklist, and a terminal close that ignores it is visible rather
than silent. What ships: `T05` extracts the WU section slicers into
`specfuse/loop/_wu_sections.py`; `T06` makes both auto-close stub writers enumerate the
gate's unwalked acceptance criteria and emit a `<!-- specfuse:autoclose-debt gate=N … -->`
marker; `T07` adds the post-pass invariant `assert_autoclose_debt_reconciled` that reads
that marker; `T08` predicts `T07`'s refusal as a `lint_plan` WARN at arm time.

**Read `close-discipline.md` §4 before writing** — it lists the exact strings the driver
checks, including the `## Cost analysis` heading required on a `met` verdict and the
`verdict:` **frontmatter** field. Those guards run after dispatch.

**Acceptance criteria.** Refined by `G1-PLAN`; these are the obligations that hold
regardless of what gate 2 turns out to contain.

1. `RETROSPECTIVE.md` covers the full feature arc — both gates, per-WU outcomes,
   surprises, and `## What I'd change`.
2. **`## Cost analysis`** present, reconciling `PLAN.md`'s $32.00 and every WU's
   `planned_cost_usd` against actual spend from `events.jsonl`, with the delta named.
   Reconcile against the **as-drafted** figure; do not re-baseline onto the feature's own
   overrun (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`). Split the variance by cause rather
   than reporting one blended percentage.
3. **`## What the loop did NOT verify`** present, enumerating every acceptance criterion
   whose verification was deferred — the criterion, why, and where verification actually
   happens. Required even when empty. If the list exceeds 2 entries or 30% of the feature's
   criteria, flag the gate sizing under `## What I'd change`.
   **One entry is known at drafting time:** `/accept-hedged-close` is a skill, and a skill
   is verified by an operator running it against a real hedged feature — not by a
   dispatched session. Structural verification (registration, sync, text assertions) is not
   the same claim.
4. **Oracles re-run fresh** (`close-discipline.md` §1): every oracle the feature's criteria
   name, full commands, exit codes read directly, never a producing WU's self-report.
5. **The one-owner property is audited, not assumed.** `grep -c "def fire_terminal_flips"
   specfuse/loop/loop.py` returns `1`, and no skill or entry point added by this feature
   writes `PLAN.md status`, the gate status, or the roadmap row directly. This is the
   feature's central constraint (`[FEAT-2026-0023/G1-CLOSE]`) and the terminal close is its
   last checkpoint. **A feature that shipped every WU green while splitting terminal-state
   ownership has failed**, and the verdict must say so.
6. **Hedged follow-up record** (§2): on `met_locally`, a named record per unmet criterion —
   the criterion, why unverifiable here, and the exact re-run condition that upgrades it to
   `met`. Note the recursion: this feature ships the path *out* of a standing hedge, so if
   its own verdict is hedged, `/accept-hedged-close` is what discharges it. Say so plainly
   rather than leaving the irony unremarked.
7. **Consumer-visible contract changes** (§3): enumerate every addition, removal, and
   rename across the whole feature, or write exactly
   `n/a — no consumer-visible contract change`. This will **not** be `n/a` — carry gate 1's
   list forward and add gate 2's. Block on human acknowledgment.
8. Durable lessons promoted to `.specfuse/LEARNINGS.md`, tagged `[FEAT-2026-0070/G2-CLOSE]`.
9. The roadmap detail section reflects the feature's real outcome. Issues #226, #243, and
   #241 are each referenced with their resolution, and #243's two held candidates (the
   intermediate roadmap status, and pre-declaring the ceiling at draft time) are restated as
   still-open with a pointer, so holding them does not read as closing them.
10. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0070-terminal-flip-contract`
    passes.
11. **`T07`'s own invariant is satisfied by this close, and the check is reported.** This is
    the terminal close of the feature that ships `assert_autoclose_debt_reconciled`, so it
    runs against itself. Gate 1 did **not** auto-close
    (`WU-90-gate-1-close-intermediate.md` carries `auto_close_disabled: true` and ran a real
    session), so no debt marker exists and the invariant passes vacuously. **Say that
    explicitly rather than letting a green post-pass read as evidence the guard works** —
    the guard's real evidence is `T07`'s negative and positive controls, and this close
    must not present a vacuous pass as a second one.
12. **The satisfiability claim is re-checked against the tree, not inherited from
    `GATE-02-REVIEW.md`.** Scan every `.specfuse/features/*/RETROSPECTIVE.md` for the debt
    marker, report the count, and state what `assert_autoclose_debt_reconciled` reports on
    each hit. The plan-time answer was zero across 11 auto-closing features; a different
    answer at close time is a finding, not a formality.

**Do NOT** add a "flip `PLAN.md status` to `done`" criterion. The driver owns the terminal
PLAN flip via `fire_terminal_flips`, gated on `verdict_permits_terminal_flips`. A manual
agent flip is redundant and re-opens the divergence this feature exists to close — which
would be a particularly poor way to end it.

`auto_close_disabled: true` is set because AC4, AC5, and AC7 are load-bearing close
obligations the auto-close predicate must not skip.

**Do not touch.** The production surfaces — this WU closes, it does not implement.
`PLAN.md`'s `status` field. `.git/`, secrets. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set the driver runs for `type: close`, plus the fresh
oracle re-runs in AC4, the greps in AC5, and the plan lint in AC10.

**Escalation triggers.** Emit `status: blocked` if a fresh oracle re-run disagrees with a
WU's self-reported outcome, if AC5's audit finds more than one terminal-state writer, or if
the human acknowledgment AC7 requires is unavailable in this session. Prefer a
`met_locally` verdict with an honest hedged-follow-up record over a `met` verdict that
overstates. Blocked is a respectable outcome (`result-contract.md` rule 4).
