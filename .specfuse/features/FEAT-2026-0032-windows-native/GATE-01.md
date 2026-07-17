---
gate: 1
status: awaiting_review
---

# Gate 1 — Driver imports and runs on native Windows, proven by CI

## Definition of done

- Every implementation work unit in this gate is `done` (T01–T04).
- On `windows-latest` CI, `import specfuse.loop.loop` succeeds and
  `loop.py --dry-run` walks the bundled example (`FEAT-2026-0001-health-endpoint`)
  in dependency order and exits `0`. The two import/runtime hard-blockers
  (`import fcntl`, the `killpg`/`SIGKILL` timeout path) no longer break on Windows.
- Home-path redaction covers the Windows home shape (`C:\Users\<name>\`).
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.
- Gate 2's work units are drafted, and `GATE-02-REVIEW.md` is written.

The closing sequence (`close-intermediate` → `plan-next`) is part of this gate
and is enforced by the linter. The driver runs the gate unattended, then stops
here for human review-and-arm: read the review artifact, accept or edit the
drafted gate-2 work units, flip the accepted ones to `pending`, set this gate's
status to `passed`, and re-run.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted gate 2 and why, anything the retrospective got wrong.>
