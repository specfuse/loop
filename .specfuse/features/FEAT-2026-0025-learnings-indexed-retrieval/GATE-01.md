---
gate: 1
status: awaiting_review
---

# Gate 1 — the LEARNINGS retrieval primitive

## Definition of done

- `.specfuse/scripts/learnings_query.py` parses `LEARNINGS.md` into tagged entries
  and exposes a stdlib BM25/tf-idf ranker returning the top-N most relevant to a
  query string (T01).
- The same module runs as a CLI (`learnings_query.py "<query>" [--top N]`) that
  prints the ranked slice, and below a configurable entry-count threshold emits a
  `load-whole` signal so small files are unaffected (T02).
- Retrospective, durable lessons, and docs are produced by the close-intermediate
  WU; gate 2's consumer-wiring WUs are drafted by the plan-next WU and left in
  `draft` for human review-and-arm.

Non-terminal gate: closing sequence is `close-intermediate` (folds
retro + lessons + docs) followed by `plan-next` (drafts gate 2). The driver halts
here for human review-and-arm before gate 2 (autonomy `review`).

## Reflection notes

<Written by the human at review time.>
