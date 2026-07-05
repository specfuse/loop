---
name: learnings-curate
description: "Compaction counterpart to learnings-suggest. Scan .specfuse/LEARNINGS.md, cluster near-duplicate and superseded entries, and propose-and-confirm three moves per cluster \u2014 merge duplicates, retire superseded entries into LEARNINGS-archive.md, and flag broadly-applicable rules for promotion into .specfuse/rules/*.md \u2014 to bound the planning-loaded LEARNINGS set. Writes only on explicit operator accept. Use when LEARNINGS.md has grown large enough to inflate planning-context cost or dilute signal."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Learnings curate (interactive, compaction)

`learnings-suggest` only ADDS candidates; nothing compacts. This skill is its
counterpart: it reads `.specfuse/LEARNINGS.md`, finds entries that are
duplicate, superseded, or so broadly applicable they belong in the binding
rules, and — on your explicit per-cluster decision — **merges**, **retires**
(moves to `LEARNINGS-archive.md`), or **flags for promotion** into
`.specfuse/rules/*.md`. It bounds the set that every planning session
(`/draft-feature`, `/pick-feature`, `plan-next`, `authoring-work-units`) loads
**whole**.

**Run interactively.** The skill needs the channel to present clusters and take
your accept/skip/edit decision. `claude -p` with stdin redirected can produce
the analysis but cannot accept your decisions, so it falls back to a read-only
report.

**This skill is read-only during analysis.** It writes only in §4 and only on
explicit operator accept. See `## Hard rules`.

## Why tags are not scope

Every LEARNINGS entry is tagged with its origin (`[FEAT-YYYY-NNNN/G<n>-LESSONS]`
or `[meta/...]`). **That tag is provenance, not scope.** An entry from a `done`
feature is usually still a durable cross-feature rule — that is the entire point
of LEARNINGS. So this skill MUST NOT archive an entry merely because its origin
feature is `done` or archived. Retirement is justified only by *redundancy* or
*obsolescence* against the rest of the set — never by the origin feature's
status. A deterministic "archive when feature done" pass would gut the file;
that is exactly the move this skill refuses.

## Pipeline overview

```
§1 Load → §2 Cluster (duplicate / superseded / promotable) → §3 Render → §4 Propose-and-confirm
```

---

## §1 Load

Read `.specfuse/LEARNINGS.md`. Parse entries: each is a top-level list item
under the `## Entries` section, beginning `- [<tag>] ` and continuing across
wrapped lines until the next `- [` at column 0 or end of file. Track for each
entry: its tag, its full text, and its line span (for later removal).

Read `.specfuse/rules/*.md` headings and the existing `.specfuse/LEARNINGS-archive.md`
(if present) so promotion and retirement proposals can reference where a rule
already lives and avoid re-archiving something already archived.

**Scope statement.** The skill reads only `.specfuse/LEARNINGS.md`,
`.specfuse/LEARNINGS-archive.md`, and `.specfuse/rules/*.md`. It does not read
feature folders — `learnings-suggest` owns the events.jsonl evidence path.

---

## §2 Cluster

Group entries into three (non-exclusive) candidate categories. An entry may
appear in at most one proposed action; if it qualifies for several, prefer
**promote > merge > retire** (promotion is the highest-leverage outcome).

- **Duplicate cluster** — two or more entries stating substantially the same
  rule, possibly from different features. Candidate action: **merge** into one
  entry that keeps every contributing tag (so provenance is preserved) and the
  clearest phrasing.
- **Superseded entry** — an entry that a later entry contradicts, generalizes,
  or makes obsolete (e.g. an entry about a behavior a later feature changed).
  Candidate action: **retire** the superseded entry to `LEARNINGS-archive.md`.
- **Promotable entry** — an entry phrased as a rule that applies to *every*
  feature regardless of domain (a methodology invariant), not a
  situation-specific lesson. Candidate action: **flag for promotion** into the
  matching `.specfuse/rules/*.md` file, then retire the LEARNINGS copy once the
  operator confirms the rule landed.

For each cluster, record the contributing entries' tags and line spans so §4
can act precisely.

---

## §3 Render

Print a compact summary before any decision, sorted promote → merge → retire:

```text
LEARNINGS curation — N entries, ~T tokens loaded into each planning session

PROMOTE (→ rules)   2 candidates
MERGE (duplicates)  3 clusters (7 entries → 3)
RETIRE (superseded) 4 entries (→ LEARNINGS-archive.md)

Net: N entries → M entries  (~T → ~T' tokens)
```

Estimate token counts as a rough char/4 heuristic; label them approximate. The
point is to show the operator the bound, not to be exact.

---

## §4 Propose-and-confirm

Walk candidates in order (promote → merge → retire). For each, show the exact
before/after, then ask `accept / skip / edit?`.

**Merge.** Show the entries being merged and the single replacement entry
(which MUST carry every contributing tag, e.g.
`- [FEAT-2026-0003/G2-LESSONS; FEAT-2026-0007/G1-LESSONS] <merged rule>`). On
**accept**, remove the contributing entries and insert the merged entry in
their place in `LEARNINGS.md`.

**Retire.** Show the entry and the reason it is superseded (cite the entry that
supersedes it). On **accept**, move the entry verbatim from `LEARNINGS.md` into
`LEARNINGS-archive.md` under a dated curation heading (see below). Removal from
LEARNINGS and the append to the archive happen together — never one without the
other.

**Promote.** Show the entry and the target `.specfuse/rules/<file>.md` it
belongs in, with the proposed rule text. On **accept**, append the rule to that
rules file, then retire the LEARNINGS copy to `LEARNINGS-archive.md` with a note
`promoted to rules/<file>.md`. If the operator prefers to write the rule
themselves, **flag-only**: leave LEARNINGS untouched and print the suggested
rules-file edit for them to apply.

**edit** — operator supplies revised text; confirm once more before writing.

The skill MUST NOT write to any file without an explicit per-candidate accept.

### LEARNINGS-archive.md format

If `.specfuse/LEARNINGS-archive.md` does not exist, create it with this header:

```markdown
---
project: <project-name from roadmap.md frontmatter, or the repo name>
---

# Archived LEARNINGS

Entries retired from `.specfuse/LEARNINGS.md` by `/learnings-curate` because they
were duplicated, superseded, or promoted into `.specfuse/rules/*.md`. Kept for
provenance — planning sessions do NOT load this file. Retirement reason and date
travel with each entry. Nothing here is authoritative; `.specfuse/LEARNINGS.md`
and `.specfuse/rules/*.md` are.

## Retired entries
```

Append retired entries under a per-run dated heading so the audit trail is
chronological:

```markdown
### Curated YYYY-MM-DD

- [<original tag>] <original entry text>
  _Retired: superseded by [<tag>]._   (or)   _Retired: promoted to rules/<file>.md._
```

Use the actual current date — ask the operator if you cannot determine it; do
not invent one.

---

## Hard rules

1. **Provenance is not scope.** Never retire an entry because its origin feature
   is `done`/`abandoned`. Retire only for redundancy or obsolescence against the
   rest of the set (see "Why tags are not scope").
2. **Read-only analysis.** No writes during §1–§3. Writing is permitted only in
   §4, only on explicit per-candidate accept.
3. **Conservation.** Every retired entry lands in `LEARNINGS-archive.md` —
   removal from `LEARNINGS.md` and the archive append are one operation. An entry
   is never deleted outright; the only loss-free path out of LEARNINGS is the
   archive (or a merge that preserves its tag and rule).
4. **Merges preserve every tag.** A merged entry carries the union of its
   sources' tags. No provenance is dropped.
5. **Scope boundary.** Reads/writes confined to `.specfuse/LEARNINGS.md`,
   `.specfuse/LEARNINGS-archive.md`, and `.specfuse/rules/*.md`. No feature
   folders, no events.jsonl — that is `learnings-suggest`'s domain.
6. **No silent re-ordering.** Apart from the entries an accepted action moves,
   leave the order of LEARNINGS untouched, so a diff shows exactly what curation
   changed.

End with the RESULT block from
[`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` once the operator has walked every cluster and the accepted
writes landed. `status: blocked` only if `LEARNINGS.md` cannot be parsed into
entries (malformed structure the operator must fix first).

## What this skill does NOT do

- **Does not auto-curate.** Every move is operator-confirmed; there is no
  batch-accept.
- **Does not generate new lessons.** Adding candidates is `learnings-suggest`'s
  job; this skill only compacts what exists.
- **Does not archive by feature status.** See hard rule 1.
- **Does not load or rank indexed slices.** Per-slice retrieval (load only the
  relevant LEARNINGS subset into a planning session) is deferred future work,
  not part of this skill.

## Version

**v0.1.** Manual, propose-and-confirm. The three moves (merge / retire /
promote) are the whole compaction surface today. Expected to grow once it is run
on a LEARNINGS file big enough that the clustering itself becomes the
bottleneck — at which point the deferred indexed-retrieval step earns its place.
Shared methodology craft (the loop is its near-term author). Pairs with
`learnings-suggest` (the additive half) and mirrors `roadmap-archive` (the
roadmap's compaction half).
