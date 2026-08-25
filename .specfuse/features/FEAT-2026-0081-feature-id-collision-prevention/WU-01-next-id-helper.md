---
id: FEAT-2026-0081/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
produces_driver_helper: next_feature_id, scan_claimed_ids
produces:
  - specfuse/loop/feature_ids.py
  - tests/test_feature_ids.py
  - pyproject.toml
model: sonnet
effort: medium
---

# Extract the four-source next-ID scan from skill prose into a tested function

**Objective.** Ship `next_feature_id()` — the four-source scan that picks the
next `FEAT-YYYY-NNNN` — as a tested function plus a `specfuse-next-id` console
script, so the scan stops being markdown every caller re-derives and becomes one
implementation the skill, the lint, and gate 2's renumbering all read.

**Context.** First WU of FEAT-2026-0081; read `PLAN.md` in this folder for the
scope boundary and the existing-mechanism verdict. Today the scan exists **only
as prose** in `.specfuse/skills/roadmap-add/SKILL.md` § *Computing the next ID*.
Read that section first and treat it as the specification — this WU is an
extraction, and the four sources, the gap-filling ERROR, the already-exists
ERROR, and the GitHub-unreachable WARN are all defined there. **Do not redesign
the scan's semantics.** If the prose is ambiguous somewhere, that is a block, not
a judgement call.

The four sources, per that prose: the roadmap table, `PLAN.md` files,
`LEARNINGS`/`RETROSPECTIVE` files, and GitHub issue/PR titles and bodies when
reachable. Note #1644 investigated the GitHub query and found it **sound** — the
reported zero-result prefix was a query the skill never issues — so do not
"fix" the query shape; port it as specified. The contamination defect that
investigation surfaced was fixed separately as #1872.

`specfuse/loop/lint_roadmap.py` is the local precedent for how a repo-scoped
reader is built here: it returns structured findings rather than raising, on the
stated grounds that a linter which crashes cannot distinguish "found a problem"
from "could not look". Apply the same posture — an unreachable GitHub must
degrade to a warning in the return value, never an exception.

Console scripts live in `pyproject.toml`'s `[project.scripts]` alongside
`specfuse-loop`, `specfuse-lint`, `specfuse-stats`. Add `specfuse-next-id` there.
`specfuse next-id` as an umbrella subcommand is **out of scope** — that table
lives in another repo (PLAN.md scope boundary).

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`verification-discipline.md`) apply. Do not restate them.

**Acceptance criteria.**

- `tests/test_feature_ids.py::test_next_id_is_one_past_the_highest_claimed`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). Given fixture sources whose highest claimed ID is `FEAT-2026-0042`,
  `next_feature_id` returns `FEAT-2026-0043`.
- After this WU's edits that same test passes, and so does
  `tests/test_feature_ids.py::test_github_unreachable_degrades_to_a_warning` —
  an injected GitHub reader that fails produces a result carrying a warning and
  a next ID computed from the three in-tree sources, and **raises nothing**.
- `scan_claimed_ids` returns, per ID, the sources that claim it — not merely the
  maximum. A test asserts an ID claimed in two sources reports both. T02 and
  gate 2 both need the per-source detail; a function that returns only a max
  forces them to re-scan.
- All four sources are read. Four tests, one per source, each asserting an ID
  visible **only** in that source raises the computed next ID.
- The GitHub reader is **injected**, not called directly, so every test above
  runs with no network. A test asserts the default path is not exercised when a
  reader is supplied.
- `specfuse-next-id` is declared in `pyproject.toml`'s `[project.scripts]` and
  its entry point is importable: `python3 -c "from specfuse.loop.feature_ids
  import next_feature_id, scan_claimed_ids, main"` exits 0.
- Running the script against this repo prints an ID one greater than the highest
  currently claimed, and exits 0. Quote the output in your RESULT.
- The year boundary is explicit: `next_feature_id` takes the year as a parameter
  rather than reading a clock. A test asserts two different years compute
  independently. (`Date.now()`-style implicit time makes a function untestable
  and its result unreproducible.)
- Every new `subprocess.run` declares `check=` explicitly (`PLW1510`).

**Do not touch.** `specfuse/loop/lint_roadmap.py` (T02 owns it);
`.specfuse/skills/roadmap-add/SKILL.md` and `.specfuse/skills/draft-feature/SKILL.md`
(T03 owns the skill-side wiring — this WU ships the function, not its callers);
the umbrella CLI's delegation table, which is in another repo. `.git/`, secrets.
The driver owns git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` (tests, lint,
security, coverage ≥ 90%, leak-scan, the bats suites) plus the symbol-import
check and the live script run above. See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if `roadmap-add/SKILL.md`'s
*Computing the next ID* prose is ambiguous or self-contradictory on any of the
four sources, the gap-filling rule, or the already-exists rule — this WU is an
extraction and inventing semantics here would silently change what every caller
gets. Also block if extracting the scan cannot be done without changing what the
skill currently produces for this repo: a behavior change disguised as a
refactor is worse than either. If `next_feature_id` is absent from the files you
edited, emit `status: blocked` — do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
