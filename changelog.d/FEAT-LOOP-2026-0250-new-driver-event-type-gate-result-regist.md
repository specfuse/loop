---
class: added
trace: FEAT-LOOP-2026-0250
---
New driver event type `gate_result` (registered in `driver-event.schema.json`): one per gate per run, carrying `attempt`, `gate`, `ok`, `skipped`, `duration_seconds` and `phase` (`attempt`, `baseline` or `broad`)
