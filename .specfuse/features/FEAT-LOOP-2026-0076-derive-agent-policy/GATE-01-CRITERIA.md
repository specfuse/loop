### T01#1

- **criterion:** `tests/test_policy_proposals.py::TestProposeDefaults::test_empty_repo_proposes_nothing`
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#2

- **criterion:** `specfuse/loop/policy_proposals.py` defines
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#3

- **criterion:** Each proposal is a mapping carrying at least the proposed `value` and a
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#4

- **criterion:** A repository with **no** `events.jsonl` anywhere returns **no** proposal for
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#5

- **criterion:** A repository **with** `events.jsonl` fixtures returns a proposal for both,
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#6

- **criterion:** `test_paths` is proposed from evidence in both directions: a fixture whose
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#7

- **criterion:** A repository where the tree and the gate commands **disagree** about the test
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#8

- **criterion:** `max_open_prs` is proposed only when the injected `runner` returns a usable
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#9

- **criterion:** **Every proposed value validates clean.** A test builds a policy file from
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#10

- **criterion:** The module performs no network call and opens no file outside `repo_root` —
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#11

- **criterion:** `python3 -m unittest tests.test_policy_proposals -v` exits zero after this
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#12

- **criterion:** `python3 -c "from specfuse.loop.policy_proposals import propose_policy_defaults"`
- **oracle:** `python3 -c "from specfuse.loop.policy_proposals import propose_policy_defaults"`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01H#1

- **criterion:** `tests/test_policy_proposals.py::TestRelativeRepoRoot::test_relative_and_absolute_agree`
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01H#2

- **criterion:** `propose_policy_defaults` resolves `repo_root` before using it to build the
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01H#3

- **criterion:** **The sibling-repository scoping is preserved.** A test asserts that
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01H#4

- **criterion:** A test asserts that on a repository **with** events history, budget proposals
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01H#5

- **criterion:** **A withheld proposal means no evidence.** A test asserts that when
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01H#6

- **criterion:** The `evidence` string for `max_tokens_per_run` names the cost-to-token
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01H#7

- **criterion:** `_ASSUMED_TOKENS_PER_USD`'s value is **unchanged** by this WU — the
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01H#8

- **criterion:** All of T01's existing tests pass **unmodified** — a test file may gain cases
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01H#9

- **criterion:** `python3 -m unittest tests.test_policy_proposals -v` exits zero after this
- **oracle:** `python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_derive_agent_policy_skill.py::TestDeriveAgentPolicySkill::test_skill_file_exists`
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#2

- **criterion:** `plugins/specfuse/skills/derive-agent-policy/SKILL.md` exists with YAML
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#3

- **criterion:** `plugins/specfuse/skills/derive-agent-policy/PROMPT.md` exists, matching the
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#4

- **criterion:** A test asserts the body names `propose_policy_defaults`,
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#5

- **criterion:** A test asserts the body names all four proposed values
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#6

- **criterion:** A test asserts the body states that where no proposal is available the shipped
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#7

- **criterion:** A test asserts the webhook constraint is present: the prose requires an
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#8

- **criterion:** A test asserts the body carries **staged per-block accepts** and the
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#9

- **criterion:** A test asserts the body carries the escalation-framing section referencing
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#10

- **criterion:** A test asserts the body carries a "What this skill does NOT do" section.
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#11

- **criterion:** `scripts/sync-scaffold.sh` has been run;
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#12

- **criterion:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#1

- **criterion:** `tests/test_agent_policy_key_ownership.py::TestKeyOwnership::test_groom_backlog_disclaims_the_other_blocks`
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#2

- **criterion:** `plugins/specfuse/skills/groom-backlog/SKILL.md` states that it owns `queue:`
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#3

- **criterion:** `plugins/specfuse/skills/derive-agent-policy/SKILL.md` states that it owns
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#4

- **criterion:** A test asserts, for each skill, that its body names **every** key block it
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#5

- **criterion:** A test asserts, for each skill, that its body names **every** key block it
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#6

- **criterion:** The two ownership sets are **disjoint and exhaustive** over the file's
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#7

- **criterion:** Both skills state the invariant in the form the operator chose: **one writer
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#8

- **criterion:** `scripts/sync-scaffold.sh` has been run and both vendored copies are
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#9

- **criterion:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
