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
