---
id: FEAT-2026-0007/T01
type: implementation
model: claude-sonnet-4-6
status: done
attempts: 1
duration_seconds: 216.217
cost_usd: 0.746002
input_tokens: 21
output_tokens: 9703
---

# Accept model family alias in WU frontmatter

**Objective.** The loop accepts model family aliases (`sonnet`, `opus`,
`haiku`) in WU frontmatter and passes them to `claude -p --model` unchanged,
in addition to the existing full IDs.

**Context.** This is `FEAT-2026-0007/T01`. `loop.py` defines
`CLAUDE_CMD = ["claude", "-p", "--model", "{model}"]` and `load_wu` reads
`fm.get("model", "claude-sonnet-4-6")`. `claude -p --help` confirms `--model`
accepts aliases (`sonnet`, `opus`, `haiku`) as well as full model IDs, so the
loop only needs to widen its accepted set in the data path — no
client-side expansion. Resolved-model capture (recording which concrete model
the CLI selected) is Gate 2's T08, not this WU. Reference the binding rules
under `.specfuse/rules/`; honor `result-contract.md` and `never-touch.md`. The
driver owns all git; edit files only.

**Acceptance criteria.**
1. `WorkUnit.model` (loop.py dataclass) accepts any of: `sonnet`, `opus`,
   `haiku`, or any full ID matching the existing pattern. Loop performs no
   expansion — the string is passed to `--model` verbatim.
2. `load_wu`'s default model is unchanged (`claude-sonnet-4-6`) so no
   existing WU file changes behavior.
3. `lint_plan.py` allows the three new aliases in addition to full IDs.
   The allowed set is an explicit set/list, not a loosened regex.
4. `WU.template.md`'s frontmatter notes document the three family aliases
   under the `model:` field and state that family aliases resolve to the
   latest model in the family at dispatch time (CLI-side, not loop-side).
5. One new unit test in `tests/` asserts: a WU with `model: sonnet` loads
   without error and a stubbed dispatch is invoked with `--model sonnet`.

**Do not touch.** Exactly 4 files change in this WU: `.specfuse/scripts/loop.py`,
`.specfuse/scripts/lint_plan.py`, `.specfuse/templates/WU.template.md`, and one
new test file under `tests/` (suggested name `tests/test_loop_model_alias.py`).
No edits to: existing WU files under `.specfuse/features/`,
`.specfuse/verification.yml`, any binding rule under `.specfuse/rules/`,
secrets, or `.git/`. See `.specfuse/rules/never-touch.md` for the full list.

**Verification.** The `code` gate set in `.specfuse/verification.yml`:
unittest discover, ruff, bandit, coverage with the repo's current floor.
Run them in order. See `.specfuse/skills/verification/SKILL.md` for how to
run and interpret them.

**Escalation triggers.** If `lint_plan.py` has no model-field validation
today, do not introduce broader validation in scope — only add a narrow
alias-set check. If widening forces a rewrite of unrelated lint paths, stop
and emit `status: blocked` naming the conflict (`result-contract.md` rule 4).
