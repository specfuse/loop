---
class: changed
trace: FEAT-LOOP-2026-0251
---
The retry note for the three deliverable refusals now lists the paths the attempt changed (at most 20, plus a count of the rest), or says it changed none. Edits kept from an earlier attempt that this attempt did not touch are not listed; kept files that this attempt deleted or reverted are. Known limits: a renamed tracked file is listed under its new name only, and later changes to a kept file with a non-ASCII name, or a mode-only change to a kept file, are not listed, so the note can say it changed none
