---
id: FEAT-2026-0085/T05
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.00
model: opus
effort: high
oracle_env: macos_local
produces:
  - .specfuse/rules/close-discipline.md
  - docs/methodology.md
  - CHANGELOG.md
gate_set: code
driver_version: 0.14.0
started_at: 2026-09-03T11:39:21.314924+00:00
duration_seconds: 1377.634
cost_usd: 7.326092
input_tokens: 198
output_tokens: 46871
---

# Rewrite close-discipline for a binary verdict, remove the acceptance skill, document migration

**Objective.** Make the prose match the mechanism: `close-discipline.md` §2
describes `FOLLOW-UPS.md` and the `human` unit instead of hedged kinds;
`/accept-hedged-close` is removed; every doc, gloss, and template that named
`met_locally` or `partially_met` is corrected; and standing hedged closes get a
migration note.

**Context.** FEAT-2026-0085/T05; read `PLAN.md`. New §2 in three sentences:
the verdict is `met` or `not_met`; on `not_met` the close writes
`FOLLOW-UPS.md`, one entry per failed criterion, and the driver files the
issues; a criterion that needs a human is a `type: human` unit placed before
the close, and a criterion that needs production is a `## Post-merge
checklist` line in `PLAN.md`, never a criterion. §5 stays. Delete
`plugins/specfuse/skills/accept-hedged-close/`, its vendored copy, the
`.claude/skills` symlink, its `docs/skills.md` entry, and
`tests/test_accept_hedged_close_skill.py` / `_headline.py`. Fix
`human-output.md`'s gloss table, `docs/methodology.md` §3 (replace the three
hedged-verdict paragraphs), `docs/glossary.md`, `docs/lifecycles.md`, the
`gate-status` and `wrap-feature` references, and the close-obligations text in
`WU.template.md` as 0084/T02 left it. Migration section in
`docs/methodology.md` titled "Migrating a hedged close": for each standing
`met_locally` / `partially_met` close, either discharge and edit the verdict
to `met` then run `--recheck-verdict`, or edit it to `not_met`, write
`FOLLOW-UPS.md` from the old follow-up record, and re-arm the failing unit;
`/accept-hedged-close` no longer exists. `CHANGELOG.md` Unreleased gets a
`breaking` entry. Sync scripts for rules, docs, and skills.

**Acceptance criteria.**

- `grep -rl "met_locally\|partially_met" specfuse/ plugins/ .specfuse/rules .specfuse/templates .specfuse/skills tests/ | wc -l` reports 0.
- `grep -rl "met_locally\|partially_met" docs/ | sort` prints exactly `docs/methodology.md`, and `grep -c "## Migrating a hedged close" docs/methodology.md` reports 1.
- `test -e plugins/specfuse/skills/accept-hedged-close` exits 1; `test -e .claude/skills/accept-hedged-close` exits 1; `grep -c "accept-hedged-close" docs/skills.md` reports 0.
- `grep -c "FOLLOW-UPS.md" .specfuse/rules/close-discipline.md` reports at least 1 and `grep -c "kind:" .specfuse/rules/close-discipline.md` reports 0 outside §5.
- `python3 -m specfuse.loop.changelog --check` (or the repo's equivalent named in `specfuse/loop/changelog.py`) accepts the new Unreleased entry tracing to `FEAT-2026-0085`.
- `bash scripts/sync-scaffold.sh` leaves `git status --porcelain specfuse/loop/data .specfuse/skills` empty; `tests/test_scaffold_data_in_sync.py` and `tests/test_skills_vendored_in_sync.py` pass.

**Do not touch.** `specfuse/loop/*.py` except `changelog.py` if its check needs
a fixture; `close-discipline.md` §5; `.specfuse/features/*/RETROSPECTIVE.md`
(history stays as written); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
commands above.

**Escalation triggers.** Emit `status: blocked` if a skill other than
`accept-hedged-close` depends on the hedged record's shape to function; name
it rather than editing it here.
