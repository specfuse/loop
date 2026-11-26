---
class: changed
trace: FEAT-LOOP-2026-0251
---
The retry note for the three deliverable refusals now lists the paths the attempt changed (at most 20, plus a count of the rest), or says it changed none. Edits kept from an earlier attempt that this attempt did not touch are not listed; deletes, reverts, both names of a rename, mode-only changes and non-ASCII names are. Not listed: files git ignores, and files named `events.jsonl`, `PROGRESS.md` or like the unit file, in any directory
