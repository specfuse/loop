---
id: FEAT-2026-0084/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
model: opus
effort: high
oracle_env: macos_local
produces:
  - .specfuse/rules/result-contract.md
  - .specfuse/rules/correlation-ids.md
  - specfuse/loop/scaffold.py
---

# Prune the included rules to 2,500 words and take the two human-facing ones out of the dispatch path

**Objective.** The seven rules `.claude/CLAUDE.md` includes into every session
total 7,213 words. Cut the set to at most 2,500 words, and move
`operator-escalation.md` and `human-output.md` out of the include block: they
govern what skills say to a human, not what an implementing session does.

**Context.** FEAT-2026-0084/T01; read `PLAN.md` in this folder. The include
block is generated from `_RULES_BLOCK` in `specfuse/loop/scaffold.py:226` and
mirrored in `.claude/CLAUDE.md`. Rules are canonical under `.specfuse/rules/` and
vendored to `specfuse/loop/data/rules/` by `scripts/sync-scaffold.sh`. The test
for each line: does a LEARNINGS entry, an issue, or a feature retrospective cite
a mistake this line prevents? If not, cut it. If yes, keep the rule in one
sentence and the citation. `tests/test_operator_escalation_rule.py` and
`tests/test_human_output_rule.py` assert the two rules are included; update them
to assert the rules are referenced from `arm-gate`, `gate-status`,
`accept-hedged-close`, `attention` and `answer-escalation` skills instead.
Red-test exempt: prose pruning, no new behaviour.

**Acceptance criteria.**

- `cat $(grep -o '@.specfuse/rules/[a-z-]*\.md' .claude/CLAUDE.md | sed 's/^@//') | wc -w` reports at most 2500.
- `grep -c "operator-escalation\|human-output" .claude/CLAUDE.md` reports 0, and `python3 -c "from specfuse.loop.scaffold import _RULES_BLOCK; assert 'operator-escalation' not in _RULES_BLOCK and 'human-output' not in _RULES_BLOCK"` exits 0.
- Every regex the two rule tests asserted before this WU is either still matched by the rule text or removed from the test with a one-line comment naming why the sentence was cut.
- `grep -rl "operator-escalation.md" plugins/specfuse/skills/*/SKILL.md | wc -l` reports at least 3.
- `result-contract.md` still carries the RESULT block grammar verbatim (`tests/test_result_block_audience.py` passes untouched) and `correlation-ids.md` still carries `CORRELATION_ID_RE`'s pattern in prose.
- `bash scripts/sync-scaffold.sh` leaves `git status --porcelain specfuse/loop/data` empty afterwards, and `tests/test_scaffold_data_in_sync.py` passes.
- A scaffold written with the old `_RULES_BLOCK` and upgraded with `specfuse upgrade` ends with the new block once, not both; one test in `tests/test_scaffold_init.py` or a sibling asserts it.

**Do not touch.** `close-discipline.md`, `planning-discipline.md`,
`design-for-diagnosis.md` (next feature); `WU.template.md` and the authoring
skill (T02); `lint_plan.py` (T03, T04); `.git/`, secrets. The driver owns git.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
commands above. `bash scripts/smoke-test.sh` is the full set.

**Escalation triggers.** Emit `status: blocked` if reaching 2,500 words requires
cutting a sentence that a LEARNINGS entry or issue cites as preventing a
recorded mistake: list the sentence and the citation, do not cut it. Blocked is
respectable.
