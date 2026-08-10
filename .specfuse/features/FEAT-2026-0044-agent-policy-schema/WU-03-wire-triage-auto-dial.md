---
id: FEAT-2026-0044/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
produces:
  - plugins/specfuse/skills/triage-issues/SKILL.md
  - tests/test_agent_policy_triage_dial.py
produces_driver_helper: resolve_triage_auto
---

# Supply `apply_triage`'s `auto` from the policy file

**Objective.** Add `resolve_triage_auto(path=None) -> bool` to
`specfuse/loop/agent_policy.py` and make the `/triage-issues` skill read the
dial from `.specfuse/agent-policy.yml` instead of asking the operator each run.

**Context.** Correlation ID `FEAT-2026-0044/T03`. Depends on
`FEAT-2026-0044/T02` for `load_policy`.

**This is the inherited handoff, and its semantics are already settled.**
FEAT-2026-0045 shipped triage's dial as an explicit keyword argument —
`apply_triage(runner, repo, decisions, *, auto: bool = False)`
(`specfuse/loop/triage.py:126`) — reading no configuration of any kind,
deliberately, because `agent-policy.yml` did not exist. That feature's
`RETROSPECTIVE.md` and the roadmap row for FEAT-2026-0044 both state the
contract for this WU in the same words:

> **Supply the value; do not redesign the semantics, and do not re-litigate
> where the dial lives.**

Under `auto=True` a decision whose confidence is not `"high"` is recorded as the
`question` category and routed to `needs-human` — **still marked, never
skipped**. That behavior is tested at both settings in
`tests/test_triage_apply.py` and this WU must not change it.

**There is no production call site today.** `apply_triage` is called only from
`tests/test_triage_apply.py` and from the `/triage-issues` skill's prose. So the
wiring is: a resolver function in `agent_policy.py`, plus the skill instruction
that tells a session to call it. Do **not** add a CLI entry point, a `main()`, or
a scheduler — FEAT-2026-0049 owns invocation.

**Skills are canonical in `plugins/specfuse/skills/`.** Edit
`plugins/specfuse/skills/triage-issues/SKILL.md`, then run
`scripts/sync-scaffold.sh` to vendor the change into `.specfuse/skills/`.
`tests/test_skills_vendored_in_sync.py` fails if you edit only one copy.

**Load-bearing strings from T01/T02, quoted verbatim:** config path
`.specfuse/agent-policy.yml`; module `specfuse/loop/agent_policy.py`; reader
`load_policy`; the dial's location in the schema is `rules.triage.auto`.

**Flag-scope table** (`.specfuse/rules/planning-discipline.md` §3). The flag is
`apply_triage`'s `auto` parameter. Every path it is claimed to affect:

| Code path | Gated by flag? | Why |
|---|---|---|
| `triage.apply_triage` — confidence branch | yes | Pre-existing, shipped by FEAT-2026-0045; `auto=True` reroutes non-`high` confidence to `question`/`needs-human`. Unchanged by this WU. |
| `triage.apply_triage` — marker write | no | Every decision is marked at both settings. The dial changes the *category*, never whether a write happens. |
| `triage.apply_triage` — label write | no | Best-effort at both settings, independent of the dial. |
| `agent_policy.resolve_triage_auto` | n/a — it *is* the source | New in this WU: reads `rules.triage.auto`, returns `False` when the policy file is absent. |
| `/triage-issues` skill's operator prompt | yes | Replaced: the skill stops asking the operator and reads the resolver instead. |
| `/diagnose-issue`, `/fix-bug`, autofix lane | no | Different pipelines with their own dials (`diagnose`, `autofix` in `monitoring.yml`). This flag does not reach them, and must not be made to. |

**Headline claim checked against the table:** the roadmap says this feature
"must wire its policy file to that parameter." The table supports exactly that
and nothing wider — no other pipeline's behavior changes.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because
`resolve_triage_auto` does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_agent_policy_triage_dial.py::TestResolveTriageAuto::test_absent_policy_file_returns_false`
   exists and **fails on HEAD before this WU runs**.
2. `specfuse/loop/agent_policy.py` defines
   `resolve_triage_auto(path: str | Path | None = None) -> bool`, reading
   `rules.triage.auto` via `load_policy`.
3. `resolve_triage_auto` returns `False` when the policy file does not exist —
   the safe default, matching `apply_triage`'s own default. A test asserts it
   does not raise.
4. `resolve_triage_auto` returns `False` when the file exists but
   `rules.triage.auto` is absent, and `True` only when that key is exactly
   boolean `true`. A test asserts the string `"true"` does **not** enable the
   dial.
5. `plugins/specfuse/skills/triage-issues/SKILL.md` instructs the session to
   obtain `auto` by calling
   `specfuse.loop.agent_policy.resolve_triage_auto()` and to pass the result to
   `apply_triage`, replacing the current "auto stays off unless the operator
   asks for it" instruction with a statement that the dial is declared in
   `.specfuse/agent-policy.yml`.
6. That same skill file still states the settled semantics verbatim: under
   `auto=True`, a decision whose confidence is not `high` is recorded as
   `question` and routed to `needs-human`, still marked, never skipped.
7. `scripts/sync-scaffold.sh` has been run, and
   `.specfuse/skills/triage-issues/SKILL.md` is byte-identical to the canonical
   copy — `python3 -m unittest tests.test_skills_vendored_in_sync -v` exits zero.
8. `specfuse/loop/triage.py` is **unmodified** by this WU — `git diff --stat`
   shows no change to it, and the existing `tests/test_triage_apply.py` passes
   untouched.
9. `python3 -m unittest tests.test_agent_policy_triage_dial tests.test_triage_apply -v`
   exits zero after this WU's edits.
10. `python3 -c "from specfuse.loop.agent_policy import resolve_triage_auto"`
    exits zero.

**Do not touch.** `specfuse/loop/triage.py` — the dial's semantics are settled
and this WU supplies a value, nothing more; if you believe the semantics are
wrong, report it rather than changing it. `tests/test_triage_apply.py` — it
must pass unmodified, which is the proof the semantics survived.
`monitoring.yml`'s `diagnose` / `autofix` dials — different pipelines.
`.specfuse/skills/triage-issues/SKILL.md` directly — edit the canonical
`plugins/` copy and let the sync script vendor it. Generated directories,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, and
`agent-policy-example-lint`. Plus the scoped runs in criteria 7, 9 and the
symbol check in criterion 10.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`tests/test_triage_apply.py` cannot pass without editing `triage.py` (that
would mean the settled semantics and this wiring genuinely conflict, which is an
operator decision, not yours); or `scripts/sync-scaffold.sh` fails or reports
drift in surfaces this WU did not touch. If `resolve_triage_auto` is absent from
the files you edited, emit `status: blocked` — do not claim complete.
