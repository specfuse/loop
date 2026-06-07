---
gate: 1
status: open
---

# Gate 1 — Single-driver working-tree lock

## Definition of done

- `loop.py`'s `run()` acquires a non-blocking exclusive advisory lock
  (`fcntl.flock`) on `.specfuse/.loop.lock` before any git mutation; a second
  driver against the same working tree exits non-zero with a clear contention
  message and touches no git/WU/GATE state. The lock auto-releases on process
  exit (incl. SIGKILL); `--dry-run` does not take the lock.
- The lock file is gitignored: this repo's root `.gitignore` ignores
  `.specfuse/.loop.lock`, and `init.sh` adds the same targeted ignore to every
  destination repo it sets up (idempotent; without ignoring the rest of
  `.specfuse/`).
- Tests prove a second acquire fails while the lock is held and succeeds once
  the first holder's fd closes.
- A retrospective exists; generalizable lessons are promoted; docs/roadmap
  reflect what shipped.

The closing sequence (retrospective → lessons → docs → plan-next) runs as the
gate's last four units. The driver runs the gate unattended, then stops here for
human review-and-arm. Single-gate feature: `plan-next` is terminal.

## Reflection notes

<Written by the human at review time.>
</content>
