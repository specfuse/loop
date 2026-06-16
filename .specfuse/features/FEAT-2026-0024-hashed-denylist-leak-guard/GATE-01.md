---
gate: 1
status: open        # open | awaiting_review | passed
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 — CI catches org-name re-introduction via a committed hashed denylist

## Definition of done

- The hashed-denylist core (normalize + salted-SHA-256 + char-sliding-window
  match + `.hashes` loader) exists and is unit-tested (T01).
- A `--hash-denylist` generator regenerates the committed
  `leak_denylist.hashes` from the gitignored plaintext, and `scan_repo`
  (`--all`) flags a denylisted org-name in CI using **only** the hashed file
  (plaintext absent) (T02).
- The committed `leak_denylist.hashes` for the current denylist literals is in
  the tree, and `leak-scan --all` stays clean on `main`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Gate 2's work units (the issue/PR-body Action, #46) are drafted, and
  `GATE-02-REVIEW.md` is written.

The closing sequence (close-intermediate → plan-next) is part of this
non-terminal gate and is enforced by the linter. The driver runs the gate, then
stops here for human review-and-arm (`autonomy: review`): read the review
artifact, accept or edit the drafted gate-2 work units, flip the accepted ones
to `pending`, set this gate's status to `passed`, and re-run.

## Reflection notes

<Written by the human at review time. What surprised you about the hashing
design, what you changed in the drafted gate 2 and why, anything the
retrospective got wrong. This is your record, not the agent's — keep it honest.>
