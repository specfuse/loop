# Rule: the RESULT block contract

Every work-unit session ends with a single fenced `result` block as the very last
thing in its output. The driver reads it; a session that does not emit one is treated
as a failed attempt. This is the agent-to-driver interface, and it is the single-repo
shape of the orchestrator's `task_completed` event — keep them aligned so the fold-in
is a rename, not a redesign.

The agent's RESULT is **advisory**. The driver runs verification itself and that is
what decides done. Report honestly: claiming `complete` on work that fails the gates
wastes an attempt and teaches the next session nothing.

## Format

````markdown
```result
status: complete | blocked        # complete = "I believe acceptance criteria are met"
summary: <one sentence on what changed>
files_changed:
  - path/to/file
acceptance_criteria:
  - text: <criterion, copied from the work unit>
    met: true | false
    evidence: <how you know — a test name, a behavior, a line reference>
blocked_reason: <present only when status is blocked>
```
````

## Rules

1. **No git.** You edit files only. The driver stages, squashes, and commits one
   trailer-carrying commit per work unit. Do not run `git` at all.
2. **Verify before you report.** Re-read what you produced and run the work unit's own
   verification before writing `status: complete`. Do not report success you have not
   checked.
3. **Blocked is a valid, respectable outcome.** If an escalation trigger fires, emit
   `status: blocked` with a precise `blocked_reason` and stop.
4. **Honesty over optimism.** A truthful `blocked` after one attempt is cheaper than
   three fresh attempts chasing a `complete` that verification keeps rejecting.
