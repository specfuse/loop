# Learnings pending — FEAT-2026-0117

- **An operator `git checkout -- .` mid-dispatch discards a WU's uncommitted
  `events.jsonl` entries, and the close's own escalation trigger is what
  catches it, not a driver guard.** `FEAT-2026-0117/G1-CLOSE`'s first attempt
  correctly refused to write `## Cost analysis` when a `done` WU
  (`FEAT-2026-0117/T02H`) had no `attempt_outcome` event at all — its own
  acceptance criterion's escalation trigger, working as designed. Recovery
  had to reconstruct the missing `task_started` / `attempt_outcome` /
  `task_completed` events from the WU's driver-stamped frontmatter, marking
  each restored event's payload with `"restored": "..."` rather than
  silently backfilling it as original. Generalizable: any operator action
  that touches the working tree mid-dispatch (a stray `checkout`, `reset`,
  or `clean`) can silently erase append-only bookkeeping the driver assumes
  is durable; a close's cost-reconciliation criterion is a cheap, generic
  detector for this class of data loss, and the recovery path (frontmatter
  as source of truth, restored events flagged rather than faked) is worth
  keeping as the standard playbook rather than re-deriving it per incident.
