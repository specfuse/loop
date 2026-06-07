---
id: FEAT-2026-0003/T03
type: implementation
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Adopt a picked issue into a dispatchable feature folder (script)

**Objective.** Add `.specfuse/scripts/adopt_feature.py`: a scaffolding script
that turns a picked `specfuse:feature` candidate (from `gh_features.list_features`)
into a dispatchable loop-feature folder under `.specfuse/features/`, seeded from
the issue body's five sections, recording the source issue URL and the
`initiative:` label — fully unit-tested with a stub `gh` runner.

**Context.** This is `FEAT-2026-0003/T03`, gate 2 of the GitHub feature-pick
build (the "write path — adopt"). Step 2 of the capability in
[`docs/handoff-github-feature-pick.md`](../../../docs/handoff-github-feature-pick.md)
§3: "turn a picked issue into a loop feature folder under `.specfuse/features/`,
using the issue ID as the feature ID (`INIT-2026-0001/F03` → a folder/PLAN the
loop can run; pick a filesystem-safe encoding, e.g. `INIT-2026-0001-F03-<slug>`).
The issue body's five sections seed the feature's gate-1 authoring; record the
source issue URL + the `initiative:` label." Gate 1 already shipped
`gh_features.list_features` (`.specfuse/scripts/gh_features.py`) returning
candidate dicts with `feature_id`, `title`, `initiative`, `task_type`, `autonomy`,
`url`, and `number`. The `gh` JSON fetch already requests the issue `body`, but
`list_features` discards it before returning — this WU widens the candidate dict
to expose `body` (a one-line change in gh_features.py; see AC 0 below) so the
scaffolder has the issue contract to embed verbatim. No other change to gate 1.

Filesystem-safe encoding: `INIT-YYYY-NNNN/FNN` → `INIT-YYYY-NNNN-FNN` (the single
`/` becomes `-`); `FEAT-YYYY-NNNN` is unchanged. Slug: lowercase the candidate's
title, replace runs of non-`[a-z0-9]` with a single `-`, strip leading/trailing
`-`.

Reference the binding rules under `.specfuse/rules/` (`result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`) and the per-WU
craft in `.specfuse/skills/authoring-work-units/SKILL.md`. The PLAN and GATE
templates live under `.specfuse/templates/`. Mirror the injectable-runner pattern
used by `gh_features.py` (default runner shells `gh`; tests inject a stub).

**Acceptance criteria.**
0. `gh_features.list_features` is widened so each returned candidate dict carries
   a `body` key whose value is `issue.get("body", "")`. This is a single-line
   addition inside the existing dict literal in `list_features`. No other change
   to `gh_features.py`. `tests/test_gh_features.py` gains one assertion that the
   new key is present and equals the expected body string in the stubbed input;
   no existing assertion is removed or weakened.
1. `adopt_feature.py` defines `adopt_feature(candidate: dict, root: Path) -> Path`
   that creates `<root>/<encoded_id>-<slug>/` and returns the created folder path.
   `encoded_id` maps `INIT-YYYY-NNNN/FNN` → `INIT-YYYY-NNNN-FNN` and leaves
   `FEAT-YYYY-NNNN` unchanged. `slug` is derived from `candidate["title"]` by
   lowercasing, replacing runs of non-`[a-z0-9]` with a single `-`, and trimming.
2. The created folder contains exactly eight files: `PLAN.md`, `GATE-01.md`,
   `GATE-02.md`, `WU-01-<slug>.md`, `WU-90-gate-1-retrospective.md`,
   `WU-91-gate-1-lessons.md`, `WU-92-gate-1-docs.md`,
   `WU-93-gate-1-plan-next.md`. No other files.
3. `PLAN.md` has frontmatter with keys `feature_id` (= `candidate["feature_id"]`),
   `title` (= `candidate["title"]`), `slug`, `branch` (=
   `feat/<encoded_id>-<slug>`), `roadmap_goal` (= `candidate["title"]`),
   `autonomy_default` (= `candidate["autonomy"]` or the literal `review`),
   `status: planned`, `source_issue_url` (= `candidate["url"]`), and `initiative`
   (= `candidate["initiative"]`; the key is **omitted** when the value is `None`
   rather than emitted as the string `"None"` — per LEARNINGS
   `[FEAT-2026-0003/G1-LESSONS]` on absent-field rendering). PLAN.md's body
   carries a `gates` graph (a fenced ```yaml block) with gate 1 listing T01 +
   four closing WUs in dependency order, and gate 2 + gate 3 stubs with empty
   `work_units` lists.
4. `WU-01-<slug>.md` has frontmatter `id: <candidate["feature_id"]>/T01`,
   `type: <candidate["task_type"]>` when truthy else `implementation`, `model:
   claude-sonnet-4-6`, `status: draft`, `attempts: 0`. Its body is `#
   <candidate["title"]>` on the first line, then a blank line, then an
   `**Objective.** TODO` placeholder line, then a blank line, then `candidate["body"]`
   verbatim (which itself carries the five mandatory sections per the issue
   contract — Context / Acceptance criteria / Do not touch / Verification /
   Escalation triggers).
5. The four closing-sequence WUs (`WU-90`..`WU-93`) carry the canonical
   frontmatter (`id: <feature_id>/G1-RETRO`..`G1-PLAN`, types `retrospective` /
   `lessons` / `docs` / `plan-next`, model `claude-sonnet-4-6` for the first three
   and `claude-opus-4-7` for `plan-next`, `status: draft`, `attempts: 0`) and a
   template body for each that contains the five mandatory sections (Context,
   Acceptance criteria, Do not touch, Verification, Escalation triggers).
   `GATE-01.md` carries frontmatter `gate: 1, status: open` and a one-line
   definition-of-done summarizing the issue title. `GATE-02.md` carries
   frontmatter `gate: 2, status: open` and the canonical "drafted by gate 1's
   plan-next" placeholder.
6. After write, `python3 .specfuse/scripts/lint_plan.py <created_folder>` exits 0
   on both the orchestrated-INIT and component-local-FEAT test fixtures.
7. CLI: `python3 .specfuse/scripts/adopt_feature.py <repo> <issue-number>` calls
   `gh_features.list_features(repo)` (accepting an injectable `--runner` for
   tests), filters the result to the entry whose `number` matches `<issue-number>`,
   invokes `adopt_feature(candidate, root=Path(".specfuse/features"))`, prints
   the created folder's path on stdout (one line), and exits 0. If no candidate
   matches, the CLI prints a one-line error to stderr (e.g. `no specfuse:feature
   issue with number <n> in <repo>`) and exits 1. The CLI MUST use
   `subprocess` with an argument list (no `shell=True`) wherever it shells out,
   and never read or echo `GH_TOKEN`.
8. `tests/test_adopt_feature.py` covers: (a) an orchestrated candidate
   (`INIT-2026-0001/F06`, with `initiative` set) → asserts folder name is
   `INIT-2026-0001-F06-<slug>`, `PLAN.md` frontmatter contains the `initiative`
   key, `WU-01-<slug>.md` frontmatter `id` is `INIT-2026-0001/F06/T01`, and the
   body contains the headings `Context`, `Acceptance criteria`, `Do not touch`,
   `Verification`, `Escalation triggers`; (b) a component-local candidate
   (`FEAT-2027-0001`, no initiative) → asserts the `initiative` key is absent
   from PLAN.md frontmatter and the folder name is `FEAT-2027-0001-<slug>`;
   (c) `lint_plan.py <created_folder>` exits 0 for both; (d) the CLI invoked
   with a stub `--runner` produces the expected folder and stdout; (e) a
   malformed-body candidate whose stubbed `body` omits one of the five required
   sections (e.g. drops `Escalation triggers`) → `adopt_feature` still writes
   the folder, but `python3 .specfuse/scripts/lint_plan.py <created_folder>`
   exits non-zero, proving the linter rejects the missing section on the draft
   `WU-01`. No live `gh` call.

**Do not touch.** `.specfuse/scripts/loop.py`, `.specfuse/scripts/lint_plan.py`,
`.specfuse/scripts/_miniyaml.py`, any existing folder under `.specfuse/features/`,
any binding rule under `.specfuse/rules/`, any skill under `.specfuse/skills/`,
generated directories, secrets (`.env`, `*.pem`, `*.key`, credential files;
never read `GH_TOKEN`'s value), `.git/`. The driver owns all git — edit files
only. This WU touches **exactly four files**: two new
(`.specfuse/scripts/adopt_feature.py`, `tests/test_adopt_feature.py`) and two
modified (`.specfuse/scripts/gh_features.py` — only the one-line widening of
`list_features`'s candidate dict to include `body`; and `tests/test_gh_features.py`
— only the addition of an assertion for the new field). Any other edit to
gh_features.py or its tests is out of scope.

**Verification.** The `code` gates in `.specfuse/verification.yml`: the full
test suite (`python3 -m unittest discover -s tests -v`), `ruff` lint, `bandit`
security scan (must stay clean — argument-list `subprocess` calls), and coverage
`--fail-under=70` (the new script must be exercised by the new tests).

**Escalation triggers.** If the issue body's structure varies enough across real
`specfuse:feature` issues that the verbatim-embed-into-WU-01 strategy would
produce a WU that fails `lint_plan` (e.g. a body that uses non-standard heading
levels for the five sections, breaking the linter's `^#+\s*<section>` match),
stop and emit `status: blocked` naming the gap — the right fix is a body-parsing
step, but that is its own WU. If the filesystem-safe encoding for an
`INIT-…/FNN` ID collides with an existing folder under `.specfuse/features/`
(would overwrite), block — never overwrite. If `gh_features.list_features` does
not expose the issue `body` field on its returned candidate, block: the body is
the contract — a gate-1 change is the right answer, not a workaround here.
