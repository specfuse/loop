---
id: FEAT-2026-0018/G1-PLAN
type: plan-next
effort: high
status: draft
attempts: 0
planned_cost_usd: 1.50
generated_surfaces: []
---

# Gate 1 plan-next — draft gate 2's substantive WUs

**Objective.** Author gate 2's substantive WU files (T04, T05, T06)
and write `GATE-02-REVIEW.md` summarizing what gate 1 produced,
what gate 2 should produce, and any open verifications for the
operator to check before arming. Updates `PLAN.md`'s gate-2
`work_units` graph with real `depends_on` edges.

**Context.** This is `FEAT-2026-0018/G1-PLAN`. Follows
G1-CLOSE-INTERMEDIATE. Drafts gate 2 from gate 1's retrospective +
lessons + this feature's overall design (PLAN.md).

Gate 2's expected scope (per PLAN.md):
- **T04** — Driver integration at terminal gate boundary.
  Calls `gate_eval.evaluate_auto_close` at the
  `set_gate(awaiting_review)` site in `loop.py`. On auto + terminal:
  write stub `RETROSPECTIVE.md`, skip `close` WU dispatch, call
  `fire_terminal_flips`. FEAT-2026-0017's
  `assert_terminal_flips_fired` invariant guard STILL fires on
  auto path. Write `auto_close_decision` event to events.jsonl.
- **T05** — Driver integration at intermediate gate boundary
  (option A). On auto: skip `close-intermediate` WU dispatch but
  DO dispatch `plan-next` WU (so next gate gets drafted). Append
  gate-section stub to RETROSPECTIVE.md.
- **T06** — `--force-full-close <feature-id>` CLI flag +
  `auto_close_disabled: true` PLAN.md frontmatter override. Both
  bypass predicate consultation; existing close path runs.

Reference binding rules at `.specfuse/rules/`. The driver owns
all git; edit files only.

**Acceptance criteria.**

1. **Gate 2 WU files drafted** (status: `draft`):
   - `WU-04-driver-terminal-wiring.md` (T04)
   - `WU-05-driver-intermediate-wiring.md` (T05)
   - `WU-06-force-full-close-flag.md` (T06)

   Each file follows `.specfuse/templates/WU.template.md` and
   the per-WU craft in
   `.specfuse/skills/authoring-work-units/SKILL.md`:
   - Five required sections (Context, Acceptance criteria, Do
     not touch, Verification, Escalation triggers).
   - Symbol-existence checks in Verification (per §9) for any
     new functions/constants introduced.
   - Completeness escalation triggers (per §9).
   - Hygiene-WU pattern documented if any T0NH precursor is
     needed (per §7).
   - For driver-integration WUs (T04, T05): a §10
     helper-duplication pre-flight grep enumerating existing
     close-path symbols in `loop.py`
     (`fire_terminal_flips`, `assert_terminal_flips_fired`,
     `verdict_permits_terminal_flips`,
     `close_wu_for_terminal`).

2. **`planned_cost_usd` on each new WU** matches PLAN.md's
   planned-cost table (T04 $2.50, T05 $2.20, T06 $0.80).

3. **`PLAN.md` gate-2 `work_units` graph updated** with real
   `depends_on` edges:
   - T04 depends_on: [T01, T02, T03] (gate 1's substantives)
     — actually depends_on can be empty here since gate 1 is
     a hard barrier. Driver enforces gate-1 done before any
     gate-2 dispatches; explicit cross-gate deps are
     redundant. Use `depends_on: []` for the first gate-2
     substantive.
   - T05 depends_on: [T04] (must land terminal-wiring first;
     intermediate-wiring reuses the predicate-call site).
   - T06 depends_on: [T05] (override hooks both wiring sites).
   - G2-CLOSE-INTERMEDIATE depends_on: [T04, T05, T06].
   - G2-PLAN depends_on: [G2-CLOSE-INTERMEDIATE].

4. **`GATE-02-REVIEW.md`** written at the feature folder root.
   Sections:
   - **Gate-1 summary** — one paragraph: what shipped, cost,
     auto-close-eligibility-of-self check on `gate_eval`
     against gate 1 (run T03's CLI on this very feature and
     paste the output).
   - **Gate-2 substantive WUs** — one paragraph per WU
     summarizing what it ships and why this scope.
   - **Open verifications** — list of decisions the operator
     should check before flipping `draft` → `pending`. Likely
     items:
       - **Driver wiring-site precise location.** T04's spec
         names "the `set_gate(awaiting_review)` site
         (loop.py:2005–2015)" — verify the line range is still
         accurate at arming time (loop.py evolves) and update
         T04's body if not.
       - **Stub `RETROSPECTIVE.md` content shape.** Confirm
         the stub template (probably YAML-like metrics block
         + one-line "auto-closed, on-plan" header) is what the
         hollow-pass guard's `assert_retrospective_exists`
         accepts — review FEAT-2026-0015/T07's regex if the
         guard checks for specific sections.
       - **WU lifecycle for auto-skipped close WUs.**
         Confirm `status: done` + `auto_close: true`
         frontmatter flag is the right shape (vs adding a new
         `skipped_auto` status). Affects `/gate-status`,
         `/wrap-feature`, lint, downstream tools — check each.
       - **Plan-next dispatched on intermediate auto-close.**
         Confirm option A (plan-next still runs) is still the
         right call after gate-1 retrospective evidence. If
         backtest implies option B (drafts upfront) or C
         (intermediate can't auto-close) is better, flag it.
   - **Cross-repo contracts** — table per
     `[FEAT-2026-0003/G3-LESSONS]`. For this gate, mostly
     internal — invented values: stub RETROSPECTIVE.md template
     content, frontmatter flag names (`auto_close`,
     `auto_close_reasons`, `auto_close_disabled`),
     `auto_close_decision` event-type string. Each row carries
     authoritative source (this feature's own docs / PLAN.md)
     and a checked/unchecked status.

5. **Predicate self-check.** Run
   `python3 .specfuse/scripts/gate_eval.py backtest
   FEAT-2026-0018 --gate 1` and paste the output into
   GATE-02-REVIEW.md's gate-1 summary. This is the first
   live use of T03's CLI on this very feature — exercises
   the recursive-dogfood property of gate 1's deliverable.
   (Gate 1 close runs through the OLD path so this output
   isn't acted on — but capturing it documents the predicate
   would have decided.)

6. **Existence check** before declaring complete:

   ```bash
   # a. Gate-2 WU files exist
   test -f .specfuse/features/FEAT-2026-0018-auto-close-predicate/WU-04-driver-terminal-wiring.md
   test -f .specfuse/features/FEAT-2026-0018-auto-close-predicate/WU-05-driver-intermediate-wiring.md
   test -f .specfuse/features/FEAT-2026-0018-auto-close-predicate/WU-06-force-full-close-flag.md

   # b. GATE-02-REVIEW.md exists and is non-empty
   test -s .specfuse/features/FEAT-2026-0018-auto-close-predicate/GATE-02-REVIEW.md

   # c. PLAN.md gate-2 work_units have real depends_on (not [])
   #    for substantive WUs (closing WUs only depend on substantives,
   #    so their depends_on stays referencing real ids)
   grep -A 20 "gate: 2" .specfuse/features/FEAT-2026-0018-auto-close-predicate/PLAN.md | grep -qE 'FEAT-2026-0018/T0[4-6]'

   # d. lint_plan.py passes on the feature folder
   python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0018-auto-close-predicate/

   # e. Predicate self-check ran (output captured in review)
   grep -q 'predicate=v1' .specfuse/features/FEAT-2026-0018-auto-close-predicate/GATE-02-REVIEW.md

   # f. Each gate-2 WU has all five required sections
   for f in .specfuse/features/FEAT-2026-0018-auto-close-predicate/WU-0[4-6]-*.md; do
     for sec in '^\*\*Context\.\*\*\|^**Context.**' '^\*\*Acceptance criteria\.\*\*\|^**Acceptance criteria.**' '^\*\*Do not touch\.\*\*\|^**Do not touch.**' '^\*\*Verification\.\*\*\|^**Verification.**' '^\*\*Escalation triggers\.\*\*\|^**Escalation triggers.**'; do
       grep -qE "$sec" "$f" || { echo "missing section $sec in $f"; exit 1; }
     done
   done
   ```

   If any check fails, emit `status: blocked` naming the
   failing check. Do NOT flip the WU `status` field as a
   substitute for drafting the gate-2 WUs.

**Do not touch.** Files this WU may edit/create:
- `WU-04-driver-terminal-wiring.md` (new)
- `WU-05-driver-intermediate-wiring.md` (new)
- `WU-06-force-full-close-flag.md` (new)
- `GATE-02-REVIEW.md` (new)
- `PLAN.md` (gate-2 `work_units` graph only — do NOT modify
  feature frontmatter, gate-1 work_units, or gate-3 scaffold)

No edits to: `gate_eval.py`, its tests, `loop.py`, other
features, skills, secrets, `.git/`. Driver owns all git. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in
`.specfuse/verification.yml`. Plus AC6 existence checks. Plus
`lint_plan.py` clean on the feature folder.

**Escalation triggers.**

1. **Gate-2 scope ambiguity surfaced by gate-1 retrospective.**
   If the retrospective revealed that one of T04/T05/T06's
   premises is wrong (e.g., the predicate API needs revision,
   or option A is no longer the right intermediate-close
   choice), emit `status: blocked` with the specific finding
   in the RESULT block. The operator updates the plan; this
   WU does not unilaterally re-scope gate 2.
2. **Driver wiring site changed.** If `loop.py`'s
   `set_gate(awaiting_review)` site (currently ~2005–2015) has
   moved or been refactored since this feature was drafted,
   T04's body needs the updated line reference. Catch it
   here at draft time — name the new location in T04's body
   and in GATE-02-REVIEW.md's Open verifications.
3. **Stub-RETROSPECTIVE shape uncertain.** The hollow-pass
   guard's `assert_retrospective_exists` was designed against
   ceremony-written retrospectives. If the stub shape is
   borderline (e.g., empty bullets, no gate section), name
   the concern in GATE-02-REVIEW.md and flag T04's body to
   verify against the guard's regex before finalizing.
4. **Cross-repo invented values.** For each invented string
   value (frontmatter flag names, event type names, stub
   template content), confirm against this feature's PLAN.md
   and prior LEARNINGS — don't invent shapes that conflict
   with existing patterns. Flag any in the Cross-repo
   contracts table for operator verification at arming time
   (per authoring-work-units §8).
