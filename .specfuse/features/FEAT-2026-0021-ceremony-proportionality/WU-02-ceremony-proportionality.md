---
id: FEAT-2026-0021/T02
type: implementation
effort: low
status: pending
attempts: 0
planned_cost_usd: 1.00
generated_surfaces: []
---

# Add the ceremony-proportionality size rule to draft-feature and methodology

**Objective.** Encode the rule "a feature with ≤4 planned substantive work
units drafts as a single gate with a single terminal `close`" in the
`draft-feature` skill (so the drafter applies it) and in `docs/methodology.md`
(so it is canonical). Documentation-only; no executable code changes.

**Context.** Part of FEAT-2026-0021, correlation ID `FEAT-2026-0021/T02`.
This is the feature's biggest cost lever: a baseline over 14 features showed
**43% of spend on closing ceremony**, worst on small features that paid a
multi-WU close on 1–2 substantive WUs. LEARNINGS[FEAT-2026-0005/G1] already
recorded the principle — *"closing-ceremony weight should scale with feature
size"* — but nothing in the drafter or the methodology encodes a threshold.
This WU adds it. The methodology already supports the single-gate terminal
`close` shape mechanically (methodology §3, §6; `PLAN.template.md`); this WU
only adds the *decision rule* for when to choose it. The existing
`gate_eval.py` auto-close predicate is the safety net: a single-gate feature
whose gate goes off-plan still gets the full close ceremony, so this rule
trades reflection only on features that stayed small AND on-plan. Binding
rules in `.specfuse/rules/` apply by reference. **Red-test exempt:**
documentation-only WU (`/authoring-work-units` §12 carve-out).

**Acceptance criteria.**

- `.specfuse/skills/draft-feature/SKILL.md` step 4 (gate skeleton) gains a
  size rule stating: when the feature's **planned substantive** WU count
  (types `implementation` / `qa_authoring` / `qa_execution` / `qa_curation`)
  is ≤ 4, draft a single gate with a single terminal `close` WU — no
  `close-intermediate`, no `plan-next`. Verify:
  `grep -Eiq "substantive.*(<=|≤) ?4|4 .*substantive" .specfuse/skills/draft-feature/SKILL.md`
  AND `grep -iq "single terminal close" .specfuse/skills/draft-feature/SKILL.md`.
- The draft-feature rule names the off-plan escape: a single-gate feature
  whose gate goes off-plan still runs the full close via the `gate_eval`
  predicate. Verify: `grep -iq "gate_eval\|off-plan\|off plan" .specfuse/skills/draft-feature/SKILL.md`.
- `docs/methodology.md` §6 (the gate cycle) gains a subsection documenting
  ceremony proportionality: the ≤4 threshold, that it keys on **planned**
  substantive count, and the off-plan safety net. Verify:
  `grep -iq "proportional" docs/methodology.md` AND a new heading line
  matches `grep -Eq "^#+ .*[Pp]roportional" docs/methodology.md`.
- The threshold is stated once as the canonical number in `methodology.md`
  and referenced (not re-defined with a different value) in `draft-feature`
  — one fact, one home. Both files state "4"; neither contradicts the other.

**Do not touch.** Any driver, predicate, or linter script under
`.specfuse/scripts/` (this is a drafting/documentation rule, not a
driver-enforced one — keep it authoring-layer); `.specfuse/templates/`; any
other feature folder; `.git/`. Edit only
`.specfuse/skills/draft-feature/SKILL.md` and `docs/methodology.md`. See
`.specfuse/rules/never-touch.md` for the full forbidden-path list.

**Verification.** Documentation WU; the `doc` gate (`artifact-changed`) plus
the grep assertions above are the real oracle (LEARNINGS[134-141]).
Additionally run, and require to pass:
- `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0021-ceremony-proportionality`
  exits 0 — this feature's own single-gate terminal shape must still lint
  clean after the rule lands.
- `python3 -m unittest discover -s tests` — confirms no test pins the
  methodology/skill prose this WU edits.

**Escalation triggers.** Emit `status: blocked` if: the methodology already
states a *different* proportionality threshold (surface the conflict rather
than silently overwriting); the `draft-feature` step-4 structure has no
coherent place for the rule without contradicting the existing "detail only
gate 1" forward-design move (the two must be reconciled — report the tension);
or encoding the rule would require a driver-script change to stay honest
(that means it is not actually authoring-layer — stop and report, it belongs
in the deferred driver-hardening feature). Blocked is respectable —
`result-contract.md` rule 4.
