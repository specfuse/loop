---
id: FEAT-2026-0054/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
oracle_env: macos_local
produces:
  - specfuse/loop/data/rules/close-discipline.md
  - specfuse/loop/data/templates/WU.template.md
---

# Point the prose at the machinery — delete the guard-defensive boilerplate

**Objective.** The closing contract's human-facing surfaces (rules, templates, skills) point at
`specfuse-lint --closing` and the dispatch skeleton instead of restating guard strings — so the
contract has one home and closing-WU prompts stop carrying ~40% defensive boilerplate.

**Context.** Gate 1 of FEAT-2026-0054, depends on T02 and T03 (the machinery must exist before
prose can delegate to it). Canonical scaffold sources live under `specfuse/loop/data/` and
`plugins/specfuse/skills/`; this repo's own `.specfuse/` mirrors sync via
`scripts/sync-scaffold.sh` — edit canonical, then sync (see LEARNINGS: skills canonical in
plugins/). Binding rules: `.specfuse/rules/result-contract.md`, `never-touch.md`.

Red-test exempt: documentation/template/rules prose only — no runtime behavior introduced
(`/authoring-work-units` §12 pure-data carve-out).

**Acceptance criteria.**

- `specfuse/loop/data/rules/close-discipline.md` §4 no longer enumerates literal guard strings
  as the authoring surface; it states the two mechanical surfaces (skeleton pre-created at
  dispatch; `specfuse-lint --closing` as the mandatory pre-report check) and keeps a short
  pointer to `closing_requirements.py` as the registry of record. Grep-checkable: the §4 table
  of per-guard literal strings is gone.
- The same section records the migration posture: already-drafted features need no conversion —
  skeleton applies at dispatch; stale guard-restating prose in old WU bodies is inert and
  advisory-removable.
- `specfuse/loop/data/templates/WU.template.md`'s "Close obligations" block: the blockquote
  warning about literal post-hoc string matching is replaced by one line requiring
  `specfuse-lint --closing` to pass (exit 0) before the closing WU reports; the §1–§3 substance
  obligations (fresh oracles, hedged record, contract-change enumeration) stay verbatim.
- `plugins/specfuse/skills/authoring-work-units/SKILL.md` and
  `plugins/specfuse/skills/draft-feature/SKILL.md`: closing-WU authoring guidance references
  the lint instead of guard-string folklore; `plugins/specfuse/skills/feature-conversion/SKILL.md`
  gains the one-line no-migration-needed note.
- `scripts/sync-scaffold.sh` run; canonical and `.specfuse/` / `.claude` mirrors agree (the
  FEAT-2026-0072 symlink/sync guards stay green).
- Full suite green — including the structural-invariant guard tests that assert
  scaffold-mirror consistency.

**Do not touch.** Driver code (`specfuse/loop/*.py` — T01/T02/T03 own it; this WU is prose
surfaces only); `.specfuse/rules/*` directly (sync from canonical instead); other features'
folders; `.git/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
`specfuse-lint --closing` still exits 0 on the FEAT-2026-0072 done-feature fixture (prose
change must not have altered machine behavior — it cannot, but the run is the proof).

**Escalation triggers.** If deleting a guard-string restatement would remove information the
lint does not yet surface (a requirement the registry missed), stop and emit `status: blocked`
naming it — the fix is a T01/T02 gap, not keeping the prose. If the canonical location of any
template/skill is ambiguous (data/ vs plugins/ vs .specfuse/), blocked rather than guessing.
