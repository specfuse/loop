---
id: FEAT-2026-0003/G3-DOCS
type: docs
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.922754
input_tokens: 28
output_tokens: 13370
---

# Gate 3 documentation update

**Objective.** Reconcile project documentation and roadmap status
with what gate 3 actually delivered: the `Backend` lifecycle
seam, the `GitHubBackend` label-transition state backend, and the
live smoke against `RestoManagerApp/Backend#287`. Mark the
feature as `done` if all three gates passed.

**Context.** Read the gate-3 commits and the gate-3 section of
`RETROSPECTIVE.md` plus the smoke journal
`SMOKE-INIT-2026-0001-F06.md`. Update repo docs to describe the
delivered state-backend mechanism (how the loop signals a
feature's start/complete via GitHub issue labels), how
`make_backend(feat_fm)` selects between local and GitHub
backends, and the label scheme
(`loop:in-progress`/`loop:complete`). Update this feature's row
in `.specfuse/roadmap.md` to reflect gate 3's completion (and
the feature's overall `done` status if gates 1-3 all passed —
mirror gate 2's `.specfuse/roadmap.md` update style). The
handoff brief `docs/handoff-github-feature-pick.md` already
declares §3.4 ("report back") as gate 3's scope — update §3.4
to past-tense if as-built matches the planned shape, or document
divergences where it does not. The state-backend/lifecycle
contract may belong in a new short doc — judge whether to add
one or extend handoff §3.4 inline.

This unit reconciles surrounding docs only. The script, the
backend, and the smoke journal are owned by T05/T06/T07 — do not
re-edit them here.

**Acceptance criteria.**
1. Docs (README sections, `docs/handoff-github-feature-pick.md`,
   any `.claude/CLAUDE.md` cross-reference, possibly a new short
   `docs/state-backend.md`) describe the delivered state-backend
   mechanism as shipped (lifecycle hooks, factory selection,
   label scheme). Diverges from planned shape are explicitly
   called out.
2. The feature's row in `.specfuse/roadmap.md` reflects gate 3's
   completion. If gates 1-2-3 all passed and the smoke
   succeeded, flip the feature's `Status` column from `active`
   to `done` and update the prose section to past-tense
   summarizing all three gates. If the smoke surfaced a defect
   that gates the feature's `done` claim, leave status `active`
   and document what is outstanding.
3. The handoff brief `docs/handoff-github-feature-pick.md` §3.4
   ("Report back") is updated from planned ("Not yet
   delivered; gate 3's scope") to delivered, with the as-built
   shape described accurately.
4. Any doc change that implies a code change is needed is
   raised in the RESULT block (an escalation) rather than
   absorbed into code edits here.

**Do not touch.** Source behavior — `.specfuse/scripts/`
(including `loop.py`, `gh_features.py`, `adopt_feature.py`,
`gh_backend.py`), `.specfuse/skills/`, binding rules under
`.specfuse/rules/`, templates under `.specfuse/templates/`,
generated directories, secrets, `.git/`. This unit documents;
it does not change code or skills. `SMOKE-INIT-2026-0001-F06.md`
is owned by T07 — do not edit.

**Verification.** The `doc` gates in
`.specfuse/verification.yml`.

**Escalation triggers.** If a doc change implies a code change
is needed (e.g. the as-built `GitHubBackend` label scheme
mismatches what the handoff brief or orchestrator addendum
promised), raise it in the RESULT block rather than changing
code here — a code change is a follow-up feature, not this WU.
If the gate-3 retrospective's `## Multi-gate proof` subsection
indicates the loop's roadmap goal was not met (e.g. smoke
failed and the orchestrator-dispatch path is not actually
working end-to-end), the roadmap update must reflect that
truth — do NOT mark the feature `done` to keep the row tidy.
