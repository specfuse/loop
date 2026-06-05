# Rule: correlation IDs

Every unit of work in the loop carries a correlation ID that threads it through the
feature folder, the WU file, the event log, the branch, and the commit history.
This rule defines the format, the surfaces the ID must appear on, how the next ID
is chosen, and what to do when you see — or are about to produce — a malformed one.

[`docs/methodology.md`](../../docs/methodology.md) §1 is normative on the
correlation-ID scheme; this file is the operational reference every session reads
before emitting an ID.

## Format

Two shapes, and only two:

- **Feature-level:** `FEAT-YYYY-NNNN`
  - `YYYY` is the four-digit calendar year in which the feature was created.
  - `NNNN` is a zero-padded four-digit ordinal, unique within that year's roadmap.
  - Example: `FEAT-2026-0042`.
- **Task-level:** `FEAT-YYYY-NNNN/<task-id>`
  - The feature-level ID, a literal `/`, then the task identifier.
  - Substantive units use `TNN` — `T` followed by a zero-padded two-digit ordinal,
    unique within the feature. Example: `FEAT-2026-0042/T07`.
  - Closing-sequence units use `G<n>-<NAME>` — `G`, the gate number, a hyphen, and
    one of `RETRO`, `LESSONS`, `DOCS`, `PLAN`. Example: `FEAT-2026-0042/G1-RETRO`.
  - **Hygiene units** use `TNNH[N…]` — the *target* substantive WU's ordinal
    followed by a literal `H`, optionally suffixed with an ordinal when more
    than one hygiene WU precedes the same target. Example: `FEAT-2026-0042/T07H`
    (the hygiene WU for T07) and `FEAT-2026-0042/T07H1` / `T07H2` (two hygiene
    WUs preceding T07). See the "Hygiene units" subsection below for the
    semantic constraints; see `.specfuse/skills/authoring-work-units/SKILL.md`
    §7 for when to author one.

The combined pattern accepted across feature and task IDs is:

```
^FEAT-\d{4}-\d{4}(/(T\d{2}(H\d*)?|G\d+-(RETRO|LESSONS|DOCS|PLAN)))?$
```

A string that does not match is malformed.

### Hygiene units

A hygiene WU is a narrow precursor authored when a substantive WU blocks on a
pre-existing bug in a path its **Do not touch** rule forbids. Its ID's numeric
part is the **target** substantive WU's ordinal — `T02H` means "the hygiene WU
for T02", not "the hygiene WU number 2." This preserves the substantive WU's
number as a sort key and visually signals which cross-cutting fix this is.

- Single hygiene WU per target: `T<NN>H`. Example: `T02H`.
- Multiple hygiene WUs for the same target: `T<NN>H1`, `T<NN>H2`, … Example:
  `T02H1` and `T02H2` if T02 needs two unrelated pre-existing fixes.
- Hygiene WUs are full work units — they appear in the PLAN graph, are
  dispatched and verified by the loop, and produce their own squashed commit.
  Their type is typically `implementation`. The target WU's `depends_on`
  is updated to include the hygiene WU's ID.

The forward-only convention: a hygiene WU authored as `T<NN>H` need not be
renumbered later if the substantive WU graph shifts; the linkage by target
number is informational, not load-bearing in the graph (the load-bearing
relationship is `depends_on`).

## Where correlation IDs must appear

For every feature, the ID appears in:

- The feature folder name: `.specfuse/features/FEAT-YYYY-NNNN-<slug>/`.
- The `feature_id` field in `PLAN.md`'s frontmatter.
- The event log filename inside the feature folder: `events.jsonl` is per-feature,
  so the ID is implicit in its path; every event entry carries `correlation_id`
  explicitly.
- The `branch` field in `PLAN.md`'s frontmatter, by convention `feat/FEAT-YYYY-NNNN-<slug>`.

For every work unit, the ID appears in:

- The `id` field in the WU file's frontmatter.
- The matching `id` entry in `PLAN.md`'s `gates[].work_units[]` graph.
- Every event entry in `events.jsonl` that concerns this unit
  (`correlation_id: FEAT-YYYY-NNNN/TNN`).
- The commit trailer on the squashed commit the driver produces:
  `Feature: FEAT-YYYY-NNNN/TNN`.

A single ID threads a unit from plan to commit. When in doubt about a surface
that materially describes the work, err toward including the ID.

> On the orchestrator surface, the same IDs additionally appear in the GitHub issue
> title (`[FEAT-YYYY-NNNN/TNN] <summary>`), the branch (per task, not per feature),
> and the PR description. The loop runs single-repo on one branch with one squashed
> commit per WU, so those surfaces collapse into the commit trailer.

## Generating the next ID

**Feature-level.** The next ordinal for year `YYYY` is one greater than the largest
`NNNN` that currently appears in `.specfuse/features/FEAT-YYYY-*/`. If no feature
for `YYYY` exists yet, start at `0001`. Padding is always four digits: `0001`,
`0042`, `1234`. Year rollover does not continue the previous year's counter — each
year starts fresh at `0001`.

**Task-level.** Within a feature, substantive units start at `T01` and increment by
one. Padding is always two digits, which caps a feature at `T99`; that ceiling is
unlikely to bind, and if it does, raise an escalation rather than invent a new
format. Closing-sequence IDs are mechanical: `G<gate>-RETRO`, `G<gate>-LESSONS`,
`G<gate>-DOCS`, `G<gate>-PLAN`, one of each per gate, in that order. The session
running `plan-next` mints the next gate's substantive IDs as drafts; the human
arms them.

Do not reuse an ordinal even after a unit is abandoned. Once an ID has appeared in
the event log, it is spent. Reusing it would make history ambiguous.

## Concrete example

A feature created in 2026, 42nd of the year:

- Feature folder: `.specfuse/features/FEAT-2026-0042-orders-validation/`
- `PLAN.md` frontmatter: `feature_id: FEAT-2026-0042`, `branch: feat/FEAT-2026-0042-orders-validation`
- Event log: `.specfuse/features/FEAT-2026-0042-orders-validation/events.jsonl`

The seventh substantive unit in that feature's gate 1:

- WU file: `WU-07-validation-handler.md`
- WU frontmatter: `id: FEAT-2026-0042/T07`
- PLAN.md graph entry: `{ id: FEAT-2026-0042/T07, file: WU-07-validation-handler.md, depends_on: [FEAT-2026-0042/T03] }`
- Commit trailer on the squashed commit: `Feature: FEAT-2026-0042/T07`
- Event entries: `correlation_id: FEAT-2026-0042/T07`

Gate 1's closing sequence: `FEAT-2026-0042/G1-RETRO`, `G1-LESSONS`, `G1-DOCS`,
`G1-PLAN`, in that fixed order.

## Failure modes

A malformed ID is a correctness bug, not a cosmetic one. The driver, the linter, and
any downstream tooling filter and join on these IDs; a typo breaks the thread.

- **Pattern mismatch.** An ID that fails the regex is malformed. The linter catches
  this for IDs in the PLAN graph and WU frontmatter; the driver catches it when it
  reads a WU file. Treat a pattern failure as a stop condition — fix the ID, then
  retry. Do not loosen the pattern to admit the malformed value.
- **Cross-surface mismatch.** If an ID is well-formed on its own but disagrees
  between surfaces — a WU file whose frontmatter `id` does not match the graph
  entry's `id` — the unit cannot be reliably committed or threaded in the event
  log. Stop and emit `status: blocked` with the mismatch named explicitly.
- **Duplicate ordinal.** If you are about to mint an ID that already exists, you
  have read the feature stale. Re-read `PLAN.md` and pick the next unused ordinal.
  Never overwrite an existing WU file or graph entry to claim its ID.
- **Year drift.** An ID whose `YYYY` does not match the year the feature was
  created is syntactically valid but semantically wrong. The year in the ID is the
  year of creation, not of any subsequent work. Do not "refresh" the year when a
  feature crosses a calendar boundary.

When you detect a malformed ID in your own work in progress, fix it before reporting.
When you detect one in an artifact that is already committed, emit
`status: blocked` rather than silently rewriting history — the
[result-contract](result-contract.md) discipline applies here too.
