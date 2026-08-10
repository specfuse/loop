### T01#1

- **criterion:** `tests/test_agent_policy_schema.py::TestValidateAgentPolicy::test_shipped_example_validates_clean`
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) — proves the named test exists and is green; the `fails on HEAD` half is historical and is recorded as D3 in RETROSPECTIVE.md
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#2

- **criterion:** `specfuse/loop/agent_policy.py` defines
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) + python3 -c "from specfuse.loop.agent_policy import validate_agent_policy" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#3

- **criterion:** Every finding string the validator returns starts with either `ERROR: ` or
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) (severity-prefix assertions) + python3 -c "from specfuse.loop.agent_policy import validate_agent_policy" over both .specfuse/agent-policy.yml and .specfuse/agent-policy.yml.example — NO FINDINGS from either
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#4

- **criterion:** Module-level enums exist as `frozenset`s and are the single source of their
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) (per-enum out-of-range rejection tests)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#5

- **criterion:** A missing required top-level key (`version`, `queue`, `rules`, `budgets`,
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) (missing-required-key tests)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#6

- **criterion:** An unknown top-level key produces one `ERROR: ` finding naming it — unknown
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) (unknown-top-level-key test)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#7

- **criterion:** A `version` other than `1` produces an `ERROR: ` finding.
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) (version-not-1 test)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#8

- **criterion:** A queue entry not matching `^FEAT-\d{4}-\d{4}$` produces an `ERROR: `
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) (malformed-entry and duplicate-entry tests)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#9

- **criterion:** An **empty** `queue:` list produces **zero** findings — a test asserts this
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) (empty-queue-is-zero-findings test)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#10

- **criterion:** Wrong-typed values produce `ERROR: ` findings rather than raising:
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) (wrong-typed-value tests: wip_limit 0 / "one", max_open_prs -1, sla_hours 0, non-bool preempt)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#11

- **criterion:** `rules.features.overrides` is optional; when present, every key matches the
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) (rules.features.overrides key/value tests)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#12

- **criterion:** `.specfuse/agent-policy.yml.example` exists, carries the Apache-2.0 comment
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) + grep -c "Licensed under the Apache License" .specfuse/agent-policy.yml.example (1) + python3 -c "from specfuse.loop.agent_policy import validate_agent_policy" over both .specfuse/agent-policy.yml and .specfuse/agent-policy.yml.example — NO FINDINGS from either
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#13

- **criterion:** `main() -> int` prints each finding one per line and returns `1` when any
- **oracle:** python3 -m unittest tests.test_agent_policy_schema (Ran 23 tests, OK, exit 0) + python3 .specfuse/scripts/lint_agent_policy.py over two purpose-built policy files: a queue entry naming a done feature printed `WARN: queue: 'FEAT-2026-0002' is roadmap status 'done'` and exited 0; a nonexistent FEAT-ID printed `ERROR: queue: 'FEAT-2026-9999' has no row in roadmap.md` and exited 1 — the WARN-only file exiting 0 is the negative observation for this criterion
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#14

- **criterion:** `.specfuse/scripts/lint_agent_policy.py` exists as a thin shim delegating to
- **oracle:** python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml (exit 0) — the gate command invokes the shim, so exit 0 proves it exists and delegates; + grep -c "Licensed under the Apache License" .specfuse/scripts/lint_agent_policy.py (1)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#15

- **criterion:** `.specfuse/verification.yml` gains a `code` gate named
- **oracle:** python3 -c "...regex over .specfuse/verification.yml..." — printed the agent-policy-example-lint command and asserted it names both .specfuse/agent-policy.yml.example and .specfuse/agent-policy.yml (exit 0) — the gate exists under `code`; note its command is T02#10's widened form, which was a planned in-feature revision, not drift
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#16

- **criterion:** `python3 -m unittest tests.test_agent_policy_schema -v` exits zero after
- **oracle:** python3 -m unittest tests.test_agent_policy_schema -v (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#17

- **criterion:** `python3 -c "from specfuse.loop.agent_policy import validate_agent_policy"`
- **oracle:** python3 -c "from specfuse.loop.agent_policy import validate_agent_policy" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_agent_policy_queue.py::TestQueueAgainstRoadmap::test_absent_feature_id_is_error`
- **oracle:** python3 -m unittest tests.test_agent_policy_queue (Ran 10 tests, OK, exit 0) — proves the named test exists and is green; the `fails on HEAD` half is historical and is recorded as D3 in RETROSPECTIVE.md
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#2

- **criterion:** `specfuse/loop/agent_policy.py` defines
- **oracle:** python3 -m unittest tests.test_agent_policy_queue (Ran 10 tests, OK, exit 0) + python3 -c "from specfuse.loop.agent_policy import load_policy" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#3

- **criterion:** `load_policy` raises `FileNotFoundError` when the path is absent — it does
- **oracle:** python3 -m unittest tests.test_agent_policy_queue (Ran 10 tests, OK, exit 0) (FileNotFoundError test)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#4

- **criterion:** `specfuse/loop/lint_roadmap.py` defines a public
- **oracle:** python3 -m unittest tests.test_agent_policy_queue (Ran 10 tests, OK, exit 0) + python3 -c "from specfuse.loop.lint_roadmap import roadmap_statuses; ..." printed `FEAT-2026-0002 -> done | FEAT-2026-0011 -> blocked` against the real roadmap (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#5

- **criterion:** `validate_agent_policy` emits one `ERROR: ` finding per queue entry that has
- **oracle:** python3 -m unittest tests.test_agent_policy_queue (Ran 10 tests, OK, exit 0) + python3 .specfuse/scripts/lint_agent_policy.py over two purpose-built policy files: a queue entry naming a done feature printed `WARN: queue: 'FEAT-2026-0002' is roadmap status 'done'` and exited 0; a nonexistent FEAT-ID printed `ERROR: queue: 'FEAT-2026-9999' has no row in roadmap.md` and exited 1 (ERROR half)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#6

- **criterion:** `validate_agent_policy` emits one `WARN: ` finding per queue entry whose
- **oracle:** python3 -m unittest tests.test_agent_policy_queue (Ran 10 tests, OK, exit 0) + python3 .specfuse/scripts/lint_agent_policy.py over two purpose-built policy files: a queue entry naming a done feature printed `WARN: queue: 'FEAT-2026-0002' is roadmap status 'done'` and exited 0; a nonexistent FEAT-ID printed `ERROR: queue: 'FEAT-2026-9999' has no row in roadmap.md` and exited 1 (WARN half)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#7

- **criterion:** `validate_agent_policy` emits **no** finding for a queue entry whose status
- **oracle:** python3 -m unittest tests.test_agent_policy_queue (Ran 10 tests, OK, exit 0) (planned/active/blocked/deferred all silent) + python3 -c "from specfuse.loop.agent_policy import validate_agent_policy" over both .specfuse/agent-policy.yml and .specfuse/agent-policy.yml.example — NO FINDINGS from either — the live queue names three planned features and produced no finding
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#8

- **criterion:** The queue check is skipped without error when `roadmap.md` is absent — a
- **oracle:** python3 -m unittest tests.test_agent_policy_queue (Ran 10 tests, OK, exit 0) (roadmap-absent test asserts zero findings, not a traceback)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#9

- **criterion:** `.specfuse/agent-policy.yml` exists at the repo root's `.specfuse/`, carries
- **oracle:** python3 -c "from specfuse.loop.agent_policy import validate_agent_policy" over both .specfuse/agent-policy.yml and .specfuse/agent-policy.yml.example — NO FINDINGS from either — .specfuse/agent-policy.yml returned zero findings, hence zero ERROR findings
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#10

- **criterion:** `.specfuse/verification.yml`'s `agent-policy-example-lint` gate is updated
- **oracle:** python3 -c "...regex over .specfuse/verification.yml..." — printed the agent-policy-example-lint command and asserted it names both .specfuse/agent-policy.yml.example and .specfuse/agent-policy.yml (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#11

- **criterion:** `python3 -m unittest tests.test_agent_policy_queue -v` exits zero after this
- **oracle:** python3 -m unittest tests.test_agent_policy_queue -v (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#12

- **criterion:** `python3 -c "from specfuse.loop.agent_policy import load_policy; from specfuse.loop.lint_roadmap import roadmap_statuses"`
- **oracle:** python3 -c "from specfuse.loop.agent_policy import load_policy; from specfuse.loop.lint_roadmap import roadmap_statuses" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#1

- **criterion:** `tests/test_agent_policy_triage_dial.py::TestResolveTriageAuto::test_absent_policy_file_returns_false`
- **oracle:** python3 -m unittest tests.test_agent_policy_triage_dial (Ran 4 tests, OK, exit 0) — proves the named test exists and is green; the `fails on HEAD` half is historical and is recorded as D3 in RETROSPECTIVE.md
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#2

- **criterion:** `specfuse/loop/agent_policy.py` defines
- **oracle:** python3 -m unittest tests.test_agent_policy_triage_dial (Ran 4 tests, OK, exit 0) + python3 -c "from specfuse.loop.agent_policy import resolve_triage_auto" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#3

- **criterion:** `resolve_triage_auto` returns `False` when the policy file does not exist —
- **oracle:** python3 -m unittest tests.test_agent_policy_triage_dial (Ran 4 tests, OK, exit 0) (absent-policy-file returns False, does not raise)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#4

- **criterion:** `resolve_triage_auto` returns `False` when the file exists but
- **oracle:** python3 -m unittest tests.test_agent_policy_triage_dial (Ran 4 tests, OK, exit 0) (absent key returns False; the string "true" does not enable the dial)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#5

- **criterion:** `plugins/specfuse/skills/triage-issues/SKILL.md` instructs the session to
- **oracle:** grep -n "resolve_triage_auto" plugins/specfuse/skills/triage-issues/SKILL.md — 2 hits (lines 63 and 108), the second inside the apply_triage call the skill instructs; read of the surrounding section confirms the operator prompt is replaced by the resolver (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#6

- **criterion:** That same skill file still states the settled semantics verbatim: under
- **oracle:** grep -c "still marked, never skipped" plugins/specfuse/skills/triage-issues/SKILL.md — 1 hit, in the sentence stating the auto=True downgrade to `question` and the `needs-human` route (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#7

- **criterion:** `scripts/sync-scaffold.sh` has been run, and
- **oracle:** python3 -m unittest tests.test_skills_vendored_in_sync (Ran 4 tests, OK, exit 0) + diff -q plugins/specfuse/skills/triage-issues/SKILL.md .specfuse/skills/triage-issues/SKILL.md (byte-identical, exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#8

- **criterion:** `specfuse/loop/triage.py` is **unmodified** by this WU — `git diff --stat`
- **oracle:** python3 -m unittest tests.test_triage_apply (Ran 7 tests, OK, exit 0) settles the second half — apply_triage's semantics survived untouched. The `git diff --stat` half was NOT run: a work-unit session runs no git (result-contract.md rule 1). See RETROSPECTIVE.md entry D2 for the re-run condition
- **kind:** `narrow`
- **state:** `unverified`
- **attempt:** `1`

### T03#9

- **criterion:** `python3 -m unittest tests.test_agent_policy_triage_dial tests.test_triage_apply -v`
- **oracle:** python3 -m unittest tests.test_agent_policy_triage_dial tests.test_triage_apply -v (both exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#10

- **criterion:** `python3 -c "from specfuse.loop.agent_policy import resolve_triage_auto"`
- **oracle:** python3 -c "from specfuse.loop.agent_policy import resolve_triage_auto" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#1

- **criterion:** `tests/test_groom_backlog_skill.py::TestGroomBacklogSkill::test_skill_file_exists`
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill (Ran 10 tests, OK, exit 0) — proves the named test exists and is green; the `fails on HEAD` half is historical and is recorded as D3 in RETROSPECTIVE.md
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#2

- **criterion:** `plugins/specfuse/skills/groom-backlog/SKILL.md` exists with YAML
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill (Ran 10 tests, OK, exit 0) (frontmatter name/description + trigger-phrase assertions)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#3

- **criterion:** A test asserts the skill body names `.specfuse/agent-policy.yml`,
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill (Ran 10 tests, OK, exit 0) (exact-match literal assertions for .specfuse/agent-policy.yml, load_policy, validate_agent_policy)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#4

- **criterion:** A test asserts the skill body contains a "What this skill does NOT do"
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill (Ran 10 tests, OK, exit 0) ("What this skill does NOT do" section: no --auto mode, writes only on explicit accept)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#5

- **criterion:** A test asserts the skill body states that the only file it writes is
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill (Ran 10 tests, OK, exit 0) (single-file-written assertion)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#6

- **criterion:** A test asserts the skill body contains the escalation-framing section
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill (Ran 10 tests, OK, exit 0) (escalation-framing section referencing .specfuse/rules/operator-escalation.md)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#7

- **criterion:** A test asserts the skill body documents the queue-hygiene pass and
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill (Ran 10 tests, OK, exit 0) (queue-hygiene pass; WARN-vs-ERROR distinction)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#8

- **criterion:** A test asserts the skill body states that an empty queue is a valid accepted
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill (Ran 10 tests, OK, exit 0) (empty-queue-is-a-valid-outcome assertion)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#9

- **criterion:** The skill carries the Apache-2.0 comment header used by every other skill in
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill (Ran 10 tests, OK, exit 0) + grep -c "Licensed under the Apache License" plugins/specfuse/skills/groom-backlog/SKILL.md (1)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#10

- **criterion:** `scripts/sync-scaffold.sh` has been run;
- **oracle:** python3 -m unittest tests.test_skills_vendored_in_sync (Ran 4 tests, OK, exit 0) + diff -q plugins/specfuse/skills/groom-backlog/SKILL.md .specfuse/skills/groom-backlog/SKILL.md (byte-identical, exit 0) + python3 -m unittest tests.test_skill_discovery_links (Ran 4 tests, OK, exit 0) + readlink .claude/skills/groom-backlog -> ../../.specfuse/skills/groom-backlog
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#11

- **criterion:** `python3 -m unittest tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **oracle:** python3 -m unittest tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v (all three exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
