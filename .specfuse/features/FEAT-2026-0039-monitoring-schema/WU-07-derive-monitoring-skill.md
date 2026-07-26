---
id: FEAT-2026-0039/T07
type: implementation
status: draft
attempts: 0
planned_cost_usd: 2.50
produces:
  - plugins/specfuse/skills/derive-monitoring/SKILL.md
  - plugins/specfuse/skills/derive-monitoring/PROMPT.md
  - .specfuse/skills/derive-monitoring/SKILL.md
  - .specfuse/skills/derive-monitoring/PROMPT.md
  - tests/test_derive_monitoring_skill_registration.py
oracle_env: macos_local
model: sonnet
effort: high
---

# Author the derive-monitoring skill and vendor it into both trees

**Objective.** Add the `derive-monitoring` skill — canonical source in
`plugins/specfuse/skills/derive-monitoring/`, byte-identical vendored copy in
`.specfuse/skills/derive-monitoring/` — so an operator can run
`/derive-monitoring` in a target project and get a drafted `monitoring.yml` that
passes gate 1's validator, plus the bootstrap artifacts T06 shipped.

**Context.** This is `FEAT-2026-0039/T07` of gate 2, following T04, T05 and T06.
Read `PLAN.md` in this folder (its **Gate 2 sketch** section names this skill's
posture and its symlink boundary as decisions already made) and `GATE-02.md`'s
definition of done.

## Operator prerequisite — read this before anything else

**The `.claude/skills/derive-monitoring` discovery symlink is operator work, not
this WU's work.** Claude Code's sandbox lists `.claude/skills` under
`denyWithinAllow` — a deny rule nested inside an allow scope, which survives
`unsandboxed: true` (`[FEAT-2026-0016/G3-CLOSE]`). A session that tries to create
that symlink burns an attempt rediscovering the boundary. Do not attempt it, and do
not add an acceptance criterion that depends on it.

What this WU ships is the two real skill directories. The operator runs, once,
before dispatching anything that needs `/derive-monitoring` interactively:

```
ln -s ../../.specfuse/skills/derive-monitoring .claude/skills/derive-monitoring
```

State this in the RESULT summary as an outstanding operator step. `tests/init_skills_idempotent.bats`
documents the same forward-symlink layout for the skills that already ship.

## The skill's posture — mirror derive-verification, do not improvise

Read `plugins/specfuse/skills/derive-verification/SKILL.md` and its companion
`PROMPT.md` **before writing a line**. That skill is the established shape and
`derive-monitoring` is its post-deploy sibling. Mirror, concretely:

- **Draft, do not write.** The produced YAML is printed and discussed; it lands at
  `.specfuse/monitoring.yml` only after the user explicitly says so, and only if the
  existing file is absent or backed up. Same `plan-next` "drafts but never arms"
  posture.
- **Infer first, ask last.** A question is legitimate only if no file in the repo
  could have answered it. Asking which components exist when deployment manifests
  are sitting in the tree is a skill bug.
- **Every produced line traces to evidence the user can audit, or to a question the
  user explicitly answered.** No silent invention.
- **Interactive by design**, with a documented degraded `[gap]` mode for when no
  human is reachable — and the same warning `derive-verification` carries: piping
  `PROMPT.md` via `claude -p` consumes stdin and silently degrades.
- Structure: `## Why this exists`, `## Hard rules`, `## The method (in strict
  order)` with numbered steps, `## Seams`, `## What this skill does *not* do`, and a
  worked example.

## The method, in order

1. **Evidence gathering → component discovery.** Use the algorithm T05 shipped as a
   reference implementation in `tests/test_derive_monitoring_discovery.py`; the
   SKILL.md method section points at it by path so the prose and the tested
   algorithm cannot diverge into two different algorithms. Evidence patterns are an
   **input**, per-stack; the neutral component records are the output.
2. **Diagnosability audit** against `.specfuse/rules/design-for-diagnosis.md` (T04).
   Findings are reported as **WARN, never ERROR** — a populated codebase predating
   the rule violates it everywhere by construction, so an ERROR predicate is
   unsatisfiable on real input (`planning-discipline.md` §2; LEARNINGS
   `[FEAT-2026-0015/G2-CLOSE]`). The audit informs the operator; it never blocks the
   draft.
3. **Ask only what the repo cannot answer.** The legitimate question set is small and
   should be batched in one round: which environments exist; each environment's
   telemetry and broker `provider` string; the credential **env-var names** for each;
   any `invariant` check's query and `fingerprint_by`; and per-component dial
   loosening beyond the conservative defaults.
4. **Output** — a drafted `monitoring.yml`, a drafted `monitoring.overrides.yml`
   derived from T06's example, a filled-in reading of
   `monitoring-secrets-checklist.md`, and a reconciliation report saying, per
   component and per check, whether it came from evidence or from an answer.

## Hard rules the skill must state in its own text

- **Credentials by environment-variable name only.** An inline connection string or
  key is a validator finding, not a style preference — gate 1's
  `lint_monitoring._CREDENTIAL_KEY_RE` / `_ENV_VAR_NAME_RE` enforce it. The skill
  never asks for a credential value and never writes one.
- **`provider` is an opaque string.** The skill does not interpret it and must not
  branch on it; adapters that give it meaning are FEAT-2026-0040's scope.
- **Never invent an `invariant` query.** It is operator-supplied by definition;
  fabricating one would be the skill inventing evidence.
- **Conservative defaults.** Every drafted component starts at `runner: local`,
  `diagnose: manual`, `autofix: "off"`, loosened one dial at a time. `autofix` is
  **quoted** — `_miniyaml` does not accept the bare `off`/`on` spellings.
- **The draft must validate.** The skill instructs the operator to run
  `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml` and states
  that a non-empty finding list means the draft is wrong, not the validator.
- **Uncomment the gate afterwards.** `.specfuse/verification.yml.example` carries
  T03's commented-out `monitoring-example-lint`-shaped gate pointed at the project's
  own `monitoring.yml`; the skill's closing step tells the operator to uncomment it.

## Vendoring and registration — three surfaces

1. **Canonical then vendored.** Author under `plugins/specfuse/skills/` and run
   `scripts/sync-scaffold.sh` to vendor into `.specfuse/skills/` (it `rm -rf`s and
   re-copies the whole tree). `tests/test_skills_vendored_in_sync.py` asserts the two
   trees are byte-identical; a skill edited in `.specfuse/skills/` only fails it.
2. **`docs/skills.md`** — add a `/derive-monitoring` entry beside
   `/derive-verification` (line 66).
3. **`specfuse/loop/data/docs/skills.md`** — `sync-scaffold.sh` does **not** sync
   `docs/`; that copy is hand-maintained, and
   `tests/test_scaffold_data_in_sync.py::test_package_docs_match_canonical` asserts
   byte equality. Copy the edit across by hand.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `verification-discipline.md`) apply.
Do not restate them.

**Acceptance criteria.**

1. `tests/test_derive_monitoring_skill_registration.py::test_skill_present_in_both_trees`
   exists and **fails on HEAD before this WU's edits** (neither directory exists). It
   asserts `SKILL.md` and `PROMPT.md` are present and non-empty under both
   `plugins/specfuse/skills/derive-monitoring/` and
   `.specfuse/skills/derive-monitoring/`.
2. After this WU's edits that test passes, and so does
   `python3 -m pytest tests/test_skills_vendored_in_sync.py` — the two trees are
   byte-identical.
3. `SKILL.md`'s YAML frontmatter carries `name: derive-monitoring` and a
   `description` that names the artifact it drafts. A test asserts both, so the skill
   is discoverable rather than merely present.
4. A test asserts `SKILL.md` contains a **draft-never-write** hard rule (grep for the
   posture sentence) and that neither `SKILL.md` nor `PROMPT.md` instructs the agent
   to write `.specfuse/monitoring.yml` without explicit user consent.
5. A test asserts `SKILL.md` references `.specfuse/rules/design-for-diagnosis.md`
   (T04) and the discovery reference implementation's path (T05) — the two artifacts
   its method depends on. A skill whose method points at nothing is prose.
6. A test asserts `SKILL.md` states the diagnosability audit's severity is `WARN`
   and contains **no** instruction to report a gap as `ERROR`. The WARN-not-ERROR
   decision is recorded in `PLAN.md`'s escalation-predicate section; a skill drafted
   with an ERROR predicate fails this WU.
7. A test asserts `SKILL.md` names the `.claude/skills/derive-monitoring` symlink as
   an **operator prerequisite** and does not present it as agent work.
8. A test asserts `SKILL.md` and `PROMPT.md` never request a credential *value* —
   every credential token in either file is `UPPER_SNAKE_CASE`, matching
   `lint_monitoring._ENV_VAR_NAME_RE`. A negative case is required: run the same
   assertion against an inline-literal string built in the test and confirm it is
   rejected (`verification-discipline.md` §3).
9. `/derive-monitoring` is registered in `docs/skills.md`, and
   `python3 -m pytest tests/test_scaffold_data_in_sync.py` exits 0 — the
   hand-maintained `specfuse/loop/data/docs/skills.md` copy updated too.
10. Every organization name, host, workspace ID, and queue name in either file is an
    obvious `acme-*` placeholder. `leak-scan` runs on this diff and the pre-commit
    hook is stricter than the CI gate.
11. Every fenced `yaml` block in `SKILL.md` and `PROMPT.md` is a **complete**
    `monitoring.yml`-shaped config, or carries the explicit fragment marker T08's
    drift test defines. T08 is the gate on this; author to it rather than leaving
    T08 to fix your examples.
12. Every new `subprocess.run` call, if any, declares `check=` explicitly
    (`PLW1510`, enforced since FEAT-2026-0037).

**No in-loop oracle for interview quality — stated, not hidden.** AC1–AC12 verify
that the skill exists, is registered, is internally consistent, and that its
examples validate. Nothing here verifies that the *interview* asks good questions or
that a real operator reaches a good `monitoring.yml`; that requires a human channel
and a target repository a dispatched WU has neither of. Do not manufacture a test
that appears to cover it. `GATE-02-REVIEW.md` records this gap and G2-CLOSE carries
it into `## What the loop did NOT verify`.

**Do not touch.** `.claude/skills/` — creating the discovery symlink is operator
work and the sandbox's `denyWithinAllow` rule will refuse it; the existing skills
under `plugins/specfuse/skills/` and `.specfuse/skills/`;
`specfuse/loop/lint_monitoring.py` and `.specfuse/monitoring.yml.example` (gate 1
shipped both); `.specfuse/rules/design-for-diagnosis.md` (T04); the discovery
reference implementation (T05); the bootstrap artifacts (T06 — reference them, do
not edit them); `.specfuse/verification.yml` and its `.example` (T03 wired both);
`.git/`, secrets. The driver owns all git operations. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` — `tests`,
`lint`, `security`, `coverage` ≥ 90%, `leak-scan`, `monitoring-example-lint`, and
the bats suites (`sync-scaffold-bats`, `init-sh-shim-bats`, `init-skills-bats`) —
must all pass, plus `python3 -m pytest tests/test_skills_vendored_in_sync.py tests/test_scaffold_data_in_sync.py`
run directly. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if the skill's method cannot be
written against T05's reference implementation because that implementation's shape
disagrees with what the interview needs — that is a real gate-2 internal
disagreement and the fix belongs in whichever WU is wrong, not in prose that papers
over it. Also block if `scripts/sync-scaffold.sh` cannot vendor the new skill
without editing the vendoring logic itself. Do **not** block on the
`.claude/skills/` symlink: it is expected to be absent, and its absence is an
operator step, not a failure. If either `SKILL.md` is absent from the files you
edited, emit `status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
