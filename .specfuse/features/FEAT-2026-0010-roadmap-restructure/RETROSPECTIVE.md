---
feature: FEAT-2026-0010
gate: 1
correlation_id: FEAT-2026-0010/G1-RETRO
written_by: WU-90-gate-1-retrospective
---

# Gate 1 Retrospective — Mechanics and migration

## Per-WU analysis

### T01 — Create roadmap-archive.md and add Detail column

**What worked.** Cleanest WU in the gate. One attempt, no deviations. Produced both
target files (`roadmap-archive.md` and the Detail column addition) within the single
squash commit. The acceptance-criteria checklist (anchor string, back-link string,
placeholder comment) gave the agent exact strings to match, which kept the output
byte-reproducible for downstream WUs.

**What failed.** Nothing failed.

**Attempts.** 1

**Rule/template gaps.** None surfaced. The escalation triggers (irregular table row
widths, interleaved prose) were not tripped.

**Cost / duration.** `cost_usd: 0.381761` / `duration_seconds: 140.664`

---

### T02 — Ship the roadmap-archive skill

**What worked.** Completed in one attempt. The skill was produced with `--auto` mode,
per-ID mode, idempotency, and refusal of `planned`/`active` rows, all as specified.
The self-test (`tests/test_roadmap_archive_skill.py`) was emitted and the symlink
created. The commit timestamp (12:56:52 EDT) is consistent with the WU's
reported duration of 532.187 s after T01's commit (12:47:59 EDT).

**What failed.** The driver did not emit `task_started` or `task_completed` events
for T02. `events.jsonl` jumps from T01 directly to T03. T02's accounting is
preserved only in its WU frontmatter (`cost_usd`, `duration_seconds`, `attempts`),
not in the append-only event log. This is a driver-side observability gap: any
downstream analysis that reads only `events.jsonl` (e.g., this retrospective WU)
cannot reconstruct T02's wall-clock span from the log alone.

**Attempts.** 1 (WU frontmatter; not independently verifiable from events.jsonl).

**Rule/template gaps.** The driver's event-emission loop has an untested edge case
where at least one WU can complete without its events landing in the log. Root cause
is not visible from this retrospective's read-only vantage point; flagged as a
structural correctness gap (see section below).

**Cost / duration.** `cost_usd: 1.160804` / `duration_seconds: 532.187`

---

### T03 — Ship the roadmap-add skill

**What worked.** Delivered the skill, tests, and symlink. The three-source next-ID
scan (roadmap table, feature PLAN.md files, LEARNINGS/RETROSPECTIVE references) was
implemented and tested. The headless `--id`/`--title`/`--slug`/`--why`/`--goal`/
`--benefits` mode was produced.

**What failed.** Attempt 1 ran for 459.198 s and was rejected (cost: $1.102973,
24 649 output tokens). Attempt 2 succeeded in 300.485 s (cost: $0.571696, 8 066
output tokens). The sharply lower output-token count on attempt 2 suggests attempt 1
produced a bloated or structurally incorrect artifact that failed one of the
verification gates (likely the `python3 -m unittest discover` suite or the
frontmatter sanity grep). Specific failure evidence is not preserved in
`events.jsonl` — the driver records cost/duration per attempt but not the failure
reason.

**Attempts.** 2

**Rule/template gaps.** The WU spec required the next-ID scan to cover three sources.
This multi-source scan is subtle and likely contributed to the first-attempt failure.
A template or helper that enumerates scan sources explicitly (similar to how T01
enumerated exact anchor/back-link strings) would reduce the surface for off-by-one
errors in future ID-allocation WUs.

**Cost / duration.** `cost_usd: 1.674669` / `duration_seconds: 759.683`

---

### T04 — Migrate FEAT-2026-0003..0008 detail sections to the archive

**What worked.** Completed in one attempt. All six target sections were moved to the
archive; all six Detail cells were updated with back-links; the main roadmap shed
223 lines (647 → 424). The grep assertions in AC 1 and 2 (`0` inline headings, `6`
archive headings) are satisfied. No rows outside the six targets were modified.
T04's `input_tokens: 606` (versus T01's 13 and T03's 52/28) reflects the agent
reading the full roadmap before acting — expected for a migration WU.

**What failed.** Nothing failed.

**Attempts.** 1

**Rule/template gaps.** T04's WU noted "if additional `done` rows beyond 0003..0008
with inline detail are found, do NOT migrate them." At execution time no such
additional rows were present, so the trigger was not tripped. The guard is correct
but was untested by this gate run.

**Cost / duration.** `cost_usd: 0.915790` / `duration_seconds: 582.829`

---

## Gate-level summary

### Totals

| WU  | Attempts | Duration (s) | Cost (USD) |
|-----|----------|-------------|------------|
| T01 | 1        | 140.664     | 0.381761   |
| T02 | 1        | 532.187     | 1.160804   |
| T03 | 2        | 759.683     | 1.674669   |
| T04 | 1        | 582.829     | 0.915790   |
| **Gate total** | **5** | **2015.363** | **4.133024** |

### Dispatch order

T01 → T02 → T03 → T04, strictly sequential. This matches the stated dependency chain
(T02 and T04 depend on T01; T04 depends on T02). No parallelism was used; no WU was
dispatched out of order.

### Spinning

No WU spun. The closest was T03 at 2 attempts; the threshold is 3. Gate 1 did not
trigger the spinning-threshold escalation path.

### T02 `--auto` flag and T04 interaction

No surprising interaction observed. T04 implements the migration by editing
`.specfuse/roadmap.md` and `.specfuse/roadmap-archive.md` directly — following the
same algorithm T02's skill would execute — rather than subprocess-invoking the skill
file. The `--auto` flag on the T02 skill is a feature for human operators running the
skill interactively; it was irrelevant to T04's execution context (an LLM agent
directly editing files). Because T04 does not call the skill as a subprocess, there
was no risk of `--auto` inadvertently archiving rows outside 0003..0008.

### Roadmap.md line-count delta

Pre-gate (branch base, commit `a3d65ed`): **647 lines**.  
Post-gate (HEAD, after T04): **424 lines**.  
Net delta: **−223 lines**.

The archive file grew to 275 lines (6 anchored sections plus the scaffold header).
The total content (roadmap + archive) went from 647 + 0 = 647 to 424 + 275 = 699
lines — the 52-line increase is accounted for by the 6 anchor lines prepended per
section, the blank separators added at the archive marker, and the scaffold header
written by T01.

### User-visible behaviour not predicted in the design

None observed by the feature's own test suite or lint gates. One marginal
observability effect: the main `.specfuse/roadmap.md` is now shorter, so a `cat`
or scroll of that file no longer shows the historical feature narratives inline.
Users or tooling that read `roadmap.md` to understand past features must now follow
the back-links. This was the intended behaviour; the design predicted it but did not
prescribe any migration notice or README update — an omission that Gate 2 docs WU
(WU-92) should close.

---

## Structural correctness gaps

1. **T02 event-emission gap.** `events.jsonl` has no entries for
   `FEAT-2026-0010/T02`. The driver updated T02's WU frontmatter but did not
   append `task_started` / `task_completed` events. Any audit, billing reconciliation,
   or retro synthesis that relies solely on `events.jsonl` will undercount Gate 1's
   actual cost by ~$1.16 and undercount the completed WU count by 1. The gap is not
   recoverable from the log; it is only reconstructible from the WU frontmatter and
   commit timestamps. Root cause: driver-side bug (unconfirmed from this read-only
   vantage; recommend a driver test asserting event count equals WU count per gate
   run).

2. **Attempt-failure evidence not preserved.** T03 required 2 attempts; the reason
   attempt 1 was rejected is not recorded in `events.jsonl` or the WU file. Future
   retros can only infer the failure from the delta in output-token counts between
   attempts. The driver should append a `task_attempt_failed` event (or a `reason`
   field on the attempt payload) so retrospective WUs can surface precise root causes
   without guesswork.

3. **T03 next-ID scan under-specification risk.** The three-source scan is described
   in prose in the WU and in the skill. No canonical list of scan sources is machine-
   readable (e.g. in `.specfuse/rules/` or a config file). If a fourth source of FEAT
   IDs is added in a future gate (e.g. a `pending/` staging folder), both the skill
   and any WU that replicates the scan logic would need manual updates. A rules file
   enumerating authoritative ID sources would prevent silent under-counting.

---

## Generalizable lessons (candidates for LEARNINGS.md)

1. Anchor strings and back-link strings specified as literal exact-match values in
   the foundation WU (T01) propagated cleanly through dependent WUs (T02, T04)
   without drift. This pattern — "name load-bearing strings once, reference them
   by quoting the exact text" — is reliable.

2. Interactive skill WUs that ship `--auto` batch modes need an explicit note about
   whether downstream dogfood WUs are expected to subprocess-invoke the skill or
   re-implement its algorithm directly. T04 re-implemented; T02 shipped the skill.
   The resulting behaviour was correct, but the contract was implicit.

3. When a WU requires scanning multiple heterogeneous sources for a global property
   (next available ID, highest sequence number), the first attempt is more likely to
   fail than for single-source tasks. Enumerating sources in a machine-readable rules
   file rather than WU prose reduces per-attempt failure rate.

4. Missing driver events (gap #1 above) are only detectable by cross-checking WU
   frontmatter against `events.jsonl`. The retro process itself is the detection
   mechanism — which is fragile. A gate-close assertion (event count == WU count)
   should run before the driver marks a gate `passed`.

---

## Focus areas for Gate 2

Gate 2 planning WU (WU-93) should address:

- **WU-91 (lessons):** Promote items 1–4 above to `.specfuse/LEARNINGS.md`.
- **WU-92 (docs):** Update the feature's own roadmap entry and README to document
  the two-file split and the back-link convention for new contributors.
- **WU-93 (plan-next):** Confirm Gate 2 scope or close the gate if Gate 1 covered
  everything required. At minimum, the driver event-emission gap (#1 above) warrants
  a follow-up work unit in the driver subsystem (likely a separate feature); the
  plan-next WU should decide whether to file it here or as a new feature.

---

# Gate 2 Retrospective — Driver auto-archive hook

---
feature: FEAT-2026-0010
gate: 2
correlation_id: FEAT-2026-0010/G2-RETRO
written_by: WU-94-gate-2-retrospective
---

## Per-WU analysis

### T05 — Driver auto-archive hook on feature completion

**What worked.**

- The implementation strategy (re-implement the skill algorithm directly in Python rather than
  subprocess-invoking the skill) was correct. The `auto_archive_feature` function was delivered
  as a standalone top-level function with the exact wire-format return strings (`"archived"`,
  `"already archived"`, `"refused: <reason>"`), matching the skill's single-feature algorithm
  Steps 1–6 verbatim.
- The load-bearing string literals — anchor `<a id="feat-yyyy-nnnn"></a>` and back-link
  `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)` — were reproduced byte-exactly by lowercasing
  the feature ID. All three test cases assert these exact strings, and the tests pass.
- The `run()` integration hook landed in the correct location: after
  `write_frontmatter_field(... "status", "complete")` and before `return 0`. Refused outcomes
  print a warning and do not abort the driver (feature is `complete`; operator can run
  `/roadmap-archive` manually). This is the correct non-fatal posture for a best-effort hook.
- The test file (`tests/test_loop_auto_archive.py`) exercises all three required cases: happy
  path, idempotency, and refusal. Idempotency is verified by byte-equal file comparison after
  the second call. No `git init` was required or used in the fixture; `tempfile.TemporaryDirectory(
  ignore_cleanup_errors=True)` was used as prescribed.
- The `_loop_loader.py` import shim (pre-existing from earlier gates) allowed `loop.py` to be
  imported directly from `.specfuse/scripts/` without packaging changes. The test used this
  pattern cleanly.
- The commit squash touched exactly the two substantive files (`loop.py` and
  `tests/test_loop_auto_archive.py`) plus the driver-managed WU frontmatter update — correct.

**What failed and why.**

T05 required 2 attempts. Attempt 1 ran 429.751 s and produced 19 567 output tokens; attempt 2
ran 411.281 s and produced 18 735 output tokens. The attempt-1 failure reason is not preserved
in `events.jsonl` (the driver records cost/duration per attempt but not the rejection cause —
the same gap documented in Gate 1 structural correctness item #2). From available evidence:

- Token counts are similar between attempts, ruling out a catastrophic structural failure
  (attempt 1 was not an empty or radically wrong artifact).
- The most likely failure gate is one of the scoped verification commands: the regex used to
  extract the inline section (`section_re`) or the column-index arithmetic in the row-update
  step may have produced an off-by-one result that the test assertions caught but a visual
  read did not flag. Alternatively, `ruff check` or `coverage --fail-under=90` may have
  caught a style or branch-coverage gap in attempt 1.
- Because attempt-1 failure evidence is not preserved, this remains inference, not confirmed
  root cause.

**Attempts.** 2

**Rule/template gaps.**

The WU specified the regex anchor/back-link strings by prose description (referencing the
`roadmap-archive.md` Conventions section and SKILL.md). Attempt 2 succeeded, so the strings
landed correctly, but the two-attempt trajectory suggests the first attempt's regex for the
Detail-cell update (`detail_start`/`detail_end` offset arithmetic relative to the row match
object) was fragile. A reference fixture showing an exact before/after for the row mutation
would reduce per-attempt failure rate for regex-heavy file-mutation WUs.

**Cost / duration (from T05 frontmatter).**

`cost_usd: 2.052703` / `duration_seconds: 841.032`

Attempt breakdown (from `events.jsonl`):

| Attempt | Duration (s) | Cost (USD)  | Output tokens |
|---------|-------------|-------------|---------------|
| 1       | 429.751     | 1.194742    | 19 567        |
| 2       | 411.281     | 0.857961    | 18 735        |
| **Total** | **841.032** | **2.052703** | **38 302**  |

---

## Gate-level summary

### Totals

| WU  | Attempts | Duration (s) | Cost (USD) |
|-----|----------|-------------|------------|
| T05 | 2        | 841.032     | 2.052703   |
| **Gate total** | **2** | **841.032** | **2.052703** |

Gate 2 was a single-WU gate. No parallelism was possible or attempted.

### Spinning

T05 did not spin. Two attempts against a three-attempt threshold. Gate 2 did not trigger the
spinning-threshold escalation path.

### Idempotency path — production vs test suite

The `auto_archive_feature` idempotency path (the `"already archived"` return branch, triggered
when `"roadmap-archive.md#"` is found in the Detail cell) was exercised only by the test suite
at T05 dispatch time. It has not been exercised by an actual feature-complete dispatch: FEAT-2026-0010
itself is the first feature whose `loop.py` contains the hook, and the hook will fire for the
first time in production when this feature's own `PLAN.md` is flipped to `complete`. Whether
the idempotency guard is exercised on that first dispatch depends on whether `wrap-feature` or
the driver's completion branch is invoked first.

### Helper and `commit_bookkeeping` interaction

No surprising interaction. `auto_archive_feature` is a pure file-mutation function: it reads
and writes `.specfuse/roadmap.md` and `.specfuse/roadmap-archive.md`, then returns a status
string. It does not stage, commit, or touch the git index. The driver's existing
`commit_bookkeeping` flow treats those edits as part of the normal working-tree diff for the
WU's squash commit — no special handling was needed. This is the correct separation: the
helper is a file transformer; the driver owns all git operations.

The only non-obvious interaction is timing: if the completion branch fires during a run where
the working tree already has staged changes (e.g., if a future refactor stages files before
calling `auto_archive_feature`), those staged changes would be included in the commit. No such
case exists today, but it is a latent coupling to note for any future refactor of the
completion branch.

---

## Structural correctness gaps

1. **Idempotency path exercised only by tests.** The `"already archived"` branch in
   `auto_archive_feature` is test-validated but not production-validated as of Gate 2 close.
   The first production exercise will occur when FEAT-2026-0010 itself completes. If the Detail
   cell format written by `commit_bookkeeping` (or by `wrap-feature`) differs from the exact
   string `"roadmap-archive.md#"` the guard tests for, the guard will fail silently — calling
   `auto_archive_feature` a second time would attempt to re-archive an already-archived section.
   Low probability, but worth a smoke-test at feature-close.

2. **Column-index regex fragility.** `auto_archive_feature` locates the Detail cell via capture
   groups on a pipe-delimited regex: group 4 = Detail. If the roadmap table ever gains an
   additional column between Folder and Detail (or columns are reordered), the column-index
   arithmetic will silently target the wrong cell and corrupt the row without raising an error.
   The helper has no column-header verification step. A future hardening WU should match
   columns by header name rather than positional index.

3. **Attempt-failure evidence still not preserved.** T05's attempt 1 failure is unrecoverable
   from `events.jsonl`. This is the same gap documented in Gate 1 structural correctness item
   #2. Gate 2 did not close it; it remains an open driver bug.

---

## Generalizable lessons (candidates for LEARNINGS.md)

1. For regex-heavy row-mutation WUs (where the agent must compute byte-offset arithmetic
   against a match object), providing a concrete before/after fixture in the WU spec reduces
   first-attempt failure rate. T05's two-attempt trajectory is consistent with offset-arithmetic
   fragility in attempt 1.

2. A helper that is fully test-validated but not yet exercised in production (T05's idempotency
   path) should be flagged explicitly in the plan-next WU so the feature-close checklist
   includes a smoke-test. Do not rely on test coverage alone for paths that depend on the
   exact byte content of files written by other tools.

3. The "re-implement the algorithm directly in Python" pattern (established in T04, repeated in
   T05) scales correctly to driver-side helpers. The alternative — subprocess-invoking the
   skill — is brittle in the driver's execution context and was correctly ruled out in both
   gates. This pattern should be elevated to a LEARNINGS entry as a settled decision.

---

## Focus areas for Gate 2 close-out (plan-next WU)

- Confirm the idempotency path fires correctly when FEAT-2026-0010 itself completes (the first
  production exercise of the hook). If wrap-feature runs before the driver's completion branch,
  the roadmap entry may already have a back-link; the guard should return `"already archived"`
  cleanly.
- File a follow-up feature or task for column-header verification in `auto_archive_feature`
  (gap #2 above).
- Promote the "re-implement algorithm directly" pattern and the "fixture-driven exact-string
  spec" lesson to `.specfuse/LEARNINGS.md` (gap from this gate's generalizable lessons).

---

## Feature verdict

Written by `G2-PLAN` (WU-97). Terminal-gate verdict for FEAT-2026-0010.

### Scope IN — delivered

PLAN.md does not carry an explicit `## Scope IN` heading; the in-scope set is
named by the intro paragraph and the `roadmap_goal` frontmatter. Per that
source:

| Scope IN item | Delivered by | Evidence |
|---|---|---|
| Split `.specfuse/roadmap.md` so the hot file carries `planned` / `active` detail sections only | T01 (scaffold + Detail column add) + T04 (migrate 6 done sections out) | Main roadmap 647 → 424 lines (−223); `grep`-asserted 0 inline `## FEAT-2026-0003..0008` headings post-T04 |
| `.specfuse/roadmap-archive.md` holds `done` / `abandoned` detail sections | T01 (scaffold + Conventions section with literal anchor / back-link strings) + T04 (populated 6 anchored sections) | Archive file at 275 lines; 6 `<a id="feat-yyyy-NNNN"></a>` anchors |
| New `Detail` back-link column on the main roadmap table | T01 | Column header present; cells `—` for non-archived rows, `[→ archive](roadmap-archive.md#...)` for the 6 migrated rows after T04 |
| `roadmap-add` skill | T03 | `.specfuse/skills/roadmap-add/SKILL.md` + symlink; `tests/test_roadmap_add_skill.py` passes; three-source next-ID scan implemented |
| `roadmap-archive` skill | T02 | `.specfuse/skills/roadmap-archive/SKILL.md` + symlink; `tests/test_roadmap_archive_skill.py` passes; per-ID and `--auto` batch modes both shipped; refuses `planned` / `active` rows |
| Dogfood migrate FEAT-2026-0003..0008 detail sections | T04 | All 6 sections moved; all 6 Detail cells now carry back-links; no row outside 0003..0008 touched |
| Driver auto-archive hook (added to Scope IN at Gate 1 plan-next; see disposition table below for Scope OUT origin) | T05 | `auto_archive_feature` helper in `.specfuse/scripts/loop.py`, called from the `gate is None` completion branch after `status: complete` flip; `tests/test_loop_auto_archive.py` covers happy / idempotent / refused paths |

### Scope OUT — disposition

| Scope OUT item (PLAN.md) | Disposition | Routed to |
|---|---|---|
| New roadmap columns (CI / BV / TF / R / Budget / Score) | Routed | FEAT-2026-0011 (planned in `.specfuse/roadmap.md`) |
| `scoring-criteria.md`, `priorities/<period>.yml`, weighting, scoring formula, `roadmap-rank` skill, `roadmap-estimate` skill | Routed | FEAT-2026-0011 (planned) |
| Auto-archive hook in `loop.py` at PLAN status flip | **Delivered in this feature.** PLAN.md flagged this as "manual-first cut; auto follow-up after this feature lands"; Gate 1 plan-next (`G1-PLAN`, `GATE-01-REVIEW.md`) reconsidered and routed it back as Gate 2 T05 rather than spawning a new feature, because the scope (one driver function + smoke test) was small enough to land on this branch | T05 (this feature) |
| Orchestrator-level cross-repo aggregation | Routed | Deferred to a future feature once the orchestrator exists. Named in PLAN.md Scope OUT as such; no orchestrator exists today so no FEAT-ID can be minted yet |
| Rewriting prose content of any feature's detail section (Why, Goal, Benefits, Verification) | Consciously dropped | T04 confirmed split-only: 6 sections moved verbatim, no prose re-authored. Re-author work is not planned |

### Per-gate cost and duration

| Gate | Substantive WUs | Total attempts | Duration (s) | Cost (USD) |
|---|---|---|---|---|
| Gate 1 | T01, T02, T03, T04 | 5 | 2 015.363 | 4.133024 |
| Gate 2 | T05 | 2 | 841.032 | 2.052703 |
| **Feature total (substantive WUs only)** | **5** | **7** | **2 856.395** | **6.185727** |

Closing-sequence WUs (G1-RETRO / G1-LESSONS / G1-DOCS / G1-PLAN, then
G2-RETRO / G2-LESSONS / G2-DOCS / G2-PLAN) are not aggregated above — they
are methodology overhead, not feature work, and each landed in one attempt
apiece per Gate 1 RETRO and Gate 2 RETRO.

### Roadmap-goal verdict

`roadmap_goal` (from PLAN.md frontmatter): *".specfuse/roadmap.md carries
detail sections only for planned/active features; done/abandoned details
live in .specfuse/roadmap-archive.md; roadmap-add and roadmap-archive
skills exist; current done features (0003..0008) migrated."*

**Met.** Every clause shipped: the main roadmap was cleaved (−223 lines,
6 detail sections moved); the archive file was created with the
back-link / anchor convention pinned in its `## Conventions` section; both
skills are in `.specfuse/skills/` with self-tests passing; the six named
done features (FEAT-2026-0003 through 0008) all carry `[→ archive]`
back-links in their Detail cell and no longer have inline detail in the
hot file. Beyond the literal goal, T05 added the driver auto-archive hook
so future features close cleanly without an operator step. The
first production exercise of the hook fires on this feature's own
completion — flagged in Gate 2 RETRO as a smoke-test to watch on the
next `loop.py` run — but that exercise happens after this WU commits and
PLAN.md flips, not during this WU. Feature ready for the close ceremony.
