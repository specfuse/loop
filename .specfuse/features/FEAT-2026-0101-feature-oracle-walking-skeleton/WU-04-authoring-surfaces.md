---
id: FEAT-2026-0101/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
oracle_env: macos_local
produces:
  - .specfuse/templates/GATE.template.md
  - plugins/specfuse/skills/draft-feature/SKILL.md
  - plugins/specfuse/skills/authoring-work-units/SKILL.md
  - docs/methodology.md
model: sonnet
effort: medium
gate_set: code
driver_version: 0.16.0
started_at: 2026-09-08T00:39:28.711342+00:00
duration_seconds: 1029.89
cost_usd: 1.824907
input_tokens: 122
output_tokens: 14893
---

# Make the oracle the drafted default across the authoring surfaces

**Objective.** Teach the template, the drafting skills and the methodology that
a gate declares one `feature_oracle`, so the next feature drafted gets one
without anyone remembering to ask.

**Context.** FEAT-2026-0101/T04; read `PLAN.md`, T01-T03. Four surfaces:

1. **`.specfuse/templates/GATE.template.md`** — the key with a one-line comment
   saying what it is and that it starts red.
2. **`/draft-feature`** — refuses to draft a gate without an oracle, and its
   gate-1 proposal step asks for one. This is where the "walking skeleton"
   framing belongs: the first implementation unit is the tracer bullet that
   makes the oracle runnable.
3. **`/authoring-work-units`** — the tracer-bullet rule: stubs are permitted in
   the unit that makes the oracle green and nowhere else.
4. **`docs/methodology.md`** — the key's one home, in the frontmatter reference
   beside `oracle_env`, `oracles`, `extra_gates`.

**Skills are canonical in `plugins/`.** The `.specfuse/skills/` copies are
generated from there. Edit the `plugins/` copy and regenerate; do not hand-edit
the generated copy and leave the canonical one stale. Rules and templates flow
the other way (`.specfuse/` → `specfuse/loop/data/`) — do not generalize one
direction to the other.

**The `plan-next` obligation is the honest half of a limit we cannot enforce.**
Nothing can decide whether gate N's oracle is *stronger* than gate N-1's —
that would mean comparing two shell commands for strength. So `plan-next` must
state in its review summary how the drafted gate's oracle advances the prior
gate's. That summary is already weighted toward doubt and already carries the
roadmap-anchor check, which is exactly where an unenforceable-but-important
judgement belongs. Write it as an obligation there, not as a lint rule.

**Acceptance criteria.**

- `grep -n "feature_oracle" .specfuse/templates/GATE.template.md` returns the key with its comment, and `.specfuse/VERSION`-mirrored template copies stay in sync: `python3 -m unittest tests.test_scaffold_data_in_sync tests.test_scaffold_resources -q` reports `OK`.
- `/draft-feature`'s SKILL.md states that a gate without a `feature_oracle` is not drafted, and names the tracer-bullet rule for the first implementation unit: `grep -c "feature_oracle" plugins/specfuse/skills/draft-feature/SKILL.md` returns at least 2.
- `/authoring-work-units` carries the tracer-bullet stub rule as a numbered rule consistent with its existing numbering: `grep -n "tracer bullet" plugins/specfuse/skills/authoring-work-units/SKILL.md` returns a hit.
- `plan-next`'s review-summary obligation is stated wherever `plan-next`'s summary contract lives (`docs/methodology.md` §7 and/or the skill): `grep -rn "advances the prior gate" docs/ plugins/` returns a hit.
- Both copies of every edited skill are identical: `diff -r plugins/specfuse/skills .specfuse/skills` reports no differences for the files this unit touched.
- `python3 -m unittest discover -s tests -q` reports `OK`, and `bash scripts/smoke-test.sh` exits 0.

**Do not touch.** `loop.py`, `lint_plan.py`, `closing_requirements.py`,
`lint_closing.py` (T01-T03 own them); `.specfuse/verification.yml` — this unit
adds no gate; the four WARN-ing gate files; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if the skills sync is
lock-file-mediated (`skills-lock.json`) and regenerating would touch entries
beyond the skills this unit edits — a broad lockfile rewrite is an operator
decision. Also block if `methodology.md` already documents a competing
feature-level oracle concept; two homes for one fact is the drift this rule
exists to prevent.
</content>
