---
name: learnings-suggest
description: Scan attempt_outcome events across features, cluster non-passing attempts by (failure_class, failure_signature), and surface clusters above a configurable threshold as candidate LEARNINGS entries for the operator to promote. Read-only — does NOT auto-append to LEARNINGS.md.
---

# Learnings suggest (interactive, diagnostic)

Run interactively. This skill scans `attempt_outcome` events across every
feature under `.specfuse/features/`, clusters non-passing attempts by
`(failure_class, failure_signature)`, and surfaces recurring patterns as
candidate LEARNINGS entries. The operator decides whether to promote each
candidate; the skill does NOT auto-append to `.specfuse/LEARNINGS.md`.

**This skill is read-only during the scan phase.** See `## Hard rules` below.

## Pipeline overview

```
§1 Scan → §2 Cluster → §3 Threshold + render → §4 Propose-and-confirm
```

---

## §1 Scan

Glob every `.specfuse/features/FEAT-*/events.jsonl`. For each file, read
line-by-line, parse JSON, and retain records where:

- `event_type == "attempt_outcome"`, AND
- `payload.outcome != "passed"`

**Scope statement.** The scan covers only `.specfuse/features/FEAT-*/`. If a
feature folder exists outside this path (e.g. `.specfuse/features-archive/`),
the glob misses it — mention any such folder explicitly in the run output as
out-of-scope.

**Malformed-line handling.** Skip lines that cannot be parsed as JSON or that
are missing required fields (`event_type`, `payload.outcome`,
`payload.failure_class`, `payload.failure_signature`, `correlation_id`). Print
a warning for each skipped line:

```
[WARN] <path>:<line_num>: skipped — <reason>
```

Do NOT abort the scan on malformed lines.

**Legacy-event tolerance.** Feature folders whose `events.jsonl` predates the
`attempt_outcome` event type (T01) will contain no matching records. These
folders contribute nothing to the clusters and are rendered silently as
"no contributing data" — NOT as errors.

---

## §2 Cluster

Group retained records by the tuple `(payload.failure_class,
payload.failure_signature)`.

For each cluster, track:

- **count** — total number of non-passing attempt records in this cluster
- **wu_set** — the set of distinct `correlation_id` values (WU IDs across
  features) that contributed at least one record
- **sources** — at least one specific `events.jsonl` path + line number per
  cluster, so the operator can verify the raw evidence

---

## §3 Threshold + render

**Default threshold: ≥ 2 distinct WUs (`correlation_id` values) in the
cluster.** A single WU spinning on the same signature is a per-WU bug, not a
general lesson. Only clusters meeting the threshold are surfaced as candidates.

**Configurable threshold — `--min-wus N` flag (default `2`).** The operator
may specify a different minimum by saying "use `--min-wus 3`" (or the
equivalent spoken form) at skill invocation. Document the current threshold in
the run header.

Print a candidate-list table sorted by descending cluster size, above the
threshold only:

```text
# cluster | failure_class | failure_signature | WUs | total attempts
1         | tests         | test_foo          | 4   | 7
2         | other         | no_gate_marker    | 3   | 5
```

Also print a summary of features that contributed no data (legacy or empty
`events.jsonl`).

---

## §4 Propose-and-confirm per cluster

For each cluster above the threshold, draft a candidate LEARNINGS entry
following the format in `.specfuse/LEARNINGS.md`'s header:

```
- [meta/learnings-suggest] <failure_class>/<short signature> recurs across
  <N> WUs (<wu_id_1>, <wu_id_2>, ...): <one-sentence rule stating what a
  FUTURE work unit should do differently to avoid this failure class>.
  Evidence: <events.jsonl path>:<line_num>.
```

Then ask the operator:

```
Cluster <n>: promote / skip / edit?
```

- **promote** — append the drafted entry (or edited version) to
  `.specfuse/LEARNINGS.md` below the `<!-- lessons work units append below
  this line -->` marker. This is the ONLY path by which this skill writes to
  `LEARNINGS.md`.
- **skip** — move to the next cluster without writing anything.
- **edit** — the operator provides a revised entry; confirm once more before
  appending.

The skill MUST NOT append to `LEARNINGS.md` without explicit operator
`promote` (or `edit` followed by accept).

---

## Hard rules

1. **Read-only scan.** The skill MUST NOT write to any `events.jsonl`, any
   feature folder, or `LEARNINGS.md` during §1–§3. Writing is permitted only
   in §4 and only on explicit operator `promote`.
2. **Trace every claim.** Every cluster surfaced MUST cite at least one
   specific `events.jsonl` path + line number that the operator can open and
   verify. Do not surface a cluster without a concrete source reference.
3. **No auto-promotion.** The LEARNINGS-promotion pipeline
   (runs → retrospective → lessons → LEARNINGS.md) is authoritative. This
   skill surfaces candidates only; the operator's explicit decision in §4 is
   required.
4. **Scope boundary.** Do not read or write files outside
   `.specfuse/features/FEAT-*/events.jsonl` (read) and
   `.specfuse/LEARNINGS.md` (write, §4 only).

---

## Binding reference

- `.specfuse/rules/result-contract.md` — read-only contract and RESULT format
- `.specfuse/LEARNINGS.md` — authoritative entry format (header § "Format")
- T01 (`attempt_outcome` payload): fields `failure_class`, `failure_signature`,
  `outcome`, `correlation_id` per FEAT-2026-0016 PLAN.md "Event payload
  shape — `attempt_outcome` v1"
