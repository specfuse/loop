---
id: FEAT-2026-0007/T06
type: implementation
model: claude-sonnet-4-6
effort: high
status: draft
attempts: 0
---

# Defaults-by-WU-type policy (with Haiku guidance)

**Objective.** When a WU's `model` or `effort` frontmatter field is absent,
the loop applies a sensible default keyed off the WU's `type`. The current
fallback (`model` mandatory; `effort` defaults to `medium` regardless of type)
forces every author to think about both fields for every WU — cheap WUs end up
on Sonnet at `medium` simply because nobody had a reason to override.

**Context.** This is `FEAT-2026-0007/T06`. Reads:

- `WorkUnit` dataclass and `load_wu` at `.specfuse/scripts/loop.py:67` and
  surrounding lines — where `effort: str = "medium"` was added by T02 and
  where `model` is currently required (no default).
- `lint_plan.py` `MODEL_ALIASES`, `VALID_EFFORT`, and `VALID_TYPES`
  (`.specfuse/scripts/lint_plan.py:41,53,54`) — the linter validates the
  values but does not default them.
- Gate 1's retrospective: T01–T03 succeeded on Sonnet in one attempt; T04
  used Opus (and per the retrospective's CRITICAL FINDING, its code never
  landed — irrelevant to the policy table, but cited so the table reflects
  what *was supposed* to happen, not what actually shipped). Cheap closing
  WUs (G1-LESSONS at $0.20 / 90s) confirm Sonnet handles synthesis at low
  effort.

Defaults are **policy**, not behavior change for declared values: a WU that
declares `model: opus` still gets Opus. The new behavior only fires when
the field is absent.

Reference the binding rules under `.specfuse/rules/`. The driver owns git;
edit files only.

**Acceptance criteria.**
1. New module-level constants in `.specfuse/scripts/loop.py`:
   ```
   MODEL_BY_TYPE = {
       "implementation": "sonnet",
       "retrospective":  "sonnet",
       "lessons":        "sonnet",
       "docs":           "sonnet",
       "plan-next":      "opus",
       "close":          "opus",
   }
   EFFORT_BY_TYPE = {
       "implementation": "medium",
       "retrospective":  "low",
       "lessons":        "low",
       "docs":           "low",
       "plan-next":      "high",
       "close":          "high",
   }
   ```
   The two tables together cover every value in `lint_plan.VALID_TYPES`.
2. `load_wu` is changed: `model` becomes optional. When frontmatter omits
   `model`, the loaded value is `MODEL_BY_TYPE[type]`. When frontmatter
   omits `effort`, the loaded value is `EFFORT_BY_TYPE[type]` (replacing
   the T02 dataclass default of `"medium"`).
3. The `effort: str = "medium"` dataclass default stays as a safety net for
   unknown future types not yet in the table; the linter still rejects any
   unknown `type` at lint time, so the safety net is unreachable in practice.
4. `lint_plan.py` treats `model` as optional (was: required) when the WU's
   `type` is in `MODEL_BY_TYPE`. When absent it is valid; when present it is
   validated as today (alias or full-id). No change to error messages for
   present-but-invalid values.
5. `WU.template.md` frontmatter is updated: the `model:` and `effort:` lines
   are commented out as `# model: <override>` / `# effort: <override>` with
   a note pointing to the two tables, signalling that the fields are
   optional and the default is type-keyed.
6. **Haiku policy doc.** Add a new section `## Haiku — when (and when not)`
   to `.specfuse/skills/authoring-work-units/SKILL.md` (or create it if
   absent — confirm via Glob first) covering:
   - Recommended for: `docs` (small reconciliation gates), `lessons`
     (append-only synthesis under ~5 entries).
   - Discouraged for: `implementation`, `plan-next`, `close`, and any
     `retrospective` of a gate with > 3 substantive WUs.
   - Rationale: Haiku 4.5 handles low-volume synthesis and pattern-matched
     edits cheaply; multi-file forward design or cross-WU reasoning
     regresses on Haiku. Source the rationale from the gate-1 cost table
     (`RETROSPECTIVE.md`: cheap closing WUs were already in the $0.20
     range; Haiku would compress further).
   - Override mechanic: opt-in only via explicit `model: haiku` in WU
     frontmatter; never a default.
7. New unit tests in `tests/test_loop_defaults_by_type.py`:
   (a) WU file with no `model:` and `type: implementation` loads with
       `wu.model == "sonnet"`.
   (b) WU file with no `effort:` and `type: plan-next` loads with
       `wu.effort == "high"`.
   (c) WU file with `model: opus` declared on a `type: implementation` WU
       loads with `wu.model == "opus"` (override wins).
   (d) `lint_plan.py` exits 0 on a WU file that omits `model:` entirely
       (regression on existing valid fixture pattern per LEARNINGS
       `[FEAT-2026-0005/G1-LESSONS]`).
8. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`): the
   Verification section below names `python3 -c "from loop import
   MODEL_BY_TYPE, EFFORT_BY_TYPE"` to confirm the constants exist before
   declaring complete.

**Do not touch.** Exactly 5 files change: `.specfuse/scripts/loop.py`,
`.specfuse/scripts/lint_plan.py`, `.specfuse/templates/WU.template.md`,
`.specfuse/skills/authoring-work-units/SKILL.md` (or its location — confirm
path before editing), and one new test file `tests/test_loop_defaults_by_type.py`.
No edits to: existing WU files under `.specfuse/features/` (the policy
applies prospectively; back-filling defaults into existing WUs is out of
scope), `.specfuse/verification.yml`, binding rules, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
plus the existence smoke check named in AC 8. Run the smoke check first;
if `ImportError` fires, the constants are not yet authored — emit
`status: blocked` rather than claim complete.

**Escalation triggers.**
1. **Completeness.** If `MODEL_BY_TYPE` or `EFFORT_BY_TYPE` is absent from
   `loop.py` after your edits, emit `status: blocked` — do not claim
   complete. (Mirrors the T04 failure mode flagged in
   `RETROSPECTIVE.md`.)
2. **Skill path.** If `.specfuse/skills/authoring-work-units/SKILL.md` is
   absent at the expected path and Glob reveals no nearby authoring guide,
   create it at the canonical path with only the Haiku section content
   rather than scattering the policy elsewhere; flag in RESULT block that
   the file was created (not edited) so the reviewer can confirm intent.
3. **Linter back-compat.** If making `model` optional in `lint_plan.py`
   would silently accept a malformed YAML structure that the current strict
   check rejects (e.g. `model:` with empty value), narrow the change to
   "absent key → default; present-but-empty → reject" and add a test for
   the present-but-empty case.
