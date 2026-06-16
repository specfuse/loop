---
id: FEAT-2026-0020/G2-CLOSE
type: close
status: done
attempts: 1
completed_out_of_loop: true
completed_note: "Terminal close performed out-of-loop 2026-06-16 (gate 2 had two hollow passes the loop couldn't be trusted to close cleanly). Wrote gate-2 + feature-arc terminal verdict in RETROSPECTIVE.md (incl. Cost analysis + What the loop did NOT verify), promoted 4 lessons to LEARNINGS.md, flipped PLAN status active->done, GATE-02 open->passed, roadmap row active->done. Feature verdict: DONE (readiness achieved); visibility flip is operator-side per FLIP-CHECKLIST.md."
generated_surfaces: []
oracle_env: macos_local
planned_cost_usd: 2.00
---

# Gate 2 close — terminal: retro + lessons + docs + feature-arc verdict

**Objective.** Terminal close for `FEAT-2026-0020`. Append a `## Gate 2` section to
`RETROSPECTIVE.md` covering the substantive gate-2 WUs (drafted by G1-PLAN), extend the
existing `## Cost analysis` table with gate-2 rows, append durable lesson(s) to
`.specfuse/LEARNINGS.md`, reconcile any docs/roadmap state, and write the terminal
**`# Feature-arc verdict`** answering: "is `main` publishable and is the public-flip
checklist sufficient that the operator can run it without an in-loop checkpoint?". Sets
`verdict: met` (or `met_locally` / `partially_met` / `not_met`) on this WU's frontmatter
so `fire_terminal_flips` fires.

**Context.** This is `FEAT-2026-0020/G2-CLOSE`. Terminal gate close (FEAT-2026-0015
contract; single-WU). Status is `draft` because G1-PLAN will revise depends_on and may
augment this body with gate-2-specific acceptance criteria once gate 2's substantive WUs
are drafted.

This stub guarantees the linter can identify gate 1 as non-terminal (per PLAN template
guidance). G1-PLAN updates the body and depends_on before this WU dispatches.

Binding rules: `.specfuse/rules/*.md`.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md` extended** with `## Gate 2` section. One sub-section per gate-2
   substantive WU: attempts, blockers, surprises.

2. **`## Cost analysis` table extended** with gate-2 rows: per-WU planned vs actual,
   delta %, aggregated feature total. Variance > 50% on any WU requires a one-paragraph
   rationale.

3. **`## What the loop did NOT verify` section extended** with gate-2 deferred
   criteria. Expected entries for this gate: the visibility flip itself (operator-side,
   not in-loop); any FLIP-CHECKLIST steps that are runbook-only and have no in-loop
   assertion. Write "(nothing new — every gate-2 acceptance criterion was verified in-
   loop)" when the list is empty. If > 2 entries OR > 30% of gate-2 criteria, flag
   feature sizing under `## What I'd change`.

4. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson from this gate OR an
   explicit `[FEAT-2026-0020/G2-CLOSE] nothing generalizes — gate ran on-plan` note.

5. **Docs + roadmap reconciliation.** Roadmap row's status column flips from `active` to
   `done` (driver fires `fire_terminal_flips` based on this WU's `verdict:` frontmatter).
   Any methodology-docs reference to the audit + flip pattern updated.

6. **`# Feature-arc verdict`** section at the bottom of RETROSPECTIVE.md. Answers the
   roadmap_goal question: is `main` publishable? Is the operator's flip path explicit
   enough to run unaided? `verdict:` frontmatter flag set accordingly:
   - `met` — audit verdict was green, hygiene files landed, FLIP-CHECKLIST is complete +
     dry-run-acknowledged.
   - `met_locally` — landed in-loop but post-merge verifications (PyPi tag from 0019,
     actual visibility flip) are deferred to operator action; expected outcome since this
     feature's exit gate IS the handoff.
   - `partially_met` / `not_met` — name what's missing.

7. **Existence check** before declaring complete:

   ```bash
   FEAT=.specfuse/features/FEAT-2026-0020-public-readiness-prep
   grep -qE '^## Gate 2' "$FEAT/RETROSPECTIVE.md"
   grep -qE '^# Feature-arc verdict' "$FEAT/RETROSPECTIVE.md"
   grep -qE '^verdict:' "$FEAT/WU-90-gate-2-close.md"
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0020' || \
     grep -q 'nothing generalizes' "$FEAT/RETROSPECTIVE.md"
   ```

   If any check fails, emit `status: blocked`.

**Do not touch.** Files this WU may edit/create:
- `RETROSPECTIVE.md` (append gate-2 section).
- `.specfuse/LEARNINGS.md` (append-only).
- Methodology docs iff a gate-2 WU surfaced something requiring reconciliation.
- This WU's frontmatter `verdict:` field.

No edits to: gate-1 or gate-2 substantive WU files, `loop.py`, other features, secrets,
`.git/`. Driver owns all git. See `.specfuse/rules/never-touch.md`.

**Verification.** `plannext` gate set (close-type → plannext gates per WU template
notes). Plus AC7 existence checks. Plus [FEAT-2026-0015/T07] closing-deliverable guards.

**Escalation triggers.**

1. **Verdict ambiguity.** If gate 2 landed everything except FLIP-CHECKLIST.md
   acknowledgement from the operator, set `verdict: met_locally` and call out the
   handoff explicitly. Do NOT set `met` if the operator-side rehearsal step is not
   yet recorded.
2. **Open audit findings resurface.** If gate-2 work inadvertently introduces a new
   audit finding (e.g. a CONTRIBUTING.md draft contains a personal reference), do NOT
   silently fix in this WU — emit `status: blocked`, re-arm a T0N hygiene WU in gate 2
   or in a follow-up feature, and only then close.
3. **Cross-feature coupling with FEAT-2026-0019.** If 0019 has begun work in parallel
   and the public visibility flip already happened, note in retro that the sequence was
   reversed (operator override) and set `verdict: met_locally`.
