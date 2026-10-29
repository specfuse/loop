### T04#1

- **criterion:** `tests/test_policy_review.py::TestReviewAgentPolicy::test_baseline_match_is_classified_and_caveated`
- **oracle:** `python3 -m unittest tests.test_policy_review -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#2

- **criterion:** `specfuse/loop/policy_review.py` defines
- **oracle:** `python3 -c "from specfuse.loop.policy_review import review_agent_policy"`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#3

- **criterion:** For each of the four in-scope keys the returned entry carries the current
- **oracle:** `direct call: review_agent_policy() over one fixture per provenance class, return value read (close session)`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#4

- **criterion:** The provenance classification is one of exactly three states —
- **oracle:** `direct call: review_agent_policy() over one fixture per provenance class, return value read (close session)`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#5

- **criterion:** An entry classified as matching the shipped baseline carries a caveat string
- **oracle:** `direct call: review_agent_policy() over one fixture per provenance class, return value read (close session)`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#6

- **criterion:** **Each entry records how its proposal was obtained** — one of `measured`
- **oracle:** `python3 -m unittest tests.test_policy_review -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#7

- **criterion:** A test asserts the three absences are distinguishable from one another: a key
- **oracle:** `direct call: review_agent_policy() over one fixture per provenance class, return value read (close session)`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#8

- **criterion:** When `.specfuse/agent-policy.yml.example` is absent or unparseable, every key
- **oracle:** `direct call: review_agent_policy() over a fixture with no example file and one with an unparseable example (close session)`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#9

- **criterion:** `review_agent_policy` never reads, returns, or reports the `queue` key, and a
- **oracle:** `direct call: review_agent_policy() over fixtures carrying a populated `queue:`, returned structure searched for `queue` (close session)`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#10

- **criterion:** The function returns a **per-key readout only** — it never returns or writes a
- **oracle:** `direct call: review_agent_policy() — returned top-level keys are exactly the four dotted in-scope keys (close session)`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#11

- **criterion:** `review_agent_policy` performs **no network call of its own**; `max_open_prs`
- **oracle:** `python3 -m unittest tests.test_policy_review -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#12

- **criterion:** `python3 -m unittest tests.test_policy_review -v` exits zero after this WU's
- **oracle:** `python3 -m unittest tests.test_policy_review -v && python3 -m unittest tests.test_policy_proposals -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#1

- **criterion:** `tests/test_derive_agent_policy_review_mode.py::TestReviewMode::test_prose_names_review_api_literals`
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#2

- **criterion:** `plugins/specfuse/skills/derive-agent-policy/SKILL.md` gains a review-mode
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#3

- **criterion:** The prose states the **entry condition** explicitly: an existing
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#4

- **criterion:** For each of the four in-scope keys the prose describes a readout carrying the
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#5

- **criterion:** The prose states that a value matching the shipped baseline is a **hint, not
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#6

- **criterion:** **The readout distinguishes a measured proposal from a converted one**, using
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#7

- **criterion:** The prose keeps review mode's corrections on the same **staged per-block
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#8

- **criterion:** `PROMPT.md` gains the matching review-mode instructions, so an operator who
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#9

- **criterion:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **oracle:** `python3 -m unittest tests.test_derive_agent_policy_review_mode tests.test_derive_agent_policy_skill tests.test_skills_vendored_in_sync tests.test_skill_discovery_links -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T05#10

- **criterion:** `scripts/sync-scaffold.sh` has been run and both vendored copies
- **oracle:** `cmp -s plugins/specfuse/skills/derive-agent-policy/SKILL.md .specfuse/skills/derive-agent-policy/SKILL.md; cmp -s plugins/specfuse/skills/derive-agent-policy/PROMPT.md .specfuse/skills/derive-agent-policy/PROMPT.md`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T06#1

- **criterion:** `tests/test_agent_policy_key_ownership.py::TestReviewModePreservation::test_review_mode_states_non_clobbering`
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T06#2

- **criterion:** `plugins/specfuse/skills/derive-agent-policy/SKILL.md`'s review-mode section
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T06#3

- **criterion:** The same section states the non-clobbering property: a proposed correction to
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T06#4

- **criterion:** A test asserts the non-clobbering statement names at least one concrete
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T06#5

- **criterion:** A test asserts review mode's stated must-never-write set covers **every**
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T06#6

- **criterion:** `tests/test_agent_policy_key_ownership.py`'s existing T03-era test methods are
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T06#7

- **criterion:** `scripts/sync-scaffold.sh` has been run and the vendored copy is
- **oracle:** `cmp -s plugins/specfuse/skills/derive-agent-policy/SKILL.md .specfuse/skills/derive-agent-policy/SKILL.md`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T06#8

- **criterion:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **oracle:** `python3 -m unittest tests.test_agent_policy_key_ownership tests.test_derive_agent_policy_review_mode tests.test_groom_backlog_skill tests.test_skills_vendored_in_sync -v`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
