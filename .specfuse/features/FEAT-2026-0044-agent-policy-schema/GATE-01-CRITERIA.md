### T01#1

- **criterion:** `tests/test_agent_policy_schema.py::TestValidateAgentPolicy::test_shipped_example_validates_clean`
- **state:** `unverified`

### T01#2

- **criterion:** `specfuse/loop/agent_policy.py` defines
- **state:** `unverified`

### T01#3

- **criterion:** Every finding string the validator returns starts with either `ERROR: ` or
- **state:** `unverified`

### T01#4

- **criterion:** Module-level enums exist as `frozenset`s and are the single source of their
- **state:** `unverified`

### T01#5

- **criterion:** A missing required top-level key (`version`, `queue`, `rules`, `budgets`,
- **state:** `unverified`

### T01#6

- **criterion:** An unknown top-level key produces one `ERROR: ` finding naming it — unknown
- **state:** `unverified`

### T01#7

- **criterion:** A `version` other than `1` produces an `ERROR: ` finding.
- **state:** `unverified`

### T01#8

- **criterion:** A queue entry not matching `^FEAT-\d{4}-\d{4}$` produces an `ERROR: `
- **state:** `unverified`

### T01#9

- **criterion:** An **empty** `queue:` list produces **zero** findings — a test asserts this
- **state:** `unverified`

### T01#10

- **criterion:** Wrong-typed values produce `ERROR: ` findings rather than raising:
- **state:** `unverified`

### T01#11

- **criterion:** `rules.features.overrides` is optional; when present, every key matches the
- **state:** `unverified`

### T01#12

- **criterion:** `.specfuse/agent-policy.yml.example` exists, carries the Apache-2.0 comment
- **state:** `unverified`

### T01#13

- **criterion:** `main() -> int` prints each finding one per line and returns `1` when any
- **state:** `unverified`

### T01#14

- **criterion:** `.specfuse/scripts/lint_agent_policy.py` exists as a thin shim delegating to
- **state:** `unverified`

### T01#15

- **criterion:** `.specfuse/verification.yml` gains a `code` gate named
- **state:** `unverified`

### T01#16

- **criterion:** `python3 -m unittest tests.test_agent_policy_schema -v` exits zero after
- **state:** `unverified`

### T01#17

- **criterion:** `python3 -c "from specfuse.loop.agent_policy import validate_agent_policy"`
- **state:** `unverified`

### T02#1

- **criterion:** `tests/test_agent_policy_queue.py::TestQueueAgainstRoadmap::test_absent_feature_id_is_error`
- **state:** `unverified`

### T02#2

- **criterion:** `specfuse/loop/agent_policy.py` defines
- **state:** `unverified`

### T02#3

- **criterion:** `load_policy` raises `FileNotFoundError` when the path is absent — it does
- **state:** `unverified`

### T02#4

- **criterion:** `specfuse/loop/lint_roadmap.py` defines a public
- **state:** `unverified`

### T02#5

- **criterion:** `validate_agent_policy` emits one `ERROR: ` finding per queue entry that has
- **state:** `unverified`

### T02#6

- **criterion:** `validate_agent_policy` emits one `WARN: ` finding per queue entry whose
- **state:** `unverified`

### T02#7

- **criterion:** `validate_agent_policy` emits **no** finding for a queue entry whose status
- **state:** `unverified`

### T02#8

- **criterion:** The queue check is skipped without error when `roadmap.md` is absent — a
- **state:** `unverified`

### T02#9

- **criterion:** `.specfuse/agent-policy.yml` exists at the repo root's `.specfuse/`, carries
- **state:** `unverified`

### T02#10

- **criterion:** `.specfuse/verification.yml`'s `agent-policy-example-lint` gate is updated
- **state:** `unverified`

### T02#11

- **criterion:** `python3 -m unittest tests.test_agent_policy_queue -v` exits zero after this
- **state:** `unverified`

### T02#12

- **criterion:** `python3 -c "from specfuse.loop.agent_policy import load_policy; from specfuse.loop.lint_roadmap import roadmap_statuses"`
- **state:** `unverified`

### T03#1

- **criterion:** `tests/test_agent_policy_triage_dial.py::TestResolveTriageAuto::test_absent_policy_file_returns_false`
- **state:** `unverified`

### T03#2

- **criterion:** `specfuse/loop/agent_policy.py` defines
- **state:** `unverified`

### T03#3

- **criterion:** `resolve_triage_auto` returns `False` when the policy file does not exist —
- **state:** `unverified`

### T03#4

- **criterion:** `resolve_triage_auto` returns `False` when the file exists but
- **state:** `unverified`

### T03#5

- **criterion:** `plugins/specfuse/skills/triage-issues/SKILL.md` instructs the session to
- **state:** `unverified`

### T03#6

- **criterion:** That same skill file still states the settled semantics verbatim: under
- **state:** `unverified`

### T03#7

- **criterion:** `scripts/sync-scaffold.sh` has been run, and
- **state:** `unverified`

### T03#8

- **criterion:** `specfuse/loop/triage.py` is **unmodified** by this WU — `git diff --stat`
- **state:** `unverified`

### T03#9

- **criterion:** `python3 -m unittest tests.test_agent_policy_triage_dial tests.test_triage_apply -v`
- **state:** `unverified`

### T03#10

- **criterion:** `python3 -c "from specfuse.loop.agent_policy import resolve_triage_auto"`
- **state:** `unverified`

### T04#1

- **criterion:** `tests/test_groom_backlog_skill.py::TestGroomBacklogSkill::test_skill_file_exists`
- **state:** `unverified`

### T04#2

- **criterion:** `plugins/specfuse/skills/groom-backlog/SKILL.md` exists with YAML
- **state:** `unverified`

### T04#3

- **criterion:** A test asserts the skill body names `.specfuse/agent-policy.yml`,
- **state:** `unverified`

### T04#4

- **criterion:** A test asserts the skill body contains a "What this skill does NOT do"
- **state:** `unverified`

### T04#5

- **criterion:** A test asserts the skill body states that the only file it writes is
- **state:** `unverified`

### T04#6

- **criterion:** A test asserts the skill body contains the escalation-framing section
- **state:** `unverified`

### T04#7

- **criterion:** A test asserts the skill body documents the queue-hygiene pass and
- **state:** `unverified`

### T04#8

- **criterion:** A test asserts the skill body states that an empty queue is a valid accepted
- **state:** `unverified`

### T04#9

- **criterion:** The skill carries the Apache-2.0 comment header used by every other skill in
- **state:** `unverified`

### T04#10

- **criterion:** `scripts/sync-scaffold.sh` has been run;
- **state:** `unverified`

### T04#11

- **criterion:** `python3 -m unittest tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **state:** `unverified`
