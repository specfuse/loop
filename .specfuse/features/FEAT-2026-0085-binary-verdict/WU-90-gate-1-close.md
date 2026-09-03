---
id: FEAT-2026-0085/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
model: opus
effort: high
oracle_env: macos_local
auto_close_disabled: true
produces:
  - .specfuse/features/FEAT-2026-0085-binary-verdict/RETROSPECTIVE.md
---

# Gate 1 close — demonstrate the five behaviours, record the counts, verdict

**Objective.** Terminal close of FEAT-2026-0085: demonstrate each behaviour in
`GATE-01.md`'s definition of done on fixtures in this session, record the
before and after counts, and write `met` or `not_met`.

**Context.** Depends on T01-T05. Binding: `.specfuse/rules/close-discipline.md`
as T05 rewrote it. The driver owns the terminal `PLAN.md status` flip. Baseline
numbers are in `PLAN.md` § Notes. This close is itself the first close bound by
the binary rule: if any behaviour cannot be demonstrated, the verdict is
`not_met` and `FOLLOW-UPS.md` names the criterion. Run `specfuse lint --closing`
before reporting `complete`.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries `## Gate 1` and a `## Measurements` table, before and after: `VERDICT_VALUES` size, files naming `met_locally`, test files referencing hedge machinery, standing hedged closes in this repository (count and list), and the exit status of each of the five fixture demonstrations, each next to the command run in this session.
- `## Retrospective` answers: which of the 42 standing hedged closes in the field this repository owns and what the migration note would have each do; and whether the `human` unit's brief was printable from real unit text.
- `## Cost analysis` reconciling `planned_cost_usd` ($35.00, per-WU) against `events.jsonl`, delta named, restart count named.
- `## Consumer-visible contract changes`: `VERDICT_VALUES` narrowed, `close-j` and `close-g` removed, `close-m` added, `FOLLOW-UPS.md` and `type: human` introduced, `/accept-hedged-close` removed, two new labels. Every scaffold consumer is affected; the `CHANGELOG.md` entry T05 wrote is the same list.
- `## Lessons`: one entry at most.
- Oracles re-run fresh: `python3 -m unittest discover -s tests -q` reports `OK`; `bash scripts/smoke-test.sh` exits 0; `specfuse lint` over every feature folder reports zero ERROR.

**Do not touch.** Source, tests, rules, docs, skills (T01-T05 own them);
`.git/`, secrets. This WU writes only its close record.

**Verification.** The `plannext` gate set plus the oracles above.

**Escalation triggers.** Emit `status: blocked` if `GATE-01.md`'s behaviours
pass on fixtures but `grep` still finds hedged vocabulary in `plugins/`,
`.specfuse/rules`, `.specfuse/templates`, or `.specfuse/skills`, or anywhere in
`specfuse/` outside the legacy-tolerance surface `GATE-01.md` names: prose and
mechanism disagree, and the close cannot pick one.
