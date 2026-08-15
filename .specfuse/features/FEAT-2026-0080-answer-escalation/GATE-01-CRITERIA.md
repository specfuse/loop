# Gate 1 — per-criterion close state

Written by `FEAT-2026-0080/G1-CLOSE`, attempt 1 of the re-armed close.
`kind` and `state` are recorded by the close that ran the oracle, per
`.specfuse/rules/close-discipline.md` §5 — never inferred by a reader.

Every entry is `narrow`: each is proved by a scoped, countable oracle (a named
test module, a byte-identity `diff`, or a structural assert), so its green is
sound to carry forward across close attempts. The feature-level full `code` gate
set is a `broad` oracle and re-ran unconditionally this attempt; it is recorded
in `RETROSPECTIVE.md` § *Oracles re-run fresh for this close*, not carried here.

### T01#1

- **criterion:** `tests/test_answer_escalation_skill.py::TestAnswerEscalationSkill::test_skill_file_exists_in_both_trees`
  fails on HEAD before this WU runs, and the failure is recorded
- **oracle:** `python3 -m unittest tests.test_answer_escalation_skill -v` (passes now); red-before verified structurally — `plugins/specfuse/skills/answer-escalation/SKILL.md` is absent at `048f036^`, so the test necessarily failed there
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#2

- **criterion:** `plugins/specfuse/skills/answer-escalation/SKILL.md` exists with YAML frontmatter carrying `name:` and a `description:` naming its trigger phrases
- **oracle:** `tests.test_answer_escalation_skill.TestAnswerEscalationSkill.test_frontmatter_names_the_skill_and_trigger_phrases`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#3

- **criterion:** `.specfuse/skills/answer-escalation/SKILL.md` is byte-identical to the canonical copy
- **oracle:** `diff plugins/specfuse/skills/answer-escalation/SKILL.md .specfuse/skills/answer-escalation/SKILL.md` → exit 0; also `tests...test_canonical_and_vendored_skill_are_byte_identical`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#4

- **criterion:** `SKILL.md` states the skill is human-invoked only and must not run headless, with the reason
- **oracle:** `tests...test_human_invoked_only_and_headless_reason_stated`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#5

- **criterion:** `SKILL.md` names all four dispositions — hand off, answer, close, skip — each as its own documented step
- **oracle:** `tests...test_all_four_dispositions_documented_as_own_step`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#6

- **criterion:** `SKILL.md` carries the category-to-owning-skill routing table with an entry for every value in `escalation.CATEGORY_LABELS`
- **oracle:** `tests...test_routing_table_covers_every_category_label_exactly`; independently confirmed by printing `sorted(CATEGORY_LABELS)` → `['blocked-wu', 'drafting-needed', 'gate-review', 'merge-approval', 'triage-question']`, all five present in the table
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#7

- **criterion:** `SKILL.md` documents the guidance-comment marker `<!-- specfuse:operator-guidance id=<correlation_id> -->`
- **oracle:** `tests...test_guidance_marker_documented`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#8

- **criterion:** `SKILL.md` states the write order explicitly — guidance comment first, label release second — and gives the reason
- **oracle:** `tests...test_write_order_documented_with_reason`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#9

- **criterion:** `SKILL.md` states that `skip` writes nothing at all: no comment, no label edit, no issue state change
- **oracle:** `tests...test_skip_writes_nothing_documented`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#10

- **criterion:** `SKILL.md` states the skill triggers no fix and no retry: never invokes `/fix-bug`, never opens a PR, never merges
- **oracle:** `tests...test_triggers_no_fix_and_no_retry`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#11

- **criterion:** `SKILL.md` documents graceful degradation when `gh` is unavailable or unauthenticated
- **oracle:** `tests...test_gh_unavailable_degradation_documented`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T01#12

- **criterion:** All tests in `tests/test_answer_escalation_skill.py` pass after this WU's edits
- **oracle:** `python3 -m unittest tests.test_answer_escalation_skill -v` → 11 tests, OK
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_fix_bug_reads_comments.py::TestFixBugReadsComments::test_step_1_command_returns_comments`
  fails on HEAD before this WU runs, and the failure is recorded
- **oracle:** `python3 -m unittest tests.test_fix_bug_reads_comments -v` (passes now); red-before verified structurally — `.specfuse/skills/fix-bug/SKILL.md:65` reads `gh issue view <issue-number>` with no `--comments` at `43b2090^`, so the test necessarily failed there
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T02#2

- **criterion:** `.specfuse/skills/fix-bug/SKILL.md` Step 1 names a command that returns comment bodies — `gh issue view <issue-number> --comments`
- **oracle:** `tests...test_step_1_command_returns_comments`; confirmed by direct read of `.specfuse/skills/fix-bug/SKILL.md:65`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T02#3

- **criterion:** The canonical copy at `plugins/specfuse/skills/fix-bug/SKILL.md` carries the identical change, and a test asserts the two copies are byte-identical
- **oracle:** `diff plugins/specfuse/skills/fix-bug/SKILL.md .specfuse/skills/fix-bug/SKILL.md` → exit 0; `tests.test_fix_bug_headless...test_canonical_and_vendored_skill_are_byte_identical`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T02#4

- **criterion:** Step 1's prose states why comments matter to a retry
- **oracle:** `tests...test_step_1_explains_why_comments_matter_to_a_retry`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T02#5

- **criterion:** No other step of `/fix-bug` is reworded; a test asserts the headless halt-to-outcome mapping and the `refused` / `could_not_proceed` / `completed` definitions are unchanged
- **oracle:** `python3 -m unittest tests.test_fix_bug_headless -v` → 6 tests, OK (includes `test_headless_outcomes_are_closed_and_named`, `test_every_refusal_path_reachable_and_mapped_to_refused`, `test_every_could_not_proceed_path_reachable`)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T02#6

- **criterion:** `tests/test_fix_bug_headless.py` and `tests/test_fix_bug_diff_self_check.py` both still pass unchanged
- **oracle:** `python3 -m unittest tests.test_fix_bug_headless tests.test_fix_bug_diff_self_check -v` → OK
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`

### T02#7

- **criterion:** All tests in `tests/test_fix_bug_reads_comments.py` pass after this WU's edits
- **oracle:** `python3 -m unittest tests.test_fix_bug_reads_comments -v` → 3 tests, OK
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `114ea006848b107c2aaf47b97c658bda654eea6c`
- **attempt:** `1`
