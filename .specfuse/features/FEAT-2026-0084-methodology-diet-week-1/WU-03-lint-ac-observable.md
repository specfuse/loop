---
id: FEAT-2026-0084/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.00
model: sonnet
effort: medium
oracle_env: macos_local
produces_driver_helper: lint_ac_observable
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_lint_ac_observable.py
  - plugins/specfuse/skills/draft-feature/SKILL.md
gate_set: code
driver_version: 0.14.0
started_at: 2026-09-02T16:38:43.109425+00:00
duration_seconds: 708.153
cost_usd: 1.052363
input_tokens: 72
output_tokens: 19254
---

# Lint: an acceptance criterion the loop cannot observe is an ERROR at arm time

**Objective.** Add `lint_ac_observable` to `specfuse/loop/lint_plan.py`. In a
work unit's acceptance-criteria section, a bullet that matches an unobservable
phrase and carries no backticked command, path, or test id is ERROR when the WU
is `pending` or `ready`, WARN when `draft`, skipped when `done`. Add the matching
question to `/draft-feature`'s QA hat so the criterion is rewritten at draft
time rather than hedged at close.

**Context.** FEAT-2026-0084/T03; read `PLAN.md` § Escalation-predicate
satisfiability. 72 of 101 hedged features across 12 repos hedged on criteria of
the form "applied in prod", "consumer repo green", "operator confirms". Reuse
`_slice_ac_section` (`lint_plan.py:161`) and the WARN plumbing of the
`oracle_env` heuristic at `:1648`. Phrase list, case-insensitive, as a module
constant: `in prod`, `in production`, `applied`, `apply to`, `live cluster`,
`operator confirms`, `operator replies`, `human confirms`, `real device`,
`store console`, `consumer repo`, `post-merge`, `after merge`. Escape hatches:
`oracle_env` set to anything other than `macos_local` / `linux_docker`, or
`human_only: true`. The rule runs inside the existing `arm-sweep-gate`
(`verification.yml:80`), so it must report zero over this repository's corpus.
Fixtures copy the bold-preamble form verbatim from `WU.template.md`
(LEARNINGS `[FEAT-2026-0055/G1-CLOSE]`). Draft-feature is canonical under
`plugins/specfuse/skills/`.

**Acceptance criteria.**

- `tests/test_lint_ac_observable.py::test_pending_wu_unobservable_bullet_is_error` fails on HEAD (`lint_ac_observable` does not exist) and passes after: a `pending` WU with the bullet `- The change is applied in prod.` yields one ERROR naming the WU file and the bullet.
- `tests/test_lint_ac_observable.py::test_backticked_check_on_same_bullet_is_clean`: `- Applied in prod: \`bash scripts/verify-prod.sh\` exits 0.` yields nothing.
- `tests/test_lint_ac_observable.py::test_escape_hatches`: the same bullet on a WU with `oracle_env: github_actions_ci`, and on a WU with `human_only: true`, yields nothing; on a `draft` WU it yields WARN; on a `done` WU nothing.
- `python3 -m specfuse.loop.lint_plan <folder>` over every folder under `.specfuse/features/` reports zero ERROR from this rule; the command and its count appear in the RESULT block.
- `plugins/specfuse/skills/draft-feature/SKILL.md` step 3, QA hat, carries the question: which criteria need something the loop cannot reach, and for each, whether it moves to a post-merge checklist item or a `human_only: true` unit before the close.
- `bash scripts/sync-scaffold.sh` leaves `git status --porcelain .specfuse/skills` empty.

**Do not touch.** The `oracle_env` heuristic's own behaviour; `WU.template.md`
and the authoring skill (T02); `.specfuse/rules/` (T01); `verification.yml`;
`.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus
`python3 -c "from specfuse.loop.lint_plan import lint_ac_observable"` exits 0.

**Escalation triggers.** Emit `status: blocked` if the corpus sweep reports any
ERROR on an existing non-`done` unit: paste the bullets, do not widen the skip
rule to silence them. Emit `status: blocked` if `lint_ac_observable` is absent
from the files you edited.
